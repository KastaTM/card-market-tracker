"""Owned offline alert outbox: bounded SQLite reads and atomic evidence associations."""

import hashlib
import io
import json
import math
import os
import re
import sqlite3
import time
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from ..persistence import sqlite_repository as paths
from ..persistence.errors import PersistenceError
from . import schema
from .errors import OutboxError

DEFAULT_TIMEOUT = 2.0
MAX_INTENT_BYTES = 64 * 1024
MAX_MESSAGE_BYTES = 4096
MAX_PREPARED_BYTES = 16 * 1024 * 1024
MAX_RESULT_BYTES = 16 * 1024 * 1024
MAX_PAGE_BYTES = 1024 * 1024
MAX_EVENTS = 1000
MAX_LIMIT = 1000
_HEX = re.compile(r"[0-9a-f]{64}")
_STAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z")


class Budget:
    """One monotonic deadline shared by original-evidence admission and outbox SQL."""

    def __init__(self, timeout: float = DEFAULT_TIMEOUT) -> None:
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 5:
            raise OutboxError("invalid_field")
        self.deadline = time.monotonic() + timeout

    def remaining(self) -> float:
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise OutboxError("storage_timeout")
        return remaining

    def progress(self) -> int:
        return int(time.monotonic() >= self.deadline)


def canonical_json(value: object) -> str:
    try:
        return json.dumps(
            value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise OutboxError("storage_corrupt") from None


def bounded_canonical_json(value: object, maximum: int, budget: Budget) -> str:
    """Enforce the ASCII byte ceiling before joining the encoded result."""
    encoder = json.JSONEncoder(
        ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    size = 0
    try:
        with io.StringIO() as output:
            for chunk in encoder.iterencode(value):
                budget.remaining()
                size += len(chunk)
                if size > maximum:
                    raise OutboxError("input_limit")
                output.write(chunk)
            return output.getvalue()
    except OutboxError:
        raise
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise OutboxError("storage_corrupt") from None


def _token(value: object, prefix: str) -> str:
    if type(value) is not str or not value.startswith(prefix) or not _HEX.fullmatch(value[5:]):
        raise OutboxError("invalid_field")
    return value


def _stamp(value: object) -> str:
    if type(value) is not str or not _STAMP.fullmatch(value):
        raise OutboxError("storage_corrupt")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        raise OutboxError("storage_corrupt") from None
    return value


def _path(value: Path, *, new: bool = False) -> Path:
    try:
        path = paths._checked_path(value)
        exists = paths._exists(path)
        if new and exists:
            raise OutboxError("unsafe_destination")
        if not new and not exists:
            raise OutboxError("storage_missing")
        paths._check_sidecars(path, new=new)
        return path
    except PersistenceError as error:
        raise OutboxError(error.category) from None
    except OSError:
        raise OutboxError("storage_io") from None


def reject_same_file(first: Path, second: Path) -> None:
    """Validate both existing paths before capture IO; aliases never cross owners."""
    left, right = _path(first), _path(second)
    try:
        if os.path.samefile(left, right):
            raise OutboxError("unsafe_destination")
    except OSError:
        raise OutboxError("storage_io") from None


def _execute(
    db: sqlite3.Connection, budget: Budget, sql: str, values: tuple[object, ...] = ()
) -> sqlite3.Cursor:
    db.execute(f"PRAGMA busy_timeout={max(1, int(budget.remaining() * 1000))}")
    return db.execute(sql, values)


@contextmanager
def _connect(path: Path, budget: Budget, *, writable: bool = False) -> Iterator[sqlite3.Connection]:
    db: sqlite3.Connection | None = None
    try:
        target = _path(path)
        before = target.lstat()
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
        # Final row values also have SQL guards. This independent ceiling prevents
        # SQLite from materializing hostile cells while evaluating corrupt input.
        db.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 2 * MAX_RESULT_BYTES)
        db.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH, 65536)
        db.set_progress_handler(budget.progress, 1000)
        db.setconfig(sqlite3.SQLITE_DBCONFIG_DEFENSIVE, True)
        _execute(db, budget, "PRAGMA trusted_schema=OFF")
        _execute(db, budget, "PRAGMA foreign_keys=ON")
        if _execute(db, budget, "PRAGMA foreign_keys").fetchone()[0] != 1:
            raise OutboxError("storage_schema")
        if not writable:
            _execute(db, budget, "PRAGMA query_only=ON")
        yield db
        budget.remaining()
    except PersistenceError as error:
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
        }.get(code, "storage_io")
        raise OutboxError(category) from None
    except OSError:
        raise OutboxError("storage_io") from None
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
    """Only internal column constants enter this SQL expression; never user identifiers."""
    return (
        f"CASE WHEN typeof({column})='text' AND "
        f"length(CAST({column} AS BLOB)) BETWEEN {minimum} AND {maximum} "
        f"THEN {column} END"
    )


