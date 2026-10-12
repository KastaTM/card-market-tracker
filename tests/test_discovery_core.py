"""Synthetic pure comparison and forged-snapshot boundary regressions."""

import hashlib
import json
import subprocess
import sys
from dataclasses import replace

import pytest

from card_market_tracker.catalog.ingestion import ExternalReference, Observation
from card_market_tracker.discovery import (
    BatchSnapshot,
    DiscoveryContext,
    DiscoveryError,
    DiscoveryRequest,
    SnapshotRecord,
    compare,
    validate_snapshot,
)
from card_market_tracker.discovery.validation import canonical_json, snapshot_dict

CURRENT = "22222222-2222-4222-8222-222222222222"
HISTORY = "11111111-1111-4111-8111-111111111111"
EMPTY = "33333333-3333-4333-8333-333333333333"
CMT_ID = "f9743b79-20e3-4815-98d3-bb06f0c8195f"
OLD = "2026-01-01T00:00:00.000000Z"
NOW = "2026-01-03T00:00:00.000000Z"


def observation(
    external_id="new", *, capture=NOW, kind="set", language="es", variant="unknown", **kwargs
):
    reference = ExternalReference("synthetic", kind, external_id, language, variant)
    parent = ExternalReference("synthetic", "set", "parent", language) if kind == "card" else None
    return Observation(
        kind,
        reference,
        "Invented name",
        set_reference=parent,
        card_number="001" if kind == "card" else None,
        captured_at=capture,
        provenance="synthetic",
        **kwargs,
    )


def record(external_id="new", *, index=0, status="accepted", capture=NOW, **kwargs):
    if kwargs.get("kind") == "card" and "variant" not in kwargs:
        kwargs["variant"] = "normal"
    return SnapshotRecord(
        index,
        status,
        "missing_binding" if status == "candidate" else None,
        CMT_ID if status == "accepted" else None,
        observation(external_id, capture=capture, **kwargs),
    )


def batch(records=(), *, batch_id=CURRENT, capture=NOW):
    accepted = sum(row.status == "accepted" for row in records)
    candidate = sum(row.status == "candidate" for row in records)
    rejected = sum(row.status == "rejected" for row in records)
    return BatchSnapshot(
        1,
        1,
        1,
        batch_id,
        capture,
        NOW,
        "a" * 64,
        "b" * 64,
        len(records),
        accepted,
        candidate,
        rejected,
        "empty" if not records else "ok" if accepted == len(records) else "mixed",
        tuple(records),
    )


def request(histories=(HISTORY,), *, kind="set", language="es"):
    return DiscoveryRequest(
        1, CURRENT, tuple(histories), DiscoveryContext("synthetic", kind, language)
    )


def empty_history():
    return batch(batch_id=HISTORY, capture=OLD)


def fails(category, req, snapshots):
    with pytest.raises(DiscoveryError) as caught:
        compare(req, snapshots)
    assert caught.value.category == category
    assert str(caught.value) == category
    assert caught.value.exit_code == (1 if category == "storage_corrupt" else 2)


def test_new_reference_known_cmt_and_candidate_set_each_emit_once():
    current = batch((record("known-alias"), record("candidate", index=1, status="candidate")))
    history = batch((record("old-alias", capture=OLD),), batch_id=HISTORY, capture=OLD)
    result = compare(request(), (current, history))
    assert result.result == "discoveries"
    assert [event.type for event in result.events] == [
        "CANDIDATE_REFERENCE_FIRST_OBSERVED",
        "SET_REFERENCE_FIRST_OBSERVED",
    ]
    assert result.events[0].cmt_id is None
    assert result.events[1].cmt_id == CMT_ID
    assert result.counts.to_dict() == {
        "batches": 2,
        "observations": 3,
        "current_observations": 2,
        "historical_observations": 1,
        "current_references": 2,
        "historical_references": 1,
        "events": 2,
    }
    output = result.to_dict()
    encoded = canonical_json(output)
    for unwanted in ("product_new", "launch", "run_id", "duration", "first_persisted_at"):
        assert unwanted not in encoded
    assert all(event.first_observed_in_window_at == NOW for event in result.events)
    assert output["window"]["history"][0]["scope_evidence"] == "records_verified"


