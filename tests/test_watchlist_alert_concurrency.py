"""DB author real-process admission races and SQLite/recovery crash boundaries."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from test_watchlist_alert_source import sources

from card_market_tracker.watchlist_alerts import application, storage
from card_market_tracker.watchlist_alerts.errors import OutboxError

WORKER = r"""
import json
import os
import sys
import time
from pathlib import Path
from card_market_tracker.watchlist_alerts import application, storage

mode, config_path, ready_path, gate_path = sys.argv[1:]
config = json.loads(Path(config_path).read_text())
outbox, watchlist, journal = (Path(config[key]) for key in ("outbox", "watchlist", "journal"))
manifest = json.loads(Path(config["manifest"]).read_text())
if mode == "race":
    Path(ready_path).write_bytes(b"ready")
    deadline = time.monotonic() + 12
    while not Path(gate_path).exists():
        if time.monotonic() >= deadline:
            raise SystemExit(80)
        time.sleep(0.005)
elif mode == "crash-before":
    execute = storage._execute
    def crashing(db, budget, sql, values=()):
        if sql.startswith("INSERT INTO watchlist_alert_evidence"):
            os._exit(71)
        return execute(db, budget, sql, values)
    storage._execute = crashing
elif mode == "crash-after":
    response = storage._response
    def crashing(operation, budget, **fields):
        if operation == "enqueue":
            os._exit(72)
        return response(operation, budget, **fields)
    storage._response = crashing
elif mode == "crash-publication":
    unlink = Path.unlink
    def crashing(path, *args, **kwargs):
        if path.name.endswith(".tmp"):
            os._exit(73)
        return unlink(path, *args, **kwargs)
    Path.unlink = crashing
    storage.backup(outbox, Path(config["destination"]), timeout=5)
    raise SystemExit(81)
