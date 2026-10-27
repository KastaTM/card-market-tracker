"""Independent synthetic journal: atomic append, deep folds and verified recovery."""

import base64
import hashlib
import json
import math
import os
import sqlite3
import stat
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from ..persistence import sqlite_repository as paths
from ..persistence.errors import PersistenceError
from ..watchlist import validation
from ..watchlist.errors import WatchlistError
from . import identity, schema, transitions
from .errors import JournalError

DEFAULT_TIMEOUT = 2.0
MAX_PAGE_BYTES = 1024 * 1024
MAX_CELL_BYTES = 65536
MAX_LIMIT = 1000


class Budget:
    """A single cooperative deadline includes validation, SQL and recovery IO."""

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


def _path(value: Path, *, new: bool = False) -> Path:
    try:
        target = paths._checked_path(value)
        exists = paths._exists(target)
        if new and exists:
            raise JournalError("unsafe_destination")
        if not new and not exists:
            raise JournalError("storage_missing")
        paths._check_sidecars(target, new=new)
        return target
    except PersistenceError as error:
        raise JournalError(error.category) from None
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
        db.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 2 * MAX_CELL_BYTES)
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
            sqlite3.SQLITE_CONSTRAINT: "storage_corrupt",
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


def _text(column: str, maximum: int = MAX_CELL_BYTES) -> str:
    # All identifiers are internal constants. Bound hostile cells before materialization.
    return (
        f"CASE WHEN typeof({column})='text' AND "
        f"length(CAST({column} AS BLOB)) BETWEEN 1 AND {maximum} THEN {column} END"
    )


def _integer(column: str) -> str:
    return f"CASE WHEN typeof({column})='integer' THEN {column} END"


def _schema(db: sqlite3.Connection, budget: Budget) -> None:
    if (
        _execute(db, budget, "PRAGMA application_id").fetchone()[0] != schema.APPLICATION_ID
        or _execute(db, budget, "PRAGMA user_version").fetchone()[0] != schema.SCHEMA_VERSION
        or _execute(db, budget, "PRAGMA journal_mode").fetchone()[0] != "delete"
    ):
        raise JournalError("storage_schema")
    expected = schema.expected_inventory()
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
    if tuple(tuple(row) for row in query) != expected:
        raise JournalError("storage_schema")
    rows = _execute(
        db,
        budget,
        "SELECT "
        + _integer("singleton")
        + ","
        + _text("owner", 128)
        + ","
        + _integer("schema_version")
        + " FROM wl_journal_metadata LIMIT 2",
    )
    if [tuple(row) for row in rows] != [(1, schema.OWNER, schema.SCHEMA_VERSION)]:
        raise JournalError("storage_schema")


def _decode(raw: object, budget: Budget) -> object:
    from ..discovery.journal_errors import JournalError as DecodeError
    from ..discovery.journal_validation import decode_json

    if type(raw) is not str:
        raise JournalError("storage_corrupt")

    def check() -> None:
        # The reused parser sanitizes unknown ValueErrors; preserve this deadline category.
        try:
            budget.remaining()
        except JournalError:
            raise DecodeError("storage_timeout") from None

    try:
        check()
        value = decode_json(raw, maximum=MAX_CELL_BYTES, check=check)
        check()
        return value
    except DecodeError as error:
        category = "storage_timeout" if error.category == "storage_timeout" else "storage_corrupt"
        raise JournalError(category) from None


def _canonical(value: object, maximum: int = MAX_CELL_BYTES) -> str:
    raw = identity.canonical(value)
    if len(raw) > maximum:
        raise JournalError("input_limit")
    return raw


