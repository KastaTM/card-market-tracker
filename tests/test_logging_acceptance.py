"""Adversarial checks for the public JSON logging boundary."""

import json
import logging
from uuid import UUID

import pytest

from card_market_tracker.logging_json import configure_logging


def test_unstructured_message_and_extra_fields_cannot_leak_secrets(
    capsys: pytest.CaptureFixture[str],
) -> None:
    run_id = "00000000-0000-4000-8000-000000000001"
    configure_logging(run_id=run_id)
    logger = logging.getLogger("card_market_tracker")

    logger.error(
        "CMT_TELEGRAM_TOKEN=sentinel-secret",
        extra={"event": "cli.version", "token": "another-sentinel-secret"},
    )
    output = capsys.readouterr().err

    assert "sentinel-secret" not in output
    assert "another-sentinel-secret" not in output
    records = [json.loads(line) for line in output.splitlines() if line.strip()]
    assert len(records) == 1
    assert records[0]["event"] == "cli.version"
    assert records[0]["run_id"] == run_id


def test_secret_like_event_is_replaced_with_safe_fallback(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging(run_id="00000000-0000-4000-8000-000000000002")
    logger = logging.getLogger("card_market_tracker")

    logger.error("safe message", extra={"event": "secrets.sentinel-secret"})
    output = capsys.readouterr().err
    records = [json.loads(line) for line in output.splitlines() if line.strip()]

    assert len(records) == 1
    assert "sentinel-secret" not in output
    assert records[0]["event"] == "unstructured"


def test_invalid_run_id_never_reaches_log_output(
    capsys: pytest.CaptureFixture[str],
) -> None:
    candidate = "token-sentinel-secret"
    try:
        configure_logging(run_id=candidate)
    except ValueError as error:
        assert candidate not in str(error)
        return

    logger = logging.getLogger("card_market_tracker")
    logger.warning("safe message", extra={"event": "cli.version"})
    output = capsys.readouterr().err
    records = [json.loads(line) for line in output.splitlines() if line.strip()]

    assert len(records) == 1
    assert candidate not in output
    UUID(records[0]["run_id"])


def test_reconfiguring_logging_does_not_duplicate_event(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging(run_id="00000000-0000-4000-8000-000000000003")
    configure_logging(run_id="00000000-0000-4000-8000-000000000004")
    logger = logging.getLogger("card_market_tracker")

    logger.warning("safe diagnostic", extra={"event": "cli.version"})
    output = capsys.readouterr().err
    records = [json.loads(line) for line in output.splitlines() if line.strip()]

    assert len(records) == 1
    assert records[0]["run_id"] == "00000000-0000-4000-8000-000000000004"


def test_nested_unhashable_extras_are_omitted_without_traceback(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging(run_id="00000000-0000-4000-8000-000000000005")
    logger = logging.getLogger("card_market_tracker")

    logger.error(
        "safe message",
        extra={
            "event": "cli.version",
            "error_category": {"marker": "category-sentinel-secret"},
            "result": ["result-sentinel-secret"],
            "duration_ms": {"marker": "duration-sentinel-secret"},
        },
    )
    output = capsys.readouterr().err
    records = [json.loads(line) for line in output.splitlines() if line.strip()]

    assert len(records) == 1
    assert "sentinel-secret" not in output
    assert "Traceback" not in output
    assert "error_category" not in records[0]
    assert "result" not in records[0]
    assert "duration_ms" not in records[0]


def test_hostile_extra_comparison_cannot_break_logging(
    capsys: pytest.CaptureFixture[str],
) -> None:
    class HostileValue:
        def __eq__(self, _other: object) -> bool:
            raise RuntimeError("comparison-sentinel-secret")

    configure_logging(run_id="00000000-0000-4000-8000-000000000006")
    logger = logging.getLogger("card_market_tracker")

    logger.error(
        "safe message",
        extra={
            "event": HostileValue(),
            "component": HostileValue(),
            "error_category": HostileValue(),
            "result": HostileValue(),
        },
    )
    output = capsys.readouterr().err
    records = [json.loads(line) for line in output.splitlines() if line.strip()]

    assert len(records) == 1
    assert "comparison-sentinel-secret" not in output
    assert "Traceback" not in output
    assert records[0]["event"] == "unstructured"
    assert records[0]["component"] == "cli"
