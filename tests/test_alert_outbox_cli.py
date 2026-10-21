"""Strict command dispatch and allowlisted output/logging on every public route."""

import json

import pytest
from test_alert_outbox_application import admitted as outbox_fixture

from card_market_tracker.cli import main

admitted = outbox_fixture


def test_all_cli_routes_and_redacted_logs(admitted, tmp_path, capsys):
    captures, journal, outbox, cid, *_ = admitted

    def cli(operation, *values, code=0, target=outbox):
        assert (
            main(["alert-outbox", operation, "--outbox-db", str(target), *map(str, values)]) == code
        )
        output = capsys.readouterr()
        payload, log = json.loads(output.out), json.loads(output.err)
        assert log["event"] == "alert.outbox.completed"
        assert log["run_id"] and log["duration_ms"] >= 0 and log["result"] == payload["result"]
        assert log["operation"].startswith("alert_outbox_")
        assert payload["version"] == 1 and type(payload["version"]) is int
        assert output.out.strip() == json.dumps(
            payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        )
        for forbidden in (
            str(tmp_path),
            "local-preview",
            "synthetic_scope",
            "candidate",
            "SELECT",
            "Accepted set reference",
        ):
            assert forbidden not in output.err
        return payload

    prepared = cli(
        "enqueue",
        "--captures-db",
        captures,
        "--journal-db",
        journal,
        "--comparison-id",
        cid,
        "--destination-key",
        "local-preview",
    )
    assert prepared["result"] == "inserted"
    aid = cli("list", "--limit", 1)["items"][0]["alert_id"]
    cli("list", "--destination-key", "local-preview")
    alert = cli("get", "--alert-id", aid)
    assert cli("preview", "--alert-id", aid)["message_text"] == alert["alert"]["message_text"]
    cli("evidence-list", "--alert-id", aid)
    cli("evidence-get", "--alert-id", aid, "--comparison-id", cid)
    cli("verify")
    cli(
        "recompute",
        "--captures-db",
        captures,
        "--journal-db",
        journal,
        "--comparison-id",
        cid,
        "--alert-id",
        aid,
    )
    backup, restored = tmp_path / "backup.db", tmp_path / "restored.db"
    cli("backup", "--destination", backup)
    cli("restore", "--destination", restored, target=backup)
    cli("verify", target=restored)
    cli("init", target=tmp_path / "empty.db")
    assert cli("list", "--limit", 0, code=2)["error_category"] == "invalid_field"
    cli("get", "--alert-id", "bad", code=2)
    cli("list", target=tmp_path / "missing.db", code=1)


@pytest.mark.parametrize(
    "flags",
    [
        [],
        ["enqueue"],
        ["send"],
        ["list", "--outbox-db", "x", "--latest"],
        ["enqueue", "--outbox-db", "x", "--result-json", "{}"],
        ["list", "--outbox-db", "x", "--timeout", "bad"],
    ],
)
def test_parser_failures_have_contract_json_and_safe_logs(flags, capsys):
    assert main(["alert-outbox", *flags]) == 2
    output = capsys.readouterr()
    assert json.loads(output.out) == {
        "version": 1,
        "operation": "alert-outbox",
        "result": "error",
        "error_category": "invalid_field",
    }
    assert json.loads(output.err)["operation"] == "alert_outbox_arguments"
    assert "Traceback" not in output.err


def test_unexpected_internal_exception_is_redacted(admitted, capsys, monkeypatch):
    from card_market_tracker.alerts import cli

    _, _, outbox, *_ = admitted

    def fail(*args, **kwargs):
        raise RuntimeError("secret path/contact payload")

    monkeypatch.setattr(cli.storage, "verify", fail)
    assert main(["alert-outbox", "verify", "--outbox-db", str(outbox)]) == 1
    output = capsys.readouterr()
    assert json.loads(output.out)["error_category"] == "storage_io"
    assert "secret" not in output.err and "secret" not in output.out
