"""Bounded, owned SQLite journal with atomic occurrences and read-only verification."""

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
from . import journal_schema as schema
from .journal_errors import JournalError

DEFAULT_TIMEOUT = 2.0
MAX_REQUEST_BYTES = 1024 * 1024
MAX_RESULT_BYTES = 16 * 1024 * 1024
MAX_PAGE_BYTES = 1024 * 1024
MAX_EVENTS = 1000
MAX_LIMIT = 1000
_HEX = re.compile(r"[0-9a-f]{64}")
_STAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z")


class Budget:
    """One monotonic deadline, shared by application admission and journal SQL."""

    def __init__(self, timeout: float = DEFAULT_TIMEOUT) -> None:
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 5:
            raise JournalError("invalid_field")
        self.deadline = time.monotonic() + timeout

    def remaining(self) -> float:
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise JournalError("storage_timeout")
        return remaining

    def progress(self) -> int:
        return int(time.monotonic() >= self.deadline)


def canonical_json(value: object) -> str:
    try:
        return json.dumps(
            value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise JournalError("storage_corrupt") from None


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
                    raise JournalError("input_limit")
                output.write(chunk)
            return output.getvalue()
    except JournalError:
        raise
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise JournalError("storage_corrupt") from None


def content_digest(request: object, result: object, *, budget: Budget | None = None) -> str:
    """Hash the exact finite canonical tuple, excluding insertion and runtime clocks."""
    digest = hashlib.sha256()
    encoder = json.JSONEncoder(
        ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    try:
        for chunk in encoder.iterencode(
            {"journal_version": 1, "request": request, "result": result}
        ):
            if budget is not None:
                budget.remaining()
            digest.update(chunk.encode("ascii"))
    except JournalError:
        raise
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise JournalError("storage_corrupt") from None
    return digest.hexdigest()


def _token(value: object, prefix: str) -> str:
    if type(value) is not str or not value.startswith(prefix) or not _HEX.fullmatch(value[5:]):
        raise JournalError("invalid_field")
    return value


def _stamp(value: object) -> str:
    if type(value) is not str or not _STAMP.fullmatch(value):
        raise JournalError("storage_corrupt")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        raise JournalError("storage_corrupt") from None
    return value


def _path(value: Path, *, new: bool = False) -> Path:
    try:
        path = paths._checked_path(value)
        exists = paths._exists(path)
        if new and exists:
            raise JournalError("unsafe_destination")
        if not new and not exists:
            raise JournalError("storage_missing")
        paths._check_sidecars(path, new=new)
        return path
    except PersistenceError as error:
        raise JournalError(error.category) from None
    except OSError:
        raise JournalError("storage_io") from None


def reject_same_file(first: Path, second: Path) -> None:
    """Validate both existing paths before capture IO; aliases never cross owners."""
    left, right = _path(first), _path(second)
    try:
        if os.path.samefile(left, right):
            raise JournalError("unsafe_destination")
    except OSError:
        raise JournalError("storage_io") from None


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
            raise JournalError("unsafe_destination")
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
            raise JournalError("storage_schema")
        if not writable:
            _execute(db, budget, "PRAGMA query_only=ON")
        yield db
        budget.remaining()
    except PersistenceError as error:
        raise JournalError(error.category) from None
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
        raise JournalError(category) from None
    except OSError:
        raise JournalError("storage_io") from None
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


def _schema(db: sqlite3.Connection, budget: Budget) -> None:
    if (
        _execute(db, budget, "PRAGMA application_id").fetchone()[0] != schema.APPLICATION_ID
        or _execute(db, budget, "PRAGMA user_version").fetchone()[0] != schema.SCHEMA_VERSION
        or _execute(db, budget, "PRAGMA journal_mode").fetchone()[0] != "delete"
    ):
        raise JournalError("storage_schema")
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
        raise JournalError("storage_schema")
    metadata = _execute(
        db,
        budget,
        "SELECT singleton," + _text("owner", 128) + ",schema_version FROM journal_metadata LIMIT 2",
    )
    if [tuple(row) for row in metadata] != [(1, schema.OWNER, schema.SCHEMA_VERSION)]:
        raise JournalError("storage_schema")


def _integrity(db: sqlite3.Connection, budget: Budget) -> None:
    # The one-result limit avoids unbounded corruption diagnostics.
    result = _execute(db, budget, "PRAGMA integrity_check(1)").fetchone()
    if result is None or result[0] != "ok":
        raise JournalError("storage_corrupt")
    if _execute(db, budget, "PRAGMA foreign_key_check").fetchone() is not None:
        raise JournalError("storage_corrupt")


def _validated_pair(
    request: object, result: object, budget: Budget
) -> tuple[dict[str, object], dict[str, object]]:
    from .journal_validation import validate_pair

    return validate_pair(request, result, check=budget.remaining)


def _load(db: sqlite3.Connection, cid: str, budget: Budget) -> dict[str, object] | None:
    from .journal_validation import decode_json

    columns = (
        _text("request_json", MAX_REQUEST_BYTES, 2),
        _text("result_json", MAX_RESULT_BYTES, 2),
        _text("content_sha256", 64, 64),
        _text("first_recorded_at", 27, 27),
    )
    row = _execute(
        db,
        budget,
        "SELECT " + ",".join(columns) + " FROM comparisons WHERE comparison_id=?",
        (cid,),
    ).fetchone()
    if row is None:
        return None
    if any(type(value) is not str for value in row):
        raise JournalError("storage_corrupt")
    request_json, result_json, digest, stamp = tuple(row)
    try:
        request, result = _validated_pair(
            decode_json(request_json, maximum=MAX_REQUEST_BYTES, check=budget.remaining),
            decode_json(result_json, maximum=MAX_RESULT_BYTES, check=budget.remaining),
            budget,
        )
    except JournalError as error:
        if error.category == "storage_timeout":
            raise
        raise JournalError("storage_corrupt") from None
    if (
        bounded_canonical_json(request, MAX_REQUEST_BYTES, budget) != request_json
        or bounded_canonical_json(result, MAX_RESULT_BYTES, budget) != result_json
        or result["comparison_id"] != cid
        or not _HEX.fullmatch(digest)
        or content_digest(request, result, budget=budget) != digest
    ):
        raise JournalError("storage_corrupt")
    _stamp(stamp)
    events = cast(list[dict[str, object]], result["events"])
    cursor = _execute(
        db,
        budget,
        "SELECT "
        + _text("event_id", 69, 69)
        + ",ordinal,"
        + _text("event_json", MAX_RESULT_BYTES, 2)
        + " FROM event_occurrences WHERE comparison_id=? ORDER BY ordinal LIMIT 1001",
        (cid,),
    )
    count = 0
    for event_row in cursor:
        budget.remaining()
        if count >= len(events):
            raise JournalError("storage_corrupt")
        if (
            type(event_row[1]) is not int
            or event_row[1] != count
            or event_row[0] != events[count]["event_id"]
            or event_row[2] != bounded_canonical_json(events[count], MAX_RESULT_BYTES, budget)
        ):
            raise JournalError("storage_corrupt")
        count += 1
    if count != len(events):
        raise JournalError("storage_corrupt")
    budget.remaining()
    return {
        "version": 1,
        "comparison_id": cid,
        "request": request,
        "comparison": result,
        "content_sha256": digest,
        "first_recorded_at": stamp,
    }


def _record_verified(path: Path, receipt: object, budget: Budget) -> dict[str, object]:
    """Private application writer: raw results and self-declared receipts have no authority."""
    from .journal_application import _consume_receipt

    budget.remaining()
    request, result = _validated_pair(*_consume_receipt(receipt, budget), budget)
    request_json = bounded_canonical_json(request, MAX_REQUEST_BYTES, budget)
    result_json = bounded_canonical_json(result, MAX_RESULT_BYTES, budget)
    cid = _token(result["comparison_id"], "cmp3:")
    events = cast(list[dict[str, object]], result["events"])
    digest = content_digest(request, result, budget=budget)
    budget.remaining()
    with _connect(path, budget, writable=True) as db:
        _execute(db, budget, "PRAGMA synchronous=FULL")
        with _transaction(db, budget, write=True):
            _schema(db, budget)
            previous = _load(db, cid, budget)
            if previous is not None:
                if (
                    canonical_json(previous["request"]) != request_json
                    or canonical_json(previous["comparison"]) != result_json
                ):
                    raise JournalError("conflict")
                outcome, stamp = "replay", previous["first_recorded_at"]
            else:
                stamp = datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
                _execute(
                    db,
                    budget,
                    "INSERT INTO comparisons VALUES (?,?,?,?,?)",
                    (cid, request_json, result_json, digest, stamp),
                )
                for ordinal, event in enumerate(events):
                    _execute(
                        db,
                        budget,
                        "INSERT INTO event_occurrences VALUES (?,?,?,?)",
                        (cid, event["event_id"], ordinal, canonical_json(event)),
                    )
                outcome = "inserted"
    return {
        "version": 1,
        "operation": "record",
        "result": outcome,
        "comparison_id": cid,
        "first_recorded_at": stamp,
        "counts": {"comparisons": 1, "occurrences": len(events)},
    }


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
                raise JournalError("unsafe_destination")
            _execute(db, budget, "PRAGMA synchronous=FULL")
            with _transaction(db, budget, write=True):
                for statement in schema.STATEMENTS:
                    _execute(db, budget, statement)
                _execute(
                    db, budget, "INSERT INTO journal_metadata VALUES (?,?,?)", (1, schema.OWNER, 1)
                )
                _execute(db, budget, f"PRAGMA application_id={schema.APPLICATION_ID}")
                _execute(db, budget, "PRAGMA user_version=1")
                _schema(db, budget)
        completed = True
        return {"version": 1, "operation": "init", "result": "ok", "schema_version": 1}
    except PersistenceError as error:
        raise JournalError(error.category) from None
    except OSError:
        raise JournalError("storage_io") from None
    finally:
        if not completed and identity is not None:
            paths._remove_owned(target, identity)


def get(path: Path, comparison_id: str, *, timeout: float = DEFAULT_TIMEOUT) -> dict[str, object]:
    budget = Budget(timeout)
    cid = _token(comparison_id, "cmp3:")
    with _connect(path, budget) as db, _transaction(db, budget):
        _schema(db, budget)
        item = _load(db, cid, budget)
        if item is None:
            raise JournalError("storage_missing")
    return {"operation": "get", "result": "ok", **item}


def _verify(db: sqlite3.Connection, budget: Budget) -> dict[str, int]:
    _schema(db, budget)
    _integrity(db, budget)
    comparisons = occurrences = 0
    cursor = _execute(
        db,
        budget,
        "SELECT " + _text("comparison_id", 69, 69) + " FROM comparisons ORDER BY comparison_id",
    )
    for row in cursor:
        budget.remaining()
        try:
            cid = _token(row[0], "cmp3:")
        except JournalError:
            raise JournalError("storage_corrupt") from None
        item = _load(db, cid, budget)
        if item is None:
            raise JournalError("storage_corrupt")
        comparisons += 1
        occurrences += len(cast(dict[str, list[object]], item["comparison"])["events"])
    return {"comparisons": comparisons, "occurrences": occurrences}


def verify(path: Path, *, timeout: float = DEFAULT_TIMEOUT) -> dict[str, object]:
    budget = Budget(timeout)
    with _connect(path, budget) as db, _transaction(db, budget):
        counts = _verify(db, budget)
    return {"version": 1, "operation": "verify", "result": "ok", "level": "local", "counts": counts}


def _page_arguments(cursor: str | None, limit: int) -> tuple[str, int]:
    if type(limit) is not int or not 1 <= limit <= MAX_LIMIT:
        raise JournalError("invalid_field")
    return "" if cursor is None else _token(cursor, "cmp3:"), limit


def _page(
    path: Path, *, event_id: str | None, cursor: str | None, limit: int, timeout: float
) -> dict[str, object]:
    budget = Budget(timeout)
    marker, size = _page_arguments(cursor, limit)
    if event_id is not None:
        _token(event_id, "evt3:")
    items: list[dict[str, object]] = []
    next_cursor: str | None = None
    with _connect(path, budget) as db, _transaction(db, budget):
        _schema(db, budget)
        if event_id is None:
            sql = (
                "SELECT "
                + ",".join(
                    (
                        _text("comparison_id", 69, 69),
                        _text("content_sha256", 64, 64),
                        _text("first_recorded_at", 27, 27),
                        "length(CAST(result_json AS BLOB))",
                    )
                )
                + " FROM comparisons WHERE comparison_id>? ORDER BY comparison_id LIMIT ?"
            )
            values: tuple[object, ...] = (marker, size + 1)
        else:
            sql = (
                "SELECT "
                + _text("comparison_id", 69, 69)
                + ",ordinal FROM event_occurrences WHERE event_id=? AND comparison_id>? "
                "ORDER BY comparison_id LIMIT ?"
            )
            values = (event_id, marker, size + 1)
        for row in _execute(db, budget, sql, values):
            budget.remaining()
            try:
                cid = _token(row[0], "cmp3:")
            except JournalError:
                raise JournalError("storage_corrupt") from None
            if len(items) == size:
                next_cursor = cast(str, items[-1]["comparison_id"])
                break
            item: dict[str, object] = {"comparison_id": cid}
            if event_id is None:
                if type(row[1]) is not str or not _HEX.fullmatch(row[1]):
                    raise JournalError("storage_corrupt")
                _stamp(row[2])
                if type(row[3]) is not int or not 2 <= row[3] <= MAX_RESULT_BYTES:
                    raise JournalError("storage_corrupt")
                item.update(content_sha256=row[1], first_recorded_at=row[2], result_bytes=row[3])
            else:
                if type(row[1]) is not int or not 0 <= row[1] < MAX_EVENTS:
                    raise JournalError("storage_corrupt")
                item["ordinal"] = row[1]
            items.append(item)
    response: dict[str, object] = {
        "version": 1,
        "operation": "list" if event_id is None else "event-occurrences",
        "result": "ok",
        "items": items,
        "next_cursor": next_cursor,
    }
    if event_id is not None:
        response["event_id"] = event_id
    if len(canonical_json(response)) > MAX_PAGE_BYTES:
        raise JournalError("input_limit")
    budget.remaining()
    return response


def list_comparisons(
    path: Path, *, cursor: str | None = None, limit: int = 100, timeout: float = DEFAULT_TIMEOUT
) -> dict[str, object]:
    return _page(path, event_id=None, cursor=cursor, limit=limit, timeout=timeout)


def event_occurrences(
    path: Path,
    event_id: str,
    *,
    cursor: str | None = None,
    limit: int = 100,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, object]:
    return _page(path, event_id=event_id, cursor=cursor, limit=limit, timeout=timeout)


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
                        raise JournalError("unsafe_destination")
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
                raise JournalError("storage_corrupt")
        completed = True
        return {"version": 1, "operation": operation, "result": "ok", "counts": counts}
    except PersistenceError as error:
        raise JournalError(error.category) from None
    except OSError:
        raise JournalError("storage_io") from None
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
