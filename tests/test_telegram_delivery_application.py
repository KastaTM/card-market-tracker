"""Author tests for original-backed manual sends; transport is always injected."""

import copy
import hashlib
import json
import socket
import sqlite3
from datetime import UTC, datetime, timedelta

import pytest
from test_alert_outbox_application import admitted as admitted  # noqa: F401

from card_market_tracker.alerts import application as outbox_application
from card_market_tracker.alerts import storage as outbox_storage
from card_market_tracker.telegram_delivery import application, storage
from card_market_tracker.telegram_delivery.errors import DeliveryError
from card_market_tracker.telegram_delivery.transport import Receipt, TransportResult


class FakeTransport:
    def __init__(self, result=None):
        self.calls = []
        self.result = result or TransportResult(
            "confirmed", receipt=Receipt(17, 1792576800, 123, 456)
        )

    def check_configuration(self):
        self.calls.append(("configuration",))

    def validate_destination(self, bot_id, chat_id, *, timeout=15):
        self.calls.append(("destination", bot_id, chat_id))

    def validate_bot(self, bot_id, *, timeout=15):
        self.calls.append(("bot", bot_id))

    def send(self, bot_id, chat_id, message_text, *, timeout=15):
        self.calls.append(("send", bot_id, chat_id, message_text))
        if isinstance(self.result, BaseException):
            raise self.result
        return self.result


@pytest.fixture
def prepared(request, tmp_path, monkeypatch):
    captures, journal, outbox, cid, *_ = request.getfixturevalue("admitted")
    monkeypatch.setattr(socket, "socket", lambda *a, **k: pytest.fail("network attempted"))
    outbox_application.enqueue(captures, journal, outbox, cid, "private-operator")
    aid = outbox_storage.list_alerts(outbox)["items"][0]["alert_id"]
    ledger = tmp_path / "ledger.db"
    storage.initialize(ledger)
    storage.destination_add(ledger, "private-operator", 123, 456, operator_private_owned=True)
    transport = FakeTransport()
    application.destination_validate(ledger, "private-operator", transport=transport)
    assert transport.calls == [("configuration",), ("destination", 123, 456)]
    result = application.prepare(captures, journal, outbox, ledger, aid, cid, "private-operator")
    return captures, journal, outbox, ledger, aid, cid, result["delivery_id"]


def send(prepared, transport):
    captures, journal, outbox, ledger, _, _, did = prepared
    return application.send(captures, journal, outbox, ledger, did, transport=transport)


def test_confirmed_durable_replay_exact_message_and_source_nonmutation(prepared):
    captures, journal, outbox, ledger, aid, cid, did = prepared
    before = tuple(path.read_bytes() for path in (captures, journal, outbox))
    transport = FakeTransport()
    assert send(prepared, transport)["state"] == "confirmed"
    assert transport.calls == [
        ("configuration",),
        ("bot", 123),
        ("send", 123, 456, outbox_storage.preview(outbox, aid)["message_text"]),
    ]
    assert tuple(path.read_bytes() for path in (captures, journal, outbox)) == before
    frozen = ledger.read_bytes()
    replay = FakeTransport()
    assert send(prepared, replay)["result"] == "replay"
    assert replay.calls == []
    assert ledger.read_bytes() == frozen
    public = json.dumps(storage.get(ledger, did))
    assert "bot_id" not in public and "chat_id" not in public and "message_text" not in public
    assert (
        application.recompute(captures, journal, outbox, ledger, did)["level"] == "origin-recompute"
    )
    assert (
        application.prepare(captures, journal, outbox, ledger, aid, cid, "private-operator")[
            "result"
        ]
        == "replay"
    )


@pytest.mark.parametrize(
    "copier", [copy.copy, copy.deepcopy, lambda r: application._Receipt(r.content_json)]
)
def test_receipt_copy_and_self_attestation_rejected(prepared, monkeypatch, copier):
    captures, journal, outbox, ledger, aid, cid, _ = prepared
    original = storage._prepare_verified
    before = ledger.read_bytes()
    monkeypatch.setattr(
        storage,
        "_prepare_verified",
        lambda path, receipt, **kw: original(path, copier(receipt), **kw),
    )
    with pytest.raises(DeliveryError, match="unsupported_evidence"):
        application.prepare(captures, journal, outbox, ledger, aid, cid, "private-operator")
    assert ledger.read_bytes() == before


def test_receipt_mutation_rejected_and_full_digests_independent(prepared, monkeypatch):
    captures, journal, outbox, ledger, aid, cid, _ = prepared
    original = storage._prepare_verified

    def check(path, receipt, **kwargs):
        binding = application._consume_receipt(receipt)

        def digest(v):
            canonical = json.dumps(
                v, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
            )
            return hashlib.sha256(canonical.encode("ascii")).hexdigest()

        assert binding["alert_content_sha256"] == digest(outbox_storage.get(outbox, aid)["alert"])
        evidence = outbox_storage.evidence_get(outbox, aid, cid)
        assert binding["evidence_content_sha256"] == digest(
            {
                key: evidence[key]
                for key in (
                    "alert_id",
                    "comparison_id",
                    "event",
                    "journal_content_sha256",
                    "event_sha256",
                )
            }
        )
        object.__setattr__(receipt, "content_json", receipt.content_json + " ")
        return original(path, receipt, **kwargs)

    monkeypatch.setattr(storage, "_prepare_verified", check)
    with pytest.raises(DeliveryError, match="unsupported_evidence"):
        application.prepare(captures, journal, outbox, ledger, aid, cid, "private-operator")