@pytest.mark.parametrize("status", ["accepted", "candidate"])
def test_seen_union_and_candidate_to_accepted_suppress_novelty(status):
    historical = batch((record(capture=OLD, status=status),), batch_id=HISTORY, capture=OLD)
    empty = batch(batch_id=EMPTY, capture="2026-01-02T00:00:00.000000Z")
    result = compare(request((EMPTY, HISTORY)), (empty, batch((record(),)), historical))
    assert result.result == "no_discoveries" and not result.events
    assert result.history_batch_ids == tuple(sorted((EMPTY, HISTORY)))


def test_metadata_changes_across_captures_and_window_scope():
    historical = batch((record(capture=OLD),), batch_id=HISTORY, capture=OLD)
    changed = replace(
        record().observation,
        name="Changed",
        release_date="2026-02-01",
        provider_updated_at="2026-01-02T00:00:00.000000Z",
    )
    current = batch((replace(record(), observation=changed),))
    assert not compare(request(), (current, historical)).events
    assert len(compare(request(), (current, empty_history())).events) == 1


@pytest.mark.parametrize("kind", ["card", "sealed"])
def test_accepted_other_kinds_seen_and_only_new_candidates_emit(kind):
    historical = batch((record(capture=OLD, kind=kind),), batch_id=HISTORY, capture=OLD)
    current = batch(
        (
            record(kind=kind, status="candidate"),
            record("accepted-new", index=1, kind=kind),
            record("candidate-new", index=2, kind=kind, status="candidate"),
        )
    )
    result = compare(request(kind=kind), (current, historical))
    assert len(result.events) == 1 and result.events[0].reference.external_id == "candidate-new"
    assert result.counts.current_references == 3


def test_identical_duplicates_collapse_with_all_indexes_but_counts_preserved():
    current = batch((record(), record(index=1)))
    result = compare(request(), (current, empty_history()))
    assert len(result.events) == 1
    assert result.events[0].current_record_indexes == (0, 1)
    assert result.counts.current_observations == 2 and result.counts.current_references == 1


@pytest.mark.parametrize("change", ["name", "status", "target", "date"])
@pytest.mark.parametrize("baseline", [False, True])
def test_same_batch_contradictions_fail_even_baseline(change, baseline):
    second = record(index=1)
    if change == "name":
        second = replace(second, observation=replace(second.observation, name="Other"))
    if change == "status":
        second = record(index=1, status="candidate")
    if change == "target":
        second = replace(second, cmt_id=HISTORY)
    if change == "date":
        second = replace(second, observation=replace(second.observation, release_date="2026-03-01"))
    current = batch((record(), second))
    fails(
        "contradictory_snapshot",
        request(() if baseline else (HISTORY,)),
        (current,) if baseline else (current, empty_history()),
    )


def test_baseline_empty_and_explicit_empty_have_distinct_semantics():
    current = batch((record(),))
    baseline = compare(request(()), (current,))
    assert baseline.result == "baseline" and not baseline.events
    explicit = compare(request(), (current, empty_history()))
    assert explicit.result == "discoveries"
    assert explicit.history[0].scope_evidence == "request_attested_empty"
    empty = compare(request(), (batch(), empty_history()))
    assert empty.result == "no_discoveries" and not empty.events
    assert empty.current.scope_evidence == "request_attested_empty"


@pytest.mark.parametrize("language", [None, "en"])
def test_language_null_is_exact_and_mixed_context_fails(language):
    current = batch((record(language=language),))
    fails("context_mismatch", request(), (current, empty_history()))
    assert compare(request(language=language), (current, empty_history())).events


@pytest.mark.parametrize("part,value", [("namespace", "other"), ("kind", "sealed")])
def test_context_fields_exact(part, value):
    obs = observation(kind=value if part == "kind" else "set")
    if part == "namespace":
        obs = replace(obs, reference=replace(obs.reference, namespace=value))
    fails(
        "context_mismatch",
        request(),
        (batch((replace(record(), observation=obs),)), empty_history()),
    )


