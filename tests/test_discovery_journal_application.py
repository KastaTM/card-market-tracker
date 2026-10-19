"""Real public admission, preserved source evidence and adversarial journal inputs."""

import copy
import hashlib
import json
import socket
import sqlite3
from dataclasses import replace
from uuid import uuid4

import pytest
from test_multi_revision_discovery import request, result
from test_scoped_discovery_core import EMPTY_MANIFEST, MIDDLE, OLD, seed

from card_market_tracker.cli import main
from card_market_tracker.discovery import journal_application as application
from card_market_tracker.discovery import journal_storage as storage
from card_market_tracker.discovery.journal_errors import JournalError
from card_market_tracker.discovery.journal_validation import (
    canonical_bounded,
    decode_json,
    validate_pair,
)
from card_market_tracker.discovery.multi_models import REVIEWED_PAIR_PROFILE
from card_market_tracker.discovery.scoped_models import ScopedDiscoveryResult
from card_market_tracker.persistence.capture import persist_bundle_v2
from card_market_tracker.pinned_repository.bundle_v2 import approved_bundle_document_v2


@pytest.fixture
def admitted(tmp_path):
    captures, journal, path = tmp_path / "captures.db", tmp_path / "journal.db", tmp_path / "r.json"
    first, _ = seed(captures, (), capture=OLD)
    second, _ = seed(captures, (), capture=MIDDLE)
    current, _ = seed(captures, ("new", "other"))
    req = request(current.batch_id, (first.batch_id,))
    path.write_text(json.dumps(req.to_dict()), encoding="utf-8")
    storage.initialize(journal)
    return captures, journal, path, req, second


def test_admitted_record_replay_digest_windows_and_recompute(admitted, monkeypatch):
    captures, journal, path, req, second = admitted
    expected = result(captures, req)
    before = captures.read_bytes()
    monkeypatch.setattr(socket, "socket", lambda *a, **k: pytest.fail("network attempted"))
    inserted = application.record(captures, journal, path)
    cid = inserted["comparison_id"]
    assert inserted["result"] == "inserted"
    retained = storage.get(journal, cid)
    assert retained["comparison"] == expected and retained["request"] == req.to_dict()
    semantic = {"journal_version": 1, "request": req.to_dict(), "result": expected}
    encoded = json.dumps(
        semantic, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(",", ":")
    )
    assert retained["content_sha256"] == hashlib.sha256(encoded.encode("ascii")).hexdigest()
    journal_bytes = journal.read_bytes()
    replay = application.record(captures, journal, path)
    assert (
        replay["result"] == "replay"
        and replay["first_recorded_at"] == inserted["first_recorded_at"]
    )
    assert journal.read_bytes() == journal_bytes
    other = request(req.current.batch_id, (second.batch_id,))
    path.write_text(json.dumps(other.to_dict()), encoding="utf-8")
    distinct = application.record(captures, journal, path)
    assert distinct["comparison_id"] != cid
    newer = storage.get(journal, distinct["comparison_id"])["comparison"]
    assert expected["events"][0]["event_id"] == newer["events"][0]["event_id"]
    assert expected["events"][0]["evidence"] != newer["events"][0]["evidence"]
    occurrences = storage.event_occurrences(journal, expected["events"][0]["event_id"], limit=1)
    assert len(occurrences["items"]) == 1 and occurrences["next_cursor"]
    following = storage.event_occurrences(
        journal, expected["events"][0]["event_id"], cursor=occurrences["next_cursor"], limit=1
    )
    assert len(following["items"]) == 1 and following["next_cursor"] is None
    assert application.recompute(captures, journal, cid)["level"] == "origin-recompute"
    assert storage.verify(journal)["counts"] == {"comparisons": 2, "occurrences": 4}
    assert captures.read_bytes() == before