def _version_integer(column: str) -> str:
    """Reject hostile TEXT in numeric version cells before returning it to Python."""
    return f"CASE WHEN typeof({column})='integer' AND {column}=1 THEN {column} END"


def _schema(db: sqlite3.Connection, budget: Budget) -> None:
    if (
        _execute(db, budget, "PRAGMA application_id").fetchone()[0] != schema.APPLICATION_ID
        or _execute(db, budget, "PRAGMA user_version").fetchone()[0] != schema.SCHEMA_VERSION
        or _execute(db, budget, "PRAGMA journal_mode").fetchone()[0] != "delete"
    ):
        raise OutboxError("storage_schema")
    expected = schema.expected_inventory()
    objects: list[tuple[object, ...]] = []
    query = _execute(
        db,
        budget,
        "SELECT "
        + ",".join(_text(column, 32768) for column in ("type", "name", "tbl_name"))
        + ",CASE WHEN sql IS NULL THEN NULL ELSE "
        + _text("sql", 32768)
        + " END FROM sqlite_master ORDER BY type,name LIMIT ?",
        (len(expected) + 1,),
    )
    for row in query:
        budget.remaining()
        objects.append(tuple(row))
    if tuple(objects) != expected:
        raise OutboxError("storage_schema")
    metadata = _execute(
        db,
        budget,
        "SELECT "
        + _version_integer("singleton")
        + ","
        + _text("owner", 128)
        + ","
        + _version_integer("schema_version")
        + " FROM outbox_metadata LIMIT 2",
    )
    if [tuple(row) for row in metadata] != [(1, schema.OWNER, schema.SCHEMA_VERSION)]:
        raise OutboxError("storage_schema")


def _integrity(db: sqlite3.Connection, budget: Budget) -> None:
    # The one-result limit avoids unbounded corruption diagnostics.
    result = _execute(db, budget, "PRAGMA integrity_check(1)").fetchone()
    if result is None or result[0] != "ok":
        raise OutboxError("storage_corrupt")
    if _execute(db, budget, "PRAGMA foreign_key_check").fetchone() is not None:
        raise OutboxError("storage_corrupt")


_ALERT_FIELDS = (
    "alert_id",
    "destination_key",
    "event_id",
    "channel",
    "policy_version",
    "renderer_version",
    "intent_json",
    "intent_sha256",
    "message_text",
    "message_sha256",
)
_ROW_FIELDS = _ALERT_FIELDS + ("event_json", "event_sha256")


def _decode(raw: str, maximum: int, budget: Budget) -> object:
    from ..discovery.journal_errors import JournalError
    from ..discovery.journal_validation import decode_json

    try:
        return decode_json(raw, maximum=maximum, check=budget.remaining)
    except JournalError as error:
        raise OutboxError(error.category) from None


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _load_alert(db: sqlite3.Connection, aid: str, budget: Budget) -> dict[str, object] | None:
    from .policy import alert_id, destination, validate_intent
    from .render import render

    bounds = (69, 64, 69, 32, 64, 0, MAX_INTENT_BYTES, 64, MAX_MESSAGE_BYTES, 64, 27, 16)
    fields = _ALERT_FIELDS + ("first_prepared_at", "state")
    columns = [
        _version_integer(field) if field == "renderer_version" else _text(field, bound)
        for field, bound in zip(fields, bounds, strict=True)
    ]
    row = _execute(
        db, budget, "SELECT " + ",".join(columns) + " FROM alerts WHERE alert_id=?", (aid,)
    ).fetchone()
    if row is None:
        return None
    if any(type(value) is not (int if index == 5 else str) for index, value in enumerate(row)):
        raise OutboxError("storage_corrupt")
    item = dict(zip(fields, row, strict=True))
    try:
        intent = validate_intent(_decode(cast(str, item["intent_json"]), MAX_INTENT_BYTES, budget))
        if (
            item["alert_id"] != aid
            or alert_id(destination(item["destination_key"]), item["event_id"]) != aid
            or item["event_id"] != intent["event_id"]
            or any(
                item[key] != intent[key]
                for key in ("channel", "policy_version", "renderer_version")
            )
            or bounded_canonical_json(intent, MAX_INTENT_BYTES, budget) != item["intent_json"]
            or _digest(cast(str, item["intent_json"])) != item["intent_sha256"]
            or render(intent) != item["message_text"]
            or _digest(cast(str, item["message_text"])) != item["message_sha256"]
            or item["state"] != "pending"
        ):
            raise OutboxError("storage_corrupt")
        _stamp(item["first_prepared_at"])
    except OutboxError as error:
        if error.category == "storage_timeout":
            raise
        raise OutboxError("storage_corrupt") from None
    budget.remaining()
    return {**item, "intent": intent}


