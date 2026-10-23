"""Author tests of identity, strict inputs and pure synthetic rule behavior."""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from card_market_tracker.catalog.manifest import parse_manifest
from card_market_tracker.watchlist import evaluation
from card_market_tracker.watchlist import validation as v
from card_market_tracker.watchlist.errors import WatchlistError

TARGET = "541b9d13-9669-4973-8413-397bea14c045"
SEALED = "79b79554-edd4-4bdc-8120-859974c3df62"
NOW = "2026-01-02T12:00:00Z"


@pytest.fixture
def manifest() -> dict[str, Any]:
    return json.loads((Path(__file__).parent / "fixtures/synthetic_manifest.json").read_text())


@pytest.fixture
def entry(manifest: dict[str, Any]) -> dict[str, Any]:
    projection = v.identity_projection(manifest, TARGET)
    return {
        "version": 1,
        "cmt_id": TARGET,
        "watch_id": v.make_watch_id(TARGET),
        "canonical_identity": projection,
        "identity_digest": v.digest(projection),
        "revision": 1,
        **v.parse_config({"target_price_minor": 1000, "restock_enabled": True}),
    }


def sample(**changes: Any) -> dict[str, Any]:
    return {
        "version": 1,
        "provenance": "synthetic",
        "sample_id": "s1",
        "cmt_id": TARGET,
        "series_key": "synthetic-series",
        "observed_at": NOW,
        "currency": "EUR",
        "unit_price_minor": 900,
        "shipping_minor": 100,
        "stock": "AVAILABLE",
        **changes,
    }


def prior(**changes: Any) -> dict[str, Any]:
    return sample(
        **{
            "sample_id": "s0",
            "observed_at": "2026-01-02T11:59:00Z",
            "stock": "OUT_OF_STOCK",
            **changes,
        }
    )


def run(entry: object, current: object, previous: object = None, **changes: Any) -> dict[str, Any]:
    return evaluation.evaluate(entry, current, previous, as_of=changes.get("as_of", NOW))


def test_identity_closure_and_hash(manifest: dict[str, Any]) -> None:
    projection = v.identity_projection(manifest, TARGET)
    assert projection["target"] == {
        "cmt_id": TARGET,
        "kind": "printing",
        "card_id": "70bf03c9-a465-4299-a4fc-adfb70de757d",
        "language": "es",
        "variant": "normal",
    }
    assert projection["parents"] == [
        {
            "cmt_id": "70bf03c9-a465-4299-a4fc-adfb70de757d",
            "kind": "card",
            "set_id": "f9743b79-20e3-4815-98d3-bb06f0c8195f",
            "card_number": "001",
        },
        {"cmt_id": "f9743b79-20e3-4815-98d3-bb06f0c8195f", "kind": "set"},
    ]
    assert (
        v.make_watch_id(TARGET)
        == "wlt1_" + hashlib.sha256(("CMT_WATCHLIST_V1\0" + TARGET).encode()).hexdigest()
    )
    manifest["entities"][0]["names"]["en"] = "A renamed localization"
    manifest["entities"][0]["release_date"] = "2026-01-01"
    manifest["bindings"] = []
    assert v.identity_projection(manifest, TARGET) == projection


def test_null_unknown_sealed_and_distinct_variants(manifest: dict[str, Any]) -> None:
    ids = [row["cmt_id"] for row in manifest["entities"] if row["kind"] == "printing"]
    assert len({v.digest(v.identity_projection(manifest, key)) for key in ids}) == len(ids)
    sealed = next(row for row in manifest["entities"] if row["cmt_id"] == SEALED)
    sealed.update({"set_id": None, "language": None, "sealed_type": "unknown"})
    manifest["bindings"] = []
    projection = v.identity_projection(manifest, SEALED)
    assert projection["parents"] == []
    assert projection["target"] == {
        "cmt_id": SEALED,
        "kind": "sealed",
        "set_id": None,
        "language": None,
        "sealed_type": "unknown",
    }
    printing = next(row for row in manifest["entities"] if row["cmt_id"] == TARGET)
    printing.update(language=None, variant="unknown")
    target = v.identity_projection(manifest, TARGET)["target"]
    assert target["language"] is None and target["variant"] == "unknown"


