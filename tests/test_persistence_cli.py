"""Storage CLI results, confirmed rows, bounded reads and error privacy."""

import json
import socket
from pathlib import Path
from uuid import UUID

import pytest

from card_market_tracker.cli import main

FIXTURES = Path(__file__).parent / "fixtures"


def invoke(arguments, capsys, expected=0):
    assert main(arguments) == expected
    captured = capsys.readouterr()
    result, event = json.loads(captured.out), json.loads(captured.err)
    assert event["event"] == "persistence.completed"
    assert event["result"] == result["result"] and event["duration_ms"] >= 0
    UUID(event["run_id"])
    assert "sentinel-private" not in captured.out + captured.err
    assert str(FIXTURES) not in captured.err
    if result["result"] == "error":
        assert result["counts"] is result["committed"] is None
        assert "new_observation_count" not in event and "input_count" not in event
    return result, event


def command(database, case="valid"):
    return [
        "persist",
        "--db",
        str(database),
        "--input",
        str(FIXTURES / f"synthetic_persistence_{case}.json"),
        "--manifest",
        str(FIXTURES / "synthetic_manifest.json"),
    ]


@pytest.mark.parametrize(
    "case,code,result",
    [
        ("valid", 0, "ok"),
        ("mixed", 3, "mixed"),
        ("candidates", 3, "mixed"),
        ("rejected", 3, "mixed"),
        ("empty", 0, "empty"),
        ("invalid", 2, "error"),
        ("missing_capture", 2, "error"),
        ("contradictory_capture", 2, "error"),
        ("documented", 2, "error"),
        ("observed", 2, "error"),
    ],
)
def test_distinct_batch_outcomes(tmp_path, capsys, monkeypatch, case, code, result):
    def no_network(*args, **kwargs):
        raise AssertionError("network is outside P3a")

    monkeypatch.setattr(socket.socket, "connect", no_network)
    database = tmp_path / "history.sqlite3"
    payload, event = invoke(command(database, case), capsys, code)
    assert payload["result"] == result and event["operation"] == "persist"
    if result == "error":
        assert not database.exists()
    else:
        counts = payload["counts"]
        assert counts["input"] == counts["accepted"] + counts["candidates"] + counts["rejected"]
        assert payload["committed"]["observations"] == counts["accepted"] + counts["candidates"]
        assert event["new_batch_count"] == 1
        if case in ("empty", "rejected", "candidates"):
            assert payload["committed"]["entities"] == 0


def test_replay_later_conflict_and_candidate_exact_read(tmp_path, capsys):
    database = tmp_path / "history.sqlite3"
    first, first_event = invoke(command(database), capsys)
    replay, event = invoke(command(database), capsys)
    assert replay["result"] == "replay"
    assert replay["first_persisted_at"] == first["first_persisted_at"]
    assert replay["committed"] == {"entities": 0, "observations": 0}
    assert event["run_id"] != first_event["run_id"]
    assert event["new_batch_count"] == 0
    later, _ = invoke(command(database, "later"), capsys)
    assert later["committed"]["observations"] == 7
    assert later["committed"]["entities"] == 0
    invoke(command(database, "conflict"), capsys, 2)
    result, _ = invoke(
        ["observations", "--db", str(database), "--batch-id", first["batch_id"]], capsys
    )
    assert len(result["records"]) == 7
    target = result["records"][0]["cmt_id"]
    by_target, _ = invoke(["observations", "--db", str(database), "--cmt-id", target], capsys)
    assert len(by_target["records"]) == 2 * sum(
        row["cmt_id"] == target for row in result["records"]
    )
    captures = [row["observation"]["captured_at"] for row in by_target["records"]]
    assert captures == sorted(captures) and len(set(captures)) == 2
    mixed, _ = invoke(command(database, "mixed"), capsys, 3)
    mixed_rows, _ = invoke(
        ["observations", "--db", str(database), "--batch-id", mixed["batch_id"]], capsys
    )
    candidate = mixed_rows["records"][1]
    reference = tmp_path / "reference.json"
    reference.write_text(json.dumps(candidate["observation"]["reference"]), encoding="utf-8")
    candidates, _ = invoke(
        ["observations", "--db", str(database), "--candidate-reference", str(reference)], capsys
    )
    assert candidates["records"] == [candidate]
    assert candidates["records"][0]["cmt_id"] is None
    assert mixed_rows["records"][2]["observation"] is None


