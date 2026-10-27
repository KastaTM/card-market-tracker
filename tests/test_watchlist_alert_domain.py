"""Author tests for original-rule evidence, exact identity and deterministic preview."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from card_market_tracker.watchlist_alerts import policy, render
from card_market_tracker.watchlist_alerts.errors import OutboxError
from card_market_tracker.watchlist_journal import identity, transitions

VECTORS = json.loads((Path(__file__).parent / "fixtures/p5b_identity_vectors_v1.json").read_text())[
    "vectors"
]


def evidence(rule: str = "price") -> dict[str, Any]:
    points = []
    for ordinal, name in enumerate(("baseline", "second"), 1):
        snap, result = identity.validate_snapshot(copy.deepcopy(VECTORS[name]["object"]))
        points.append(
            {
                "evaluation_id": identity.evaluation_id(snap),
                "sequence_id": snap["sequence_id"],
                "ordinal": ordinal,
                "predecessor_evaluation_id": None if ordinal == 1 else points[0]["evaluation_id"],
                "snapshot": snap,
                "evaluation_result": result,
            }
        )
    signal = next(
        item
        for item in transitions.derive_signals(points[0]["snapshot"], points[1]["snapshot"])
        if item["rule"] == rule
    )
    return {"version": 1, "signal": signal, "predecessor": points[0], "current": points[1]}


@pytest.mark.parametrize("rule", ["price", "restock"])
def test_full_evidence_derives_frozen_identity_and_renderer(rule: str) -> None:
    bundle = evidence(rule)
    before = copy.deepcopy(bundle)
    row = policy.prepare(bundle, "local-preview")
    expected = (
        "walt1_"
        + hashlib.sha256(
            b"CMT_WATCHLIST_ALERT_V1\x00"
            + json.dumps(
                {
                    "identity_version": 1,
                    "destination_key": "local-preview",
                    "signal_id": bundle["signal"]["signal_id"],
                },
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            ).encode()
        ).hexdigest()
    )
    assert row["alert_id"] == expected
    assert len(row) == 14 and row["version"] == 1
    assert row["channel"] == "offline_preview" and row["state"] == "pending"
    assert row["message_text"].startswith(
        "SYNTHETIC — DEMONSTRATION ONLY\nNot a real offer or commercial notification.\n"
    )
    assert not row["message_text"].endswith("\n")
    assert row["message_sha256"] == hashlib.sha256(row["message_text"].encode()).hexdigest()
    assert row["evidence_sha256"] == hashlib.sha256(row["evidence_json"].encode()).hexdigest()
    assert row["message_text"] == render.render(json.loads(row["intent_json"]), bundle)
    assert bundle == before
    assert policy.validate_prepared(row) == row


@pytest.mark.parametrize(
    "mutation",
    [
        "result",
        "ordinal",
        "previous",
        "signal",
        "extra",
        "bool_version",
        "predecessor_link",
        "entry",
        "stale",
    ],
)
def test_coherently_rehashed_bad_evidence_is_not_authority(mutation: str) -> None:
    bundle = evidence()
    if mutation == "result":
        bundle["current"]["evaluation_result"]["rules"][0]["reason"] = "forged"
    elif mutation == "ordinal":
        bundle["current"]["ordinal"] = 3
    elif mutation == "previous":
        bundle["current"]["snapshot"]["previous"]["stock"] = "UNKNOWN"
    elif mutation == "signal":
        bundle["signal"]["signal_id"] = "wsig1_" + "0" * 64
    elif mutation == "extra":
        bundle["caller_verified"] = True
    elif mutation == "bool_version":
        bundle["version"] = True
    elif mutation == "predecessor_link":
        bundle["predecessor"]["predecessor_evaluation_id"] = bundle["current"]["evaluation_id"]
    elif mutation == "entry":
        bundle["predecessor"]["snapshot"]["entry"]["priority"] = "low"
    else:
        bundle["current"]["snapshot"]["as_of"] = "2030-01-01T00:00:00Z"
    with pytest.raises(OutboxError):
        policy.prepare(bundle, "local-preview")


@pytest.mark.parametrize("alias", ["", "A", "x/y", "a.b", "a\n", "a" * 65, True, None])
def test_alias_is_local_ascii_only(alias: object) -> None:
    with pytest.raises(OutboxError, match="invalid_field"):
        policy.prepare(evidence(), alias)


def test_renderer_requires_matching_intent_and_preserves_money_unknown() -> None:
    bundle = evidence()
    # A valid out-of-stock predecessor can have unknown monetary components.
    bundle["predecessor"]["snapshot"]["current"]["unit_price_minor"] = None
    bundle["predecessor"]["snapshot"]["current"]["shipping_minor"] = None
    bundle["current"]["snapshot"]["previous"] = copy.deepcopy(
        bundle["predecessor"]["snapshot"]["current"]
    )
    for point in (bundle["predecessor"], bundle["current"]):
        snap, result = identity.validate_snapshot(point["snapshot"])
        point.update(
            snapshot=snap, evaluation_result=result, evaluation_id=identity.evaluation_id(snap)
        )
    bundle["current"]["predecessor_evaluation_id"] = bundle["predecessor"]["evaluation_id"]
    bundle["signal"] = transitions.derive_signals(
        bundle["predecessor"]["snapshot"], bundle["current"]["snapshot"]
    )[0]
    row = policy.prepare(bundle, "local-preview")
    assert "predecessor_unit_price_minor: unknown\n" in row["message_text"]
    assert "predecessor_shipping_minor: unknown\n" in row["message_text"]
    assert "predecessor_effective_cost_minor: unknown\n" in row["message_text"]
    intent = json.loads(row["intent_json"])
    intent["revision"] = 2
    with pytest.raises(OutboxError):
        render.render(intent, bundle)


def test_destination_changes_id_but_not_intrinsic_intent() -> None:
    left = policy.prepare(evidence(), "local-preview")
    right = policy.prepare(evidence(), "qa-preview")
    assert left["alert_id"] != right["alert_id"]
    assert left["intent_json"] == right["intent_json"]
    assert left["message_text"] == right["message_text"]


def test_receipt_document_bounds_are_distinct_from_semantic_scalars() -> None:
    row = policy.prepare(evidence(), "local-preview")
    assert len(row["evidence_json"]) > 1024
    assert len(row["message_text"]) > 1024
    assert policy.validate_prepared(row) == row
    changed = dict(row, message_text=row["message_text"] + "\nforged")
    with pytest.raises(OutboxError):
        policy.validate_prepared(changed)


@pytest.mark.parametrize("rule", ["price", "restock"])
def test_renderer_exact_complete_golden_lines(rule: str) -> None:
    bundle = evidence(rule)
    row = policy.prepare(bundle, "local-preview")
    expected = [
        "SYNTHETIC — DEMONSTRATION ONLY",
        "Not a real offer or commercial notification.",
        "Historical Watchlist simulation; not current notification authorization.",
        "cmt_id: 541b9d13-9669-4973-8413-397bea14c045",
        "watch_id: wlt1_3fd89463c0b769769b7ace4993c3baee6e4e0cbead43856fdb50d42db4787cc0",
        "historical_revision: 1",
        f"rule: {rule}",
        f"signal_id: {VECTORS['signal_' + rule]['id']}",
        f"sequence_id: {VECTORS['sequence']['id']}",
        f"from_evaluation_id: {VECTORS['baseline']['id']}",
        f"to_evaluation_id: {VECTORS['second']['id']}",
        "predecessor_current_observed_at: 2026-10-23T11:00:00Z",
        "predecessor_previous_observed_at: none",
        "predecessor_as_of: 2026-10-23T11:00:00Z",
        "current_current_observed_at: 2026-10-23T12:00:00Z",
        "current_previous_observed_at: 2026-10-23T11:00:00Z",
        "current_as_of: 2026-10-23T12:00:00Z",
        "predecessor_rule_result: NO_MATCH",
        "predecessor_rule_reason: current_out_of_stock",
        "current_rule_result: MATCH",
        "current_rule_reason: " + ("at_or_below_target" if rule == "price" else "restocked"),
    ]
    if rule == "price":
        expected += [
            "Synthetic price rule entered MATCH.",
            "currency: EUR",
            "target_price_minor: 1000",
            "predecessor_unit_price_minor: unknown",
            "predecessor_shipping_minor: unknown",
            "predecessor_effective_cost_minor: unknown",
            "current_unit_price_minor: 900",
            "current_shipping_minor: 100",
            "current_effective_cost_minor: 1000",
        ]
    else:
        expected += [
            "Synthetic restock rule entered MATCH; no real shop availability is asserted.",
            "predecessor_previous_stock: none",
            "predecessor_current_stock: OUT_OF_STOCK",
            "current_previous_stock: OUT_OF_STOCK",
            "current_current_stock: AVAILABLE",
        ]
    assert row["message_text"].encode("utf-8") == "\n".join(expected).encode("utf-8")


def _rederive(bundle: dict[str, Any], rule: str = "price") -> dict[str, Any]:
    for point in (bundle["predecessor"], bundle["current"]):
        snap, result = identity.validate_snapshot(point["snapshot"])
        point.update(
            snapshot=snap, evaluation_result=result, evaluation_id=identity.evaluation_id(snap)
        )
    bundle["current"]["predecessor_evaluation_id"] = bundle["predecessor"]["evaluation_id"]
    bundle["signal"] = next(
        signal
        for signal in transitions.derive_signals(
            bundle["predecessor"]["snapshot"], bundle["current"]["snapshot"]
        )
        if signal["rule"] == rule
    )
    return bundle


@pytest.mark.parametrize(
    "unit,shipping,target", [(1000, 0, 1000), (1_000_000_000, 0, 1_000_000_000)]
)
def test_known_free_shipping_and_exact_maximum_price(unit: int, shipping: int, target: int) -> None:
    bundle = evidence()
    for point in ("predecessor", "current"):
        bundle[point]["snapshot"]["entry"]["target_price_minor"] = target
    bundle["current"]["snapshot"]["current"].update(unit_price_minor=unit, shipping_minor=shipping)
    row = policy.prepare(_rederive(bundle), "local-preview")
    assert f"current_unit_price_minor: {unit}\n" in row["message_text"]
    assert "current_shipping_minor: 0\n" in row["message_text"]
    assert row["message_text"].endswith(f"current_effective_cost_minor: {unit}")


@pytest.mark.parametrize("unit,shipping", [(None, 0), (500, None)])
def test_partial_unknown_predecessor_cost_is_never_invented(
    unit: int | None, shipping: int | None
) -> None:
    bundle = evidence()
    bundle["predecessor"]["snapshot"]["current"].update(
        unit_price_minor=unit, shipping_minor=shipping
    )
    bundle["current"]["snapshot"]["previous"] = copy.deepcopy(
        bundle["predecessor"]["snapshot"]["current"]
    )
    message = policy.prepare(_rederive(bundle), "local-preview")["message_text"]
    assert "predecessor_effective_cost_minor: unknown\n" in message


@pytest.mark.parametrize("value", [True, 0, -1, 1_000_000_001, 1.5, "900"])
def test_money_invalid_types_and_range_rejected_before_id_comparison(value: object) -> None:
    bundle = evidence()
    bundle["current"]["snapshot"]["current"]["unit_price_minor"] = value
    with pytest.raises(OutboxError, match="invalid_field"):
        policy.prepare(bundle, "local-preview")


@pytest.mark.parametrize(
    "text,expected",
    [
        ("plain", "plain"),
        ("a\\b", "a\\\\b"),
        ("x\ny\r\t", "x\\ny\\r\\t"),
        ("\x1b[31m", "\\u001b[31m"),
        ("x\u202ey\u2066z\u2069", "x\\u202ey\\u2066z\\u2069"),
        ("a\u2028b\u2029", "a\\u2028b\\u2029"),
        ("\ud800", "\\ud800"),
    ],
)
def test_renderer_defense_escapes_controls_backslashes_bidi_and_separators(
    text: str, expected: str
) -> None:
    # Narrow public semantic fields reject these values; exercise the defense
    # independently without turning arbitrary text into admissible evidence.
    assert render._safe(text) == expected


def test_renderer_internal_oversize_guard_rejects_instead_of_truncating() -> None:
    bundle = policy.validate_evidence(evidence())
    intent = policy.intent_from_evidence(bundle)
    intent["cmt_id"] = "x" * 4096
    with pytest.raises(OutboxError, match="input_limit"):
        render._render_normalized(intent, bundle)
    with pytest.raises(OutboxError, match="input_limit"):
        render.render(intent, bundle)


@pytest.mark.parametrize(
    "raw,category",
    [
        (None, "invalid_field"),
        ("[", "invalid_json"),
        ('{"version":1,"version":1}', "duplicate_key"),
        ('{"value":NaN}', "invalid_json"),
        ("[" * 17 + "0" + "]" * 17, "input_limit"),
        ("é", "invalid_json"),
        ("x" * 262145, "input_limit"),
        ("{}", "invalid_json"),
    ],
    ids=["type", "syntax", "duplicate", "nonfinite", "depth", "unicode", "oversize", "spacing"],
)
def test_prepared_document_decode_limits_and_noncanonical_bytes(raw: object, category: str) -> None:
    row = policy.prepare(evidence(), "local-preview")
    row["evidence_json"] = raw
    if raw == "{}":
        row["evidence_json"] = "{ }"
    with pytest.raises(OutboxError, match=category):
        policy.validate_prepared(row)
