"""Independent CMTY persistence with verified immutable previews and exclusive recovery."""

from __future__ import annotations

import base64
import binascii
import json
import os
import re
import sqlite3
import stat
import uuid
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from ..catalog.validation import CatalogError, _constant, _pairs, _preflight
from ..persistence import sqlite_repository as paths
from ..persistence.errors import PersistenceError
from ..watchlist.errors import WatchlistError
from ..watchlist_journal.errors import JournalError
from ..watchlist_journal.storage import Budget
from . import policy, schema
from .errors import OutboxError

DEFAULT_TIMEOUT = 2.0
MAX_PAGE_BYTES = 1048576
MAX_LIMIT = 1000
MAX_CELL_BYTES = 262144
_ALERT_FIELDS = (
    "alert_id",
    "destination_key",
    "signal_id",
    "policy_version",
    "renderer_version",
    "channel",
    "state",
    "intent_json",
    "intent_sha256",
    "message_text",
    "message_sha256",
    "first_prepared_at",
)
_PREPARED_FIELDS = _ALERT_FIELDS[:-1] + ("evidence_json", "evidence_sha256")
_STAMP = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z")


@contextmanager
def _errors() -> Iterator[None]:
    """Translate category-bearing boundaries without leaking SQLite or OS diagnostics."""
    try:
        yield
    except (PersistenceError, WatchlistError, JournalError) as error:
        raise OutboxError(error.category) from None
    except sqlite3.Error as error:
        code = getattr(error, "sqlite_errorcode", 0) & 0xFF
        category = {
            sqlite3.SQLITE_BUSY: "storage_locked",
            sqlite3.SQLITE_LOCKED: "storage_locked",
            sqlite3.SQLITE_CORRUPT: "storage_corrupt",
            sqlite3.SQLITE_NOTADB: "storage_corrupt",
            sqlite3.SQLITE_TOOBIG: "storage_corrupt",
            sqlite3.SQLITE_INTERRUPT: "storage_timeout",
            sqlite3.SQLITE_CONSTRAINT: "storage_corrupt",
        }.get(code, "storage_io")
        raise OutboxError(category) from None
    except OSError:
        raise OutboxError("storage_io") from None


def _sqlite_text(raw: bytes) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        raise OutboxError("storage_corrupt") from None


def _budget_for(timeout: float, supplied: Budget | None) -> Budget:
    budget = Budget(timeout) if supplied is None else supplied
    budget.remaining()
    return budget


def _path(value: Path, *, new: bool = False) -> Path:
    with _errors():
        target = paths._checked_path(value)
        exists = paths._exists(target)
        if new and exists:
            raise OutboxError("unsafe_destination")
        if not new and not exists:
            raise OutboxError("storage_missing")
        paths._check_sidecars(target, new=new)
        return target
    raise AssertionError("unreachable")


def _owned_header(path: Path, budget: Budget) -> tuple[int, int]:
    """Reject foreign physical ownership before SQLite can recover a wrong target."""
    target = _path(path)
    before = paths._unsafe_stat(target, file=True)
    identity = (before.st_dev, before.st_ino)
    budget.remaining()
    with target.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        if (opened.st_dev, opened.st_ino) != identity or opened.st_nlink != 1:
            raise OutboxError("unsafe_destination")
        header = stream.read(100)
    after = paths._unsafe_stat(target, file=True)
    if (after.st_dev, after.st_ino) != identity:
        raise OutboxError("unsafe_destination")
    budget.remaining()
    if len(header) != 100 or header[:16] != b"SQLite format 3\x00":
        raise OutboxError("storage_corrupt")
    if (
        int.from_bytes(header[68:72], "big") != schema.APPLICATION_ID
        or int.from_bytes(header[60:64], "big") != schema.SCHEMA_VERSION
    ):
        raise OutboxError("storage_schema")
    return identity


def reject_same_file(first: Path, second: Path) -> None:
    """Reject aliases before accessing a second owner's data."""
    with _errors():
        left, right = _path(first), _path(second)
        if left == right or os.path.samefile(left, right):
            raise OutboxError("unsafe_destination")


