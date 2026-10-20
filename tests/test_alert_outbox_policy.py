"""Independent identity vectors and full intrinsic/window validation probes."""

import copy
import hashlib
import json

import pytest
from test_alert_outbox_application import admitted as outbox_fixture

from card_market_tracker.alerts import policy, render
from card_market_tracker.alerts.errors import OutboxError
from card_market_tracker.discovery import journal_storage

admitted = outbox_fixture


@pytest.fixture
def event(admitted):
    _, journal, _, cid, *_ = admitted
    return journal_storage.get(journal, cid)["comparison"]["events"][0]


def test_independent_exact_identity_vector():
    expected = "alt1:acb91b4f47f23723329afbc7dde2857cf3da79e52446485784570284a0f2826f"
    assert policy.alert_id("local-preview", "evt3:" + "0" * 64) == expected
    preimage = (
        b'{"destination_key":"local-preview","event_id":"evt3:'
        b'0000000000000000000000000000000000000000000000000000000000000000",'
        b'"identity_version":1}'
    )
    assert "alt1:" + hashlib.sha256(preimage).hexdigest() == expected
    assert policy.alert_id("other", "evt3:" + "0" * 64) != expected


@pytest.mark.parametrize(
    "value", [None, True, "", "A", "a/b", "a.b", "a@b", "a b", "a\n", "á", "a" * 65]
)
def test_destination_grammar(value):
    with pytest.raises(OutboxError, match="invalid_field"):
        policy.destination(value)


def test_destination_boundaries():
    assert policy.destination("a") == "a"
    assert policy.destination("a" * 64) == "a" * 64
    assert policy.destination("local_preview-1") == "local_preview-1"


@pytest.mark.parametrize("prefix", ["evt3:", "alt1:", "cmp3:"])
@pytest.mark.parametrize("suffix", ["0" * 63, "0" * 65, "A" * 64, "g" * 64, "0" * 64 + "\n"])
def test_strict_token_grammar(prefix, suffix):
    with pytest.raises(OutboxError):
        policy.token(prefix + suffix, prefix)


def test_exact_intrinsic_intent_and_safe_frozen_message(event):
    row = policy.prepare_event(event, "local-preview", event["evidence"]["comparison_id"])
    intent = json.loads(row["intent_json"])
    assert set(intent) == {
        "version",
        "policy_version",
        "renderer_version",
        "channel",
        "event_id",
        "type",
        "reference",
        "status",
        "category",
        "cmt_id",
        "current_batch_id",
        "captured_at",
        "first_observed_in_window_at",
        "profile",
        "evidence_level",
        "mode",
    }
    assert "comparison_id" not in intent and "history" not in intent
    assert intent["profile"] == "synthetic_multi_revision_v1"
    assert intent["mode"] == "synthetic" and intent["evidence_level"] == "producer_declared"
    assert intent["renderer_version"] == 1 and type(intent["renderer_version"]) is int
    assert row["intent_sha256"] == hashlib.sha256(row["intent_json"].encode("ascii")).hexdigest()
    assert row["message_sha256"] == hashlib.sha256(row["message_text"].encode("utf-8")).hexdigest()
    assert row["event_sha256"] == hashlib.sha256(row["event_json"].encode("ascii")).hexdigest()
    message = row["message_text"]
    assert "SYNTHETIC demonstration" in message and "Accepted set reference" in message
    assert "First observed in selected comparison window." in message
    assert len(message.encode("utf-8")) <= 4096
    assert render.render(intent) == message
    frozen = policy.validate_intent(intent)
    intent["reference"]["external_id"] = "mutated"
    assert frozen["reference"]["external_id"] != "mutated"


def test_candidate_is_explicit_and_not_an_accepted_entity(admitted):
    _, journal, _, cid, *_ = admitted
    candidate = journal_storage.get(journal, cid)["comparison"]["events"][1]
    row = policy.prepare_event(candidate, "local-preview", cid)
    assert "Unaccepted candidate reference" in row["message_text"]
    intent = json.loads(row["intent_json"])
    assert intent["cmt_id"] is None and intent["status"] == "candidate"


