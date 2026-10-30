"""Independent CMTZ ledger with immutable claims, semantic folds and fenced results."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import re
import secrets
import sqlite3
import stat
import uuid
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from datetime import datetime, timedelta
from pathlib import Path
from typing import cast

from ..catalog.validation import CatalogError, _constant, _pairs, _preflight
from ..persistence import sqlite_repository as paths
from ..persistence.errors import PersistenceError
from ..watchlist.errors import WatchlistError
from ..watchlist_journal.errors import JournalError
from . import policy, schema
from .budget import Budget
from .errors import DeliveryError

DEFAULT_TIMEOUT = 2.0
MAX_PAGE_BYTES = 1048576
MAX_PROVIDER_ID = 2**52 - 1
STATES = frozenset(
    {"ready", "in_flight", "retryable", "confirmed", "permanent_failure", "uncertain"}
)
_STAMP = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z")


@contextmanager
def _errors() -> Iterator[None]:
    """Translate category-bearing boundaries without leaking SQLite or OS diagnostics."""
    try:
        yield
    except (PersistenceError, WatchlistError, JournalError) as error:
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
            sqlite3.SQLITE_CONSTRAINT: "storage_corrupt",
        }.get(code, "storage_io")
        raise DeliveryError(category) from None
    except OSError:
        raise DeliveryError("storage_io") from None


def _sqlite_text(raw: bytes) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        raise DeliveryError("storage_corrupt") from None


def _budget_for(timeout: float, supplied: Budget | None) -> Budget:
    budget = Budget(timeout) if supplied is None else supplied
    budget.remaining()
    return budget


def _path(value: Path, *, new: bool = False) -> Path:
    with _errors():
        target = paths._checked_path(value)
        exists = paths._exists(target)
        if new and exists:
            raise DeliveryError("unsafe_destination")
        if not new and not exists:
            raise DeliveryError("storage_missing")
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
            raise DeliveryError("unsafe_destination")
        header = stream.read(100)
    after = paths._unsafe_stat(target, file=True)
    if (after.st_dev, after.st_ino) != identity:
        raise DeliveryError("unsafe_destination")
    budget.remaining()
    if len(header) != 100 or header[:16] != b"SQLite format 3\x00":
        raise DeliveryError("storage_corrupt")
    page_size = int.from_bytes(header[16:18], "big")
    if page_size == 1:
        page_size = 65536
    if (
        page_size < 512
        or page_size > 65536
        or page_size & (page_size - 1)
        or after.st_size < page_size
        or after.st_size % page_size
    ):
        raise DeliveryError("storage_corrupt")
    if (
        int.from_bytes(header[68:72], "big") != schema.APPLICATION_ID
        or int.from_bytes(header[60:64], "big") != schema.SCHEMA_VERSION
    ):
        raise DeliveryError("storage_schema")
    return identity


def reject_same_file(first: Path, second: Path) -> None:
    """Reject aliases before accessing a second owner's data."""
    with _errors():
        left, right = _path(first), _path(second)
        if left == right or os.path.samefile(left, right):
            raise DeliveryError("unsafe_destination")


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
    _reserved: bool = False,
) -> Iterator[sqlite3.Connection]:
    db: sqlite3.Connection | None = None
    with _errors():
        try:
            target = _path(path)
            before = target.lstat()
            if not _reserved:
                _owned_header(target, budget)
            if (
                _expected_identity is not None
                and (before.st_dev, before.st_ino) != _expected_identity
            ):
                raise DeliveryError("unsafe_destination")
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
            db.text_factory = _sqlite_text
            db.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 524288)
            db.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH, 65536)
            db.set_progress_handler(budget.progress, 1000)
            db.setconfig(sqlite3.SQLITE_DBCONFIG_DEFENSIVE, True)
            _execute(db, budget, "PRAGMA trusted_schema=OFF")
            _execute(db, budget, "PRAGMA foreign_keys=ON")
            if _execute(db, budget, "PRAGMA foreign_keys").fetchone()[0] != 1:
                raise DeliveryError("storage_schema")
            if writable:
                _execute(db, budget, "PRAGMA synchronous=FULL")
            else:
                _execute(db, budget, "PRAGMA query_only=ON")
            yield db
            budget.remaining()
            final = paths._unsafe_stat(target, file=True)
            paths._check_sidecars(target, new=False)
            if (final.st_dev, final.st_ino) != (before.st_dev, before.st_ino):
                raise DeliveryError("unsafe_destination")
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


