"""Independent guarded Telegram ledger; immutable claims and fenced final outcomes."""

import hashlib
import json
import math
import os
import re
import secrets
import sqlite3
import time
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

from ..persistence import sqlite_repository as paths
from ..persistence.errors import PersistenceError
from . import schema
from .errors import DeliveryError

DEFAULT_TIMEOUT = 2.0
MAX_RESULT_BYTES = 65536
MAX_PAGE_BYTES = 1024 * 1024
MAX_LIMIT = 1000
MAX_PROVIDER_ID = 2**52 - 1
STATES = frozenset(
    {"ready", "in_flight", "retryable", "confirmed", "permanent_failure", "uncertain"}
)
_PERMANENT_CATEGORIES = frozenset({"provider_rejection", "provider_rejected", "retry_exhausted"})
_UNCERTAIN_CATEGORIES = frozenset(
    {
        "network_uncertain",
        "malformed_response",
        "deadline_exceeded",
        "local_commit_failed",
        "transport_timeout",
        "transport_failure",
        "provider_invalid",
        "token_configuration",
        "bot_mismatch",
        "destination_mismatch",
        "confirmation_failed",
        "recovered",
    }
)
OUTCOME_CATEGORIES = (
    _PERMANENT_CATEGORIES | _UNCERTAIN_CATEGORIES | {"rate_limited", "provider_rate_limit"}
)
BINDING_FIELDS = (
    "alert_id",
    "event_id",
    "comparison_id",
    "alias",
    "intent_sha256",
    "message_sha256",
    "event_sha256",
    "journal_content_sha256",
    "alert_content_sha256",
    "evidence_content_sha256",
)
_HEX = re.compile(r"[0-9a-f]{64}")
_STAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z")


class Budget:
    """A bounded monotonic budget for one local ledger operation."""

    def __init__(self, timeout: float = DEFAULT_TIMEOUT) -> None:
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 5:
            raise DeliveryError("invalid_field")
        self.deadline = time.monotonic() + timeout

    def remaining(self) -> float:
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise DeliveryError("storage_timeout")
        return remaining

    def progress(self) -> int:
        return int(time.monotonic() >= self.deadline)


def canonical_json(value: object) -> str:
    try:
        return json.dumps(
            value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise DeliveryError("storage_corrupt") from None


def _token(value: object, prefix: str) -> str:
    if type(value) is not str or not value.startswith(prefix) or not _HEX.fullmatch(value[5:]):
        raise DeliveryError("invalid_field")
    return value


def _stamp(value: object) -> str:
    if type(value) is not str or not _STAMP.fullmatch(value):
        raise DeliveryError("storage_corrupt")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        raise DeliveryError("storage_corrupt") from None
    return value


def _path(value: Path, *, new: bool = False) -> Path:
    try:
        path = paths._checked_path(value)
        exists = paths._exists(path)
        if new and exists:
            raise DeliveryError("unsafe_destination")
        if not new and not exists:
            raise DeliveryError("storage_missing")
        paths._check_sidecars(path, new=new)
        return path
    except PersistenceError as error:
        raise DeliveryError(error.category) from None
    except OSError:
        raise DeliveryError("storage_io") from None


def reject_same_file(first: Path, second: Path) -> None:
    """Validate both existing paths before capture IO; aliases never cross owners."""
    left, right = _path(first), _path(second)
    try:
        if os.path.samefile(left, right):
            raise DeliveryError("unsafe_destination")
    except OSError:
        raise DeliveryError("storage_io") from None


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
            raise DeliveryError("unsafe_destination")
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
            raise DeliveryError("storage_schema")
        if not writable:
            _execute(db, budget, "PRAGMA query_only=ON")
        yield db
        budget.remaining()
    except PersistenceError as error:
        raise DeliveryError(error.category) from None
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
        raise DeliveryError(category) from None
    except OSError:
        raise DeliveryError("storage_io") from None
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


def _schema(db: sqlite3.Connection, budget: Budget) -> bool:
    if (
        _execute(db, budget, "PRAGMA application_id").fetchone()[0] != schema.APPLICATION_ID
        or _execute(db, budget, "PRAGMA user_version").fetchone()[0] != schema.SCHEMA_VERSION
        or _execute(db, budget, "PRAGMA journal_mode").fetchone()[0] != "delete"
    ):
        raise DeliveryError("storage_schema")
    expected = schema.expected_inventory()
    objects = tuple(
        tuple(row)
        for row in _execute(
            db,
            budget,
            "SELECT "
            + ",".join(_text(column, 32768) for column in ("type", "name", "tbl_name"))
            + ",CASE WHEN sql IS NULL THEN NULL ELSE "
            + _text("sql", 32768)
            + " END FROM sqlite_master ORDER BY type,name LIMIT ?",
            (len(expected) + 1,),
        )
    )
    if objects != expected:
        raise DeliveryError("storage_schema")
    metadata = _execute(
        db,
        budget,
        "SELECT "
        + _version_integer("singleton")
        + ","
        + _text("owner", 128)
        + ","
        + _version_integer("schema_version")
        + ",CASE WHEN typeof(send_quarantined)='integer' AND send_quarantined IN (0,1) "
        "THEN send_quarantined END FROM delivery_metadata LIMIT 2",
    )
    rows = [tuple(row) for row in metadata]
    if len(rows) != 1 or rows[0][:3] != (1, schema.OWNER, schema.SCHEMA_VERSION):
        raise DeliveryError("storage_schema")
    if type(rows[0][3]) is not int or rows[0][3] not in (0, 1):
        raise DeliveryError("storage_corrupt")
    return bool(rows[0][3])


def _integrity(db: sqlite3.Connection, budget: Budget) -> None:
    # The one-result limit avoids unbounded corruption diagnostics.
    result = _execute(db, budget, "PRAGMA integrity_check(1)").fetchone()
    if result is None or result[0] != "ok":
        raise DeliveryError("storage_corrupt")
    if _execute(db, budget, "PRAGMA foreign_key_check").fetchone() is not None:
        raise DeliveryError("storage_corrupt")


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("ascii")).hexdigest()


