"""P4b persisted synthetic windows and the unchanged approved real capture."""

import json
import socket
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import pytest

from card_market_tracker.catalog.ingestion import ExternalReference, Observation, RecordError
from card_market_tracker.discovery.errors import DiscoveryError
from card_market_tracker.discovery.scoped_comparison import compare
from card_market_tracker.discovery.scoped_input import parse_request
from card_market_tracker.discovery.scoped_models import ScopedCapture
from card_market_tracker.discovery.scoped_snapshot import validate_scoped_snapshot
from card_market_tracker.persistence.application import build_batch
from card_market_tracker.persistence.capture import persist_bundle, persist_capture
from card_market_tracker.persistence.sqlite_repository import (
    backup as backup_database,
)
from card_market_tracker.persistence.sqlite_repository import (
    read_scoped_snapshots,
)
from card_market_tracker.persistence.sqlite_repository import (
    restore as restore_database,
)
from card_market_tracker.pinned_repository import approved_bundle_document

OLD = "2026-01-01T00:00:00.000000Z"
MIDDLE = "2026-01-02T00:00:00.000000Z"
NOW = "2026-01-03T00:00:00.000000Z"
TARGET = "f9743b79-20e3-4815-98d3-bb06f0c8195f"
OTHER = "74105a60-375c-4780-a355-88e241982944"
EMPTY_MANIFEST = {"version": 1, "entities": [], "bindings": []}


def observation(
    external_id="new",
    *,
    captured_at=NOW,
    namespace="synthetic_scope",
    kind="set",
    language="es",
    variant="unknown",
    name="Invented name",
):
    ref = ExternalReference(namespace, kind, external_id, language, variant)
    parent = ExternalReference(namespace, "set", "parent", language) if kind == "card" else None
    return Observation(
        kind,
        ref,
        name,
        set_reference=parent,
        card_number="001" if kind == "card" else None,
        captured_at=captured_at,
        provenance="synthetic",
    )


def curated(*names, namespace="synthetic_scope", target=TARGET):
    return {
        "version": 1,
        "entities": [{"cmt_id": target, "kind": "set"}],
        "bindings": [
            {
                "reference": {
                    "namespace": namespace,
                    "kind": "set",
                    "external_id": name,
                    "language": "es",
                    "variant": "unknown",
                },
                "cmt_id": target,
                "reason": "Explicit synthetic test decision.",
            }
            for name in names
        ],
    }


def seed(
    path,
    names=("new",),
    *,
    capture=NOW,
    selector="unit",
    paths=("synthetic/a",),
    namespace="synthetic_scope",
    kind="set",
    language="es",
    items=None,
    manifest=None,
    outcome="complete",
    completed=None,
    outside=(),
    token=None,
):
    if items is None:
        items = tuple(
            observation(
                name, captured_at=capture, namespace=namespace, kind=kind, language=language
            )
            for name in names
        )
    all_items = (*items, *outside)
    batch = build_batch(token or str(uuid4()), capture, all_items, manifest or EMPTY_MANIFEST)
    unit = {
        "namespace": namespace,
        "kind": kind,
        "language": language,
        "selector": selector,
        "selected": list(paths),
        "completed": list(paths if completed is None else completed),
        "record_indexes": list(range(len(items))),
    }
    units = [unit]
    if outside:
        units.append(
            {
                **unit,
                "selector": "outside",
                "record_indexes": list(range(len(items), len(all_items))),
            }
        )
    scope = {
        "version": 1,
        "acquired_at": capture,
        "captured_at": capture,
        "outcome": outcome,
        "units": units,
    }
    persist_capture(path, batch, scope)
    return batch, scope


def request(
    current,
    histories=(),
    *,
    selector="unit",
    namespace="synthetic_scope",
    kind="set",
    language="es",
):
    return parse_request(
        {
            "version": 2,
            "context": {"namespace": namespace, "kind": kind, "language": language},
            "current": {"batch_id": current, "selector": selector},
            "history": [{"batch_id": token, "selector": selector} for token in histories],
        }
    )


