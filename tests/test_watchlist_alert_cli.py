"""Installed-process isolation, exact CLI responses and redacted P8c logs."""

from __future__ import annotations

import json
import logging
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

from card_market_tracker.cli import main
from card_market_tracker.logging_json import configure_logging
from card_market_tracker.watchlist import application as watch_app
from card_market_tracker.watchlist import storage as watch_storage
from card_market_tracker.watchlist_journal import application as journal_app
from card_market_tracker.watchlist_journal import storage as journal_storage

FIXTURES = Path(__file__).parent / "fixtures"
TARGET = "541b9d13-9669-4973-8413-397bea14c045"
GROUP = "watchlist-alert-outbox"


@pytest.fixture
def pipeline(tmp_path):
    manifest = json.loads((FIXTURES / "synthetic_manifest.json").read_text())
    origin, journal, outbox = (tmp_path / n for n in ("watch.db", "journal.db", "outbox.db"))
    watch_storage.initialize(origin)
    entry = watch_app.add(
        origin,
        manifest,
        TARGET,
        {"target_price_minor": 1000, "restock_enabled": True},
        request_token="p8c-cli",
    )["entry"]
    journal_storage.initialize(journal)
    previous = None
    signals = []
    for index, stock in enumerate(
        ("OUT_OF_STOCK", "AVAILABLE", "AVAILABLE", "OUT_OF_STOCK", "AVAILABLE")
    ):
        sample = {
            "version": 1,
            "provenance": "synthetic",
            "sample_id": "cli-" + str(index),
            "cmt_id": TARGET,
            "series_key": "cli-series",
            "observed_at": f"2026-10-23T12:0{index}:00Z",
            "currency": "EUR",
            "unit_price_minor": 900,
            "shipping_minor": 100,
            "stock": stock,
        }
        result = journal_app.record(
            journal,
            origin,
            manifest,
            entry["watch_id"],
            sample,
            previous,
            revision=1,
            as_of=sample["observed_at"],
            timeout=5,
        )
        signals.extend(result["signal_ids"])
        previous = sample
    assert len(signals) == 4
    return origin, journal, outbox, signals


def test_all_cli_operations_original_nonmutation_and_replay(
    pipeline, tmp_path, capsys, monkeypatch
):
    origin, journal, outbox, signals = pipeline
    before = origin.read_bytes(), journal.read_bytes()

    def denied(*args, **kwargs):
        pytest.fail("product socket attempted")

    monkeypatch.setattr(socket, "socket", denied)
    monkeypatch.setattr(socket, "create_connection", denied)

    def call(operation, *flags, target=outbox, code=0):
        result = main(
            [GROUP, operation, "--outbox-db", str(target), "--timeout", "5", *map(str, flags)]
        )
        captured = capsys.readouterr()
        assert result == code, (captured.out, captured.err)
        payload, record = json.loads(captured.out), json.loads(captured.err)
        assert record["event"] == "watchlist.alert_outbox.completed"
        assert record["operation"] == "watchlist_alert_outbox_" + operation.replace("-", "_")
        assert str(tmp_path) not in captured.err and TARGET not in captured.err
        assert "local-preview" not in captured.err and "wsig1_" not in captured.err
        assert payload["version"] == 1 and payload["operation"] == operation
        return payload

    call("init")
    flags = (
        "--watchlist-db",
        origin,
        "--journal-db",
        journal,
        "--manifest",
        FIXTURES / "synthetic_manifest.json",
        "--destination-key",
        "local-preview",
    )
    alerts = [call("enqueue", *flags, "--signal-id", signal)["alert_id"] for signal in signals]
    frozen = outbox.read_bytes()
    assert call("enqueue", *flags, "--signal-id", signals[0])["result"] == "replayed"
    assert outbox.read_bytes() == frozen
    selected = call("get", "--alert-id", alerts[0])["alert"]
    assert set(selected) == {
        "alert_id",
        "destination_key",
        "signal_id",
        "policy_version",
        "renderer_version",
        "channel",
        "state",
        "intent",
        "intent_sha256",
        "message_text",
        "message_sha256",
        "first_prepared_at",
    }
    assert call("preview", "--alert-id", alerts[0])["message_text"] == selected["message_text"]
    assert (
        call("evidence-get", "--alert-id", alerts[0])["evidence"]["signal"]["signal_id"]
        == signals[0]
    )
    first = call("list", "--limit", 1)
    assert len(first["items"]) == 1 and first["next_cursor"]
    assert set(first["items"][0]) == set(selected) - {"intent", "message_text"}
    assert call("list", "--cursor", first["next_cursor"])["items"]
    call("list", "--cursor", first["next_cursor"], "--destination-key", "other", code=2)
    assert call("verify")["counts"] == {"alerts": 4, "evidence": 4}
    call(
        "recompute",
        "--alert-id",
        alerts[0],
        "--watchlist-db",
        origin,
        "--journal-db",
        journal,
        "--manifest",
        FIXTURES / "synthetic_manifest.json",
    )
    assert outbox.read_bytes() == frozen
    backup, restored = tmp_path / "backup.db", tmp_path / "restored.db"
    call("backup", "--destination", backup)
    call("restore", "--destination", restored, target=backup)
    assert call("get", "--alert-id", alerts[0], target=restored)["alert"] == selected
    assert (origin.read_bytes(), journal.read_bytes()) == before