def _integer(value: object, maximum: int = MAX_PROVIDER_ID) -> int:
    if type(value) is not int or not 1 <= value <= maximum:
        raise DeliveryError("invalid_field")
    return value


def _alias(value: object) -> str:
    if type(value) is not str or not re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", value):
        raise DeliveryError("invalid_destination")
    return value


def delivery_id(alert_id: str) -> str:
    aid = _token(alert_id, "alt1:")
    return "tdl1:" + _digest({"identity_version": 1, "alert_id": aid, "provider": "telegram"})


def _binding(value: object) -> dict[str, object]:
    if type(value) is not dict or set(value) != set(BINDING_FIELDS):
        raise DeliveryError("unsupported_evidence")
    item = cast(dict[str, object], value)
    for key, prefix in (("alert_id", "alt1:"), ("event_id", "evt3:"), ("comparison_id", "cmp3:")):
        _token(item[key], prefix)
    _alias(item["alias"])
    for key in BINDING_FIELDS[4:]:
        raw = item[key]
        if type(raw) is not str or not _HEX.fullmatch(raw):
            raise DeliveryError("invalid_field")
    expected = "alt1:" + _digest(
        {"identity_version": 1, "destination_key": item["alias"], "event_id": item["event_id"]}
    )
    if item["alert_id"] != expected:
        raise DeliveryError("unsupported_evidence")
    return dict(item)


_DEST_FIELDS = (
    "alias",
    "provider",
    "bot_id",
    "chat_id",
    "chat_type",
    "operator_attested_owner",
    "validated_at",
    "route_sha256",
)
_DELIVERY_FIELDS = (
    "delivery_id",
    "alert_id",
    "event_id",
    "provider",
    "alias",
    "comparison_id",
    *BINDING_FIELDS[4:],
    "route_sha256",
    "state",
    "attempt_count",
    "current_attempt_id",
    "not_before",
    "created_at",
    "updated_at",
)
_ATTEMPT_FIELDS = ("attempt_id", "delivery_id", "ordinal", "claimed_at")
_RESULT_FIELDS = (
    "attempt_id",
    "state",
    "completed_at",
    "error_category",
    "retry_after",
    "not_before",
    "message_id",
    "accepted_at",
    "bot_id",
    "chat_id",
)
# Constants alone enter the SQL projection. Guard every cell before materialization.
_TEXT_BOUNDS = {
    "alias": 64,
    "provider": 8,
    "chat_type": 7,
    "validated_at": 27,
    "route_sha256": 64,
    "delivery_id": 69,
    "alert_id": 69,
    "event_id": 69,
    "comparison_id": 69,
    "state": 17,
    "current_attempt_id": 69,
    "not_before": 27,
    "created_at": 27,
    "updated_at": 27,
    "attempt_id": 69,
    "claimed_at": 27,
    "completed_at": 27,
    "error_category": 64,
    **dict.fromkeys(BINDING_FIELDS[4:], 64),
}
_INT_BOUNDS = {
    "bot_id": MAX_PROVIDER_ID,
    "chat_id": MAX_PROVIDER_ID,
    "operator_attested_owner": 1,
    "attempt_count": 3,
    "ordinal": 3,
    "retry_after": 86400,
    "message_id": 2**63 - 1,
    "accepted_at": 253402300799,
}


def _projection(fields: tuple[str, ...]) -> str:
    expressions: list[str] = []
    for key in fields:
        if key in _TEXT_BOUNDS:
            expression = (
                f"CASE WHEN {key} IS NULL THEN NULL WHEN typeof({key})='text' AND "
                f"length(CAST({key} AS BLOB)) BETWEEN 1 AND {_TEXT_BOUNDS[key]} "
                f"THEN {key} ELSE -1 END"
            )
        else:
            expression = (
                f"CASE WHEN {key} IS NULL THEN NULL WHEN typeof({key})='integer' AND "
                f"{key} BETWEEN 0 AND {_INT_BOUNDS[key]} THEN {key} ELSE -1 END"
            )
        expressions.append(expression)
    return ",".join(expressions)