def result(path, req):
    return compare(req, read_scoped_snapshots(path, req)).to_dict()


def fails(category, action):
    with pytest.raises(DiscoveryError) as caught:
        action()
    assert caught.value.category == category
    assert str(caught.value) == category


def test_synthetic_baseline_positive_candidate_and_accepted_new_alias(tmp_path, monkeypatch):
    path = tmp_path / "history.db"
    history, _ = seed(path, ("known",), capture=OLD, manifest=curated("known"))
    current, _ = seed(path, ("known", "alias", "candidate"), manifest=curated("known", "alias"))
    monkeypatch.setattr(socket, "socket", lambda *args, **kwargs: pytest.fail("network attempted"))
    before = path.read_bytes()
    baseline = result(path, request(current.batch_id))
    assert baseline["result"] == "baseline" and baseline["events"] == []
    payload = result(path, request(current.batch_id, (history.batch_id,)))
    assert payload["result"] == "discoveries"
    assert [event["type"] for event in payload["events"]] == [
        "SET_REFERENCE_FIRST_OBSERVED",
        "CANDIDATE_REFERENCE_FIRST_OBSERVED",
    ]
    assert payload["events"][0]["cmt_id"] == TARGET
    assert payload["events"][1]["category"] == "missing_binding"
    assert payload["counts"] == {
        "validated_batches": 2,
        "validated_records": 4,
        "current_selected_records": 3,
        "historical_selected_records": 1,
        "current_selected_references": 3,
        "historical_selected_references": 1,
        "events": 2,
    }
    assert payload["current"]["evidence_state"] == "producer_declared"
    assert (
        payload["current"]["scope_semantics"]["semantics"]["method"] == "generic_synthetic_capture"
    )
    assert path.read_bytes() == before


def test_union_candidate_then_accepted_and_binding_metadata_changes(tmp_path):
    path = tmp_path / "union.db"
    first, _ = seed(path, ("seen",), capture=OLD)
    empty, _ = seed(path, (), capture=MIDDLE)
    current, _ = seed(
        path,
        capture=NOW,
        items=(replace(observation("seen"), name="Updated", release_date="2026-01-01"),),
        manifest=curated("seen"),
    )
    payload = result(path, request(current.batch_id, (first.batch_id, empty.batch_id)))
    assert payload["result"] == "no_discoveries" and payload["events"] == []
    changed, _ = seed(path, ("seen",), capture=MIDDLE, manifest=curated("seen", target=OTHER))
    assert result(path, request(current.batch_id, (changed.batch_id,)))["events"] == []


def test_complete_empty_current_and_history_do_not_emit_absence_events(tmp_path):
    path = tmp_path / "empty.db"
    history, _ = seed(path, ("a",), capture=OLD)
    empty, _ = seed(path, (), capture=MIDDLE)
    current, _ = seed(path, ("a",))
    assert result(path, request(empty.batch_id))["result"] == "baseline"
    assert result(path, request(empty.batch_id, (history.batch_id,)))["result"] == "no_discoveries"
    assert result(path, request(current.batch_id, (empty.batch_id,)))["result"] == "discoveries"
    assert (
        result(path, request(current.batch_id, (history.batch_id, empty.batch_id)))["events"] == []
    )


def test_exact_selected_unit_counts_outside_excluded_original_indexes(tmp_path):
    path = tmp_path / "units.db"
    # The first unit is outside; selected unit begins at index 1.
    current, scope = seed(path, ("outside-reference",), outside=(observation("selected"),))
    req = request(current.batch_id, selector="outside")
    payload = result(path, req)
    assert payload["counts"]["validated_records"] == 2
    assert payload["counts"]["current_selected_records"] == 1
    assert payload["current"]["scope"]["record_indexes"] == [1]
    earlier, _ = seed(path, (), capture=OLD, selector="outside")
    payload = result(path, request(current.batch_id, (earlier.batch_id,), selector="outside"))
    assert payload["events"][0]["reference"]["external_id"] == "selected"
    assert payload["events"][0]["evidence"]["current_record_indexes"] == [1]
    assert len(payload["events"]) == 1
    assert scope["units"][0]["record_indexes"] == [0]


