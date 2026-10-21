"""Original-capture proof, sealed preparation and one durable manual send attempt."""

from __future__ import annotations

import hashlib
import json
import math
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from itertools import combinations
from pathlib import Path
from typing import Protocol, cast

from ..alerts import application as outbox_application
from ..alerts import storage as outbox_storage
from ..alerts.errors import OutboxError
from ..alerts.policy import destination, token
from ..discovery.journal_errors import JournalError
from ..discovery.journal_validation import canonical_bounded
from . import storage
from .errors import DeliveryError
from .transport import TelegramTransport, TransportResult

_AUTHORITY = object()
_BINDING_KEYS = frozenset(
    {
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
    }
)


class Transport(Protocol):
    def check_configuration(self) -> None: ...
    def validate_destination(self, bot_id: int, chat_id: int, *, timeout: float = 15.0) -> None: ...
    def validate_bot(self, bot_id: int, *, timeout: float = 15.0) -> None: ...
    def send(
        self, bot_id: int, chat_id: int, message_text: str, *, timeout: float = 15.0
    ) -> TransportResult: ...


class _Budget:
    def __init__(self, timeout: float, maximum: float = 5.0) -> None:
        if (
            type(timeout) not in (int, float)
            or not math.isfinite(timeout)
            or not 0 < timeout <= maximum
        ):
            raise DeliveryError("invalid_field")
        self.deadline = time.monotonic() + timeout
        self.reserve = min(0.5, timeout / 5)

    def remaining(self, *, reserve: bool = False) -> float:
        left = self.deadline - time.monotonic() - (self.reserve if reserve else 0)
        if left <= 0:
            raise DeliveryError("deadline_exceeded")
        return left

    def local(self, *, reserve: bool = False) -> float:
        return min(5.0, self.remaining(reserve=reserve))


@dataclass(frozen=True)
class _Receipt:
    content_json: str
    _authority: object = field(default=None, init=False, repr=False, compare=False)


def _digest(content: str) -> str:
    return hashlib.sha256(content.encode("ascii")).hexdigest()


def _consume_receipt(receipt: object) -> dict[str, object]:
    """Only an unmodified application-issued instance grants database authority."""
    if type(receipt) is not _Receipt:
        raise DeliveryError("unsupported_evidence")
    content = receipt.content_json
    if type(content) is not str or len(content) > 4096 or not content.isascii():
        raise DeliveryError("unsupported_evidence")
    authority = receipt._authority
    if (
        type(authority) is not tuple
        or len(authority) != 3
        or authority[0] is not _AUTHORITY
        or authority[1] != id(receipt)
        or authority[2] != _digest(content)
    ):
        raise DeliveryError("unsupported_evidence")
    value = json.loads(content)
    if type(value) is not dict or set(value) != _BINDING_KEYS:
        raise DeliveryError("unsupported_evidence")
    return cast(dict[str, object], value)


def _canonical(value: object, budget: _Budget) -> str:
    try:
        return canonical_bounded(value, 16 * 1024 * 1024, check=budget.remaining)
    except JournalError as error:
        raise DeliveryError(error.category) from None


def _paths(paths: tuple[Path, Path, Path, Path], budget: _Budget) -> None:
    try:
        for left, right in combinations(paths, 2):
            budget.remaining()
            outbox_storage.reject_same_file(left, right)
    except OutboxError as error:
        raise DeliveryError(error.category) from None


def _snapshot(outbox_db: Path, aid: str, cid: str, budget: _Budget) -> tuple[str, str]:
    try:
        alert = outbox_storage.get(outbox_db, aid, timeout=budget.local())["alert"]
        association = outbox_storage.evidence_get(outbox_db, aid, cid, timeout=budget.local())
        evidence = {
            key: association[key]
            for key in (
                "alert_id",
                "comparison_id",
                "event",
                "journal_content_sha256",
                "event_sha256",
            )
        }
        return _canonical(alert, budget), _canonical(evidence, budget)
    except OutboxError as error:
        raise DeliveryError(error.category) from None