def _load_evidence(
    db: sqlite3.Connection, alert: dict[str, object], cid: str, budget: Budget
) -> dict[str, object] | None:
    from .policy import prepare_event

    row = _execute(
        db,
        budget,
        "SELECT "
        + ",".join(
            (
                _text("event_json", MAX_RESULT_BYTES, 2),
                _text("journal_content_sha256", 64, 64),
                _text("event_sha256", 64, 64),
            )
        )
        + " FROM alert_evidence WHERE alert_id=? AND comparison_id=?",
        (alert["alert_id"], cid),
    ).fetchone()
    if row is None:
        return None
    if any(type(value) is not str for value in row):
        raise OutboxError("storage_corrupt")
    event_json, journal_digest, event_digest = tuple(row)
    # A comparison has one frozen journal digest even when its events are
    # associated with several alerts or destinations. Compare in SQL without
    # materializing potentially hostile sibling cells.
    if (
        _execute(
            db,
            budget,
            "SELECT 1 FROM alert_evidence WHERE comparison_id=? AND "
            "(typeof(journal_content_sha256)!='text' OR "
            "length(CAST(journal_content_sha256 AS BLOB))!=64 OR "
            "journal_content_sha256!=?) LIMIT 1",
            (cid, journal_digest),
        ).fetchone()
        is not None
    ):
        raise OutboxError("storage_corrupt")
    try:
        event = _decode(event_json, MAX_RESULT_BYTES, budget)
        expected = prepare_event(
            event, cast(str, alert["destination_key"]), cid, check=budget.remaining
        )
        if (
            not _HEX.fullmatch(journal_digest)
            or _digest(event_json) != event_digest
            or expected["event_json"] != event_json
            or expected["event_sha256"] != event_digest
            or any(expected[key] != alert[key] for key in _ALERT_FIELDS)
        ):
            raise OutboxError("storage_corrupt")
    except OutboxError as error:
        if error.category == "storage_timeout":
            raise
        raise OutboxError("storage_corrupt") from None
    return {
        "alert_id": alert["alert_id"],
        "comparison_id": cid,
        "event": event,
        "journal_content_sha256": journal_digest,
        "event_sha256": event_digest,
    }


