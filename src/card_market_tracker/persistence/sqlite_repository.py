"""Bounded, atomic, synthetic-only SQLite persistence and consistent local copies."""

import os
import sqlite3
import stat
import time
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from datetime import UTC, datetime
from pathlib import Path

from card_market_tracker.catalog.ingestion import ExternalReference
from card_market_tracker.catalog.manifest import parse_reference
from card_market_tracker.catalog.models import Entity
from card_market_tracker.catalog.resolver import reference_dict
from card_market_tracker.catalog.validation import CatalogError, uuid_value

from . import schema
from .application import context_fingerprint, fingerprint, validate_batch
from .errors import PersistenceError
from .models import PersistedRecord, PersistenceBatch, WriteResult

DEFAULT_TIMEOUT = 2.0
MAX_LIMIT = 1000
_SIDECARS = ("-journal", "-wal", "-shm")
_ENTITY_COLUMNS = "cmt_id,kind,set_id,card_id,card_number,language,variant,sealed_type"
_RECORD_COLUMNS = (
    "batch_id,record_index,status,category,cmt_id,kind,namespace,external_id,language,"
    "variant,name,set_namespace,set_external_id,set_language,card_number,release_date,"
    "provider_updated_at,captured_at,provenance"
)


class _Budget:
    def __init__(self, timeout: float) -> None:
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
            raise PersistenceError("invalid_field")
        if not 0 < timeout <= 5:
            raise PersistenceError("invalid_field")
        self.deadline = time.monotonic() + timeout

    def remaining(self) -> float:
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise PersistenceError("storage_timeout")
        return remaining

    def progress(self) -> int:
        return int(time.monotonic() >= self.deadline)


def _exists(path: Path) -> bool:
    return os.path.lexists(path)