def _verified(
    captures_db: Path,
    journal_db: Path,
    outbox_db: Path,
    ledger_db: Path,
    alert_id: str,
    comparison_id: str,
    alias: str,
    budget: _Budget,
) -> tuple[_Receipt, str]:
    try:
        aid, cid = token(alert_id, "alt1:"), token(comparison_id, "cmp3:")
        alias = destination(alias)
    except OutboxError as error:
        raise DeliveryError(error.category) from None
    _paths((captures_db, journal_db, outbox_db, ledger_db), budget)
    before = _snapshot(outbox_db, aid, cid, budget)
    try:
        outbox_application.recompute(
            captures_db, journal_db, outbox_db, aid, cid, timeout=budget.local()
        )
    except OutboxError as error:
        raise DeliveryError(error.category) from None
    after = _snapshot(outbox_db, aid, cid, budget)
    if after != before:
        raise DeliveryError("recompute_mismatch")
    alert, evidence = (cast(dict[str, object], json.loads(item)) for item in before)
    if alert["destination_key"] != alias:
        raise DeliveryError("invalid_destination")
    binding = {
        "alert_id": aid,
        "event_id": alert["event_id"],
        "comparison_id": cid,
        "alias": alias,
        "intent_sha256": alert["intent_sha256"],
        "message_sha256": alert["message_sha256"],
        "event_sha256": evidence["event_sha256"],
        "journal_content_sha256": evidence["journal_content_sha256"],
        "alert_content_sha256": _digest(before[0]),
        "evidence_content_sha256": _digest(before[1]),
    }
    content = _canonical(binding, budget)
    receipt = _Receipt(content)
    object.__setattr__(receipt, "_authority", (_AUTHORITY, id(receipt), _digest(content)))
    return receipt, cast(str, alert["message_text"])


def prepare(
    captures_db: Path,
    journal_db: Path,
    outbox_db: Path,
    ledger_db: Path,
    alert_id: str,
    comparison_id: str,
    alias: str,
    *,
    timeout: float = 2.0,
) -> dict[str, object]:
    budget = _Budget(timeout)
    receipt, _ = _verified(
        captures_db, journal_db, outbox_db, ledger_db, alert_id, comparison_id, alias, budget
    )
    return storage._prepare_verified(ledger_db, receipt, timeout=budget.local())


def recompute(
    captures_db: Path,
    journal_db: Path,
    outbox_db: Path,
    ledger_db: Path,
    delivery_id: str,
    *,
    timeout: float = 2.0,
) -> dict[str, object]:
    budget = _Budget(timeout)
    delivery = storage.load_delivery(ledger_db, delivery_id, timeout=budget.local())
    receipt, _ = _verified(
        captures_db,
        journal_db,
        outbox_db,
        ledger_db,
        cast(str, delivery["alert_id"]),
        cast(str, delivery["comparison_id"]),
        cast(str, delivery["alias"]),
        budget,
    )
    if any(delivery[key] != value for key, value in _consume_receipt(receipt).items()):
        raise DeliveryError("recompute_mismatch")
    return {
        "version": 1,
        "operation": "recompute",
        "result": "ok",
        "level": "origin-recompute",
        "delivery_id": delivery_id,
    }


def destination_validate(
    ledger_db: Path,
    alias: str,
    *,
    transport: Transport | None = None,
    timeout: float = 15.0,
) -> dict[str, object]:
    budget = _Budget(timeout, 30.0)
    route = storage.load_destination(ledger_db, alias, timeout=budget.local())
    client = transport if transport is not None else TelegramTransport()
    client.check_configuration()
    client.validate_destination(
        cast(int, route["bot_id"]),
        cast(int, route["chat_id"]),
        timeout=budget.remaining(reserve=True),
    )
    return storage.destination_validated(
        ledger_db,
        alias,
        cast(int, route["bot_id"]),
        cast(int, route["chat_id"]),
        timeout=budget.local(),
    )


