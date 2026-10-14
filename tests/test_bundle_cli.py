"""P1b local commands, separate process durability and safe observed boundaries."""

import json
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from card_market_tracker.cli import main

FIXTURES = Path(__file__).parent / "fixtures"
TOKEN = "bd9cc4b8-eace-4567-8364-93cc4eccddc5"


def invoke(arguments, capsys, expected=0):
    assert main(arguments) == expected
    captured = capsys.readouterr()
    payload, event = json.loads(captured.out), json.loads(captured.err)
    assert event["event"] == "persistence.completed"
    assert event["result"] == payload["result"] and event["duration_ms"] >= 0
    for forbidden in ("swsh3", "Furret", str(FIXTURES), TOKEN, "sentinel-private"):
        assert forbidden not in captured.err
    if payload["result"] == "error":
        assert payload["counts"] is payload["committed"] is None
        assert event["error_category"] == payload["error_category"]
    return payload


def import_command(database, manifest="synthetic_manifest.json", batch_id=TOKEN):
    return [
        "bundle",
        "import",
        "--db",
        str(database),
        "--input",
        str(FIXTURES / "pinned_repository_bundle_v1.json"),
        "--manifest",
        str(FIXTURES / manifest),
        "--batch-id",
        batch_id,
    ]


def test_offline_import_replay_conflict_and_process_reopen(tmp_path, capsys, monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("runtime must be offline")

    monkeypatch.setattr(socket.socket, "connect", no_network)
    database = tmp_path / "history.db"
    invoke(["db", "init", "--db", str(database)], capsys)
    first = invoke(import_command(database), capsys, 3)
    assert first["counts"] == {"input": 4, "accepted": 0, "candidates": 4, "rejected": 0}
    assert first["committed"] == {"entities": 0, "observations": 4}
    command = ["captures", "--db", str(database), "--batch-id", TOKEN]
    before = invoke(command, capsys)
    assert before["evidence_state"] == "verified_local_pinned_bundle"
    replay = invoke(import_command(database), capsys)
    assert (
        replay["result"] == "replay" and replay["first_persisted_at"] == first["first_persisted_at"]
    )
    assert replay["committed"] == {"entities": 0, "observations": 0}
    assert (
        invoke(
            import_command(database, "synthetic_discovery_manifest.json"),
            capsys,
            2,
        )["error_category"]
        == "replay_conflict"
    )
    assert invoke(command, capsys) == before
    reopened = subprocess.run(
        [sys.executable, "-m", "card_market_tracker.cli", *command],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    assert json.loads(reopened.stdout) == before
    assert all(row["cmt_id"] is None for row in before["records"])


@pytest.mark.parametrize(
    "arguments",
    [
        ["bundle"],
        ["bundle", "verify"],
        ["bundle", "import"],
        ["captures"],
        ["db", "migrate"],
    ],
)
def test_argument_errors_are_categorized(arguments, capsys):
    assert invoke(arguments, capsys, 2)["error_category"] == "invalid_field"


def test_synthetic_adversarial_bundle_tampering_never_creates_db(tmp_path, capsys):
    # A modified temporary document is adversarial synthetic input, not retained real evidence.
    document = json.loads((FIXTURES / "pinned_repository_bundle_v1.json").read_text("utf-8"))
    document["sentinel-private"] = "excluded"
    modified = tmp_path / "synthetic_tampered.json"
    modified.write_text(json.dumps(document), encoding="utf-8")
    database = tmp_path / "absent.db"
    arguments = import_command(database)
    arguments[arguments.index("--input") + 1] = str(modified)
    assert invoke(arguments, capsys, 2)["result"] == "error"
    assert not database.exists()


def test_verify_and_missing_capture_errors(tmp_path, capsys):
    assert (
        invoke(
            [
                "bundle",
                "verify",
                "--input",
                str(FIXTURES / "pinned_repository_bundle_v1.json"),
            ],
            capsys,
        )["evidence"]
        == "verified_local_pinned_bundle"
    )
    invoke(["bundle", "verify", "--input", str(tmp_path / "missing")], capsys, 1)
    invoke(["captures", "--db", str(tmp_path / "missing.db"), "--batch-id", TOKEN], capsys, 1)