def _digest(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _nullable_text(column: str, maximum: int = MAX_CELL_BYTES) -> str:
    return f"CASE WHEN {column} IS NULL THEN NULL ELSE COALESCE({_text(column, maximum)},'') END"


def _load_evaluation(db: sqlite3.Connection, budget: Budget, key: str) -> dict[str, object] | None:
    columns = (
        _text("evaluation_id", 69),
        _text("sequence_id", 69),
        _text("current_sample_id", 128),
        _nullable_text("prior_eval_id", 69),
        _text("snapshot_json"),
        _text("result_json"),
        _text("observed_at", 32),
        _text("as_of", 32),
        _text("persisted_at", 32),
        _integer("ordinal"),
    )
    row = _execute(
        db,
        budget,
        "SELECT " + ",".join(columns) + " FROM wl_journal_evaluations WHERE evaluation_id=?",
        (key,),
    ).fetchone()
    if row is None:
        return None
    try:
        snapshot, result = identity.validate_snapshot(_decode(row[4], budget))
        current = cast(dict[str, object], snapshot["current"])
        if (
            row[0] != key
            or identity._evaluation_id(snapshot) != key
            or row[1] != snapshot["sequence_id"]
            or row[2] != current["sample_id"]
            or row[4] != _canonical(snapshot)
            or row[5] != _canonical(result)
            or row[6] != current["observed_at"]
            or row[7] != snapshot["as_of"]
            or validation.timestamp(row[8]) != row[8]
            or type(row[9]) is not int
            or row[9] < 1
        ):
            raise JournalError("storage_corrupt")
        return {
            "evaluation_id": key,
            "sequence_id": row[1],
            "predecessor_evaluation_id": row[3],
            "ordinal": row[9],
            "persisted_at": row[8],
            "snapshot": snapshot,
            "evaluation_result": result,
        }
    except (JournalError, WatchlistError) as error:
        if error.category == "storage_timeout":
            raise JournalError("storage_timeout") from None
        raise JournalError("storage_corrupt") from None


def _signals_for(
    db: sqlite3.Connection, budget: Budget, evaluation_id: str
) -> list[dict[str, object]]:
    columns = ("signal_id", "sequence_id", "rule", "from_eval_id", "to_eval_id", "body_json")
    results: list[dict[str, object]] = []
    for row in _execute(
        db,
        budget,
        "SELECT "
        + ",".join(_text(column) for column in columns)
        + " FROM wl_journal_signals WHERE to_eval_id=? ORDER BY signal_id",
        (evaluation_id,),
    ):
        budget.remaining()
        try:
            body = _decode(row[5], budget)
            if type(body) is not dict:
                raise JournalError("storage_corrupt")
            body = cast(dict[str, object], body)
            if (
                identity.signal_id(body) != row[0]
                or _canonical(body) != row[5]
                or body["sequence_id"] != row[1]
                or body["rule"] != row[2]
                or body["from_evaluation_id"] != row[3]
                or body["to_evaluation_id"] != row[4]
                or row[4] != evaluation_id
            ):
                raise JournalError("storage_corrupt")
            results.append({**body, "signal_id": row[0]})
        except JournalError as error:
            if error.category == "storage_timeout":
                raise
            raise JournalError("storage_corrupt") from None
    return results


def _verify(db: sqlite3.Connection, budget: Budget) -> dict[str, int]:
    _schema(db, budget)
    if _execute(db, budget, "PRAGMA integrity_check(1)").fetchone()[0] != "ok":
        raise JournalError("storage_corrupt")
    if _execute(db, budget, "PRAGMA foreign_key_check").fetchone() is not None:
        raise JournalError("storage_corrupt")
    counts = {"sequences": 0, "evaluations": 0, "signals": 0}
    entries: dict[tuple[str, int], str] = {}
    columns = (
        _text("sequence_id", 69),
        _text("watch_id", 69),
        _integer("revision"),
        _text("policy_version", 64),
        _text("series_key", 128),
        _text("entry_json"),
        _text("entry_digest", 64),
        _text("head_eval_id", 69),
        _text("head_observed_at", 32),
        _text("head_as_of", 32),
        _integer("head_ordinal"),
    )
    try:
        for sequence in _execute(
            db,
            budget,
            "SELECT " + ",".join(columns) + " FROM wl_journal_sequences ORDER BY sequence_id",
        ):
            budget.remaining()
            sid = identity.validate_id(sequence[0], "wjs1_")
            entry = validation.parse_entry(_decode(sequence[5], budget))
            entry_json = _canonical(entry)
            key = (cast(str, entry["watch_id"]), cast(int, entry["revision"]))
            if (
                sequence[1] != key[0]
                or sequence[2] != key[1]
                or sequence[3] != "watchlist-rules-v1"
                or sequence[5] != entry_json
                or sequence[6] != _digest(entry_json)
                or entries.setdefault(key, entry_json) != entry_json
            ):
                raise JournalError("storage_corrupt")
            previous: dict[str, object] | None = None
            previous_id: str | None = None
            previous_point: transitions._FoldPoint | None = None
            ordinal = 0
            sample_ids: set[str] = set()
            for row in _execute(
                db,
                budget,
                "SELECT "
                + _text("evaluation_id", 69)
                + " FROM wl_journal_evaluations WHERE sequence_id=? ORDER BY ordinal",
                (sid,),
            ):
                budget.remaining()
                ordinal += 1
                eid = identity.validate_id(row[0], "wje1_")
                loaded = _load_evaluation(db, budget, eid)
                if loaded is None:
                    raise JournalError("storage_corrupt")
                snapshot = cast(dict[str, object], loaded["snapshot"])
                current = cast(dict[str, object], snapshot["current"])
                sample_id = cast(str, current["sample_id"])
                if (
                    loaded["sequence_id"] != sid
                    or loaded["ordinal"] != ordinal
                    or loaded["predecessor_evaluation_id"] != previous_id
                    or _canonical(snapshot["entry"]) != entry_json
                    or current["series_key"] != sequence[4]
                    or sample_id in sample_ids
                ):
                    raise JournalError("storage_corrupt")
                sample_ids.add(sample_id)
                # Each row's snapshot, recomputed result and ID were checked by _load_evaluation.
                # Reuse them only in this fold; source, copy and reopen each start from fresh rows.
                point = (snapshot, cast(dict[str, object], loaded["evaluation_result"]), eid)
                expected = transitions._derive_normalized_signals(previous_point, point)
                actual = _signals_for(db, budget, eid)
                if sorted(expected, key=lambda item: cast(str, item["signal_id"])) != actual:
                    raise JournalError("storage_corrupt")
                counts["signals"] += len(actual)
                previous, previous_id = snapshot, eid
                previous_point = point
            if previous is None:
                raise JournalError("storage_corrupt")
            current = cast(dict[str, object], previous["current"])
            if (
                sequence[7] != previous_id
                or sequence[8] != current["observed_at"]
                or sequence[9] != previous["as_of"]
                or sequence[10] != ordinal
            ):
                raise JournalError("storage_corrupt")
            counts["sequences"] += 1
            counts["evaluations"] += ordinal
        for name in ("sequences", "evaluations", "signals"):
            if (
                _execute(db, budget, "SELECT COUNT(*) FROM wl_journal_" + name).fetchone()[0]
                != counts[name]
            ):
                raise JournalError("storage_corrupt")
        budget.remaining()
        return counts
    except (JournalError, WatchlistError) as error:
        if error.category == "storage_timeout":
            raise JournalError("storage_timeout") from None
        raise JournalError("storage_corrupt") from None


def _response(
    evaluation: dict[str, object], signals: list[dict[str, object]], replay: bool
) -> dict[str, object]:
    return {
        "version": 1,
        "operation": "record",
        "result": "replayed" if replay else "recorded",
        "sequence_id": evaluation["sequence_id"],
        "evaluation_id": evaluation["evaluation_id"],
        "predecessor_evaluation_id": evaluation["predecessor_evaluation_id"],
        "signal_ids": sorted(cast(str, signal["signal_id"]) for signal in signals),
        "signals_count": len(signals),
        "persisted_at": evaluation["persisted_at"],
    }


def _record_validated(
    path: Path, value: object, *, timeout: float = DEFAULT_TIMEOUT, _budget: Budget | None = None
) -> dict[str, object]:
    """Private application boundary; original admission remains application.record's duty."""
    budget = Budget(timeout) if _budget is None else _budget
    snapshot, result = identity.validate_snapshot(value)
    sid = cast(str, snapshot["sequence_id"])
    eid = identity.evaluation_id(snapshot)
    entry = cast(dict[str, object], snapshot["entry"])
    current = cast(dict[str, object], snapshot["current"])
    entry_json = _canonical(entry)
    with _connect(path, budget, writable=True) as db:
        # Owner/schema inspection precedes any database mutation.
        _schema(db, budget)
        _execute(db, budget, "PRAGMA synchronous=FULL")
        with _transaction(db, budget, write=True):
            _verify(db, budget)
            for row in _execute(
                db,
                budget,
                "SELECT "
                + _text("entry_json")
                + " FROM wl_journal_sequences WHERE watch_id=? AND revision=?",
                (entry["watch_id"], entry["revision"]),
            ):
                if row[0] != entry_json:
                    raise JournalError("identity_conflict")
            replay = _load_evaluation(db, budget, eid)
            if replay is not None:
                return _response(replay, _signals_for(db, budget, eid), True)
            collision = _execute(
                db,
                budget,
                "SELECT 1 FROM wl_journal_evaluations WHERE sequence_id=? AND current_sample_id=?",
                (sid, current["sample_id"]),
            ).fetchone()
            if collision is not None:
                raise JournalError("replay_conflict")
            head = _execute(
                db,
                budget,
                "SELECT "
                + _text("head_eval_id", 69)
                + ","
                + _integer("head_ordinal")
                + " FROM wl_journal_sequences WHERE sequence_id=?",
                (sid,),
            ).fetchone()
            previous: dict[str, object] | None = None
            prior_id: str | None = None
            ordinal = 1
            if head is not None:
                prior_id, ordinal = head[0], head[1] + 1
                predecessor = _load_evaluation(db, budget, cast(str, prior_id))
                if predecessor is None:
                    raise JournalError("storage_corrupt")
                previous = cast(dict[str, object], predecessor["snapshot"])
            signals = transitions.derive_signals(previous, snapshot)
            persisted = datetime.now(UTC).isoformat().replace("+00:00", "Z")
            if head is None:
                _execute(
                    db,
                    budget,
                    "INSERT INTO wl_journal_sequences VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        sid,
                        entry["watch_id"],
                        entry["revision"],
                        snapshot["policy_version"],
                        current["series_key"],
                        entry_json,
                        _digest(entry_json),
                        eid,
                        current["observed_at"],
                        snapshot["as_of"],
                        ordinal,
                    ),
                )
            _execute(
                db,
                budget,
                "INSERT INTO wl_journal_evaluations VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    eid,
                    sid,
                    current["sample_id"],
                    prior_id,
                    _canonical(snapshot),
                    _canonical(result),
                    current["observed_at"],
                    snapshot["as_of"],
                    persisted,
                    ordinal,
                ),
            )
            for signal in signals:
                body = {key: value for key, value in signal.items() if key != "signal_id"}
                _execute(
                    db,
                    budget,
                    "INSERT INTO wl_journal_signals VALUES (?,?,?,?,?,?)",
                    (
                        signal["signal_id"],
                        sid,
                        signal["rule"],
                        signal["from_evaluation_id"],
                        signal["to_evaluation_id"],
                        _canonical(body),
                    ),
                )
            if head is not None:
                changed = _execute(
                    db,
                    budget,
                    "UPDATE wl_journal_sequences SET head_eval_id=?,head_observed_at=?,"
                    "head_as_of=?,head_ordinal=? WHERE sequence_id=? "
                    "AND head_eval_id=? AND head_ordinal=?",
                    (
                        eid,
                        current["observed_at"],
                        snapshot["as_of"],
                        ordinal,
                        sid,
                        prior_id,
                        ordinal - 1,
                    ),
                )
                if changed.rowcount != 1:
                    raise JournalError("replay_conflict")
            response = _response(
                {
                    "evaluation_id": eid,
                    "sequence_id": sid,
                    "predecessor_evaluation_id": prior_id,
                    "persisted_at": persisted,
                },
                signals,
                False,
            )
    budget.remaining()
    return response


