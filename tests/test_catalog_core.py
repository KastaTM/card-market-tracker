"""Contract-derived identity, poisoning, determinism and input-boundary cases."""

import copy
import json
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import pytest

from card_market_tracker.catalog.ingestion import ExternalReference, Observation, RecordError
from card_market_tracker.catalog.manifest import parse_manifest, parse_reference
from card_market_tracker.catalog.resolver import resolve
from card_market_tracker.catalog.validation import (
    MAX_BYTES,
    MAX_DEPTH,
    MAX_NODES,
    CatalogError,
    array_value,
    date_value,
    object_value,
    read_json,
    string_value,
    timestamp_value,
    token_value,
    uuid_value,
    validate_structure,
)

FIXTURE = Path(__file__).parent / "fixtures" / "synthetic_manifest.json"


@pytest.fixture
def document():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def ref(kind="card", external_id="synthetic-card-001", language="es", variant="normal"):
    return ExternalReference("tcgdex", kind, external_id, language, variant)


def card(**changes):
    original = Observation(
        "card",
        ref(),
        "Synthetic Card",
        ref("set", "synthetic-set", variant="unknown"),
        "001",
        provenance="synthetic",
    )
    return replace(original, **changes)


def test_stable_manifest_identity_and_relation_closure(document):
    manifest = parse_manifest(document)
    batch = (
        card(),
        card(),
        card(reference=ref(variant="holo")),
        card(reference=ref(variant="reverse")),
        card(
            reference=ref(language="en"), set_reference=ref("set", "synthetic-set", "en", "unknown")
        ),
    )
    first = resolve(batch, manifest)
    second = resolve(batch, parse_manifest(copy.deepcopy(document)))
    assert first == second
    assert first.accepted == 5 and first.candidates == first.rejected == 0
    assert len(first.entities) == 6  # four printings, their card, their set
    assert len({entity.cmt_id for entity in first.entities}) == len(first.entities)
    assert [row.index for row in first.records] == list(range(5))
    assert first.records[0].cmt_id == first.records[1].cmt_id
    assert len({row.cmt_id for row in first.records}) == 4
    assert first.to_dict()["counts"] == {
        "input": 5,
        "accepted": 5,
        "candidates": 0,
        "rejected": 0,
        "entities": 6,
    }
    serialized = json.dumps(first.to_dict())
    assert "Synthetic Card" not in serialized and '"names":' not in serialized


def test_name_and_external_alias_never_define_identity(document):
    manifest = parse_manifest(document)
    alias = ExternalReference("curated", "card", "synthetic-alias", "es", "normal")
    batch = resolve((card(), card(name="Entirely renamed", reference=alias)), manifest)
    assert batch.accepted == 2 and batch.records[0].cmt_id == batch.records[1].cmt_id
    sets = [entity for entity in manifest.entities if entity.kind == "set"]
    assert sets[0].names == sets[1].names and sets[0].cmt_id != sets[1].cmt_id
    missing = card(reference=ref(external_id="new-same-name"))
    assert resolve((missing,), manifest).records[0].category == "missing_binding"


@pytest.mark.parametrize(
    "number,external_id", [("TG01", "synthetic-card-TG01"), ("SVP-001", "synthetic-card-SVP-001")]
)
def test_special_numbers_preserved(document, number, external_id):
    observation = card(card_number=number, reference=ref(external_id=external_id))
    if number == "SVP-001":
        observation = replace(
            observation, set_reference=ref("set", "synthetic-other-set", variant="unknown")
        )
    result = resolve((observation,), parse_manifest(document))
    assert result.accepted == 1
    assert number in {entity.card_number for entity in result.entities}


@pytest.mark.parametrize(
    "observation,reason",
    [
        (card(reference=ref(variant="unknown")), "unknown_variant"),
        (card(reference=ref(language=None)), "unknown_language"),
        (card(reference=ref(external_id="unknown")), "missing_binding"),
        (card(set_reference=ref("set", "unknown-set", variant="unknown")), "missing_binding"),
    ],
)
def test_candidates_not_promoted(document, observation, reason):
    result = resolve((observation,), parse_manifest(document))
    assert result.accepted == result.rejected == 0 and result.candidates == 1
    assert result.entities == ()
    assert result.records[0].category == reason and result.records[0].cmt_id is None
    assert result.records[0].reference == observation.reference
    assert result.records[0].provenance == "synthetic"


