"""RW-01 author regressions: genuine original sources and transactional invariants."""

from __future__ import annotations

import copy
import json
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from card_market_tracker.watchlist import application as watchlist_app
from card_market_tracker.watchlist import storage as watchlist_storage
from card_market_tracker.watchlist_alerts import application as app
from card_market_tracker.watchlist_alerts import storage
from card_market_tracker.watchlist_alerts.errors import OutboxError
from card_market_tracker.watchlist_journal import application as journal_app
from card_market_tracker.watchlist_journal import storage as journal_storage

TARGET = "541b9d13-9669-4973-8413-397bea14c045"
OTHER_TARGET = "b980e1f7-9bae-432e-b02a-182dbcca478d"


@dataclass(frozen=True)
class Original:
    watchlist: Path
    journal: Path
    manifest: dict[str, Any]
    entry: dict[str, Any]
    signal: str
    sample: dict[str, Any]


def original(
    directory: Path,
    *,
    config: dict[str, Any] | None = None,
    series: str = "synthetic-rw01",
    sample_prefix: str = "sample",
    target: str = TARGET,
    revision: int = 1,
    manifest: dict[str, Any] | None = None,
) -> Original:
    """Create independent P5a/P5b originals using only their public operations."""
    directory.mkdir()
    if manifest is None:
        manifest = json.loads(
            (Path(__file__).parent / "fixtures/synthetic_manifest.json").read_text()
        )
    watchlist, journal = directory / "watchlist.db", directory / "journal.db"
    watchlist_storage.initialize(watchlist)
    effective = {"target_price_minor": 1000, "restock_enabled": True, **(config or {})}
    entry = watchlist_app.add(watchlist, manifest, target, effective, request_token="initial")[
        "entry"
    ]
    if revision == 2:
        entry = watchlist_app.update(
            watchlist,
            manifest,
            entry["watch_id"],
            effective,
            expected_revision=1,
            request_token="revision-two",
        )["entry"]
    journal_storage.initialize(journal)
    previous = None
    for ordinal, stock in enumerate(("OUT_OF_STOCK", "AVAILABLE"), 1):
        current = {
            "version": 1,
            "provenance": "synthetic",
            "sample_id": f"{sample_prefix}-{ordinal}",
            "cmt_id": target,
            "series_key": series,
            "observed_at": f"2026-10-23T12:0{ordinal}:00Z",
            "currency": "EUR",
            "unit_price_minor": 900,
            "shipping_minor": 100,
            "stock": stock,
        }
        point = journal_app.record(
            journal,
            watchlist,
            manifest,
            entry["watch_id"],
            current,
            previous,
            revision=revision,
            as_of=current["observed_at"],
        )
        previous = current
    signal = next(
        key
        for key in point["signal_ids"]
        if journal_storage.signal_get(journal, key)["signal"]["rule"] == "price"
    )
    return Original(watchlist, journal, manifest, entry, signal, current)


def enqueue(outbox: Path, source: Original, alias: str = "rw-preview", **kwargs):
    return app.enqueue(
        outbox,
        source.watchlist,
        source.journal,
        source.manifest,
        source.signal,
        alias,
        **kwargs,
    )


def source_bytes(*sources: Original) -> tuple[bytes, ...]:
    return tuple(
        path.read_bytes() for source in sources for path in (source.watchlist, source.journal)
    )


def retained(outbox: Path, alert_id: str):
    return (
        outbox.read_bytes(),
        storage.get(outbox, alert_id),
        storage.evidence_get(outbox, alert_id),
        storage.list_alerts(outbox),
    )


def healthy_backup(outbox: Path, destination: Path, count: int) -> None:
    counts = {"alerts": count, "evidence": count}
    assert storage.verify(outbox)["counts"] == counts
    assert storage.backup(outbox, destination)["counts"] == counts
    assert storage.verify(destination)["counts"] == counts


