"""Temporal, synthetic provenance, safe rejection and replay equivalence risks."""

import copy
import json
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import pytest

from card_market_tracker.catalog.adapters.tcgdex import translate_batch
from card_market_tracker.catalog.ingestion import ExternalReference, Observation
from card_market_tracker.catalog.manifest import parse_manifest
from card_market_tracker.catalog.resolver import resolve
from card_market_tracker.catalog.validation import MAX_BYTES, CatalogError, read_json
from card_market_tracker.persistence import (
    PersistenceError,
    WriteResult,
    build_batch,
    canonical_payload,
    context_fingerprint,
    fingerprint,
    parse_persistence,
    read_persistence,
    validate_batch,
)

FIXTURES = Path(__file__).parent / "fixtures"
CAPTURE = "2026-10-10T09:00:00.000000Z"
TOKEN = "824d9220-d225-4d09-9964-6d33142408a7"


def document(name="valid"):
    return read_json(FIXTURES / f"synthetic_persistence_{name}.json")


def manifest_document():
    return json.loads((FIXTURES / "synthetic_manifest.json").read_text(encoding="utf-8"))


def batch(name="valid"):
    return parse_persistence(document(name), manifest_document())


def test_complete_metadata_survives_lossy_p1a_result():
    value = document()
    normalized = translate_batch(value["ingestion"])
    p1a_output = resolve(normalized, parse_manifest(manifest_document())).to_dict()
    persisted = batch()
    assert persisted.records[2].observation.name == "Carta sintética"
    assert persisted.records[2].observation.card_number == "001"
    assert persisted.records[2].observation.set_reference.external_id == "synthetic-set"
    assert persisted.records[2].observation.provider_updated_at == "2026-10-09T09:30:00.000000Z"
    assert persisted.records[0].observation.release_date == "2025-01-01"
    assert all(record.observation.captured_at == CAPTURE for record in persisted.records)
    assert "provider_updated_at" not in json.dumps(p1a_output)
    assert "captured_at" not in json.dumps(p1a_output)
    assert "Carta sintética" not in json.dumps(p1a_output, ensure_ascii=False)
    assert validate_batch(persisted) == persisted
    with pytest.raises(FrozenInstanceError):
        persisted.captured_at = "mutated"


@pytest.mark.parametrize(
    "name,accepted,candidates,rejected",
    [
        ("valid", 7, 0, 0),
        ("mixed", 1, 1, 1),
        ("candidates", 0, 2, 0),
        ("rejected", 0, 0, 2),
        ("empty", 0, 0, 0),
    ],
)
def test_partition_safe_rejection_and_candidates(name, accepted, candidates, rejected):
    value = batch(name)
    assert sum(row.status == "accepted" for row in value.records) == accepted
    assert sum(row.status == "candidate" for row in value.records) == candidates
    assert sum(row.status == "rejected" for row in value.records) == rejected
    assert [row.index for row in value.records] == list(range(len(value.records)))
    for row in value.records:
        if row.status == "rejected":
            assert row.observation is row.cmt_id is None
        elif row.status == "candidate":
            assert row.cmt_id is None and row.observation.reference is not None
    assert "Rejected invented sentinel" not in json.dumps(canonical_payload(value))
    if accepted == 0:
        assert value.entities == ()


@pytest.mark.parametrize(
    "name,category",
    [
        ("missing_capture", "capture_required"),
        ("contradictory_capture", "capture_conflict"),
        ("invalid", "unsupported_version"),
        ("documented", "synthetic_only"),
        ("observed", "synthetic_only"),
    ],
)
def test_global_negative_fixtures(name, category):
    with pytest.raises(PersistenceError) as failure:
        batch(name)
    assert failure.value.category == category and failure.value.exit_code == 2
    assert str(failure.value) == category


@pytest.mark.parametrize(
    "timestamp",
    [
        None,
        "2026-10-10T09:00:00",
        "2026-10-10",
        "2026-02-30T00:00:00Z",
        "0001-01-01T00:00:00+23:59",
        "9999-12-31T23:59:59-23:59",
        False,
        123,
    ],
)
def test_capture_is_explicit_zoned_and_overflow_safe(timestamp):
    value = document("empty")
    value["captured_at"] = timestamp
    with pytest.raises(PersistenceError) as failure:
        parse_persistence(value, manifest_document())
    assert failure.value.category in ("capture_required", "invalid_field")
    assert str(timestamp) not in str(failure.value)