def _route(item: dict[str, object]) -> dict[str, object]:
    return {
        key: item[key]
        for key in (
            "alias",
            "provider",
            "bot_id",
            "chat_id",
            "chat_type",
            "operator_attested_owner",
        )
    }


def _load_destination(db: sqlite3.Connection, alias: str, budget: Budget) -> dict[str, object]:
    row = _execute(
        db,
        budget,
        "SELECT " + _projection(_DEST_FIELDS) + " FROM destinations WHERE alias=?",
        (alias,),
    ).fetchone()
    if row is None:
        raise DeliveryError("storage_missing")
    item = dict(zip(_DEST_FIELDS, row, strict=True))
    try:
        if item["alias"] != _alias(alias) or item["provider"] != "telegram":
            raise DeliveryError("storage_corrupt")
        _integer(item["bot_id"])
        _integer(item["chat_id"])
        if item["chat_type"] != "private" or item["operator_attested_owner"] != 1:
            raise DeliveryError("storage_corrupt")
        item["operator_attested_owner"] = True
        if item["validated_at"] is not None:
            _stamp(item["validated_at"])
        if item["route_sha256"] != _digest(_route(item)):
            raise DeliveryError("storage_corrupt")
    except DeliveryError:
        raise DeliveryError("storage_corrupt") from None
    return item


def _load_result(
    db: sqlite3.Connection, attempt_id: str, route: dict[str, object], budget: Budget
) -> dict[str, object] | None:
    row = _execute(
        db,
        budget,
        "SELECT "
        + _projection(_RESULT_FIELDS)
        + " FROM delivery_attempt_results WHERE attempt_id=?",
        (attempt_id,),
    ).fetchone()
    if row is None:
        return None
    item = dict(zip(_RESULT_FIELDS, row, strict=True))
    try:
        if item["attempt_id"] != attempt_id:
            raise DeliveryError("storage_corrupt")
        _stamp(item["completed_at"])
        state = item["state"]
        if state not in {"retryable", "confirmed", "permanent_failure", "uncertain"}:
            raise DeliveryError("storage_corrupt")
        receipt_keys = ("message_id", "accepted_at", "bot_id", "chat_id")
        if state == "confirmed":
            _integer(item["message_id"], 2**63 - 1)
            _integer(item["accepted_at"], 253402300799)
            if item["bot_id"] != route["bot_id"] or item["chat_id"] != route["chat_id"]:
                raise DeliveryError("storage_corrupt")
            if item["error_category"] is not None:
                raise DeliveryError("storage_corrupt")
        elif any(item[key] is not None for key in receipt_keys):
            raise DeliveryError("storage_corrupt")
        elif item["error_category"] not in (
            _PERMANENT_CATEGORIES
            if state == "permanent_failure"
            else _UNCERTAIN_CATEGORIES
            if state == "uncertain"
            else {"rate_limited"}
        ):
            raise DeliveryError("storage_corrupt")
        if state == "retryable":
            seconds = _integer(item["retry_after"], 86400)
            _stamp(item["not_before"])
            if item["error_category"] != "rate_limited" or item["not_before"] != _after(
                cast(str, item["completed_at"]), seconds
            ):
                raise DeliveryError("storage_corrupt")
        elif item["retry_after"] is not None or item["not_before"] is not None:
            raise DeliveryError("storage_corrupt")
        if item["error_category"] == "retry_exhausted" and state != "permanent_failure":
            raise DeliveryError("storage_corrupt")
        if item["error_category"] == "recovered" and state != "uncertain":
            raise DeliveryError("storage_corrupt")
    except (DeliveryError, OverflowError, ValueError):
        raise DeliveryError("storage_corrupt") from None
    return item


