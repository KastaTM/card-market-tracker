"""Real admission and mutation barriers for the separate offline outbox."""

import copy
import json
import socket
import sqlite3
import time
from dataclasses import replace
from uuid import uuid4

import pytest
from test_multi_revision_discovery import request
from test_scoped_discovery_core import EMPTY_MANIFEST, MIDDLE, OLD, curated, seed

from card_market_tracker.alerts import application, storage
from card_market_tracker.alerts.errors import OutboxError
from card_market_tracker.discovery import journal_application, journal_storage
from card_market_tracker.discovery.multi_models import REVIEWED_PAIR_PROFILE
from card_market_tracker.discovery.scoped_models import ScopedDiscoveryResult
from card_market_tracker.persistence.capture import persist_bundle_v2
from card_market_tracker.pinned_repository.bundle_v2 import approved_bundle_document_v2


@pytest.fixture
def admitted(tmp_path):
    captures, journal, outbox = (
        tmp_path / name for name in ("captures.db", "journal.db", "outbox.db")
    )
    old, _ = seed(captures, (), capture=OLD)
    middle, _ = seed(captures, (), capture=MIDDLE)
    current, _ = seed(captures, ("accepted", "candidate"), manifest=curated("accepted"))
    req = request(current.batch_id, (old.batch_id,))
    path = tmp_path / "request.json"
    path.write_text(json.dumps(req.to_dict()), encoding="utf-8")
    journal_storage.initialize(journal)
    cid = journal_application.record(captures, journal, path)["comparison_id"]
    storage.initialize(outbox)
    return captures, journal, outbox, cid, req, middle, path


def test_origin_shared_event_windows_replay_destinations_and_copy(admitted, tmp_path, monkeypatch):
    captures, journal, outbox, cid, req, middle, path = admitted
    monkeypatch.setattr(socket, "socket", lambda *a, **k: pytest.fail("network attempted"))
    original = (captures.read_bytes(), journal.read_bytes())
    first = application.enqueue(captures, journal, outbox, cid, "local-preview")
    assert {
        key: first[key]
        for key in (
            "alerts_new",
            "alerts_existing",
            "associations_new",
            "associations_existing",
            "events",
        )
    } == {
        "alerts_new": 2,
        "alerts_existing": 0,
        "associations_new": 2,
        "associations_existing": 0,
        "events": 2,
    }
    page = storage.list_alerts(outbox)
    aid = page["items"][0]["alert_id"]
    alert = storage.get(outbox, aid)
    before = outbox.read_bytes()
    assert (
        application.enqueue(captures, journal, outbox, cid, "local-preview")["result"] == "replay"
    )
    assert outbox.read_bytes() == before
    assert storage.preview(outbox, aid)["message_text"] == alert["alert"]["message_text"]
    assert application.recompute(captures, journal, outbox, aid, cid)["level"] == "origin-recompute"
    assert outbox.read_bytes() == before
    assert (captures.read_bytes(), journal.read_bytes()) == original
    path.write_text(
        json.dumps(
            replace(req, history=(replace(req.current, batch_id=middle.batch_id),)).to_dict()
        ),
        encoding="utf-8",
    )
    other = journal_application.record(captures, journal, path)["comparison_id"]
    second = application.enqueue(captures, journal, outbox, other, "local-preview")
    assert (second["alerts_new"], second["alerts_existing"], second["associations_new"]) == (
        0,
        2,
        2,
    )
    assert storage.get(outbox, aid) == alert
    evidence = storage.evidence_list(outbox, aid, limit=1)
    assert len(evidence["items"]) == 1 and evidence["next_cursor"]
    assert len(storage.evidence_list(outbox, aid, cursor=evidence["next_cursor"])["items"]) == 1
    e1, e2 = (storage.evidence_get(outbox, aid, item) for item in (cid, other))
    assert e1["event"]["event_id"] == e2["event"]["event_id"]
    assert e1["event"]["evidence"] != e2["event"]["evidence"]
    assert application.enqueue(captures, journal, outbox, cid, "other-preview")["alerts_new"] == 2
    assert storage.verify(outbox)["counts"] == {"alerts": 4, "associations": 6}
    backup, restored = tmp_path / "backup.db", tmp_path / "restored.db"
    storage.backup(outbox, backup)
    storage.restore(backup, restored)
    assert storage.get(restored, aid) == alert
    assert (
        application.enqueue(captures, journal, restored, cid, "local-preview")["result"] == "replay"
    )
    application.recompute(captures, journal, restored, aid, other)


@pytest.mark.parametrize("value", [{"verified": True}, object(), application._Receipt("{}")])
def test_self_attested_receipt_never_creates_database(tmp_path, value):
    path = tmp_path / "missing.db"
    with pytest.raises(OutboxError, match="unsupported_evidence"):
        storage._enqueue_verified(path, value, storage.Budget())
    assert not path.exists()


