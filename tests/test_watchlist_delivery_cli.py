"""Privacy/import/CLI integration against actual P8d storage and fake native outcomes."""

from __future__ import annotations

import io
import json
import logging
import os
import subprocess
import sys
from uuid import uuid4

import pytest

from card_market_tracker.logging_json import JsonFormatter
from card_market_tracker.watchlist_delivery import application, cli
from card_market_tracker.watchlist_delivery.errors import ERROR_CATEGORIES

DENIED = """
import importlib.abc, os, socket, sys
class Deny(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith('card_market_tracker.telegram_delivery'):
            raise AssertionError('Telegram imported offline')
sys.meta_path.insert(0,Deny())
original_get=os.environ.get
original_item=type(os.environ).__getitem__
def get(key,*args):
    if key=='CMT_TELEGRAM_BOT_TOKEN': raise AssertionError('Token read')
    return original_get(key,*args)
def item(self,key):
    if key=='CMT_TELEGRAM_BOT_TOKEN': raise AssertionError('Token read')
    return original_item(self,key)
os.environ.get=get
type(os.environ).__getitem__=item
def no_socket(*a,**k): raise AssertionError('Socket used offline')
socket.socket=no_socket
from card_market_tracker.cli import main
sys.exit(main(sys.argv[1:]))
"""


def invoke(*args: str) -> subprocess.CompletedProcess[str]:
    # Do not copy or inspect production credentials.
    env = {
        key: os.environ[key]
        for key in ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP")
        if key in os.environ
    }
    env["CMT_TELEGRAM_BOT_TOKEN"] = "SYNTHETIC_TOKEN_SENTINEL"
    return subprocess.run(
        [sys.executable, "-B", "-c", DENIED, *args],
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=10,
    )


@pytest.mark.parametrize(
    "args,code",
    [
        (("--help",), 0),
        (("unknown-command",), 2),
        (("watchlist-telegram-delivery", "--help"), 0),
        (("watchlist-telegram-delivery", "send", "--help"), 0),
        (("watchlist-telegram-delivery", "send"), 2),
        (("watchlist-telegram-delivery", "send-all"), 2),
        (("watchlist-alert-outbox", "--help"), 0),
        (("watchlist", "--help"), 0),
        (("watchlist-journal", "--help"), 0),
    ],
)
def test_fresh_process_offline_import_token_socket_guards(args, code):
    result = invoke(*args)
    assert result.returncode == code, result.stderr
    assert "SYNTHETIC_TOKEN_SENTINEL" not in result.stdout + result.stderr
    assert "AssertionError" not in result.stdout + result.stderr
    if args[0] == "watchlist-telegram-delivery":
        logs = [json.loads(line) for line in result.stderr.splitlines()]
        assert len(logs) == 1
        assert logs[0]["event"] == "watchlist.telegram_delivery.completed"
        if code:
            assert json.loads(result.stdout) == {
                "version": 1,
                "operation": "watchlist-telegram-delivery",
                "result": "error",
                "error_category": "invalid_field",
            }