def _after(stamp: str, seconds: int) -> str:
    return (
        (
            datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=UTC)
            + timedelta(seconds=seconds)
        )
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _load_delivery(db: sqlite3.Connection, did: str, budget: Budget) -> dict[str, object]:
    row = _execute(
        db,
        budget,
        "SELECT " + _projection(_DELIVERY_FIELDS) + " FROM deliveries WHERE delivery_id=?",
        (did,),
    ).fetchone()
    if row is None:
        raise DeliveryError("storage_missing")
    item = dict(zip(_DELIVERY_FIELDS, row, strict=True))
    try:
        _binding({key: item[key] for key in BINDING_FIELDS})
        if item["delivery_id"] != did or delivery_id(cast(str, item["alert_id"])) != did:
            raise DeliveryError("storage_corrupt")
        if item["provider"] != "telegram" or item["state"] not in STATES:
            raise DeliveryError("storage_corrupt")
        route = _load_destination(db, cast(str, item["alias"]), budget)
        if route["route_sha256"] != item["route_sha256"] or route["validated_at"] is None:
            raise DeliveryError("storage_corrupt")
        _stamp(item["created_at"])
        _stamp(item["updated_at"])
        if cast(str, route["validated_at"]) > cast(str, item["created_at"]):
            raise DeliveryError("storage_corrupt")
        attempts: list[dict[str, object]] = []
        expected_state: object = "ready"
        expected_active: object = None
        expected_not_before: object = None
        previous_stamp = cast(str, item["created_at"])
        for claim_row in _execute(
            db,
            budget,
            "SELECT "
            + _projection(_ATTEMPT_FIELDS)
            + " FROM delivery_attempts WHERE delivery_id=? ORDER BY ordinal LIMIT 4",
            (did,),
        ):
            budget.remaining()
            claim = dict(zip(_ATTEMPT_FIELDS, claim_row, strict=True))
            ordinal = len(attempts) + 1
            if ordinal > 3 or claim["ordinal"] != ordinal or claim["delivery_id"] != did:
                raise DeliveryError("storage_corrupt")
            aid = _token(claim["attempt_id"], "tat1:")
            claimed_at = _stamp(claim["claimed_at"])
            if claimed_at < previous_stamp or expected_state not in {"ready", "retryable"}:
                raise DeliveryError("storage_corrupt")
            if expected_not_before is not None and claimed_at < cast(str, expected_not_before):
                raise DeliveryError("storage_corrupt")
            outcome = _load_result(db, aid, route, budget)
            if outcome is None:
                expected_state, expected_active, expected_not_before = "in_flight", aid, None
                previous_stamp = claimed_at
            else:
                completed_at = cast(str, outcome["completed_at"])
                if completed_at < claimed_at:
                    raise DeliveryError("storage_corrupt")
                if outcome["state"] == "retryable" and ordinal >= 3:
                    raise DeliveryError("storage_corrupt")
                if outcome["error_category"] == "retry_exhausted" and ordinal != 3:
                    raise DeliveryError("storage_corrupt")
                expected_state, expected_active = outcome["state"], None
                expected_not_before = outcome["not_before"]
                previous_stamp = completed_at
            claim["result"] = outcome
            attempts.append(claim)
        if (
            type(item["attempt_count"]) is not int
            or item["attempt_count"] != len(attempts)
            or item["state"] != expected_state
            or item["current_attempt_id"] != expected_active
            or item["not_before"] != expected_not_before
            or item["updated_at"] != previous_stamp
        ):
            raise DeliveryError("storage_corrupt")
    except DeliveryError as error:
        if error.category == "storage_timeout":
            raise
        raise DeliveryError("storage_corrupt") from None
    return {
        **item,
        **{
            key: route[key]
            for key in ("bot_id", "chat_id", "chat_type", "operator_attested_owner", "validated_at")
        },
        "attempts": attempts,
    }


def _verify(db: sqlite3.Connection, budget: Budget) -> tuple[dict[str, int], bool]:
    quarantined = _schema(db, budget)
    _integrity(db, budget)
    counts = {"destinations": 0, "deliveries": 0, "attempts": 0, "results": 0}
    for row in _execute(
        db, budget, "SELECT " + _text("alias", 64) + " FROM destinations ORDER BY alias"
    ):
        budget.remaining()
        try:
            alias = _alias(row[0])
        except DeliveryError:
            raise DeliveryError("storage_corrupt") from None
        _load_destination(db, alias, budget)
        counts["destinations"] += 1
    for row in _execute(
        db,
        budget,
        "SELECT " + _text("delivery_id", 69, 69) + " FROM deliveries ORDER BY delivery_id",
    ):
        budget.remaining()
        try:
            did = _token(row[0], "tdl1:")
        except DeliveryError:
            raise DeliveryError("storage_corrupt") from None
        item = _load_delivery(db, did, budget)
        attempts = cast(list[dict[str, object]], item["attempts"])
        counts["deliveries"] += 1
        counts["attempts"] += len(attempts)
        counts["results"] += sum(claim["result"] is not None for claim in attempts)
    for key, table in (("attempts", "delivery_attempts"), ("results", "delivery_attempt_results")):
        if _execute(db, budget, "SELECT count(*) FROM " + table).fetchone()[0] != counts[key]:
            raise DeliveryError("storage_corrupt")
    return counts, quarantined


def _safe_delivery(item: dict[str, object]) -> dict[str, object]:
    result = {
        key: value
        for key, value in item.items()
        if key
        not in {
            "bot_id",
            "chat_id",
            "operator_attested_owner",
            "chat_type",
            "validated_at",
            "attempts",
        }
    }
    result["attempts"] = [
        {
            **{key: value for key, value in claim.items() if key != "result"},
            "result": None
            if claim["result"] is None
            else {
                key: value
                for key, value in cast(dict[str, object], claim["result"]).items()
                if key not in {"bot_id", "chat_id"}
            },
        }
        for claim in cast(list[dict[str, object]], item["attempts"])
    ]
    return result


def _envelope(operation: str, result: str = "ok", **values: object) -> dict[str, object]:
    return {"version": 1, "operation": operation, "result": result, **values}


def load_destination(
    path: Path, alias: str, *, timeout: float = DEFAULT_TIMEOUT
) -> dict[str, object]:
    budget = Budget(timeout)
    alias = _alias(alias)
    with _connect(path, budget) as db, _transaction(db, budget):
        _schema(db, budget)
        return _load_destination(db, alias, budget)