_TEXT = {
    "owner": 128,
    "operational_high_water": 27,
    "destination_key": 64,
    "provider": 8,
    "chat_type": 7,
    "route_json": 2048,
    "route_sha256": 64,
    "registered_at": 27,
    "validated_at": 27,
    "watch_id": 69,
    "entry_json": 65536,
    "entry_sha256": 64,
    "delivery_id": 70,
    "alert_id": 70,
    "signal_id": 70,
    "cmt_id": 36,
    "policy_version": 64,
    "intent_json": 65536,
    "evidence_json": 262144,
    "message_text": 4096,
    "consent_json": 4096,
    "binding_json": 8192,
    "intent_sha256": 64,
    "evidence_sha256": 64,
    "message_sha256": 64,
    "source_alert_sha256": 64,
    "consent_sha256": 64,
    "binding_sha256": 64,
    "prepared_at": 27,
    "state": 17,
    "current_attempt_id": 70,
    "current_owner": 64,
    "not_before": 27,
    "updated_at": 27,
    "attempt_id": 70,
    "claimed_at": 27,
    "route_validated_at": 27,
    "completed_at": 27,
    "error_category": 32,
}
_INTS = {
    "singleton": 1,
    "schema_version": 1,
    "send_quarantined": 1,
    "bot_id": MAX_PROVIDER_ID,
    "chat_id": MAX_PROVIDER_ID,
    "operator_attested": 1,
    "revision": 2147483647,
    "renderer_version": 1,
    "attempt_count": 3,
    "ordinal": 3,
    "retry_after": 86400,
    "message_id": 2**63 - 1,
    "accepted_at": 253402300799,
}
_FIELDS = {
    "wtd_metadata": (
        "singleton",
        "owner",
        "schema_version",
        "send_quarantined",
        "operational_high_water",
    ),
    "wtd_destinations": (
        "destination_key",
        "provider",
        "bot_id",
        "chat_id",
        "chat_type",
        "operator_attested",
        "route_json",
        "route_sha256",
        "registered_at",
        "validated_at",
    ),
    "wtd_watch_entries": ("watch_id", "revision", "entry_json", "entry_sha256"),
    "wtd_deliveries": (
        "delivery_id",
        "provider",
        "alert_id",
        "destination_key",
        "signal_id",
        "watch_id",
        "revision",
        "cmt_id",
        "policy_version",
        "renderer_version",
        "intent_json",
        "evidence_json",
        "message_text",
        "consent_json",
        "binding_json",
        "intent_sha256",
        "evidence_sha256",
        "message_sha256",
        "entry_sha256",
        "source_alert_sha256",
        "route_sha256",
        "consent_sha256",
        "binding_sha256",
        "prepared_at",
    ),
    "wtd_state": (
        "delivery_id",
        "state",
        "attempt_count",
        "current_attempt_id",
        "current_owner",
        "not_before",
        "updated_at",
    ),
    "wtd_claims": (
        "attempt_id",
        "delivery_id",
        "owner",
        "ordinal",
        "claimed_at",
        "route_validated_at",
    ),
    "wtd_results": (
        "attempt_id",
        "owner",
        "state",
        "completed_at",
        "error_category",
        "retry_after",
        "not_before",
        "message_id",
        "accepted_at",
        "bot_id",
        "chat_id",
    ),
}
_NULLABLE = frozenset(
    {
        "validated_at",
        "current_attempt_id",
        "current_owner",
        "not_before",
        "error_category",
        "retry_after",
        "message_id",
        "accepted_at",
        "bot_id",
        "chat_id",
    }
)
_KEYS = {
    "wtd_metadata": "singleton",
    "wtd_destinations": "destination_key",
    "wtd_watch_entries": "watch_id,revision",
    "wtd_deliveries": "delivery_id",
    "wtd_state": "delivery_id",
    "wtd_claims": "attempt_id",
    "wtd_results": "attempt_id",
}
_UNCERTAIN = frozenset(
    {
        "network_uncertain",
        "transport_timeout",
        "transport_failure",
        "provider_invalid",
        "bot_mismatch",
        "destination_mismatch",
        "token_configuration",
        "local_commit_failed",
        "deadline_exceeded",
        "recovered",
        "clock_skew",
    }
)


def _text(column: str, maximum: int, minimum: int = 1) -> str:
    return (
        f"CASE WHEN typeof({column})='text' AND "
        f"length(CAST({column} AS BLOB)) BETWEEN {minimum} AND {maximum} THEN {column} END"
    )


def _projection(fields: tuple[str, ...]) -> str:
    values = []
    for field in fields:
        if field in _TEXT:
            guard = (
                f"typeof({field})='text' AND "
                f"length(CAST({field} AS BLOB)) BETWEEN 1 AND {_TEXT[field]}"
            )
        else:
            guard = f"typeof({field})='integer' AND {field} BETWEEN 0 AND {_INTS[field]}"
        # The -1 sentinel cannot be mistaken for a genuine nullable NULL.
        values.append(f"CASE WHEN {field} IS NULL THEN NULL WHEN {guard} THEN {field} ELSE -1 END")
    return ",".join(values)


def _rows(
    db: sqlite3.Connection,
    table: str,
    budget: Budget,
    *,
    where: str = "",
    values: tuple[object, ...] = (),
    maximum: int = 100000001,
) -> Iterator[dict[str, object]]:
    fields = _FIELDS[table]
    keys = _KEYS[table].split(",")
    last: tuple[object, ...] | None = None
    loaded = 0
    while loaded < maximum:
        allowance = min(1000, maximum - loaded)
        clauses = [where] if where else []
        parameters = values
        if last is not None:
            clauses.append("(" + ",".join(keys) + ") > (" + ",".join("?" for _ in keys) + ")")
            parameters += last
        cursor = _execute(
            db,
            budget,
            "SELECT "
            + _projection(fields)
            + " FROM "
            + table
            + (
                " WHERE " + " AND ".join("(" + clause + ")" for clause in clauses)
                if clauses
                else ""
            )
            + " ORDER BY "
            + _KEYS[table]
            + " LIMIT ?",
            parameters + (allowance,),
        )
        received = 0
        for row in cursor:
            budget.remaining()
            item = dict(zip(fields, row, strict=True))
            for key, value in item.items():
                if value is None:
                    if key not in _NULLABLE:
                        raise DeliveryError("storage_corrupt")
                elif key in _TEXT:
                    if type(value) is not str:
                        raise DeliveryError("storage_corrupt")
                elif type(value) is not int or value < 0:
                    raise DeliveryError("storage_corrupt")
            received += 1
            loaded += 1
            last = tuple(item[key] for key in keys)
            yield item
        if received < allowance:
            break


def _one(
    db: sqlite3.Connection,
    table: str,
    budget: Budget,
    key: str,
    value: object,
    *,
    required: bool = True,
) -> dict[str, object] | None:
    found = list(_rows(db, table, budget, where=key + "=?", values=(value,), maximum=2))
    if len(found) > 1:
        raise DeliveryError("storage_corrupt")
    if not found:
        if required:
            raise DeliveryError("not_found")
        return None
    return found[0]


def _stamp(value: object) -> str:
    if type(value) is not str or _STAMP.fullmatch(value) is None:
        raise DeliveryError("storage_corrupt")
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        raise DeliveryError("storage_corrupt") from None
    return value


def _now() -> str:
    return policy.now()


def _after(value: str, seconds: int) -> str:
    stamp = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ") + timedelta(seconds=seconds)
    return (
        f"{stamp.year:04d}-{stamp.month:02d}-{stamp.day:02d}T"
        f"{stamp.hour:02d}:{stamp.minute:02d}:{stamp.second:02d}.{stamp.microsecond:06d}Z"
    )


def _json(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    )


def _decode(value: object, budget: Budget) -> object:
    if type(value) is not str:
        raise DeliveryError("storage_corrupt")
    try:
        budget.remaining()
        _preflight(value)
        decoded: object = json.loads(value, object_pairs_hook=_pairs, parse_constant=_constant)
        budget.remaining()
        if _json(decoded) != value:
            raise DeliveryError("storage_corrupt")
        return decoded
    except (CatalogError, ValueError, RecursionError, UnicodeError):
        raise DeliveryError("storage_corrupt") from None