def test_variant_is_full_identity():
    historical = batch(
        (record(kind="card", variant="normal", capture=OLD),), batch_id=HISTORY, capture=OLD
    )
    current = batch((record(kind="card", variant="holo", status="candidate"),))
    assert len(compare(request(kind="card"), (current, historical)).events) == 1


@pytest.mark.parametrize("capture", [NOW, "2026-01-04T00:00:00.000000Z"])
def test_history_must_be_strictly_earlier(capture):
    fails("chronology", request(), (batch(), batch(batch_id=HISTORY, capture=capture)))


def test_selected_set_missing_extra_and_duplicate_fail():
    fails("batch_missing", request(), (batch(),))
    fails("storage_corrupt", request(()), (batch(), empty_history()))
    fails("storage_corrupt", request(), (batch(), empty_history(), empty_history()))
    fails("storage_corrupt", request(), [batch(), empty_history()])


@pytest.mark.parametrize("historical", [False, True])
def test_rejected_evidence_fails_globally(historical):
    rejection = SnapshotRecord(0, "rejected", "invalid_field", None, None)
    if historical:
        snapshots = (batch(), batch((rejection,), batch_id=HISTORY, capture=OLD))
    else:
        snapshots = (batch((rejection,)), empty_history())
    fails("incomplete_evidence", request(), snapshots)


def test_deterministic_replay_history_permutation_and_exact_hashes():
    current = batch((record(),))
    extra = batch(batch_id=EMPTY, capture=OLD)
    req = request((EMPTY, HISTORY))
    first = compare(req, (current, empty_history(), extra))
    second = compare(request((HISTORY, EMPTY)), (extra, current, empty_history()))
    assert first.to_dict() == second.to_dict()
    payload = {
        "identity_version": 1,
        "request": replace(req, history_batch_ids=(HISTORY, EMPTY)).to_dict(),
        "snapshots": [
            snapshot_dict(b)
            for b in sorted((current, empty_history(), extra), key=lambda b: b.batch_id)
        ],
    }
    assert (
        first.comparison_id
        == "cmp1:" + hashlib.sha256(canonical_json(payload).encode("ascii")).hexdigest()
    )
    event = first.events[0]
    identity = {
        "identity_version": 1,
        "type": event.type,
        "context": req.context.to_dict(),
        "reference": {
            "namespace": "synthetic",
            "kind": "set",
            "external_id": "new",
            "language": "es",
            "variant": "unknown",
        },
        "current_batch_id": CURRENT,
        "captured_at": NOW,
    }
    assert (
        event.event_id
        == "evt1:" + hashlib.sha256(canonical_json(identity).encode("ascii")).hexdigest()
    )
    one_history = compare(request(), (current, empty_history()))
    assert one_history.events[0].event_id == event.event_id
    assert one_history.comparison_id != first.comparison_id


def test_hash_metadata_persistence_time_and_capture_sensitivity():
    current = batch((record(),))
    original = compare(request(), (current, empty_history()))
    persisted = replace(current, first_persisted_at="2026-01-05T00:00:00.000000Z")
    assert compare(request(), (persisted, empty_history())).to_dict() == original.to_dict()
    changed = replace(current, fingerprint="c" * 64)
    assert compare(request(), (changed, empty_history())).comparison_id != original.comparison_id
    changed = replace(
        current, records=(replace(record(), observation=replace(observation(), name="Changed")),)
    )
    changed_result = compare(request(), (changed, empty_history()))
    assert changed_result.comparison_id != original.comparison_id
    assert changed_result.events[0].event_id == original.events[0].event_id
    later = "2026-01-04T00:00:00.000000Z"
    changed = replace(current, captured_at=later, records=(record(capture=later),))
    assert (
        compare(request(), (changed, empty_history())).events[0].event_id
        != original.events[0].event_id
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("version", True),
        ("input_version", 2),
        ("resolver_version", False),
        ("batch_id", "bad"),
        ("captured_at", "2026-01-03T00:00:00Z"),
        ("first_persisted_at", None),
        ("fingerprint", "A" * 64),
        ("context_fingerprint", "g" * 64),
        ("input_count", True),
        ("accepted_count", -1),
        ("candidate_count", 1),
        ("rejected_count", 1),
        ("result", "mixed"),
        ("records", []),
        ("input_count", 2),
    ],
)
def test_snapshot_metadata_forgery(field, value):
    fails(
        "storage_corrupt",
        request(),
        (replace(batch((record(),)), **{field: value}), empty_history()),
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"index": True},
        {"index": 1},
        {"status": "bad"},
        {"category": "invalid_field"},
        {"cmt_id": None},
        {"observation": None},
        {"observation": {}},
    ],
)
def test_record_forgery(changes):
    forged = replace(record(), **changes)
    with pytest.raises(DiscoveryError, match="storage_corrupt"):
        validate_snapshot(batch((forged,)))