def load_delivery(
    path: Path, delivery_id: str, *, timeout: float = DEFAULT_TIMEOUT
) -> dict[str, object]:
    budget = Budget(timeout)
    did = _token(delivery_id, "tdl1:")
    with _connect(path, budget) as db, _transaction(db, budget):
        quarantine = _schema(db, budget)
        return {**_load_delivery(db, did, budget), "send_quarantined": quarantine}


def get(path: Path, delivery_id: str, *, timeout: float = DEFAULT_TIMEOUT) -> dict[str, object]:
    item = load_delivery(path, delivery_id, timeout=timeout)
    return _envelope(
        "get", delivery=_safe_delivery(item), send_quarantined=item["send_quarantined"]
    )


def verify(path: Path, *, timeout: float = DEFAULT_TIMEOUT) -> dict[str, object]:
    budget = Budget(timeout)
    with _connect(path, budget) as db, _transaction(db, budget):
        counts, quarantine = _verify(db, budget)
    return _envelope("verify", level="local", counts=counts, send_quarantined=quarantine)


def list_deliveries(
    path: Path,
    *,
    state: str | None = None,
    cursor: str | None = None,
    limit: int = 100,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, object]:
    budget = Budget(timeout)
    if type(limit) is not int or not 1 <= limit <= MAX_LIMIT:
        raise DeliveryError("invalid_field")
    if state is not None and (type(state) is not str or state not in STATES):
        raise DeliveryError("invalid_field")
    marker = "" if cursor is None else _token(cursor, "tdl1:")
    items: list[dict[str, object]] = []
    page_bytes = 2
    next_cursor: str | None = None
    with _connect(path, budget) as db, _transaction(db, budget):
        quarantine = _schema(db, budget)
        rows = _execute(
            db,
            budget,
            "SELECT "
            + _text("delivery_id", 69, 69)
            + " FROM deliveries WHERE delivery_id>?"
            + (" AND state=?" if state else "")
            + " ORDER BY delivery_id LIMIT ?",
            (marker, state, limit + 1) if state else (marker, limit + 1),
        )
        for row in rows:
            budget.remaining()
            if len(items) == limit:
                next_cursor = cast(str, items[-1]["delivery_id"])
                break
            try:
                did = _token(row[0], "tdl1:")
            except DeliveryError:
                raise DeliveryError("storage_corrupt") from None
            item = _safe_delivery(_load_delivery(db, did, budget))
            page_bytes += len(canonical_json(item)) + 1
            if page_bytes > MAX_PAGE_BYTES:
                raise DeliveryError("input_limit")
            items.append(item)
    return _envelope("list", items=items, next_cursor=next_cursor, send_quarantined=quarantine)


def destination_add(
    path: Path,
    alias: str,
    bot_id: int,
    chat_id: int,
    *,
    operator_private_owned: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, object]:
    budget = Budget(timeout)
    alias = _alias(alias)
    _integer(bot_id)
    _integer(chat_id)
    if operator_private_owned is not True:
        raise DeliveryError("invalid_destination")
    route: dict[str, object] = {
        "alias": alias,
        "provider": "telegram",
        "bot_id": bot_id,
        "chat_id": chat_id,
        "chat_type": "private",
        "operator_attested_owner": True,
    }
    route_digest = _digest(route)
    result = "inserted"
    with _connect(path, budget, writable=True) as db:
        _execute(db, budget, "PRAGMA synchronous=FULL")
        with _transaction(db, budget, write=True):
            _schema(db, budget)
            present = _execute(
                db, budget, "SELECT 1 FROM destinations WHERE alias=?", (alias,)
            ).fetchone()
            if present is not None:
                previous = _load_destination(db, alias, budget)
                if previous["route_sha256"] != route_digest:
                    raise DeliveryError("conflict")
                result = "replay"
            else:
                _execute(
                    db,
                    budget,
                    "INSERT INTO destinations VALUES (?,?,?,?,?,?,?,?)",
                    (alias, "telegram", bot_id, chat_id, "private", 1, None, route_digest),
                )
    return _envelope("destination-add", result, alias=alias)


def destination_validated(
    path: Path,
    alias: str,
    bot_id: int,
    chat_id: int,
    *,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, object]:
    budget = Budget(timeout)
    alias = _alias(alias)
    _integer(bot_id)
    _integer(chat_id)
    with _connect(path, budget, writable=True) as db:
        _execute(db, budget, "PRAGMA synchronous=FULL")
        with _transaction(db, budget, write=True):
            _schema(db, budget)
            previous = _load_destination(db, alias, budget)
            if previous["bot_id"] != bot_id or previous["chat_id"] != chat_id:
                raise DeliveryError("conflict")
            result = "replay" if previous["validated_at"] is not None else "ok"
            if previous["validated_at"] is None:
                _execute(
                    db,
                    budget,
                    "UPDATE destinations SET validated_at=? WHERE alias=? AND validated_at IS NULL",
                    (_now(), alias),
                )
    return _envelope("destination-validate", result, alias=alias)