@pytest.mark.parametrize("variant", ["normal", "unknown", "holo"])
@pytest.mark.parametrize("change", ["number", "set"])
def test_contradictions_precede_unknown_candidate(document, variant, change):
    observation = card(reference=ref(variant=variant))
    if change == "number":
        observation = replace(observation, card_number="1")
    else:
        observation = replace(
            observation, set_reference=ref("set", "synthetic-other-set", variant="unknown")
        )
    result = resolve((observation,), parse_manifest(document))
    assert result.rejected == 1 and result.records[0].category == "identity_conflict"
    assert result.records[0].reference is None


def test_set_localizations_and_release_conflict(document):
    manifest = parse_manifest(document)
    es = Observation(
        "set",
        ref("set", "synthetic-set", variant="unknown"),
        "Changed name",
        provenance="synthetic",
    )
    en = replace(es, reference=ref("set", "synthetic-set", "en", "unknown"))
    unknown_language = replace(es, reference=ref("set", "synthetic-set", None, "unknown"))
    assert resolve((es, en), manifest).accepted == 2
    assert len(resolve((es, en), manifest).entities) == 1
    assert resolve((unknown_language,), manifest).candidates == 1
    assert resolve((replace(es, release_date="2025-02-01"),), manifest).rejected == 1
    assert resolve((replace(es, release_date="2025-01-01"),), manifest).accepted == 1


def test_sealed_independent_and_no_booster_derivation(document):
    manifest = parse_manifest(document)
    reference = ExternalReference("curated", "sealed", "synthetic-box", "es")
    observed = Observation(
        "sealed",
        reference,
        "Synthetic box",
        ref("set", "synthetic-set", variant="unknown"),
        provenance="synthetic",
    )
    result = resolve((observed,), manifest)
    assert result.accepted == 1 and {row.kind for row in result.entities} == {"set", "sealed"}
    assert all(row.card_id is None for row in result.entities)
    assert (
        resolve(
            (replace(observed, reference=replace(reference, language=None)),), manifest
        ).candidates
        == 1
    )
    assert (
        resolve(
            (
                replace(
                    observed, set_reference=ref("set", "synthetic-other-set", variant="unknown")
                ),
            ),
            manifest,
        ).rejected
        == 1
    )


def test_empty_and_mixed_counts(document):
    manifest = parse_manifest(document)
    assert resolve((), manifest).to_dict()["counts"] == {
        "input": 0,
        "accepted": 0,
        "candidates": 0,
        "rejected": 0,
        "entities": 0,
    }
    result = resolve(
        (
            card(),
            card(reference=ref(variant="unknown")),
            RecordError(2, "invalid_field"),
            RecordError(3, "raw-secret-must-never-appear"),
        ),
        manifest,
    )
    assert (result.accepted, result.candidates, result.rejected) == (1, 1, 2)
    assert "raw-secret" not in json.dumps(result.to_dict())
    assert parse_manifest({"version": 1, "entities": [], "bindings": []}).entities == ()
    with pytest.raises(CatalogError, match="input_limit"):
        resolve((card(),) * 1001, manifest)


@pytest.mark.parametrize(
    "changes",
    [
        {"kind": "set"},
        {"name": ""},
        {"provenance": "guess"},
        {"card_number": None},
        {"card_number": "x" * 65},
        {"set_reference": None},
        {"set_reference": ref()},
        {"release_date": "2025-02-30"},
        {"provider_updated_at": "2025-01-01"},
        {"captured_at": "2025-01-01T00:00:00"},
        {"reference": ref(external_id="https://evil.example/")},
    ],
)
def test_normalized_boundary_rejects_malformed_observations(document, changes):
    assert resolve((card(**changes),), parse_manifest(document)).rejected == 1


def test_noncard_cannot_carry_card_number(document):
    observation = Observation(
        "set",
        ref("set", "synthetic-set", variant="unknown"),
        "Set",
        card_number="001",
        provenance="synthetic",
    )
    assert resolve((observation,), parse_manifest(document)).rejected == 1