@pytest.mark.parametrize(
    "changes",
    [
        {"selector": "missing"},
        {"namespace": "other"},
        {"kind": "card"},
        {"language": None},
    ],
)
def test_no_matching_unit_is_error_not_empty(tmp_path, changes):
    path = tmp_path / "selection.db"
    current, _ = seed(path)
    fails("unit_missing", lambda: result(path, request(current.batch_id, **changes)))


@pytest.mark.parametrize("scope_change", [{"selector": "other"}, {"paths": ("synthetic/other",)}])
def test_different_selector_or_path_set_not_comparable(tmp_path, scope_change):
    path = tmp_path / "scope.db"
    history, _ = seed(path, (), capture=OLD, **scope_change)
    current, _ = seed(path)
    req = request(current.batch_id, (history.batch_id,))
    if "selector" in scope_change:
        document = req.to_dict()
        document["history"][0]["selector"] = "other"
        req = parse_request(document)
    fails("scope_mismatch", lambda: result(path, req))


def test_path_order_history_order_replay_and_restore_preserve_identity(tmp_path):
    path = tmp_path / "stable.db"
    earlier, _ = seed(path, (), capture=OLD, paths=("synthetic/b", "synthetic/a"))
    equal_history, _ = seed(path, ("old",), capture=OLD, paths=("synthetic/a", "synthetic/b"))
    current, scope = seed(path, ("new",), paths=("synthetic/a", "synthetic/b"))
    req = request(current.batch_id, (earlier.batch_id, equal_history.batch_id))
    payload = result(path, req)
    reverse = replace(req, history=tuple(reversed(req.history)))
    assert result(path, reverse) == payload
    scope["units"][0]["selected"].reverse()
    scope["units"][0]["completed"].reverse()
    assert persist_capture(path, current, scope).result == "replay"
    assert result(path, req) == payload
    backup = tmp_path / "backup.db"
    restored = tmp_path / "restored.db"
    backup_database(path, backup)
    restore_database(backup, restored)
    assert result(restored, req) == payload
    # Current appearance identity ignores the chosen historical window.
    subset = result(path, request(current.batch_id, (earlier.batch_id,)))
    assert subset["comparison_id"] != payload["comparison_id"]
    assert subset["events"][0]["event_id"] == payload["events"][0]["event_id"]
    assert payload["comparison_id"].startswith("cmp2:")
    assert payload["events"][0]["event_id"].startswith("evt2:")


@pytest.mark.parametrize("capture", [NOW, "2026-01-04T00:00:00.000000Z"])
def test_history_equal_or_future_is_chronology_failure(tmp_path, capture):
    path = tmp_path / "time.db"
    history, _ = seed(path, (), capture=capture)
    current, _ = seed(path)
    fails("chronology", lambda: result(path, request(current.batch_id, (history.batch_id,))))


@pytest.mark.parametrize(
    "outcome,completed,names",
    [
        ("partial", (), ("new",)),
        ("failed", (), ()),
        ("partial", ("synthetic/a",), ("new",)),
    ],
)
def test_partial_failed_are_never_complete_even_baseline(tmp_path, outcome, completed, names):
    path = tmp_path / "incomplete.db"
    current, _ = seed(path, names, outcome=outcome, completed=completed)
    fails("incomplete_evidence", lambda: result(path, request(current.batch_id)))


def test_selected_rejection_is_not_empty_but_other_unit_rejection_is_explicit_scope(tmp_path):
    path = tmp_path / "rejected.db"
    current, _ = seed(path, items=(RecordError(0, "invalid_field"),))
    fails("incomplete_evidence", lambda: result(path, request(current.batch_id)))
    separate, _ = seed(
        path, items=(observation("valid"),), outside=(RecordError(1, "invalid_field"),)
    )
    payload = result(path, request(separate.batch_id))
    assert payload["counts"]["validated_records"] == 2
    assert payload["counts"]["current_selected_records"] == 1
    assert payload["result"] == "baseline"