def _unsafe_stat(path: Path, *, file: bool) -> os.stat_result:
    information = path.lstat()
    reparse = getattr(information, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
    if path.is_symlink() or path.is_junction() or reparse:
        raise PersistenceError("unsafe_destination")
    if file and (not stat.S_ISREG(information.st_mode) or information.st_nlink != 1):
        raise PersistenceError("unsafe_destination")
    if not file and not stat.S_ISDIR(information.st_mode):
        raise PersistenceError("unsafe_destination")
    return information


def _checked_path(value: Path) -> Path:
    if not isinstance(value, Path):
        raise PersistenceError("invalid_field")
    text = str(value)
    if not text or len(text) > 4096 or "\x00" in text or ".." in value.parts:
        raise PersistenceError("unsafe_destination")
    # UNC/device paths and Windows alternate data streams are not local DB files.
    if text.startswith(("\\\\", "//")) or any(":" in part for part in value.parts[1:]):
        raise PersistenceError("unsafe_destination")
    isreserved = getattr(os.path, "isreserved", None)
    if isreserved is not None and isreserved(text):
        raise PersistenceError("unsafe_destination")
    path = value.absolute()
    for parent in reversed(path.parents):
        _unsafe_stat(parent, file=False)
    if _exists(path):
        _unsafe_stat(path, file=True)
    return path


def _sidecars(path: Path) -> Iterator[Path]:
    for suffix in _SIDECARS:
        yield Path(str(path) + suffix)


def _check_sidecars(path: Path, *, new: bool) -> None:
    for sidecar in _sidecars(path):
        if _exists(sidecar):
            if new:
                raise PersistenceError("unsafe_destination")
            _unsafe_stat(sidecar, file=True)


def _reserve(path: Path) -> tuple[int, int]:
    _check_sidecars(path, new=True)
    flags = os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        information = os.fstat(descriptor)
        if not stat.S_ISREG(information.st_mode) or information.st_nlink != 1:
            raise PersistenceError("unsafe_destination")
        return information.st_dev, information.st_ino
    finally:
        os.close(descriptor)


def _error(error: sqlite3.Error) -> PersistenceError:
    code = getattr(error, "sqlite_errorcode", 0) & 0xFF
    if code in (sqlite3.SQLITE_BUSY, sqlite3.SQLITE_LOCKED):
        return PersistenceError("storage_locked")
    if code in (sqlite3.SQLITE_CORRUPT, sqlite3.SQLITE_NOTADB):
        return PersistenceError("storage_corrupt")
    if code == sqlite3.SQLITE_INTERRUPT:
        return PersistenceError("storage_timeout")
    return PersistenceError("storage_io")


@contextmanager
def _connection(
    value: Path, *, writable: bool, create: bool = False, timeout: float = DEFAULT_TIMEOUT
) -> Iterator[tuple[sqlite3.Connection, _Budget]]:
    connection: sqlite3.Connection | None = None
    budget = _Budget(timeout)
    try:
        path = _checked_path(value)
        existed = _exists(path)
        if not existed:
            if not create:
                raise PersistenceError("storage_io")
            reserved = _reserve(path)
            information = path.lstat()
            if (information.st_dev, information.st_ino) != reserved:
                raise PersistenceError("unsafe_destination")
        else:
            _check_sidecars(path, new=False)
        mode = "rw" if writable else "ro"
        connection = sqlite3.connect(
            path.as_uri() + "?mode=" + mode,
            uri=True,
            autocommit=True,
            timeout=budget.remaining(),
        )
        connection.row_factory = sqlite3.Row
        connection.set_progress_handler(budget.progress, 1000)
        _execute(connection, budget, "PRAGMA foreign_keys=ON")
        if _execute(connection, budget, "PRAGMA foreign_keys").fetchone()[0] != 1:
            raise PersistenceError("storage_schema")
        if not writable:
            _execute(connection, budget, "PRAGMA query_only=ON")
        yield connection, budget
    except sqlite3.Error as error:
        raise _error(error) from None
    except OSError:
        raise PersistenceError("storage_io") from None
    finally:
        if connection is not None:
            connection.close()


def _execute(
    connection: sqlite3.Connection,
    budget: _Budget,
    sql: str,
    values: tuple[object, ...] = (),
) -> sqlite3.Cursor:
    # Identifiers are internal constants; the pragma requires a fixed integer literal.
    milliseconds = max(1, int(budget.remaining() * 1000))
    connection.execute(f"PRAGMA busy_timeout={milliseconds}")
    return connection.execute(sql, values)


@contextmanager
def _transaction(connection: sqlite3.Connection, budget: _Budget) -> Iterator[None]:
    _execute(connection, budget, "BEGIN IMMEDIATE")
    try:
        yield
        _execute(connection, budget, "COMMIT")
    except BaseException:
        # Recovery must remain possible after an exhausted VM/lock budget.
        connection.set_progress_handler(None, 0)
        connection.execute("PRAGMA busy_timeout=0")
        if connection.in_transaction:
            with suppress(sqlite3.Error):
                connection.execute("ROLLBACK")
        raise


def _check_schema(connection: sqlite3.Connection, budget: _Budget) -> bool:
    objects = schema.inventory(connection)
    application = _execute(connection, budget, "PRAGMA application_id").fetchone()[0]
    version = _execute(connection, budget, "PRAGMA user_version").fetchone()[0]
    if not objects and application == 0 and version == 0:
        return False
    if application != schema.APPLICATION_ID or version != schema.SCHEMA_VERSION:
        raise PersistenceError("storage_schema")
    if objects != schema.expected_inventory():
        raise PersistenceError("storage_schema")
    metadata = _execute(
        connection, budget, "SELECT singleton,owner,schema_version FROM storage_metadata"
    ).fetchall()
    if [tuple(row) for row in metadata] != [(1, schema.OWNER, schema.SCHEMA_VERSION)]:
        raise PersistenceError("storage_schema")
    journal = _execute(connection, budget, "PRAGMA journal_mode").fetchone()[0]
    if journal != "delete":
        raise PersistenceError("storage_schema")
    return True


def _require_schema(connection: sqlite3.Connection, budget: _Budget) -> None:
    if not _check_schema(connection, budget):
        raise PersistenceError("storage_schema")


def _initialize(connection: sqlite3.Connection, budget: _Budget) -> None:
    # Inspect before changing persistent journal state, especially foreign databases.
    current = _check_schema(connection, budget)
    if current:
        _execute(connection, budget, "PRAGMA synchronous=FULL")
        return
    if _execute(connection, budget, "PRAGMA journal_mode=DELETE").fetchone()[0] != "delete":
        raise PersistenceError("storage_schema")
    _execute(connection, budget, "PRAGMA synchronous=FULL")
    with _transaction(connection, budget):
        # Another initializer may have won the lock before this transaction began.
        if _check_schema(connection, budget):
            return
        for statement in schema.STATEMENTS:
            _execute(connection, budget, statement)
        _execute(
            connection,
            budget,
            "INSERT INTO storage_metadata VALUES (?,?,?)",
            (1, schema.OWNER, schema.SCHEMA_VERSION),
        )
        _execute(connection, budget, f"PRAGMA application_id={schema.APPLICATION_ID}")
        _execute(connection, budget, f"PRAGMA user_version={schema.SCHEMA_VERSION}")


def _ok() -> dict[str, object]:
    return {"version": 1, "result": "ok", "schema_version": schema.SCHEMA_VERSION}


def initialize(path: Path, *, timeout: float = DEFAULT_TIMEOUT) -> dict[str, object]:
    with _connection(path, writable=True, create=True, timeout=timeout) as (connection, budget):
        _initialize(connection, budget)
    return _ok()


def _entity_values(entity: Entity) -> tuple[object, ...]:
    return (
        entity.cmt_id,
        entity.kind,
        entity.set_id,
        entity.card_id,
        entity.card_number,
        entity.language,
        entity.variant,
        entity.sealed_type,
    )


def _project_entities(
    connection: sqlite3.Connection, budget: _Budget, entities: tuple[Entity, ...]
) -> int:
    inserted = 0
    order = {"set": 0, "card": 1, "printing": 2, "sealed": 3}
    for entity in sorted(entities, key=lambda item: (order[item.kind], item.cmt_id)):
        values = _entity_values(entity)
        previous = _execute(
            connection,
            budget,
            "SELECT " + _ENTITY_COLUMNS + " FROM entities WHERE cmt_id=?",
            (entity.cmt_id,),
        ).fetchone()
        if previous is not None:
            if tuple(previous) != values:
                raise PersistenceError("identity_conflict")
            continue
        try:
            _execute(
                connection,
                budget,
                "INSERT INTO entities (" + _ENTITY_COLUMNS + ") VALUES (?,?,?,?,?,?,?,?)",
                values,
            )
        except sqlite3.IntegrityError:
            raise PersistenceError("identity_conflict") from None
        inserted += 1
    return inserted


def _record_values(batch_id: str, record: PersistedRecord) -> tuple[object, ...]:
    prefix = (batch_id, record.index, record.status, record.category, record.cmt_id)
    observation = record.observation
    if observation is None:
        return (*prefix, *((None,) * 14))
    reference = observation.reference
    parent = observation.set_reference
    return (
        *prefix,
        observation.kind,
        reference.namespace,
        reference.external_id,
        reference.language,
        reference.variant,
        observation.name,
        None if parent is None else parent.namespace,
        None if parent is None else parent.external_id,
        None if parent is None else parent.language,
        observation.card_number,
        observation.release_date,
        observation.provider_updated_at,
        observation.captured_at,
        observation.provenance,
    )


def _result(row: sqlite3.Row, *, replay: bool, observations: int, entities: int) -> WriteResult:
    return WriteResult(
        result="replay" if replay else row["result"],
        batch_id=row["batch_id"],
        first_persisted_at=row["first_persisted_at"],
        input_count=row["input_count"],
        accepted_count=row["accepted_count"],
        candidate_count=row["candidate_count"],
        rejected_count=row["rejected_count"],
        committed_observations=observations,
        committed_entities=entities,
    )


def persist(
    path: Path, batch: PersistenceBatch, *, timeout: float = DEFAULT_TIMEOUT
) -> WriteResult:
    admitted = validate_batch(batch)
    content_hash = fingerprint(admitted)
    context_hash = context_fingerprint(admitted)
    result: WriteResult
    with _connection(path, writable=True, create=True, timeout=timeout) as (connection, budget):
        _initialize(connection, budget)
        with _transaction(connection, budget):
            previous = _execute(
                connection, budget, "SELECT * FROM batches WHERE batch_id=?", (admitted.batch_id,)
            ).fetchone()
            if previous is not None:
                if previous["fingerprint"] != content_hash:
                    raise PersistenceError("replay_conflict")
                result = _result(previous, replay=True, observations=0, entities=0)
            else:
                inserted = _project_entities(connection, budget, admitted.entities)
                count = len(admitted.records)
                accepted = sum(record.status == "accepted" for record in admitted.records)
                candidates = sum(record.status == "candidate" for record in admitted.records)
                rejected = count - accepted - candidates
                outcome = "empty" if count == 0 else "ok" if accepted == count else "mixed"
                first = datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
                _execute(
                    connection,
                    budget,
                    "INSERT INTO batches VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        admitted.batch_id,
                        1,
                        1,
                        admitted.captured_at,
                        first,
                        content_hash,
                        context_hash,
                        count,
                        accepted,
                        candidates,
                        rejected,
                        outcome,
                    ),
                )
                for record in admitted.records:
                    _execute(
                        connection,
                        budget,
                        "INSERT INTO records ("
                        + _RECORD_COLUMNS
                        + ") VALUES ("
                        + ",".join("?" for _ in range(19))
                        + ")",
                        _record_values(admitted.batch_id, record),
                    )
                stored = _execute(
                    connection,
                    budget,
                    "SELECT * FROM batches WHERE batch_id=?",
                    (admitted.batch_id,),
                ).fetchone()
                result = _result(
                    stored, replay=False, observations=accepted + candidates, entities=inserted
                )
    return result


