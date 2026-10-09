"""P1a additive logging contract: bounded metrics and hostile extras."""

import json
import logging

import pytest

from card_market_tracker.logging_json import configure_logging


@pytest.mark.parametrize("value", [-1, True, 10001, "sentinel-secret", {"raw": "secret"}])
def test_catalog_counts_omit_untrusted_values(value: object, capsys: pytest.CaptureFixture[str]):
    logger = configure_logging("00000000-0000-4000-8000-000000000001")
    logger.info("raw-secret", extra={"event": "catalog.completed", "input_count": value})
    record = json.loads(capsys.readouterr().err)
    assert record["event"] == "catalog.completed"
    assert "input_count" not in record
    assert "secret" not in json.dumps(record)


def test_catalog_event_allowlist_and_counts(capsys: pytest.CaptureFixture[str]):
    logger = configure_logging("00000000-0000-4000-8000-000000000001")
    logger.error(
        "raw-secret",
        extra={
            "event": "catalog.completed",
            "result": "mixed",
            "duration_ms": 0,
            "input_count": 3,
            "accepted_count": 1,
            "candidate_count": 1,
            "rejected_count": 1,
            "error_category": "invalid_field",
            "provider_name": "sentinel-secret",
            "payload": {"token": "secret"},
        },
    )
    record = json.loads(capsys.readouterr().err)
    assert record["result"] == "mixed"
    assert record["error_category"] == "invalid_field"
    assert record["duration_ms"] == 0
    assert record["input_count"] == 3
    assert record["accepted_count"] == record["candidate_count"] == record["rejected_count"] == 1
    assert "secret" not in json.dumps(record)
    assert len(logging.getLogger("card_market_tracker").handlers) == 1
