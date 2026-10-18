"""Bounded SQLite history, explicit migration and consistent verified local copies."""

import os
import sqlite3
import stat
import time
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from card_market_tracker.catalog.ingestion import ExternalReference, Observation
from card_market_tracker.catalog.manifest import parse_manifest, parse_reference
from card_market_tracker.catalog.models import Entity
from card_market_tracker.catalog.resolver import reference_dict
from card_market_tracker.catalog.validation import CatalogError, uuid_value
from card_market_tracker.discovery.errors import DiscoveryError
from card_market_tracker.discovery.models import BatchSnapshot, SnapshotRecord
from card_market_tracker.discovery.multi_models import MultiRevisionRequest, ProfiledCapture
from card_market_tracker.discovery.scoped_models import ScopedCapture, ScopedDiscoveryRequest
from card_market_tracker.discovery.validation import validate_snapshot

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
    if application != schema.APPLICATION_ID or version not in (1, 2):
        raise PersistenceError("storage_schema")
    if objects != schema.expected_inventory(version):
        raise PersistenceError("storage_schema")
    metadata = _execute(
        connection, budget, "SELECT singleton,owner,schema_version FROM storage_metadata"
    ).fetchall()
    if [tuple(row) for row in metadata] != [(1, schema.OWNER, version)]:
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


def _ok(version: int = schema.SCHEMA_VERSION) -> dict[str, object]:
    return {"version": 1, "result": "ok", "schema_version": version}


def initialize(path: Path, *, timeout: float = DEFAULT_TIMEOUT) -> dict[str, object]:
    with _connection(path, writable=True, create=True, timeout=timeout) as (connection, budget):
        _initialize(connection, budget)
        version = _execute(connection, budget, "PRAGMA user_version").fetchone()[0]
    return _ok(version)


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
                if _execute(connection, budget, "PRAGMA user_version").fetchone()[0] == 2:
                    from .capture import store_legacy

                    store_legacy(connection, budget, admitted.batch_id)
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
        _execute(connection, budget, "BEGIN")
        _require_schema(connection, budget)
        _check_integrity(connection, budget)
        if _execute(connection, budget, "PRAGMA user_version").fetchone()[0] == 2:
            from .capture import verify_captures

            verify_captures(connection, budget)
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


def _check_integrity(connection: sqlite3.Connection, budget: _Budget) -> None:
    integrity = _execute(connection, budget, "PRAGMA integrity_check(1)").fetchone()
    foreign_key = _execute(connection, budget, "PRAGMA foreign_key_check").fetchone()
    if integrity is None or tuple(integrity) != ("ok",) or foreign_key is not None:
        raise PersistenceError("storage_corrupt")


def _verify(connection: sqlite3.Connection, budget: _Budget) -> None:
    _require_schema(connection, budget)
    _check_integrity(connection, budget)
    if _execute(connection, budget, "PRAGMA user_version").fetchone()[0] == 2:
        from .capture import verify_captures

        verify_captures(connection, budget)


def verify(path: Path, *, timeout: float = DEFAULT_TIMEOUT) -> dict[str, object]:
    with _connection(path, writable=False, timeout=timeout) as (connection, budget):
        _verify(connection, budget)
        version = _execute(connection, budget, "PRAGMA user_version").fetchone()[0]
    return _ok(version)


def _snapshot_record(row: sqlite3.Row) -> SnapshotRecord:
    observation = None
    if row["status"] != "rejected":
        parent = None
        if row["set_namespace"] is not None:
            parent = ExternalReference(
                row["set_namespace"], "set", row["set_external_id"], row["set_language"]
            )
        observation = Observation(
            row["kind"],
            ExternalReference(
                row["namespace"], row["kind"], row["external_id"], row["language"], row["variant"]
            ),
            row["name"],
            parent,
            row["card_number"],
            row["release_date"],
            row["provider_updated_at"],
            row["captured_at"],
            provenance=row["provenance"],
        )
    return SnapshotRecord(
        row["record_index"], row["status"], row["category"], row["cmt_id"], observation
    )


