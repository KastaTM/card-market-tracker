"""Compatible strict Discovery logging counts and hostile redaction boundary."""

import json
import logging

import pytest

from card_market_tracker.logging_json import JsonFormatter


@pytest.mark.parametrize(
    "field,maximum",
    [
        ("batch_count", 33),
        ("discovery_observation_count", 33000),
        ("event_count", 1000),
    ],
)
def test_new_count_limits_do_not_widen_existing_fields(field, maximum):
    formatter = JsonFormatter("11111111-1111-4111-8111-111111111111")
    for value in (-1, True, maximum + 1, "1", 1.5, None, 0, maximum):
        record = logging.makeLogRecord(
            {
                "event": "discovery.completed",
                "result": "discoveries",
                field: value,
                "observation_count": 33000,
                "batch_id": "private-id",
                "path": "private-path",
                "msg": "private-message",
                "sql": "DROP TABLE records",
                "exc_text": "private-exception",
            }
        )
        output = formatter.format(record)
        payload = json.loads(output)
        assert (field in payload) == (type(value) is int and 0 <= value <= maximum)
        assert "observation_count" not in payload
        assert "private" not in output and "DROP TABLE" not in output


@pytest.mark.parametrize("result", ["baseline", "no_discoveries", "discoveries", "error"])
def test_discovery_outcomes_are_distinct_and_allowlisted(result):
    record = logging.makeLogRecord(
        {
            "event": "discovery.completed",
            "result": result,
            "error_category": "context_mismatch",
        }
    )
    payload = json.loads(JsonFormatter("11111111-1111-4111-8111-111111111111").format(record))
    assert payload["event"] == "discovery.completed" and payload["result"] == result
    assert payload["error_category"] == "context_mismatch"
