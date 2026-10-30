"""Author oracles for literal-NUL identity and complete local semantic reconstruction."""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any

import pytest
from test_watchlist_alert_domain import evidence

from card_market_tracker.watchlist_alerts import policy as source_policy
from card_market_tracker.watchlist_delivery import policy
from card_market_tracker.watchlist_delivery.errors import DeliveryError


def route(alias: str = "private") -> dict[str, Any]:
    return {
        "route_version": 1,
        "provider": "telegram",
        "destination_key": alias,
        "bot_id": 1,
        "chat_id": 2,
        "chat_type": "private",
        "operator_attested": True,
    }


def content(operation: str = "prepare") -> dict[str, Any]:
    bundle = evidence()
    prepared = source_policy.prepare(bundle, "private")
    alert = {
        key: prepared[key]
        for key in (
            "alert_id",
            "destination_key",
            "signal_id",
            "policy_version",
            "renderer_version",
            "channel",
            "state",
            "intent_sha256",
            "message_text",
            "message_sha256",
        )
    }
    alert.update(
        intent=json.loads(prepared["intent_json"]), first_prepared_at="2026-10-23T12:00:00.000000Z"
    )
    return policy.prepare(alert, bundle, route(), operation=operation)


@pytest.mark.parametrize(
    "char,expected",
    [
        ("0", "b08e2920077a2f36ba634b32c0f1215e952063c55cfc99320ab55fbbdf9d36f5"),
        ("f", "810e8528fcea94a8ee848b56cb50ae04ff35bbaef05de8f667bddda896cac9d8"),
    ],
)
def test_exact_identity_literal_nul_oracle(char: str, expected: str) -> None:
    signal = "wsig1_" + char * 64
    preimage = (
        b'CMT_WATCHLIST_TELEGRAM_DELIVERY_V1\x00{"identity_version":1,"provider":"telegram","signal_id":"wsig1_'
        + char.encode() * 64
        + b'"}'
    )
    assert len(preimage) == 164
    assert preimage[34] == 0
    assert hashlib.sha256(preimage).hexdigest() == expected
    assert policy.delivery_id(signal) == "wtdl1_" + expected


def test_complete_semantics_binding_and_operational_projection() -> None:
    row = content()
    assert policy.validate_prepared(row) == row
    assert len(row["binding"]) == 18
    assert row["binding"]["source_alert_sha256"]
    assert (
        json.loads(row["consent_json"])["acknowledgement"] == "SYNTHETIC_HISTORICAL_DEMONSTRATION"
    )
    assert row["message_text"].startswith("SYNTHETIC — DEMONSTRATION ONLY")


@pytest.mark.parametrize(
    "field",
    [
        "entry_json",
        "intent_json",
        "evidence_json",
        "message_text",
        "route_json",
        "consent_json",
        "binding",
        "binding_sha256",
        "operation",
        "authority_version",
    ],
)
def test_every_frozen_field_is_rebuilt(field: str) -> None:
    row = copy.deepcopy(content())
    if field == "binding":
        row[field]["revision"] = True
    elif field == "authority_version":
        row[field] = True
    elif field == "operation":
        row[field] = "send"
    else:
        row[field] += " "
    with pytest.raises(DeliveryError):
        policy.validate_prepared(row)


@pytest.mark.parametrize(
    "key,value",
    [
        ("bot_id", True),
        ("chat_id", 0),
        ("chat_id", 2**52),
        ("route_version", True),
        ("operator_attested", 1),
        ("provider", "other"),
        ("chat_type", "group"),
        ("destination_key", "Private"),
    ],
)
def test_route_types_exact(key: str, value: object) -> None:
    selected = route()
    selected[key] = value
    with pytest.raises(DeliveryError):
        policy.route(selected)


@pytest.mark.parametrize(
    "value",
    [
        "2026-02-30T00:00:00.000000Z",
        "2026-01-01T00:00:00Z",
        "2026-01-01T00:00:00.000000+00:00",
        "0000-01-01T00:00:00.000000Z",
        "2026-01-01T00:00:60.000000Z",
        True,
    ],
)
def test_strict_operational_timestamp(value: object) -> None:
    with pytest.raises(DeliveryError, match="invalid_timestamp"):
        policy.timestamp(value)


@pytest.mark.parametrize(
    "raw,category",
    [
        (' {"v":1}', "invalid_json"),
        ('{"v":1,"v":1}', "duplicate_key"),
        ('{"v":NaN}', "invalid_json"),
        ('"é"', "invalid_json"),
    ],
)
def test_document_decoder_strict(raw: str, category: str) -> None:
    with pytest.raises(DeliveryError, match=category):
        policy.decode(raw, 100)
