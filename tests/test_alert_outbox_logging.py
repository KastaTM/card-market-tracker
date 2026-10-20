"""The outbox log boundary keeps sensitive evidence out of diagnostics."""

import json
import logging

import pytest

from card_market_tracker.logging_json import configure_logging


@pytest.mark.parametrize(
    "operation",
    (
        "arguments",
        "init",
        "enqueue",
        "get",
        "list",
        "evidence_list",
        "evidence_get",
        "preview",
        "verify",
        "recompute",
        "backup",
        "restore",
    ),
)
def test_outbox_diagnostics_allow_only_safe_metadata(operation, capsys):
    configure_logging("00000000-0000-4000-8000-000000000001")
    logger = logging.getLogger("card_market_tracker")
    try:
        raise ValueError("raw-exception-sentinel")
    except ValueError:
        logger.error(
            "raw-message-sentinel",
            exc_info=True,
            extra={
                "event": "alert.outbox.completed",
                "operation": "alert_outbox_" + operation,
                "result": "inserted",
                "duration_ms": 1,
                "outbox_alerts_count": 2,
                "outbox_associations_count": 4,
                "outbox_events_count": 2,
                "destination_key": "destination-sentinel",
                "message_text": "message-sentinel",
                "reference": {"external_id": "reference-sentinel"},
                "path": "path-sentinel",
                "payload": {"raw": "payload-sentinel"},
                "sql": "SQL-sentinel",
            },
        )
    stderr = capsys.readouterr().err
    assert "sentinel" not in stderr and "Traceback" not in stderr
    record = json.loads(stderr)
    assert record["event"] == "alert.outbox.completed"
    assert record["operation"] == "alert_outbox_" + operation
    assert record["outbox_alerts_count"] == 2
    assert record["outbox_associations_count"] == 4
    assert record["outbox_events_count"] == 2


@pytest.mark.parametrize("bad", (True, False, -1, 100000001, "1", None, [], {}))
def test_invalid_outbox_log_counters_are_omitted(bad, capsys):
    configure_logging("00000000-0000-4000-8000-000000000001")
    logging.getLogger("card_market_tracker").error(
        "ignored",
        extra={
            "event": "alert.outbox.completed",
            "operation": "alert_outbox_verify",
            "result": "error",
            "error_category": "storage_corrupt",
            "outbox_alerts_count": bad,
            "outbox_associations_count": bad,
            "outbox_events_count": bad,
        },
    )
    record = json.loads(capsys.readouterr().err)
    assert not any(key.startswith("outbox_") for key in record)
    assert record["error_category"] == "storage_corrupt"


def test_outbox_event_counter_has_narrower_limit(capsys):
    configure_logging("00000000-0000-4000-8000-000000000001")
    logging.getLogger("card_market_tracker").info(
        "ignored",
        extra={
            "event": "alert.outbox.completed",
            "outbox_alerts_count": 100000000,
            "outbox_associations_count": 100000000,
            "outbox_events_count": 1001,
        },
    )
    record = json.loads(capsys.readouterr().err)
    assert record["outbox_alerts_count"] == 100000000
    assert record["outbox_associations_count"] == 100000000
    assert "outbox_events_count" not in record