def test_real_cli_init_get_verify_and_restore_are_offline(tmp_path):
    ledger = tmp_path / "ledger.sqlite"
    restore = tmp_path / "restored.sqlite"
    backup = tmp_path / "backup.sqlite"
    for operation, extra in (
        ("init", ()),
        ("verify", ()),
        ("list", ("--limit", "1")),
        ("backup", ("--destination", str(backup))),
    ):
        result = invoke(
            "watchlist-telegram-delivery", operation, "--ledger-db", str(ledger), *extra
        )
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["operation"] == operation and payload["result"] == "ok"
        assert len(result.stderr.splitlines()) == 1
    result = invoke(
        "watchlist-telegram-delivery",
        "restore",
        "--ledger-db",
        str(backup),
        "--destination",
        str(restore),
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["send_quarantined"] is True
    result = invoke(
        "watchlist-telegram-delivery",
        "send",
        "--ledger-db",
        str(restore),
        "--delivery-id",
        "wtdl1_" + "0" * 64,
        "--manifest",
        str(tmp_path / "unavailable"),
    )
    assert json.loads(result.stdout)["error_category"] == "send_quarantined"


def test_parse_time_is_inside_budget_and_context_resets(monkeypatch, tmp_path):
    # No new budget can erase an already exhausted invocation allowance.
    from card_market_tracker.cli import main
    from card_market_tracker.logging_json import configure_logging

    monkeypatch.setattr(sys, "stdout", io.StringIO())
    monkeypatch.setattr(sys, "stderr", io.StringIO())
    assert application._invocation_budget.get() is None
    args = type("Args", (), {"watchlist_delivery_operation": "init", "timeout": 0.001})()
    assert cli.dispatch(args, 0.0, started_monotonic=0.0) == 1
    assert application._invocation_budget.get() is None
    assert not (tmp_path / "unused").exists()
    configure_logging(str(uuid4()))
    assert (
        main(["watchlist-telegram-delivery", "verify", "--ledger-db", str(tmp_path / "absent")])
        == 1
    )
    assert application._invocation_budget.get() is None


@pytest.mark.parametrize("category", sorted(ERROR_CATEGORIES))
def test_closed_log_categories_and_private_extra_redaction(category):
    record = logging.LogRecord("test", logging.ERROR, "", 0, "PRIVATE_EXCEPTION_SENTINEL", (), None)
    fields = {
        "event": "watchlist.telegram_delivery.completed",
        "operation": "watchlist_telegram_delivery_send",
        "component": "cli",
        "result": "error",
        "error_category": category,
        "delivery_id": "wtdl1_" + "a" * 64,
        "attempt_id": "wtat1_" + "b" * 64,
        "state": "uncertain",
        "attempt_count": 1,
        "delivery_count": 1,
        "token": "PRIVATE_TOKEN_SENTINEL",
        "alias": "PRIVATE_ALIAS_SENTINEL",
        "route_sha256": "PRIVATE_ROUTE_SENTINEL",
        "message": "PRIVATE_MESSAGE_SENTINEL",
        "alert_id": "walt1_" + "c" * 64,
        "path": "PRIVATE_PATH_SENTINEL",
    }
    for key, value in fields.items():
        setattr(record, key, value)
    rendered = JsonFormatter(str(uuid4())).format(record)
    result = json.loads(rendered)
    assert "PRIVATE_" not in rendered
    assert result["error_category"] == category
    assert result["delivery_id"].startswith("wtdl1_")
    assert result["attempt_id"].startswith("wtat1_")
    assert "alert_id" not in result


def test_log_wrong_ids_types_counts_and_unknown_operation_omitted():
    record = logging.LogRecord("test", logging.INFO, "", 0, "", (), None)
    for key, value in {
        "event": "watchlist.telegram_delivery.completed",
        "operation": "watchlist_telegram_delivery_force",
        "result": "fabricated",
        "error_category": "raw private exception",
        "delivery_id": "tdl1:" + "a" * 64,
        "attempt_id": "wtat1_" + "A" * 64,
        "attempt_count": True,
        "delivery_count": 100000001,
    }.items():
        setattr(record, key, value)
    result = json.loads(JsonFormatter(str(uuid4())).format(record))
    assert set(result) == {"timestamp", "level", "event", "component", "run_id"}


@pytest.mark.parametrize(
    "state,category,retry,expected_code,expected_category",
    [
        ("retryable", "provider_rate_limit", 1, 1, "rate_limited"),
        ("permanent_failure", "provider_rejection", None, 2, "provider_rejection"),
        ("uncertain", "transport_timeout", None, 1, "transport_timeout"),
    ],
)
def test_durable_fake_send_errors_have_frozen_exit_and_completion(
    tmp_path, monkeypatch, capsys, state, category, retry, expected_code, expected_category
):
    from test_watchlist_delivery_application import Fake, prepared

    from card_market_tracker.cli import main
    from card_market_tracker.telegram_delivery.transport import TransportResult

    ledger, origins, did = prepared(tmp_path)
    fake = Fake(TransportResult(state, category, retry))
    monkeypatch.setattr(application, "_transport_factory", lambda: fake)
    application.destination_validate(ledger, "private")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(origins[3]), encoding="utf-8")
    capsys.readouterr()
    code = main(
        [
            "watchlist-telegram-delivery",
            "send",
            "--ledger-db",
            str(ledger),
            "--delivery-id",
            did,
            "--watchlist-db",
            str(origins[0]),
            "--journal-db",
            str(origins[1]),
            "--outbox-db",
            str(origins[2]),
            "--manifest",
            str(manifest),
        ]
    )
    output = capsys.readouterr()
    payload = json.loads(output.out)
    event = json.loads(output.err)
    assert code == expected_code
    assert payload["result"] == "error" and payload["error_category"] == expected_category
    assert event["result"] == "error" and event["error_category"] == expected_category
    assert event["level"] == "ERROR"
    assert fake.calls.count("send") == 1