def test_identical_duplicates_collapse_preserving_indexes_and_contradiction_fails(tmp_path):
    path = tmp_path / "duplicates.db"
    old, _ = seed(path, (), capture=OLD)
    current, _ = seed(path, ("duplicate", "duplicate"), manifest=curated("duplicate"))
    payload = result(path, request(current.batch_id, (old.batch_id,)))
    assert payload["counts"]["current_selected_records"] == 2
    assert payload["counts"]["current_selected_references"] == 1
    assert payload["events"][0]["evidence"]["current_record_indexes"] == [0, 1]
    conflict, _ = seed(
        path, items=(observation("duplicate"), observation("duplicate", name="Different"))
    )
    fails("contradictory_snapshot", lambda: result(path, request(conflict.batch_id)))


@pytest.mark.parametrize("kind,language", [("card", "es"), ("sealed", None)])
def test_candidates_preserve_text_card_number_unknown_variant_and_null_language(
    tmp_path, kind, language
):
    path = tmp_path / "candidate.db"
    old, _ = seed(path, (), capture=OLD, kind=kind, language=language)
    current, _ = seed(path, kind=kind, language=language)
    payload = result(path, request(current.batch_id, (old.batch_id,), kind=kind, language=language))
    event = payload["events"][0]
    assert event["type"] == "CANDIDATE_REFERENCE_FIRST_OBSERVED"
    assert event["reference"]["language"] == language
    assert event["reference"]["variant"] == "unknown"
    snapshots = read_scoped_snapshots(path, request(current.batch_id, kind=kind, language=language))
    if kind == "card":
        assert snapshots[0].snapshot.records[0].observation.card_number == "001"


@pytest.mark.parametrize(
    "kind,namespace,external_id",
    [
        ("card", "tcgdex", "synthetic-card-001"),
        ("sealed", "curated", "synthetic-box"),
    ],
)
def test_accepted_non_set_does_not_generate_event(tmp_path, kind, namespace, external_id):
    path = tmp_path / "non-set.db"
    manifest = json.loads((Path(__file__).parent / "fixtures/synthetic_manifest.json").read_text())
    parent = ExternalReference("tcgdex", "set", "synthetic-set", "es")
    obs = observation(
        external_id,
        namespace=namespace,
        kind=kind,
        variant="normal" if kind == "card" else "unknown",
    )
    if kind == "card":
        obs = replace(obs, set_reference=parent)
    current, _ = seed(path, items=(obs,), manifest=manifest, namespace=namespace, kind=kind)
    old, _ = seed(path, (), capture=OLD, namespace=namespace, kind=kind)
    payload = result(
        path, request(current.batch_id, (old.batch_id,), namespace=namespace, kind=kind)
    )
    assert current.records[0].status == "accepted"
    assert payload["result"] == "no_discoveries" and payload["events"] == []


@pytest.mark.parametrize("curated_sets", [False, True])
@pytest.mark.parametrize(
    "kind,language,selector,index",
    [
        ("set", "es", "swsh3", 0),
        ("set", "en", "swsh3", 1),
        ("card", "es", "swsh3-136", 2),
        ("card", "en", "swsh3-136", 3),
    ],
)
def test_four_real_units_each_baseline_at_original_capture_only(
    tmp_path,
    curated_sets,
    kind,
    language,
    selector,
    index,
):
    path = tmp_path / "pinned.db"
    manifest = curated("swsh3", namespace="tcgdex_repository") if curated_sets else EMPTY_MANIFEST
    if curated_sets:
        manifest["bindings"].append(
            {
                **manifest["bindings"][0],
                "reference": {**manifest["bindings"][0]["reference"], "language": "en"},
            }
        )
    token = str(uuid4())
    persist_bundle(path, approved_bundle_document(), token, manifest)
    payload = result(
        path,
        request(
            token, namespace="tcgdex_repository", kind=kind, language=language, selector=selector
        ),
    )
    assert payload["result"] == "baseline" and payload["events"] == []
    assert payload["counts"]["validated_records"] == 4
    assert payload["counts"]["current_selected_records"] == 1
    assert payload["current"]["scope"]["record_indexes"] == [index]
    assert payload["current"]["evidence_state"] == "verified_local_pinned_bundle"
    assert payload["current"]["captured_at"] == approved_bundle_document()["captured_at"]


