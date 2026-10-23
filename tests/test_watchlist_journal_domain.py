"""Author tests for semantic identities and the pure, explicit-time signal fold."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from card_market_tracker.watchlist_journal import identity, transitions
from card_market_tracker.watchlist_journal.errors import JournalError

VECTORS = json.loads((Path(__file__).parent / "fixtures/p5b_identity_vectors_v1.json").read_text())[
    "vectors"
]


def snapshot(name: str = "second", **changes: Any) -> dict[str, Any]:
    row = copy.deepcopy(VECTORS[name]["object"])
    row.update(changes)
    return row


def checkpoint(
    sample_id: str,
    hour: int,
    stock: str = "AVAILABLE",
    unit: int | None = 900,
    *,
    previous: dict[str, Any] | None = None,
    entry: dict[str, Any] | None = None,
    as_of: str | None = None,
) -> dict[str, Any]:
    sample = {
        **snapshot()["current"],
        "sample_id": sample_id,
        "observed_at": f"2026-10-23T{hour:02}:00:00Z",
        "stock": stock,
        "unit_price_minor": unit,
    }
    return identity.normalized_snapshot(
        entry or snapshot()["entry"], sample, previous, as_of=as_of or sample["observed_at"]
    )


def test_golden_preimage_bytes_and_independent_hashes() -> None:
    baseline, second = snapshot("baseline"), snapshot()
    assert identity.sequence_id(second["entry"], second["current"]) == VECTORS["sequence"]["id"]
    for name in ("baseline", "second"):
        vector = VECTORS[name]
        assert identity.evaluation_id(vector["object"]) == vector["id"]
        encoded = (
            vector["domain"].encode("ascii")
            + b"\x00"
            + json.dumps(
                vector["object"],
                sort_keys=True,
                ensure_ascii=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        )
        assert encoded == vector["preimage_text"].encode("utf-8")
        assert identity.preimage(vector["domain"], vector["object"]) == encoded
        assert "wje1_" + hashlib.sha256(encoded).hexdigest() == vector["id"]
    signals = transitions.derive_signals(baseline, second)
    assert [signal["signal_id"] for signal in signals] == [
        VECTORS["signal_price"]["id"],
        VECTORS["signal_restock"]["id"],
    ]
    for signal in signals:
        body = {key: value for key, value in signal.items() if key != "signal_id"}
        assert body == VECTORS["signal_" + signal["rule"]]["object"]
        assert identity.signal_id(body) == signal["signal_id"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("priority", "low"),
        ("enabled", False),
        ("target_price_minor", 999),
        ("restock_enabled", False),
        ("max_age_seconds", 80000),
        ("revision", 2),
    ],
)
def test_every_config_field_commits_evaluation_identity(field: str, value: Any) -> None:
    row = snapshot()
    row["entry"][field] = value
    normalized = identity.normalized_snapshot(
        row["entry"], row["current"], row["previous"], as_of=row["as_of"]
    )
    assert identity.evaluation_id(normalized) != VECTORS["second"]["id"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("sample_id", "another"),
        ("series_key", "another-series"),
        ("observed_at", "2026-10-23T11:59:59Z"),
        ("unit_price_minor", 901),
        ("shipping_minor", 0),
        ("stock", "UNKNOWN"),
    ],
)
def test_every_current_semantic_field_commits_identity(field: str, value: Any) -> None:
    row = snapshot()
    row["current"][field] = value
    if field == "series_key":
        row["previous"][field] = value
    normalized = identity.normalized_snapshot(
        row["entry"], row["current"], row["previous"], as_of=row["as_of"]
    )
    assert identity.evaluation_id(normalized) != VECTORS["second"]["id"]


def test_previous_as_of_and_normalized_offsets_commit_exact_semantics() -> None:
    row = snapshot()
    row["current"]["observed_at"] = "2026-10-23T14:00:00+02:00"
    row["as_of"] = "2026-10-23T13:00:00+01:00"
    assert identity.evaluation_id(row) == VECTORS["second"]["id"]
    row["previous"]["shipping_minor"] = 0
    assert identity.evaluation_id(row) != VECTORS["second"]["id"]
    row = snapshot(as_of="2026-10-23T12:00:01Z")
    assert identity.evaluation_id(row) != VECTORS["second"]["id"]


def test_initial_match_with_external_previous_is_signal_free() -> None:
    _, result = identity.validate_snapshot(snapshot())
    assert result["result"] == "MATCH"
    assert transitions.derive_signals(None, snapshot()) == []


def test_persistent_match_and_two_episodes_each_rule() -> None:
    points = [snapshot("baseline"), snapshot()]
    for sample_id, hour, stock in [
        ("same-match", 13, "AVAILABLE"),
        ("down", 14, "OUT_OF_STOCK"),
        ("up", 15, "AVAILABLE"),
    ]:
        points.append(checkpoint(sample_id, hour, stock, previous=points[-1]["current"]))
    assert [
        [signal["rule"] for signal in transitions.derive_signals(prior, new)]
        for prior, new in zip(points, points[1:], strict=False)
    ] == [
        ["price", "restock"],
        [],
        [],
        ["price", "restock"],
    ]


def test_per_rule_transition_even_when_aggregate_was_already_match() -> None:
    prior = checkpoint("above-restocked", 12, unit=1500, previous=snapshot("baseline")["current"])
    current = checkpoint("price-enters", 13, previous=prior["current"])
    assert identity.validate_snapshot(prior)[1]["result"] == "MATCH"
    assert identity.validate_snapshot(current)[1]["result"] == "MATCH"
    assert [row["rule"] for row in transitions.derive_signals(prior, current)] == ["price"]


@pytest.mark.parametrize(
    "prior_stock,prior_unit,prior_shipping",
    [
        ("UNKNOWN", 900, 100),
        ("AVAILABLE", None, 100),
        ("AVAILABLE", 900, None),
    ],
)
def test_indeterminate_price_never_enters_match(
    prior_stock: str, prior_unit: Any, prior_shipping: Any
) -> None:
    sample = snapshot("baseline")["current"]
    sample.update(stock=prior_stock, unit_price_minor=prior_unit, shipping_minor=prior_shipping)
    prior = identity.normalized_snapshot(snapshot()["entry"], sample, as_of=sample["observed_at"])
    current = checkpoint("known", 12, previous=sample)
    assert transitions.derive_signals(prior, current) == []


@pytest.mark.parametrize("seconds,expected", [(3600, ["price", "restock"]), (3601, [])])
def test_prior_freshness_uses_new_clock_and_inclusive_boundary(
    seconds: int, expected: list[str]
) -> None:
    entry = {**snapshot()["entry"], "max_age_seconds": 3600}
    baseline = identity.normalized_snapshot(
        entry, snapshot("baseline")["current"], as_of="2026-10-23T11:00:00Z"
    )
    current = checkpoint(
        "edge",
        12,
        previous=baseline["current"],
        entry=entry,
        as_of=f"2026-10-23T12:00:{seconds - 3600:02}Z",
    )
    assert [row["rule"] for row in transitions.derive_signals(baseline, current)] == expected


def test_current_stale_and_disabled_produce_no_signals_but_validate() -> None:
    baseline = snapshot("baseline")
    current = snapshot(as_of="2026-10-24T12:00:01Z")
    assert transitions.derive_signals(baseline, current) == []
    entry = {**baseline["entry"], "enabled": False}
    prior = identity.normalized_snapshot(entry, baseline["current"], as_of=baseline["as_of"])
    row = snapshot()
    new = identity.normalized_snapshot(entry, row["current"], row["previous"], as_of=row["as_of"])
    assert identity.validate_snapshot(new)[1]["result"] == "SKIPPED"
    assert transitions.derive_signals(prior, new) == []
    new["current"]["unit_price_minor"] = True
    with pytest.raises(JournalError, match="invalid_field"):
        transitions.derive_signals(prior, new)


@pytest.mark.parametrize(
    "change,category",
    [
        ("previous_missing", "replay_conflict"),
        ("previous_content", "replay_conflict"),
        ("observed_equal", "invalid_chronology"),
        ("clock_backwards", "invalid_chronology"),
        ("revision", "incompatible_context"),
        ("series", "incompatible_context"),
        ("entry", "identity_conflict"),
    ],
)
def test_append_rejects_wrong_explicit_predecessor_time_and_context(
    change: str, category: str
) -> None:
    prior, new = snapshot("baseline"), snapshot()
    if change == "previous_missing":
        new["previous"] = None
    elif change == "previous_content":
        new["previous"]["shipping_minor"] = 0
    elif change == "observed_equal":
        new["current"]["observed_at"] = prior["current"]["observed_at"]
        new["previous"] = None
    elif change == "clock_backwards":
        prior["as_of"] = "2026-10-23T12:00:01Z"
    elif change == "revision":
        new["entry"]["revision"] = 2
    elif change == "series":
        new["current"]["series_key"] = new["previous"]["series_key"] = "another-series"
    elif change == "entry":
        new["entry"]["priority"] = "low"
    if change in ("revision", "series"):
        new = identity.normalized_snapshot(
            new["entry"], new["current"], new["previous"], as_of=new["as_of"]
        )
    with pytest.raises(JournalError, match=category):
        transitions.derive_signals(prior, new)


@pytest.mark.parametrize(
    "change", ["result", "verified", "version_bool", "policy", "sequence", "dataclass"]
)
def test_snapshots_have_no_authority_flags_or_caller_verdicts(change: str) -> None:
    row: Any = snapshot()
    if change in ("result", "verified"):
        row[change] = True
    elif change == "version_bool":
        row["version"] = True
    elif change == "policy":
        row["policy_version"] = "future"
    elif change == "sequence":
        row["sequence_id"] = "wjs1_" + "0" * 64
    else:
        from types import SimpleNamespace

        row = SimpleNamespace(**row)
    with pytest.raises(JournalError):
        identity.validate_snapshot(row)


@pytest.mark.parametrize("change", ["version", "kind", "mode", "rule", "extra", "same", "bad_id"])
def test_signal_identity_rejects_malformed_semantics(change: str) -> None:
    body = copy.deepcopy(VECTORS["signal_price"]["object"])
    if change == "version":
        body["version"] = True
    elif change == "extra":
        body["sent"] = True
    elif change == "same":
        body["to_evaluation_id"] = body["from_evaluation_id"]
    elif change == "bad_id":
        body["sequence_id"] = "wjs1_" + "A" * 64
    else:
        body[change] = "invalid"
    with pytest.raises(JournalError):
        identity.signal_id(body)


def test_bounded_objects_and_redacted_error_categories() -> None:
    row = snapshot()
    row["entry"]["private"] = "x" * 1025
    with pytest.raises(JournalError, match="input_limit"):
        identity.validate_snapshot(row)
    assert str(JournalError("secret arbitrary detail")) == "invalid_field"
    assert JournalError("storage_io").exit_code == 1
    assert JournalError("identity_conflict").exit_code == 2
