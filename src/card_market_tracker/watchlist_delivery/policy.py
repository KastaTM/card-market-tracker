"""Pure reconstruction of every retained historical-content and consent relation."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from datetime import UTC, datetime
from typing import cast

from ..catalog.validation import CatalogError, _constant, _pairs, _preflight
from ..watchlist_alerts import policy as source_policy
from ..watchlist_alerts.errors import OutboxError
from . import models
from .errors import DeliveryError

Check = Callable[[], object] | None


def _check(check: Check) -> None:
    if check is not None:
        check()


def canonical(value: object, maximum: int = models.MAX_INPUT_BYTES, *, check: Check = None) -> str:
    try:
        return source_policy.canonical(value, maximum, check=check)
    except OutboxError as error:
        raise DeliveryError(error.category) from None


def _json(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    )


def digest(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def domain_digest(domain: str, value: object) -> str:
    return hashlib.sha256(
        domain.encode("ascii") + b"\x00" + canonical(value).encode("ascii")
    ).hexdigest()


def destination(value: object) -> str:
    try:
        return source_policy.destination(value)
    except OutboxError as error:
        raise DeliveryError(error.category) from None


def validate_id(value: object, prefix: str = "wtdl1_") -> str:
    if type(value) is not str or re.fullmatch(re.escape(prefix) + r"[0-9a-f]{64}", value) is None:
        raise DeliveryError("invalid_field")
    return value


def delivery_id(signal_id: object) -> str:
    return "wtdl1_" + domain_digest(
        "CMT_WATCHLIST_TELEGRAM_DELIVERY_V1",
        {
            "identity_version": 1,
            "provider": "telegram",
            "signal_id": validate_id(signal_id, "wsig1_"),
        },
    )


def _object(value: object, fields: frozenset[str]) -> dict[str, object]:
    if type(value) is not dict or set(value) != fields:
        raise DeliveryError("invalid_shape")
    return cast(dict[str, object], value)


def integer(value: object, maximum: int = models.MAX_ID) -> int:
    if type(value) is not int or not 1 <= value <= maximum:
        raise DeliveryError("invalid_field")
    return value


def timestamp(value: object) -> str:
    if (
        type(value) is not str
        or re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z", value)
        is None
    ):
        raise DeliveryError("invalid_timestamp")
    try:
        datetime.fromisoformat(value)
    except ValueError:
        raise DeliveryError("invalid_timestamp") from None
    return value


def now() -> str:
    value = datetime.now(UTC)
    return (
        f"{value.year:04d}-{value.month:02d}-{value.day:02d}T"
        f"{value.hour:02d}:{value.minute:02d}:{value.second:02d}.{value.microsecond:06d}Z"
    )


def route(value: object) -> dict[str, object]:
    row = _object(value, models.ROUTE_FIELDS)
    if type(row["route_version"]) is not int or row["route_version"] != 1:
        raise DeliveryError("unsupported_version")
    if (
        type(row["provider"]) is not str
        or type(row["chat_type"]) is not str
        or row["provider"] != "telegram"
        or row["chat_type"] != "private"
        or row["operator_attested"] is not True
    ):
        raise DeliveryError("invalid_destination")
    return {
        "route_version": 1,
        "provider": "telegram",
        "destination_key": destination(row["destination_key"]),
        "bot_id": integer(row["bot_id"]),
        "chat_id": integer(row["chat_id"]),
        "chat_type": "private",
        "operator_attested": True,
    }


def route_sha256(value: object) -> str:
    return domain_digest("CMT_WATCHLIST_TELEGRAM_ROUTE_V1", route(value))


def decode(raw: object, maximum: int, *, check: Check = None) -> object:
    if type(raw) is not str or not raw.isascii():
        raise DeliveryError("invalid_json")
    if len(raw) > maximum:
        raise DeliveryError("input_limit")
    _check(check)
    try:
        _preflight(raw)
        value: object = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)
    except CatalogError as error:
        raise DeliveryError(error.category) from None
    except (ValueError, RecursionError):
        raise DeliveryError("invalid_json") from None
    if canonical(value, maximum, check=check) != raw:
        raise DeliveryError("invalid_json")
    return value


def _from_evidence(
    evidence: object, destination_key: object, check: Check
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    try:
        prepared = source_policy.prepare(evidence, destination_key, check=check)
    except OutboxError as error:
        raise DeliveryError(error.category) from None
    bundle = cast(dict[str, object], json.loads(cast(str, prepared["evidence_json"])))
    old = cast(dict[str, object], cast(dict[str, object], bundle["predecessor"])["snapshot"])
    current = cast(dict[str, object], cast(dict[str, object], bundle["current"])["snapshot"])
    entry = cast(dict[str, object], current["entry"])
    if canonical(old["entry"], models.MAX_ENTRY_BYTES, check=check) != canonical(
        entry, models.MAX_ENTRY_BYTES, check=check
    ):
        raise DeliveryError("identity_conflict")
    intent = cast(dict[str, object], json.loads(cast(str, prepared["intent_json"])))
    message = cast(str, prepared["message_text"])
    if not 1 <= len(message.encode("utf-8")) <= models.MAX_MESSAGE_BYTES:
        raise DeliveryError("input_limit")
    source = {key: prepared[key] for key in models.ALERT_FIELDS - {"intent", "first_prepared_at"}}
    source["intent"] = intent
    return prepared, source, entry


def _build(
    evidence: object, selected_route: object, operation: object, check: Check
) -> tuple[dict[str, object], dict[str, object]]:
    if operation not in ("prepare", "claim") or type(operation) is not str:
        raise DeliveryError("invalid_field")
    frozen_route = route(selected_route)
    prepared, source, entry = _from_evidence(evidence, frozen_route["destination_key"], check)
    entry_json = canonical(entry, models.MAX_ENTRY_BYTES, check=check)
    route_json = canonical(frozen_route, models.MAX_ROUTE_BYTES, check=check)
    rdigest = route_sha256(frozen_route)
    source_digest = digest(_json(source))
    consent = {
        "consent_version": 1,
        "acknowledgement": models.ACKNOWLEDGEMENT,
        "alert_id": prepared["alert_id"],
        "signal_id": prepared["signal_id"],
        "watch_id": entry["watch_id"],
        "revision": entry["revision"],
        "message_sha256": prepared["message_sha256"],
        "evidence_sha256": prepared["evidence_sha256"],
        "entry_sha256": digest(entry_json),
        "intent_sha256": prepared["intent_sha256"],
        "source_alert_sha256": source_digest,
        "route_sha256": rdigest,
    }
    binding = {
        "binding_version": 1,
        "provider": "telegram",
        "delivery_id": delivery_id(prepared["signal_id"]),
        "destination_key": frozen_route["destination_key"],
        "cmt_id": entry["cmt_id"],
        "policy_version": prepared["policy_version"],
        "renderer_version": prepared["renderer_version"],
        "consent_sha256": domain_digest("CMT_WATCHLIST_TELEGRAM_CONSENT_V1", consent),
        **{key: consent[key] for key in models.BINDING_FIELDS & models.CONSENT_FIELDS},
    }
    result: dict[str, object] = {
        "authority_version": 1,
        "operation": operation,
        "binding": binding,
        "binding_sha256": domain_digest("CMT_WATCHLIST_TELEGRAM_BINDING_V1", binding),
        "entry_json": entry_json,
        "intent_json": prepared["intent_json"],
        "evidence_json": prepared["evidence_json"],
        "message_text": prepared["message_text"],
        "route_json": route_json,
        "consent_json": canonical(consent, models.MAX_CONSENT_BYTES, check=check),
    }
    _check(check)
    return result, source


def prepare(
    alert: object,
    evidence: object,
    selected_route: object,
    *,
    operation: str = "prepare",
    check: Check = None,
) -> dict[str, object]:
    """Reconstruct intrinsic content; this plain result confers no writer authority."""
    row = _object(alert, models.ALERT_FIELDS)
    rebuilt, source = _build(evidence, selected_route, operation, check)
    actual = {key: item for key, item in row.items() if key != "first_prepared_at"}
    if _json(actual) != _json(source):
        raise DeliveryError("recompute_mismatch")
    return rebuilt


def validate_prepared(value: object, *, check: Check = None) -> dict[str, object]:
    """Independently rebuild all embedded schemas and every complete binding relation."""
    row = _object(value, models.PREPARED_FIELDS)
    if type(row["authority_version"]) is not int or row["authority_version"] != 1:
        raise DeliveryError("unsupported_version")
    evidence = decode(row["evidence_json"], models.MAX_EVIDENCE_BYTES, check=check)
    frozen_route = decode(row["route_json"], models.MAX_ROUTE_BYTES, check=check)
    rebuilt, _ = _build(evidence, frozen_route, row["operation"], check)
    for key, expected in rebuilt.items():
        actual = row[key]
        if type(actual) is not type(expected) or _json(actual) != _json(expected):
            raise DeliveryError("invalid_transition")
    _check(check)
    return rebuilt
