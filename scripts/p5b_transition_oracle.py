"""Standalone reference transition policy for P5b contract tests (not runtime).

It deliberately consumes only per-rule verdicts, separately from the P5a
application; production must re-evaluate P5a rather than trust such inputs.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta


def rules_entering_match(
    *,
    predecessor: Mapping[str, str] | None,
    current: Mapping[str, str],
    predecessor_observed_at: str | None,
    current_observed_at: str,
    as_of: str,
    max_age_seconds: int,
) -> tuple[str, ...]:
    """Return independent rule names in stable order for an eligible append."""
    if predecessor is None or predecessor_observed_at is None:
        return ()  # First evaluation is baseline even if MATCH.
    now = datetime.fromisoformat(as_of.replace("Z", "+00:00"))
    before = datetime.fromisoformat(predecessor_observed_at.replace("Z", "+00:00"))
    after = datetime.fromisoformat(current_observed_at.replace("Z", "+00:00"))
    if not (
        timedelta(0) <= now - before <= timedelta(seconds=max_age_seconds)
        and timedelta(0) <= now - after <= timedelta(seconds=max_age_seconds)
    ):
        return ()
    return tuple(
        name
        for name in ("price", "restock")
        if predecessor.get(name) == "NO_MATCH" and current.get(name) == "MATCH"
    )