@pytest.mark.parametrize(
    "changes",
    [
        {"provenance": "observed"},
        {"kind": "sealed"},
        {"captured_at": OLD},
        {"name": ""},
        {"name": "bad\nname"},
        {"release_date": "2026-02-30"},
        {"card_number": "001"},
        {"provider_updated_at": "2026-01-01T01:00:00+01:00"},
        {"reference": {}},
        {"set_reference": {}},
    ],
)
def test_observation_forgery(changes):
    with pytest.raises(DiscoveryError, match="storage_corrupt"):
        validate_snapshot(
            batch((replace(record(), observation=replace(observation(), **changes)),))
        )


def test_candidate_and_rejection_shape_forgery():
    for bad in (
        replace(record(status="candidate"), category="invalid_field"),
        replace(record(status="candidate"), category=None),
        replace(record(status="candidate"), cmt_id=CMT_ID),
        SnapshotRecord(0, "rejected", "invalid_field", None, observation()),
        SnapshotRecord(0, "rejected", "arbitrary-secret", None, None),
    ):
        with pytest.raises(DiscoveryError, match="storage_corrupt"):
            validate_snapshot(batch((bad,)))


def test_snapshot_missing_attribute_and_non_dataclass_fail_safely():
    for value in ({}, object.__new__(BatchSnapshot)):
        with pytest.raises(DiscoveryError, match="storage_corrupt"):
            validate_snapshot(value)


@pytest.mark.parametrize(
    "kind,language,variant,status,category,valid",
    [
        ("sealed", None, "unknown", "accepted", None, False),
        ("card", "es", "unknown", "accepted", None, False),
        ("set", "es", "unknown", "candidate", "unknown_variant", False),
        ("card", "es", "normal", "candidate", "unknown_variant", False),
        ("card", "es", "unknown", "candidate", "unknown_variant", True),
        ("card", None, "unknown", "candidate", "unknown_variant", True),
        ("set", None, "unknown", "candidate", "unknown_language", False),
        ("sealed", "es", "unknown", "candidate", "unknown_language", False),
        ("card", None, "unknown", "candidate", "unknown_language", False),
        ("card", None, "normal", "candidate", "unknown_language", True),
        ("sealed", None, "unknown", "candidate", "unknown_language", True),
        ("card", "es", "unknown", "candidate", "missing_binding", False),
        ("card", None, "unknown", "candidate", "missing_binding", False),
        ("card", None, "normal", "candidate", "missing_binding", False),
        ("sealed", None, "unknown", "candidate", "missing_binding", False),
        ("card", "es", "normal", "candidate", "missing_binding", True),
        ("sealed", "es", "unknown", "candidate", "missing_binding", True),
        ("set", None, "unknown", "candidate", "missing_binding", True),
    ],
)
def test_frozen_status_category_known_facts(kind, language, variant, status, category, valid):
    row = replace(
        record(kind=kind, language=language, variant=variant, status=status), category=category
    )
    snapshot = batch((row,))
    if valid:
        assert validate_snapshot(snapshot) == snapshot
    else:
        with pytest.raises(DiscoveryError, match="storage_corrupt"):
            validate_snapshot(snapshot)