def _execute(
    db: sqlite3.Connection, budget: Budget, sql: str, values: tuple[object, ...] = ()
) -> sqlite3.Cursor:
    db.execute(f"PRAGMA busy_timeout={max(1, int(budget.remaining() * 1000))}")
    return db.execute(sql, values)


@contextmanager
def _connect(
    path: Path,
    budget: Budget,
    *,
    writable: bool = False,
    _expected_identity: tuple[int, int] | None = None,
) -> Iterator[sqlite3.Connection]:
    db: sqlite3.Connection | None = None
    with _errors():
        try:
            target = _path(path)
            before = target.lstat()
            if (
                _expected_identity is not None
                and (before.st_dev, before.st_ino) != _expected_identity
            ):
                raise OutboxError("unsafe_destination")
            db = sqlite3.connect(
                target.as_uri() + ("?mode=rw" if writable else "?mode=ro"),
                uri=True,
                autocommit=True,
                timeout=budget.remaining(),
            )
            after = paths._unsafe_stat(target, file=True)
            if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
                raise OutboxError("unsafe_destination")
            db.row_factory = sqlite3.Row
            db.text_factory = _sqlite_text
            db.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 524288)
            db.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH, 65536)
            db.set_progress_handler(budget.progress, 1000)
            db.setconfig(sqlite3.SQLITE_DBCONFIG_DEFENSIVE, True)
            _execute(db, budget, "PRAGMA trusted_schema=OFF")
            _execute(db, budget, "PRAGMA foreign_keys=ON")
            if _execute(db, budget, "PRAGMA foreign_keys").fetchone()[0] != 1:
                raise OutboxError("storage_schema")
            if writable:
                _execute(db, budget, "PRAGMA synchronous=FULL")
            else:
                _execute(db, budget, "PRAGMA query_only=ON")
            yield db
            budget.remaining()
        finally:
            if db is not None:
                db.close()


def _rollback(db: sqlite3.Connection) -> None:
    db.set_progress_handler(None, 0)
    with suppress(sqlite3.Error):
        db.execute("PRAGMA busy_timeout=0")
        if db.in_transaction:
            db.execute("ROLLBACK")


@contextmanager
def _transaction(db: sqlite3.Connection, budget: Budget, *, write: bool = False) -> Iterator[None]:
    _execute(db, budget, "BEGIN IMMEDIATE" if write else "BEGIN")
    try:
        yield
        if write:
            _execute(db, budget, "COMMIT")
    finally:
        _rollback(db)


def _text(column: str, maximum: int, minimum: int = 1) -> str:
    # Identifiers are internal constants, not input-controlled SQL.
    return (
        f"CASE WHEN typeof({column})='text' AND "
        f"length(CAST({column} AS BLOB)) BETWEEN {minimum} AND {maximum} "
        f"THEN {column} END"
    )


def _integer(column: str) -> str:
    return f"CASE WHEN typeof({column})='integer' THEN {column} END"


def _schema(db: sqlite3.Connection, budget: Budget) -> None:
    if (
        _execute(db, budget, "PRAGMA application_id").fetchone()[0] != schema.APPLICATION_ID
        or _execute(db, budget, "PRAGMA user_version").fetchone()[0] != 1
        or _execute(db, budget, "PRAGMA journal_mode").fetchone()[0] != "delete"
    ):
        raise OutboxError("storage_schema")
    expected = schema.expected_inventory()
    objects = _execute(
        db,
        budget,
        "SELECT "
        + ",".join(_text(column, 32768) for column in ("type", "name", "tbl_name"))
        + ",CASE WHEN sql IS NULL THEN NULL ELSE "
        + _text("sql", 32768)
        + " END FROM sqlite_master ORDER BY type,name LIMIT ?",
        (len(expected) + 1,),
    )
    actual: list[tuple[object, ...]] = []
    for row in objects:
        budget.remaining()
        actual.append(tuple(row))
    if tuple(actual) != expected:
        raise OutboxError("storage_schema")
    metadata = _execute(
        db,
        budget,
        "SELECT "
        + _integer("singleton")
        + ","
        + _text("owner", 128)
        + ","
        + _integer("schema_version")
        + " FROM watchlist_alert_metadata LIMIT 2",
    )
    if [tuple(row) for row in metadata] != [(1, schema.OWNER, 1)]:
        raise OutboxError("storage_schema")


