"""Pure explicit-time sequence continuity and independently derived rule signals."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import cast

from .errors import JournalError
from .identity import canonical, evaluation_id, signal_body, signal_id, validate_snapshot


def _time(value: object) -> datetime:
    return datetime.fromisoformat(cast(str, value))


def check_append(previous: object, current: object) -> None:
    """Check the operator-selected predecessor; never fill or select evidence."""
    prior, _ = validate_snapshot(previous)
    new, _ = validate_snapshot(current)
    if prior["sequence_id"] != new["sequence_id"]:
        raise JournalError("incompatible_context")
    if canonical(prior["entry"]) != canonical(new["entry"]):
        raise JournalError("identity_conflict")
    old_sample = cast(dict[str, object], prior["current"])
    new_sample = cast(dict[str, object], new["current"])
    if (
        new_sample["sample_id"] == old_sample["sample_id"]
        or _time(new_sample["observed_at"]) <= _time(old_sample["observed_at"])
        or _time(new["as_of"]) < _time(prior["as_of"])
    ):
        raise JournalError("invalid_chronology")
    if canonical(new["previous"]) != canonical(old_sample):
        raise JournalError("replay_conflict")


def derive_signals(previous: object, current: object) -> list[dict[str, object]]:
    """Recalculate both P5a verdicts, then fold individual fresh transitions."""
    new, result = validate_snapshot(current)
    if previous is None:
        return []
    prior, old_result = validate_snapshot(previous)
    check_append(prior, new)
    entry = cast(dict[str, object], new["entry"])
    if not entry["enabled"]:
        return []
    clock, maximum = _time(new["as_of"]), timedelta(seconds=cast(int, entry["max_age_seconds"]))
    for snapshot in (prior, new):
        sample = cast(dict[str, object], snapshot["current"])
        if not timedelta(0) <= clock - _time(sample["observed_at"]) <= maximum:
            return []
    old_rules = {
        row["rule"]: row["result"] for row in cast(list[dict[str, object]], old_result["rules"])
    }
    signals: list[dict[str, object]] = []
    for row in cast(list[dict[str, object]], result["rules"]):
        if old_rules.get(row["rule"]) == "NO_MATCH" and row["result"] == "MATCH":
            body = signal_body(
                new["sequence_id"], row["rule"], evaluation_id(prior), evaluation_id(new)
            )
            signals.append({**body, "signal_id": signal_id(body)})
    return signals