@pytest.mark.parametrize(
    "result,state",
    [
        (TransportResult("uncertain", "provider_invalid"), "uncertain"),
        (TransportResult("permanent_failure", "provider_rejection"), "permanent_failure"),
        (RuntimeError("private TOKEN https://api.telegram.org/botSECRET"), "uncertain"),
        (object(), "uncertain"),
    ],
)
def test_ambiguous_or_rejected_send_never_resends(prepared, result, state):
    transport = FakeTransport(result)
    assert send(prepared, transport)["state"] == state
    second = FakeTransport()
    with pytest.raises(DeliveryError, match="delivery_blocked"):
        send(prepared, second)
    assert second.calls == []


def test_bot_mismatch_precedes_claim(prepared):
    transport = FakeTransport()

    def reject(*args, **kwargs):
        raise DeliveryError("bot_mismatch")

    transport.validate_bot = reject
    with pytest.raises(DeliveryError, match="bot_mismatch"):
        send(prepared, transport)
    assert storage.load_delivery(prepared[3], prepared[-1])["state"] == "ready"
    assert not any(call[0] == "send" for call in transport.calls)


def test_valid429_due_gate_and_attempt_limit(prepared, monkeypatch):
    transport = FakeTransport(TransportResult("retryable", "provider_rate_limit", retry_after=1))
    assert send(prepared, transport)["state"] == "retryable"
    blocked = FakeTransport()
    with pytest.raises(DeliveryError, match="retry_not_due"):
        send(prepared, blocked)
    assert blocked.calls == []
    # Advance the ledger clock and application's local preflight together; no sleeps.
    initial = datetime.now(UTC)
    original_now = storage._now
    for offset in (3, 6):
        now = (initial + timedelta(seconds=offset)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        monkeypatch.setattr(storage, "_now", lambda now=now: now)
        monkeypatch.setattr(application, "_preflight", lambda d: None)
        outcome = send(prepared, transport)
    assert outcome["state"] == "permanent_failure"
    assert len([call for call in transport.calls if call[0] == "send"]) == 3
    monkeypatch.setattr(storage, "_now", original_now)


def test_failed_confirmation_commit_is_uncertain_not_confirmed(prepared, monkeypatch):
    original = storage.finish

    def fail_confirmation(*args, **kwargs):
        if kwargs["state"] == "confirmed":
            raise OSError("token-private")
        return original(*args, **kwargs)

    monkeypatch.setattr(storage, "finish", fail_confirmation)
    with pytest.raises(DeliveryError, match="local_commit_failed"):
        send(prepared, FakeTransport())
    assert storage.load_delivery(prepared[3], prepared[-1])["state"] == "uncertain"


def test_failed_fallback_stays_inflight_recovery_required(prepared, monkeypatch):
    monkeypatch.setattr(
        storage, "finish", lambda *a, **k: (_ for _ in ()).throw(OSError("private"))
    )
    with pytest.raises(DeliveryError, match="local_commit_failed"):
        send(prepared, FakeTransport())
    assert storage.load_delivery(prepared[3], prepared[-1])["state"] == "in_flight"
    with pytest.raises(DeliveryError, match="delivery_blocked"):
        send(prepared, FakeTransport())


def test_outbox_changes_during_recompute_fail_before_metadata(prepared, monkeypatch):
    original = application.outbox_application.recompute
    original_snapshot = application._snapshot
    calls = 0

    def snapshot(*args):
        nonlocal calls
        calls += 1
        result = original_snapshot(*args)
        return result if calls == 1 else (result[0] + " ", result[1])

    monkeypatch.setattr(application, "_snapshot", snapshot)
    monkeypatch.setattr(application.outbox_application, "recompute", original)
    transport = FakeTransport()
    with pytest.raises(DeliveryError, match="recompute_mismatch"):
        send(prepared, transport)
    assert transport.calls == []


def test_coherent_journal_rewrite_and_alias_mismatch_fail_offline(prepared):
    captures, journal, outbox, ledger, aid, cid, _ = prepared
    with pytest.raises(DeliveryError, match="invalid_destination"):
        application.prepare(captures, journal, outbox, ledger, aid, cid, "other")
    with sqlite3.connect(journal) as db:
        db.execute("UPDATE comparisons SET content_sha256=?", ("0" * 64,))
    transport = FakeTransport()
    with pytest.raises(DeliveryError):
        send(prepared, transport)
    assert transport.calls == []


def test_quarantine_blocks_network_but_allows_origin_recompute(prepared, tmp_path):
    captures, journal, outbox, ledger, _, _, did = prepared
    backup, restored = tmp_path / "backup.db", tmp_path / "restored.db"
    storage.backup(ledger, backup)
    storage.restore(backup, restored)
    transport = FakeTransport()
    with pytest.raises(DeliveryError, match="send_quarantined"):
        application.send(captures, journal, outbox, restored, did, transport=transport)
    assert transport.calls == []
    assert application.recompute(captures, journal, outbox, restored, did)["result"] == "ok"


@pytest.mark.parametrize("left,right", [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)])
def test_all_four_paths_distinct(prepared, left, right):
    paths = list(prepared[:4])
    paths[right] = paths[left]
    with pytest.raises(DeliveryError, match="unsafe_destination"):
        application.prepare(*paths, prepared[4], prepared[5], "private-operator")