def test_offsets_are_equivalent_and_fractional_precision_stably_orders():
    assert batch("offset") == batch()
    assert fingerprint(batch("offset")) == fingerprint(batch())
    value = document("empty")
    value["captured_at"] = "2026-10-10T09:00:00.1Z"
    one = parse_persistence(value, manifest_document())
    value["captured_at"] = "2026-10-10T09:00:00.100001Z"
    two = parse_persistence(value, manifest_document())
    assert one.captured_at == "2026-10-10T09:00:00.100000Z"
    assert CAPTURE < one.captured_at < two.captured_at


def test_existing_p1a_capture_remains_optional_and_never_inferred():
    normalized = translate_batch(document()["ingestion"])
    assert all(item.captured_at is None for item in normalized)
    persisted = build_batch(TOKEN, CAPTURE, normalized, manifest_document())
    assert persisted.records[0].observation.captured_at == CAPTURE
    assert persisted.records[0].observation.provider_updated_at is None
    assert persisted.records[0].observation.release_date == "2025-01-01"


def test_programmatic_sealed_generic_api_requires_curated_binding():
    sealed = Observation(
        "sealed",
        ExternalReference("curated", "sealed", "synthetic-box", "es"),
        "Invented sealed observation",
        ExternalReference("tcgdex", "set", "synthetic-set", "es"),
        provider_updated_at="2026-10-09T10:30:00+01:00",
        provenance="synthetic",
    )
    value = build_batch(TOKEN, CAPTURE, (sealed,), parse_manifest(manifest_document()))
    assert value.records[0].status == "accepted"
    assert value.records[0].cmt_id == "79b79554-edd4-4bdc-8120-859974c3df62"
    assert value.records[0].observation.provider_updated_at == "2026-10-09T09:30:00.000000Z"
    assert {entity.kind for entity in value.entities} == {"set", "sealed"}
    assert validate_batch(value) == value


@pytest.mark.parametrize("provenance", ["observed", "documented", None, "forged"])
def test_programmatic_provenance_fails_before_invalid_observation_is_rejected(provenance):
    invalid = replace(batch().records[2].observation, name="", provenance=provenance)
    with pytest.raises(PersistenceError, match="synthetic_only"):
        build_batch(TOKEN, CAPTURE, (invalid,), manifest_document())


def test_programmatic_capture_conflicts_even_for_otherwise_rejected_observation():
    invalid = replace(batch().records[2].observation, name="", captured_at="2026-10-11T09:00:00Z")
    with pytest.raises(PersistenceError, match="capture_conflict"):
        build_batch(TOKEN, CAPTURE, (invalid,), manifest_document())


def test_provider_timestamp_error_is_safe_record_rejection():
    invalid = replace(batch().records[2].observation, provider_updated_at="secret invalid instant")
    value = build_batch(TOKEN, CAPTURE, (invalid,), manifest_document())
    assert value.records[0].category == "invalid_field"
    assert value.records[0].observation is None
    assert "secret" not in json.dumps(canonical_payload(value))


def test_normalized_identity_poison_is_not_retained_or_hashed():
    invalid = replace(
        batch().records[2].observation, card_number="poisoned", name="private sentinel"
    )
    value = build_batch(TOKEN, CAPTURE, (invalid,), manifest_document())
    alternative = build_batch(
        TOKEN, CAPTURE, (replace(invalid, name="another sentinel"),), manifest_document()
    )
    assert value.records[0].category == "identity_conflict"
    assert value.records[0].observation is None
    assert value.entities == ()
    assert fingerprint(value) == fingerprint(alternative)
    assert "sentinel" not in json.dumps(canonical_payload(value))


def test_token_excluded_capture_order_duplicates_and_evidence_included():
    first = batch()
    another_token = replace(first, batch_id="5c367329-bd86-4652-b0ac-8b68ed9a08a9")
    assert fingerprint(first) == fingerprint(another_token)
    assert fingerprint(first) != fingerprint(batch("conflict"))
    observations = tuple(row.observation for row in first.records)
    reversed_batch = build_batch(TOKEN, CAPTURE, tuple(reversed(observations)), first.manifest)
    duplicate_batch = build_batch(TOKEN, CAPTURE, observations + observations[:1], first.manifest)
    renamed_batch = build_batch(
        TOKEN,
        CAPTURE,
        (replace(observations[0], name="Changed evidence"),) + observations[1:],
        first.manifest,
    )
    assert (
        len(
            {
                fingerprint(first),
                fingerprint(reversed_batch),
                fingerprint(duplicate_batch),
                fingerprint(renamed_batch),
            }
        )
        == 4
    )
    assert context_fingerprint(first) == context_fingerprint(batch("later"))


