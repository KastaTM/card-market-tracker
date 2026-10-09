"""Observable offline operation, error distinction and privacy."""

import json
import socket
from pathlib import Path
from uuid import UUID

import pytest

from card_market_tracker.cli import main

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize(
    ("case", "expected", "outcome"),
    [
        ("valid", 0, "ok"),
        ("empty", 0, "empty"),
        ("mixed", 3, "mixed"),
        ("candidates", 3, "mixed"),
        ("invalid", 2, "error"),
    ],
)
def test_catalog_cases(case, expected, outcome, capsys, monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("unexpected network")

    monkeypatch.setattr(socket.socket, "connect", no_network)
    command = [
        "catalog",
        "--input",
        str(FIXTURES / f"synthetic_tcgdex_{case}.json"),
        "--manifest",
        str(FIXTURES / "synthetic_manifest.json"),
    ]
    assert main(command) == expected
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    event = json.loads(captured.err)
    assert result["result"] == outcome
    assert event["event"] == "catalog.completed"
    assert event["result"] == outcome
    assert event["duration_ms"] >= 0
    UUID(event["run_id"])
    assert str(FIXTURES) not in captured.err
    assert main(command) == expected
    assert json.loads(capsys.readouterr().out) == result


def test_parse_failure_not_empty(tmp_path, capsys):
    path = tmp_path / "sentinel-secret-input.json"
    path.write_text('{"sentinel-secret":', encoding="utf-8")
    assert (
        main(
            [
                "catalog",
                "--input",
                str(path),
                "--manifest",
                str(FIXTURES / "synthetic_manifest.json"),
            ]
        )
        == 2
    )
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert result["result"] == "error" and result["counts"] is None
    assert "sentinel-secret" not in captured.out + captured.err


def test_unreadable_manifest(tmp_path, capsys):
    assert (
        main(
            [
                "catalog",
                "--input",
                str(FIXTURES / "synthetic_tcgdex_empty.json"),
                "--manifest",
                str(tmp_path / "sentinel-secret"),
            ]
        )
        == 2
    )
    captured = capsys.readouterr()
    assert "sentinel-secret" not in captured.out + captured.err
    assert json.loads(captured.out)["result"] == "error"


def test_unexpected_catalog_failure(monkeypatch, capsys):
    import card_market_tracker.cli as cli

    def broken(path):
        raise RuntimeError("sentinel-secret")

    monkeypatch.setattr(cli, "read_json", broken)
    assert main(["catalog", "--input", "input", "--manifest", "manifest"]) == 1
    captured = capsys.readouterr()
    assert "sentinel-secret" not in captured.out + captured.err
    assert json.loads(captured.err)["error_category"] == "local_execution"


def test_catalog_requires_paths(capsys):
    assert main(["catalog"]) == 2
    assert json.loads(capsys.readouterr().err)["event"] == "config.invalid"


def test_all_rejected_is_unsuccessful(tmp_path, capsys):
    path = tmp_path / "batch.json"
    path.write_text(
        json.dumps({"version": 1, "provenance": "synthetic", "records": [None]}), encoding="utf-8"
    )
    assert (
        main(
            [
                "catalog",
                "--input",
                str(path),
                "--manifest",
                str(FIXTURES / "synthetic_manifest.json"),
            ]
        )
        == 3
    )
    result = json.loads(capsys.readouterr().out)
    assert result["counts"]["accepted"] == 0
    assert result["counts"]["rejected"] == 1
    assert result["result"] == "mixed"