@pytest.mark.parametrize("timeout", [True, False, 0, -1, float("nan"), float("inf"), 30.01])
def test_invalid_send_deadline_before_io(tmp_path, timeout):
    with pytest.raises(DeliveryError, match="invalid_field"):
        application.send(
            *(tmp_path / name for name in ("a", "b", "c", "d")), "tdl1:" + "0" * 64, timeout=timeout
        )


@pytest.mark.parametrize("receipt", [{}, object(), application._Receipt("{}")])
def test_unsealed_receipt_never_authorizes(receipt):
    with pytest.raises(DeliveryError, match="unsupported_evidence"):
        application._consume_receipt(receipt)


def test_confirmed_replay_still_requires_safe_distinct_source_paths(prepared):
    captures, journal, outbox, ledger, _, _, did = prepared
    send(prepared, FakeTransport())
    replay = FakeTransport()
    with pytest.raises(DeliveryError, match="unsafe_destination"):
        application.send(captures, journal, ledger, ledger, did, transport=replay)
    assert replay.calls == []


@pytest.mark.parametrize(
    "field,value,category",
    [
        ("validated_at", None, "not_validated"),
        ("updated_at", "9999-01-01T00:00:00.000000Z", "clock_skew"),
    ],
)
def test_local_route_and_clock_preflight_before_metadata(
    prepared, monkeypatch, field, value, category
):
    original = storage.load_delivery

    def altered(*args, **kwargs):
        return {**original(*args, **kwargs), field: value}

    monkeypatch.setattr(storage, "load_delivery", altered)
    transport = FakeTransport()
    with pytest.raises(DeliveryError, match=category):
        send(prepared, transport)
    assert transport.calls == []


def test_default_transport_needs_local_environment_before_claim(prepared, monkeypatch):
    monkeypatch.delenv("CMT_TELEGRAM_BOT_TOKEN", raising=False)
    captures, journal, outbox, ledger, _, _, did = prepared
    with pytest.raises(DeliveryError, match="token_configuration"):
        application.send(captures, journal, outbox, ledger, did)
    with pytest.raises(DeliveryError, match="token_configuration"):
        application.destination_validate(ledger, "private-operator")
    assert storage.load_delivery(ledger, did)["state"] == "ready"


def test_peer_confirmation_between_preflight_and_claim_never_sends(prepared, monkeypatch):
    claim = storage._claim_verified

    def peer_confirms(path, did, receipt, **kwargs):
        claimed = claim(path, did, receipt, **kwargs)
        storage.finish(
            path,
            did,
            claimed["attempt_id"],
            state="confirmed",
            receipt={"message_id": 19, "accepted_at": 1792576800, "bot_id": 123, "chat_id": 456},
        )
        return claim(path, did, receipt, **kwargs)

    monkeypatch.setattr(storage, "_claim_verified", peer_confirms)
    transport = FakeTransport()
    assert send(prepared, transport)["result"] == "replay"
    assert transport.calls == [("configuration",), ("bot", 123)]


def test_frozen_binding_mismatch_detected_by_readonly_recompute(prepared, monkeypatch):
    captures, journal, outbox, ledger, _, _, did = prepared
    original = storage.load_delivery
    monkeypatch.setattr(
        storage,
        "load_delivery",
        lambda *a, **kw: {**original(*a, **kw), "message_sha256": "0" * 64},
    )
    with pytest.raises(DeliveryError, match="recompute_mismatch"):
        application.recompute(captures, journal, outbox, ledger, did)
    transport = FakeTransport()
    with pytest.raises(DeliveryError, match="recompute_mismatch"):
        send(prepared, transport)
    assert transport.calls == []


def test_invalid_identifier_before_origin_reads(prepared):
    captures, journal, outbox, ledger, _, cid, _ = prepared
    with pytest.raises(DeliveryError, match="invalid_field"):
        application.prepare(captures, journal, outbox, ledger, "invalid", cid, "private-operator")


def test_budget_expiration_is_fixed_safe_category():
    budget = application._Budget(1)
    budget.deadline = 0
    with pytest.raises(DeliveryError, match="deadline_exceeded"):
        budget.remaining()