def _schema(db: sqlite3.Connection, budget: Budget) -> dict[str, object]:
    if (
        _execute(db, budget, "PRAGMA application_id").fetchone()[0] != schema.APPLICATION_ID
        or _execute(db, budget, "PRAGMA user_version").fetchone()[0] != 1
        or _execute(db, budget, "PRAGMA journal_mode").fetchone()[0] != "delete"
    ):
        raise DeliveryError("storage_schema")
    cursor = _execute(
        db,
        budget,
        "SELECT "
        + ",".join(_text(c, 128) for c in ("type", "name", "tbl_name"))
        + ",CASE WHEN sql IS NULL THEN NULL WHEN typeof(sql)='text' "
        + "AND length(CAST(sql AS BLOB)) BETWEEN 1 AND 32768 THEN sql ELSE -1 "
        + "END FROM sqlite_master ORDER BY type,name LIMIT 46",
    )
    if tuple(tuple(row) for row in cursor) != schema.expected_inventory():
        raise DeliveryError("storage_schema")
    metadata = list(_rows(db, "wtd_metadata", budget, maximum=2))
    if len(metadata) != 1 or any(
        metadata[0][key] != value
        for key, value in {"singleton": 1, "owner": schema.OWNER, "schema_version": 1}.items()
    ):
        raise DeliveryError("storage_schema")
    result = metadata[0]
    if result["send_quarantined"] not in (0, 1):
        raise DeliveryError("storage_corrupt")
    _stamp(result["operational_high_water"])
    return result


def _integrity(db: sqlite3.Connection, budget: Budget) -> None:
    if (
        _execute(db, budget, "PRAGMA integrity_check(1)").fetchone()[0] != "ok"
        or _execute(db, budget, "PRAGMA foreign_key_check").fetchone() is not None
    ):
        raise DeliveryError("storage_corrupt")


def _route(item: dict[str, object], budget: Budget) -> dict[str, object]:
    route = {
        "route_version": 1,
        **{
            key: item[key]
            for key in ("provider", "destination_key", "bot_id", "chat_id", "chat_type")
        },
        "operator_attested": True,
    }
    # Rebuild through BE policy so all strict boundary rules are shared.
    if (
        item["operator_attested"] != 1
        or _json(route) != item["route_json"]
        or policy.domain_digest("CMT_WATCHLIST_TELEGRAM_ROUTE_V1", route) != item["route_sha256"]
    ):
        raise DeliveryError("storage_corrupt")
    policy.route(route)
    _stamp(item["registered_at"])
    if item["validated_at"] is not None and _stamp(item["validated_at"]) < cast(
        str, item["registered_at"]
    ):
        raise DeliveryError("storage_corrupt")
    budget.remaining()
    return route


def _envelope(operation: str, **values: object) -> dict[str, object]:
    return {"version": 1, "operation": operation, "result": "ok", **values}


def _safe_delivery(item: dict[str, object]) -> dict[str, object]:
    fields = (
        "delivery_id",
        "alert_id",
        "signal_id",
        "state",
        "attempt_count",
        "current_attempt_id",
        "not_before",
        "updated_at",
        "message_sha256",
        "evidence_sha256",
        "route_sha256",
        "consent_sha256",
        "binding_sha256",
        "send_quarantined",
        "last_error_category",
    )
    return {**{k: item[k] for k in fields}, "first_prepared_at": item["prepared_at"]}


def _local_envelope(
    item: dict[str, object],
    entry: dict[str, object],
    destination: dict[str, object],
    budget: Budget,
) -> dict[str, object]:
    return {
        "authority_version": 1,
        "operation": "prepare",
        "binding": _decode(item["binding_json"], budget),
        "binding_sha256": item["binding_sha256"],
        "entry_json": entry["entry_json"],
        "intent_json": item["intent_json"],
        "evidence_json": item["evidence_json"],
        "message_text": item["message_text"],
        "route_json": destination["route_json"],
        "consent_json": item["consent_json"],
    }


def _result(item: dict[str, object], claim: dict[str, object], route: dict[str, object]) -> None:
    if item["attempt_id"] != claim["attempt_id"] or item["owner"] != claim["owner"]:
        raise DeliveryError("storage_corrupt")
    _stamp(item["completed_at"])
    if cast(str, item["completed_at"]) < cast(str, claim["claimed_at"]):
        raise DeliveryError("storage_corrupt")
    state = item["state"]
    category = item["error_category"]
    receipt_keys = ("message_id", "accepted_at", "bot_id", "chat_id")
    if state == "confirmed":
        if (
            category is not None
            or any(type(item[k]) is not int or cast(int, item[k]) <= 0 for k in receipt_keys)
            or item["bot_id"] != route["bot_id"]
            or item["chat_id"] != route["chat_id"]
            or item["retry_after"] is not None
            or item["not_before"] is not None
        ):
            raise DeliveryError("storage_corrupt")
    elif any(item[k] is not None for k in receipt_keys):
        raise DeliveryError("storage_corrupt")
    elif state == "retryable":
        if (
            category != "rate_limited"
            or claim["ordinal"] == 3
            or type(item["retry_after"]) is not int
            or not 1 <= item["retry_after"] <= 86400
            or item["not_before"] != _after(cast(str, item["completed_at"]), item["retry_after"])
        ):
            raise DeliveryError("storage_corrupt")
    elif state == "permanent_failure":
        if item["not_before"] is not None or not (
            (category == "provider_rejection" and item["retry_after"] is None)
            or (
                category == "retry_exhausted"
                and claim["ordinal"] == 3
                and type(item["retry_after"]) is int
                and 1 <= item["retry_after"] <= 86400
            )
        ):
            raise DeliveryError("storage_corrupt")
    elif state == "uncertain":
        if (
            category not in _UNCERTAIN
            or item["retry_after"] is not None
            or item["not_before"] is not None
        ):
            raise DeliveryError("storage_corrupt")
    else:
        raise DeliveryError("storage_corrupt")