def verify(path: Path, *, timeout: float = DEFAULT_TIMEOUT) -> dict[str, object]:
    budget = Budget(timeout)
    with _connect(path, budget) as db, _transaction(db, budget):
        counts = _verify(db, budget)
    return {"version": 1, "operation": "verify", "result": "ok", "counts": counts}


def get(
    path: Path,
    evaluation_id: object,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    _budget: Budget | None = None,
) -> dict[str, object]:
    budget = Budget(timeout) if _budget is None else _budget
    key = identity.validate_id(evaluation_id, "wje1_")
    with _connect(path, budget) as db, _transaction(db, budget):
        _verify(db, budget)
        evaluation = _load_evaluation(db, budget, key)
        if evaluation is None:
            raise JournalError("not_found")
        evaluation["signal_ids"] = [item["signal_id"] for item in _signals_for(db, budget, key)]
    return {"version": 1, "operation": "get", "result": "ok", "evaluation": evaluation}


def signal_get(
    path: Path, signal_id: object, *, timeout: float = DEFAULT_TIMEOUT
) -> dict[str, object]:
    budget = Budget(timeout)
    key = identity.validate_id(signal_id, "wsig1_")
    with _connect(path, budget) as db, _transaction(db, budget):
        _verify(db, budget)
        row = _execute(
            db,
            budget,
            "SELECT " + _text("to_eval_id", 69) + " FROM wl_journal_signals WHERE signal_id=?",
            (key,),
        ).fetchone()
        if row is None:
            raise JournalError("not_found")
        signal = next(item for item in _signals_for(db, budget, row[0]) if item["signal_id"] == key)
    return {"version": 1, "operation": "signal-get", "result": "ok", "signal": signal}