def _integrity(db: sqlite3.Connection, budget: Budget) -> None:
    result = _execute(db, budget, "PRAGMA integrity_check(1)").fetchone()
    if result is None or result[0] != "ok":
        raise OutboxError("storage_corrupt")
    if _execute(db, budget, "PRAGMA foreign_key_check").fetchone() is not None:
        raise OutboxError("storage_corrupt")


def _decode(raw: object, maximum: int, budget: Budget) -> object:
    if type(raw) is not str:
        raise OutboxError("storage_corrupt")
    try:
        budget.remaining()
        if len(raw.encode("utf-8")) > maximum:
            raise OutboxError("storage_corrupt")
        _preflight(raw)
        value: object = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)
        budget.remaining()
        return value
    except (CatalogError, ValueError, RecursionError, UnicodeError) as error:
        if isinstance(error, (JournalError, OutboxError)) and error.category == "storage_timeout":
            raise OutboxError("storage_timeout") from None
        raise OutboxError("storage_corrupt") from None


def _json(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    )


def _stamp(value: object) -> str:
    if type(value) is not str or _STAMP.fullmatch(value) is None:
        raise OutboxError("storage_corrupt")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        raise OutboxError("storage_corrupt") from None
    return value


def _prepare_local(evidence: object, alias: object, budget: Budget) -> dict[str, object]:
    try:
        budget.remaining()
        return policy.prepare(evidence, alias, check=budget.remaining)
    except (OutboxError, WatchlistError, JournalError) as error:
        category = "storage_timeout" if error.category == "storage_timeout" else "storage_corrupt"
        raise OutboxError(category) from None


def _load_pair(
    db: sqlite3.Connection, budget: Budget, key: str
) -> tuple[dict[str, object], dict[str, object]] | None:
    bounds = (70, 64, 70, 64, 0, 32, 16, 65536, 64, 4096, 64, 27)
    columns = [
        _integer(column) if column == "renderer_version" else _text(column, maximum)
        for column, maximum in zip(_ALERT_FIELDS, bounds, strict=True)
    ]
    alert = _execute(
        db,
        budget,
        "SELECT " + ",".join(columns) + " FROM watchlist_alerts WHERE alert_id=?",
        (key,),
    ).fetchone()
    evidence = _execute(
        db,
        budget,
        "SELECT "
        + ",".join(
            (_text("alert_id", 70), _text("evidence_json", 262144), _text("evidence_sha256", 64))
        )
        + " FROM watchlist_alert_evidence WHERE alert_id=?",
        (key,),
    ).fetchone()
    if alert is None and evidence is None:
        return None
    if alert is None or evidence is None or any(value is None for value in (*alert, *evidence)):
        raise OutboxError("storage_corrupt")
    parsed = _decode(evidence[1], 262144, budget)
    prepared = _prepare_local(parsed, alert[1], budget)
    stored = dict(zip(_ALERT_FIELDS, alert, strict=True))
    stored.update(evidence_json=evidence[1], evidence_sha256=evidence[2])
    if (
        evidence[0] != key
        or prepared["alert_id"] != key
        or any(stored[field] != prepared[field] for field in _PREPARED_FIELDS)
        or type(stored["renderer_version"]) is not int
    ):
        raise OutboxError("storage_corrupt")
    prepared["first_prepared_at"] = _stamp(stored["first_prepared_at"])
    return prepared, cast(dict[str, object], parsed)


def _alert(prepared: dict[str, object], budget: Budget) -> dict[str, object]:
    return {
        **{field: prepared[field] for field in _ALERT_FIELDS if field not in ("intent_json",)},
        "intent": _decode(prepared["intent_json"], 65536, budget),
    }


def _response(
    operation: str, budget: Budget, *, result: object = "ok", **fields: object
) -> dict[str, object]:
    response = {"version": 1, "operation": operation, "result": result, **fields}
    budget.remaining()
    if len(_json(response).encode("ascii")) + 1 > MAX_PAGE_BYTES:
        raise OutboxError("input_limit")
    budget.remaining()
    return response