def _fold(
    db: sqlite3.Connection, budget: Budget
) -> tuple[dict[str, int], dict[str, object], dict[str, dict[str, object]], str]:
    metadata = _schema(db, budget)
    _integrity(db, budget)
    high = cast(str, metadata["operational_high_water"])
    logical = hashlib.sha256()
    counts = {"destinations": 0, "watch_entries": 0, "deliveries": 0, "claims": 0, "results": 0}
    destinations = {}
    entries = {}
    deliveries = {}
    used_entries: set[tuple[object, object]] = set()
    seen_owners = set()

    def event(value: object) -> str:
        instant = _stamp(value)
        if instant > high:
            raise DeliveryError("storage_corrupt")
        return instant

    def absorb(table: str, row: dict[str, object]) -> None:
        value = dict(row)
        if table == "wtd_metadata":
            value.pop("send_quarantined")
        logical.update((_json([table, value]) + "\n").encode("ascii"))

    absorb("wtd_metadata", metadata)
    try:
        for destination in _rows(db, "wtd_destinations", budget):
            _route(destination, budget)
            event(destination["registered_at"])
            if destination["validated_at"] is not None:
                event(destination["validated_at"])
            destination_key = cast(str, destination["destination_key"])
            destinations[destination_key] = destination
            counts["destinations"] += 1
            absorb("wtd_destinations", destination)
        for entry in _rows(db, "wtd_watch_entries", budget):
            _decode(entry["entry_json"], budget)
            if (
                hashlib.sha256(cast(str, entry["entry_json"]).encode("ascii")).hexdigest()
                != entry["entry_sha256"]
            ):
                raise DeliveryError("storage_corrupt")
            entries[(entry["watch_id"], entry["revision"])] = entry
            counts["watch_entries"] += 1
            absorb("wtd_watch_entries", entry)
        for item in _rows(db, "wtd_deliveries", budget):
            did = cast(str, item["delivery_id"])
            key = (item["watch_id"], item["revision"])
            selected_entry = entries.get(key)
            selected_destination = destinations.get(cast(str, item["destination_key"]))
            if selected_entry is None or selected_destination is None:
                raise DeliveryError("storage_corrupt")
            entry = selected_entry
            destination = selected_destination
            envelope = _local_envelope(item, entry, destination, budget)
            validated = policy.validate_prepared(envelope, check=budget.remaining)
            binding = cast(dict[str, object], validated["binding"])
            if (
                any(item[k] != v for k, v in binding.items() if k != "binding_version")
                or item["binding_sha256"] != validated["binding_sha256"]
            ):
                raise DeliveryError("storage_corrupt")
            state = _one(db, "wtd_state", budget, "delivery_id", did)
            if state is None:
                raise DeliveryError("storage_corrupt")
            previous = event(item["prepared_at"])
            expected = "ready"
            current = None
            owner = None
            due = None
            attempts = []
            for claim in _rows(
                db, "wtd_claims", budget, where="delivery_id=?", values=(did,), maximum=4
            ):
                # Claims are retrieved by random attempt ID; explicitly sort by ordinal below.
                attempts.append(claim)
            attempts.sort(key=lambda c: cast(int, c["ordinal"]))
            for ordinal, claim in enumerate(attempts, 1):
                if (
                    ordinal > 3
                    or claim["ordinal"] != ordinal
                    or expected not in ("ready", "retryable")
                    or claim["owner"] in seen_owners
                ):
                    raise DeliveryError("storage_corrupt")
                seen_owners.add(claim["owner"])
                policy.validate_id(claim["attempt_id"], "wtat1_")
                if re.fullmatch("[0-9a-f]{64}", cast(str, claim["owner"])) is None:
                    raise DeliveryError("storage_corrupt")
                claimed = event(claim["claimed_at"])
                snapshot = event(claim["route_validated_at"])
                if (
                    claimed < previous
                    or (due is not None and claimed < due)
                    or destination["validated_at"] is None
                    or not cast(str, destination["registered_at"]) <= snapshot <= claimed
                    or snapshot > cast(str, destination["validated_at"])
                ):
                    raise DeliveryError("storage_corrupt")
                outcome = _one(
                    db, "wtd_results", budget, "attempt_id", claim["attempt_id"], required=False
                )
                if outcome is None:
                    expected = "in_flight"
                    current = claim["attempt_id"]
                    owner = claim["owner"]
                    due = None
                    previous = claimed
                else:
                    _result(outcome, claim, destination)
                    previous = event(outcome["completed_at"])
                    expected = cast(str, outcome["state"])
                    current = None
                    owner = None
                    due = cast(str | None, outcome["not_before"])
                    counts["results"] += 1
                claim["result"] = outcome
            check = {
                "state": expected,
                "attempt_count": len(attempts),
                "current_attempt_id": current,
                "current_owner": owner,
                "not_before": due,
                "updated_at": previous,
            }
            if any(state[k] != v for k, v in check.items()):
                raise DeliveryError("storage_corrupt")
            last = cast(dict[str, object] | None, attempts[-1]["result"]) if attempts else None
            deliveries[did] = {
                **item,
                **validated,
                **state,
                **{
                    k: destination[k]
                    for k in ("bot_id", "chat_id", "validated_at", "registered_at")
                },
                "operational_high_water": high,
                "send_quarantined": bool(metadata["send_quarantined"]),
                "attempts": attempts,
                "last_error_category": None if last is None else last["error_category"],
            }
            used_entries.add(key)
            counts["deliveries"] += 1
            counts["claims"] += len(attempts)
            absorb("wtd_deliveries", item)
            absorb("wtd_state", state)
        if used_entries != set(entries):
            raise DeliveryError("storage_corrupt")
        for table, count_key in (
            ("wtd_state", "deliveries"),
            ("wtd_claims", "claims"),
            ("wtd_results", "results"),
        ):
            actual = 0
            for row in _rows(db, table, budget):
                actual += 1
                if table != "wtd_state":
                    absorb(table, row)
            if actual != counts[count_key]:
                raise DeliveryError("storage_corrupt")
        if any(value > 100000000 for value in counts.values()):
            raise DeliveryError("storage_corrupt")
        budget.remaining()
        return counts, metadata, deliveries, logical.hexdigest()
    except (DeliveryError, CatalogError, ValueError, TypeError, KeyError, OverflowError) as error:
        if getattr(error, "category", None) == "storage_timeout":
            raise DeliveryError("storage_timeout") from None
        raise DeliveryError("storage_corrupt") from None