def _verified_signal_bundle(path: Path, signal_id: object, *, _budget: Budget) -> dict[str, object]:
    """Read one deeply verified original signal/pair under a single ro snapshot."""
    key = identity.validate_id(signal_id, "wsig1_")
    _budget.remaining()
    with _connect(path, _budget) as db, _transaction(db, _budget):
        _verify(db, _budget)
        row = _execute(
            db,
            _budget,
            "SELECT " + _text("to_eval_id", 69) + " FROM wl_journal_signals WHERE signal_id=?",
            (key,),
        ).fetchone()
        if row is None:
            raise JournalError("not_found")
        actual = _signals_for(db, _budget, row[0])
        selected = next((item for item in actual if item["signal_id"] == key), None)
        if selected is None:
            raise JournalError("storage_corrupt")
        before = _load_evaluation(db, _budget, cast(str, selected["from_evaluation_id"]))
        after = _load_evaluation(db, _budget, cast(str, selected["to_evaluation_id"]))
        if before is None or after is None:
            raise JournalError("storage_corrupt")
        expected = transitions._derive_normalized_signals(
            (
                cast(dict[str, object], before["snapshot"]),
                cast(dict[str, object], before["evaluation_result"]),
                cast(str, before["evaluation_id"]),
            ),
            (
                cast(dict[str, object], after["snapshot"]),
                cast(dict[str, object], after["evaluation_result"]),
                cast(str, after["evaluation_id"]),
            ),
        )
        if (
            after["predecessor_evaluation_id"] != before["evaluation_id"]
            or after["ordinal"] != cast(int, before["ordinal"]) + 1
            or selected not in expected
        ):
            raise JournalError("storage_corrupt")
        fields = (
            "evaluation_id",
            "sequence_id",
            "ordinal",
            "predecessor_evaluation_id",
            "snapshot",
            "evaluation_result",
        )
        bundle = {
            "version": 1,
            "signal": selected,
            "predecessor": {name: before[name] for name in fields},
            "current": {name: after[name] for name in fields},
        }
        _canonical(bundle, 262144)
        _budget.remaining()
    return bundle


