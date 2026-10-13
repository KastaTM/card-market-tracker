"""Discovery CLI separates complete evidence, input failure and local failure."""

import json
import socket
from pathlib import Path

import pytest

from card_market_tracker import cli
from card_market_tracker.persistence.input import read_persistence
from card_market_tracker.persistence.sqlite_repository import persist

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "history.sqlite3"
    for case in ("history", "current", "empty", "rejected"):
        persist(
            path,
            read_persistence(
                FIXTURES / f"synthetic_discovery_{case}.json",
                FIXTURES / "synthetic_discovery_manifest.json",
            ),
        )
    return path


def invoke(capsys, database, case="request", expected=0):
    args = [
        "discover",
        "--db",
        str(database),
        "--request",
        str(FIXTURES / f"synthetic_discovery_{case}.json"),
    ]
    assert cli.main(args) == expected
    output = capsys.readouterr()
    payload = json.loads(output.out)
    logs = [json.loads(line) for line in output.err.splitlines()]
    assert len(logs) == 1 and logs[0]["event"] == "discovery.completed"
    assert logs[0]["result"] == payload["result"] and logs[0]["duration_ms"] >= 0
    for forbidden in (str(database), str(FIXTURES), "tcgdex", "11111111-1111", "22222222-2222"):
        assert forbidden not in output.err
    if expected:
        assert payload["counts"] is None and payload["events"] == []
        assert "event_count" not in logs[0] and "discovery_observation_count" not in logs[0]
    else:
        assert logs[0]["event_count"] == len(payload["events"])
        assert logs[0]["batch_count"] == payload["counts"]["batches"]
    return payload, logs[0]


@pytest.mark.parametrize(
    "case,result",
    [
        ("request", "discoveries"),
        ("baseline_request", "baseline"),
        ("no_discoveries_request", "no_discoveries"),
        ("empty_request", "discoveries"),
    ],
)
def test_success_results_nonmutation_replay_and_no_network(
    capsys, database, case, result, monkeypatch
):
    def deny(*args, **kwargs):
        raise AssertionError("runtime attempted network")

    monkeypatch.setattr(socket, "socket", deny)
    before = database.read_bytes()
    first, log = invoke(capsys, database, case)
    second, replay_log = invoke(capsys, database, case)
    assert first == second and first["result"] == result
    assert log["run_id"] != replay_log["run_id"]
    assert database.read_bytes() == before
    assert "run_id" not in first and "duration_ms" not in first


@pytest.mark.parametrize(
    "case,category",
    [
        ("rejected_request", "incomplete_evidence"),
        ("context_request", "context_mismatch"),
    ],
)
def test_data_failure_never_reports_success(capsys, database, case, category):
    payload, _ = invoke(capsys, database, case, 2)
    assert payload["error_category"] == category


def test_missing_database_never_created(capsys, tmp_path):
    path = tmp_path / "missing.sqlite3"
    payload, _ = invoke(capsys, path, expected=1)
    assert payload["error_category"] == "storage_io" and not path.exists()


@pytest.mark.parametrize(
    "args",
    [
        ["discover"],
        ["discover", "--db", "private-path"],
        ["discover", "--request", "private-path"],
        ["discover", "--db", "secret-path", "--request", "secret-path", "--sql", "secret"],
    ],
)
def test_missing_or_invalid_arguments_return_discovery_json(capsys, args):
    assert cli.main(args) == 2
    output = capsys.readouterr()
    assert json.loads(output.out)["result"] == "error"
    event = json.loads(output.err)
    assert event["event"] == "discovery.completed" and event["error_category"] == "invalid_field"
    assert "path" not in output.err and "secret" not in output.err


@pytest.mark.parametrize(
    "content,category",
    [
        (None, "input_io"),
        ("{", "invalid_json"),
        ('{"version":1,"version":1}', "duplicate_key"),
        (
            '{"version":true,"current_batch_id":"22222222-2222-4222-8222-222222222222",'
            '"history_batch_ids":[],"context":{"namespace":"tcgdex","kind":"set","language":"es"}}',
            "unsupported_version",
        ),
    ],
)
def test_invalid_request_exit2_and_redaction(capsys, tmp_path, content, category):
    path = tmp_path / "private-request.json"
    if content is not None:
        path.write_text(content, encoding="utf-8")
    assert cli.main(["discover", "--db", str(tmp_path / "absent.db"), "--request", str(path)]) == 2
    output = capsys.readouterr()
    assert json.loads(output.out)["error_category"] == category
    assert "private-request" not in output.err and "absent.db" not in output.err


def test_unexpected_and_catalog_boundary_errors_are_sanitized(capsys, tmp_path, monkeypatch):
    from card_market_tracker.catalog.validation import CatalogError

    for failure, expected, category in (
        (RuntimeError("sensitive SQL and path"), 1, "local_execution"),
        (CatalogError("invalid_field"), 2, "invalid_field"),
    ):

        def fail(_path, error=failure):
            raise error

        monkeypatch.setattr(cli, "read_request", fail)
        payload, _ = invoke(capsys, tmp_path / "absent.db", expected=expected)
        assert payload["error_category"] == category