def _verify(db: sqlite3.Connection, budget: Budget) -> tuple[dict[str, int], bool]:
    counts, metadata, _, _ = _fold(db, budget)
    return counts, bool(metadata["send_quarantined"])


def _insert(db: sqlite3.Connection, table: str, item: dict[str, object], budget: Budget) -> None:
    fields = _FIELDS[table]
    cursor = _execute(
        db,
        budget,
        "INSERT INTO "
        + table
        + "("
        + ",".join(fields)
        + ") VALUES("
        + ",".join("?" for _ in fields)
        + ")",
        tuple(item[k] for k in fields),
    )
    if cursor.rowcount != 1:
        raise DeliveryError("storage_corrupt")


def load_destination(
    path: Path, alias: str, *, timeout: float = DEFAULT_TIMEOUT, _budget: Budget | None = None
) -> dict[str, object]:
    budget = _budget_for(timeout, _budget)
    alias = policy.destination(alias)
    with _connect(path, budget) as db, _transaction(db, budget):
        _fold(db, budget)
        item = _one(db, "wtd_destinations", budget, "destination_key", alias)
        assert item is not None
        return {**item, **_route(item, budget)}


def load_delivery(
    path: Path,
    delivery_id: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    _budget: Budget | None = None,
    _for_send: bool = False,
) -> dict[str, object]:
    budget = _budget_for(timeout, _budget)
    policy.validate_id(delivery_id)
    with _connect(path, budget) as db, _transaction(db, budget):
        _, metadata, deliveries, _ = _fold(db, budget)
        if _for_send and metadata["send_quarantined"]:
            raise DeliveryError("send_quarantined")
        if delivery_id not in deliveries:
            raise DeliveryError("not_found")
        return deliveries[delivery_id]


def get(
    path: Path, delivery_id: str, *, timeout: float = DEFAULT_TIMEOUT, _budget: Budget | None = None
) -> dict[str, object]:
    return _envelope(
        "get",
        delivery=_safe_delivery(load_delivery(path, delivery_id, timeout=timeout, _budget=_budget)),
    )


def verify(
    path: Path, *, timeout: float = DEFAULT_TIMEOUT, _budget: Budget | None = None
) -> dict[str, object]:
    budget = _budget_for(timeout, _budget)
    with _connect(path, budget) as db, _transaction(db, budget):
        counts, quarantined = _verify(db, budget)
        return _envelope("verify", level="local", counts=counts, send_quarantined=quarantined)


def destination_add(
    path: Path,
    alias: str,
    bot_id: int,
    chat_id: int,
    *,
    operator_private_owned: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
    _budget: Budget | None = None,
) -> dict[str, object]:
    budget = _budget_for(timeout, _budget)
    if operator_private_owned is not True:
        raise DeliveryError("invalid_destination")
    route = policy.route(
        {
            "route_version": 1,
            "provider": "telegram",
            "destination_key": alias,
            "bot_id": bot_id,
            "chat_id": chat_id,
            "chat_type": "private",
            "operator_attested": True,
        }
    )
    rdigest = policy.route_sha256(route)
    with _connect(path, budget, writable=True) as db, _transaction(db, budget, write=True):
        _, metadata, _, _ = _fold(db, budget)
        current = _one(db, "wtd_destinations", budget, "destination_key", alias, required=False)
        if current is not None:
            if current["route_json"] != _json(route) or current["route_sha256"] != rdigest:
                raise DeliveryError("conflict")
            result = "replay"
        else:
            now = _now()
            if now < cast(str, metadata["operational_high_water"]):
                raise DeliveryError("clock_skew")
            _insert(
                db,
                "wtd_destinations",
                {
                    **route,
                    "operator_attested": 1,
                    "route_json": _json(route),
                    "route_sha256": rdigest,
                    "registered_at": now,
                    "validated_at": None,
                },
                budget,
            )
            _fold(db, budget)
            result = "inserted"
    return {
        **_envelope("destination-add", destination_key=alias, route_sha256=rdigest),
        "result": result,
    }


def _destination_validated(
    path: Path,
    alias: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    _budget: Budget | None = None,
    expected_route_sha256: str | None = None,
) -> dict[str, object]:
    budget = _budget_for(timeout, _budget)
    policy.destination(alias)
    with _connect(path, budget, writable=True) as db, _transaction(db, budget, write=True):
        _, metadata, _, _ = _fold(db, budget)
        route = _one(db, "wtd_destinations", budget, "destination_key", alias)
        assert route is not None
        if expected_route_sha256 is not None and route["route_sha256"] != expected_route_sha256:
            raise DeliveryError("conflict")
        now = _now()
        if now < max(
            cast(str, metadata["operational_high_water"]),
            cast(str, route["registered_at"]),
            cast(str, route["validated_at"] or route["registered_at"]),
        ):
            raise DeliveryError("clock_skew")
        if (
            _execute(
                db,
                budget,
                "UPDATE wtd_destinations SET validated_at=? WHERE destination_key=?",
                (now, alias),
            ).rowcount
            != 1
        ):
            raise DeliveryError("conflict")
        _fold(db, budget)
    return _envelope(
        "destination-validate",
        destination_key=alias,
        route_sha256=route["route_sha256"],
        validated_at=now,
    )


def _authority(receipt: object, budget: Budget, operation: str, path: Path) -> dict[str, object]:
    from .application import _consume_receipt

    # Single-use authority is consumed before any writable open, including failures.
    envelope = _consume_receipt(receipt, budget, operation, path)
    return policy.validate_prepared(envelope, check=budget.remaining)


def _agreement(
    db: sqlite3.Connection, envelope: dict[str, object], budget: Budget
) -> tuple[dict[str, object], dict[str, object]]:
    binding = cast(dict[str, object], envelope["binding"])
    entry = list(
        _rows(
            db,
            "wtd_watch_entries",
            budget,
            where="watch_id=? AND revision=?",
            values=(binding["watch_id"], binding["revision"]),
            maximum=2,
        )
    )
    if len(entry) > 1:
        raise DeliveryError("storage_corrupt")
    if entry and (
        entry[0]["entry_json"] != envelope["entry_json"]
        or entry[0]["entry_sha256"] != binding["entry_sha256"]
    ):
        raise DeliveryError("identity_conflict")
    route = _one(db, "wtd_destinations", budget, "destination_key", binding["destination_key"])
    assert route is not None
    if (
        route["route_json"] != envelope["route_json"]
        or route["route_sha256"] != binding["route_sha256"]
    ):
        raise DeliveryError("conflict")
    return binding, route