def _encode_cursor(binding: dict[str, object], last: str) -> str:
    return base64.urlsafe_b64encode(
        _canonical({"binding": binding, "last": last}).encode()
    ).decode()


def _cursor(value: object, binding: dict[str, object], prefix: str) -> str:
    if value is None:
        return ""
    if type(value) is not str or not 1 <= len(value) <= 2048:
        raise JournalError("invalid_cursor")
    try:
        raw = base64.b64decode(value, altchars=b"-_", validate=True).decode("ascii")
        decoded = json.loads(raw)
        if type(decoded) is not dict or set(decoded) != {"binding", "last"}:
            raise ValueError
        last = identity.validate_id(decoded["last"], prefix)
        if decoded["binding"] != binding or _encode_cursor(binding, last) != value:
            raise ValueError
        return last
    except (JournalError, ValueError, UnicodeError, RecursionError):
        raise JournalError("invalid_cursor") from None


def _list(
    path: Path,
    *,
    signals: bool,
    sequence_id: object,
    watch_id: object,
    revision: object,
    rule: object,
    limit: int,
    cursor: object,
    timeout: float,
) -> dict[str, object]:
    budget = Budget(timeout)
    if type(limit) is not int or not 1 <= limit <= MAX_LIMIT:
        raise JournalError("invalid_field")
    if sequence_id is not None:
        sequence_id = identity.validate_id(sequence_id, "wjs1_")
    try:
        if watch_id is not None:
            watch_id = validation.validate_watch_id(watch_id)
        if revision is not None:
            revision = validation.validate_revision(revision)
    except WatchlistError as error:
        raise JournalError(error.category) from None
    if rule is not None and (type(rule) is not str or rule not in ("price", "restock")):
        raise JournalError("invalid_field")
    operation = "signal-list" if signals else "list"
    field, table, prefix = (
        ("signal_id", "signals", "wsig1_") if signals else ("evaluation_id", "evaluations", "wje1_")
    )
    binding: dict[str, object] = {
        "version": 1,
        "operation": operation,
        "order": field,
        "sequence_id": sequence_id,
        "watch_id": watch_id,
        "revision": revision,
        "rule": rule,
    }
    marker = _cursor(cursor, binding, prefix)
    sql = "SELECT " + _text("item." + field, 70)
    sql += " FROM wl_journal_" + table + " AS item JOIN wl_journal_sequences AS seq"
    sql += " ON item.sequence_id=seq.sequence_id WHERE item." + field + ">?"
    parameters: tuple[object, ...] = (marker,)
    for column, value in (
        ("seq.sequence_id", sequence_id),
        ("seq.watch_id", watch_id),
        ("seq.revision", revision),
        ("item.rule", rule),
    ):
        if value is not None:
            sql += " AND " + column + "=?"
            parameters += (value,)
    sql += " ORDER BY item." + field + " LIMIT ?"
    parameters += (limit + 1,)
    items: list[dict[str, object]] = []
    next_cursor: str | None = None
    last = marker
    with _connect(path, budget) as db, _transaction(db, budget):
        _verify(db, budget)
        for row in _execute(db, budget, sql, parameters):
            budget.remaining()
            if len(items) == limit:
                next_cursor = _encode_cursor(binding, last)
                break
            key = cast(str, row[0])
            if signals:
                to_id = _execute(
                    db,
                    budget,
                    "SELECT "
                    + _text("to_eval_id", 69)
                    + " FROM wl_journal_signals WHERE signal_id=?",
                    (key,),
                ).fetchone()[0]
                item = next(
                    item for item in _signals_for(db, budget, to_id) if item["signal_id"] == key
                )
            else:
                loaded = _load_evaluation(db, budget, key)
                if loaded is None:
                    raise JournalError("storage_corrupt")
                item = loaded
                item["signal_ids"] = [
                    signal["signal_id"] for signal in _signals_for(db, budget, key)
                ]
            candidate = {
                "version": 1,
                "operation": operation,
                "result": "ok",
                table: items + [item],
                "next_cursor": _encode_cursor(binding, key),
            }
            if (
                len(json.dumps(candidate, ensure_ascii=True, separators=(",", ":")))
                > MAX_PAGE_BYTES
            ):
                if not items:
                    raise JournalError("input_limit")
                next_cursor = _encode_cursor(binding, last)
                break
            items.append(item)
            last = key
        response: dict[str, object] = {
            "version": 1,
            "operation": operation,
            "result": "ok",
            table: items,
            "next_cursor": next_cursor,
        }
        budget.remaining()
    return response