print(json.dumps(application.enqueue(
    outbox, watchlist, journal, manifest, config["signal"], "process-preview", timeout=5
)), flush=True)
"""


@pytest.fixture
def originals(tmp_path):
    watchlist, journal, manifest, _, points = sources(tmp_path)
    outbox, manifest_path = tmp_path / "outbox.db", tmp_path / "manifest.json"
    storage.initialize(outbox)
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    config = {
        "outbox": str(outbox),
        "watchlist": str(watchlist),
        "journal": str(journal),
        "manifest": str(manifest_path),
        "signal": points[-1]["signal_ids"][0],
        "destination": str(tmp_path / "published.db"),
    }
    config_path = tmp_path / "process-config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return config, config_path, manifest


def child_command(mode, config_path, ready, gate):
    return [
        sys.executable,
        "-X",
        "utf8",
        "-c",
        WORKER,
        mode,
        str(config_path),
        str(ready),
        str(gate),
    ]


def enqueue(config, manifest):
    return application.enqueue(
        Path(config["outbox"]),
        Path(config["watchlist"]),
        Path(config["journal"]),
        manifest,
        config["signal"],
        "process-preview",
        timeout=5,
    )


def test_two_processes_race_through_actual_original_admission_one_records_one_replays(
    originals, tmp_path
):
    config, config_path, manifest = originals
    before = (Path(config["watchlist"]).read_bytes(), Path(config["journal"]).read_bytes())
    gate = tmp_path / "gate"
    ready = [tmp_path / f"ready-{index}" for index in range(2)]
    processes = [
        subprocess.Popen(
            child_command("race", config_path, marker, gate),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        for marker in ready
    ]
    try:
        deadline = time.monotonic() + 12
        while not all(marker.exists() for marker in ready):
            assert all(p.poll() is None for p in processes)
            assert time.monotonic() < deadline
            time.sleep(0.005)
        gate.write_bytes(b"go")
        responses = []
        for process in processes:
            stdout, stderr = process.communicate(timeout=20)
            assert process.returncode == 0, stderr
            responses.append(json.loads(stdout))
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=5)
    assert sorted(row["result"] for row in responses) == ["recorded", "replayed"]
    assert len({row["alert_id"] for row in responses}) == 1
    assert storage.verify(Path(config["outbox"]))["counts"] == {"alerts": 1, "evidence": 1}
    assert enqueue(config, manifest)["result"] == "replayed"
    assert (Path(config["watchlist"]).read_bytes(), Path(config["journal"]).read_bytes()) == before


@pytest.mark.parametrize(
    "mode,exit_code,retry_result",
    [
        ("crash-before", 71, "recorded"),
        ("crash-after", 72, "replayed"),
    ],
)
def test_process_death_before_and_after_commit_recovers_without_half_pair(
    originals, tmp_path, mode, exit_code, retry_result
):
    config, config_path, manifest = originals
    before = (Path(config["watchlist"]).read_bytes(), Path(config["journal"]).read_bytes())
    result = subprocess.run(
        child_command(mode, config_path, tmp_path / "unused", tmp_path / "unused-gate"),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=20,
    )
    assert result.returncode == exit_code, result.stderr
    if mode == "crash-after":
        assert storage.verify(Path(config["outbox"]))["counts"] == {"alerts": 1, "evidence": 1}
    # A new product writer opens rw and permits SQLite to recover its own journal.
    # No test code removes recovery files or manually repairs database rows.
    assert enqueue(config, manifest)["result"] == retry_result
    assert storage.verify(Path(config["outbox"]))["counts"] == {"alerts": 1, "evidence": 1}
    assert (Path(config["watchlist"]).read_bytes(), Path(config["journal"]).read_bytes()) == before


def test_process_death_after_exclusive_link_preserves_two_names_for_inspection(originals, tmp_path):
    config, config_path, manifest = originals
    enqueue(config, manifest)
    source = Path(config["outbox"])
    before = source.read_bytes()
    result = subprocess.run(
        child_command(
            "crash-publication", config_path, tmp_path / "unused", tmp_path / "unused-gate"
        ),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=20,
    )
    assert result.returncode == 73, result.stderr
    destination = Path(config["destination"])
    (provisional,) = tmp_path.glob(".cmt-watchlist-alert-outbox-*.tmp")
    assert destination.exists() and provisional.exists()
    assert os.path.samefile(destination, provisional)
    assert destination.stat().st_nlink == provisional.stat().st_nlink == 2
    with pytest.raises(OutboxError, match="unsafe_destination"):
        storage.verify(destination)
    assert source.read_bytes() == before
    assert storage.verify(source)["counts"] == {"alerts": 1, "evidence": 1}


def test_foreign_hot_journal_is_not_recovered_by_wrong_outbox_writer(originals, tmp_path):
    """A crashed foreign fixture is evidence; passing it as outbox must change no byte."""
    config, _, manifest = originals
    foreign = tmp_path / "foreign-watchlist.db"
    foreign.write_bytes(Path(config["watchlist"]).read_bytes())
    crash = r"""
import os
import sqlite3
import sys
db = sqlite3.connect(sys.argv[1])
db.execute("PRAGMA synchronous=FULL")
db.execute("PRAGMA cache_size=2")
db.execute("BEGIN IMMEDIATE")
db.execute("CREATE TABLE uncommitted_probe(payload BLOB)")
for index in range(64):
    db.execute("INSERT INTO uncommitted_probe VALUES (zeroblob(4096))")
os._exit(74)
"""
    result = subprocess.run(
        [sys.executable, "-c", crash, str(foreign)], capture_output=True, timeout=20
    )
    assert result.returncode == 74, result.stderr
    journal = Path(str(foreign) + "-journal")
    assert journal.exists()
    assert journal.read_bytes()[:8] == bytes.fromhex("d9d505f920a163d7")
    before = foreign.read_bytes(), journal.read_bytes()
    with pytest.raises(OutboxError, match="storage_schema"):
        application.enqueue(
            foreign,
            Path(config["watchlist"]),
            Path(config["journal"]),
            manifest,
            config["signal"],
            "wrong-outbox",
            timeout=5,
        )
    assert journal.exists()
    assert (foreign.read_bytes(), journal.read_bytes()) == before