@pytest.mark.parametrize(
    "mutation",
    ["comparison_id", "journal_content_sha256", "message_text", "event_json", "intent_json"],
)
def test_all_consumed_receipt_fields_are_sealed(admitted, monkeypatch, mutation):
    captures, journal, outbox, cid, *_ = admitted
    original = storage._enqueue_verified
    before = outbox.read_bytes()

    def mutate(path, receipt, budget):
        value = json.loads(receipt.content_json)
        if mutation in ("comparison_id", "journal_content_sha256"):
            value[mutation] = "0" * 64
        else:
            value["rows"][0][mutation] += " "
        object.__setattr__(receipt, "content_json", storage.canonical_json(value))
        return original(path, receipt, budget)

    monkeypatch.setattr(storage, "_enqueue_verified", mutate)
    with pytest.raises(OutboxError, match="unsupported_evidence"):
        application.enqueue(captures, journal, outbox, cid, "local-preview")
    assert outbox.read_bytes() == before


def test_journal_coherent_rewrite_detected_before_any_outbox_write(admitted):
    captures, journal, outbox, cid, *_ = admitted
    stored = journal_storage.get(journal, cid)
    stored["comparison"]["counts"]["validated_records"] += 1
    with sqlite3.connect(journal) as db:
        db.execute(
            "UPDATE comparisons SET result_json=?, content_sha256=?",
            (
                journal_storage.canonical_json(stored["comparison"]),
                journal_storage.content_digest(stored["request"], stored["comparison"]),
            ),
        )
    assert journal_storage.verify(journal)["level"] == "local"
    before = outbox.read_bytes()
    with pytest.raises(OutboxError, match="recompute_mismatch"):
        application.enqueue(captures, journal, outbox, cid, "local-preview")
    assert outbox.read_bytes() == before


@pytest.mark.parametrize("copier", [copy.copy, copy.deepcopy])
def test_copied_receipt_cannot_grant_authority(admitted, monkeypatch, copier):
    captures, journal, outbox, cid, *_ = admitted
    original = storage._enqueue_verified
    before = outbox.read_bytes()

    def copied(path, receipt, budget):
        return original(path, copier(receipt), budget)

    monkeypatch.setattr(storage, "_enqueue_verified", copied)
    with pytest.raises(OutboxError, match="unsupported_evidence"):
        application.enqueue(captures, journal, outbox, cid, "local-preview")
    assert outbox.read_bytes() == before


def test_retained_pair_is_frozen_before_comparator_callback(admitted, monkeypatch):
    captures, journal, outbox, cid, *_ = admitted
    retained = journal_storage.get(journal, cid)
    original_compare = application.compare
    monkeypatch.setattr(application, "journal_get", lambda *a, **k: retained)

    def mutate(*args):
        retained["comparison"]["events"][0]["category"] = "tampered"
        return original_compare(*args)

    monkeypatch.setattr(application, "compare", mutate)
    application.enqueue(captures, journal, outbox, cid, "local-preview")
    aid = storage.list_alerts(outbox)["items"][0]["alert_id"]
    assert storage.evidence_get(outbox, aid, cid)["event"]["category"] != "tampered"


def test_full_canonical_comparison_mismatch_and_missing_sources(admitted, monkeypatch):
    captures, journal, outbox, cid, *_ = admitted
    actual = journal_storage.get(journal, cid)["comparison"]
    changed = copy.deepcopy(actual)
    changed["counts"]["validated_records"] += 1
    monkeypatch.setattr(application, "compare", lambda *a: ScopedDiscoveryResult(changed))
    before = outbox.read_bytes()
    with pytest.raises(OutboxError, match="recompute_mismatch"):
        application.enqueue(captures, journal, outbox, cid, "local-preview")
    assert outbox.read_bytes() == before
    for source in (captures, journal):
        missing = source.with_suffix(".missing")
        with pytest.raises(OutboxError, match="storage_missing"):
            application.enqueue(
                missing if source == captures else captures,
                missing if source == journal else journal,
                outbox,
                cid,
                "local-preview",
            )


@pytest.mark.parametrize("which", ["captures-journal", "captures-outbox", "journal-outbox"])
def test_three_paths_must_be_distinct_before_reads(admitted, which):
    captures, journal, outbox, cid, *_ = admitted
    args = {
        "captures-journal": (captures, captures, outbox),
        "captures-outbox": (captures, journal, captures),
        "journal-outbox": (captures, journal, journal),
    }[which]
    with pytest.raises(OutboxError, match="unsafe_destination"):
        application.enqueue(*args, cid, "local-preview")


@pytest.mark.parametrize("timeout", [True, False, 0, -1, 5.1, float("inf"), float("nan")])
def test_timeout_strict_before_io(tmp_path, timeout):
    with pytest.raises(OutboxError, match="invalid_field"):
        application.enqueue(
            tmp_path / "a",
            tmp_path / "b",
            tmp_path / "c",
            "cmp3:" + "0" * 64,
            "local-preview",
            timeout=timeout,
        )