def _same(item: dict[str, object], envelope: dict[str, object]) -> bool:
    return all(
        item[k] == v for k, v in envelope.items() if k not in ("operation", "authority_version")
    )


def _prepare_verified(path: Path, receipt: object, budget: Budget) -> dict[str, object]:
    envelope = _authority(receipt, budget, "prepare", path)
    with _connect(path, budget, writable=True) as db, _transaction(db, budget, write=True):
        _, metadata, deliveries, _ = _fold(db, budget)
        binding, _ = _agreement(db, envelope, budget)
        did = cast(str, binding["delivery_id"])
        now = _now()
        if now < cast(str, metadata["operational_high_water"]):
            raise DeliveryError("clock_skew")
        if did in deliveries:
            if not _same(deliveries[did], envelope):
                raise DeliveryError("conflict")
            item = deliveries[did]
            result = "replay"
        else:
            existing = list(
                _rows(
                    db,
                    "wtd_watch_entries",
                    budget,
                    where="watch_id=? AND revision=?",
                    values=(binding["watch_id"], binding["revision"]),
                    maximum=2,
                )
            )
            if not existing:
                _insert(
                    db,
                    "wtd_watch_entries",
                    {
                        "watch_id": binding["watch_id"],
                        "revision": binding["revision"],
                        "entry_json": envelope["entry_json"],
                        "entry_sha256": binding["entry_sha256"],
                    },
                    budget,
                )
            row = {
                **binding,
                **{
                    k: envelope[k]
                    for k in (
                        "intent_json",
                        "evidence_json",
                        "message_text",
                        "consent_json",
                        "binding_sha256",
                    )
                },
                "binding_json": _json(binding),
                "prepared_at": now,
            }
            _insert(db, "wtd_deliveries", row, budget)
            _, _, after, _ = _fold(db, budget)
            item = after[did]
            result = "inserted"
    return {**_envelope("prepare", delivery=_safe_delivery(item)), "result": result}


_CLAIM_AUTHORITY = object()


@dataclass(frozen=True)
class _ClaimHandle:
    """One operation's immutable, exact-instance claim authority."""

    content_json: str
    _authority: object = dataclass_field(default=None, init=False, repr=False, compare=False)
    _used: bool = dataclass_field(default=False, init=False, repr=False, compare=False)


def _seal_handle(path: Path, budget: Budget, item: dict[str, object]) -> _ClaimHandle:
    info = paths._unsafe_stat(_path(path), file=True)
    content = _json(
        {
            key: item[key]
            for key in ("delivery_id", "current_attempt_id", "current_owner", "binding_sha256")
        }
    )
    handle = _ClaimHandle(content)
    seal = (
        _CLAIM_AUTHORITY,
        id(handle),
        hashlib.sha256(content.encode("ascii")).hexdigest(),
        budget,
        budget.global_deadline,
        str(_path(path)),
        info.st_dev,
        info.st_ino,
    )
    object.__setattr__(handle, "_authority", seal)
    return handle


def _consume_handle(path: Path, did: str, handle: object, budget: Budget) -> tuple[str, str, str]:
    if type(handle) is not _ClaimHandle or handle._used is not False:
        raise DeliveryError("stale_attempt")
    seal = handle._authority
    raw = handle.content_json
    if (
        type(raw) is not str
        or not raw.isascii()
        or len(raw) > 1024
        or type(seal) is not tuple
        or len(seal) != 8
        or seal[0] is not _CLAIM_AUTHORITY
        or seal[1] != id(handle)
        or seal[2] != hashlib.sha256(raw.encode("ascii")).hexdigest()
        or seal[3] is not budget
        or seal[4] != budget.global_deadline
    ):
        raise DeliveryError("stale_attempt")
    object.__setattr__(handle, "_used", True)
    info = paths._unsafe_stat(_path(path), file=True)
    if seal[5:] != (str(_path(path)), info.st_dev, info.st_ino):
        raise DeliveryError("stale_attempt")
    content = _decode(raw, budget)
    if (
        type(content) is not dict
        or set(content) != {"delivery_id", "current_attempt_id", "current_owner", "binding_sha256"}
        or content["delivery_id"] != did
    ):
        raise DeliveryError("stale_attempt")
    return (
        cast(str, content["current_attempt_id"]),
        cast(str, content["current_owner"]),
        cast(str, content["binding_sha256"]),
    )


def _claim_verified(
    path: Path, delivery_id: str, receipt: object, budget: Budget
) -> dict[str, object]:
    envelope = _authority(receipt, budget, "claim", path)
    policy.validate_id(delivery_id)
    budget.preclaim()
    with _connect(path, budget, writable=True) as db, _transaction(db, budget, write=True):
        _, metadata, deliveries, _ = _fold(db, budget)
        if metadata["send_quarantined"]:
            raise DeliveryError("send_quarantined")
        binding, route = _agreement(db, envelope, budget)
        if binding["delivery_id"] != delivery_id or delivery_id not in deliveries:
            raise DeliveryError("not_found")
        item = deliveries[delivery_id]
        if not _same(item, envelope):
            raise DeliveryError("conflict")
        if route["validated_at"] is None:
            raise DeliveryError("not_validated")
        now = _now()
        if now < max(
            cast(str, metadata["operational_high_water"]),
            cast(str, route["validated_at"]),
            cast(str, item["updated_at"]),
        ):
            raise DeliveryError("clock_skew")
        if item["state"] not in ("ready", "retryable"):
            raise DeliveryError("delivery_blocked")
        if cast(int, item["attempt_count"]) >= 3:
            raise DeliveryError("attempt_limit")
        if item["not_before"] is not None and now < cast(str, item["not_before"]):
            raise DeliveryError("retry_not_due")
        attempt = "wtat1_" + secrets.token_hex(32)
        owner = secrets.token_hex(32)
        budget.preclaim()
        _insert(
            db,
            "wtd_claims",
            {
                "attempt_id": attempt,
                "delivery_id": delivery_id,
                "owner": owner,
                "ordinal": cast(int, item["attempt_count"]) + 1,
                "claimed_at": now,
                "route_validated_at": route["validated_at"],
            },
            budget,
        )
        _, _, after, _ = _fold(db, budget)
        item = after[delivery_id]
        budget.preclaim()
    handle = _seal_handle(path, budget, item)
    return {"delivery": item, "attempt_id": attempt, "owner": owner, "_handle": handle}


