"""Independent P4b QA: risk-derived persisted synthetic windows and trust boundaries.

All positive temporal transitions here are invented synthetic evidence.  Storage
receipts come only from the real reader after persist_capture/persist_bundle.
"""

import copy
import json
import socket
from dataclasses import replace
from uuid import uuid4

import pytest

from card_market_tracker import cli
from card_market_tracker.catalog.ingestion import ExternalReference, Observation, RecordError
from card_market_tracker.discovery.errors import DiscoveryError
from card_market_tracker.discovery.scoped_comparison import compare
from card_market_tracker.discovery.scoped_input import parse_request
from card_market_tracker.discovery.scoped_models import ScopedCapture
from card_market_tracker.persistence.application import build_batch
from card_market_tracker.persistence.capture import persist_bundle, persist_capture
from card_market_tracker.persistence.errors import PersistenceError
from card_market_tracker.persistence.sqlite_repository import backup, read_scoped_snapshots, restore
from card_market_tracker.pinned_repository import approved_bundle_document

NAMESPACE = "qa_synthetic"
TARGET = "f9743b79-20e3-4815-98d3-bb06f0c8195f"
EMPTY_MANIFEST = {"version": 1, "entities": [], "bindings": []}
EARLIER = "2026-10-13T00:00:00.000000Z"
LATER = "2026-10-15T00:00:00.000000Z"


def observation(external_id, captured_at, *, namespace=NAMESPACE, name=None, language="es"):
    return Observation(
        "set",
        ExternalReference(namespace, "set", external_id, language),
        name or "Invented QA " + external_id,
        captured_at=captured_at,
        provenance="synthetic",
    )


def manifest(*external_ids):
    return {
        "version": 1,
        "entities": [{"kind": "set", "cmt_id": TARGET}],
        "bindings": [
            {
                "reference": {
                    "namespace": NAMESPACE,
                    "kind": "set",
                    "external_id": external_id,
                    "language": "es",
                    "variant": "unknown",
                },
                "cmt_id": TARGET,
                "reason": "Invented QA aliases; no real identity inference",
            }
            for external_id in external_ids
        ],
    }


def seed(
    path,
    captured_at,
    items=(),
    *,
    curated=None,
    paths=("synthetic/qa/a",),
    outcome="complete",
    completed=None,
    selector="selected",
    namespace=NAMESPACE,
    language="es",
    other_indexes=(),
):
    token = str(uuid4())
    batch = build_batch(token, captured_at, tuple(items), curated or EMPTY_MANIFEST)
    selected_indexes = [index for index in range(len(items)) if index not in other_indexes]
    unit = {
        "namespace": namespace,
        "kind": "set",
        "language": language,
        "selector": selector,
        "selected": list(paths),
        "completed": list(paths if completed is None else completed),
        "record_indexes": selected_indexes,
    }
    units = [unit]
    if other_indexes:
        units.append({**unit, "selector": "unselected", "record_indexes": list(other_indexes)})
    persist_capture(
        path,
        batch,
        {
            "version": 1,
            "acquired_at": captured_at,
            "captured_at": captured_at,
            "outcome": outcome,
            "units": units,
        },
    )
    return token


def request(current, *history, namespace=NAMESPACE, language="es", selector="selected"):
    return parse_request(
        {
            "version": 2,
            "context": {"namespace": namespace, "kind": "set", "language": language},
            "current": {"batch_id": current, "selector": selector},
            "history": [{"batch_id": token, "selector": selector} for token in history],
        }
    )


def result(path, selected):
    return compare(selected, read_scoped_snapshots(path, selected)).to_dict()


def error(category, action):
    with pytest.raises((DiscoveryError, PersistenceError)) as caught:
        action()
    assert caught.value.category == category
    assert str(caught.value) == category


def test_candidate_history_and_empty_gap_are_union_not_previous_capture(tmp_path):
    path = tmp_path / "union.db"
    old = seed(path, EARLIER, [observation("seen", EARLIER)])
    gap = seed(path, "2026-10-14T00:00:00Z")
    current = seed(path, LATER, [observation("seen", LATER)], curated=manifest("seen"))
    window = result(path, request(current, gap, old))
    assert window["result"] == "no_discoveries"
    assert window["events"] == []
    assert window["counts"]["historical_selected_references"] == 1
    # Omission of the older capture genuinely changes the explicitly selected window.
    gap_only = result(path, request(current, gap))
    assert [event["type"] for event in gap_only["events"]] == ["SET_REFERENCE_FIRST_OBSERVED"]
    assert gap_only["comparison_id"] != window["comparison_id"]