def test_manifest_order_localization_and_reasons_do_not_change_context():
    changed = manifest_document()
    changed["entities"].reverse()
    changed["bindings"].reverse()
    changed["entities"][0]["names"] = {"es": "Valid new localization"}
    for binding in changed["bindings"]:
        binding["reason"] = "New valid curator audit text"
    rebuilt = parse_persistence(document(), changed)
    assert fingerprint(rebuilt) == fingerprint(batch())
    assert context_fingerprint(rebuilt) == context_fingerprint(batch())


def test_unrelated_manifest_binding_and_release_metadata_change_context():
    changed = manifest_document()
    changed["bindings"].append(copy.deepcopy(changed["bindings"][0]))
    changed["bindings"][-1]["reference"]["namespace"] = "synthetic-other-namespace"
    assert context_fingerprint(parse_persistence(document(), changed)) != context_fingerprint(
        batch()
    )
    changed = manifest_document()
    changed["entities"][1]["release_date"] = "2024-01-01"
    assert context_fingerprint(parse_persistence(document(), changed)) != context_fingerprint(
        batch()
    )


@pytest.mark.parametrize(
    "mutation", ["extra", "missing", "bool_version", "null_ingestion", "bad_token"]
)
def test_strict_wrapper_shape_version_and_token(mutation):
    value = document("empty")
    if mutation == "extra":
        value["extra"] = "sentinel"
    elif mutation == "missing":
        del value["ingestion"]
    elif mutation == "bool_version":
        value["version"] = True
    elif mutation == "null_ingestion":
        value["ingestion"] = None
    else:
        value["batch_id"] = "11111111-1111-1111-1111-111111111111"
    with pytest.raises(PersistenceError):
        parse_persistence(value, manifest_document())


@pytest.mark.parametrize("kind", ["depth", "nodes", "string", "records", "bytes"])
def test_programmatic_wrapper_reuses_p1a_resource_bounds(kind):
    value = document("empty")
    if kind == "depth":
        nested = {}
        for _ in range(20):
            nested = {"extra": nested}
        value["ingestion"]["records"] = [nested]
    elif kind == "nodes":
        value["ingestion"]["records"] = [None] * 20001
    elif kind == "string":
        value["ingestion"]["extra"] = "x" * 1025
    elif kind == "records":
        value["ingestion"]["records"] = [None] * 1001
    else:
        value["ingestion"]["records"] = [{"extra": ["x" * 1024] * 1030}]
    with pytest.raises(PersistenceError, match="input_limit"):
        parse_persistence(value, manifest_document())


@pytest.mark.parametrize(
    "contents,category",
    [
        (b'{"version":1,"version":1}', "duplicate_key"),
        (b"\xff", "invalid_json"),
        (b"{" + b" " * MAX_BYTES, "input_limit"),
    ],
    ids=["duplicate", "encoding", "bytes"],
)
def test_file_reader_bounds_and_json_failures(tmp_path, contents, category):
    source = tmp_path / "input.json"
    source.write_bytes(contents)
    with pytest.raises(PersistenceError) as failure:
        read_persistence(source, FIXTURES / "synthetic_manifest.json")
    assert failure.value.category == category


def test_missing_file_is_local_error_not_valid_empty(tmp_path):
    with pytest.raises(PersistenceError) as failure:
        read_persistence(tmp_path / "missing.json", FIXTURES / "synthetic_manifest.json")
    assert failure.value.category == "input_io" and failure.value.exit_code == 1


def test_read_boundary_and_processing_vs_committed_counts():
    assert (
        read_persistence(
            FIXTURES / "synthetic_persistence_valid.json", FIXTURES / "synthetic_manifest.json"
        )
        == batch()
    )
    replay = WriteResult("replay", TOKEN, CAPTURE, 3, 1, 1, 1, 0, 0).to_dict()
    assert replay["counts"] == {"input": 3, "accepted": 1, "candidates": 1, "rejected": 1}
    assert replay["committed"] == {"observations": 0, "entities": 0}


def test_only_safe_categories_enter_exceptions():
    failure = PersistenceError("private secret / file path")
    assert failure.category == "invalid_field"
    assert str(failure) == "invalid_field"
    assert not isinstance(failure, CatalogError)
