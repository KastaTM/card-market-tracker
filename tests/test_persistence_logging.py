"""Allowlisted storage telemetry never leaks attempt evidence or raw failures."""

import json
import logging

import pytest

from card_market_tracker.logging_json import configure_logging


def test_storage_metrics_redact_identifiers_and_exceptions(capsys):
    logger = configure_logging("00000000-0000-4000-8000-000000000001")
    try:
        raise RuntimeError("sentinel-private-exception")
    except RuntimeError:
        logger.error(
            "sentinel-private-message",
            exc_info=True,
            extra={
                "event": "persistence.completed",
                "operation": "persist",
                "result": "replay",
                "duration_ms": 2,
                "input_count": 3,
                "new_observation_count": 0,
                "new_entity_count": 0,
                "new_batch_count": 0,
                "error_category": "replay_conflict",
                "batch_id": "sentinel-private-token",
                "path": "sentinel-private-path",
                "sql": "sentinel-private-sql",
                "reference": "sentinel-private-reference",
                "payload": {"secret": "sentinel-private-payload"},
            },
        )
    raw = capsys.readouterr().err
    event = json.loads(raw)
    assert "sentinel-private" not in raw
    assert event["event"] == "persistence.completed"
    assert event["operation"] == "persist" and event["result"] == "replay"
    assert event["new_observation_count"] == event["new_entity_count"] == 0
    assert event["new_batch_count"] == 0
    assert len(logging.getLogger("card_market_tracker").handlers) == 1


@pytest.mark.parametrize("value", [True, -1, 10001, None, "sentinel-private", {}])
def test_failed_storage_omits_unconfirmed_or_invalid_counts(value, capsys):
    logger = configure_logging("00000000-0000-4000-8000-000000000001")
    logger.error(
        "",
        extra={
            "event": "persistence.completed",
            "operation": "sentinel-private",
            "result": "error",
            "new_observation_count": value,
            "new_entity_count": value,
            "new_batch_count": value,
            "observation_count": value,
            "error_category": "sentinel-private",
        },
    )
    raw = capsys.readouterr().err
    event = json.loads(raw)
    assert "sentinel-private" not in raw
    assert not (
        {
            "operation",
            "error_category",
            "new_observation_count",
            "new_entity_count",
            "new_batch_count",
            "observation_count",
        }
        & event.keys()
    )


@pytest.mark.parametrize(
    "category",
    [
        "capture_required",
        "capture_conflict",
        "synthetic_only",
        "replay_conflict",
        "storage_schema",
        "storage_locked",
        "storage_io",
        "storage_corrupt",
        "storage_timeout",
        "unsafe_destination",
        "resolution_mismatch",
    ],
)
def test_storage_error_categories_are_stable(category, capsys):
    logger = configure_logging("00000000-0000-4000-8000-000000000001")
    logger.error("", extra={"event": "persistence.completed", "error_category": category})
    assert json.loads(capsys.readouterr().err)["error_category"] == category