def _receipt_binding(receipt: object) -> dict[str, object]:
    from .application import _consume_receipt

    return _binding(_consume_receipt(receipt))


def _prepare_verified(
    path: Path,
    receipt: object,
    *,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, object]:
    budget = Budget(timeout)
    bound = _receipt_binding(receipt)
    did = delivery_id(cast(str, bound["alert_id"]))
    result = "inserted"
    with _connect(path, budget, writable=True) as db:
        _execute(db, budget, "PRAGMA synchronous=FULL")
        with _transaction(db, budget, write=True):
            _schema(db, budget)
            route = _load_destination(db, cast(str, bound["alias"]), budget)
            if route["validated_at"] is None:
                raise DeliveryError("not_validated")
            other = _execute(
                db,
                budget,
                "SELECT "
                + _text("delivery_id", 69, 69)
                + " FROM deliveries WHERE provider='telegram' "
                "AND (alert_id=? OR event_id=?) LIMIT 2",
                (bound["alert_id"], bound["event_id"]),
            ).fetchall()
            if other:
                if len(other) != 1 or other[0][0] != did:
                    raise DeliveryError("conflict")
                previous = _load_delivery(db, did, budget)
                if (
                    any(previous[key] != bound[key] for key in BINDING_FIELDS)
                    or previous["route_sha256"] != route["route_sha256"]
                ):
                    raise DeliveryError("conflict")
                result = "replay"
            else:
                stamp = _now()
                if stamp < cast(str, route["validated_at"]):
                    raise DeliveryError("delivery_blocked")
                item = {
                    **bound,
                    "delivery_id": did,
                    "provider": "telegram",
                    "route_sha256": route["route_sha256"],
                    "state": "ready",
                    "attempt_count": 0,
                    "current_attempt_id": None,
                    "not_before": None,
                    "created_at": stamp,
                    "updated_at": stamp,
                }
                _execute(
                    db,
                    budget,
                    "INSERT INTO deliveries VALUES ("
                    + ",".join("?" for _ in _DELIVERY_FIELDS)
                    + ")",
                    tuple(item[key] for key in _DELIVERY_FIELDS),
                )
    return _envelope(
        "prepare",
        result,
        delivery_id=did,
        state="ready" if result == "inserted" else previous["state"],
    )


def _claim_verified(
    path: Path,
    delivery_id: str,
    receipt: object,
    *,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, object]:
    budget = Budget(timeout)
    did = _token(delivery_id, "tdl1:")
    bound = _receipt_binding(receipt)
    with _connect(path, budget, writable=True) as db:
        _execute(db, budget, "PRAGMA synchronous=FULL")
        with _transaction(db, budget, write=True):
            quarantined = _schema(db, budget)
            item = _load_delivery(db, did, budget)
            if any(item[key] != bound[key] for key in BINDING_FIELDS):
                raise DeliveryError("conflict")
            if item["state"] == "confirmed":
                return _envelope("claim", "replay", delivery_id=did, delivery=item)
            if quarantined:
                raise DeliveryError("send_quarantined")
            if item["state"] not in {"ready", "retryable"}:
                raise DeliveryError("delivery_blocked")
            if cast(int, item["attempt_count"]) >= 3:
                raise DeliveryError("attempt_limit")
            now = _now()
            if now < cast(str, item["updated_at"]):
                raise DeliveryError("delivery_blocked")
            if item["not_before"] is not None and now < cast(str, item["not_before"]):
                raise DeliveryError("retry_not_due")
            aid, ordinal = "tat1:" + secrets.token_hex(32), cast(int, item["attempt_count"]) + 1
            _execute(
                db,
                budget,
                "INSERT INTO delivery_attempts VALUES (?,?,?,?)",
                (aid, did, ordinal, now),
            )
            changed = _execute(
                db,
                budget,
                "UPDATE deliveries SET state='in_flight',attempt_count=?,current_attempt_id=?,"
                "not_before=NULL,updated_at=? WHERE delivery_id=? AND state=? AND attempt_count=? "
                "AND current_attempt_id IS NULL",
                (ordinal, aid, now, did, item["state"], item["attempt_count"]),
            ).rowcount
            if changed != 1:
                raise DeliveryError("stale_attempt")
            claimed = _load_delivery(db, did, budget)
    return _envelope(
        "claim", "claimed", delivery_id=did, delivery=claimed, attempt_id=aid, ordinal=ordinal
    )