@pytest.mark.parametrize(
    "target",
    [
        "f9743b79-20e3-4815-98d3-bb06f0c8195f",
        "70bf03c9-a465-4299-a4fc-adfb70de757d",
        "11111111-1111-4111-8111-111111111111",
        "https://example.invalid",
        "synthetic-card-001",
    ],
)
def test_reject_non_sellable_targets(manifest: dict[str, Any], target: object) -> None:
    with pytest.raises(WatchlistError):
        v.identity_projection(manifest, target)


def test_full_manifest_and_forged_dataclass_rejected(manifest: dict[str, Any]) -> None:
    with pytest.raises(WatchlistError):
        v.identity_projection(parse_manifest(manifest), TARGET)
    manifest["entities"][0]["extra"] = True
    with pytest.raises(WatchlistError, match="invalid_shape"):
        v.identity_projection(manifest, TARGET)


@pytest.mark.parametrize(
    "change",
    [
        {"priority": "urgent"},
        {"enabled": 1},
        {"restock_enabled": 1},
        {"target_price_minor": True},
        {"target_price_minor": 0},
        {"target_price_minor": -1},
        {"target_price_minor": 1.0},
        {"target_price_minor": 1_000_000_001},
        {"max_age_seconds": 0},
        {"max_age_seconds": True},
        {"max_age_seconds": 604801},
        {"query": "SELECT 1"},
        {},
    ],
)
def test_bad_config(change: dict[str, Any]) -> None:
    with pytest.raises(WatchlistError):
        v.parse_config(change)


def test_config_defaults_and_bounds() -> None:
    assert v.parse_config({"restock_enabled": True}) == {
        "priority": "normal",
        "enabled": True,
        "target_price_minor": None,
        "restock_enabled": True,
        "max_age_seconds": 86400,
    }
    assert (
        v.parse_config({"target_price_minor": 1_000_000_000, "max_age_seconds": 604800})[
            "target_price_minor"
        ]
        == 1_000_000_000
    )


@pytest.mark.parametrize(
    "change",
    [
        {"version": True},
        {"provenance": "real"},
        {"currency": "USD"},
        {"unit_price_minor": 0},
        {"unit_price_minor": False},
        {"unit_price_minor": 1.5},
        {"unit_price_minor": 1_000_000_001},
        {"shipping_minor": -1},
        {"shipping_minor": True},
        {"shipping_minor": 1_000_000_001},
        {"sample_id": "https://bad.invalid"},
        {"series_key": "x" * 129},
        {"stock": "PREORDER"},
        {"url": "https://bad.invalid"},
        {"observed_at": "2026-01-02T12:00:00"},
    ],
)
def test_bad_samples(change: dict[str, Any]) -> None:
    with pytest.raises(WatchlistError):
        v.parse_sample(sample(**change))


@pytest.mark.parametrize(
    "value",
    [
        "2026-01-02",
        "2026-01-02 12:00:00Z",
        "2026-13-02T12:00:00Z",
        "0001-01-01T00:00:00+01:00",
        "2026-01-02T12:00:00+25:00",
        "2026-01-02T12:00:00+01:60",
        None,
    ],
)
def test_invalid_timestamp(value: object) -> None:
    with pytest.raises(WatchlistError, match="invalid_timestamp"):
        v.timestamp(value)


def test_offset_canonical_equivalence(entry: dict[str, Any]) -> None:
    assert run(
        entry, sample(observed_at="2026-01-02T13:00:00+01:00"), as_of="2026-01-02T07:00:00-05:00"
    ) == run(entry, sample())
    assert v.canonical({"z": "é", "a": 1}) == '{"a":1,"z":"\\u00e9"}'


@pytest.mark.parametrize(
    ("unit", "shipping", "expected"),
    [
        (899, 100, "MATCH"),
        (900, 100, "MATCH"),
        (901, 100, "NO_MATCH"),
        (1000, 0, "MATCH"),
        (1000, None, "INDETERMINATE"),
        (None, 0, "INDETERMINATE"),
        (1_000_000_000, 1_000_000_000, "NO_MATCH"),
    ],
)
def test_exact_money(
    entry: dict[str, Any], unit: int | None, shipping: int | None, expected: str
) -> None:
    entry["restock_enabled"] = False
    result = run(entry, sample(unit_price_minor=unit, shipping_minor=shipping))
    assert result["result"] == expected
    assert result["rules"][0]["result"] == expected