def test_init_verify_backup_restore_and_safe_existing_destination(tmp_path, capsys):
    database = tmp_path / "history.sqlite3"
    invoke(["db", "init", "--db", str(database)], capsys)
    invoke(["db", "init", "--db", str(database)], capsys)
    assert invoke(["observations", "--db", str(database)], capsys)[0]["result"] == "empty"
    invoke(command(database), capsys)
    before = invoke(["observations", "--db", str(database)], capsys)[0]
    copied, restored = tmp_path / "backup.sqlite3", tmp_path / "restored.sqlite3"
    invoke(["db", "verify", "--db", str(database)], capsys)
    invoke(["db", "backup", "--db", str(database), "--destination", str(copied)], capsys)
    invoke(["db", "restore", "--db", str(copied), "--destination", str(restored)], capsys)
    assert invoke(["observations", "--db", str(restored)], capsys)[0] == before
    assert invoke(command(restored), capsys)[0]["result"] == "replay"
    error, _ = invoke(
        ["db", "backup", "--db", str(database), "--destination", str(copied)], capsys, 1
    )
    assert error["error_category"] == "unsafe_destination"
    assert invoke(["observations", "--db", str(copied)], capsys)[0] == before


@pytest.mark.parametrize(
    "arguments",
    [
        ["persist"],
        ["observations"],
        ["db"],
        ["db", "verify"],
        ["observations", "--db", "sentinel-private", "--limit", "invalid"],
        ["observations", "--db", "sentinel-private", "--batch-id", "x", "--cmt-id", "x"],
    ],
)
def test_invalid_arguments_have_safe_json(arguments, capsys):
    invoke(arguments, capsys, 2)


@pytest.mark.parametrize("limit", ["0", "-1", "1001"])
def test_invalid_read_limit_does_not_create_database(tmp_path, capsys, limit):
    database = tmp_path / "missing.sqlite3"
    invoke(["observations", "--db", str(database), "--limit", limit], capsys, 2)
    assert not database.exists()


def test_missing_database_and_empty_read_are_different(tmp_path, capsys):
    database = tmp_path / "missing.sqlite3"
    error, _ = invoke(["observations", "--db", str(database)], capsys, 1)
    assert error["error_category"] == "storage_io" and not database.exists()


@pytest.mark.parametrize("category", [None, "storage_locked", "storage_corrupt", "storage_io"])
def test_storage_failure_never_reports_attempted_counts(tmp_path, capsys, monkeypatch, category):
    import card_market_tracker.cli as cli
    from card_market_tracker.persistence.errors import PersistenceError

    def fail(*args, **kwargs):
        if category is None:
            raise RuntimeError("sentinel-private-storage")
        raise PersistenceError(category)

    monkeypatch.setattr(cli, "persist", fail)
    invoke(command(tmp_path / "history.sqlite3"), capsys, 1)


def test_candidate_reference_validation_redacts_input(tmp_path, capsys):
    reference = tmp_path / "sentinel-private.json"
    reference.write_text('{"namespace":"sentinel-private"}', encoding="utf-8")
    invoke(
        [
            "observations",
            "--db",
            str(tmp_path / "missing.sqlite3"),
            "--candidate-reference",
            str(reference),
        ],
        capsys,
        2,
    )


def test_missing_candidate_reference_is_a_local_io_error(tmp_path, capsys):
    result, _ = invoke(
        [
            "observations",
            "--db",
            str(tmp_path / "missing.sqlite3"),
            "--candidate-reference",
            str(tmp_path / "sentinel-private.json"),
        ],
        capsys,
        1,
    )
    assert result["error_category"] == "input_io"