@pytest.mark.parametrize(
    "kind,language,variant,original_category",
    [
        ("card", "es", "unknown", "unknown_variant"),
        ("card", None, "unknown", "unknown_variant"),
        ("card", None, "normal", "unknown_language"),
        ("sealed", None, "unknown", "unknown_language"),
    ],
)
def test_stored_candidate_category_tampering_rejects_missing_binding(
    tmp_path, kind, language, variant, original_category
):
    import sqlite3
    from contextlib import closing

    from card_market_tracker.catalog.manifest import Manifest
    from card_market_tracker.persistence import sqlite_repository as storage
    from card_market_tracker.persistence.application import build_batch

    path = tmp_path / "category-tampering.db"
    value = build_batch(
        CURRENT,
        NOW,
        (observation(kind=kind, language=language, variant=variant),),
        Manifest((), ()),
    )
    assert value.records[0].category == original_category
    storage.persist(path, value)
    (original,) = storage.read_snapshots(path, (CURRENT,))
    assert original.records[0].category == original_category
    # This remains a known SQL category; business validation must detect that
    # the frozen evidence could never produce it under resolver version 1.
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute(
            "UPDATE records SET category = ? WHERE batch_id = ? AND record_index = ?",
            ("missing_binding", CURRENT, 0),
        )
    before_read = path.read_bytes()
    with pytest.raises(DiscoveryError, match="storage_corrupt"):
        storage.read_snapshots(path, (CURRENT,))
    assert path.read_bytes() == before_read


@pytest.mark.parametrize(
    "changes",
    [
        {"set_reference": None},
        {"card_number": None},
        {"set_reference": ExternalReference("synthetic", "sealed", "bad", "es")},
    ],
)
def test_card_parent_and_number_business_validation(changes):
    row = record(kind="card")
    with pytest.raises(DiscoveryError, match="storage_corrupt"):
        validate_snapshot(batch((replace(row, observation=replace(row.observation, **changes)),)))


def test_rejection_target_and_category_forgery():
    for row in (
        SnapshotRecord(0, "rejected", "invalid_field", CMT_ID, None),
        SnapshotRecord(0, "rejected", None, None, None),
    ):
        with pytest.raises(DiscoveryError, match="storage_corrupt"):
            validate_snapshot(batch((row,)))


def test_forged_nested_nonjson_cycles_are_bounded():
    poisoned = []
    poisoned.append(poisoned)
    for name in (poisoned, {"a": "b"}):
        with pytest.raises(DiscoveryError) as caught:
            validate_snapshot(
                batch((replace(record(), observation=replace(observation(), name=name)),))
            )
        assert caught.value.category in ("input_limit", "storage_corrupt")


def test_limits_and_all_33000_records_are_supported():
    rows = tuple(record(index=index) for index in range(1000))
    current = batch(rows)
    histories = tuple(
        batch(
            tuple(record(index=index, capture=OLD) for index in range(1000)),
            batch_id=f"{number:08x}-1111-4111-8111-111111111111",
            capture=OLD,
        )
        for number in range(1, 33)
    )
    result = compare(request(tuple(b.batch_id for b in histories)), (current, *histories))
    assert result.counts.observations == 33000 and not result.events
    with pytest.raises(DiscoveryError, match="input_limit"):
        validate_snapshot(
            replace(
                current, records=(*rows, record(index=1000)), input_count=1001, accepted_count=1001
            )
        )
    with pytest.raises(DiscoveryError, match="input_limit"):
        validate_snapshot(replace(current, input_count=1001))
    with pytest.raises(DiscoveryError, match="input_limit"):
        validate_snapshot(
            batch((replace(record(), observation=replace(observation(), name="x" * 1025)),))
        )
    fails("input_limit", request(), tuple(batch() for _ in range(34)))


def test_max_1000_events_and_stable_order():
    current = batch(tuple(record(f"new-{index:04}", index=index) for index in range(1000)))
    result = compare(request(), (current, empty_history()))
    assert len(result.events) == 1000
    assert [e.reference.external_id for e in result.events] == sorted(
        e.reference.external_id for e in result.events
    )


def test_comparator_import_has_no_sqlite_provider_or_persistence_dependency():
    script = (
        "import card_market_tracker.discovery; import sys,json; "
        "print(json.dumps(sorted(m for m in sys.modules "
        "if m=='sqlite3' or '.adapters' in m or '.persistence' in m)))"
    )
    result = subprocess.run(
        [sys.executable, "-c", script], check=True, capture_output=True, text=True
    )
    assert json.loads(result.stdout) == []