def list_evaluations(
    path: Path,
    *,
    sequence_id: object = None,
    watch_id: object = None,
    revision: object = None,
    limit: int = 100,
    cursor: object = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, object]:
    return _list(
        path,
        signals=False,
        sequence_id=sequence_id,
        watch_id=watch_id,
        revision=revision,
        rule=None,
        limit=limit,
        cursor=cursor,
        timeout=timeout,
    )


def signal_list(
    path: Path,
    *,
    sequence_id: object = None,
    watch_id: object = None,
    revision: object = None,
    rule: object = None,
    limit: int = 100,
    cursor: object = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, object]:
    return _list(
        path,
        signals=True,
        sequence_id=sequence_id,
        watch_id=watch_id,
        revision=revision,
        rule=rule,
        limit=limit,
        cursor=cursor,
        timeout=timeout,
    )


def _cleanup_reserved(path: Path, identity: tuple[int, int]) -> None:
    """Only our inode may be removed, and SQLite recovery evidence is retained."""
    with suppress(OSError, PersistenceError):
        information = paths._unsafe_stat(path, file=True)
        if (information.st_dev, information.st_ino) != identity:
            return
        if any(paths._exists(sidecar) for sidecar in paths._sidecars(path)):
            return
        path.unlink()


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
                    db,
                    budget,
                    "INSERT INTO wl_journal_metadata VALUES (?,?,?)",
                    (1, schema.OWNER, 1),
                )
                _execute(db, budget, f"PRAGMA application_id={schema.APPLICATION_ID}")
                _execute(db, budget, "PRAGMA user_version=1")
                _verify(db, budget)
        completed = True
        return {"version": 1, "operation": "init", "result": "ok", "schema_version": 1}
    except PersistenceError as error:
        raise JournalError(error.category) from None
    except OSError:
        raise JournalError("storage_io") from None
    finally:
        if not completed and identity is not None:
            _cleanup_reserved(target, identity)


