"""Deterministic synthetic-only rules, without storage, transport or implicit clock."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import cast

from .errors import WatchlistError
from .models import MAX_TOTAL, POLICY_VERSION, RuleStatus
from .validation import digest, parse_entry, parse_sample, timestamp


def _time(value: object) -> datetime:
    return datetime.fromisoformat(cast(str, value))


def _rule(name: str, result: RuleStatus, reason: str) -> dict[str, object]:
    return {"rule": name, "result": result, "reason": reason}


def _price(entry: dict[str, object], current: dict[str, object], fresh: bool) -> dict[str, object]:
    if not fresh:
        return _rule("price", "INDETERMINATE", "current_stale")
    if current["stock"] == "OUT_OF_STOCK":
        return _rule("price", "NO_MATCH", "current_out_of_stock")
    if current["stock"] == "UNKNOWN":
        return _rule("price", "INDETERMINATE", "current_stock_unknown")
    unit, shipping = current["unit_price_minor"], current["shipping_minor"]
    if unit is None or shipping is None:
        return _rule("price", "INDETERMINATE", "price_unknown")
    # Individual fields are bounded to 1e9. Python exact integers preserve their
    # checked sum; the explicit total cap is 2e9, with no float/SQL conversion.
    total = cast(int, unit) + cast(int, shipping)
    if total > MAX_TOTAL:
        raise WatchlistError("invalid_field")
    matched = total <= cast(int, entry["target_price_minor"])
    return _rule(
        "price",
        "MATCH" if matched else "NO_MATCH",
        "at_or_below_target" if matched else "above_target",
    )


def _restock(
    current: dict[str, object], previous: dict[str, object] | None, fresh: bool, prior_fresh: bool
) -> dict[str, object]:
    if not fresh:
        return _rule("restock", "INDETERMINATE", "current_stale")
    if current["stock"] == "OUT_OF_STOCK":
        return _rule("restock", "NO_MATCH", "current_out_of_stock")
    if current["stock"] == "UNKNOWN":
        return _rule("restock", "INDETERMINATE", "current_stock_unknown")
    if previous is None:
        return _rule("restock", "INDETERMINATE", "previous_missing")
    if not prior_fresh:
        return _rule("restock", "INDETERMINATE", "previous_stale")
    if previous["stock"] == "UNKNOWN":
        return _rule("restock", "INDETERMINATE", "previous_stock_unknown")
    if previous["stock"] == "OUT_OF_STOCK":
        return _rule("restock", "MATCH", "restocked")
    return _rule("restock", "NO_MATCH", "already_available")


def evaluate(
    entry: object, current: object, previous: object = None, *, as_of: object
) -> dict[str, object]:
    """Revalidate every input before a disabled entry can produce SKIPPED."""
    watch = parse_entry(entry)
    now = timestamp(as_of)
    sample = parse_sample(current)
    prior = None if previous is None else parse_sample(previous)
    observed, clock = _time(sample["observed_at"]), _time(now)
    if sample["cmt_id"] != watch["cmt_id"]:
        raise WatchlistError("incompatible_context")
    if observed > clock:
        raise WatchlistError("future_sample")
    if prior is not None:
        if prior["sample_id"] == sample["sample_id"]:
            raise WatchlistError("invalid_chronology")
        if prior["cmt_id"] != sample["cmt_id"] or prior["series_key"] != sample["series_key"]:
            raise WatchlistError("incompatible_context")
        if _time(prior["observed_at"]) > clock:
            raise WatchlistError("future_sample")
        if _time(prior["observed_at"]) >= observed:
            raise WatchlistError("invalid_chronology")
    result: dict[str, object] = {
        "version": 1,
        "policy_version": POLICY_VERSION,
        "watch_id": watch["watch_id"],
        "revision": watch["revision"],
        "cmt_id": watch["cmt_id"],
        "as_of": now,
        "current_sample": {"sample_id": sample["sample_id"], "digest": digest(sample)},
        "previous_sample": None
        if prior is None
        else {"sample_id": prior["sample_id"], "digest": digest(prior)},
    }
    rules: list[dict[str, object]] = []
    if not watch["enabled"]:
        result.update({"result": "SKIPPED", "rules": rules, "reason": "disabled"})
        return result
    age = cast(int, watch["max_age_seconds"])
    fresh = timedelta(0) <= clock - observed <= timedelta(seconds=age)
    prior_fresh = prior is not None and timedelta(0) <= clock - _time(
        prior["observed_at"]
    ) <= timedelta(seconds=age)
    if watch["target_price_minor"] is not None:
        rules.append(_price(watch, sample, fresh))
    if watch["restock_enabled"]:
        rules.append(_restock(sample, prior, fresh, prior_fresh))
    statuses = {rule["result"] for rule in rules}
    aggregate = (
        "MATCH"
        if "MATCH" in statuses
        else "INDETERMINATE"
        if "INDETERMINATE" in statuses
        else "NO_MATCH"
    )
    result.update({"result": aggregate, "rules": rules})
    return result