def _preflight(delivery: dict[str, object]) -> None:
    if delivery["send_quarantined"]:
        raise DeliveryError("send_quarantined")
    if delivery["state"] not in ("ready", "retryable"):
        raise DeliveryError("delivery_blocked")
    if not delivery["validated_at"]:
        raise DeliveryError("not_validated")
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    updated = delivery.get("updated_at")
    if type(updated) is str and now < updated:
        raise DeliveryError("clock_skew")
    not_before = delivery.get("not_before")
    if type(not_before) is str and now < not_before:
        raise DeliveryError("retry_not_due")


def send(
    captures_db: Path,
    journal_db: Path,
    outbox_db: Path,
    ledger_db: Path,
    delivery_id: str,
    *,
    transport: Transport | None = None,
    timeout: float = 15.0,
) -> dict[str, object]:
    budget = _Budget(timeout, 30.0)
    delivery = storage.load_delivery(ledger_db, delivery_id, timeout=budget.local())
    if delivery["state"] == "confirmed":
        _paths((captures_db, journal_db, outbox_db, ledger_db), budget)
        payload = storage.get(ledger_db, delivery_id, timeout=budget.local())
        return {**payload, "operation": "send", "result": "replay"}
    _preflight(delivery)
    receipt, message = _verified(
        captures_db,
        journal_db,
        outbox_db,
        ledger_db,
        cast(str, delivery["alert_id"]),
        cast(str, delivery["comparison_id"]),
        cast(str, delivery["alias"]),
        budget,
    )
    if any(delivery[key] != value for key, value in _consume_receipt(receipt).items()):
        raise DeliveryError("recompute_mismatch")
    client = transport if transport is not None else TelegramTransport()
    client.check_configuration()
    client.validate_bot(cast(int, delivery["bot_id"]), timeout=budget.remaining(reserve=True))
    claimed = storage._claim_verified(
        ledger_db, delivery_id, receipt, timeout=budget.local(reserve=True)
    )
    if claimed["result"] == "replay":
        payload = storage.get(ledger_db, delivery_id, timeout=budget.local())
        return {**payload, "operation": "send", "result": "replay"}
    attempt_id = cast(str, claimed["attempt_id"])
    route = cast(dict[str, object], claimed["delivery"])
    try:
        result = client.send(
            cast(int, route["bot_id"]),
            cast(int, route["chat_id"]),
            message,
            timeout=budget.remaining(reserve=True),
        )
        if not isinstance(result, TransportResult):
            raise DeliveryError("provider_invalid")
    except Exception:
        result = TransportResult("uncertain", "network_uncertain")
    try:
        safe_receipt: dict[str, object] | None = None
        if result.receipt is not None:
            safe_receipt = {
                key: getattr(result.receipt, key)
                for key in ("message_id", "accepted_at", "bot_id", "chat_id")
            }
        finished = storage.finish(
            ledger_db,
            delivery_id,
            attempt_id,
            state=result.state,
            error_category=result.error_category,
            receipt=safe_receipt,
            retry_after=result.retry_after,
            timeout=budget.local(),
        )
    except Exception:
        # Remote acceptance is not confirmation until the local receipt is durable.
        # Failed fallback leaves in_flight, which only explicit recovery may resolve.
        try:
            storage.finish(
                ledger_db,
                delivery_id,
                attempt_id,
                state="uncertain",
                error_category="local_commit_failed",
                timeout=budget.local(),
            )
        except Exception:
            pass
        raise DeliveryError("local_commit_failed") from None
    return {
        **finished,
        "operation": "send",
        "previous_state": delivery["state"],
        "result": "ok" if finished["state"] == "confirmed" else "error",
        **(
            {"error_category": finished.get("error_category", result.error_category)}
            if finished.get("error_category", result.error_category) is not None
            else {}
        ),
    }