def _enqueue_verified(path: Path, receipt: object, budget: Budget) -> dict[str, object]:
    """Only sealed application receipts grant admission; all local rows are revalidated."""
    from .application import _consume_receipt
    from .policy import prepare_event

    cid, journal_digest, rows = _consume_receipt(receipt, budget)
    _token(cid, "cmp3:")
    if type(journal_digest) is not str or not _HEX.fullmatch(journal_digest):
        raise OutboxError("unsupported_evidence")
    if type(rows) is not list or len(rows) > MAX_EVENTS:
        raise OutboxError("input_limit")
    bounded_canonical_json(rows, MAX_PREPARED_BYTES, budget)
    seen: set[str] = set()
    for row in rows:
        budget.remaining()
        if type(row) is not dict or set(row) != set(_ROW_FIELDS):
            raise OutboxError("unsupported_evidence")
        expected = prepare_event(
            _decode(cast(str, row["event_json"]), MAX_RESULT_BYTES, budget),
            cast(str, row["destination_key"]),
            cid,
            check=budget.remaining,
        )
        if canonical_json(expected) != canonical_json(row) or row["alert_id"] in seen:
            raise OutboxError("unsupported_evidence")
        seen.add(cast(str, row["alert_id"]))
    counts = {
        "alerts_new": 0,
        "alerts_existing": 0,
        "associations_new": 0,
        "associations_existing": 0,
        "events": len(rows),
    }
    with _connect(path, budget, writable=bool(rows)) as db:
        if rows:
            _execute(db, budget, "PRAGMA synchronous=FULL")
        with _transaction(db, budget, write=bool(rows)):
            _schema(db, budget)
            if rows:
                existing_digest = _execute(
                    db,
                    budget,
                    "SELECT "
                    + _text("journal_content_sha256", 64, 64)
                    + " FROM alert_evidence WHERE comparison_id=? LIMIT 1",
                    (cid,),
                ).fetchone()
                if existing_digest is not None and existing_digest[0] != journal_digest:
                    raise OutboxError("conflict")
            stamp = datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
            for row in rows:
                aid = cast(str, row["alert_id"])
                previous = _load_alert(db, aid, budget)
                if previous is None:
                    _execute(
                        db,
                        budget,
                        "INSERT INTO alerts VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        tuple(row[key] for key in _ALERT_FIELDS) + (stamp, "pending"),
                    )
                    counts["alerts_new"] += 1
                    previous = _load_alert(db, aid, budget)
                    if previous is None:
                        raise OutboxError("storage_corrupt")
                else:
                    if any(previous[key] != row[key] for key in _ALERT_FIELDS):
                        raise OutboxError("conflict")
                    counts["alerts_existing"] += 1
                evidence = _load_evidence(db, previous, cid, budget)
                if evidence is None:
                    _execute(
                        db,
                        budget,
                        "INSERT INTO alert_evidence VALUES (?,?,?,?,?)",
                        (aid, cid, row["event_json"], journal_digest, row["event_sha256"]),
                    )
                    counts["associations_new"] += 1
                else:
                    if (
                        evidence["journal_content_sha256"] != journal_digest
                        or bounded_canonical_json(evidence["event"], MAX_RESULT_BYTES, budget)
                        != row["event_json"]
                    ):
                        raise OutboxError("conflict")
                    counts["associations_existing"] += 1
    return {
        "version": 1,
        "operation": "enqueue",
        "result": "inserted" if counts["alerts_new"] or counts["associations_new"] else "replay",
        "comparison_id": cid,
        **counts,
    }


def get(path: Path, alert_id: str, *, timeout: float = DEFAULT_TIMEOUT) -> dict[str, object]:
    budget = Budget(timeout)
    aid = _token(alert_id, "alt1:")
    with _connect(path, budget) as db, _transaction(db, budget):
        _schema(db, budget)
        item = _load_alert(db, aid, budget)
        if item is None:
            raise OutboxError("storage_missing")
    item.pop("intent_json")
    return {"version": 1, "operation": "get", "result": "ok", "alert": item}


def preview(path: Path, alert_id: str, *, timeout: float = DEFAULT_TIMEOUT) -> dict[str, object]:
    item = cast(dict[str, object], get(path, alert_id, timeout=timeout)["alert"])
    return {
        "version": 1,
        "operation": "preview",
        "result": "ok",
        **{
            key: item[key]
            for key in (
                "alert_id",
                "message_text",
                "renderer_version",
                "policy_version",
                "channel",
                "state",
            )
        },
    }


def evidence_get(
    path: Path, alert_id: str, comparison_id: str, *, timeout: float = DEFAULT_TIMEOUT
) -> dict[str, object]:
    budget = Budget(timeout)
    aid, cid = _token(alert_id, "alt1:"), _token(comparison_id, "cmp3:")
    with _connect(path, budget) as db, _transaction(db, budget):
        _schema(db, budget)
        alert = _load_alert(db, aid, budget)
        if alert is None:
            raise OutboxError("storage_missing")
        evidence = _load_evidence(db, alert, cid, budget)
        if evidence is None:
            raise OutboxError("storage_missing")
    return {"version": 1, "operation": "evidence-get", "result": "ok", **evidence}