@pytest.mark.parametrize(
    "field,value,category",
    [
        ("version", 2, "unsupported_version"),
        ("version", True, "unsupported_version"),
        ("entities", None, "invalid_shape"),
        ("bindings", {}, "invalid_shape"),
        ("extra", "ignored?", "invalid_shape"),
    ],
)
def test_manifest_top_level_contract(document, field, value, category):
    document[field] = value
    with pytest.raises(CatalogError, match=category):
        parse_manifest(document)


@pytest.mark.parametrize(
    "field,value,category",
    [
        ("cmt_id", "provider-id", "invalid_field"),
        ("kind", "listing", "invalid_field"),
        ("names", {"fr": "Name"}, "invalid_field"),
        ("names", {"es": None}, "invalid_field"),
        ("set_id", str(uuid4()), "invalid_field"),
        ("card_id", str(uuid4()), "invalid_field"),
        ("card_number", "001", "invalid_field"),
        ("language", "es", "invalid_field"),
        ("variant", "normal", "invalid_field"),
        ("release_date", "2025-02-30", "invalid_field"),
        ("sealed_type", "box", "invalid_field"),
        ("raw_payload", {}, "invalid_shape"),
    ],
)
def test_manifest_entity_contract(document, field, value, category):
    document["entities"][0][field] = value
    with pytest.raises(CatalogError, match=category):
        parse_manifest(document)


@pytest.mark.parametrize(
    "mutation,category",
    [
        ("duplicate_id", "duplicate_id"),
        ("duplicate_card", "duplicate_identity"),
        ("duplicate_printing", "duplicate_identity"),
        ("missing_set", "broken_relation"),
        ("wrong_set", "broken_relation"),
        ("missing_card", "broken_relation"),
        ("wrong_card", "broken_relation"),
        ("printing_set", "broken_relation"),
        ("no_card_number", "broken_relation"),
        ("no_card_set", "broken_relation"),
        ("no_printing_card", "broken_relation"),
        ("sealed_variant", "invalid_field"),
        ("sealed_type", "invalid_field"),
    ],
)
def test_manifest_relations_and_unique_constraints(document, mutation, category):
    entities = document["entities"]
    if mutation.startswith("duplicate"):
        original = entities[
            0 if mutation == "duplicate_id" else 2 if mutation == "duplicate_card" else 5
        ]
        duplicate = copy.deepcopy(original)
        if mutation != "duplicate_id":
            duplicate["cmt_id"] = str(uuid4())
        entities.append(duplicate)
    elif mutation in ("missing_set", "wrong_set", "no_card_set", "no_card_number"):
        entities[2]["set_id"] = str(uuid4()) if mutation == "missing_set" else entities[2]["cmt_id"]
        if mutation == "no_card_set":
            entities[2]["set_id"] = None
        if mutation == "no_card_number":
            entities[2]["set_id"] = entities[0]["cmt_id"]
            entities[2]["card_number"] = None
    elif mutation in ("missing_card", "wrong_card", "no_printing_card", "printing_set"):
        entities[5]["card_id"] = (
            str(uuid4()) if mutation == "missing_card" else entities[0]["cmt_id"]
        )
        if mutation == "no_printing_card":
            entities[5]["card_id"] = None
        if mutation == "printing_set":
            entities[5]["card_id"] = entities[2]["cmt_id"]
            entities[5]["set_id"] = entities[0]["cmt_id"]
    else:
        entities[-1]["variant" if mutation == "sealed_variant" else "sealed_type"] = (
            "normal" if mutation == "sealed_variant" else None
        )
    with pytest.raises(CatalogError, match=category):
        parse_manifest(document)


@pytest.mark.parametrize(
    "mutation,category",
    [
        ("duplicate", "contradictory_binding"),
        ("wrong_target", "broken_relation"),
        ("missing_target", "broken_relation"),
        ("language", "contradictory_binding"),
        ("variant", "contradictory_binding"),
        ("missing_reason", "invalid_shape"),
        ("variant_cross_card", "contradictory_binding"),
    ],
)
def test_manifest_binding_contradictions(document, mutation, category):
    bindings = document["bindings"]
    if mutation == "duplicate":
        bindings.append(copy.deepcopy(bindings[0]))
    elif mutation == "wrong_target":
        bindings[3]["cmt_id"] = document["entities"][2]["cmt_id"]
    elif mutation == "missing_target":
        bindings[0]["cmt_id"] = str(uuid4())
    elif mutation in ("language", "variant"):
        bindings[3]["reference"][mutation] = "en" if mutation == "language" else "reverse"
    elif mutation == "variant_cross_card":
        document["entities"][6]["card_id"] = document["entities"][3]["cmt_id"]
    else:
        bindings[0].pop("reason")
    with pytest.raises(CatalogError, match=category):
        parse_manifest(document)