def _observation(row: sqlite3.Row) -> dict[str, object] | None:
    if row["status"] == "rejected":
        return None
    parent: dict[str, object] | None = None
    if row["set_namespace"] is not None:
        parent = {
            "namespace": row["set_namespace"],
            "kind": "set",
            "external_id": row["set_external_id"],
            "language": row["set_language"],
            "variant": "unknown",
        }
    return {
        "kind": row["kind"],
        "reference": {
            "namespace": row["namespace"],
            "kind": row["kind"],
            "external_id": row["external_id"],
            "language": row["language"],
            "variant": row["variant"],
        },
        "name": row["name"],
        "set_reference": parent,
        "card_number": row["card_number"],
        "release_date": row["release_date"],
        "provider_updated_at": row["provider_updated_at"],
        "captured_at": row["captured_at"],
        "provenance": row["provenance"],
    }


def query(
    path: Path,
    *,
    batch_id: str | None = None,
    cmt_id: str | None = None,
    candidate_reference: ExternalReference | None = None,
    limit: int = 100,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, object]:
    if type(limit) is not int or not 1 <= limit <= MAX_LIMIT:
        raise PersistenceError("invalid_field")
    if sum(value is not None for value in (batch_id, cmt_id, candidate_reference)) > 1:
        raise PersistenceError("invalid_shape")
    sql_filter = ""
    values: tuple[object, ...] = ()
    try:
        if batch_id is not None:
            sql_filter, values = " WHERE r.batch_id=?", (uuid_value(batch_id),)
        elif cmt_id is not None:
            sql_filter, values = " WHERE r.cmt_id=?", (uuid_value(cmt_id),)
        elif candidate_reference is not None:
            if not isinstance(candidate_reference, ExternalReference):
                raise PersistenceError("invalid_field")
            reference = parse_reference(reference_dict(candidate_reference))
            sql_filter = (
                " WHERE r.status='candidate' AND r.namespace=? AND r.kind=?"
                " AND r.external_id=? AND r.language IS ? AND r.variant=?"
            )
            values = (
                reference.namespace,
                reference.kind,
                reference.external_id,
                reference.language,
                reference.variant,
            )
    except CatalogError as error:
        raise PersistenceError(error.category) from None
    with _connection(path, writable=False, timeout=timeout) as (connection, budget):
        _require_schema(connection, budget)
        rows = _execute(
            connection,
            budget,
            "SELECT r.*,b.first_persisted_at FROM records r JOIN batches b ON b.batch_id=r.batch_id"
            + sql_filter
            + " ORDER BY COALESCE(r.captured_at,b.captured_at),r.batch_id,r.record_index LIMIT ?",
            (*values, limit),
        ).fetchall()
        records: list[object] = [
            {
                "batch_id": row["batch_id"],
                "index": row["record_index"],
                "status": row["status"],
                "category": row["category"],
                "cmt_id": row["cmt_id"],
                "observation": _observation(row),
                "first_persisted_at": row["first_persisted_at"],
            }
            for row in rows
        ]
    return {"version": 1, "result": "ok" if records else "empty", "records": records}