@pytest.mark.parametrize(
    ("current_stock", "previous_stock", "expected"),
    [
        ("OUT_OF_STOCK", "OUT_OF_STOCK", "NO_MATCH"),
        ("OUT_OF_STOCK", "AVAILABLE", "NO_MATCH"),
        ("OUT_OF_STOCK", "UNKNOWN", "NO_MATCH"),
        ("AVAILABLE", "OUT_OF_STOCK", "MATCH"),
        ("AVAILABLE", "AVAILABLE", "NO_MATCH"),
        ("AVAILABLE", "UNKNOWN", "INDETERMINATE"),
        ("UNKNOWN", "OUT_OF_STOCK", "INDETERMINATE"),
        ("UNKNOWN", "AVAILABLE", "INDETERMINATE"),
        ("UNKNOWN", "UNKNOWN", "INDETERMINATE"),
    ],
)
def test_complete_restock_stock_matrix(
    entry: dict[str, Any], current_stock: str, previous_stock: str, expected: str
) -> None:
    entry["target_price_minor"] = None
    assert (
        run(entry, sample(stock=current_stock), prior(stock=previous_stock))["result"] == expected
    )


@pytest.mark.parametrize(
    ("stock", "expected"),
    [("AVAILABLE", "INDETERMINATE"), ("OUT_OF_STOCK", "NO_MATCH"), ("UNKNOWN", "INDETERMINATE")],
)
def test_missing_previous(entry: dict[str, Any], stock: str, expected: str) -> None:
    entry["target_price_minor"] = None
    assert run(entry, sample(stock=stock))["result"] == expected


def test_freshness_inclusive_and_previous_only_when_needed(entry: dict[str, Any]) -> None:
    current_time = datetime(2026, 1, 2, 12, tzinfo=UTC)
    for delta, expected in [(0, "MATCH"), (86400, "MATCH"), (86400.000001, "INDETERMINATE")]:
        stamp = (current_time - timedelta(seconds=delta)).isoformat()
        entry["restock_enabled"] = False
        assert run(entry, sample(observed_at=stamp))["result"] == expected
    entry["restock_enabled"] = True
    entry["target_price_minor"] = None
    stale = prior(observed_at="2025-12-30T12:00:00Z")
    assert run(entry, sample(stock="OUT_OF_STOCK"), stale)["result"] == "NO_MATCH"
    assert run(entry, sample(), stale)["rules"][0]["reason"] == "previous_stale"
    assert (
        run(entry, sample(stock="OUT_OF_STOCK", observed_at="2025-12-30T12:00:00Z"))["result"]
        == "INDETERMINATE"
    )


@pytest.mark.parametrize("disabled", [False, True])
@pytest.mark.parametrize(
    ("current", "previous", "category"),
    [
        (sample(cmt_id=SEALED), None, "incompatible_context"),
        (sample(observed_at="2026-01-02T12:00:01Z"), None, "future_sample"),
        (sample(), prior(series_key="different"), "incompatible_context"),
        (sample(), prior(cmt_id=SEALED), "incompatible_context"),
        (sample(), prior(observed_at=NOW), "invalid_chronology"),
        (sample(), prior(sample_id="s1"), "invalid_chronology"),
        (sample(), prior(observed_at="2026-01-02T12:01:00Z"), "future_sample"),
    ],
)
def test_context_time_errors_even_disabled(
    entry: dict[str, Any], disabled: bool, current: object, previous: object, category: str
) -> None:
    entry["enabled"] = not disabled
    with pytest.raises(WatchlistError, match=category):
        run(entry, current, previous)


def test_or_disabled_determinism_and_nonmutation(entry: dict[str, Any]) -> None:
    original = copy.deepcopy(entry)
    assert run(entry, sample())["result"] == "MATCH"
    result = run(entry, sample(unit_price_minor=1100))
    assert result["result"] == "INDETERMINATE"
    assert [rule["result"] for rule in result["rules"]] == ["NO_MATCH", "INDETERMINATE"]
    assert run(entry, sample(unit_price_minor=1100), prior())["result"] == "MATCH"
    assert v.canonical(run(entry, sample(), prior())) == v.canonical(run(entry, sample(), prior()))
    assert entry == original
    entry["enabled"] = False
    assert run(entry, sample())["result"] == "SKIPPED"
    with pytest.raises(WatchlistError):
        run(entry, sample(unit_price_minor=True))


