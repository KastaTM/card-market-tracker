"""Author tests for strict Telegram operations, stable exits and redacted reporting."""

import json

import pytest
from test_alert_outbox_application import admitted as outbox_fixture
from test_telegram_delivery_application import FakeTransport
from test_telegram_delivery_application import prepared as ledger_fixture

from card_market_tracker.cli import main
from card_market_tracker.telegram_delivery import application, cli, storage
from card_market_tracker.telegram_delivery.errors import ERROR_CATEGORIES, DeliveryError
from card_market_tracker.telegram_delivery.transport import TransportResult

prepared = ledger_fixture
admitted = outbox_fixture


def test_all_public_operations_json_and_redaction(prepared, tmp_path, capsys, monkeypatch):
    captures, journal, outbox, ledger, aid, cid, did = prepared
    fake = FakeTransport()
    original_send = application.send
    original_validate = application.destination_validate
    monkeypatch.setattr(
        application, "send", lambda *a, **kw: original_send(*a, transport=fake, **kw)
    )
    monkeypatch.setattr(
        application,
        "destination_validate",
        lambda *a, **kw: original_validate(*a, transport=fake, **kw),
    )

    def invoke(operation, *args, target=ledger, code=0):
        assert (
            main(["telegram-delivery", operation, "--ledger-db", str(target), *map(str, args)])
            == code
        )
        output = capsys.readouterr()
        payload, log = json.loads(output.out), json.loads(output.err)
        assert log["event"] == "telegram.delivery.completed"
        assert log["run_id"] and log["duration_ms"] >= 0
        assert log["result"] == payload["result"]
        if "previous_state" in payload:
            assert log["previous_state"] == payload["previous_state"]
        assert output.out.strip() == json.dumps(
            payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        )
        for forbidden in (
            str(tmp_path),
            "bot_id",
            "chat_id",
            "message_text",
            "TOKEN",
            "api.telegram.org",
        ):
            assert forbidden not in output.out + output.err
        return payload

    invoke("init", target=tmp_path / "new.db")
    invoke(
        "destination-add",
        "--alias",
        "private-operator",
        "--bot-id",
        123,
        "--chat-id",
        456,
        "--operator-private-owned",
    )
    invoke("destination-validate", "--alias", "private-operator")
    invoke(
        "destination-add",
        "--alias",
        "new-private",
        "--bot-id",
        123,
        "--chat-id",
        456,
        "--operator-private-owned",
    )
    assert invoke("destination-validate", "--alias", "new-private")["result"] == "ok"
    source = ("--captures-db", captures, "--journal-db", journal, "--outbox-db", outbox)
    invoke(
        "prepare", *source, "--alert-id", aid, "--comparison-id", cid, "--alias", "private-operator"
    )
    invoke("get", "--delivery-id", did)
    invoke("list", "--state", "ready", "--limit", 1)
    invoke("verify")
    invoke("recompute", *source, "--delivery-id", did)
    invoke("recover", "--delivery-id", did, "--worker-quiesced", code=2)
    assert invoke("send", *source, "--delivery-id", did)["state"] == "confirmed"
    count = len(fake.calls)
    assert invoke("send", *source, "--delivery-id", did)["result"] == "replay"
    assert len(fake.calls) == count
    backup, restored = tmp_path / "backup.db", tmp_path / "restored.db"
    invoke("backup", "--destination", backup)
    invoke("restore", "--destination", restored, target=backup)
    invoke("verify", target=restored)
    invoke("list", "--limit", 0, code=2)
    invoke("get", "--delivery-id", "bad", code=2)
    invoke("verify", target=tmp_path / "missing.db", code=1)


@pytest.mark.parametrize(
    "flags",
    [
        [],
        ["send"],
        ["list", "--ledger-db", "x", "--latest"],
        ["list", "--ledger-db", "x", "--timeout", "bad"],
        ["send", "--ledger-db", "x", "--token", "SECRET"],
        [
            "destination-add",
            "--ledger-db",
            "x",
            "--alias",
            "a",
            "--bot-id",
            "123",
            "--chat-id",
            "456",
        ],
        ["recover", "--ledger-db", "x", "--delivery-id", "x"],
        ["list", "--ledger-db", "x", "--state", "invented"],
        ["list", "--ledger", "x"],
    ],
)
def test_parser_failure_safe_json(flags, capsys):
    assert main(["telegram-delivery", *flags]) == 2
    output = capsys.readouterr()
    assert json.loads(output.out) == {
        "version": 1,
        "operation": "telegram-delivery",
        "result": "error",
        "error_category": "invalid_field",
    }
    assert json.loads(output.err)["operation"] == "telegram_delivery_arguments"
    assert "SECRET" not in output.out + output.err
    assert "Traceback" not in output.err


@pytest.mark.parametrize(
    "result,code",
    [
        (TransportResult("uncertain", "provider_invalid"), 1),
        (TransportResult("retryable", "provider_rate_limit", retry_after=1), 1),
        (TransportResult("permanent_failure", "provider_rejection"), 2),
    ],
)
def test_send_exit_codes(prepared, monkeypatch, capsys, result, code):
    captures, journal, outbox, ledger, _, _, did = prepared
    original = application.send
    monkeypatch.setattr(
        application, "send", lambda *a, **kw: original(*a, transport=FakeTransport(result), **kw)
    )
    assert (
        main(
            [
                "telegram-delivery",
                "send",
                "--captures-db",
                str(captures),
                "--journal-db",
                str(journal),
                "--outbox-db",
                str(outbox),
                "--ledger-db",
                str(ledger),
                "--delivery-id",
                did,
            ]
        )
        == code
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["result"] == "error" and payload["state"] == result.state


def test_unexpected_exception_and_foreign_category_redacted(tmp_path, monkeypatch, capsys):
    def fail(*args, **kwargs):
        raise RuntimeError("TOKEN private route payload")

    monkeypatch.setattr(storage, "verify", fail)
    assert main(["telegram-delivery", "verify", "--ledger-db", str(tmp_path / "x")]) == 1
    output = capsys.readouterr()
    assert json.loads(output.out)["error_category"] == "storage_io"
    assert "TOKEN" not in output.out + output.err
    assert DeliveryError("TOKEN").category == "invalid_field"
    assert str(DeliveryError("TOKEN")) == "invalid_field"


@pytest.mark.parametrize("category", sorted(ERROR_CATEGORIES))
def test_all_error_categories_have_stable_safe_exit(category):
    error = DeliveryError(category)
    assert error.category == category and str(error) == category
    assert error.exit_code in (1, 2)


def test_unknown_dispatch_is_invalid_field(capsys):
    import argparse
    import time

    assert (
        cli.dispatch(
            argparse.Namespace(telegram_delivery_operation="unknown", ledger_db=None, timeout=2),
            time.perf_counter(),
        )
        == 2
    )
    assert json.loads(capsys.readouterr().out)["error_category"] == "invalid_field"
