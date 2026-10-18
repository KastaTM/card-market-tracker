"""V3 real no-change window and explicitly synthetic temporal adversaries."""

import json
import socket
from dataclasses import replace
from uuid import uuid4

import pytest
from test_scoped_discovery_core import (
    EMPTY_MANIFEST,
    MIDDLE,
    OLD,
    curated,
    observation,
    seed,
)
from test_scoped_discovery_core import (
    request as scoped_request,
)

from card_market_tracker.catalog.validation import CatalogError
from card_market_tracker.discovery.errors import DiscoveryError
from card_market_tracker.discovery.multi_comparison import compare
from card_market_tracker.discovery.multi_input import parse_request, validate_request
from card_market_tracker.discovery.multi_models import (
    REVIEWED_PAIR_PROFILE,
    SYNTHETIC_PROFILE,
    ProfiledCapture,
)
from card_market_tracker.persistence.capture import persist_bundle_v2
from card_market_tracker.persistence.errors import PersistenceError
from card_market_tracker.persistence.sqlite_repository import (
    backup,
    read_multi_revision_snapshots,
    restore,
)
from card_market_tracker.pinned_repository.bundle_v2 import approved_bundle_document_v2


def request(current, history=(), *, profile=SYNTHETIC_PROFILE, **kwargs):
    return parse_request(
        {**scoped_request(current, history, **kwargs).to_dict(), "version": 3, "profile": profile}
    )


def result(path, req):
    return compare(req, read_multi_revision_snapshots(path, req)).to_dict()


def fail(category, call):
    with pytest.raises((DiscoveryError, PersistenceError)) as caught:
        call()
    assert caught.value.category == category


@pytest.mark.parametrize("kind,selector", [("set", "swsh3"), ("card", "swsh3-136")])
@pytest.mark.parametrize("language", ["es", "en"])
@pytest.mark.parametrize("bound", [False, True])
def test_real_pair_four_no_change_units(tmp_path, monkeypatch, kind, selector, language, bound):
    path = tmp_path / "real.db"
    manifest = curated("swsh3", namespace="tcgdex_repository") if bound else EMPTY_MANIFEST
    if bound:
        manifest["bindings"].append(
            {
                **manifest["bindings"][0],
                "reference": {**manifest["bindings"][0]["reference"], "language": "en"},
            }
        )
    r0, r1 = str(uuid4()), str(uuid4())
    for token, member in ((r0, "r0"), (r1, "r1")):
        persist_bundle_v2(path, approved_bundle_document_v2(member), token, manifest)
    req = request(
        r1,
        (r0,),
        profile=REVIEWED_PAIR_PROFILE,
        namespace="tcgdex_repository",
        kind=kind,
        language=language,
        selector=selector,
    )
    monkeypatch.setattr(socket, "socket", lambda *a, **kw: pytest.fail("network attempted"))
    before = path.read_bytes()
    payload = result(path, req)
    assert path.read_bytes() == before
    assert payload["version"] == 3 and payload["profile"] == REVIEWED_PAIR_PROFILE
    assert payload["result"] == "no_discoveries" and payload["events"] == []
    assert payload["counts"]["validated_records"] == 8
    assert payload["counts"]["current_selected_records"] == 1
    proof = payload["current"]["extraction_proof"]
    assert proof == payload["history"][0]["extraction_proof"]
    assert proof["extractor"] == "pinned_ts_literals_v1" and len(proof["fields"]) == 8
    assert next(field for field in proof["fields"] if field["field"] == "id") == {
        "path": "data/Sword & Shield/Darkness Ablaze.ts",
        "field": "id",
        "start": 104,
        "end": 111,
        "transformation": "exact_literal",
    }
    captures = read_multi_revision_snapshots(path, req)
    scopes = [json.loads(item.capture.scope_json) for item in captures]
    assert {scope["revision"] for scope in scopes} == {
        approved_bundle_document_v2(member)["revision"] for member in ("r0", "r1")
    }
    assert len({scope["bundle_sha256"] for scope in scopes}) == 2
    assert len({scope["captured_at"] for scope in scopes}) == 2
    # Acquisition evidence must remain in public comparison evidence as well.
    assert (
        payload["current"]["acquisition"]["revision"] == approved_bundle_document_v2()["revision"]
    )
    reverse = replace(req, current=req.history[0], history=(req.current,))
    fail("chronology", lambda: result(path, reverse))


def test_synthetic_union_aliases_metadata_reappearance_and_copy(tmp_path):
    path = tmp_path / "history.db"
    first, _ = seed(path, ("seen",), capture=OLD)
    empty, _ = seed(path, (), capture=MIDDLE)
    current, _ = seed(
        path,
        items=(
            replace(observation("seen"), name="Changed"),
            observation("alias"),
            observation("candidate"),
        ),
        manifest=curated("seen", "alias"),
    )
    req = request(current.batch_id, (first.batch_id, empty.batch_id))
    payload = result(path, req)
    assert [event["type"] for event in payload["events"]] == [
        "SET_REFERENCE_FIRST_OBSERVED",
        "CANDIDATE_REFERENCE_FIRST_OBSERVED",
    ]
    assert payload["comparison_id"].startswith("cmp3:")
    assert all(event["event_id"].startswith("evt3:") for event in payload["events"])
    assert result(path, replace(req, history=tuple(reversed(req.history)))) == payload
    backup(path, tmp_path / "backup.db")
    restore(tmp_path / "backup.db", tmp_path / "restored.db")
    assert result(tmp_path / "restored.db", req) == payload
    assert result(path, request(current.batch_id))["result"] == "baseline"


