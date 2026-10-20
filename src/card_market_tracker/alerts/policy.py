"""Versioned pure alert identity and complete event-to-intent validation."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from typing import cast

from ..catalog.manifest import parse_reference
from ..catalog.validation import CatalogError, object_value, uuid_value
from ..discovery.journal_errors import JournalError
from ..discovery.journal_validation import canonical_bounded, decode_json, validate_pair
from ..discovery.multi_models import REVIEWED_PAIR_PROFILE, SYNTHETIC_PROFILE
from ..discovery.validation import CANDIDATE_CATEGORIES, canonical_timestamp
from .errors import OutboxError

POLICY_VERSION = "discovery_reference_alert_v1"
RENDERER_VERSION = 1
CHANNEL = "offline_preview"
_FIELDS = {
    "event_id",
    "type",
    "reference",
    "status",
    "category",
    "cmt_id",
    "current_batch_id",
    "captured_at",
    "first_observed_in_window_at",
}
_INTENT_KEYS = _FIELDS | {
    "version",
    "policy_version",
    "renderer_version",
    "channel",
    "profile",
    "evidence_level",
    "mode",
}


def destination(value: object) -> str:
    if type(value) is not str or re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", value) is None:
        raise OutboxError("invalid_field")
    return value


def token(value: object, prefix: str) -> str:
    if type(value) is not str or re.fullmatch(re.escape(prefix) + r"[0-9a-f]{64}", value) is None:
        raise OutboxError("invalid_field")
    return value


def alert_id(destination_key: str, event_id: str) -> str:
    preimage = {
        "identity_version": 1,
        "destination_key": destination(destination_key),
        "event_id": token(event_id, "evt3:"),
    }
    return "alt1:" + hashlib.sha256(canonical_bounded(preimage).encode("ascii")).hexdigest()


def validate_intent(value: object) -> dict[str, object]:
    """Validate frozen intrinsic fields without treating their claims as authority."""
    try:
        intent = object_value(value)
        if set(intent) != _INTENT_KEYS:
            raise OutboxError("storage_corrupt")
        canonical_bounded(intent, 64 * 1024)
        if not (
            type(intent["version"]) is int
            and intent["version"] == 1
            and intent["policy_version"] == POLICY_VERSION
            and type(intent["renderer_version"]) is int
            and intent["renderer_version"] == RENDERER_VERSION
            and intent["channel"] == CHANNEL
        ):
            raise OutboxError("storage_corrupt")
        token(intent["event_id"], "evt3:")
        uuid_value(intent["current_batch_id"])
        canonical_timestamp(intent["captured_at"])
        if intent["first_observed_in_window_at"] != intent["captured_at"]:
            raise OutboxError("storage_corrupt")
        reference = parse_reference(intent["reference"])
        if intent["status"] == "accepted":
            if not (
                reference.kind == "set"
                and intent["type"] == "SET_REFERENCE_FIRST_OBSERVED"
                and intent["category"] is None
            ):
                raise OutboxError("storage_corrupt")
            uuid_value(intent["cmt_id"])
        elif intent["status"] == "candidate":
            if not (
                intent["type"] == "CANDIDATE_REFERENCE_FIRST_OBSERVED"
                and intent["cmt_id"] is None
                and type(intent["category"]) is str
                and intent["category"] in CANDIDATE_CATEGORIES
            ):
                raise OutboxError("storage_corrupt")
            variant = reference.kind == "card" and reference.variant == "unknown"
            language = reference.kind in ("card", "sealed") and reference.language is None
            category = intent["category"]
            if (
                (category == "unknown_variant" and not variant)
                or (category == "unknown_language" and (not language or variant))
                or (
                    category not in ("unknown_variant", "unknown_language")
                    and (variant or language)
                )
            ):
                raise OutboxError("storage_corrupt")
        else:
            raise OutboxError("storage_corrupt")
        if intent["profile"] == SYNTHETIC_PROFILE:
            expected = ("synthetic", "producer_declared")
        elif intent["profile"] == REVIEWED_PAIR_PROFILE:
            expected = ("pinned", "verified_local_pinned_bundle")
        else:
            raise OutboxError("invalid_profile")
        if (intent["mode"], intent["evidence_level"]) != expected:
            raise OutboxError("unsupported_evidence")
        # Snapshot independently from the caller's mutable dictionaries.
        return cast(
            dict[str, object], decode_json(canonical_bounded(intent, 64 * 1024), maximum=64 * 1024)
        )
    except (CatalogError, JournalError, KeyError, TypeError, RecursionError) as error:
        raise OutboxError(getattr(error, "category", "storage_corrupt")) from None


def prepare_event(
    event: object,
    destination_key: str,
    comparison_id: str,
    *,
    check: Callable[[], object] | None = None,
) -> dict[str, object]:
    """Validate the complete standalone v3 event, then derive exact persisted fields."""
    from .render import render

    destination_key = destination(destination_key)
    token(comparison_id, "cmp3:")
    try:
        # Bound before walking or copying the input, including all repeated history.
        event_json = canonical_bounded(event, check=check)
        frozen = object_value(decode_json(event_json, check=check))
        evidence = object_value(frozen["evidence"])
        current = object_value(evidence["current"])
        history = evidence["history"]
        if type(history) is not list or not 1 <= len(history) <= 32:
            raise OutboxError("storage_corrupt")
        scope = object_value(current["scope"])
        context = {key: scope[key] for key in ("namespace", "kind", "language")}

        def selection(item: object) -> dict[str, object]:
            unit = object_value(item)
            return {"batch_id": unit["batch_id"], "selector": unit["selector"]}

        historical_records = sum(
            len(cast(list[object], object_value(object_value(item)["scope"])["record_indexes"]))
            for item in history
        )
        current_records = len(cast(list[object], scope["record_indexes"]))
        request = {
            "version": 3,
            "profile": current["profile"],
            "context": context,
            "current": selection(current),
            "history": [selection(item) for item in history],
        }
        result = {
            "version": 3,
            "result": "discoveries",
            "comparison_id": comparison_id,
            "profile": current["profile"],
            "context": context,
            "current": current,
            "history": history,
            "window": {"scope": "explicit_selected_capture_units"},
            "counts": {
                "validated_batches": len(history) + 1,
                "validated_records": current_records + historical_records,
                "current_selected_records": current_records,
                "historical_selected_records": historical_records,
                "current_selected_references": current_records,
                "historical_selected_references": historical_records,
                "events": 1,
            },
            "events": [frozen],
        }
        validate_pair(request, result, check=check)
        intent = validate_intent(
            {
                **{key: frozen[key] for key in _FIELDS},
                "version": 1,
                "policy_version": POLICY_VERSION,
                "renderer_version": RENDERER_VERSION,
                "channel": CHANNEL,
                "profile": current["profile"],
                "evidence_level": current["evidence_state"],
                "mode": current["mode"],
            }
        )
        intent_json = canonical_bounded(intent, 64 * 1024, check=check)
        message = render(intent)
        return {
            "alert_id": alert_id(destination_key, cast(str, frozen["event_id"])),
            "destination_key": destination_key,
            "event_id": frozen["event_id"],
            "channel": CHANNEL,
            "policy_version": POLICY_VERSION,
            "renderer_version": RENDERER_VERSION,
            "intent_json": intent_json,
            "intent_sha256": hashlib.sha256(intent_json.encode("ascii")).hexdigest(),
            "message_text": message,
            "message_sha256": hashlib.sha256(message.encode("utf-8")).hexdigest(),
            "event_json": event_json,
            "event_sha256": hashlib.sha256(event_json.encode("ascii")).hexdigest(),
        }
    except (
        CatalogError,
        JournalError,
        KeyError,
        TypeError,
        AttributeError,
        RecursionError,
    ) as error:
        raise OutboxError(getattr(error, "category", "storage_corrupt")) from None