def _enqueue_verified(path: Path, receipt: object, budget: Budget) -> dict[str, object]:
    from .application import _consume_receipt

    with _errors():
        supplied = _consume_receipt(receipt, budget)
        evidence = _decode(supplied["evidence_json"], 262144, budget)
        expected = policy.prepare(evidence, supplied["destination_key"], check=budget.remaining)
        if _json(expected) != _json(supplied):
            raise OutboxError("unsupported_evidence")
        key = cast(str, expected["alert_id"])
        recorded = False
        physical_owner = _owned_header(path, budget)
        with (
            _connect(path, budget, writable=True, _expected_identity=physical_owner) as db,
            _transaction(db, budget, write=True),
        ):
            # Finish the existing semantic fold before classifying the new
            # candidate: preexisting corruption must never look like a conflict.
            _, entries, previous = _fold(db, budget, selected=key)
            duplicate = _execute(
                db,
                budget,
                "SELECT "
                + _text("alert_id", 70)
                + " FROM watchlist_alerts WHERE destination_key=? AND signal_id=? LIMIT 1",
                (expected["destination_key"], expected["signal_id"]),
            ).fetchone()
            if duplicate is not None and duplicate[0] != key:
                raise OutboxError("storage_corrupt")
            if previous is not None:
                if any(previous[0][field] != expected[field] for field in _PREPARED_FIELDS):
                    raise OutboxError("replay_conflict")
            else:
                entry_key, entry_json = _entry_identity(cast(dict[str, object], evidence), budget)
                if entry_key in entries and entries[entry_key] != entry_json:
                    raise OutboxError("identity_conflict")
                stamp = datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
                values = tuple(expected[field] for field in _ALERT_FIELDS[:-1]) + (_stamp(stamp),)
                _execute(
                    db,
                    budget,
                    "INSERT INTO watchlist_alerts VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    values,
                )
                _execute(
                    db,
                    budget,
                    "INSERT INTO watchlist_alert_evidence VALUES (?,?,?)",
                    (key, expected["evidence_json"], expected["evidence_sha256"]),
                )
                loaded = _load_pair(db, budget, key)
                if loaded is None:
                    raise OutboxError("storage_corrupt")
                _integrity(db, budget)
                recorded = True
            budget.remaining()
        return _response(
            "enqueue",
            budget,
            result="recorded" if recorded else "replayed",
            alert_id=key,
            signal_id=expected["signal_id"],
            destination_key=expected["destination_key"],
        )
    raise AssertionError("unreachable")


def _selected(
    path: Path, key: object, budget: Budget
) -> tuple[dict[str, object], dict[str, object]]:
    aid = policy.validate_id(key)
    with _connect(path, budget) as db, _transaction(db, budget):
        _schema(db, budget)
        _integrity(db, budget)
        loaded = _load_pair(db, budget, aid)
        if loaded is None:
            raise OutboxError("not_found")
        return loaded


def _get_pair(
    path: Path, alert_id: object, budget: Budget
) -> tuple[dict[str, object], dict[str, object]]:
    """Load one complete local pair for original recompute in a single read snapshot."""
    with _errors():
        prepared, evidence = _selected(path, alert_id, budget)
        return _alert(prepared, budget), evidence
    raise AssertionError("unreachable")


def get(
    path: Path, alert_id: object, *, timeout: float = DEFAULT_TIMEOUT, _budget: Budget | None = None
) -> dict[str, object]:
    with _errors():
        budget = _budget_for(timeout, _budget)
        prepared, _ = _selected(path, alert_id, budget)
        return _response("get", budget, alert=_alert(prepared, budget))
    raise AssertionError("unreachable")


def evidence_get(
    path: Path, alert_id: object, *, timeout: float = DEFAULT_TIMEOUT, _budget: Budget | None = None
) -> dict[str, object]:
    with _errors():
        budget = _budget_for(timeout, _budget)
        prepared, evidence = _selected(path, alert_id, budget)
        return _response(
            "evidence-get",
            budget,
            alert_id=prepared["alert_id"],
            evidence=evidence,
            evidence_sha256=prepared["evidence_sha256"],
        )
    raise AssertionError("unreachable")