def _verify(db: sqlite3.Connection, budget: Budget) -> dict[str, int]:
    _schema(db, budget)
    _integrity(db, budget)
    alerts = associations = 0
    for row in _execute(
        db, budget, "SELECT " + _text("alert_id", 69, 69) + " FROM alerts ORDER BY alert_id"
    ):
        budget.remaining()
        try:
            aid = _token(row[0], "alt1:")
        except OutboxError:
            raise OutboxError("storage_corrupt") from None
        alert = _load_alert(db, aid, budget)
        if alert is None:
            raise OutboxError("storage_corrupt")
        associated = 0
        for evidence in _execute(
            db,
            budget,
            "SELECT "
            + _text("comparison_id", 69, 69)
            + " FROM alert_evidence WHERE alert_id=? ORDER BY comparison_id",
            (aid,),
        ):
            budget.remaining()
            try:
                cid = _token(evidence[0], "cmp3:")
            except OutboxError:
                raise OutboxError("storage_corrupt") from None
            if _load_evidence(db, alert, cid, budget) is None:
                raise OutboxError("storage_corrupt")
            associated += 1
        if not associated:
            raise OutboxError("storage_corrupt")
        alerts += 1
        associations += associated
    return {"alerts": alerts, "associations": associations}


def verify(path: Path, *, timeout: float = DEFAULT_TIMEOUT) -> dict[str, object]:
    budget = Budget(timeout)
    with _connect(path, budget) as db, _transaction(db, budget):
        counts = _verify(db, budget)
    return {"version": 1, "operation": "verify", "result": "ok", "level": "local", "counts": counts}


def _page_arguments(cursor: str | None, limit: int, prefix: str) -> tuple[str, int]:
    if type(limit) is not int or not 1 <= limit <= MAX_LIMIT:
        raise OutboxError("invalid_field")
    return "" if cursor is None else _token(cursor, prefix), limit


def _page(
    path: Path,
    *,
    alert_id: str | None,
    destination_key: str | None,
    cursor: str | None,
    limit: int,
    timeout: float,
) -> dict[str, object]:
    from .policy import destination

    budget = Budget(timeout)
    marker, size = _page_arguments(cursor, limit, "alt1:" if alert_id is None else "cmp3:")
    if destination_key is not None:
        destination_key = destination(destination_key)
    if alert_id is not None:
        _token(alert_id, "alt1:")
    items: list[dict[str, object]] = []
    page_bytes = 2
    next_cursor: str | None = None
    with _connect(path, budget) as db, _transaction(db, budget):
        _schema(db, budget)
        if alert_id is None:
            query = (
                "SELECT "
                + _text("alert_id", 69, 69)
                + " FROM alerts WHERE alert_id>?"
                + (" AND destination_key=?" if destination_key is not None else "")
                + " ORDER BY alert_id LIMIT ?"
            )
            parameters: tuple[object, ...] = (
                (marker, size + 1)
                if destination_key is None
                else (marker, destination_key, size + 1)
            )
        else:
            if _load_alert(db, alert_id, budget) is None:
                raise OutboxError("storage_missing")
            query = (
                "SELECT "
                + _text("comparison_id", 69, 69)
                + ","
                + _text("journal_content_sha256", 64, 64)
                + ","
                + _text("event_sha256", 64, 64)
                + " FROM alert_evidence WHERE alert_id=? AND comparison_id>?"
                " ORDER BY comparison_id LIMIT ?"
            )
            parameters = (alert_id, marker, size + 1)
        for row in _execute(db, budget, query, parameters):
            budget.remaining()
            try:
                token = _token(row[0], "alt1:" if alert_id is None else "cmp3:")
            except OutboxError:
                raise OutboxError("storage_corrupt") from None
            if len(items) == size:
                key = "alert_id" if alert_id is None else "comparison_id"
                next_cursor = cast(str, items[-1][key])
                break
            if alert_id is None:
                alert = _load_alert(db, token, budget)
                if alert is None:
                    raise OutboxError("storage_corrupt")
                item = {
                    key: value
                    for key, value in alert.items()
                    if key not in ("intent", "intent_json", "message_text")
                }
            else:
                if any(type(value) is not str or not _HEX.fullmatch(value) for value in row[1:]):
                    raise OutboxError("storage_corrupt")
                item = {
                    "comparison_id": token,
                    "journal_content_sha256": row[1],
                    "event_sha256": row[2],
                }
            page_bytes += len(bounded_canonical_json(item, MAX_PAGE_BYTES, budget)) + 1
            if page_bytes > MAX_PAGE_BYTES:
                raise OutboxError("input_limit")
            items.append(item)
    response: dict[str, object] = {
        "version": 1,
        "operation": "list" if alert_id is None else "evidence-list",
        "result": "ok",
        "items": items,
        "next_cursor": next_cursor,
    }
    if alert_id is not None:
        response["alert_id"] = alert_id
    bounded_canonical_json(response, MAX_PAGE_BYTES, budget)
    return response