def test_baseline_and_no_discoveries_are_zero_write_replay(admitted):
    captures, journal, outbox, _, req, _, path = admitted
    for changed in (
        replace(req, history=()),
        request(req.current.batch_id, (req.history[0].batch_id,)),
    ):
        if changed.history:
            # All current references occur in this separate later historical batch.
            old, _ = seed(captures, ("accepted", "candidate"), capture=MIDDLE)
            changed = request(req.current.batch_id, (old.batch_id,))
        path.write_text(json.dumps(changed.to_dict()), encoding="utf-8")
        cid = journal_application.record(captures, journal, path)["comparison_id"]
        before = outbox.read_bytes()
        result = application.enqueue(captures, journal, outbox, cid, "local-preview")
        assert result["events"] == 0 and result["result"] == "replay"
        assert outbox.read_bytes() == before


@pytest.mark.parametrize("kind,selector", [("set", "swsh3"), ("card", "swsh3-136")])
@pytest.mark.parametrize("language", ["es", "en"])
def test_all_four_real_units_produce_zero_alerts(tmp_path, kind, selector, language):
    captures, journal, outbox = (tmp_path / name for name in ("real.db", "journal.db", "outbox.db"))
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
    path = tmp_path / "request.json"
    path.write_text(json.dumps(req.to_dict()), encoding="utf-8")
    journal_storage.initialize(journal)
    cid = journal_application.record(captures, journal, path)["comparison_id"]
    storage.initialize(outbox)
    before = (captures.read_bytes(), journal.read_bytes(), outbox.read_bytes())
    assert application.enqueue(captures, journal, outbox, cid, "local-preview")["events"] == 0
    assert (captures.read_bytes(), journal.read_bytes(), outbox.read_bytes()) == before


def test_one_shared_budget_is_retained_through_origin_prepare_and_storage(admitted, monkeypatch):
    captures, journal, outbox, cid, *_ = admitted
    origin, write = application._verified_pair, storage._enqueue_verified
    observed = []

    def inspect_origin(captures, journal, comparison_id, budget):
        observed.append(budget)
        return origin(captures, journal, comparison_id, budget)

    def inspect_write(path, receipt, budget):
        assert budget is observed[0]
        return write(path, receipt, budget)

    monkeypatch.setattr(application, "_verified_pair", inspect_origin)
    monkeypatch.setattr(storage, "_enqueue_verified", inspect_write)
    application.enqueue(captures, journal, outbox, cid, "local-preview")


def test_shared_deadline_during_preparation_remains_timeout(admitted, monkeypatch):
    captures, journal, outbox, cid, *_ = admitted
    original = application.prepare_event

    def expire(*args, **kwargs):
        time.sleep(0.15)
        return original(*args, **kwargs)

    monkeypatch.setattr(application, "prepare_event", expire)
    before = outbox.read_bytes()
    with pytest.raises(OutboxError, match="storage_timeout"):
        application.enqueue(captures, journal, outbox, cid, "local-preview", timeout=0.1)
    assert outbox.read_bytes() == before


def test_event_count_limit_precedes_preparation(admitted, monkeypatch):
    captures, journal, outbox, cid, *_ = admitted
    monkeypatch.setattr(
        application, "_verified_pair", lambda *args: ({"events": [{}] * 1001}, "0" * 64)
    )
    monkeypatch.setattr(
        application,
        "prepare_event",
        lambda *args, **kwargs: pytest.fail("prepared beyond event cap"),
    )
    before = outbox.read_bytes()
    with pytest.raises(OutboxError, match="input_limit"):
        application.enqueue(captures, journal, outbox, cid, "local-preview")
    assert outbox.read_bytes() == before


def test_whole_prepared_envelope_limit_precedes_receipt_and_write(admitted, monkeypatch):
    captures, journal, outbox, cid, *_ = admitted
    original = application.prepare_event

    def oversized(*args, **kwargs):
        row = original(*args, **kwargs)
        row["message_text"] = "x" * (16 * 1024 * 1024)
        return row

    monkeypatch.setattr(application, "prepare_event", oversized)
    monkeypatch.setattr(
        storage, "_enqueue_verified", lambda *args: pytest.fail("write beyond aggregate cap")
    )
    before = outbox.read_bytes()
    with pytest.raises(OutboxError, match="input_limit"):
        application.enqueue(captures, journal, outbox, cid, "local-preview")
    assert outbox.read_bytes() == before


@pytest.mark.parametrize("field", ["journal_content_sha256", "event", "event_sha256"])
def test_recompute_matches_complete_frozen_association(admitted, monkeypatch, field):
    captures, journal, outbox, cid, *_ = admitted
    application.enqueue(captures, journal, outbox, cid, "local-preview")
    aid = storage.list_alerts(outbox)["items"][0]["alert_id"]
    original = storage.evidence_get

    def alter(*args, **kwargs):
        value = original(*args, **kwargs)
        if field == "event":
            value[field]["evidence"]["history"][0]["captured_at"] = "altered"
        else:
            value[field] = "0" * 64
        return value

    monkeypatch.setattr(storage, "evidence_get", alter)
    before = outbox.read_bytes()
    with pytest.raises(OutboxError, match="recompute_mismatch"):
        application.recompute(captures, journal, outbox, aid, cid)
    assert outbox.read_bytes() == before