@pytest.mark.parametrize("kind,selector", [("set", "swsh3"), ("card", "swsh3-136")])
@pytest.mark.parametrize("language", ["es", "en"])
def test_real_approved_pair_no_discoveries(tmp_path, kind, selector, language):
    captures, journal = tmp_path / "real.db", tmp_path / "journal.db"
    tokens = [str(uuid4()), str(uuid4())]
    for token, member in zip(tokens, ("r0", "r1"), strict=True):
        persist_bundle_v2(captures, approved_bundle_document_v2(member), token, EMPTY_MANIFEST)
    req = request(
        tokens[1],
        (tokens[0],),
        profile=REVIEWED_PAIR_PROFILE,
        namespace="tcgdex_repository",
        kind=kind,
        language=language,
        selector=selector,
    )
    path = tmp_path / "req.json"
    path.write_text(json.dumps(req.to_dict()), encoding="utf-8")
    before = captures.read_bytes()
    storage.initialize(journal)
    receipt = application.record(captures, journal, path)
    comparison = storage.get(journal, receipt["comparison_id"])["comparison"]
    assert comparison == result(captures, req)
    assert comparison["result"] == "no_discoveries" and comparison["events"] == []
    assert receipt["counts"] == {"comparisons": 1, "occurrences": 0}
    assert application.recompute(captures, journal, receipt["comparison_id"])["result"] == "ok"
    assert captures.read_bytes() == before


def test_baseline_and_source_errors_have_no_entries(admitted):
    captures, journal, path, req, _ = admitted
    path.write_text(json.dumps(replace(req, history=()).to_dict()), encoding="utf-8")
    recorded = application.record(captures, journal, path)
    assert storage.get(journal, recorded["comparison_id"])["comparison"]["result"] == "baseline"
    assert recorded["counts"]["occurrences"] == 0
    before = journal.read_bytes()
    path.write_text(
        json.dumps(replace(req, profile=REVIEWED_PAIR_PROFILE).to_dict()), encoding="utf-8"
    )
    with pytest.raises(ValueError):
        application.record(captures, journal, path)
    assert journal.read_bytes() == before


@pytest.mark.parametrize(
    "receipt",
    [{"verified": True}, ScopedDiscoveryResult({}), application._Receipt("{}", "{}"), object()],
)
def test_self_attested_receipts_fail_before_storage(tmp_path, receipt):
    path = tmp_path / "missing.db"
    with pytest.raises(JournalError, match="unsupported_evidence"):
        storage._record_verified(path, receipt, storage.Budget(2))
    assert not path.exists()


def test_receipt_mutation_after_verified_compare(admitted, monkeypatch):
    captures, journal, path, _, _ = admitted
    original = application._record_verified

    def mutate(path, receipt, budget):
        object.__setattr__(
            receipt, "result_json", receipt.result_json.replace("discoveries", "baseline")
        )
        return original(path, receipt, budget)

    monkeypatch.setattr(application, "_record_verified", mutate)
    with pytest.raises(JournalError, match="unsupported_evidence"):
        application.record(captures, journal, path)
    assert storage.verify(journal)["counts"]["comparisons"] == 0


def test_semantic_collision_no_overwrite(admitted, monkeypatch):
    captures, journal, path, req, _ = admitted
    application.record(captures, journal, path)
    before = journal.read_bytes()
    changed = result(captures, req)
    changed["counts"]["validated_records"] += 1
    monkeypatch.setattr(application, "compare", lambda *a: ScopedDiscoveryResult(changed))
    with pytest.raises(JournalError, match="conflict"):
        application.record(captures, journal, path)
    assert journal.read_bytes() == before


def test_coherent_tamper_needs_original_recompute(admitted):
    captures, journal, path, _, _ = admitted
    cid = application.record(captures, journal, path)["comparison_id"]
    stored = storage.get(journal, cid)
    stored["comparison"]["counts"]["validated_records"] += 1
    with sqlite3.connect(journal) as db:
        db.execute(
            "UPDATE comparisons SET result_json=?, content_sha256=?",
            (
                storage.canonical_json(stored["comparison"]),
                storage.content_digest(stored["request"], stored["comparison"]),
            ),
        )
    assert storage.verify(journal)["level"] == "local"
    before = journal.read_bytes()
    with pytest.raises(JournalError, match="recompute_mismatch"):
        application.recompute(captures, journal, cid)
    assert journal.read_bytes() == before


