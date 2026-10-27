"""Pure exact v1 demonstration plaintext; no filesystem, clock or transport."""

from __future__ import annotations

import json
import unicodedata
from typing import cast

from .errors import OutboxError
from .models import MAX_MESSAGE_BYTES


def _safe(value: object) -> str:
    text = str(value)
    result = []
    for char in text:
        if not char.isprintable() or unicodedata.category(char).startswith("C"):
            result.append(json.dumps(char, ensure_ascii=True)[1:-1])
        elif char == "\\":
            result.append("\\\\")
        else:
            result.append(char)
    return "".join(result)


def _money(value: object) -> str:
    return "unknown" if value is None else str(value)


def _total(sample: dict[str, object]) -> str:
    unit, shipping = sample["unit_price_minor"], sample["shipping_minor"]
    return (
        "unknown"
        if unit is None or shipping is None
        else str(cast(int, unit) + cast(int, shipping))
    )


def _render_normalized(intent: dict[str, object], evidence: dict[str, object]) -> str:
    """Render only normalized values retained privately within this operation."""
    snapshots = []
    rules = []
    for name in ("predecessor", "current"):
        point = cast(dict[str, object], evidence[name])
        snapshots.append(cast(dict[str, object], point["snapshot"]))
        result = cast(dict[str, object], point["evaluation_result"])
        rules.append(
            next(
                row
                for row in cast(list[dict[str, object]], result["rules"])
                if row["rule"] == intent["rule"]
            )
        )
    before, after = snapshots
    old_sample, sample = (cast(dict[str, object], snap["current"]) for snap in snapshots)
    old_previous = cast(dict[str, object] | None, before["previous"])
    previous = cast(dict[str, object], after["previous"])
    fields: list[tuple[str, object]] = [
        ("cmt_id", intent["cmt_id"]),
        ("watch_id", intent["watch_id"]),
        ("historical_revision", intent["revision"]),
        ("rule", intent["rule"]),
        ("signal_id", intent["signal_id"]),
        ("sequence_id", intent["sequence_id"]),
        ("from_evaluation_id", intent["from_evaluation_id"]),
        ("to_evaluation_id", intent["to_evaluation_id"]),
        ("predecessor_current_observed_at", old_sample["observed_at"]),
        (
            "predecessor_previous_observed_at",
            "none" if old_previous is None else old_previous["observed_at"],
        ),
        ("predecessor_as_of", before["as_of"]),
        ("current_current_observed_at", sample["observed_at"]),
        ("current_previous_observed_at", previous["observed_at"]),
        ("current_as_of", after["as_of"]),
        ("predecessor_rule_result", rules[0]["result"]),
        ("predecessor_rule_reason", rules[0]["reason"]),
        ("current_rule_result", rules[1]["result"]),
        ("current_rule_reason", rules[1]["reason"]),
    ]
    lines = [
        "SYNTHETIC — DEMONSTRATION ONLY",
        "Not a real offer or commercial notification.",
        "Historical Watchlist simulation; not current notification authorization.",
    ]
    lines.extend(f"{key}: {_safe(value)}" for key, value in fields)
    if intent["rule"] == "price":
        entry = cast(dict[str, object], after["entry"])
        lines.extend(
            [
                "Synthetic price rule entered MATCH.",
                "currency: EUR",
                f"target_price_minor: {_safe(entry['target_price_minor'])}",
            ]
        )
        for name, source in (("predecessor", old_sample), ("current", sample)):
            lines.extend(
                [
                    f"{name}_unit_price_minor: {_money(source['unit_price_minor'])}",
                    f"{name}_shipping_minor: {_money(source['shipping_minor'])}",
                    f"{name}_effective_cost_minor: {_total(source)}",
                ]
            )
    else:
        lines.append("Synthetic restock rule entered MATCH; no real shop availability is asserted.")
        lines.extend(
            f"{key}: {_safe(value)}"
            for key, value in [
                (
                    "predecessor_previous_stock",
                    "none" if old_previous is None else old_previous["stock"],
                ),
                ("predecessor_current_stock", old_sample["stock"]),
                ("current_previous_stock", previous["stock"]),
                ("current_current_stock", sample["stock"]),
            ]
        )
    message = "\n".join(lines)
    if len(message.encode("utf-8")) > MAX_MESSAGE_BYTES:
        raise OutboxError("input_limit")
    return message


def render(intent: object, evidence: object) -> str:
    """Reconstruct evidence and intent before rendering caller-provided data."""
    from . import policy

    bundle = policy.validate_evidence(evidence)
    expected = policy._intent(bundle)
    if policy.canonical(intent) != policy.canonical(expected):
        raise OutboxError("invalid_transition")
    return _render_normalized(expected, bundle)