def test_same_real_package_two_import_tokens_cannot_form_temporal_history(tmp_path):
    path = tmp_path / "real-time.db"
    tokens = (str(uuid4()), str(uuid4()))
    for token in tokens:
        persist_bundle(path, approved_bundle_document(), token, EMPTY_MANIFEST)
    req = request(tokens[1], (tokens[0],), namespace="tcgdex_repository", selector="swsh3")
    fails("chronology", lambda: result(path, req))


def test_mixed_real_synthetic_window_rejected_without_provenance_normalization(tmp_path):
    path = tmp_path / "families.db"
    token = str(uuid4())
    persist_bundle(path, approved_bundle_document(), token, EMPTY_MANIFEST)
    fake, _ = seed(path, (), capture=OLD, namespace="tcgdex_repository", selector="swsh3")
    req = request(token, (fake.batch_id,), namespace="tcgdex_repository", selector="swsh3")
    fails("scope_mismatch", lambda: result(path, req))


def test_constructor_replace_and_receipt_copy_do_not_grant_storage_authority(tmp_path):
    path = tmp_path / "authority.db"
    current, _ = seed(path)
    req = request(current.batch_id)
    (valid,) = read_scoped_snapshots(path, req)
    forged = ScopedCapture(
        valid.snapshot,
        valid.mode,
        valid.evidence_state,
        valid.scope_json,
        valid.capture_fingerprint,
    )
    for invalid in (forged, replace(valid)):
        fails("unsupported_evidence", lambda invalid=invalid: compare(req, (invalid,)))
    fails("storage_corrupt", lambda: compare(req, (object.__new__(ScopedCapture),)))
    changed_row = replace(
        valid.snapshot.records[0],
        observation=replace(valid.snapshot.records[0].observation, name="Changed"),
    )
    forged = replace(valid, snapshot=replace(valid.snapshot, records=(changed_row,)))
    object.__setattr__(forged, "_storage_authority", valid._storage_authority)
    fails("unsupported_evidence", lambda: compare(req, (forged,)))


def test_public_compare_revalidates_window_members_and_request(tmp_path):
    path = tmp_path / "boundary.db"
    current, _ = seed(path)
    other, _ = seed(path, (), capture=OLD)
    req = request(current.batch_id)
    captures = read_scoped_snapshots(path, request(current.batch_id, (other.batch_id,)))
    current_capture = next(c for c in captures if c.snapshot.batch_id == current.batch_id)
    for invalid, category in (
        ([], "storage_corrupt"),
        ((object(),), "storage_corrupt"),
        ((), "batch_missing"),
        (captures, "storage_corrupt"),
        ((current_capture, current_capture), "storage_corrupt"),
        ((current_capture,) * 34, "input_limit"),
    ):
        fails(category, lambda invalid=invalid: compare(req, invalid))
    fails("unsupported_version", lambda: compare(replace(req, version=True), (current_capture,)))


@pytest.mark.parametrize(
    "changes",
    [
        {"version": True},
        {"input_version": 2},
        {"resolver_version": 0},
        {"input_count": True},
        {"input_count": 99},
        {"accepted_count": -1},
        {"fingerprint": "not-a-digest"},
        {"context_fingerprint": "A" * 64},
        {"captured_at": "2026-01-01"},
        {"first_persisted_at": NOW.replace("Z", "+00:00")},
        {"records": []},
        {"result": "empty"},
        {"rejected_count": 1},
    ],
)
def test_versioned_snapshot_validator_independently_rejects_forged_metadata(tmp_path, changes):
    path = tmp_path / "snapshot.db"
    current, _ = seed(path)
    (capture,) = read_scoped_snapshots(path, request(current.batch_id))
    fails(
        "storage_corrupt",
        lambda: validate_scoped_snapshot(
            replace(capture.snapshot, **changes), provenance="synthetic"
        ),
    )


