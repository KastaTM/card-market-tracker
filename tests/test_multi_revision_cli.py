"""Explicit versioned CLI output, safe logs, offline behavior and categorized errors."""

import json
import socket
from uuid import uuid4

import pytest

from card_market_tracker.cli import main
from card_market_tracker.discovery.multi_models import REVIEWED_PAIR_PROFILE


def call(capsys, args, code):
    assert main(args) == code
    out = capsys.readouterr()
    payload = json.loads(out.out)
    event = json.loads(out.err)
    assert event["result"] == payload["result"]
    assert "run_id" in event and event["duration_ms"] >= 0
    for forbidden in ("tcgdex", "swsh3", "poison", "sqlite", "batch_id", "selector"):
        assert forbidden not in out.err
    return payload, event


def test_cli_versioned_admission_and_real_pair(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(socket, "socket", lambda *a, **kw: pytest.fail("network attempted"))
    database = tmp_path / "private.sqlite3"
    manifest = tmp_path / "manifest.json"
    manifest.write_text('{"version":1,"entities":[],"bindings":[]}', encoding="utf-8")
    tokens = [str(uuid4()), str(uuid4())]
    for member, token in zip((1, 2), tokens, strict=True):
        fixture = f"tests/fixtures/pinned_repository_bundle_v{member}.json"
        verified, log = call(capsys, ["bundle-v2", "verify", "--input", fixture], 0)
        assert verified["version"] == 2 and log["operation"] == "bundle_v2_verify"
        args = [
            "bundle-v2",
            "import",
            "--db",
            str(database),
            "--input",
            fixture,
            "--manifest",
            str(manifest),
            "--batch-id",
            token,
        ]
        assert call(capsys, args, 3)[0]["result"] == "mixed"
        before = database.read_bytes()
        assert call(capsys, args, 0)[0]["result"] == "replay"
        assert database.read_bytes() == before
    req = tmp_path / "request.json"
    request = {
        "version": 3,
        "profile": REVIEWED_PAIR_PROFILE,
        "context": {"namespace": "tcgdex_repository", "kind": "set", "language": "es"},
        "current": {"batch_id": tokens[1], "selector": "swsh3"},
        "history": [{"batch_id": tokens[0], "selector": "swsh3"}],
    }
    req.write_text(json.dumps(request), encoding="utf-8")
    payload, log = call(
        capsys, ["discover-multi-revision", "--db", str(database), "--request", str(req)], 0
    )
    assert payload["version"] == 3 and payload["result"] == "no_discoveries"
    assert log["event"] == "discovery.multi.completed"
    assert log["operation"] == "discover_multi_revision"
    assert log["batch_count"] == 2 and log["scoped_validated_record_count"] == 8
    assert log["event_count"] == 0


@pytest.mark.parametrize(
    "command,version,operation",
    [
        ("discover-multi-revision", 3, "discover_multi_revision"),
        ("bundle-v2", 2, "bundle_v2_verify"),
    ],
)
def test_bad_arguments_use_requested_version(capsys, command, version, operation):
    payload, log = call(capsys, [command, "--poison"], 2)
    assert payload["version"] == version and payload["counts"] is None
    assert log["operation"] == operation
    if version == 3:
        assert payload["events"] == []


@pytest.mark.parametrize(
    "document", ["{", '{"version":3,"version":3}', '{"version":2}', '"poison"']
)
def test_malformed_request_never_opens_db(tmp_path, capsys, document):
    req, database = tmp_path / "poison.json", tmp_path / "missing.db"
    req.write_text(document, encoding="utf-8")
    payload, _ = call(
        capsys, ["discover-multi-revision", "--db", str(database), "--request", str(req)], 2
    )
    assert payload["version"] == 3 and payload["counts"] is None and payload["events"] == []
    assert not database.exists()


@pytest.mark.parametrize("command", ["discover-multi-revision", "bundle-v2"])
def test_missing_input_is_local_failure(tmp_path, capsys, command):
    args = (
        ["--db", str(tmp_path / "missing.db"), "--request"]
        if command.startswith("discover")
        else ["verify", "--input"]
    )
    payload, _ = call(capsys, [command, *args, str(tmp_path / "missing.json")], 1)
    assert payload["error_category"] == "input_io" and payload["counts"] is None


def test_self_declared_registry_and_observed_rejected_before_db(tmp_path, capsys):
    original = json.loads(
        open("tests/fixtures/pinned_repository_bundle_v2.json", encoding="utf-8").read()
    )
    original["registry"] = {"approved": True, "observed": True}
    package = tmp_path / "poison.json"
    package.write_text(json.dumps(original), encoding="utf-8")
    payload, _ = call(
        capsys,
        [
            "bundle-v2",
            "import",
            "--input",
            str(package),
            "--manifest",
            "tests/fixtures/synthetic_manifest.json",
            "--db",
            str(tmp_path / "missing.db"),
            "--batch-id",
            str(uuid4()),
        ],
        2,
    )
    assert payload["error_category"] == "unapproved_bundle"
    assert not (tmp_path / "missing.db").exists()
