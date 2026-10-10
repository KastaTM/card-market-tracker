"""Manual dataclasses must not forge authority, snapshots or rejection evidence."""

from dataclasses import replace

import pytest
from test_persistence_input import CAPTURE, TOKEN, batch, manifest_document

from card_market_tracker.catalog.ingestion import RecordError
from card_market_tracker.catalog.manifest import Binding, Manifest
from card_market_tracker.catalog.models import Localization
from card_market_tracker.catalog.resolver import BatchResult
from card_market_tracker.persistence import (
    PersistedRecord,
    PersistenceError,
    application,
    build_batch,
    canonical_payload,
    validate_batch,
)


@pytest.mark.parametrize(
    "change", ["target", "status", "category", "index", "bool_index", "context"]
)
def test_manually_forged_resolution_is_recomputed(change):
    original = batch()
    row = original.records[2]
    if change == "target":
        row = replace(row, cmt_id=original.records[3].cmt_id)
    elif change == "status":
        row = replace(row, status="candidate", cmt_id=None, category="missing_binding")
    elif change == "category":
        row = replace(row, category="missing_binding")
    elif change == "index":
        row = replace(row, index=10)
    elif change == "bool_index":
        row = replace(row, index=False)
    else:
        row = replace(
            row,
            observation=replace(
                row.observation, reference=replace(row.observation.reference, variant="holo")
            ),
        )
    forged = replace(original, records=original.records[:2] + (row,) + original.records[3:])
    with pytest.raises(PersistenceError, match="resolution_mismatch"):
        validate_batch(forged)
    with pytest.raises(PersistenceError):
        canonical_payload(forged)


@pytest.mark.parametrize("change", ["target", "category", "accepted", "absent_observation"])
def test_candidate_cannot_promote_itself_or_change_reason(change):
    original = batch("candidates")
    row = original.records[0]
    if change == "target":
        row = replace(row, cmt_id="f9743b79-20e3-4815-98d3-bb06f0c8195f")
    elif change == "category":
        row = replace(row, category="unknown_variant")
    elif change == "accepted":
        row = replace(
            row, status="accepted", category=None, cmt_id="f9743b79-20e3-4815-98d3-bb06f0c8195f"
        )
    else:
        row = replace(row, observation=None)
    with pytest.raises(PersistenceError):
        validate_batch(replace(original, records=(row,) + original.records[1:]))


@pytest.mark.parametrize("change", ["payload", "target", "raw_category", "null_category"])
def test_rejection_cannot_retain_raw_evidence(change):
    original = batch("rejected")
    row = original.records[0]
    if change == "payload":
        row = replace(row, observation=batch().records[0].observation)
    elif change == "target":
        row = replace(row, cmt_id="f9743b79-20e3-4815-98d3-bb06f0c8195f")
    elif change == "raw_category":
        row = replace(row, category="raw private sentinel")
    else:
        row = replace(row, category=None)
    with pytest.raises(PersistenceError) as failure:
        validate_batch(replace(original, records=(row,) + original.records[1:]))
    assert "sentinel" not in str(failure.value)


@pytest.mark.parametrize(
    "error",
    [
        RecordError(2, "invalid_field"),
        RecordError(False, "invalid_field"),
        RecordError(0, "secret"),
        RecordError(0, []),
    ],
)
def test_generic_safe_errors_require_exact_index_and_category(error):
    with pytest.raises(PersistenceError):
        build_batch(TOKEN, CAPTURE, (error,), manifest_document())


def test_categorical_rejection_is_a_documented_producer_assertion():
    result = build_batch(
        TOKEN, CAPTURE, (RecordError(0, "identity_conflict"),), manifest_document()
    )
    assert result.records == (PersistedRecord(0, "rejected", "identity_conflict", None, None),)
    assert validate_batch(result) == result


