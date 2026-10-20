"""Original-capture authority and a frozen content-bound outbox receipt."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

from ..catalog.validation import CatalogError
from ..discovery.errors import DiscoveryError
from ..discovery.journal_errors import JournalError
from ..discovery.journal_storage import get as journal_get
from ..discovery.journal_validation import canonical_bounded, decode_json, validate_pair
from ..discovery.multi_comparison import compare
from ..discovery.multi_input import parse_request
from ..persistence.errors import PersistenceError
from ..persistence.sqlite_repository import read_multi_revision_snapshots
from . import storage
from .errors import OutboxError
from .policy import destination, prepare_event, token
from .storage import Budget

_AUTHORITY = object()
_MAXIMUM = 16 * 1024 * 1024


@dataclass(frozen=True)
class _Receipt:
    content_json: str
    _authority: object = field(default=None, init=False, repr=False, compare=False)


def _seal(content: str) -> str:
    return hashlib.sha256(content.encode("ascii")).hexdigest()


def _consume_receipt(receipt: object, budget: Budget) -> tuple[str, str, list[dict[str, object]]]:
    """A copied DTO or mutated sealed envelope never grants write authority."""
    if type(receipt) is not _Receipt:
        raise OutboxError("unsupported_evidence")
    content = receipt.content_json
    if type(content) is not str or len(content) > _MAXIMUM:
        raise OutboxError("input_limit")
    if not content.isascii():
        raise OutboxError("unsupported_evidence")
    authority = receipt._authority
    if (
        type(authority) is not tuple
        or len(authority) != 3
        or authority[0] is not _AUTHORITY
        or authority[1] != id(receipt)
        or authority[2] != _seal(content)
    ):
        raise OutboxError("unsupported_evidence")
    try:
        # Only the sealed, application-issued canonical string reaches this parser;
        # embedded event_json strings legitimately exceed the v3 scalar cap.
        budget.remaining()
        value = json.loads(content)
        budget.remaining()
        if type(value) is not dict or set(value) != {
            "comparison_id",
            "journal_content_sha256",
            "rows",
        }:
            raise OutboxError("unsupported_evidence")
        comparison_id = token(value["comparison_id"], "cmp3:")
        digest = token(value["journal_content_sha256"], "")
        rows = value["rows"]
        if type(rows) is not list or len(rows) > 1000 or any(type(row) is not dict for row in rows):
            raise OutboxError("input_limit")
        return comparison_id, digest, cast(list[dict[str, object]], rows)
    except JournalError as error:
        raise OutboxError(error.category) from None


def _paths(captures: Path, journal: Path, outbox: Path, budget: Budget) -> None:
    for first, second in ((captures, journal), (captures, outbox), (journal, outbox)):
        budget.remaining()
        storage.reject_same_file(first, second)


def _verified_pair(
    captures: Path, journal: Path, comparison_id: str, budget: Budget
) -> tuple[dict[str, object], str]:
    try:
        retained = journal_get(journal, comparison_id, timeout=budget.remaining())
        # Freeze the one retained pair before comparator execution or any callback.
        request_json = canonical_bounded(retained["request"], 1024 * 1024, check=budget.remaining)
        expected = canonical_bounded(retained["comparison"], check=budget.remaining)
        digest = token(retained["content_sha256"], "")
        request_value, frozen = validate_pair(
            decode_json(request_json, maximum=1024 * 1024, check=budget.remaining),
            decode_json(expected, check=budget.remaining),
            check=budget.remaining,
        )
        request = parse_request(request_value)
        snapshots = read_multi_revision_snapshots(captures, request, timeout=budget.remaining())
        budget.remaining()
        actual = compare(request, snapshots)
        encoded = canonical_bounded(actual.payload, check=budget.remaining)
        if actual.payload.get("comparison_id") != comparison_id or encoded != expected:
            raise OutboxError("recompute_mismatch")
        budget.remaining()
        return frozen, digest
    except (CatalogError, DiscoveryError, JournalError, PersistenceError) as error:
        raise OutboxError(error.category) from None


def enqueue(
    captures_db: Path,
    journal_db: Path,
    outbox_db: Path,
    comparison_id: str,
    destination_key: str,
    *,
    timeout: float = 2.0,
) -> dict[str, object]:
    """Origin-check exactly one frozen comparison, prepare it, and commit atomically."""
    budget = Budget(timeout)
    comparison_id = token(comparison_id, "cmp3:")
    destination_key = destination(destination_key)
    _paths(captures_db, journal_db, outbox_db, budget)
    frozen, digest = _verified_pair(captures_db, journal_db, comparison_id, budget)
    events = frozen["events"]
    if type(events) is not list or len(events) > 1000:
        raise OutboxError("input_limit")
    rows: list[dict[str, object]] = []
    # Track the whole serialized envelope before retaining another prepared row.
    base: dict[str, object] = {
        "comparison_id": comparison_id,
        "journal_content_sha256": digest,
        "rows": [],
    }
    try:
        used = len(canonical_bounded(base, _MAXIMUM, check=budget.remaining))
        for event in events:
            budget.remaining()
            row = prepare_event(event, destination_key, comparison_id, check=budget.remaining)
            encoded = canonical_bounded(row, _MAXIMUM - used, check=budget.remaining)
            used += len(encoded) + bool(rows)
            if used > _MAXIMUM:
                raise OutboxError("input_limit")
            rows.append(row)
        base["rows"] = rows
        content = canonical_bounded(base, _MAXIMUM, check=budget.remaining)
    except JournalError as error:
        raise OutboxError(error.category) from None
    receipt = _Receipt(content)
    object.__setattr__(receipt, "_authority", (_AUTHORITY, id(receipt), _seal(content)))
    return storage._enqueue_verified(outbox_db, receipt, budget)


def recompute(
    captures_db: Path,
    journal_db: Path,
    outbox_db: Path,
    alert_id: str,
    comparison_id: str,
    *,
    timeout: float = 2.0,
) -> dict[str, object]:
    """Read-only origin proof for one explicit persisted window association."""
    budget = Budget(timeout)
    token(alert_id, "alt1:")
    token(comparison_id, "cmp3:")
    _paths(captures_db, journal_db, outbox_db, budget)
    alert = cast(
        dict[str, object], storage.get(outbox_db, alert_id, timeout=budget.remaining())["alert"]
    )
    association = storage.evidence_get(
        outbox_db, alert_id, comparison_id, timeout=budget.remaining()
    )
    frozen, digest = _verified_pair(captures_db, journal_db, comparison_id, budget)
    events = cast(list[dict[str, object]], frozen["events"])
    event = next((item for item in events if item["event_id"] == alert["event_id"]), None)
    if event is None or digest != association["journal_content_sha256"]:
        raise OutboxError("recompute_mismatch")
    try:
        if canonical_bounded(event, check=budget.remaining) != canonical_bounded(
            association["event"], check=budget.remaining
        ):
            raise OutboxError("recompute_mismatch")
        row = prepare_event(
            event, cast(str, alert["destination_key"]), comparison_id, check=budget.remaining
        )
        if row["intent_json"] != canonical_bounded(alert["intent"], check=budget.remaining):
            raise OutboxError("recompute_mismatch")
        for key in (
            "alert_id",
            "event_id",
            "channel",
            "policy_version",
            "renderer_version",
            "intent_sha256",
            "message_text",
            "message_sha256",
        ):
            if row[key] != alert[key]:
                raise OutboxError("recompute_mismatch")
        if row["event_sha256"] != association["event_sha256"]:
            raise OutboxError("recompute_mismatch")
    except JournalError as error:
        raise OutboxError(error.category) from None
    budget.remaining()
    return {
        "version": 1,
        "operation": "recompute",
        "result": "ok",
        "level": "origin-recompute",
        "alert_id": alert_id,
        "comparison_id": comparison_id,
    }