_IDENTITY_FIELDS = tuple(_ENTITY_COLUMNS.split(","))
_SNAPSHOT_JOIN = (
    "SELECT r.*,"
    + ",".join(
        f"{alias}.{field} AS {alias}_{field}"
        for alias in ("e", "c", "s")
        for field in _IDENTITY_FIELDS
    )
    + " FROM records r LEFT JOIN entities e ON e.cmt_id=r.cmt_id"
    + " LEFT JOIN entities c ON c.cmt_id=e.card_id"
    + " LEFT JOIN entities s ON s.cmt_id=COALESCE(c.set_id,e.set_id)"
    + " WHERE r.batch_id=? ORDER BY r.record_index LIMIT 1001"
)


def _snapshot_target(row: sqlite3.Row, cache: dict[str, tuple[Entity, Entity | None]]) -> None:
    """Check stored identity closure, without consulting or recreating bindings."""
    if row["status"] != "accepted":
        return
    target_id = row["cmt_id"]
    if target_id not in cache:
        projections = [
            {field: row[f"{alias}_{field}"] for field in _IDENTITY_FIELDS}
            for alias in ("e", "c", "s")
            if row[f"{alias}_cmt_id"] is not None
        ]
        try:
            identities = parse_manifest({"version": 1, "entities": projections, "bindings": []})
        except CatalogError:
            raise DiscoveryError("storage_corrupt") from None
        by_id = {entity.cmt_id: entity for entity in identities.entities}
        target = by_id.get(target_id)
        if target is None:
            raise DiscoveryError("storage_corrupt")
        cache[target_id] = target, by_id.get(target.card_id or "")
    target, card = cache[target_id]
    expected_kind = "printing" if row["kind"] == "card" else row["kind"]
    if target.kind != expected_kind:
        raise DiscoveryError("storage_corrupt")
    if row["kind"] in ("card", "sealed") and target.language != row["language"]:
        raise DiscoveryError("storage_corrupt")
    if row["kind"] == "card" and (
        target.variant != row["variant"] or card is None or card.card_number != row["card_number"]
    ):
        raise DiscoveryError("storage_corrupt")


