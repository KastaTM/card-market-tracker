"""Strict snapshots and frozen domain-separated semantic equality identities."""

from __future__ import annotations

import hashlib
import re
from typing import cast

from ..watchlist import evaluation, validation
from ..watchlist.errors import WatchlistError
from .errors import JournalError
from .models import (
    EVALUATION_DOMAIN,
    MAX_SNAPSHOT_BYTES,
    POLICY_VERSION,
    RULES,
    SEQUENCE_DOMAIN,
    SIGNAL_DOMAIN,
    SIGNAL_KIND,
    SIGNAL_MODE,
)

_SNAPSHOT_FIELDS = frozenset(
    {
        "version",
        "sequence_id",
        "policy_version",
        "entry",
        "current",
        "previous",
        "as_of",
    }
)
_SIGNAL_FIELDS = frozenset(
    {
        "version",
        "kind",
        "mode",
        "sequence_id",
        "rule",
        "from_evaluation_id",
        "to_evaluation_id",
    }
)


def canonical(value: object) -> str:
    """Use exactly the accepted P5a bounded canonical JSON encoding."""
    try:
        return validation.canonical(value)
    except WatchlistError as error:
        raise JournalError(error.category) from None


def _object(value: object, fields: frozenset[str]) -> dict[str, object]:
    canonical(value)
    if type(value) is not dict or set(value) != fields:
        raise JournalError("invalid_shape")
    return cast(dict[str, object], value)


def validate_id(value: object, prefix: str) -> str:
    if type(value) is not str or re.fullmatch(re.escape(prefix) + r"[0-9a-f]{64}", value) is None:
        raise JournalError("invalid_field")
    return value


def preimage(domain: str, value: object) -> bytes:
    return domain.encode("ascii") + b"\x00" + canonical(value).encode("utf-8")


def _identity(prefix: str, domain: str, value: object) -> str:
    return prefix + hashlib.sha256(preimage(domain, value)).hexdigest()


def sequence_id(entry: object, current: object) -> str:
    try:
        watch, sample = validation.parse_entry(entry), validation.parse_sample(current)
    except WatchlistError as error:
        raise JournalError(error.category) from None
    if sample["cmt_id"] != watch["cmt_id"]:
        raise JournalError("incompatible_context")
    return _identity(
        "wjs1_",
        SEQUENCE_DOMAIN,
        {
            "watch_id": watch["watch_id"],
            "revision": watch["revision"],
            "policy_version": POLICY_VERSION,
            "series_key": sample["series_key"],
        },
    )


def normalized_snapshot(
    entry: object, current: object, previous: object = None, *, as_of: object
) -> dict[str, object]:
    """Validate all evidence and derive the exact evaluation identity object."""
    try:
        watch = validation.parse_entry(entry)
        sample = validation.parse_sample(current)
        prior = None if previous is None else validation.parse_sample(previous)
        clock = validation.timestamp(as_of)
        result = evaluation.evaluate(watch, sample, prior, as_of=clock)
    except WatchlistError as error:
        raise JournalError(error.category) from None
    snapshot = {
        "version": 1,
        "sequence_id": sequence_id(watch, sample),
        "policy_version": POLICY_VERSION,
        "entry": watch,
        "current": sample,
        "previous": prior,
        "as_of": clock,
    }
    # The complete retained evidence, including its recalculated result, is bounded.
    if (
        len(canonical({"snapshot": snapshot, "evaluation_result": result}).encode("utf-8"))
        > MAX_SNAPSHOT_BYTES
    ):
        raise JournalError("input_limit")
    return snapshot


def validate_snapshot(value: object) -> tuple[dict[str, object], dict[str, object]]:
    """Recompute rather than trust snapshots, verdicts or asserted verification."""
    row = _object(value, _SNAPSHOT_FIELDS)
    if type(row["version"]) is not int or row["version"] != 1:
        raise JournalError("unsupported_version")
    if row["policy_version"] != POLICY_VERSION:
        raise JournalError("unsupported_version")
    snapshot = normalized_snapshot(
        row["entry"], row["current"], row["previous"], as_of=row["as_of"]
    )
    if row["sequence_id"] != snapshot["sequence_id"]:
        raise JournalError("identity_conflict")
    try:
        result = evaluation.evaluate(
            snapshot["entry"], snapshot["current"], snapshot["previous"], as_of=snapshot["as_of"]
        )
    except WatchlistError as error:
        raise JournalError(error.category) from None
    return snapshot, result


def evaluation_id(snapshot: object) -> str:
    normalized, _ = validate_snapshot(snapshot)
    return _identity("wje1_", EVALUATION_DOMAIN, normalized)


def signal_body(
    sequence: object, rule: object, from_id: object, to_id: object
) -> dict[str, object]:
    sequence = validate_id(sequence, "wjs1_")
    from_id, to_id = validate_id(from_id, "wje1_"), validate_id(to_id, "wje1_")
    if rule not in RULES or type(rule) is not str or from_id == to_id:
        raise JournalError("invalid_field")
    return {
        "version": 1,
        "kind": SIGNAL_KIND,
        "mode": SIGNAL_MODE,
        "sequence_id": sequence,
        "rule": rule,
        "from_evaluation_id": from_id,
        "to_evaluation_id": to_id,
    }


def signal_id(value: object) -> str:
    row = _object(value, _SIGNAL_FIELDS)
    expected = signal_body(
        row["sequence_id"], row["rule"], row["from_evaluation_id"], row["to_evaluation_id"]
    )
    if canonical(row) != canonical(expected):
        raise JournalError("invalid_field")
    return _identity("wsig1_", SIGNAL_DOMAIN, expected)
