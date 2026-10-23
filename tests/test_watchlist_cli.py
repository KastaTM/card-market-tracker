"""Watchlist command surface: durable preferences, simulation and safe errors."""

import json
import logging
import socket
from pathlib import Path

import pytest

from card_market_tracker.cli import main
from card_market_tracker.logging_json import JsonFormatter

FIXTURES = Path(__file__).parent / "fixtures"
PRODUCT = "541b9d13-9669-4973-8413-397bea14c045"


def test_every_command_offline_and_redacted(tmp_path, capsys, monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("socket attempted")

    monkeypatch.setattr(socket, "socket", denied)
    monkeypatch.setattr(socket, "create_connection", denied)
    db = tmp_path / "watchlist.db"
    manifest = FIXTURES / "synthetic_manifest.json"
    config = FIXTURES / "synthetic_watchlist_config.json"

    def call(operation, *flags, target=db, code=0):
        assert (
            main(["watchlist", operation, "--watchlist-db", str(target), *map(str, flags)]) == code
        )
        output = capsys.readouterr()
        payload, log = json.loads(output.out), json.loads(output.err)
        assert payload["version"] == 1 and payload["operation"] == operation
        assert log["event"] == "watchlist.completed"
        assert log["operation"] == "watchlist_" + operation
        assert log["duration_ms"] >= 0 and log["run_id"]
        assert str(tmp_path) not in output.err and PRODUCT not in output.err
        assert "target_price_minor" not in output.err and "synthetic" not in output.err
        return payload

    call("init")
    add = (
        "--manifest",
        manifest,
        "--cmt-id",
        PRODUCT,
        "--input",
        config,
        "--request-token",
        "initial",
    )
    original = call("add", *add)
    watch = original["entry"]["watch_id"]
    edit = (
        "--manifest",
        manifest,
        "--watch-id",
        watch,
        "--input",
        config,
        "--expected-revision",
        1,
        "--request-token",
        "edit",
    )
    assert call("update", *edit)["entry"]["revision"] == 2
    assert call("add", *add)["replayed"] is True
    assert call("update", *edit)["replayed"] is True
    assert call("get", "--watch-id", watch)["entry"]["revision"] == 2
    assert call("list", "--priority", "high", "--enabled", "true")["entries"]
    assert call("list", "--priority", "low")["entries"] == []
    page = call("history", "--watch-id", watch, "--limit", 1)
    assert page["next_cursor"]
    assert call("history", "--watch-id", watch, "--cursor", page["next_cursor"])["entries"]
    assert call("list", "--limit", 1001, code=2)["error_category"] == "invalid_field"
    evaluate = (
        "--manifest",
        manifest,
        "--watch-id",
        watch,
        "--revision",
        2,
        "--sample",
        FIXTURES / "synthetic_watchlist_current.json",
        "--previous",
        FIXTURES / "synthetic_watchlist_previous.json",
        "--as-of",
        "2026-10-23T12:00:00Z",
    )
    before = db.read_bytes()
    result = call("evaluate", *evaluate)
    assert result["result"] == "MATCH"
    assert call("evaluate", *evaluate) == result and before == db.read_bytes()
    common = ("--manifest", manifest, "--watch-id", watch)
    assert (
        call("disable", *common, "--expected-revision", 2, "--request-token", "off")["entry"][
            "enabled"
        ]
        is False
    )
    assert (
        call("enable", *common, "--expected-revision", 3, "--request-token", "on")["entry"][
            "enabled"
        ]
        is True
    )
    call("verify")
    copy, restored = tmp_path / "copy.db", tmp_path / "restored.db"
    call("backup", "--destination", copy)
    call("restore", "--destination", restored, target=copy)
    call("verify", target=restored)
    assert call("get", "--watch-id", watch, target=restored)["entry"]["revision"] == 4
    call("get", "--watch-id", "invalid", code=2)
    call("list", target=tmp_path / "absent.db", code=1)


@pytest.mark.parametrize(
    "args",
    [
        [],
        ["send"],
        ["init"],
        ["list", "--watchlist-db", "x", "--limit", "secret-value"],
        ["evaluate", "--watchlist-db", "x"],
        ["list", "--watchlist-db", "x", "--latest"],
        ["list", "--watchlist-db", "x", "--enabled", "maybe"],
    ],
)
def test_argument_errors_are_versioned_and_sanitized(args, capsys):
    assert main(["watchlist", *args]) == 2
    output = capsys.readouterr()
    assert json.loads(output.out) == {
        "version": 1,
        "operation": "arguments",
        "result": "error",
        "error_category": "invalid_field",
    }
    assert json.loads(output.err)["operation"] == "watchlist_arguments"
    assert "secret-value" not in output.out + output.err


def test_json_error_and_unexpected_exception_are_sanitized(tmp_path, capsys, monkeypatch):
    from card_market_tracker.watchlist import storage

    def fail(*args, **kwargs):
        raise RuntimeError("private-path-and-payload")

    monkeypatch.setattr(storage, "initialize", fail)
    assert main(["watchlist", "init", "--watchlist-db", str(tmp_path / "x")]) == 1
    output = capsys.readouterr()
    assert json.loads(output.out)["error_category"] == "storage_io"
    assert "private-path-and-payload" not in output.out + output.err
    hostile = tmp_path / "bad.json"
    hostile.write_text('{"target_price_minor":1,"target_price_minor":2}', encoding="utf-8")
    assert (
        main(
            [
                "watchlist",
                "add",
                "--watchlist-db",
                str(tmp_path / "x"),
                "--manifest",
                str(FIXTURES / "synthetic_manifest.json"),
                "--cmt-id",
                PRODUCT,
                "--input",
                str(hostile),
                "--request-token",
                "x",
            ]
        )
        == 2
    )
    assert json.loads(capsys.readouterr().out)["error_category"] == "duplicate_key"


@pytest.mark.parametrize("count", [0, 1000, True, -1, 1001, "1"])
def test_log_count_bounds_and_privacy(count):
    record = logging.LogRecord("card_market_tracker", logging.INFO, "", 0, "secret", (), None)
    record.event = "watchlist.completed"
    record.operation = "watchlist_evaluate"
    record.result = "ok"
    record.watchlist_entries_count = count
    record.target_price_minor = 1000
    record.sample = "secret-sample"
    payload = json.loads(JsonFormatter("run").format(record))
    assert "secret" not in json.dumps(payload)
    assert "target_price_minor" not in payload
    assert ("watchlist_entries_count" in payload) == (type(count) is int and 0 <= count <= 1000)