def read_snapshots(
    path: Path, batch_ids: tuple[str, ...], *, timeout: float = DEFAULT_TIMEOUT
) -> tuple[BatchSnapshot, ...]:
    """Read complete selected batch evidence in one owned, bounded read transaction."""
    if not isinstance(batch_ids, tuple):
        raise DiscoveryError("invalid_shape")
    if not 1 <= len(batch_ids) <= 33:
        raise DiscoveryError("input_limit")
    try:
        tokens = tuple(uuid_value(value) for value in batch_ids)
    except CatalogError as error:
        raise DiscoveryError(error.category) from None
    if len(set(tokens)) != len(tokens):
        raise DiscoveryError("invalid_field")
    snapshots: list[BatchSnapshot] = []
    with _connection(path, writable=False, timeout=timeout) as (connection, budget):
        _execute(connection, budget, "BEGIN")
        try:
            _require_schema(connection, budget)
            # One error is sufficient; do not materialize a hostile FK error inventory.
            integrity = _execute(connection, budget, "PRAGMA integrity_check(1)").fetchone()
            foreign_key = _execute(connection, budget, "PRAGMA foreign_key_check").fetchone()
            if integrity is None or tuple(integrity) != ("ok",) or foreign_key is not None:
                raise DiscoveryError("storage_corrupt")
            total = 0
            identities: dict[str, tuple[Entity, Entity | None]] = {}
            for token in sorted(tokens):
                metadata = _execute(
                    connection, budget, "SELECT * FROM batches WHERE batch_id=?", (token,)
                ).fetchone()
                if metadata is None:
                    raise DiscoveryError("batch_missing")
                admission = None
                if _execute(connection, budget, "PRAGMA user_version").fetchone()[0] == 2:
                    admission = _execute(
                        connection, budget, "SELECT mode FROM captures WHERE batch_id=?", (token,)
                    ).fetchone()
                    if admission is None:
                        raise DiscoveryError("storage_corrupt")
                    if admission["mode"] == "pinned":
                        raise DiscoveryError("synthetic_only")
                rows = _execute(connection, budget, _SNAPSHOT_JOIN, (token,)).fetchall()
                total += len(rows)
                if len(rows) > MAX_LIMIT or total > 33000:
                    raise DiscoveryError("input_limit")
                if any(row["provenance"] not in (None, "synthetic") for row in rows):
                    raise DiscoveryError("synthetic_only")
                if admission is not None:
                    from .capture import _capture_row, _check_capture

                    # Validate retained v2 evidence within this same selected snapshot.
                    # Only stored resolver context is consulted; no current manifest.
                    try:
                        capture = _capture_row(connection, budget, token)
                        if capture is None:
                            raise DiscoveryError("storage_corrupt")
                        _check_capture(connection, budget, metadata, capture)
                    except PersistenceError as error:
                        raise DiscoveryError(error.category) from None
                for row in rows:
                    budget.remaining()
                    _snapshot_target(row, identities)
                snapshot = BatchSnapshot(
                    version=1,
                    input_version=metadata["input_version"],
                    resolver_version=metadata["resolver_version"],
                    batch_id=metadata["batch_id"],
                    captured_at=metadata["captured_at"],
                    first_persisted_at=metadata["first_persisted_at"],
                    fingerprint=metadata["fingerprint"],
                    context_fingerprint=metadata["context_fingerprint"],
                    input_count=metadata["input_count"],
                    accepted_count=metadata["accepted_count"],
                    candidate_count=metadata["candidate_count"],
                    rejected_count=metadata["rejected_count"],
                    result=metadata["result"],
                    records=tuple(_snapshot_record(row) for row in rows),
                )
                snapshots.append(validate_snapshot(snapshot))
                budget.remaining()
            budget.remaining()
        finally:
            # Cleanup works even when the deadline/VM progress callback has expired.
            connection.set_progress_handler(None, 0)
            connection.execute("PRAGMA busy_timeout=0")
            if connection.in_transaction:
                connection.execute("ROLLBACK")
        budget.remaining()
    return tuple(snapshots)


def read_scoped_snapshots(
    path: Path, request: ScopedDiscoveryRequest, *, timeout: float = DEFAULT_TIMEOUT
) -> tuple[ScopedCapture, ...]:
    """Version2 preserves its original R0-only pinned admission."""
    return cast(tuple[ScopedCapture, ...], _read_scoped_window(path, request, timeout=timeout))


def read_multi_revision_snapshots(
    path: Path, request: MultiRevisionRequest, *, timeout: float = DEFAULT_TIMEOUT
) -> tuple[ProfiledCapture, ...]:
    """Read and profile-authorize the complete window in one read transaction."""
    from ..discovery.multi_input import validate_request

    validated = validate_request(request)
    return cast(
        tuple[ProfiledCapture, ...],
        _read_scoped_window(
            path, validated.scoped_request(), timeout=timeout, profile=validated.profile
        ),
    )


