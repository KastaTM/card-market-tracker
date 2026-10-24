"""P5b CLI admission, bounded pages, read-only recompute and safe failures."""

import json
import socket
import time
from pathlib import Path

import pytest

from card_market_tracker.cli import main
from card_market_tracker.watchlist import application as watch_application
from card_market_tracker.watchlist import storage as watch_storage

FIXTURES = Path(__file__).parent / "fixtures"
TARGET = "541b9d13-9669-4973-8413-397bea14c045"


def test_all_commands_offline_redacted_and_origin_unchanged(tmp_path, capsys, monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("socket attempted")

    monkeypatch.setattr(socket, "socket", denied)
    monkeypatch.setattr(socket, "create_connection", denied)
    manifest = json.loads((FIXTURES / "synthetic_manifest.json").read_text())
    origin, journal = tmp_path / "origin.db", tmp_path / "journal.db"
    watch_storage.initialize(origin)
    entry = watch_application.add(
        origin,
        manifest,
        TARGET,
        json.loads((FIXTURES / "synthetic_watchlist_config.json").read_text()),
        request_token="cli-journal",
    )["entry"]
    original = origin.read_bytes()

    def call(operation, *flags, target=journal, code=0):
        assert (
            main(["watchlist-journal", operation, "--journal-db", str(target), *map(str, flags)])
            == code
        )
        output = capsys.readouterr()
        payload, log = json.loads(output.out), json.loads(output.err)
        assert payload["operation"] == operation
        assert log["event"] == "watchlist.journal.completed"
        assert log["operation"] == "watchlist_journal_" + operation.replace("-", "_")
        assert log["duration_ms"] >= 0 and log["run_id"]
        assert str(tmp_path) not in output.err and TARGET not in output.err
        assert "target_price_minor" not in output.err and "synthetic" not in output.err
        return payload

    call("init")
    common = (
        "--watchlist-db",
        origin,
        "--manifest",
        FIXTURES / "synthetic_manifest.json",
        "--watch-id",
        entry["watch_id"],
        "--revision",
        1,
    )
    prior, current = (
        FIXTURES / "synthetic_watchlist_previous.json",
        FIXTURES / "synthetic_watchlist_current.json",
    )
    baseline_args = (*common, "--sample", prior, "--as-of", "2026-10-23T11:00:00Z")
    first = call("record", *baseline_args)
    second = call(
        "record",
        *common,
        "--sample",
        current,
        "--previous",
        prior,
        "--as-of",
        "2026-10-23T12:00:00Z",
    )
    assert first["signals_count"] == 0 and second["signals_count"] == 2
    replay = call("record", *baseline_args)
    assert replay["result"] == "replayed" and replay["persisted_at"] == first["persisted_at"]
    evaluation = call("get", "--evaluation-id", second["evaluation_id"])
    call("signal-get", "--signal-id", second["signal_ids"][0])
    page = call("list", "--limit", 1)
    assert page["next_cursor"]
    assert call("list", "--cursor", page["next_cursor"])["evaluations"]
    call("list", "--cursor", page["next_cursor"], "--watch-id", entry["watch_id"], code=2)
    assert len(call("signal-list", "--rule", "price")["signals"]) == 1
    assert len(call("signal-list")["signals"]) == 2
    call("list", "--limit", 1001, code=2)
    call("verify")
    before = journal.read_bytes()
    call(
        "recompute",
        "--watchlist-db",
        origin,
        "--manifest",
        FIXTURES / "synthetic_manifest.json",
        "--evaluation-id",
        second["evaluation_id"],
    )
    assert journal.read_bytes() == before
    call(
        "recompute",
        "--watchlist-db",
        tmp_path / "absent.db",
        "--manifest",
        FIXTURES / "synthetic_manifest.json",
        "--evaluation-id",
        second["evaluation_id"],
        code=1,
    )
    call("verify")
    copy, restored = tmp_path / "backup.db", tmp_path / "restored.db"
    call("backup", "--destination", copy)
    call("restore", "--destination", restored, target=copy)
    call("verify", target=restored)
    assert call("get", "--evaluation-id", second["evaluation_id"], target=restored) == evaluation
    call("get", "--evaluation-id", "invalid", code=2)
    call("list", target=tmp_path / "missing.db", code=1)
    assert origin.read_bytes() == original


@pytest.mark.parametrize(
    "args",
    [
        [],
        ["send"],
        ["init"],
        ["record", "--journal-db", "private"],
        ["list", "--journal-db", "private", "--latest"],
        ["list", "--journal-db", "private", "--limit", "secret-value"],
        ["signal-list", "--journal-db", "private", "--rule", "secret-value"],
    ],
)
def test_argument_errors_are_safe_json(args, capsys):
    assert main(["watchlist-journal", *args]) == 2
    output = capsys.readouterr()
    assert json.loads(output.out) == {
        "version": 1,
        "operation": "arguments",
        "result": "error",
        "error_category": "invalid_field",
    }
    assert json.loads(output.err)["operation"] == "watchlist_journal_arguments"
    assert "secret-value" not in output.out + output.err


@pytest.mark.parametrize("timeout", ["0", "-1", "6", "nan", "inf"])
def test_invalid_budget_is_input_failure(timeout, tmp_path, capsys):
    assert (
        main(
            ["watchlist-journal", "init", "--journal-db", str(tmp_path / "x"), "--timeout", timeout]
        )
        == 2
    )
    output = capsys.readouterr()
    assert json.loads(output.out)["error_category"] == "invalid_field"
    assert not (tmp_path / "x").exists()


def test_parse_deadline_and_unexpected_failure_are_safe(tmp_path, capsys, monkeypatch):
    from card_market_tracker.watchlist_journal import cli, storage

    def failed(*args, **kwargs):
        raise RuntimeError("private payload and path")

    monkeypatch.setattr(storage, "initialize", failed)
    assert main(["watchlist-journal", "init", "--journal-db", str(tmp_path / "x")]) == 1
    output = capsys.readouterr()
    assert "private payload" not in output.out + output.err
    assert json.loads(output.out)["error_category"] == "storage_io"

    def delayed(*args, **kwargs):
        time.sleep(0.02)
        return {}

    monkeypatch.setattr(cli, "read_json", delayed)
    assert (
        main(
            [
                "watchlist-journal",
                "record",
                "--journal-db",
                str(tmp_path / "x"),
                "--watchlist-db",
                str(tmp_path / "origin"),
                "--manifest",
                "x",
                "--watch-id",
                "x",
                "--revision",
                "1",
                "--sample",
                "x",
                "--as-of",
                "x",
                "--timeout",
                "0.001",
            ]
        )
        == 1
    )
    output = capsys.readouterr()
    assert json.loads(output.out)["error_category"] == "storage_timeout"


def test_input_io_is_local_failure_with_no_path_leak(tmp_path, capsys):
    assert (
        main(
            [
                "watchlist-journal",
                "record",
                "--journal-db",
                str(tmp_path / "journal"),
                "--watchlist-db",
                str(tmp_path / "origin"),
                "--manifest",
                str(tmp_path / "private-missing"),
                "--watch-id",
                "x",
                "--revision",
                "1",
                "--sample",
                "x",
                "--as-of",
                "x",
            ]
        )
        == 1
    )
    output = capsys.readouterr()
    assert json.loads(output.out)["error_category"] == "input_io"
    assert str(tmp_path) not in output.out + output.err