@pytest.mark.parametrize(
    "change",
    [
        {"language": "fr"},
        {"variant": None},
        {"kind": "cardx"},
        {"namespace": "evil://"},
        {"kind": "set", "variant": "normal"},
    ],
)
def test_reference_context_validation(change):
    mapping = {
        "namespace": "tcgdex",
        "kind": "card",
        "external_id": "001",
        "language": "es",
        "variant": "normal",
    }
    with pytest.raises(CatalogError):
        parse_reference({**mapping, **change})


@pytest.mark.parametrize(
    "text,category",
    [
        ("{", "invalid_json"),
        ('{"x":1,"x":2}', "duplicate_key"),
        ('{"nested":{"id":"a","id":"b"}}', "duplicate_key"),
        ("NaN", "invalid_json"),
        ("Infinity", "invalid_json"),
        ("1e999", "invalid_json"),
        ('"\\ud800"', "invalid_json"),
        ('"unfinished\\"', "invalid_json"),
    ],
)
def test_strict_json_reader(tmp_path, text, category):
    path = tmp_path / "input.json"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(CatalogError, match=category):
        read_json(path)


def test_reader_limits_and_safe_paths(tmp_path):
    with pytest.raises(CatalogError, match="input_io"):
        read_json(tmp_path / "missing")
    with pytest.raises(CatalogError, match="input_io"):
        read_json(tmp_path)
    path = tmp_path / "input.json"
    path.write_bytes(b"x" * (MAX_BYTES + 1))
    with pytest.raises(CatalogError, match="input_limit"):
        read_json(path)
    path.write_bytes(b'"\xff"')
    with pytest.raises(CatalogError, match="invalid_json"):
        read_json(path)
    path.write_text("[" * (MAX_DEPTH + 1) + "0" + "]" * (MAX_DEPTH + 1), encoding="utf-8")
    with pytest.raises(CatalogError, match="input_limit"):
        read_json(path)
    # Brackets and escaped quotes inside a string do not consume nesting budget.
    path.write_text(json.dumps({"x": '["escaped\\"]}'}), encoding="utf-8")
    assert read_json(path) == {"x": '["escaped\\"]}'}


@pytest.mark.parametrize(
    "value",
    [
        "x" * 1025,
        [0] * MAX_NODES,
        [0] * (MAX_NODES + 1),
        {str(i): 0 for i in range(MAX_NODES + 1)},
        {"x": float("nan")},
        {"x": object()},
        {1: "value"},
    ],
)
def test_direct_structure_is_bounded(value):
    with pytest.raises(CatalogError):
        validate_structure(value)


def test_direct_depth_and_valid_primitives():
    value = 0
    for _ in range(MAX_DEPTH + 1):
        value = [value]
    with pytest.raises(CatalogError, match="input_limit"):
        validate_structure(value)
    validate_structure({"values": [None, True, 1, 1.5, "name"]})


@pytest.mark.parametrize(
    "validator,value",
    [
        (object_value, []),
        (array_value, {}),
        (string_value, None),
        (string_value, ""),
        (string_value, "secret\nvalue"),
        (string_value, "\ud800"),
        (token_value, "/tmp/path"),
        (uuid_value, "00000000-0000-1000-8000-000000000000"),
        (uuid_value, 123),
        (date_value, "20250101"),
        (timestamp_value, "2025-01-01T00:00:00+02:00"),
        (timestamp_value, "not-a-date"),
    ],
)
def test_field_validator_failures(validator, value):
    with pytest.raises(CatalogError):
        validator(value)


def test_valid_nullable_fields_and_safe_errors():
    assert date_value(None) is timestamp_value(None) is None
    assert date_value("2025-01-01") == "2025-01-01"
    assert timestamp_value("2025-01-01T00:00:00Z") == "2025-01-01T00:00:00Z"
    assert str(CatalogError("arbitrary secret")) == "invalid_field"
    with pytest.raises(CatalogError, match="input_limit"):
        array_value([1], limit=0)