def _read_scoped_window(
    path: Path,
    request: ScopedDiscoveryRequest,
    *,
    timeout: float,
    profile: str | None = None,
) -> tuple[ScopedCapture | ProfiledCapture, ...]:
    """Reconstruct complete v2 captures in one owned read-only SQLite snapshot.

    Scope selection belongs to the pure comparator, after every row and unit in
    every requested capture has passed retained-admission validation here.
    """
    from ..discovery.multi_models import (
        REVIEWED_PAIR_PROFILE,
        SYNTHETIC_PROFILE,
        _validated_profile_capture,
    )
    from ..discovery.scoped_errors import ScopedDiscoveryError
    from ..discovery.scoped_input import validate_request
    from ..discovery.scoped_models import _validated_storage_capture
    from ..discovery.scoped_snapshot import validate_scoped_snapshot
    from .capture import _capture_row, _check_capture
    from .input import canonical_json

    validated = validate_request(request)
    tokens = tuple(sorted((validated.current.batch_id, *(s.batch_id for s in validated.history))))
    captures: list[ScopedCapture | ProfiledCapture] = []
    with _connection(path, writable=False, timeout=timeout) as (connection, budget):
        _execute(connection, budget, "BEGIN")
        try:
            _require_schema(connection, budget)
            if _execute(connection, budget, "PRAGMA user_version").fetchone()[0] != 2:
                raise ScopedDiscoveryError("unsupported_evidence")
            _check_integrity(connection, budget)
            total = 0
            identities: dict[str, tuple[Entity, Entity | None]] = {}
            for token in tokens:
                metadata = _execute(
                    connection, budget, "SELECT * FROM batches WHERE batch_id=?", (token,)
                ).fetchone()
                if metadata is None:
                    raise DiscoveryError("batch_missing")
                capture = _capture_row(connection, budget, token)
                if capture is None:
                    raise DiscoveryError("storage_corrupt")
                mode, state = capture["mode"], capture["evidence_state"]
                states = {
                    "legacy": "legacy_unverified",
                    "synthetic": "producer_declared",
                    "pinned": "verified_local_pinned_bundle",
                }
                if mode not in states or state != states[mode]:
                    raise DiscoveryError("storage_corrupt")
                if mode == "legacy":
                    raise ScopedDiscoveryError("unsupported_evidence")
                rows = _execute(connection, budget, _SNAPSHOT_JOIN, (token,)).fetchall()
                total += len(rows)
                if len(rows) > MAX_LIMIT or total > 33_000:
                    raise DiscoveryError("input_limit")
                provenance = "observed" if mode == "pinned" else "synthetic"
                if any(
                    row["provenance"] != (None if row["status"] == "rejected" else provenance)
                    for row in rows
                ):
                    raise DiscoveryError("storage_corrupt")
                # This independently rebuilds the admitted pinned package or
                # synthetic scope, resolution, partition, counters and snapshots.
                envelope = _check_capture(connection, budget, metadata, capture)
                extraction_proof: object = None
                if profile is None:
                    if envelope["version"] != 1:
                        raise ScopedDiscoveryError("unsupported_evidence")
                elif profile == REVIEWED_PAIR_PROFILE:
                    if mode != "pinned":
                        raise ScopedDiscoveryError("unsupported_evidence")
                    # Full package membership is checked from the reconstructed
                    # envelope, never from requested profile or claimed scope hash.
                    from ..pinned_repository.bundle_v2 import (
                        extraction_evidence_v2,
                        validate_bundle_v2,
                    )

                    extraction_proof = extraction_evidence_v2(
                        validate_bundle_v2(envelope["bundle"])
                    )
                elif profile == SYNTHETIC_PROFILE:
                    if mode != "synthetic":
                        raise ScopedDiscoveryError("unsupported_evidence")
                else:
                    raise ScopedDiscoveryError("unsupported_evidence")
                for row in rows:
                    budget.remaining()
                    _snapshot_target(row, identities)
                snapshot = BatchSnapshot(
                    version=1,
                    records=tuple(_snapshot_record(row) for row in rows),
                    **{
                        field: metadata[field]
                        for field in (
                            "input_version",
                            "resolver_version",
                            "batch_id",
                            "captured_at",
                            "first_persisted_at",
                            "fingerprint",
                            "context_fingerprint",
                            "input_count",
                            "accepted_count",
                            "candidate_count",
                            "rejected_count",
                            "result",
                        )
                    },
                )
                snapshot = validate_scoped_snapshot(snapshot, provenance=provenance)
                validated_capture = _validated_storage_capture(
                    snapshot,
                    mode,
                    state,
                    canonical_json(envelope["scope"]),
                    capture["capture_fingerprint"],
                )
                captures.append(
                    validated_capture
                    if profile is None
                    else _validated_profile_capture(validated_capture, profile, extraction_proof)
                )
                budget.remaining()
        finally:
            # Cleanup remains possible after an expired deadline/progress callback.
            connection.set_progress_handler(None, 0)
            connection.execute("PRAGMA busy_timeout=0")
            if connection.in_transaction:
                connection.execute("ROLLBACK")
        budget.remaining()
    return tuple(captures)


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
            version = _execute(connection, budget, "PRAGMA user_version").fetchone()[0]
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
        return _ok(version)
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