def preview(
    path: Path, alert_id: object, *, timeout: float = DEFAULT_TIMEOUT, _budget: Budget | None = None
) -> dict[str, object]:
    with _errors():
        budget = _budget_for(timeout, _budget)
        prepared, _ = _selected(path, alert_id, budget)
        return _response(
            "preview",
            budget,
            **{
                key: prepared[key]
                for key in (
                    "alert_id",
                    "message_text",
                    "policy_version",
                    "renderer_version",
                    "channel",
                    "state",
                )
            },
        )
    raise AssertionError("unreachable")


def _entry_identity(evidence: dict[str, object], budget: Budget) -> tuple[tuple[str, int], str]:
    """Project an entry only after its complete evidence was reconstructed."""
    snapshot = cast(dict[str, object], cast(dict[str, object], evidence["current"])["snapshot"])
    entry = cast(dict[str, object], snapshot["entry"])
    key = (cast(str, entry["watch_id"]), cast(int, entry["revision"]))
    return key, policy.canonical(entry, check=budget.remaining)


def _fold(
    db: sqlite3.Connection, budget: Budget, *, selected: str | None = None
) -> tuple[
    dict[str, int],
    dict[tuple[str, int], str],
    tuple[dict[str, object], dict[str, object]] | None,
]:
    """Verify one snapshot fully, retaining only this operation's entry map/pair."""
    _schema(db, budget)
    _integrity(db, budget)
    count = 0
    entries: dict[tuple[str, int], str] = {}
    selected_pair = None
    for row in _execute(
        db, budget, "SELECT " + _text("alert_id", 70) + " FROM watchlist_alerts ORDER BY alert_id"
    ):
        budget.remaining()
        if type(row[0]) is not str:
            raise OutboxError("storage_corrupt")
        pair = _load_pair(db, budget, row[0])
        if pair is None:
            raise OutboxError("storage_corrupt")
        _, evidence = pair
        key, entry_json = _entry_identity(evidence, budget)
        if entries.setdefault(key, entry_json) != entry_json:
            raise OutboxError("storage_corrupt")
        if row[0] == selected:
            selected_pair = pair
        count += 1
    counts: dict[str, int] = {}
    for suffix in ("alerts", "evidence"):
        table = "watchlist_alerts" if suffix == "alerts" else "watchlist_alert_evidence"
        total = _execute(db, budget, "SELECT COUNT(*) FROM " + table).fetchone()[0]
        if type(total) is not int or total != count:
            raise OutboxError("storage_corrupt")
        counts[suffix] = total
    budget.remaining()
    return counts, entries, selected_pair


def _verify(db: sqlite3.Connection, budget: Budget) -> dict[str, int]:
    counts, _, _ = _fold(db, budget)
    return counts


def verify(
    path: Path, *, timeout: float = DEFAULT_TIMEOUT, _budget: Budget | None = None
) -> dict[str, object]:
    with _errors():
        budget = _budget_for(timeout, _budget)
        with _connect(path, budget) as db, _transaction(db, budget):
            counts = _verify(db, budget)
        return _response("verify", budget, level="local", counts=counts)
    raise AssertionError("unreachable")


def _encode_cursor(binding: dict[str, object], last: str) -> str:
    raw = _json({"version": 1, "filters": binding, "last_alert_id": last})
    return base64.urlsafe_b64encode(raw.encode("ascii")).decode("ascii")


def _cursor(value: object, binding: dict[str, object], budget: Budget) -> str:
    if (
        type(value) is not str
        or not 1 <= len(value) <= 2048
        or len(value) % 4
        or re.fullmatch(r"[A-Za-z0-9_-]+={0,2}", value) is None
    ):
        raise OutboxError("invalid_cursor")
    try:
        raw = base64.b64decode(value, altchars=b"-_", validate=True)
        if len(raw) > 1536:
            raise ValueError
        decoded = _decode(raw.decode("ascii"), 1536, budget)
        if (
            type(decoded) is not dict
            or set(decoded) != {"version", "filters", "last_alert_id"}
            or type(decoded["version"]) is not int
            or decoded["version"] != 1
            or _json(decoded["filters"]) != _json(binding)
        ):
            raise ValueError
        last = policy.validate_id(decoded["last_alert_id"])
        if _encode_cursor(binding, last) != value:
            raise ValueError
        return last
    except (ValueError, UnicodeError, binascii.Error) as error:
        if isinstance(error, (OutboxError, JournalError)) and error.category == "storage_timeout":
            raise OutboxError("storage_timeout") from None
        raise OutboxError("invalid_cursor") from None