def _finish_row(
    db: sqlite3.Connection,
    did: str,
    attempt: str,
    owner: str,
    outcome: dict[str, object],
    budget: Budget,
    *,
    recovered: bool = False,
) -> dict[str, object]:
    _, metadata, deliveries, _ = _fold(db, budget)
    if did not in deliveries:
        raise DeliveryError("not_found")
    item = deliveries[did]
    if (
        item["state"] != "in_flight"
        or item["current_attempt_id"] != attempt
        or item["current_owner"] != owner
    ):
        raise DeliveryError("stale_attempt")
    attempts = cast(list[dict[str, object]], item["attempts"])
    claim = attempts[-1]
    now = _now()
    floor = max(cast(str, claim["claimed_at"]), cast(str, metadata["operational_high_water"]))
    state = outcome["state"]
    category = outcome["error_category"]
    retry = outcome["retry_after"]
    receipt = outcome["receipt"]
    due = None
    if now < floor:
        state = "uncertain"
        category = "clock_skew"
        retry = None
        receipt = None
        now = floor
    elif recovered:
        state = "uncertain"
        category = "recovered"
        retry = None
        receipt = None
    elif state == "retryable":
        if type(retry) is not int or not 1 <= retry <= 86400 or category != "rate_limited":
            raise DeliveryError("provider_invalid")
        if item["attempt_count"] == 3:
            state = "permanent_failure"
            category = "retry_exhausted"
        else:
            try:
                due = _after(now, retry)
            except (ValueError, OverflowError):
                state = "uncertain"
                category = "provider_invalid"
                retry = None
    row = {
        "attempt_id": attempt,
        "owner": owner,
        "state": state,
        "completed_at": now,
        "error_category": category,
        "retry_after": retry,
        "not_before": due,
        **dict.fromkeys(("message_id", "accepted_at", "bot_id", "chat_id")),
    }
    if state == "confirmed":
        if type(receipt) is not dict or set(receipt) != {
            "message_id",
            "accepted_at",
            "bot_id",
            "chat_id",
        }:
            raise DeliveryError("provider_invalid")
        row.update(receipt)
    _result(row, claim, item)
    _insert(db, "wtd_results", row, budget)
    _, _, after, _ = _fold(db, budget)
    return after[did]


def _finish(
    path: Path, delivery_id: str, handle: object, outcome: dict[str, object], budget: Budget
) -> dict[str, object]:
    attempt, owner, binding = _consume_handle(path, delivery_id, handle, budget)
    with _connect(path, budget, writable=True) as db, _transaction(db, budget, write=True):
        _, _, items, _ = _fold(db, budget)
        if delivery_id not in items or items[delivery_id]["binding_sha256"] != binding:
            raise DeliveryError("stale_attempt")
        item = _finish_row(db, delivery_id, attempt, owner, outcome, budget)
    return _safe_delivery(item)


def recover(
    path: Path,
    delivery_id: str,
    *,
    worker_quiesced: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
    _budget: Budget | None = None,
) -> dict[str, object]:
    budget = _budget_for(timeout, _budget)
    policy.validate_id(delivery_id)
    if worker_quiesced is not True:
        raise DeliveryError("invalid_field")
    with _connect(path, budget, writable=True) as db, _transaction(db, budget, write=True):
        _, _, items, _ = _fold(db, budget)
        if delivery_id not in items:
            raise DeliveryError("not_found")
        current = items[delivery_id]
        if current["state"] != "in_flight":
            raise DeliveryError("delivery_blocked")
        item = _finish_row(
            db,
            delivery_id,
            cast(str, current["current_attempt_id"]),
            cast(str, current["current_owner"]),
            {
                "state": "uncertain",
                "error_category": "recovered",
                "retry_after": None,
                "receipt": None,
            },
            budget,
            recovered=True,
        )
    return _envelope("recover", delivery=_safe_delivery(item))


def _cleanup_reserved(path: Path, identity: tuple[int, int]) -> None:
    with suppress(OSError, PersistenceError):
        information = paths._unsafe_stat(path, file=True)
        if (information.st_dev, information.st_ino) != identity:
            return
        if any(paths._exists(sidecar) for sidecar in paths._sidecars(path)):
            return
        path.unlink()


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
        raise DeliveryError("unsafe_destination")
    if any(paths._exists(sidecar) for sidecar in paths._sidecars(provisional)):
        raise DeliveryError("unsafe_destination")
    try:
        os.link(provisional, target)
    except FileExistsError:
        raise DeliveryError("unsafe_destination") from None
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
        raise DeliveryError("unsafe_destination")
    descriptor = os.open(provisional, os.O_RDWR | getattr(os, "O_NOFOLLOW", 0))
    try:
        opened = os.fstat(descriptor)
        if (
            (opened.st_dev, opened.st_ino) != identity
            or opened.st_nlink != 1
            or not stat.S_ISREG(opened.st_mode)
        ):
            raise DeliveryError("unsafe_destination")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _sync_parent(path: Path) -> None:
    # Windows does not expose a supported directory fsync through os.open.
    if os.name == "nt":
        return
    descriptor = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def initialize(
    path: Path, *, timeout: float = DEFAULT_TIMEOUT, _budget: Budget | None = None
) -> dict[str, object]:
    identity = None
    completed = False
    budget = _budget_for(timeout, _budget)
    with _errors():
        target = _path(path, new=True)
        try:
            identity = paths._reserve(target)
            with _connect(
                target, budget, writable=True, _expected_identity=identity, _reserved=True
            ) as db:
                with _transaction(db, budget, write=True):
                    for statement in schema.STATEMENTS:
                        _execute(db, budget, statement)
                    _execute(db, budget, "PRAGMA application_id=" + str(schema.APPLICATION_ID))
                    _execute(db, budget, "PRAGMA user_version=1")
                    _insert(
                        db,
                        "wtd_metadata",
                        {
                            "singleton": 1,
                            "owner": schema.OWNER,
                            "schema_version": 1,
                            "send_quarantined": 0,
                            "operational_high_water": _now(),
                        },
                        budget,
                    )
                    _fold(db, budget)
            _fsync(target, identity)
            _sync_parent(target)
            budget.remaining()
            completed = True
            return _envelope("init", schema_version=1, send_quarantined=False)
        finally:
            if not completed and identity is not None:
                _cleanup_reserved(target, identity)
    raise AssertionError("unreachable")


