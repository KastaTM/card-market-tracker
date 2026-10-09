"""Synthetic contract tests; no provider response or network access is involved."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pytest

from card_market_tracker.catalog.adapters.tcgdex import translate_batch
from card_market_tracker.catalog.ingestion import Observation, RecordError
from card_market_tracker.catalog.validation import MAX_RECORDS, CatalogError, read_json

FIXTURES = Path(__file__).parent / "fixtures"


def batch(data: dict[str, Any], **wrapper: Any) -> dict[str, Any]:
    return {
        "version": 1,
        "provenance": "synthetic",
        "records": [{"kind": "card", "language": "es", "data": data, **wrapper}],
    }


def card() -> dict[str, Any]:
    return {
        "id": "synthetic-card-001",
        "name": "Carta sintética",
        "localId": "001",
        "set": {"id": "synthetic-set"},
    }


def test_synthetic_es_en_and_curated_variant_shape() -> None:
    result = translate_batch(read_json(FIXTURES / "synthetic_tcgdex_valid.json"))
    assert len(result) == 7
    assert all(isinstance(record, Observation) for record in result)
    observations = [record for record in result if isinstance(record, Observation)]
    assert observations[0].reference.external_id == observations[1].reference.external_id
    assert [row.reference.language for row in observations[:2]] == ["es", "en"]
    assert [row.reference.variant for row in observations[2:5]] == ["normal", "holo", "reverse"]
    assert observations[2].card_number == "001"
    assert observations[-1].card_number == "TG01"
    assert observations[0].release_date == "2025-01-01"
    assert all(row.provenance == "synthetic" for row in observations)
    assert translate_batch(read_json(FIXTURES / "synthetic_tcgdex_valid.json")) == result


@pytest.mark.parametrize(
    "flags",
    [{}, {"normal": True}, {"normal": False}, {"normal": True, "holo": True, "reverse": True}],
)
def test_availability_never_selects_observed_variant(flags: dict[str, bool]) -> None:
    data = card()
    data["variants"] = flags
    result = translate_batch(batch(data))
    assert isinstance(result[0], Observation)
    assert result[0].reference.variant == "unknown"


def test_unknown_metadata_and_null_language_remain_unknown() -> None:
    data = card()
    data["updated"] = None
    result = translate_batch(batch(data, language=None, variant=None))
    assert isinstance(result[0], Observation)
    assert result[0].reference.language is None
    assert result[0].reference.variant == "unknown"
    assert result[0].provider_updated_at is None
    assert result[0].captured_at is None


@pytest.mark.parametrize("field", ["id", "name", "localId", "set"])
@pytest.mark.parametrize("value", [None, 3, False, [], ""])
def test_required_fields_reject_incompatible_types(field: str, value: object) -> None:
    data = card()
    data[field] = value
    assert translate_batch(batch(data)) == (RecordError(0, "invalid_field"),)


@pytest.mark.parametrize("field", ["id", "name", "localId", "set"])
def test_required_field_disappearance_rejects(field: str) -> None:
    data = card()
    del data[field]
    assert translate_batch(batch(data)) == (RecordError(0, "invalid_field"),)


@pytest.mark.parametrize("value", [{}, {"id": None}, {"id": 3}, {"id": ""}])
def test_required_set_reference_rejects(value: object) -> None:
    data = card()
    data["set"] = value
    assert translate_batch(batch(data)) == (RecordError(0, "invalid_field"),)


@pytest.mark.parametrize(
    "value",
    [None, [], True, "normal", {"normal": None}, {"reverse": 1}, {"holo": "true"}, {"wPromo": 0}],
)
def test_present_variant_shape_is_strict(value: object) -> None:
    data = card()
    data["variants"] = value
    assert translate_batch(batch(data)) == (RecordError(0, "invalid_field"),)


@pytest.mark.parametrize(
    "wrapper",
    [
        {"kind": "sealed"},
        {"language": "fr"},
        {"variant": "foil"},
        {"variant": False},
        {"unexpected": "ignored?"},
    ],
)
def test_incompatible_wrapper_is_explicit(wrapper: dict[str, Any]) -> None:
    assert translate_batch(batch(card(), **wrapper)) == (RecordError(0, "invalid_field"),)


def test_provider_extras_cannot_contaminate_normalized_output() -> None:
    data = card()
    data.update(
        {
            "image": "https://images.invalid/forbidden-sentinel",
            "pricing": {"cardmarket": {"avg": 999}},
            "description": "forbidden-description-sentinel",
            "boosters": [{"id": "invented-booster", "name": "forbidden-booster-sentinel"}],
            "variants_detailed": [{"type": "holo", "thirdParty": {"cardmarket": 1}}],
            "newCompatibleField": {"value": "forbidden-extra-sentinel"},
        }
    )
    data["set"]["logo"] = "https://logos.invalid/forbidden-logo-sentinel"
    result = translate_batch(batch(data))
    assert isinstance(result[0], Observation)
    exported = json.dumps(asdict(result[0]))
    assert "forbidden" not in exported
    assert "pricing" not in exported
    assert "invented-booster" not in exported
    assert result[0].kind == "card"
    assert result[0].reference.variant == "unknown"


@pytest.mark.parametrize("value", ["2026-13-01", "2026-02-30", "20260101", 3, False])
def test_incompatible_release_dates_reject(value: object) -> None:
    document = batch({"id": "synthetic-set", "name": "Conjunto", "releaseDate": value}, kind="set")
    assert translate_batch(document) == (RecordError(0, "invalid_field"),)


@pytest.mark.parametrize("value", ["2026-01-01", "bad-date", "2026-02-30T01:01:01Z", 3])
def test_incompatible_provider_timestamps_reject(value: object) -> None:
    data = card()
    data["updated"] = value
    assert translate_batch(batch(data)) == (RecordError(0, "invalid_field"),)


def test_distinct_valid_timestamps_and_nullable_set_release() -> None:
    data = card()
    data["updated"] = "2026-01-01T00:00:00+02:00"
    document = batch(data)
    document["captured_at"] = "2026-10-09T00:00:00Z"
    result = translate_batch(document)
    assert isinstance(result[0], Observation)
    assert result[0].provider_updated_at != result[0].captured_at
    document = batch({"id": "synthetic-set", "name": "Conjunto", "releaseDate": None}, kind="set")
    assert isinstance(translate_batch(document)[0], Observation)


@pytest.mark.parametrize(
    "document",
    [
        None,
        [],
        {},
        {"version": True, "provenance": "synthetic", "records": []},
        {"version": 1, "records": []},
        {"version": 1, "provenance": "invented", "records": []},
        {"version": 1, "provenance": "synthetic", "records": None},
        {"version": 1, "provenance": "synthetic", "records": [], "bad": True},
        {"version": 1, "provenance": "synthetic", "records": [], "captured_at": "bad"},
    ],
)
def test_global_envelope_failures_are_sanitized(document: object) -> None:
    with pytest.raises(CatalogError) as failure:
        translate_batch(document)
    assert "invented" not in str(failure.value)
    assert "records" not in str(failure.value)


def test_empty_mixed_global_invalid_and_malformed_are_distinct() -> None:
    assert translate_batch(read_json(FIXTURES / "synthetic_tcgdex_empty.json")) == ()
    mixed = translate_batch(read_json(FIXTURES / "synthetic_tcgdex_mixed.json"))
    assert isinstance(mixed[0], Observation)
    assert isinstance(mixed[1], Observation)
    assert mixed[1].reference.variant == "unknown"
    assert mixed[2] == RecordError(2, "invalid_field")
    with pytest.raises(CatalogError, match="unsupported_version"):
        translate_batch(read_json(FIXTURES / "synthetic_tcgdex_invalid.json"))
    with pytest.raises(CatalogError):
        read_json(FIXTURES / "synthetic_tcgdex_malformed.json")


def test_in_memory_work_is_bounded() -> None:
    with pytest.raises(CatalogError):
        translate_batch(
            {"version": 1, "provenance": "synthetic", "records": [None] * (MAX_RECORDS + 1)}
        )
    nested: object = {}
    for _ in range(20):
        nested = {"extra": nested}
    data = card()
    data["extra"] = nested
    with pytest.raises(CatalogError):
        translate_batch(batch(data))


@pytest.mark.parametrize("value", [" ", "x" * 257, "secret\nvalue"])
def test_bounded_metadata_strings_and_safe_errors(value: str) -> None:
    data = card()
    data["name"] = value
    assert translate_batch(batch(data)) == (RecordError(0, "invalid_field"),)


def test_nonobject_record_and_set_variant_reject_without_crash() -> None:
    assert translate_batch({"version": 1, "provenance": "synthetic", "records": [None]}) == (
        RecordError(0, "invalid_field"),
    )
    assert translate_batch(
        batch({"id": "synthetic-set", "name": "Conjunto"}, kind="set", variant="holo")
    ) == (RecordError(0, "invalid_field"),)


def test_provider_timezone_normalizes_utc_without_fabricated_capture() -> None:
    data = card()
    data["updated"] = "2026-01-01T02:00:00+02:00"
    result = translate_batch(batch(data))
    assert isinstance(result[0], Observation)
    assert result[0].provider_updated_at == "2026-01-01T00:00:00Z"
    assert result[0].captured_at is None


@pytest.mark.parametrize("value", ["https://host.invalid/id", "bad id", "x" * 129])
def test_external_identifiers_must_be_bounded_tokens(value: str) -> None:
    data = card()
    data["id"] = value
    assert translate_batch(batch(data)) == (RecordError(0, "invalid_field"),)


@pytest.mark.parametrize("value", [" ", "x" * 65])
def test_card_number_text_is_bounded(value: str) -> None:
    data = card()
    data["localId"] = value
    assert translate_batch(batch(data)) == (RecordError(0, "invalid_field"),)


@pytest.mark.parametrize("value", ["0001-01-01T00:00:00+23:59", "9999-12-31T23:59:59-23:59"])
def test_timestamp_normalization_extremes_reject_safely(value: str) -> None:
    data = card()
    data["updated"] = value
    assert translate_batch(batch(data)) == (RecordError(0, "invalid_field"),)