def migrate(
    path: Path, destination: Path, *, timeout: float = DEFAULT_TIMEOUT
) -> dict[str, object]:
    """Explicit atomic v1->v2, with an exclusively reserved verified v1 backup."""
    target: Path | None = None
    owned: tuple[int, int] | None = None
    verified_backup = False
    try:
        with _connection(path, writable=True, timeout=timeout) as (connection, budget):
            _require_schema(connection, budget)
            if _execute(connection, budget, "PRAGMA user_version").fetchone()[0] != 1:
                raise PersistenceError("storage_schema")
            _execute(connection, budget, "PRAGMA synchronous=FULL")
            _execute(connection, budget, "BEGIN EXCLUSIVE")
            try:
                _verify(connection, budget)
                target = _checked_path(destination)
                if _exists(target):
                    raise PersistenceError("unsafe_destination")
                owned = _reserve(target)
                information = _unsafe_stat(target, file=True)
                if (information.st_dev, information.st_ino) != owned:
                    raise PersistenceError("unsafe_destination")
                # BEGIN EXCLUSIVE + DELETE journal keeps main bytes stable before DDL.
                with path.open("rb") as source, target.open("r+b") as backup_file:
                    while chunk := source.read(1024 * 1024):
                        budget.remaining()
                        backup_file.write(chunk)
                    backup_file.flush()
                    os.fsync(backup_file.fileno())
                with _connection(target, writable=False, timeout=budget.remaining()) as (
                    copy,
                    remaining,
                ):
                    _verify(copy, remaining)
                    if _execute(copy, remaining, "PRAGMA user_version").fetchone()[0] != 1:
                        raise PersistenceError("storage_corrupt")
                verified_backup = True
                # Rebuild only the provenance CHECK; copied rows/fingerprints are unchanged.
                for name in (
                    "record_context",
                    "record_order",
                    "record_target",
                    "candidate_context",
                ):
                    kind = "TRIGGER" if name == "record_context" else "INDEX"
                    _execute(connection, budget, f"DROP {kind} {name}")
                _execute(connection, budget, "ALTER TABLE records RENAME TO records_v1")
                record_sql = next(
                    statement
                    for statement in schema.STATEMENTS
                    if statement.startswith("CREATE TABLE records")
                )
                _execute(connection, budget, record_sql)
                _execute(connection, budget, "INSERT INTO records SELECT * FROM records_v1")
                _execute(connection, budget, "DROP TABLE records_v1")
                for statement in schema.STATEMENTS:
                    if (
                        statement.startswith("CREATE TRIGGER record_context")
                        or statement.startswith("CREATE INDEX record_")
                        or statement.startswith("CREATE INDEX candidate_context")
                        or statement.startswith("CREATE TABLE captures")
                        or statement.startswith("CREATE TRIGGER capture_")
                    ):
                        _execute(connection, budget, statement)
                _execute(connection, budget, "DROP TABLE storage_metadata")
                _execute(connection, budget, schema.STATEMENTS[0])
                _execute(
                    connection,
                    budget,
                    "INSERT INTO storage_metadata VALUES (?,?,?)",
                    (1, schema.OWNER, 2),
                )
                from .capture import store_legacy

                cursor = _execute(
                    connection, budget, "SELECT batch_id FROM batches ORDER BY batch_id"
                )
                for row in cursor:
                    store_legacy(connection, budget, row[0])
                _execute(connection, budget, "PRAGMA user_version=2")
                _verify(connection, budget)
                _execute(connection, budget, "COMMIT")
            except BaseException:
                connection.set_progress_handler(None, 0)
                connection.execute("PRAGMA busy_timeout=0")
                if connection.in_transaction:
                    connection.execute("ROLLBACK")
                raise
        return _ok(2)
    except OSError:
        raise PersistenceError("storage_io") from None
    finally:
        # A verified original backup survives any migration failure.
        if not verified_backup and target is not None and owned is not None:
            _remove_owned(target, owned)