def list_alerts(
    path: Path,
    *,
    destination_key: object = None,
    limit: object = 100,
    cursor: object = None,
    timeout: float = DEFAULT_TIMEOUT,
    _budget: Budget | None = None,
) -> dict[str, object]:
    with _errors():
        budget = _budget_for(timeout, _budget)
        if type(limit) is not int or not 1 <= limit <= MAX_LIMIT:
            raise OutboxError("invalid_field")
        alias = None if destination_key is None else policy.destination(destination_key)
        binding: dict[str, object] = {"destination_key": alias}
        last = "" if cursor is None else _cursor(cursor, binding, budget)
        items: list[dict[str, object]] = []
        more = False
        with _connect(path, budget) as db, _transaction(db, budget):
            _schema(db, budget)
            _integrity(db, budget)
            sql = "SELECT " + _text("alert_id", 70) + " FROM watchlist_alerts WHERE alert_id>?"
            values: tuple[object, ...] = (last,)
            if alias is not None:
                sql += " AND destination_key=?"
                values += (alias,)
            rows = _execute(db, budget, sql + " ORDER BY alert_id LIMIT ?", values + (limit + 1,))
            for row in rows:
                budget.remaining()
                if type(row[0]) is not str:
                    raise OutboxError("storage_corrupt")
                if len(items) == limit:
                    more = True
                    break
                pair = _load_pair(db, budget, row[0])
                if pair is None:
                    raise OutboxError("storage_corrupt")
                summary = {
                    key: value
                    for key, value in _alert(pair[0], budget).items()
                    if key not in ("intent", "message_text")
                }
                prospective = {
                    "version": 1,
                    "operation": "list",
                    "result": "ok",
                    "items": [*items, summary],
                    "next_cursor": _encode_cursor(binding, row[0]),
                }
                if len(_json(prospective).encode("ascii")) + 1 > MAX_PAGE_BYTES:
                    if not items:
                        raise OutboxError("input_limit")
                    more = True
                    break
                items.append(summary)
        next_cursor = _encode_cursor(binding, cast(str, items[-1]["alert_id"])) if more else None
        return _response("list", budget, items=items, next_cursor=next_cursor)
    raise AssertionError("unreachable")


def _cleanup_reserved(path: Path, identity: tuple[int, int]) -> None:
    with suppress(OSError, PersistenceError):
        information = paths._unsafe_stat(path, file=True)
        if (information.st_dev, information.st_ino) != identity:
            return
        if any(paths._exists(sidecar) for sidecar in paths._sidecars(path)):
            return
        path.unlink()


def initialize(
    path: Path, *, timeout: float = DEFAULT_TIMEOUT, _budget: Budget | None = None
) -> dict[str, object]:
    identity: tuple[int, int] | None = None
    completed = False
    with _errors():
        budget = _budget_for(timeout, _budget)
        target = _path(path, new=True)
        try:
            identity = paths._reserve(target)
            with _connect(target, budget, writable=True) as db:
                information = paths._unsafe_stat(target, file=True)
                if (information.st_dev, information.st_ino) != identity:
                    raise OutboxError("unsafe_destination")
                with _transaction(db, budget, write=True):
                    for statement in schema.STATEMENTS:
                        _execute(db, budget, statement)
                    _execute(
                        db,
                        budget,
                        "INSERT INTO watchlist_alert_metadata VALUES (?,?,?)",
                        (1, schema.OWNER, 1),
                    )
                    _execute(db, budget, f"PRAGMA application_id={schema.APPLICATION_ID}")
                    _execute(db, budget, "PRAGMA user_version=1")
                    _verify(db, budget)
            completed = True
            return _response("init", budget, schema_version=1)
        finally:
            if not completed and identity is not None:
                _cleanup_reserved(target, identity)
    raise AssertionError("unreachable")