def _rollback_publication(provisional: Path, destination: Path, identity: tuple[int, int]) -> None:
    """Remove only our new link when the verified inode still has both names."""
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
    """Expose only a verified complete file, atomically and without replacement."""
    target = _path(destination, new=True)
    information = paths._unsafe_stat(provisional, file=True)
    if (information.st_dev, information.st_ino) != identity:
        raise JournalError("unsafe_destination")
    if any(paths._exists(sidecar) for sidecar in paths._sidecars(provisional)):
        raise JournalError("unsafe_destination")
    # link() has exclusive create semantics on both supported operating systems.
    # Trusted directory ownership is required, as with every earlier storage owner.
    try:
        os.link(provisional, target)
    except FileExistsError:
        raise JournalError("unsafe_destination") from None
    try:
        provisional.unlink()
    except OSError:
        _rollback_publication(provisional, target, identity)
        raise


def _copy(source: Path, destination: Path, operation: str, timeout: float) -> dict[str, object]:
    budget = Budget(timeout)
    provisional: Path | None = None
    identity: tuple[int, int] | None = None
    completed = False
    try:
        target = _path(destination, new=True)
        with _connect(source, budget) as reader, _transaction(reader, budget):
            _verify(reader, budget)
            provisional = target.parent / (".cmt-watchlist-journal-" + uuid.uuid4().hex + ".tmp")
            _path(provisional, new=True)
            identity = paths._reserve(provisional)
            with _connect(provisional, budget, writable=True) as writer:
                information = provisional.lstat()
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
        with _connect(provisional, budget) as reopened, _transaction(reopened, budget):
            if _verify(reopened, budget) != counts:
                raise JournalError("storage_corrupt")
        # fsync the complete verified inode before publishing its destination name.
        with provisional.open("r+b") as stream:
            os.fsync(stream.fileno())
        budget.remaining()
        _publish(provisional, target, identity)
        completed = True
        return {"version": 1, "operation": operation, "result": "ok", "counts": counts}
    except PersistenceError as error:
        raise JournalError(error.category) from None
    except OSError:
        raise JournalError("storage_io") from None
    finally:
        if not completed and identity is not None and provisional is not None:
            _cleanup_reserved(provisional, identity)


def backup(
    source: Path, destination: Path, *, timeout: float = DEFAULT_TIMEOUT
) -> dict[str, object]:
    return _copy(source, destination, "backup", timeout)


def restore(
    source: Path, destination: Path, *, timeout: float = DEFAULT_TIMEOUT
) -> dict[str, object]:
    return _copy(source, destination, "restore", timeout)