@pytest.mark.parametrize("contradictory", [False, True])
def test_duplicates_original_indexes_and_contradictions(tmp_path, contradictory):
    path = tmp_path / "duplicate.db"
    history, _ = seed(path, (), capture=OLD)
    item = observation("new")
    current, _ = seed(
        path, items=(item, replace(item, name="Different") if contradictory else item)
    )
    req = request(current.batch_id, (history.batch_id,))
    if contradictory:
        fail("contradictory_snapshot", lambda: result(path, req))
    else:
        payload = result(path, req)
        assert len(payload["events"]) == 1
        assert payload["events"][0]["evidence"]["current_record_indexes"] == [0, 1]


@pytest.mark.parametrize("outcome", ["partial", "failed"])
def test_incomplete_baseline_rejected(tmp_path, outcome):
    path = tmp_path / "partial.db"
    current, _ = seed(path, () if outcome == "failed" else ("new",), outcome=outcome, completed=())
    fail("incomplete_evidence", lambda: result(path, request(current.batch_id)))


def test_equal_time_foreign_family_paths_and_forged_receipts(tmp_path):
    path = tmp_path / "forged.db"
    first, _ = seed(path)
    current, _ = seed(path)
    req = request(current.batch_id, (first.batch_id,))
    fail("chronology", lambda: result(path, req))
    baseline = request(current.batch_id)
    (issued,) = read_multi_revision_snapshots(path, baseline)
    fail(
        "unsupported_evidence",
        lambda: compare(baseline, (ProfiledCapture(issued.capture, SYNTHETIC_PROFILE),)),
    )
    forged = replace(issued, profile=REVIEWED_PAIR_PROFILE)
    fail("unsupported_evidence", lambda: compare(baseline, (forged,)))
    copied = replace(issued)
    object.__setattr__(copied, "_authority", issued._authority)
    object.__setattr__(copied, "capture", replace(issued.capture, capture_fingerprint="0" * 64))
    fail("unsupported_evidence", lambda: compare(baseline, (copied,)))
    altered_proof = replace(issued, extraction_json='{"version":1}')
    object.__setattr__(altered_proof, "_authority", issued._authority)
    fail("unsupported_evidence", lambda: compare(baseline, (altered_proof,)))
    fail(
        "unsupported_evidence",
        lambda: result(path, replace(baseline, profile=REVIEWED_PAIR_PROFILE)),
    )
    later, _ = seed(path, capture="2026-01-04T00:00:00.000000Z", paths=("synthetic/b",))
    fail("scope_mismatch", lambda: result(path, request(later.batch_id, (current.batch_id,))))


@pytest.mark.parametrize(
    "field,value",
    [
        ("version", 2),
        ("version", True),
        ("profile", "unknown"),
        ("profile", {}),
        ("extra", "registry"),
    ],
)
def test_strict_request_versions_profiles_and_shape(field, value):
    document = request(str(uuid4())).to_dict()
    document[field] = value
    with pytest.raises(DiscoveryError):
        parse_request(document)
    with pytest.raises(DiscoveryError):
        validate_request(document)


def test_missing_extra_batches_and_historical_bound(tmp_path):
    path = tmp_path / "bounds.db"
    current, _ = seed(path)
    req = request(current.batch_id)
    captures = read_multi_revision_snapshots(path, req)
    fail("batch_missing", lambda: compare(req, ()))
    fail("storage_corrupt", lambda: compare(req, captures + captures))
    fail("input_limit", lambda: compare(req, captures * 34))
    fail("storage_corrupt", lambda: compare(req, [*captures]))
    document = req.to_dict()
    document["history"] = [{"batch_id": str(uuid4()), "selector": "unit"} for _ in range(33)]
    fail("input_limit", lambda: parse_request(document))


@pytest.mark.parametrize(
    "attack",
    [
        "extra",
        "version",
        "empty",
        "duplicate",
        "overflow",
        "bool",
        "reverse",
        "negative",
        "transform",
        "path",
        "field",
        "many",
        "json",
        "depth",
    ],
)
def test_generic_extraction_decoder_strict_bounds(tmp_path, attack):
    from card_market_tracker.discovery.multi_validation import _extraction_proof

    path, token = tmp_path / "proof.db", str(uuid4())
    persist_bundle_v2(path, approved_bundle_document_v2(), token, EMPTY_MANIFEST)
    req = request(
        token, profile=REVIEWED_PAIR_PROFILE, namespace="tcgdex_repository", selector="swsh3"
    )
    (issued,) = read_multi_revision_snapshots(path, req)
    proof = json.loads(issued.extraction_json)
    field = proof["fields"][0]
    if attack == "extra":
        proof["unreviewed"] = "payload"
    elif attack == "version":
        proof["version"] = True
    elif attack == "empty":
        proof["fields"] = []
    elif attack == "duplicate":
        proof["fields"].append(dict(field))
    elif attack in ("overflow", "bool", "reverse", "negative"):
        field["start"], field["end"] = {
            "overflow": (0, 65537),
            "bool": (False, 1),
            "reverse": (2, 1),
            "negative": (-1, 1),
        }[attack]
    elif attack == "transform":
        field["transformation"] = "execute"
    elif attack in ("path", "field"):
        field[attack] = "x" * 257
    elif attack == "many":
        proof["fields"] *= 5
    raw = json.dumps(proof)
    if attack == "json":
        raw = '{"version":1,"version":1}'
    elif attack == "depth":
        raw = "[" * 17 + "0" + "]" * 17
    with pytest.raises((CatalogError, DiscoveryError)):
        _extraction_proof(replace(issued, extraction_json=raw))