def list_alerts(
    path: Path,
    *,
    cursor: str | None = None,
    limit: int = 100,
    destination_key: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, object]:
    return _page(
        path,
        alert_id=None,
        destination_key=destination_key,
        cursor=cursor,
        limit=limit,
        timeout=timeout,
    )


def evidence_list(
    path: Path,
    alert_id: str,
    *,
    cursor: str | None = None,
    limit: int = 100,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, object]:
    return _page(
        path, alert_id=alert_id, destination_key=None, cursor=cursor, limit=limit, timeout=timeout
    )


def initialize(path: Path, *, timeout: float = DEFAULT_TIMEOUT) -> dict[str, object]:
    budget = Budget(timeout)
    target = _path(path, new=True)
    identity: tuple[int, int] | None = None
    completed = False
    try:
        identity = paths._reserve(target)
        with _connect(target, budget, writable=True) as db:
            information = target.lstat()
            if (information.st_dev, information.st_ino) != identity:
                raise OutboxError("unsafe_destination")
            _execute(db, budget, "PRAGMA synchronous=FULL")
            with _transaction(db, budget, write=True):
                for statement in schema.STATEMENTS:
                    _execute(db, budget, statement)
                _execute(
                    db, budget, "INSERT INTO outbox_metadata VALUES (?,?,?)", (1, schema.OWNER, 1)
                )
                _execute(db, budget, f"PRAGMA application_id={schema.APPLICATION_ID}")
                _execute(db, budget, "PRAGMA user_version=1")
                _schema(db, budget)
        completed = True
        return {"version": 1, "operation": "init", "result": "ok", "schema_version": 1}
    except PersistenceError as error:
        raise OutboxError(error.category) from None
    except OSError:
        raise OutboxError("storage_io") from None
    finally:
        if not completed and identity is not None:
            paths._remove_owned(target, identity)


def _copy(source: Path, destination: Path, operation: str, timeout: float) -> dict[str, object]:
    budget = Budget(timeout)
    target: Path | None = None
    identity: tuple[int, int] | None = None
    completed = False
    try:
        with _connect(source, budget) as reader:
            # Validate source before reserving a destination, and keep that read
            # transaction during backup so its verified snapshot is copied.
            _execute(reader, budget, "BEGIN")
            try:
                _verify(reader, budget)
                target = _path(destination, new=True)
                identity = paths._reserve(target)
                with _connect(target, budget, writable=True) as writer:
                    information = target.lstat()
                    if (information.st_dev, information.st_ino) != identity:
                        raise OutboxError("unsafe_destination")
                    _execute(writer, budget, "PRAGMA synchronous=FULL")
                    reader.execute("PRAGMA busy_timeout=0")
                    writer.execute("PRAGMA busy_timeout=0")

                    def progress(status: int, remaining: int, total: int) -> None:
                        budget.remaining()

                    reader.backup(writer, pages=32, progress=progress, sleep=0.01)
                    with _transaction(writer, budget):
                        counts = _verify(writer, budget)
            finally:
                _rollback(reader)
        with _connect(target, budget) as reopened, _transaction(reopened, budget):
            if _verify(reopened, budget) != counts:
                raise OutboxError("storage_corrupt")
        completed = True
        return {"version": 1, "operation": operation, "result": "ok", "counts": counts}
    except PersistenceError as error:
        raise OutboxError(error.category) from None
    except OSError:
        raise OutboxError("storage_io") from None
    finally:
        if not completed and identity is not None and target is not None:
            paths._remove_owned(target, identity)


def backup(
    source: Path, destination: Path, *, timeout: float = DEFAULT_TIMEOUT
) -> dict[str, object]:
    return _copy(source, destination, "backup", timeout)


def restore(
    source: Path, destination: Path, *, timeout: float = DEFAULT_TIMEOUT
) -> dict[str, object]:
    return _copy(source, destination, "restore", timeout)