@pytest.mark.parametrize(
    "field", ["watch_id", "identity_digest", "canonical_identity", "revision", "enabled", "extra"]
)
def test_forged_entry_revalidated(entry: dict[str, Any], field: str) -> None:
    entry[field] = {"canonical_identity": {}, "revision": True, "enabled": 1}.get(field, "forged")
    with pytest.raises(WatchlistError):
        run(entry, sample())


def test_json_bounds_duplicate_keys_and_safe_errors(tmp_path: Path) -> None:
    path = tmp_path / "input.json"
    path.write_text('{"version":1,"version":1}')
    with pytest.raises(WatchlistError, match="duplicate_key"):
        v.read_json(path)
    for value in [{"x": "a" * 1025}, [0] * 20001, {"x": float("nan")}, object()]:
        with pytest.raises(WatchlistError):
            v.canonical(value)
    nested: Any = 0
    for _ in range(18):
        nested = [nested]
    with pytest.raises(WatchlistError, match="input_limit"):
        v.canonical(nested)
    with pytest.raises(WatchlistError, match="input_limit"):
        v.canonical(["x" * 1024] * 1100)
    error = WatchlistError("secret arbitrary content")
    assert str(error) == "invalid_field" and error.exit_code == 2
    assert WatchlistError("storage_io").exit_code == 1


@pytest.mark.parametrize("value", [True, 0, -1, 2_147_483_648, 1.0])
def test_revision_validation(value: object) -> None:
    with pytest.raises(WatchlistError):
        v.validate_revision(value)


def test_token_and_watch_validation() -> None:
    assert v.token("request_1:a-b.c") == "request_1:a-b.c"
    assert v.validate_revision(0, allow_zero=True) == 0
    assert v.watch_id(v.make_watch_id(TARGET)) == v.make_watch_id(TARGET)
    for token in ["", "x" * 129, "é", "a b", "https://example.invalid"]:
        with pytest.raises(WatchlistError):
            v.token(token)


@pytest.mark.parametrize(
    ("stock", "expected", "reason"),
    [
        ("AVAILABLE", "MATCH", "at_or_below_target"),
        ("OUT_OF_STOCK", "NO_MATCH", "current_out_of_stock"),
        ("UNKNOWN", "INDETERMINATE", "current_stock_unknown"),
    ],
)
def test_price_stock_matrix(entry: dict[str, Any], stock: str, expected: str, reason: str) -> None:
    entry["restock_enabled"] = False
    result = run(entry, sample(stock=stock))
    assert result["result"] == expected
    assert result["rules"][0]["reason"] == reason


def test_projection_and_entry_cannot_be_forged(entry: dict[str, Any]) -> None:
    original = copy.deepcopy(entry)
    mutations = [
        lambda row: row.update(version=True),
        lambda row: row["canonical_identity"].update(version=2),
        lambda row: row["canonical_identity"].update(parents={}),
        lambda row: row["canonical_identity"]["parents"].reverse(),
        lambda row: row["canonical_identity"]["target"].update(names={"en": "injected"}),
    ]
    for change in mutations:
        row = copy.deepcopy(original)
        change(row)
        row["identity_digest"] = v.digest(row["canonical_identity"])
        with pytest.raises(WatchlistError):
            v.parse_entry(row)


def test_json_input_read_failures(tmp_path: Path) -> None:
    path = tmp_path / "input.json"
    with pytest.raises(WatchlistError, match="input_io"):
        v.read_json(path)
    for raw, category in [
        (b'{"x":NaN}', "invalid_json"),
        (b"\xff", "invalid_json"),
        (b"x" * 1048577, "input_limit"),
    ]:
        path.write_bytes(raw)
        with pytest.raises(WatchlistError, match=category):
            v.read_json(path)
    with pytest.raises(WatchlistError, match="invalid_shape"):
        v.parse_config([])