def _verify(connection: sqlite3.Connection, budget: _Budget) -> None:
    _require_schema(connection, budget)
    integrity = _execute(connection, budget, "PRAGMA integrity_check").fetchall()
    foreign_keys = _execute(connection, budget, "PRAGMA foreign_key_check").fetchall()
    if [tuple(row) for row in integrity] != [("ok",)] or foreign_keys:
        raise PersistenceError("storage_corrupt")


def verify(path: Path, *, timeout: float = DEFAULT_TIMEOUT) -> dict[str, object]:
    with _connection(path, writable=False, timeout=timeout) as (connection, budget):
        _verify(connection, budget)
    return _ok()


def _remove_owned(path: Path, identity: tuple[int, int]) -> None:
    """Only clean files reserved by this failed copy, in a trusted local directory."""
    with suppress(OSError, PersistenceError):
        information = _unsafe_stat(path, file=True)
        if (information.st_dev, information.st_ino) != identity:
            return
        for sidecar in _sidecars(path):
            if _exists(sidecar):
                _unsafe_stat(sidecar, file=True)
                sidecar.unlink()
        path.unlink()


def _copy(source: Path, destination: Path, *, timeout: float) -> dict[str, object]:
    owned: tuple[int, int] | None = None
    target: Path | None = None
    completed = False
    try:
        with _connection(source, writable=False, timeout=timeout) as (connection, budget):
            _verify(connection, budget)
            target = _checked_path(destination)
            if _exists(target):
                raise PersistenceError("unsafe_destination")
            owned = _reserve(target)
            with _connection(target, writable=True, timeout=budget.remaining()) as (
                copy,
                copy_budget,
            ):
                information = target.lstat()
                if (information.st_dev, information.st_ino) != owned:
                    raise PersistenceError("unsafe_destination")
                _execute(copy, copy_budget, "PRAGMA synchronous=FULL")

                def progress(status: int, remaining: int, total: int) -> None:
                    budget.remaining()

                # No initial busy wait: the bounded callback controls retry duration.
                connection.execute("PRAGMA busy_timeout=0")
                copy.execute("PRAGMA busy_timeout=0")
                connection.backup(copy, pages=32, progress=progress, sleep=0.025)
                _verify(copy, copy_budget)
            with _connection(target, writable=False, timeout=budget.remaining()) as (
                reopened,
                again,
            ):
                _verify(reopened, again)
        completed = True
        return _ok()
    except OSError:
        raise PersistenceError("storage_io") from None
    finally:
        # Success leaves a verified artifact; any exception removes the owned partial file.
        if not completed and target is not None and owned is not None:
            _remove_owned(target, owned)


def backup(
    source: Path, destination: Path, *, timeout: float = DEFAULT_TIMEOUT
) -> dict[str, object]:
    return _copy(source, destination, timeout=timeout)


def restore(
    source: Path, destination: Path, *, timeout: float = DEFAULT_TIMEOUT
) -> dict[str, object]:
    return _copy(source, destination, timeout=timeout)