def _finish(
    db: sqlite3.Connection,
    budget: Budget,
    item: dict[str, object],
    attempt_id: str,
    *,
    state: str,
    error_category: str | None,
    receipt: dict[str, object] | None,
    retry_after: int | None,
) -> str:
    if item["state"] != "in_flight" or item["current_attempt_id"] != attempt_id:
        raise DeliveryError("stale_attempt")
    if type(state) is not str or state not in {
        "confirmed",
        "permanent_failure",
        "retryable",
        "uncertain",
    }:
        raise DeliveryError("invalid_field")
    stamp = _now()
    if stamp < cast(str, item["updated_at"]):
        raise DeliveryError("delivery_blocked")
    if state == "confirmed":
        if type(receipt) is not dict or set(receipt) != {
            "message_id",
            "accepted_at",
            "bot_id",
            "chat_id",
        }:
            raise DeliveryError("invalid_field")
        _integer(receipt["message_id"], 2**63 - 1)
        _integer(receipt["accepted_at"], 253402300799)
        _integer(receipt["bot_id"])
        _integer(receipt["chat_id"])
        if receipt["bot_id"] != item["bot_id"] or receipt["chat_id"] != item["chat_id"]:
            raise DeliveryError("conflict")
        if error_category is not None or retry_after is not None:
            raise DeliveryError("invalid_field")
    else:
        if (
            receipt is not None
            or type(error_category) is not str
            or error_category not in OUTCOME_CATEGORIES
        ):
            raise DeliveryError("invalid_field")
        if state == "retryable":
            _integer(retry_after, 86400)
            if error_category not in {"rate_limited", "provider_rate_limit"}:
                raise DeliveryError("invalid_field")
            error_category = "rate_limited"
            if item["attempt_count"] == 3:
                state, error_category, retry_after = "permanent_failure", "retry_exhausted", None
        elif retry_after is not None:
            raise DeliveryError("invalid_field")
    if state == "permanent_failure" and error_category not in _PERMANENT_CATEGORIES:
        raise DeliveryError("invalid_field")
    if state == "uncertain" and error_category not in _UNCERTAIN_CATEGORIES:
        raise DeliveryError("invalid_field")
    if error_category == "recovered" and state != "uncertain":
        raise DeliveryError("invalid_field")
    if error_category == "retry_exhausted" and (
        state != "permanent_failure" or item["attempt_count"] != 3
    ):
        raise DeliveryError("invalid_field")
    try:
        not_before = _after(stamp, cast(int, retry_after)) if state == "retryable" else None
    except (ValueError, OverflowError):
        raise DeliveryError("invalid_field") from None
    values = (attempt_id, state, stamp, error_category, retry_after, not_before) + tuple(
        None if receipt is None else receipt[key]
        for key in ("message_id", "accepted_at", "bot_id", "chat_id")
    )
    _execute(
        db, budget, "INSERT INTO delivery_attempt_results VALUES (?,?,?,?,?,?,?,?,?,?)", values
    )
    changed = _execute(
        db,
        budget,
        "UPDATE deliveries SET state=?,current_attempt_id=NULL,not_before=?,updated_at=? "
        "WHERE delivery_id=? AND current_attempt_id=? AND state='in_flight'",
        (state, not_before, stamp, item["delivery_id"], attempt_id),
    ).rowcount
    if changed != 1:
        raise DeliveryError("stale_attempt")
    _load_delivery(db, cast(str, item["delivery_id"]), budget)
    return state


def finish(
    path: Path,
    delivery_id: str,
    attempt_id: str,
    *,
    state: str,
    error_category: str | None = None,
    receipt: dict[str, object] | None = None,
    retry_after: int | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, object]:
    budget = Budget(timeout)
    did, aid = _token(delivery_id, "tdl1:"), _token(attempt_id, "tat1:")
    with _connect(path, budget, writable=True) as db:
        _execute(db, budget, "PRAGMA synchronous=FULL")
        with _transaction(db, budget, write=True):
            _schema(db, budget)
            state = _finish(
                db,
                budget,
                _load_delivery(db, did, budget),
                aid,
                state=state,
                error_category=error_category,
                receipt=receipt,
                retry_after=retry_after,
            )
            last = cast(list[dict[str, object]], _load_delivery(db, did, budget)["attempts"])[-1]
            outcome = cast(dict[str, object], last["result"])
    response = _envelope("finish", delivery_id=did, attempt_id=aid, state=state)
    if outcome["error_category"] is not None:
        response["error_category"] = outcome["error_category"]
    return response


def recover(
    path: Path,
    delivery_id: str,
    *,
    worker_quiesced: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, object]:
    if worker_quiesced is not True:
        raise DeliveryError("delivery_blocked")
    budget = Budget(timeout)
    did = _token(delivery_id, "tdl1:")
    with _connect(path, budget, writable=True) as db:
        _execute(db, budget, "PRAGMA synchronous=FULL")
        with _transaction(db, budget, write=True):
            _schema(db, budget)
            item = _load_delivery(db, did, budget)
            if item["state"] != "in_flight":
                raise DeliveryError("delivery_blocked")
            aid = cast(str, item["current_attempt_id"])
            _finish(
                db,
                budget,
                item,
                aid,
                state="uncertain",
                error_category="recovered",
                receipt=None,
                retry_after=None,
            )
    return _envelope("recover", delivery_id=did, attempt_id=aid, state="uncertain")