@pytest.mark.parametrize(
    "alias,series",
    [
        ("rw-preview", "synthetic-rw01"),
        ("other", "synthetic-rw01"),
        ("rw-preview", "another-series"),
        ("other", "another-series"),
    ],
)
@pytest.mark.parametrize(
    "change",
    [
        {"target_price_minor": 1200},
        {"priority": "high"},
        {"max_age_seconds": 120},
        {"restock_enabled": False},
    ],
    ids=["target", "priority", "freshness", "restock"],
)
def test_public_incompatible_originals_are_rejected_without_mutation(
    tmp_path, alias, series, change
):
    first = original(tmp_path / "first")
    second = original(tmp_path / "second", config=change, series=series)
    assert first.entry["watch_id"] == second.entry["watch_id"]
    assert first.entry["revision"] == second.entry["revision"] == 1
    assert first.entry != second.entry and first.signal != second.signal
    origins = source_bytes(first, second)
    outbox = tmp_path / "outbox.db"
    storage.initialize(outbox)
    recorded = enqueue(outbox, first)
    assert recorded["result"] == "recorded"
    before = retained(outbox, recorded["alert_id"])
    with pytest.raises(OutboxError) as caught:
        enqueue(outbox, second, alias)
    assert caught.value.category == "identity_conflict" and caught.value.exit_code == 2
    assert retained(outbox, recorded["alert_id"]) == before
    healthy_backup(outbox, tmp_path / "backup.db", 1)
    assert source_bytes(first, second) == origins


def test_complete_canonical_identity_is_compared_from_genuine_originals(tmp_path):
    first = original(tmp_path / "first")
    changed_manifest = copy.deepcopy(first.manifest)
    next(row for row in changed_manifest["entities"] if row["kind"] == "card")["card_number"] = (
        "002"
    )
    second = original(tmp_path / "second", manifest=changed_manifest)
    assert first.entry["watch_id"] == second.entry["watch_id"]
    assert first.entry["canonical_identity"] != second.entry["canonical_identity"]
    outbox = tmp_path / "outbox.db"
    storage.initialize(outbox)
    saved = enqueue(outbox, first)
    before, origins = retained(outbox, saved["alert_id"]), source_bytes(first, second)
    with pytest.raises(OutboxError, match="identity_conflict"):
        enqueue(outbox, second)
    assert retained(outbox, saved["alert_id"]) == before
    assert source_bytes(first, second) == origins
    healthy_backup(outbox, tmp_path / "backup.db", 1)


@pytest.mark.parametrize(
    "options,alias",
    [
        ({}, "other"),
        ({"sample_prefix": "independent"}, "rw-preview"),
        ({"series": "independent"}, "rw-preview"),
    ],
)
def test_semantically_equal_independent_originals_coexist(tmp_path, options, alias):
    first = original(tmp_path / "first")
    second = original(tmp_path / "second", **options)
    assert first.entry == second.entry
    outbox = tmp_path / "outbox.db"
    storage.initialize(outbox)
    origins = source_bytes(first, second)
    left = enqueue(outbox, first)
    right = enqueue(outbox, second, alias)
    assert left["result"] == right["result"] == "recorded"
    assert left["alert_id"] != right["alert_id"]
    healthy_backup(outbox, tmp_path / "backup.db", 2)
    assert source_bytes(first, second) == origins


@pytest.mark.parametrize("options", [{"revision": 2}, {"target": OTHER_TARGET}])
def test_distinct_revision_and_product_watch_are_independent(tmp_path, options):
    first = original(tmp_path / "first")
    second = original(tmp_path / "second", config={"target_price_minor": 1200}, **options)
    assert (first.entry["watch_id"], first.entry["revision"]) != (
        second.entry["watch_id"],
        second.entry["revision"],
    )
    outbox = tmp_path / "outbox.db"
    storage.initialize(outbox)
    origins = source_bytes(first, second)
    assert enqueue(outbox, first)["result"] == enqueue(outbox, second)["result"] == "recorded"
    healthy_backup(outbox, tmp_path / "backup.db", 2)
    assert source_bytes(first, second) == origins


def test_ancient_replay_after_growth_and_rejection_preserves_frozen_pair(tmp_path):
    first = original(tmp_path / "first")
    second = original(tmp_path / "second", config={"target_price_minor": 1200})
    outbox = tmp_path / "outbox.db"
    storage.initialize(outbox)
    saved = enqueue(outbox, first)
    before = retained(outbox, saved["alert_id"])
    previous = first.sample
    for ordinal, stock in enumerate(("OUT_OF_STOCK", "AVAILABLE"), 3):
        current = dict(
            previous,
            sample_id=f"later-{ordinal}",
            stock=stock,
            observed_at=f"2026-10-23T12:0{ordinal}:00Z",
        )
        journal_app.record(
            first.journal,
            first.watchlist,
            first.manifest,
            first.entry["watch_id"],
            current,
            previous,
            revision=1,
            as_of=current["observed_at"],
        )
        previous = current
    watchlist_app.update(
        first.watchlist,
        first.manifest,
        first.entry["watch_id"],
        {"target_price_minor": 1500},
        expected_revision=1,
        request_token="later-revision",
    )
    origins = source_bytes(first, second)
    with pytest.raises(OutboxError, match="identity_conflict"):
        enqueue(outbox, second)
    assert enqueue(outbox, first)["result"] == "replayed"
    assert retained(outbox, saved["alert_id"]) == before
    healthy_backup(outbox, tmp_path / "backup.db", 1)
    assert source_bytes(first, second) == origins


