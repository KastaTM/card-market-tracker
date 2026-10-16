"""V2 logs expose only bounded operational metrics and fixed categories."""

import json
import logging

import pytest

from card_market_tracker.logging_json import JsonFormatter

RUN = "22222222-2222-4222-8222-222222222222"


def formatted(**extras):
    record = logging.LogRecord(
        "card_market_tracker", logging.INFO, __file__, 1, "secret raw text", (), None
    )
    for key, value in extras.items():
        setattr(record, key, value)
    return json.loads(JsonFormatter(RUN).format(record))


def test_scoped_event_operation_safe_metrics_and_payload_redaction():
    payload = formatted(
        event="discovery.scoped.completed",
        operation="discover_scoped",
        result="discoveries",
        batch_count=33,
        scoped_validated_record_count=33000,
        scoped_selected_record_count=33000,
        event_count=1000,
        duration_ms=1,
        selector="secret selector",
        db="/secret/database",
        tokens=["secret-token"],
        sql="SELECT secret",
        payload="secret names",
        names=["secret"],
        reference={"external_id": "secret"},
        scope={"selected": ["secret/path"]},
    )
    assert payload["event"] == "discovery.scoped.completed"
    assert payload["operation"] == "discover_scoped"
    assert payload["batch_count"] == 33
    assert payload["scoped_validated_record_count"] == 33000
    assert payload["scoped_selected_record_count"] == 33000
    assert payload["event_count"] == 1000
    assert "secret" not in json.dumps(payload)
    assert set(payload) == {
        "timestamp",
        "level",
        "event",
        "component",
        "run_id",
        "operation",
        "result",
        "batch_count",
        "scoped_validated_record_count",
        "scoped_selected_record_count",
        "event_count",
        "duration_ms",
    }


@pytest.mark.parametrize(
    "field,maximum",
    [
        ("batch_count", 33),
        ("scoped_validated_record_count", 33000),
        ("scoped_selected_record_count", 33000),
        ("event_count", 1000),
    ],
)
@pytest.mark.parametrize("bad", [True, -1, 1.0, "secret", None, 33001])
def test_bounded_metrics(field, maximum, bad):
    value = maximum + 1 if bad == 33001 else bad
    assert field not in formatted(**{field: value})


@pytest.mark.parametrize(
    "category",
    [
        "unsupported_evidence",
        "scope_mismatch",
        "unit_missing",
        "ambiguous_unit",
        "incomplete_evidence",
        "chronology",
        "storage_corrupt",
        "storage_locked",
        "storage_timeout",
        "storage_schema",
        "input_io",
    ],
)
def test_categories_allowlisted(category):
    assert formatted(error_category=category)["error_category"] == category


def test_arbitrary_operation_event_category_are_not_echoed():
    payload = formatted(
        event="secret-event", operation="secret-operation", error_category="secret-error"
    )
    assert payload["event"] == "unstructured"
    assert "operation" not in payload and "error_category" not in payload
    assert "secret" not in json.dumps(payload)