@pytest.mark.parametrize(
    "arguments",
    [
        [],
        ["send"],
        ["init"],
        ["list", "--outbox-db", "private", "--latest"],
        ["list", "--outbox-db", "private", "--limit", "private-sentinel"],
        ["init", "--outbox-d", "private"],
        ["li", "--outbox-db", "private"],
    ],
)
def test_parser_error_shape_and_privacy(arguments, capsys):
    assert main([GROUP, *arguments]) == 2
    captured = capsys.readouterr()
    assert json.loads(captured.out) == {
        "version": 1,
        "operation": GROUP,
        "result": "error",
        "error_category": "invalid_field",
    }
    assert json.loads(captured.err)["operation"] == "watchlist_alert_outbox_arguments"
    assert "private" not in captured.out + captured.err


@pytest.mark.parametrize("value", ["0", "-1", "6", "nan", "inf"])
def test_invalid_timeouts_do_not_create_file(value, tmp_path, capsys):
    destination = tmp_path / "invalid.db"
    assert main([GROUP, "init", "--outbox-db", str(destination), "--timeout", value]) == 2
    captured = capsys.readouterr()
    assert json.loads(captured.out)["error_category"] == "invalid_field"
    assert not destination.exists()


def test_deadline_includes_parsing_input_and_serialization(tmp_path, capsys, monkeypatch):
    from card_market_tracker import cli as root_cli
    from card_market_tracker.watchlist_alerts import cli

    parser = root_cli._parser

    def slow_parser(**kwargs):
        result = parser(**kwargs)
        time.sleep(0.02)
        return result

    monkeypatch.setattr(root_cli, "_parser", slow_parser)
    target = tmp_path / "late.db"
    assert main([GROUP, "init", "--outbox-db", str(target), "--timeout", "0.001"]) == 1
    assert json.loads(capsys.readouterr().out)["error_category"] == "storage_timeout"
    assert not target.exists()
    monkeypatch.setattr(root_cli, "_parser", parser)

    def slow_json(path):
        time.sleep(0.02)
        return {}

    monkeypatch.setattr(cli, "read_json", slow_json)
    assert (
        main(
            [
                GROUP,
                "enqueue",
                "--outbox-db",
                str(target),
                "--watchlist-db",
                "a",
                "--journal-db",
                "b",
                "--manifest",
                "c",
                "--signal-id",
                "x",
                "--destination-key",
                "local",
                "--timeout",
                "0.001",
            ]
        )
        == 1
    )
    assert json.loads(capsys.readouterr().out)["error_category"] == "storage_timeout"

    original_dump = cli.json.dumps

    def slow_dump(*args, **kwargs):
        result = original_dump(*args, **kwargs)
        time.sleep(0.02)
        return result

    monkeypatch.setattr(cli.json, "dumps", slow_dump)
    from card_market_tracker.watchlist_journal.storage import Budget

    budget = Budget(0.001)
    assert (
        cli._report(
            {"version": 1, "operation": "verify", "result": "ok"},
            "verify",
            time.perf_counter(),
            0,
            budget=budget,
        )
        == 1
    )
    assert json.loads(capsys.readouterr().out)["error_category"] == "storage_timeout"