WORKER = r"""
import json
import sys
import time
from pathlib import Path
from card_market_tracker.watchlist_alerts import application
from card_market_tracker.watchlist_alerts.errors import OutboxError
config, ready, gate = map(Path, sys.argv[1:])
values = json.loads(config.read_text())
ready.write_bytes(b"ready")
deadline = time.monotonic() + 12
while not gate.exists():
    if time.monotonic() >= deadline:
        raise SystemExit(80)
    time.sleep(0.005)
try:
    result = application.enqueue(
        Path(values["outbox"]), Path(values["watchlist"]), Path(values["journal"]),
        values["manifest"], values["signal"], "race-preview", timeout=5
    )
except OutboxError as error:
    print(json.dumps({"result": "error", "category": error.category}), flush=True)
    raise SystemExit(error.exit_code)
print(json.dumps(result), flush=True)
"""


def test_incompatible_processes_serialize_one_record_and_one_identity_conflict(tmp_path):
    originals = [
        original(tmp_path / "first"),
        original(tmp_path / "second", config={"target_price_minor": 1200}),
    ]
    origins = source_bytes(*originals)
    outbox = tmp_path / "outbox.db"
    storage.initialize(outbox)
    gate, processes, ready = tmp_path / "gate", [], []
    for index, source in enumerate(originals):
        config = tmp_path / f"config-{index}.json"
        config.write_text(
            json.dumps(
                {
                    "outbox": str(outbox),
                    "watchlist": str(source.watchlist),
                    "journal": str(source.journal),
                    "manifest": source.manifest,
                    "signal": source.signal,
                }
            )
        )
        marker = tmp_path / f"ready-{index}"
        ready.append(marker)
        processes.append(
            subprocess.Popen(
                [sys.executable, "-X", "utf8", "-c", WORKER, str(config), str(marker), str(gate)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
        )
    try:
        deadline = time.monotonic() + 12
        while not all(marker.exists() for marker in ready):
            assert all(process.poll() is None for process in processes)
            assert time.monotonic() < deadline
            time.sleep(0.005)
        gate.write_bytes(b"go")
        results = []
        codes = []
        for process in processes:
            stdout, stderr = process.communicate(timeout=20)
            assert process.returncode in (0, 2), stderr
            results.append(json.loads(stdout))
            codes.append(process.returncode)
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=5)
    assert sorted(codes) == [0, 2]
    assert sorted(result["result"] for result in results) == ["error", "recorded"]
    assert (
        next(result for result in results if result["result"] == "error")["category"]
        == "identity_conflict"
    )
    healthy_backup(outbox, tmp_path / "backup.db", 1)
    assert source_bytes(*originals) == origins


@pytest.mark.parametrize("stage", ["watchlist_alerts", "watchlist_alert_evidence", "COMMIT"])
@pytest.mark.parametrize("failure,category", [("timeout", "storage_timeout"), ("io", "storage_io")])
def test_precommit_failure_after_consistency_check_rolls_back(
    tmp_path, monkeypatch, stage, failure, category
):
    first = original(tmp_path / "first")
    second = original(tmp_path / "second", sample_prefix="other")
    outbox = tmp_path / "outbox.db"
    storage.initialize(outbox)
    saved = enqueue(outbox, first)
    before, origins = retained(outbox, saved["alert_id"]), source_bytes(first, second)
    budget = storage.Budget()
    execute, reached = storage._execute, []

    def fail(db, supplied, sql, values=()):
        if sql == stage or sql.startswith("INSERT INTO " + stage + " "):
            assert supplied is budget and db.in_transaction
            reached.append(stage)
            if failure == "timeout":
                supplied.deadline = 0
            else:
                raise OSError("controlled failure")
        return execute(db, supplied, sql, values)

    with monkeypatch.context() as context:
        context.setattr(storage, "_execute", fail)
        with pytest.raises(OutboxError, match=category):
            enqueue(outbox, second, _budget=budget)
    assert reached == [stage]
    assert retained(outbox, saved["alert_id"]) == before
    healthy_backup(outbox, tmp_path / "backup.db", 1)
    assert source_bytes(first, second) == origins


@pytest.mark.parametrize("attempt", ["replay", "different-entry"])
def test_preexisting_contradiction_is_corruption_before_candidate_conflict(tmp_path, attempt):
    first = original(tmp_path / "first")
    second = original(tmp_path / "second", config={"target_price_minor": 1200})
    third = original(tmp_path / "third", config={"target_price_minor": 1400})
    outbox, other = tmp_path / "outbox.db", tmp_path / "other.db"
    storage.initialize(outbox)
    storage.initialize(other)
    enqueue(outbox, first)
    enqueue(other, second)
    # Deliberately construct the old writer's contradictory local state from two
    # independently admitted pairs. Original P5a/P5b sources are never mutated.
    with sqlite3.connect(outbox) as writer, sqlite3.connect(other) as reader:
        writer.execute(
            "INSERT INTO watchlist_alerts VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            reader.execute("SELECT * FROM watchlist_alerts").fetchone(),
        )
        writer.execute(
            "INSERT INTO watchlist_alert_evidence VALUES (?,?,?)",
            reader.execute("SELECT * FROM watchlist_alert_evidence").fetchone(),
        )
    before, origins = outbox.read_bytes(), source_bytes(first, second, third)
    with pytest.raises(OutboxError, match="storage_corrupt"):
        storage.verify(outbox)
    with pytest.raises(OutboxError, match="storage_corrupt"):
        enqueue(outbox, first if attempt == "replay" else third)
    assert outbox.read_bytes() == before
    assert source_bytes(first, second, third) == origins


@pytest.mark.parametrize("replay", [False, True])
def test_writer_reuses_one_fresh_verified_fold_and_the_original_budget(
    tmp_path, monkeypatch, replay
):
    source = original(tmp_path / "original")
    outbox = tmp_path / "outbox.db"
    storage.initialize(outbox)
    first = enqueue(outbox, source)
    second = enqueue(outbox, source, "second")
    budget = storage.Budget()
    load_pair, fold = storage._load_pair, storage._fold
    loaded, folds = [], []

    def counted_pair(db, supplied, key):
        assert supplied is budget and db.in_transaction
        assert db.execute("PRAGMA query_only").fetchone()[0] == 0
        loaded.append(key)
        return load_pair(db, supplied, key)

    def counted_fold(db, supplied, **kwargs):
        assert supplied is budget and db.in_transaction
        folds.append(db)
        return fold(db, supplied, **kwargs)

    with monkeypatch.context() as context:
        context.setattr(storage, "_load_pair", counted_pair)
        context.setattr(storage, "_fold", counted_fold)
        saved = enqueue(outbox, source, "rw-preview" if replay else "third", _budget=budget)
    assert len(folds) == 1
    assert loaded.count(first["alert_id"]) == loaded.count(second["alert_id"]) == 1
    if replay:
        assert saved["result"] == "replayed" and len(loaded) == 2
    else:
        assert saved["result"] == "recorded" and loaded.count(saved["alert_id"]) == 1
    healthy_backup(outbox, tmp_path / "backup.db", 2 if replay else 3)


def test_malformed_retained_pair_takes_priority_over_incoming_identity_conflict(tmp_path):
    first = original(tmp_path / "first")
    second = original(tmp_path / "second", config={"target_price_minor": 1200})
    outbox = tmp_path / "outbox.db"
    storage.initialize(outbox)
    enqueue(outbox, first)
    # Only the local outbox is intentionally corrupted; restore the exact trigger
    # so the semantic read, rather than catalog inventory, must detect this.
    with sqlite3.connect(outbox) as db:
        (trigger,) = db.execute(
            "SELECT sql FROM sqlite_master WHERE name='watchlist_alerts_no_update'"
        ).fetchone()
        db.execute("DROP TRIGGER watchlist_alerts_no_update")
        db.execute("UPDATE watchlist_alerts SET message_text='invalid retained render'")
        db.execute(trigger)
    before, origins = outbox.read_bytes(), source_bytes(first, second)
    with pytest.raises(OutboxError, match="storage_corrupt"):
        enqueue(outbox, second)
    assert outbox.read_bytes() == before
    assert source_bytes(first, second) == origins