def _copy(source: Path, destination: Path, operation: str, budget: Budget) -> dict[str, object]:
    provisional = None
    identity = None
    completed = False
    with _errors():
        target = _path(destination, new=True)
        try:
            with _connect(source, budget) as reader, _transaction(reader, budget):
                counts, metadata, _, digest = _fold(reader, budget)
                provisional = target.parent / (
                    ".cmt-watchlist-delivery-" + uuid.uuid4().hex + ".tmp"
                )
                _path(provisional, new=True)
                identity = paths._reserve(provisional)
                with _connect(
                    provisional, budget, writable=True, _expected_identity=identity, _reserved=True
                ) as writer:
                    reader.execute("PRAGMA busy_timeout=0")
                    writer.execute("PRAGMA busy_timeout=0")

                    def progress(status: int, remaining: int, total: int) -> None:
                        budget.remaining()

                    reader.backup(writer, pages=32, progress=progress, sleep=0.01)
                    if operation == "restore":
                        with _transaction(writer, budget, write=True):
                            _execute(
                                writer,
                                budget,
                                "UPDATE wtd_metadata SET send_quarantined=1 WHERE singleton=1",
                            )
                    with _transaction(writer, budget):
                        copy_counts, copy_metadata, _, copy_digest = _fold(writer, budget)
                        expected = 1 if operation == "restore" else metadata["send_quarantined"]
                        if (
                            copy_counts != counts
                            or copy_digest != digest
                            or copy_metadata["send_quarantined"] != expected
                        ):
                            raise DeliveryError("storage_corrupt")
            _fsync(provisional, identity)
            budget.remaining()
            with (
                _connect(provisional, budget, _expected_identity=identity) as reopened,
                _transaction(reopened, budget),
            ):
                again_counts, again_metadata, _, again_digest = _fold(reopened, budget)
                if (
                    again_counts != counts
                    or again_digest != digest
                    or again_metadata != copy_metadata
                ):
                    raise DeliveryError("storage_corrupt")
            budget.remaining()
            _fsync(provisional, identity)
            _sync_parent(provisional)
            budget.remaining()
            _publish(provisional, target, identity)
            _sync_parent(target)
            # Bounded final readback checks exact published inode and durable quarantine.
            with (
                _connect(target, budget, _expected_identity=identity) as final,
                _transaction(final, budget),
            ):
                final_metadata = _schema(final, budget)
                if final_metadata != copy_metadata:
                    raise DeliveryError("storage_corrupt")
            completed = True
            return _envelope(
                operation, counts=counts, send_quarantined=bool(copy_metadata["send_quarantined"])
            )
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
    return _copy(source, destination, "backup", _budget_for(timeout, _budget))


def restore(
    source: Path,
    destination: Path,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    _budget: Budget | None = None,
) -> dict[str, object]:
    return _copy(source, destination, "restore", _budget_for(timeout, _budget))


def _encode_cursor(state: str | None, last: str) -> str:
    return base64.urlsafe_b64encode(
        _json({"version": 1, "filters": {"state": state}, "last_delivery_id": last}).encode("ascii")
    ).decode("ascii")


def _cursor(value: object, state: str | None, budget: Budget) -> str:
    try:
        if (
            type(value) is not str
            or not 1 <= len(value) <= 2048
            or len(value) % 4
            or re.fullmatch("[A-Za-z0-9_-]+={0,2}", value) is None
        ):
            raise ValueError
        raw = base64.b64decode(value, altchars=b"-_", validate=True)
        if len(raw) > 1536:
            raise ValueError
        decoded = _decode(raw.decode("ascii"), budget)
        if (
            type(decoded) is not dict
            or set(decoded) != {"version", "filters", "last_delivery_id"}
            or type(decoded["version"]) is not int
            or decoded["version"] != 1
            or decoded["filters"] != {"state": state}
        ):
            raise ValueError
        last = policy.validate_id(decoded["last_delivery_id"])
        if _encode_cursor(state, last) != value:
            raise ValueError
        return last
    except (ValueError, UnicodeError, binascii.Error, DeliveryError) as error:
        if getattr(error, "category", None) == "storage_timeout":
            raise
        raise DeliveryError("invalid_cursor") from None


def list_deliveries(
    path: Path,
    *,
    state: str | None = None,
    limit: int = 100,
    cursor: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    _budget: Budget | None = None,
) -> dict[str, object]:
    budget = _budget_for(timeout, _budget)
    if state is not None and (type(state) is not str or state not in STATES):
        raise DeliveryError("invalid_field")
    if type(limit) is not int or not 1 <= limit <= 1000:
        raise DeliveryError("invalid_field")
    last = "" if cursor is None else _cursor(cursor, state, budget)
    with _connect(path, budget) as db, _transaction(db, budget):
        _, _, deliveries, _ = _fold(db, budget)
        selected = [
            item
            for did, item in sorted(deliveries.items())
            if did > last and (state is None or item["state"] == state)
        ]
        items: list[dict[str, object]] = []
        next_cursor = None
        for index, item in enumerate(selected):
            budget.remaining()
            candidate = _safe_delivery(item)
            prospective = items + [candidate]
            continuation = (
                _encode_cursor(state, cast(str, item["delivery_id"]))
                if index + 1 < len(selected)
                else None
            )
            response = _envelope("list", items=prospective, next_cursor=continuation)
            if len((_json(response) + "\n").encode("ascii")) > MAX_PAGE_BYTES:
                if not items:
                    raise DeliveryError("input_limit")
                next_cursor = _encode_cursor(state, cast(str, items[-1]["delivery_id"]))
                break
            items = prospective
            if len(items) == limit:
                next_cursor = continuation
                break
        budget.remaining()
        return _envelope("list", items=items, next_cursor=next_cursor)