@pytest.mark.parametrize("change", ["missing_parent", "extra_entity", "relation", "names"])
def test_parent_closure_is_independently_checked(change):
    original = batch()
    entities = original.entities
    if change == "missing_parent":
        entities = tuple(entity for entity in entities if entity.kind != "set")
    elif change == "extra_entity":
        extra = next(entity for entity in original.manifest.entities if entity.kind == "sealed")
        entities = entities + (extra,)
    elif change == "relation":
        entities = tuple(
            replace(entity, card_id=None) if entity.kind == "printing" else entity
            for entity in entities
        )
    else:
        entities = (
            replace(entities[0], names=(Localization("es", "forged localization"),)),
        ) + entities[1:]
    with pytest.raises(PersistenceError):
        validate_batch(replace(original, entities=entities))


@pytest.mark.parametrize(
    "change",
    [
        "entity",
        "binding",
        "reference",
        "reason",
        "duplicate_localization",
        "localization_object",
        "entities_list",
        "bindings_list",
    ],
)
def test_manually_constructed_manifest_is_reparsed_without_unsafe_exceptions(change):
    original = batch().manifest
    entities, bindings = original.entities, original.bindings
    if change == "entity":
        entities = (replace(entities[0], cmt_id="sentinel"),) + entities[1:]
    elif change == "binding":
        bindings = (Binding(bindings[0].reference, "sentinel", "audit"),) + bindings[1:]
    elif change == "reference":
        bindings = (replace(bindings[0], reference=None),) + bindings[1:]
    elif change == "reason":
        bindings = (replace(bindings[0], reason=None),) + bindings[1:]
    elif change == "duplicate_localization":
        entities = (
            replace(entities[0], names=(Localization("es", "a"), Localization("es", "b"))),
        ) + entities[1:]
    elif change == "localization_object":
        entities = (replace(entities[0], names=(None,)),) + entities[1:]
    elif change == "entities_list":
        entities = list(entities)
    else:
        bindings = list(bindings)
    with pytest.raises(PersistenceError) as failure:
        build_batch(TOKEN, CAPTURE, (), Manifest(entities, bindings))
    assert "sentinel" not in str(failure.value)


@pytest.mark.parametrize("change", ["reference", "set_reference", "name", "provenance", "capture"])
def test_malformed_nested_programmatic_observations_fail_safely(change):
    original = batch()
    observation = original.records[2].observation
    if change == "reference":
        observation = replace(observation, reference=None)
    elif change == "set_reference":
        observation = replace(observation, set_reference="sentinel")
    elif change == "name":
        observation = replace(observation, name={"secret": "sentinel"})
    elif change == "provenance":
        observation = replace(observation, provenance=["synthetic"])
    else:
        observation = replace(observation, captured_at={"secret": "sentinel"})
    forged_row = replace(original.records[2], observation=observation)
    with pytest.raises(PersistenceError) as failure:
        validate_batch(
            replace(original, records=original.records[:2] + (forged_row,) + original.records[3:])
        )
    assert "sentinel" not in str(failure.value)


@pytest.mark.parametrize("value", [None, {}, [], "sentinel"])
def test_public_batch_boundary_checks_dataclass_type(value):
    with pytest.raises(PersistenceError):
        validate_batch(value)


def test_oversize_programmatic_observations_are_bounded_before_resolution():
    observation = batch().records[0].observation
    with pytest.raises(PersistenceError, match="input_limit"):
        build_batch(TOKEN, CAPTURE, (observation,) * 1001, manifest_document())


@pytest.mark.parametrize("change", ["truncated", "index", "reference", "provenance"])
def test_composition_verifies_resolver_correspondence(monkeypatch, change):
    original = batch()
    observations = tuple(row.observation for row in original.records)
    result = application.resolve(observations, original.manifest)
    records = result.records
    if change == "truncated":
        records = records[:-1]
    else:
        first = records[0]
        if change == "index":
            first = replace(first, index=1)
        elif change == "reference":
            first = replace(first, reference=records[2].reference)
        else:
            first = replace(first, provenance="observed")
        records = (first,) + records[1:]
    monkeypatch.setattr(application, "resolve", lambda *_: BatchResult(records, result.entities))
    with pytest.raises(PersistenceError, match="resolution_mismatch"):
        build_batch(TOKEN, CAPTURE, observations, original.manifest)