def _rollback_publication(provisional: Path, destination: Path, identity: tuple[int, int]) -> None:
    with suppress(OSError):
        for name in (provisional, destination):
            information = name.lstat()
            if (
                (information.st_dev, information.st_ino) != identity
                or information.st_nlink != 2
                or not stat.S_ISREG(information.st_mode)
                or getattr(information, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
                or any(paths._exists(sidecar) for sidecar in paths._sidecars(name))
            ):
                return
        destination.unlink()


def _publish(provisional: Path, destination: Path, identity: tuple[int, int]) -> None:
    target = _path(destination, new=True)
    information = paths._unsafe_stat(provisional, file=True)
    if (information.st_dev, information.st_ino) != identity:
        raise OutboxError("unsafe_destination")
    if any(paths._exists(sidecar) for sidecar in paths._sidecars(provisional)):
        raise OutboxError("unsafe_destination")
    try:
        os.link(provisional, target)
    except FileExistsError:
        raise OutboxError("unsafe_destination") from None
    try:
        provisional.unlink()
    except OSError:
        _rollback_publication(provisional, target, identity)
        raise


def _fsync(provisional: Path, identity: tuple[int, int]) -> None:
    information = paths._unsafe_stat(provisional, file=True)
    if (information.st_dev, information.st_ino) != identity or any(
        paths._exists(sidecar) for sidecar in paths._sidecars(provisional)
    ):
        raise OutboxError("unsafe_destination")
    descriptor = os.open(provisional, os.O_RDWR | getattr(os, "O_NOFOLLOW", 0))
    try:
        opened = os.fstat(descriptor)
        if (
            (opened.st_dev, opened.st_ino) != identity
            or opened.st_nlink != 1
            or not stat.S_ISREG(opened.st_mode)
        ):
            raise OutboxError("unsafe_destination")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _copy(source: Path, destination: Path, operation: str, budget: Budget) -> dict[str, object]:
    provisional: Path | None = None
    identity: tuple[int, int] | None = None
    completed = False
    with _errors():
        try:
            target = _path(destination, new=True)
            budget.remaining()
            with _connect(source, budget) as reader, _transaction(reader, budget):
                _verify(reader, budget)
                provisional = target.parent / (
                    ".cmt-watchlist-alert-outbox-" + uuid.uuid4().hex + ".tmp"
                )
                _path(provisional, new=True)
                identity = paths._reserve(provisional)
                with _connect(provisional, budget, writable=True) as writer:
                    information = paths._unsafe_stat(provisional, file=True)
                    if (information.st_dev, information.st_ino) != identity:
                        raise OutboxError("unsafe_destination")
                    reader.execute("PRAGMA busy_timeout=0")
                    writer.execute("PRAGMA busy_timeout=0")

                    def progress(status: int, remaining: int, total: int) -> None:
                        budget.remaining()

                    reader.backup(writer, pages=32, progress=progress, sleep=0.01)
                    with _transaction(writer, budget):
                        counts = _verify(writer, budget)
            with _connect(provisional, budget) as reopened, _transaction(reopened, budget):
                if _verify(reopened, budget) != counts:
                    raise OutboxError("storage_corrupt")
            budget.remaining()
            _fsync(provisional, identity)
            budget.remaining()
            _publish(provisional, target, identity)
            completed = True
            budget.remaining()
            return _response(operation, budget, counts=counts)
        finally:
            if not completed and identity is not None and provisional is not None:
                _cleanup_reserved(provisional, identity)
    raise AssertionError("unreachable")


def backup(
    source: Path,
    destination: Path,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    _budget: Budget | None = None,
) -> dict[str, object]:
    with _errors():
        return _copy(source, destination, "backup", _budget_for(timeout, _budget))
    raise AssertionError("unreachable")


def restore(
    source: Path,
    destination: Path,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    _budget: Budget | None = None,
) -> dict[str, object]:
    with _errors():
        return _copy(source, destination, "restore", _budget_for(timeout, _budget))
    raise AssertionError("unreachable")