def test_alias_same_target_is_new_reference_without_promoting_candidates(tmp_path):
    path = tmp_path / "aliases.db"
    old = seed(path, EARLIER, [observation("old", EARLIER)], curated=manifest("old", "alias"))
    current = seed(
        path,
        LATER,
        [observation("old", LATER), observation("alias", LATER), observation("unbound", LATER)],
        curated=manifest("old", "alias"),
    )
    output = result(path, request(current, old))
    events = {event["reference"]["external_id"]: event for event in output["events"]}
    assert set(events) == {"alias", "unbound"}
    assert events["alias"]["type"] == "SET_REFERENCE_FIRST_OBSERVED"
    assert events["alias"]["cmt_id"] == TARGET
    assert events["unbound"]["type"] == "CANDIDATE_REFERENCE_FIRST_OBSERVED"
    assert events["unbound"]["cmt_id"] is None
    assert events["unbound"]["category"] == "missing_binding"
    assert all(event["first_observed_in_window_at"] == LATER for event in events.values())


def test_duplicate_indices_original_selection_and_unselected_rejections(tmp_path):
    path = tmp_path / "selected.db"
    old = seed(path, EARLIER)
    item = observation("new", LATER)
    current = seed(path, LATER, [RecordError(0, "invalid_field"), item, item], other_indexes=(0,))
    output = result(path, request(current, old))
    assert output["counts"]["validated_records"] == 3
    assert output["counts"]["current_selected_records"] == 2
    assert output["counts"]["current_selected_references"] == 1
    assert len(output["events"]) == 1
    assert output["events"][0]["evidence"]["current_record_indexes"] == [1, 2]
    assert output["current"]["scope"]["record_indexes"] == [1, 2]


def test_contradiction_invalidates_even_baseline_but_cross_capture_edits_are_valid(tmp_path):
    path = tmp_path / "contradiction.db"
    old = seed(path, EARLIER, [observation("same", EARLIER, name="Old QA name")])
    current = seed(path, LATER, [observation("same", LATER, name="Edited QA name")])
    assert result(path, request(current, old))["result"] == "no_discoveries"
    bad = seed(
        path, LATER, [observation("same", LATER), observation("same", LATER, name="Conflict")]
    )
    error("contradictory_snapshot", lambda: result(path, request(bad)))


@pytest.mark.parametrize("outcome,completed", [("partial", ()), ("failed", ())])
def test_incomplete_empty_never_becomes_baseline(tmp_path, outcome, completed):
    path = tmp_path / "incomplete.db"
    token = seed(path, LATER, outcome=outcome, completed=completed)
    error("incomplete_evidence", lambda: result(path, request(token)))


def test_selected_rejection_is_not_empty_and_null_is_not_wildcard(tmp_path):
    path = tmp_path / "rejected.db"
    rejected = seed(path, LATER, [RecordError(0, "invalid_field")])
    error("incomplete_evidence", lambda: result(path, request(rejected)))
    null = seed(path, LATER, [observation("null", LATER, language=None)], language=None)
    assert result(path, request(null, language=None))["result"] == "baseline"
    error("unit_missing", lambda: result(path, request(null)))


def test_path_permutation_history_ties_and_backups_preserve_output(tmp_path):
    path = tmp_path / "history.db"
    paths = ("../../metadata-only-never-open", "https://invalid.example/metadata-only")
    one = seed(path, EARLIER, paths=paths)
    two = seed(path, "2026-10-13T01:00:00+01:00", paths=tuple(reversed(paths)))
    current = seed(path, LATER, [observation("new", LATER)], paths=paths)
    selected = request(current, two, one)
    before = path.read_bytes()
    output = result(path, selected)
    assert output == result(path, request(current, one, two))
    assert {item["captured_at"] for item in output["history"]} == {EARLIER}
    copied, restored = tmp_path / "backup.db", tmp_path / "restored.db"
    backup(path, copied)
    restore(copied, restored)
    assert result(restored, selected) == output
    assert path.read_bytes() == before
    assert output["comparison_id"].startswith("cmp2:")
    assert output["events"][0]["event_id"].startswith("evt2:")
    single = result(path, request(current, one))
    assert single["events"][0]["event_id"] == output["events"][0]["event_id"]
    assert single["comparison_id"] != output["comparison_id"]


@pytest.mark.parametrize("change", ["path", "selector"])
def test_scope_change_cannot_masquerade_as_new_reference(tmp_path, change):
    path = tmp_path / "scope.db"
    old = seed(path, EARLIER)
    current = seed(
        path,
        LATER,
        [observation("new", LATER)],
        paths=("synthetic/changed",) if change == "path" else ("synthetic/qa/a",),
        selector="different" if change == "selector" else "selected",
    )
    selected = request(current, old)
    if change == "selector":
        selected = replace(selected, current=replace(selected.current, selector="different"))
    error("scope_mismatch", lambda: result(path, selected))


@pytest.mark.parametrize("history_at", [LATER, "2026-10-16T00:00:00Z", "2026-10-15T01:00:00+01:00"])
def test_capture_chronology_rejects_future_and_offset_equal_time(tmp_path, history_at):
    path = tmp_path / "chronology.db"
    older_token = seed(path, history_at)
    current = seed(path, LATER)
    error("chronology", lambda: result(path, request(current, older_token)))