def _cleanup_reserved(path: Path, identity: tuple[int, int]) -> None:
    """Remove only our unused inode; preserve SQLite sidecars and recovery evidence."""
    with suppress(OSError, PersistenceError):
        information = paths._unsafe_stat(path, file=True)
        if (information.st_dev, information.st_ino) != identity:
            return
        # SQLite owns recovery/sidecar removal. If anything remains after close,
        # retain the main file as well for recovery or operator investigation.
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
                raise DeliveryError("unsafe_destination")
            _execute(db, budget, "PRAGMA synchronous=FULL")
            with _transaction(db, budget, write=True):
                for statement in schema.STATEMENTS:
                    _execute(db, budget, statement)
                _execute(
                    db,
                    budget,
                    "INSERT INTO delivery_metadata VALUES (?,?,?,?)",
                    (1, schema.OWNER, 1, 0),
                )
                _execute(db, budget, f"PRAGMA application_id={schema.APPLICATION_ID}")
                _execute(db, budget, "PRAGMA user_version=1")
                _schema(db, budget)
        completed = True
        return {"version": 1, "operation": "init", "result": "ok", "schema_version": 1}
    except PersistenceError as error:
        raise DeliveryError(error.category) from None
    except OSError:
        raise DeliveryError("storage_io") from None
    finally:
        if not completed and identity is not None:
            _cleanup_reserved(target, identity)


def _assert_reserved(path: Path, identity: tuple[int, int]) -> None:
    information = paths._unsafe_stat(path, file=True)
    if (information.st_dev, information.st_ino) != identity:
        raise DeliveryError("unsafe_destination")


def _snapshot(reader: sqlite3.Connection, writer: sqlite3.Connection, budget: Budget) -> None:
    reader.execute("PRAGMA busy_timeout=0")
    writer.execute("PRAGMA busy_timeout=0")

    def progress(status: int, remaining: int, total: int) -> None:
        budget.remaining()

    reader.backup(writer, pages=32, progress=progress, sleep=0.01)


def _copy(source: Path, destination: Path, operation: str, timeout: float) -> dict[str, object]:
    budget = Budget(timeout)
    target: Path | None = None
    identity: tuple[int, int] | None = None
    staging: Path | None = None
    staging_identity: tuple[int, int] | None = None
    completed = False
    try:
        with _connect(source, budget) as reader, _transaction(reader, budget):
            expected_counts, source_quarantine = _verify(reader, budget)
            target = _path(destination, new=True)
            # Quarantine BEFORE a valid restored schema can appear at the final
            # pathname. Direct backup then UPDATE would leave a dispatch race.
            if operation == "restore":
                staging = target.with_name("." + target.name + ".restore-" + secrets.token_hex(16))
                staging = _path(staging, new=True)
                staging_identity = paths._reserve(staging)
                with _connect(staging, budget, writable=True) as stage:
                    _assert_reserved(staging, staging_identity)
                    _execute(stage, budget, "PRAGMA synchronous=FULL")
                    _snapshot(reader, stage, budget)
                    with _transaction(stage, budget, write=True):
                        _verify(stage, budget)
                        _execute(
                            stage,
                            budget,
                            "UPDATE delivery_metadata SET send_quarantined=1 WHERE singleton=1",
                        )
                        staged_counts, quarantine = _verify(stage, budget)
                        if staged_counts != expected_counts or not quarantine:
                            raise DeliveryError("storage_corrupt")
                    # The stage is owned and quarantined. Final target is a new,
                    # exclusively reserved file; its very first valid snapshot
                    # already has quarantine, including for absent deliveries.
                    identity = paths._reserve(target)
                    with _connect(target, budget, writable=True) as writer:
                        _assert_reserved(target, identity)
                        _execute(writer, budget, "PRAGMA synchronous=FULL")
                        _snapshot(stage, writer, budget)
                        with _transaction(writer, budget):
                            counts, quarantine = _verify(writer, budget)
            else:
                identity = paths._reserve(target)
                with _connect(target, budget, writable=True) as writer:
                    _assert_reserved(target, identity)
                    _execute(writer, budget, "PRAGMA synchronous=FULL")
                    _snapshot(reader, writer, budget)
                    with _transaction(writer, budget):
                        counts, quarantine = _verify(writer, budget)
            if counts != expected_counts or quarantine != (
                operation == "restore" or source_quarantine
            ):
                raise DeliveryError("storage_corrupt")
        with _connect(target, budget) as reopened, _transaction(reopened, budget):
            if _verify(reopened, budget) != (counts, quarantine):
                raise DeliveryError("storage_corrupt")
        completed = True
        if staging is not None and staging_identity is not None:
            _cleanup_reserved(staging, staging_identity)
        return _envelope(operation, counts=counts, send_quarantined=quarantine)
    except PersistenceError as error:
        raise DeliveryError(error.category) from None
    except OSError:
        raise DeliveryError("storage_io") from None
    finally:
        if not completed and identity is not None and target is not None:
            _cleanup_reserved(target, identity)
        # Failed staging DBs are deliberately retained as recovery evidence.


def backup(
    source: Path, destination: Path, *, timeout: float = DEFAULT_TIMEOUT
) -> dict[str, object]:
    return _copy(source, destination, "backup", timeout)


def restore(
    source: Path, destination: Path, *, timeout: float = DEFAULT_TIMEOUT
) -> dict[str, object]:
    return _copy(source, destination, "restore", timeout)