BLOCKED_IMPORTS = """
import importlib.abc,sys,socket
class Deny(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.startswith('card_market_tracker.telegram_delivery'):
            raise AssertionError('Telegram import forbidden')
def denied(*a,**k):
    raise AssertionError('socket forbidden')
sys.meta_path.insert(0,Deny())
socket.socket=denied
socket.create_connection=denied
from card_market_tracker.cli import main
sys.exit(main(sys.argv[1:]))
"""


@pytest.mark.parametrize(
    "flags,expected",
    [
        (["--help"], 0),
        (["preview", "--help"], 0),
        ([], 2),
        (["send"], 2),
        (["verify", "--outbox-db", "missing.db"], 1),
    ],
)
def test_fresh_process_route_never_imports_telegram_or_opens_socket(tmp_path, flags, expected):
    completed = subprocess.run(
        [sys.executable, "-I", "-c", BLOCKED_IMPORTS, GROUP, *flags],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=20,
    )
    assert completed.returncode == expected, completed.stderr
    assert "Traceback" not in completed.stderr


@pytest.mark.parametrize("value", [True, False, -1, 100000001, "1", None])
def test_log_field_allowlist_and_invalid_counts(value, capsys):
    configure_logging("00000000-0000-4000-8000-000000000001")
    logging.getLogger("card_market_tracker").error(
        "",
        extra={
            "event": "watchlist.alert_outbox.completed",
            "operation": "watchlist_alert_outbox_verify",
            "result": "error",
            "error_category": "storage_corrupt",
            "duration_ms": 1,
            "watchlist_alerts_count": value,
            "watchlist_alert_evidence_count": 1,
            "delivery_id": "tdl1:" + "0" * 64,
            "attempt_count": 3,
            "path": "sentinel",
            "destination_key": "sentinel",
            "message_text": "sentinel",
        },
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.err)
    assert "sentinel" not in captured.err
    assert "delivery_id" not in payload and "attempt_count" not in payload
    assert "watchlist_alerts_count" not in payload
    assert "watchlist_alert_evidence_count" not in payload


def test_global_version_keeps_new_route_side_effect_free(tmp_path, capsys):
    target = tmp_path / "must-not-exist.db"
    assert main(["--version", GROUP, "init", "--outbox-db", str(target)]) == 0
    assert capsys.readouterr().out.startswith("cmt ")
    assert not target.exists()


def test_logging_follows_timely_response_with_one_completion(capsys, monkeypatch):
    from card_market_tracker.watchlist_alerts import cli
    from card_market_tracker.watchlist_journal.storage import Budget

    budget = Budget(5)
    events = []
    real_print = print

    def audited_print(value):
        budget.remaining()
        events.append("stdout")
        real_print(value)

    def exhaust_budget(_logger, _level, _message, *, extra):
        events.append(extra["result"])
        budget.deadline = 0

    monkeypatch.setattr(cli, "print", audited_print, raising=False)
    monkeypatch.setattr(logging.Logger, "log", exhaust_budget)
    assert (
        cli._report(
            {"version": 1, "operation": "verify", "result": "ok"},
            "verify",
            time.perf_counter(),
            0,
            budget=budget,
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["result"] == "ok"
    assert events == ["stdout", "ok"]


def test_final_pre_stdout_check_reports_expiration_once(capsys, monkeypatch):
    from card_market_tracker.watchlist_alerts import cli
    from card_market_tracker.watchlist_journal.storage import Budget

    budget = Budget(5)
    remaining = Budget.remaining
    calls = 0
    logged = []

    def expire_final(supplied):
        nonlocal calls
        calls += 1
        if calls == 2:
            supplied.deadline = 0
        return remaining(supplied)

    def record(_logger, _level, _message, *, extra):
        logged.append(extra)

    monkeypatch.setattr(Budget, "remaining", expire_final)
    monkeypatch.setattr(logging.Logger, "log", record)
    assert (
        cli._report(
            {
                "version": 1,
                "operation": "verify",
                "result": "ok",
                "counts": {"alerts": 0, "evidence": 0},
            },
            "verify",
            time.perf_counter(),
            0,
            budget=budget,
        )
        == 1
    )
    assert json.loads(capsys.readouterr().out) == {
        "version": 1,
        "operation": "verify",
        "result": "error",
        "error_category": "storage_timeout",
    }
    assert len(logged) == 1 and logged[0]["result"] == "error"
    assert "watchlist_alerts_count" not in logged[0]
    assert "watchlist_alert_evidence_count" not in logged[0]