def test_constructor_and_copied_receipts_cannot_promote_changed_content(tmp_path):
    path = tmp_path / "authority.db"
    token = seed(path, LATER, [observation("one", LATER)])
    selected = request(token)
    (capture,) = read_scoped_snapshots(path, selected)
    constructed = ScopedCapture(
        capture.snapshot,
        capture.mode,
        capture.evidence_state,
        capture.scope_json,
        capture.capture_fingerprint,
    )
    error("unsupported_evidence", lambda: compare(selected, (constructed,)))
    # Attack the public boundary using a genuine receipt copied from an unrelated payload.
    for changes, category in (
        ({"mode": "pinned", "evidence_state": "verified_local_pinned_bundle"}, "storage_corrupt"),
        (
            {"scope_json": capture.scope_json.replace("synthetic/qa/a", "synthetic/qa/b")},
            "unsupported_evidence",
        ),
        ({"snapshot": replace(capture.snapshot, captured_at=EARLIER)}, "storage_corrupt"),
        ({"capture_fingerprint": "0" * 64}, "unsupported_evidence"),
    ):
        forged = replace(capture, **changes)
        object.__setattr__(forged, "_storage_authority", capture._storage_authority)
        error(category, lambda forged=forged: compare(selected, (forged,)))
    assert compare(selected, (copy.copy(capture),)).to_dict() == result(path, selected)


@pytest.mark.parametrize("shape", [None, [], {}, (None,), (object(),)])
def test_comparator_shapes_are_categorized_and_never_partial_success(tmp_path, shape):
    path = tmp_path / "shape.db"
    token = seed(path, LATER)
    error("storage_corrupt", lambda: compare(request(token), shape))


def test_mixed_families_rejected_using_only_real_pinned_admission(tmp_path):
    path = tmp_path / "mixed.db"
    token = str(uuid4())
    persist_bundle(path, approved_bundle_document(), token, EMPTY_MANIFEST)
    synthetic = seed(path, LATER, namespace="tcgdex_repository", selector="swsh3")
    selected = request(synthetic, token, namespace="tcgdex_repository", selector="swsh3")
    error("scope_mismatch", lambda: result(path, selected))


def test_cli_redaction_read_only_no_network_and_error_shape(tmp_path, monkeypatch, capsys):
    path = tmp_path / "sensitive-database.db"
    selector = "private-qa-selector"
    old = seed(path, EARLIER, selector=selector)
    current = seed(path, LATER, [observation("sensitive-reference", LATER)], selector=selector)
    selected = request(current, old, selector=selector)
    request_path = tmp_path / "sensitive-request.json"
    request_path.write_text(json.dumps(selected.to_dict()), encoding="utf-8")
    before = path.read_bytes()

    def no_network(*args, **kwargs):
        raise AssertionError("P4b attempted external network")

    monkeypatch.setattr(socket, "socket", no_network)
    args = ["discover-scoped", "--db", str(path), "--request", str(request_path)]
    assert cli.main(args) == 0
    output = capsys.readouterr()
    payload = json.loads(output.out)
    assert payload["result"] == "discoveries"
    assert path.read_bytes() == before
    for secret in (
        str(path),
        str(request_path),
        current,
        old,
        "sensitive-reference",
        selector,
        "synthetic/qa/a",
    ):
        assert secret not in output.err
    request_path.write_text(
        json.dumps(request(current, language=None, selector=selector).to_dict()), encoding="utf-8"
    )
    assert cli.main(args) == 2
    output = capsys.readouterr()
    payload = json.loads(output.out)
    assert payload["version"] == 2
    assert payload["error_category"] == "unit_missing"
    assert payload["counts"] is None and payload["events"] == []
    assert path.read_bytes() == before


def test_unselected_historical_reference_cannot_suppress_selected_novelty(tmp_path):
    path = tmp_path / "other-scope.db"
    old = seed(path, EARLIER, [observation("new", EARLIER)], other_indexes=(0,))
    current = seed(path, LATER, [observation("new", LATER)])
    output = result(path, request(current, old))
    assert output["counts"]["validated_records"] == 2
    assert output["counts"]["historical_selected_records"] == 0
    assert output["counts"]["historical_selected_references"] == 0
    assert [event["reference"]["external_id"] for event in output["events"]] == ["new"]


@pytest.mark.parametrize("position", ["baseline", "current", "history"])
def test_qaf01_unselected_contradictions_invalidate_the_complete_envelope(tmp_path, position):
    path = tmp_path / "hidden-contradiction.db"
    timestamp = EARLIER if position == "history" else LATER
    bad = seed(
        path,
        timestamp,
        [
            observation("hidden", timestamp, name="First invented QA name"),
            observation("hidden", timestamp, name="Contradictory invented QA name"),
        ],
        other_indexes=(0, 1),
    )
    if position == "baseline":
        selected = request(bad)
    elif position == "current":
        selected = request(bad, seed(path, EARLIER))
    else:
        current = seed(path, LATER, [observation("new", LATER)])
        selected = request(current, bad)
    error("contradictory_snapshot", lambda: result(path, selected))
