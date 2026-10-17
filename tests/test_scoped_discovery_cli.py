"""Version-two CLI errors, safe logs, replay, DB nonmutation and v1 coexistence."""

import json
import socket
import sqlite3

import pytest
from test_scoped_discovery_core import OLD, request, seed

from card_market_tracker import cli
from card_market_tracker.persistence import sqlite_repository as storage


def invoke(capsys, path, request_path, expected=0, extra=()):
    assert (
        cli.main(["discover-scoped", "--db", str(path), "--request", str(request_path), *extra])
        == expected
    )
    output = capsys.readouterr()
    payload = json.loads(output.out)
    log = json.loads(output.err)
    assert payload["version"] == 2
    assert log["event"] == "discovery.scoped.completed"
    assert log["operation"] == "discover_scoped"
    assert log["result"] == payload["result"]
    for secret in (
        str(path),
        str(request_path),
        "synthetic_scope",
        "private-selector",
        "raw exception",
    ):
        assert secret not in output.err
    if expected:
        assert payload["result"] == "error"
        assert payload["counts"] is None and payload["events"] == []
        assert "batch_count" not in log and "event_count" not in log
        assert "scoped_validated_record_count" not in log
    else:
        assert log["batch_count"] == payload["counts"]["validated_batches"]
        assert log["scoped_validated_record_count"] == payload["counts"]["validated_records"]
        assert log["scoped_selected_record_count"] == (
            payload["counts"]["current_selected_records"]
            + payload["counts"]["historical_selected_records"]
        )
        assert log["event_count"] == len(payload["events"])
    return payload, log


@pytest.fixture
def scoped_database(tmp_path):
    path = tmp_path / "scoped.db"
    history, _ = seed(path, (), capture=OLD, selector="private-selector")
    current, _ = seed(path, selector="private-selector")
    request_path = tmp_path / "request.json"
    request_path.write_text(
        json.dumps(
            request(current.batch_id, (history.batch_id,), selector="private-selector").to_dict()
        )
    )
    return path, request_path, current, history


def test_success_replay_no_network_and_no_db_writes(capsys, scoped_database, monkeypatch):
    path, request_path, _, _ = scoped_database
    before = path.read_bytes()
    monkeypatch.setattr(socket, "socket", lambda *args, **kwargs: pytest.fail("network requested"))
    first, first_log = invoke(capsys, path, request_path)
    second, second_log = invoke(capsys, path, request_path)
    assert first == second and first["result"] == "discoveries"
    assert first_log["run_id"] != second_log["run_id"]
    assert path.read_bytes() == before
    assert "run_id" not in first and "duration_ms" not in first


@pytest.mark.parametrize(
    "case,category,code",
    [
        ("bad_json", "invalid_json", 2),
        ("v1", "invalid_shape", 2),
        ("bad_version", "unsupported_version", 2),
        ("unit_missing", "unit_missing", 2),
        ("missing_db", "storage_io", 1),
        ("missing_request", "input_io", 1),
        ("corrupt_db", "storage_schema", 1),
    ],
)
def test_categorized_failures(capsys, scoped_database, case, category, code):
    path, request_path, current, _ = scoped_database
    if case == "bad_json":
        request_path.write_text("{")
    elif case == "v1":
        request_path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "current_batch_id": current.batch_id,
                    "history_batch_ids": [],
                    "context": {"namespace": "synthetic_scope", "kind": "set", "language": "es"},
                }
            )
        )
    elif case == "bad_version":
        document = json.loads(request_path.read_text())
        document["version"] = 1
        request_path.write_text(json.dumps(document))
    elif case == "unit_missing":
        request_path.write_text(json.dumps(request(current.batch_id, selector="wrong").to_dict()))
    elif case == "missing_db":
        path = path.with_name("missing.db")
    elif case == "missing_request":
        request_path = request_path.with_name("missing.json")
    elif case == "corrupt_db":
        path = path.with_name("foreign.db")
        with sqlite3.connect(path) as connection:
            connection.execute("CREATE TABLE foreign_table(a INTEGER)")
    payload, log = invoke(capsys, path, request_path, code)
    assert payload["error_category"] == log["error_category"] == category


@pytest.mark.parametrize(
    "category,code",
    [
        ("incomplete_evidence", 2),
        ("chronology", 2),
        ("scope_mismatch", 2),
        ("storage_corrupt", 1),
        ("storage_locked", 1),
        ("storage_timeout", 1),
        ("storage_io", 1),
    ],
)
def test_safe_reader_error_categories(capsys, scoped_database, monkeypatch, category, code):
    path, request_path, _, _ = scoped_database

    def fail(*args, **kwargs):
        from card_market_tracker.discovery.scoped_errors import ScopedDiscoveryError

        raise ScopedDiscoveryError(category)

    monkeypatch.setattr(storage, "read_scoped_snapshots", fail)
    payload, _ = invoke(capsys, path, request_path, code)
    assert payload["error_category"] == category


def test_unexpected_exception_redacted(capsys, scoped_database, monkeypatch):
    path, request_path, _, _ = scoped_database

    def fail(*args, **kwargs):
        raise RuntimeError("raw exception contains private-selector")

    monkeypatch.setattr(storage, "read_scoped_snapshots", fail)
    payload, _ = invoke(capsys, path, request_path, 1)
    assert payload["error_category"] == "local_execution"


@pytest.mark.parametrize(
    "arguments",
    [
        ["discover-scoped"],
        ["discover-scoped", "--db", "private-selector"],
        ["discover-scoped", "--unknown", "private-selector"],
    ],
)
def test_argument_errors_are_v2_safe_json(capsys, arguments):
    assert cli.main(arguments) == 2
    output = capsys.readouterr()
    payload = json.loads(output.out)
    assert payload == {
        "version": 2,
        "result": "error",
        "error_category": "invalid_field",
        "counts": None,
        "events": [],
    }
    assert "private-selector" not in output.err


def test_real_partial_baseline_rejected(capsys, tmp_path):
    path = tmp_path / "partial.db"
    current, _ = seed(path, outcome="partial", completed=())
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(request(current.batch_id).to_dict()))
    payload, _ = invoke(capsys, path, request_path, 2)
    assert payload["error_category"] == "incomplete_evidence"


def test_cli_v1_still_rejects_real_observed(capsys, tmp_path):
    from uuid import uuid4

    from card_market_tracker.persistence.capture import persist_bundle
    from card_market_tracker.pinned_repository import approved_bundle_document

    path = tmp_path / "real.db"
    token = str(uuid4())
    persist_bundle(
        path, approved_bundle_document(), token, {"version": 1, "entities": [], "bindings": []}
    )
    request_path = tmp_path / "request-v1.json"
    request_path.write_text(
        json.dumps(
            {
                "version": 1,
                "current_batch_id": token,
                "history_batch_ids": [],
                "context": {"namespace": "tcgdex_repository", "kind": "set", "language": "es"},
            }
        )
    )
    assert cli.main(["discover", "--db", str(path), "--request", str(request_path)]) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["version"] == 1 and payload["error_category"] == "synthetic_only"