@pytest.mark.parametrize(
    "attack",
    [
        "version",
        "extra",
        "profile",
        "context",
        "clock",
        "acquisition",
        "scope",
        "counts",
        "bool",
        "event",
        "indexes",
        "proof",
        "order",
        "history",
        "type",
        "reference",
        "category",
        "target",
        "nested_bool",
        "semantics_bool",
    ],
)
def test_complete_result_grammar(admitted, attack):
    captures, _, _, req, _ = admitted
    payload = copy.deepcopy(result(captures, req))
    event = payload["events"][0]
    if attack == "version":
        payload["version"] = True
    elif attack == "extra":
        payload["extra"] = "not allowed"
    elif attack == "profile":
        payload["profile"] = "unauthorized"
    elif attack == "context":
        payload["context"]["kind"] = "card"
    elif attack == "clock":
        payload["current"]["captured_at"] = "not a timestamp"
    elif attack == "acquisition":
        payload["current"]["acquisition"]["outcome"] = "partial"
    elif attack == "scope":
        payload["current"]["scope"]["completed"] = []
    elif attack == "counts":
        payload["counts"]["events"] = 0
    elif attack == "bool":
        payload["counts"]["validated_records"] = True
    elif attack == "event":
        event["evidence"]["comparison_id"] = "cmp3:" + "0" * 64
    elif attack == "indexes":
        event["evidence"]["current_record_indexes"] = [False]
    elif attack == "proof":
        payload["current"]["extraction_proof"] = {}
    elif attack == "order":
        payload["events"].reverse()
    elif attack == "history":
        payload["history"] = []
    elif attack == "type":
        event["type"] = "ALERT"
    elif attack == "reference":
        event["reference"]["external_id"] = "x" * 1025
    elif attack == "category":
        event["category"] = "arbitrary"
    elif attack == "target":
        event["cmt_id"] = str(uuid4())
    elif attack == "nested_bool":
        event["evidence"]["current"]["acquisition"]["version"] = True
    elif attack == "semantics_bool":
        payload["current"]["scope_semantics"]["semantics"]["version"] = True
    with pytest.raises(JournalError):
        validate_pair(req.to_dict(), payload)


@pytest.mark.parametrize(
    "raw",
    ['{"x":1,"x":2}', '{"x":NaN}', '{"x":1e999}', "[" * 17 + "0" + "]" * 17, "{", '"\\ud800"'],
)
def test_decoder_lexical_adversaries(raw):
    with pytest.raises(JournalError):
        decode_json(raw)


def test_result_cap_precedes_to_dict(admitted, monkeypatch):
    captures, journal, path, _, _ = admitted
    monkeypatch.setattr(
        application, "compare", lambda *a: ScopedDiscoveryResult({"x": "x" * (16 * 1024 * 1024)})
    )
    monkeypatch.setattr(ScopedDiscoveryResult, "to_dict", lambda *a: pytest.fail("unbounded copy"))
    with pytest.raises(JournalError, match="input_limit"):
        application.record(captures, journal, path)
    assert storage.verify(journal)["counts"]["comparisons"] == 0
    with pytest.raises(JournalError):
        canonical_bounded({"x": float("nan")})


def test_cli_all_routes_and_redaction(admitted, tmp_path, capsys):
    captures, journal, path, _, _ = admitted

    def cli(operation, *values, code=0, target=journal):
        assert (
            main(["discovery-journal", operation, "--journal-db", str(target), *map(str, values)])
            == code
        )
        output = capsys.readouterr()
        payload, log = json.loads(output.out), json.loads(output.err)
        assert log["event"] == "discovery.journal.completed" and log["result"] == payload["result"]
        assert log["run_id"] and log["duration_ms"] >= 0 and "operation" in log
        for secret in (str(tmp_path), "synthetic_scope", "unit", "new", "other", "SELECT"):
            assert secret not in output.err
        return payload

    recorded = cli("record", "--captures-db", captures, "--request", path)
    assert recorded["result"] == "inserted"
    cid = recorded["comparison_id"]
    pair = cli("get", "--comparison-id", cid)
    cli("list", "--limit", 1)
    cli("event-occurrences", "--event-id", pair["comparison"]["events"][0]["event_id"])
    cli("verify")
    cli("recompute", "--captures-db", captures, "--comparison-id", cid)
    backup, restored = tmp_path / "backup.db", tmp_path / "restored.db"
    cli("backup", "--destination", backup)
    cli("restore", "--destination", restored, target=backup)
    cli("verify", target=restored)
    cli("init", target=tmp_path / "empty.db")
    assert cli("record", "--result", "do-not-admit", code=2)["error_category"] == "invalid_field"
    cli("list", "--limit", 0, code=2)
    cli("get", "--comparison-id", "bad", code=2)
    cli("list", target=tmp_path / "missing.db", code=1)
