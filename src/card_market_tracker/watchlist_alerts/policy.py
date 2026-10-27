"""Pure complete-evidence reconstruction and stable offline Watchlist alert policy."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from typing import cast

from ..catalog.validation import CatalogError, _constant, _pairs, _preflight
from ..watchlist import validation
from ..watchlist.errors import WatchlistError
from ..watchlist_journal import identity, transitions
from ..watchlist_journal.errors import JournalError
from .errors import OutboxError
from .models import (
    CHANNEL,
    EVALUATION_FIELDS,
    EVIDENCE_FIELDS,
    MAX_EVIDENCE_BYTES,
    MAX_INPUT_BYTES,
    MAX_INTENT_BYTES,
    POLICY_VERSION,
    PREPARED_FIELDS,
    RENDERER_VERSION,
    SIGNAL_FIELDS,
    STATE,
)

Check = Callable[[], object] | None


def _check(check: Check) -> None:
    if check is not None:
        check()


def canonical(value: object, maximum: int = MAX_INPUT_BYTES, *, check: Check = None) -> str:
    """Use accepted strict bounded semantic JSON, with cooperative outer checks."""
    _check(check)
    try:
        raw = validation.canonical(value)
    except WatchlistError as error:
        raise OutboxError(error.category) from None
    if len(raw) > maximum:
        raise OutboxError("input_limit")
    _check(check)
    return raw


def digest(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def destination(value: object) -> str:
    if type(value) is not str or re.fullmatch(r"[a-z][a-z0-9_-]{0,63}", value) is None:
        raise OutboxError("invalid_field")
    return value


def validate_id(value: object, prefix: str = "walt1_") -> str:
    try:
        return identity.validate_id(value, prefix)
    except JournalError as error:
        raise OutboxError(error.category) from None


def alert_id(destination_key: object, signal_id: object) -> str:
    payload = {
        "identity_version": 1,
        "destination_key": destination(destination_key),
        "signal_id": validate_id(signal_id, "wsig1_"),
    }
    return (
        "walt1_"
        + hashlib.sha256(
            b"CMT_WATCHLIST_ALERT_V1\x00" + canonical(payload).encode("ascii")
        ).hexdigest()
    )


def _object(value: object, fields: frozenset[str]) -> dict[str, object]:
    if type(value) is not dict or set(value) != fields:
        raise OutboxError("invalid_shape")
    return cast(dict[str, object], value)


def _evaluation(value: object, check: Check) -> dict[str, object]:
    row = _object(value, EVALUATION_FIELDS)
    _check(check)
    snapshot, result = identity.validate_snapshot(row["snapshot"])
    key = validate_id(row["evaluation_id"], "wje1_")
    ordinal = row["ordinal"]
    if type(ordinal) is not int or ordinal < 1:
        raise OutboxError("invalid_field")
    prior = row["predecessor_evaluation_id"]
    if prior is not None:
        validate_id(prior, "wje1_")
    if (
        key != identity._evaluation_id(snapshot)
        or row["sequence_id"] != snapshot["sequence_id"]
        or canonical(row["snapshot"], check=check) != canonical(snapshot, check=check)
        or canonical(row["evaluation_result"], check=check) != canonical(result, check=check)
    ):
        raise OutboxError("invalid_transition")
    return {
        "evaluation_id": key,
        "sequence_id": snapshot["sequence_id"],
        "ordinal": ordinal,
        "predecessor_evaluation_id": prior,
        "snapshot": snapshot,
        "evaluation_result": result,
    }


def validate_evidence(value: object, *, check: Check = None) -> dict[str, object]:
    """Independently reconstruct BOTH results, identities and the selected transition."""
    try:
        raw = canonical(value, MAX_EVIDENCE_BYTES, check=check)
        row = _object(value, EVIDENCE_FIELDS)
        if type(row["version"]) is not int or row["version"] != 1:
            raise OutboxError("unsupported_version")
        signal = _object(row["signal"], SIGNAL_FIELDS)
        predecessor = _evaluation(row["predecessor"], check)
        current = _evaluation(row["current"], check)
        old_id, new_id = predecessor["evaluation_id"], current["evaluation_id"]
        old_ordinal, new_ordinal = predecessor["ordinal"], current["ordinal"]
        earlier = predecessor["predecessor_evaluation_id"]
        if (
            new_ordinal != cast(int, old_ordinal) + 1
            or current["predecessor_evaluation_id"] != old_id
            or (earlier is None) != (old_ordinal == 1)
            or earlier in (old_id, new_id)
        ):
            raise OutboxError("invalid_transition")
        before = cast(dict[str, object], predecessor["snapshot"])
        after = cast(dict[str, object], current["snapshot"])
        old_result = cast(dict[str, object], predecessor["evaluation_result"])
        new_result = cast(dict[str, object], current["evaluation_result"])
        expected = transitions._derive_normalized_signals(
            (before, old_result, cast(str, old_id)), (after, new_result, cast(str, new_id))
        )
        _check(check)
        body = {key: item for key, item in signal.items() if key != "signal_id"}
        if validate_id(signal["signal_id"], "wsig1_") != identity.signal_id(body) or not any(
            canonical(signal) == canonical(item) for item in expected
        ):
            raise OutboxError("invalid_transition")
        result = {
            "version": 1,
            "signal": dict(signal),
            "predecessor": predecessor,
            "current": current,
        }
        if raw != canonical(result, MAX_EVIDENCE_BYTES, check=check):
            raise OutboxError("invalid_transition")
        return result
    except (JournalError, WatchlistError) as error:
        raise OutboxError(error.category) from None


def _intent(evidence: dict[str, object]) -> dict[str, object]:
    signal = cast(dict[str, object], evidence["signal"])
    point = cast(dict[str, object], evidence["current"])
    snapshot = cast(dict[str, object], point["snapshot"])
    entry = cast(dict[str, object], snapshot["entry"])
    return {
        "version": 1,
        "policy_version": POLICY_VERSION,
        "renderer_version": RENDERER_VERSION,
        "channel": CHANNEL,
        "state": STATE,
        "signal_id": signal["signal_id"],
        "kind": signal["kind"],
        "mode": signal["mode"],
        "rule": signal["rule"],
        "sequence_id": signal["sequence_id"],
        "watch_id": entry["watch_id"],
        "revision": entry["revision"],
        "cmt_id": entry["cmt_id"],
        "from_evaluation_id": signal["from_evaluation_id"],
        "to_evaluation_id": signal["to_evaluation_id"],
    }


def intent_from_evidence(value: object, *, check: Check = None) -> dict[str, object]:
    return _intent(validate_evidence(value, check=check))


def prepare(evidence: object, destination_key: object, *, check: Check = None) -> dict[str, object]:
    """Construct intrinsic bytes; this public data result grants NO write authority."""
    from .render import _render_normalized

    alias = destination(destination_key)
    bundle = validate_evidence(evidence, check=check)
    intent = _intent(bundle)
    intent_json = canonical(intent, MAX_INTENT_BYTES, check=check)
    evidence_json = canonical(bundle, MAX_EVIDENCE_BYTES, check=check)
    message = _render_normalized(intent, bundle)
    _check(check)
    signal = cast(dict[str, object], bundle["signal"])["signal_id"]
    return {
        "version": 1,
        "alert_id": alert_id(alias, signal),
        "destination_key": alias,
        "signal_id": signal,
        "policy_version": POLICY_VERSION,
        "renderer_version": RENDERER_VERSION,
        "channel": CHANNEL,
        "state": STATE,
        "intent_json": intent_json,
        "intent_sha256": digest(intent_json),
        "evidence_json": evidence_json,
        "evidence_sha256": digest(evidence_json),
        "message_text": message,
        "message_sha256": digest(message),
    }


def _decode_document(raw: object, maximum: int, check: Check) -> object:
    if type(raw) is not str:
        raise OutboxError("invalid_field")
    if len(raw) > maximum:
        raise OutboxError("input_limit")
    if not raw.isascii():
        raise OutboxError("invalid_json")
    _check(check)
    try:
        _preflight(raw)
        value: object = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)
    except CatalogError as error:
        raise OutboxError(error.category) from None
    except (ValueError, RecursionError):
        raise OutboxError("invalid_json") from None
    if canonical(value, maximum, check=check) != raw:
        raise OutboxError("invalid_json")
    return value


def validate_prepared(value: object, *, check: Check = None) -> dict[str, object]:
    """Rebuild a bounded envelope, treating encoded documents separately from scalars."""
    row = _object(value, PREPARED_FIELDS)
    evidence = _decode_document(row["evidence_json"], MAX_EVIDENCE_BYTES, check)
    rebuilt = prepare(evidence, row["destination_key"], check=check)
    # Canonical semantic checks belong to the embedded documents, not their strings
    # or the complete message. Their exact expected bytes enforce envelope types.
    for key, expected in rebuilt.items():
        actual = row[key]
        if type(actual) is not type(expected) or actual != expected:
            raise OutboxError("invalid_transition")
    _check(check)
    return rebuilt