def test_snapshot_validator_does_not_convert_provenance_and_rejects_forged_records(tmp_path):
    path = tmp_path / "snapshot-record.db"
    current, _ = seed(path)
    (capture,) = read_scoped_snapshots(path, request(current.batch_id))
    snapshot = capture.snapshot
    row = snapshot.records[0]
    for changed in (
        replace(row, index=True),
        replace(row, status="accepted", cmt_id=TARGET, category="missing_binding"),
        replace(row, category="unknown_variant"),
        replace(row, cmt_id=TARGET),
        replace(row, observation=replace(row.observation, provenance="observed")),
        replace(row, observation=replace(row.observation, provenance="documented")),
        replace(row, observation=None),
    ):
        fails(
            "storage_corrupt",
            lambda changed=changed: validate_scoped_snapshot(
                replace(snapshot, records=(changed,)), provenance="synthetic"
            ),
        )
    fails("storage_corrupt", lambda: validate_scoped_snapshot(snapshot, provenance="documented"))


def test_unselected_unit_contradiction_cannot_be_hidden_by_empty_selected_unit(tmp_path):
    path = tmp_path / "outside-conflict.db"
    current, _ = seed(
        path,
        (),
        outside=(observation("same", name="One"), observation("same", name="Two")),
    )
    fails("contradictory_snapshot", lambda: result(path, request(current.batch_id)))


def test_global_event_budget_failure_never_returns_truncated_success(tmp_path, monkeypatch):
    from card_market_tracker.discovery import scoped_comparison

    path = tmp_path / "event-budget.db"
    old, _ = seed(path, (), capture=OLD)
    current, _ = seed(path, ("one", "two"))
    req = request(current.batch_id, (old.batch_id,))
    assert len(result(path, req)["events"]) == 2
    monkeypatch.setattr(scoped_comparison, "MAX_EVENTS", 1)
    fails("input_limit", lambda: result(path, req))


def test_relevant_current_content_changes_identity_same_tokens_and_original_capture(tmp_path):
    tokens = (str(uuid4()), str(uuid4()))
    payloads = []
    for name, path in (("One", tmp_path / "one.db"), ("Two", tmp_path / "two.db")):
        old, _ = seed(path, (), capture=OLD, token=tokens[0])
        current, _ = seed(path, items=(observation("same", name=name),), token=tokens[1])
        payloads.append(result(path, request(current.batch_id, (old.batch_id,))))
    assert payloads[0]["comparison_id"] != payloads[1]["comparison_id"]
    assert payloads[0]["events"][0]["event_id"] != payloads[1]["events"][0]["event_id"]


@pytest.mark.parametrize("field", ["snapshot", "scope_json"])
def test_bounds_precede_receipt_hash_for_mutated_python_objects(tmp_path, monkeypatch, field):
    from card_market_tracker.discovery import scoped_validation

    path = tmp_path / "receipt-budget.db"
    current, _ = seed(path)
    req = request(current.batch_id)
    (capture,) = read_scoped_snapshots(path, req)
    if field == "scope_json":
        mutated = replace(capture, scope_json=" " * 1048577)
    else:
        row = capture.snapshot.records[0]
        row = replace(row, observation=replace(row.observation, name="x" * 1025))
        mutated = replace(capture, snapshot=replace(capture.snapshot, records=(row,)))
    monkeypatch.setattr(
        scoped_validation,
        "_has_storage_authority",
        lambda value: pytest.fail("receipt hash ran before bounds"),
    )
    fails("input_limit", lambda: compare(req, (mutated,)))
