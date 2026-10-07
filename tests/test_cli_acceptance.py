"""Black-box acceptance checks for the Foundation command line interface."""

import json
import socket
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

import card_market_tracker.cli as cli_module
from card_market_tracker.cli import main


def _records(output: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in output.splitlines() if line.strip()]


def test_version_succeeds_without_configuration(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("CMT_LOG_LEVEL", "invalid-secret-value")

    exit_code = main(["--version"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.strip()
    assert "invalid-secret-value" not in captured.out + captured.err


def test_diagnose_is_local_and_emits_contract_log(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CMT_LOG_LEVEL", raising=False)
    monkeypatch.delenv("CMT_WORK_DIR", raising=False)

    def reject_network(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("diagnose attempted a network connection")

    monkeypatch.setattr(socket, "create_connection", reject_network)
    monkeypatch.setattr(socket.socket, "connect", reject_network)

    assert main(["diagnose"]) == 0
    records = _records(capsys.readouterr().err)

    assert records
    for record in records:
        assert isinstance(record["timestamp"], str)
        timestamp = datetime.fromisoformat(record["timestamp"].replace("Z", "+00:00"))
        assert timestamp.utcoffset() == timedelta(0)
        assert isinstance(record["level"], str)
        assert isinstance(record["event"], str)
        assert isinstance(record["component"], str)
        assert isinstance(record["run_id"], str) and record["run_id"]

    completed = [record for record in records if record["event"] == "diagnose.completed"]
    assert len(completed) == 1
    assert completed[0]["result"] == "ok"
    assert isinstance(completed[0]["duration_ms"], int)
    assert completed[0]["duration_ms"] >= 0
    assert len({record["run_id"] for record in records}) == 1


def test_invalid_configuration_exits_nonzero_without_disclosing_value(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("CMT_LOG_LEVEL", "invalid-secret-value")

    exit_code = main(["diagnose"])
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "invalid-secret-value" not in captured.out + captured.err
    records = _records(captured.err)
    invalid = [record for record in records if record["event"] == "config.invalid"]
    assert len(invalid) == 1
    assert isinstance(invalid[0]["error_category"], str)
    assert invalid[0]["error_category"]


def test_missing_work_dir_fails_without_disclosing_configured_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CMT_LOG_LEVEL", raising=False)
    monkeypatch.setenv("CMT_WORK_DIR", "secret-missing-directory")

    assert main(["diagnose"]) == 2
    captured = capsys.readouterr()
    assert "secret-missing-directory" not in captured.out + captured.err
    invalid = [record for record in _records(captured.err) if record["event"] == "config.invalid"]
    assert len(invalid) == 1
    assert invalid[0]["error_category"]


def test_repeated_invocations_do_not_duplicate_handlers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CMT_LOG_LEVEL", raising=False)
    monkeypatch.delenv("CMT_WORK_DIR", raising=False)

    assert main(["diagnose"]) == 0
    first = _records(capsys.readouterr().err)
    assert main(["diagnose"]) == 0
    second = _records(capsys.readouterr().err)

    assert len([record for record in first if record["event"] == "diagnose.completed"]) == 1
    assert len([record for record in second if record["event"] == "diagnose.completed"]) == 1
    assert first[0]["run_id"] != second[0]["run_id"]


def test_unexpected_local_probe_failure_exits_one_without_traceback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CMT_LOG_LEVEL", raising=False)
    monkeypatch.setenv("CMT_WORK_DIR", str(tmp_path))

    def fail_probe(*_args: object, **_kwargs: object) -> None:
        raise OSError("probe-sentinel-secret")

    monkeypatch.setattr(cli_module.tempfile, "TemporaryFile", fail_probe)

    assert main(["diagnose"]) == 1
    captured = capsys.readouterr()
    assert "probe-sentinel-secret" not in captured.out + captured.err
    assert "Traceback" not in captured.out + captured.err
    records = _records(captured.err)
    failures = [record for record in records if record["event"] == "diagnose.completed"]
    assert len(failures) == 1
    assert failures[0]["result"] == "error"
    assert failures[0]["error_category"] == "local_execution"
    assert isinstance(failures[0]["duration_ms"], int)
    assert failures[0]["duration_ms"] >= 0