@pytest.mark.parametrize(
    "attack",
    [
        "extra",
        "evidence-extra",
        "history",
        "current",
        "indexes",
        "profile",
        "proof",
        "clock",
        "id",
        "type",
        "status",
        "category",
        "target",
        "reference",
    ],
)
def test_full_standalone_event_validation(event, attack):
    event = copy.deepcopy(event)
    cid = event["evidence"]["comparison_id"]
    if attack == "extra":
        event["extra"] = "untrusted"
    elif attack == "evidence-extra":
        event["evidence"]["extra"] = "untrusted"
    elif attack == "history":
        event["evidence"]["history"] = []
    elif attack == "current":
        event["evidence"]["current"]["acquisition"]["outcome"] = "partial"
    elif attack == "indexes":
        event["evidence"]["current_record_indexes"] = [False]
    elif attack == "profile":
        event["evidence"]["current"]["profile"] = "untrusted"
    elif attack == "proof":
        event["evidence"]["current"]["extraction_proof"] = {"verified": True}
    elif attack == "clock":
        event["captured_at"] = "later"
    elif attack == "id":
        event["event_id"] = "evt2:" + "0" * 64
    elif attack == "type":
        event["type"] = "PRICE_CHANGED"
    elif attack == "status":
        event["status"] = "candidate"
    elif attack == "category":
        event["category"] = "arbitrary"
    elif attack == "target":
        event["cmt_id"] = None
    elif attack == "reference":
        event["reference"]["external_id"] = "unsafe\nreference"
    with pytest.raises(OutboxError):
        policy.prepare_event(event, "local-preview", cid)


@pytest.mark.parametrize(
    "key,value",
    [
        ("version", True),
        ("renderer_version", True),
        ("renderer_version", 2),
        ("channel", "telegram"),
        ("policy_version", "other"),
        ("profile", "unknown"),
        ("mode", "pinned"),
        ("evidence_level", "verified_local_pinned_bundle"),
        ("status", "sent"),
        ("type", "OTHER"),
        ("category", "unexpected"),
        ("first_observed_in_window_at", "bad"),
        ("current_batch_id", "bad"),
        ("event_id", "evt3:" + "F" * 64),
    ],
)
def test_intent_exact_contract(event, key, value):
    row = policy.prepare_event(event, "local-preview", event["evidence"]["comparison_id"])
    intent = json.loads(row["intent_json"])
    intent[key] = value
    with pytest.raises(OutboxError):
        policy.validate_intent(intent)


def test_intent_cannot_carry_window_or_unknown_fields(event):
    row = policy.prepare_event(event, "local-preview", event["evidence"]["comparison_id"])
    intent = json.loads(row["intent_json"])
    intent["comparison_id"] = event["evidence"]["comparison_id"]
    with pytest.raises(OutboxError):
        policy.validate_intent(intent)


def test_safe_display_escapes_control_bidi_and_backslash():
    assert (
        render._safe("a\r\nb\x1b\x00\u202e\u2066\u200b\\")
        == r"a\r\nb\u001b\u0000\u202e\u2066\u200b\\"
    )
    assert render._safe("café 🃏") == "café 🃏"
    assert render._safe(None) == "null"


def test_renderer_byte_limit_not_character_limit(event, monkeypatch):
    row = policy.prepare_event(event, "local-preview", event["evidence"]["comparison_id"])
    intent = json.loads(row["intent_json"])
    # Exercise the renderer's independent defensive cap after upstream validation.
    monkeypatch.setattr(policy, "validate_intent", lambda value: value)
    intent["reference"]["external_id"] = "🃏" * 1000
    with pytest.raises(OutboxError, match="input_limit"):
        render.render(intent)
    intent["reference"]["external_id"] = "🃏"
    assert "🃏" in render.render(intent)


def test_standalone_event_byte_limit_before_materialization(event):
    event["oversized"] = "x" * (16 * 1024 * 1024)
    with pytest.raises(OutboxError, match="input_limit"):
        policy.prepare_event(event, "local-preview", event["evidence"]["comparison_id"])
