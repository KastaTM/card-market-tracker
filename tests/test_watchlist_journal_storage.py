"""DB author probes for CMTQ atomic append, complete fold and exclusive recovery."""

import copy
import json
import os
import sqlite3
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest

from card_market_tracker.watchlist_journal import identity, schema, storage
from card_market_tracker.watchlist_journal.errors import JournalError

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def snapshots():
    vectors = json.loads((FIXTURES / "p5b_identity_vectors_v1.json").read_text())["vectors"]
    return vectors["baseline"]["object"], vectors["second"]["object"]


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "journal.db"
    storage.initialize(path)
    return path


@pytest.fixture
def populated(database, snapshots):
    first, second = snapshots
    one = storage._record_validated(database, first)
    two = storage._record_validated(database, second)
    return database, first, second, one, two


def category(expected, operation):
    with pytest.raises(JournalError) as caught:
        operation()
    assert caught.value.category == expected


def privileged(path, trigger, sql, values=()):
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA ignore_check_constraints=ON")
        if trigger:
            db.execute("DROP TRIGGER " + trigger)
        db.execute(sql, values)
        if trigger:
            db.execute(
                next(item for item in schema.STATEMENTS if "CREATE TRIGGER " + trigger in item)
            )


def test_independent_exact_strict_schema_and_no_implicit_init(database, tmp_path, snapshots):
    with sqlite3.connect(database) as db:
        assert db.execute("PRAGMA application_id").fetchone() == (0x434D5451,)
        assert db.execute("PRAGMA user_version").fetchone() == (1,)
        assert (
            tuple(db.execute("SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"))
            == schema.expected_inventory()
        )
        assert len(schema.expected_inventory()) == 23
        assert all(
            row[5] == 1
            for row in db.execute("PRAGMA table_list")
            if row[1].startswith("wl_journal_")
        )
    assert storage.verify(database)["counts"] == {"sequences": 0, "evaluations": 0, "signals": 0}
    before = database.read_bytes()
    category("unsafe_destination", lambda: storage.initialize(database))
    assert database.read_bytes() == before
    missing = tmp_path / "missing.db"
    category("storage_missing", lambda: storage._record_validated(missing, snapshots[0]))
    assert not missing.exists()


def test_ancient_replay_preserves_original_time_heads_signals_and_bytes(populated):
    path, first, second, one, two = populated
    before = path.read_bytes()
    assert storage._record_validated(path, first) == {**one, "result": "replayed"}
    assert storage._record_validated(path, second) == {**two, "result": "replayed"}
    assert one["signals_count"] == 0
    assert two["signals_count"] == 2
    assert path.read_bytes() == before
    with sqlite3.connect(path) as db:
        assert db.execute(
            "SELECT head_eval_id,head_ordinal FROM wl_journal_sequences"
        ).fetchone() == (two["evaluation_id"], 2)


@pytest.mark.parametrize("field,value", [("as_of", "2026-10-23T12:01:00Z"), ("current", None)])
def test_sample_reuse_with_changed_semantics_conflicts(populated, field, value):
    path, _, second, _, _ = populated
    changed = copy.deepcopy(second)
    if field == "current":
        changed["current"]["unit_price_minor"] = 901
    else:
        changed[field] = value
    before = path.read_bytes()
    category("replay_conflict", lambda: storage._record_validated(path, changed))
    assert path.read_bytes() == before


def test_new_sample_cannot_backfill_equal_time_or_omit_predecessor(populated):
    path, first, second, _, _ = populated
    for observed, previous, expected in [
        ("2026-10-23T12:00:00Z", first["current"], "invalid_chronology"),
        ("2026-10-23T13:00:00Z", first["current"], "replay_conflict"),
        ("2026-10-23T13:00:00Z", None, "replay_conflict"),
    ]:
        current = {**second["current"], "sample_id": "synthetic-third", "observed_at": observed}
        changed = identity.normalized_snapshot(
            second["entry"], current, previous, as_of="2026-10-23T13:00:00Z"
        )
        before = path.read_bytes()
        category(expected, lambda changed=changed: storage._record_validated(path, changed))
        assert path.read_bytes() == before


@pytest.mark.parametrize("stage", ["evaluation", "first-signal", "second-signal", "head", "commit"])
def test_injected_failure_rolls_back_every_append_component(
    database, snapshots, monkeypatch, stage
):
    first, second = snapshots
    storage._record_validated(database, first)
    original = storage._execute
    signals = 0

    def failing(db, budget, sql, values=()):
        nonlocal signals
        if sql.startswith("INSERT INTO wl_journal_signals"):
            signals += 1
        fail = (
            (stage == "evaluation" and sql.startswith("INSERT INTO wl_journal_evaluations"))
            or (stage == "first-signal" and signals == 1)
            or (stage == "second-signal" and signals == 2)
            or (stage == "head" and sql.startswith("UPDATE wl_journal_sequences"))
            or (stage == "commit" and sql == "COMMIT")
        )
        if fail:
            raise OSError("synthetic disk failure")
        return original(db, budget, sql, values)

    with monkeypatch.context() as patch:
        patch.setattr(storage, "_execute", failing)
        category("storage_io", lambda: storage._record_validated(database, second))
    assert storage.verify(database)["counts"] == {"sequences": 1, "evaluations": 1, "signals": 0}
    assert storage._record_validated(database, second)["signals_count"] == 2


@pytest.mark.parametrize(
    "mutation",
    [
        "PRAGMA application_id=7",
        "PRAGMA user_version=2",
        "CREATE TABLE foreign_object(x TEXT)",
        "DROP INDEX wl_journal_signals_by_sequence",
        "DROP TRIGGER wl_journal_evaluation_no_update",
    ],
)
def test_exact_schema_rejects_all_unknown_or_changed_objects(database, mutation):
    with sqlite3.connect(database) as db:
        db.execute(mutation)
    before = database.read_bytes()
    category("storage_schema", lambda: storage.verify(database))
    assert database.read_bytes() == before


@pytest.mark.parametrize(
    "mutation,trigger",
    [
        ("DELETE FROM wl_journal_signals WHERE rule='price'", "wl_journal_signal_no_delete"),
        (
            "UPDATE wl_journal_signals SET body_json='{}' WHERE rule='price'",
            "wl_journal_signal_no_update",
        ),
        ("UPDATE wl_journal_sequences SET head_ordinal=1", "wl_journal_sequence_immutable"),
        (
            "UPDATE wl_journal_sequences SET head_eval_id=(SELECT evaluation_id "
            "FROM wl_journal_evaluations WHERE ordinal=1)",
            "wl_journal_sequence_immutable",
        ),
        (
            "UPDATE wl_journal_evaluations SET ordinal=4 WHERE ordinal=2",
            "wl_journal_evaluation_no_update",
        ),
        (
            "UPDATE wl_journal_evaluations SET prior_eval_id=NULL WHERE ordinal=2",
            "wl_journal_evaluation_no_update",
        ),
        (
            "UPDATE wl_journal_evaluations SET snapshot_json='{' WHERE ordinal=2",
            "wl_journal_evaluation_no_update",
        ),
        (
            "UPDATE wl_journal_evaluations SET result_json='{}' WHERE ordinal=2",
            "wl_journal_evaluation_no_update",
        ),
        (
            "UPDATE wl_journal_evaluations SET persisted_at='bad' WHERE ordinal=2",
            "wl_journal_evaluation_no_update",
        ),
        (
            "UPDATE wl_journal_sequences SET entry_digest=printf('%064d',0)",
            "wl_journal_sequence_immutable",
        ),
    ],
)
def test_deep_verify_rejects_full_history_corruption(populated, mutation, trigger):
    path = populated[0]
    privileged(path, trigger, mutation)
    before = path.read_bytes()
    category("storage_corrupt", lambda: storage.verify(path))
    category("storage_corrupt", lambda: storage.get(path, populated[4]["evaluation_id"]))
    assert path.read_bytes() == before


def test_rehashed_evaluation_input_does_not_authorize_forged_result(populated):
    path, first, _, one, _ = populated
    saved = storage.get(path, one["evaluation_id"])["evaluation"]
    forged = copy.deepcopy(saved["evaluation_result"])
    forged["result"] = "MATCH"
    forged["rules"][0]["result"] = "MATCH"
    privileged(
        path,
        "wl_journal_evaluation_no_update",
        "UPDATE wl_journal_evaluations SET result_json=? WHERE evaluation_id=?",
        (identity.canonical(forged), one["evaluation_id"]),
    )
    assert identity.evaluation_id(first) == one["evaluation_id"]
    category("storage_corrupt", lambda: storage.verify(path))


def test_all_immutable_rows_enforce_sql_triggers(populated):
    with sqlite3.connect(populated[0]) as db:
        for table in ("metadata", "evaluations", "signals"):
            with pytest.raises(sqlite3.IntegrityError):
                db.execute("DELETE FROM wl_journal_" + table)
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("UPDATE wl_journal_sequences SET head_ordinal=head_ordinal+2")


def test_keyset_pages_bind_all_filters_and_have_exact_gets(populated):
    path, _, _, one, two = populated
    first = storage.list_evaluations(path, limit=1)
    second = storage.list_evaluations(path, limit=1, cursor=first["next_cursor"])
    assert {item["evaluation_id"] for item in first["evaluations"] + second["evaluations"]} == {
        one["evaluation_id"],
        two["evaluation_id"],
    }
    assert second["next_cursor"] is None
    category(
        "invalid_cursor",
        lambda: storage.list_evaluations(
            path, watch_id="wlt1_" + "0" * 64, cursor=first["next_cursor"]
        ),
    )
    signals = storage.signal_list(path, sequence_id=one["sequence_id"], rule="price")["signals"]
    assert len(signals) == 1
    assert storage.signal_get(path, signals[0]["signal_id"])["signal"] == signals[0]
    category("not_found", lambda: storage.get(path, "wje1_" + "0" * 64))
    category("not_found", lambda: storage.signal_get(path, "wsig1_" + "0" * 64))


@pytest.mark.parametrize("limit", [0, -1, 1001, True, "1"])
def test_page_limit_is_strict(database, limit):
    category("invalid_field", lambda: storage.list_evaluations(database, limit=limit))


@pytest.mark.parametrize("cursor", ["!", "a" * 2049, 12, "e30="])
def test_cursor_is_bounded_and_canonical(database, cursor):
    category("invalid_cursor", lambda: storage.signal_list(database, cursor=cursor))


def test_output_page_byte_bound_is_enforced_without_losing_position(populated, monkeypatch):
    path = populated[0]
    one = storage.list_evaluations(path, limit=1)
    size = len(json.dumps(one, ensure_ascii=True, separators=(",", ":")))
    monkeypatch.setattr(storage, "MAX_PAGE_BYTES", size + 10)
    page = storage.list_evaluations(path)
    assert len(page["evaluations"]) == 1
    assert page["next_cursor"] is not None
    assert len(storage.list_evaluations(path, cursor=page["next_cursor"])["evaluations"]) == 1
    monkeypatch.setattr(storage, "MAX_PAGE_BYTES", 1)
    category("input_limit", lambda: storage.list_evaluations(path))


def test_backup_restore_verify_before_exposure_and_refuse_collisions(populated, tmp_path):
    path = populated[0]
    backup, restored = tmp_path / "backup.db", tmp_path / "restored.db"
    before = path.read_bytes()
    assert storage.backup(path, backup)["counts"] == storage.verify(path)["counts"]
    assert storage.restore(backup, restored)["counts"] == storage.verify(path)["counts"]
    assert storage.list_evaluations(restored) == storage.list_evaluations(path)
    assert path.read_bytes() == before
    category("unsafe_destination", lambda: storage.restore(backup, restored))
    collision = tmp_path / "collision.db"
    sidecar = Path(str(collision) + "-journal")
    sidecar.write_bytes(b"other process evidence")
    category("unsafe_destination", lambda: storage.backup(path, collision))
    assert sidecar.read_bytes() == b"other process evidence"
    assert not collision.exists()


def test_failed_copy_cleans_only_reserved_inode_and_preserves_sidecars(
    populated, tmp_path, monkeypatch
):
    path = populated[0]
    destination = tmp_path / "failed.db"

    def fail(*args):
        raise OSError("synthetic failure before publication")

    monkeypatch.setattr(storage, "_publish", fail)
    category("storage_io", lambda: storage.backup(path, destination))
    assert not destination.exists()
    assert not list(tmp_path.glob(".cmt-watchlist-journal-*.tmp"))
    own = tmp_path / "own.db"
    reserved = storage.paths._reserve(own)
    sidecar = Path(str(own) + "-journal")
    sidecar.write_bytes(b"recovery evidence")
    storage._cleanup_reserved(own, reserved)
    assert own.exists() and sidecar.exists()
    other = tmp_path / "other.db"
    other.write_bytes(b"other inode")
    storage._cleanup_reserved(other, reserved)
    assert other.read_bytes() == b"other inode"


def test_hardlink_and_sidecar_aliases_fail_safely(database, tmp_path):
    alias = tmp_path / "alias.db"
    os.link(database, alias)
    category("unsafe_destination", lambda: storage.verify(database))
    alias.unlink()
    sidecar = Path(str(database) + "-wal")
    other = tmp_path / "other"
    other.write_bytes(b"other evidence")
    os.link(other, sidecar)
    category("unsafe_destination", lambda: storage.verify(database))
    assert other.read_bytes() == b"other evidence"


def test_finite_lock_and_whole_history_deadline_fail(database, monkeypatch):
    with sqlite3.connect(database, autocommit=True) as db:
        db.execute("BEGIN EXCLUSIVE")
        category("storage_locked", lambda: storage.verify(database, timeout=0.04))
        db.execute("ROLLBACK")
    original = storage._load_evaluation

    def exhausted(db, budget, key):
        budget.deadline = 0
        return original(db, budget, key)

    monkeypatch.setattr(storage, "_load_evaluation", exhausted)
    category("storage_timeout", lambda: storage.verify(database, timeout=0.000000001))


WORKER = r"""
import json, sys, time
from pathlib import Path
from card_market_tracker.watchlist_journal import storage
from card_market_tracker.watchlist_journal.errors import JournalError
database, payload, ready, gate = map(Path, sys.argv[1:])
value = json.loads(payload.read_text())
ready.write_text("ready")
deadline = time.monotonic() + 10
while not gate.exists():
    if time.monotonic() > deadline:
        raise RuntimeError("barrier timeout")
    time.sleep(.005)
try:
    print(json.dumps(storage._record_validated(database, value, timeout=5)))
except JournalError as error:
    print(json.dumps({"error":error.category}))
"""


def race(path, values, tmp_path):
    gate = tmp_path / "gate"
    processes = []
    ready_paths = []
    for number, value in enumerate(values):
        payload, ready = tmp_path / f"input-{number}.json", tmp_path / f"ready-{number}"
        payload.write_text(json.dumps(value))
        ready_paths.append(ready)
        processes.append(
            subprocess.Popen(
                [sys.executable, "-c", WORKER, str(path), str(payload), str(ready), str(gate)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        )
    try:
        deadline = time.monotonic() + 10
        while not all(ready.exists() for ready in ready_paths):
            assert time.monotonic() < deadline
            time.sleep(0.005)
        gate.write_text("go")
        results = []
        for process in processes:
            stdout, stderr = process.communicate(timeout=10)
            assert process.returncode == 0, stderr
            results.append(json.loads(stdout))
        return results
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.wait()


def test_real_process_identical_race_is_one_record_one_replay(database, snapshots, tmp_path):
    results = race(database, [snapshots[0], snapshots[0]], tmp_path)
    assert sorted(result["result"] for result in results) == ["recorded", "replayed"]
    assert results[0]["persisted_at"] == results[1]["persisted_at"]
    assert storage.verify(database)["counts"]["evaluations"] == 1


def test_real_process_competing_successors_commit_at_most_one(database, snapshots, tmp_path):
    first, second = snapshots
    storage._record_validated(database, first)
    changed = copy.deepcopy(second)
    changed["current"]["sample_id"] = "synthetic-competing"
    results = race(database, [second, changed], tmp_path)
    assert sum(result.get("result") == "recorded" for result in results) == 1
    assert sum("error" in result for result in results) == 1
    assert storage.verify(database)["counts"] == {"sequences": 1, "evaluations": 2, "signals": 2}


def test_same_process_threads_share_atomic_sqlite_head_guard(database, snapshots):
    barrier = Barrier(2)

    def record():
        barrier.wait(timeout=5)
        return storage._record_validated(database, snapshots[0], timeout=5)

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(record) for _ in range(2)]
        results = [future.result(timeout=10) for future in futures]
    assert sorted(result["result"] for result in results) == ["recorded", "replayed"]
    assert storage.verify(database)["counts"]["evaluations"] == 1


def test_process_exit_inside_signal_append_rolls_back_and_restarts(database, snapshots, tmp_path):
    first, second = snapshots
    storage._record_validated(database, first)
    payload = tmp_path / "crash.json"
    payload.write_text(json.dumps(second))
    script = r"""
import json, os, sys
from pathlib import Path
from card_market_tracker.watchlist_journal import storage
original = storage._execute
def interrupted(db,budget,sql,values=()):
    result = original(db,budget,sql,values)
    if sql.startswith("INSERT INTO wl_journal_signals"):
        os._exit(19)
    return result
storage._execute = interrupted
storage._record_validated(Path(sys.argv[1]),json.loads(Path(sys.argv[2]).read_text()))
"""
    process = subprocess.run(
        [sys.executable, "-c", script, str(database), str(payload)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert process.returncode == 19, process.stderr
    # A fresh writable open can perform SQLite's standard recovery; no sidecar is removed.
    recorded = storage._record_validated(database, second)
    assert recorded["signals_count"] == 2
    assert storage.verify(database)["counts"] == {"sequences": 1, "evaluations": 2, "signals": 2}


def test_history_timeout_mid_fold_cannot_return_partial_success(populated, monkeypatch):
    original = storage._load_evaluation
    seen = 0

    def exhausted(db, budget, key):
        nonlocal seen
        seen += 1
        if seen == 2:
            budget.deadline = 0
        return original(db, budget, key)

    monkeypatch.setattr(storage, "_load_evaluation", exhausted)
    category("storage_timeout", lambda: storage.verify(populated[0]))
    assert seen == 2


def test_decode_rejects_malformed_or_timed_out_json_with_own_error():
    category("storage_corrupt", lambda: storage._decode("{", storage.Budget()))
    category("storage_corrupt", lambda: storage._decode(None, storage.Budget()))
    budget = storage.Budget()
    budget.deadline = 0
    category("storage_timeout", lambda: storage._decode('{"valid":true}', budget))


def test_inode_swap_is_detected_after_open(database, tmp_path, monkeypatch):
    other = tmp_path / "other.db"
    other.write_bytes(b"other file")
    other_stat = other.stat()
    original = storage.paths._unsafe_stat
    calls = 0

    def changed(path, *, file):
        nonlocal calls
        if path == database:
            calls += 1
            if calls == 2:
                return other_stat
        return original(path, file=file)

    monkeypatch.setattr(storage.paths, "_unsafe_stat", changed)
    category("unsafe_destination", lambda: storage.verify(database))


def test_foreign_database_is_readonly_and_never_repaired(tmp_path, snapshots):
    path = tmp_path / "foreign.db"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE unrelated(value TEXT)")
        db.execute("INSERT INTO unrelated VALUES ('preserve')")
    before = path.read_bytes()
    category("storage_schema", lambda: storage._record_validated(path, snapshots[0]))
    assert path.read_bytes() == before


def test_hostile_oversized_cells_fail_before_materialization(populated):
    privileged(
        populated[0],
        "wl_journal_evaluation_no_update",
        "UPDATE wl_journal_evaluations SET snapshot_json=? WHERE ordinal=2",
        ('"' + "x" * 200000 + '"',),
    )
    category("storage_corrupt", lambda: storage.verify(populated[0]))


def test_failed_restore_never_exposes_corrupt_provisional_copy(populated, tmp_path, monkeypatch):
    original = storage._verify
    calls = 0

    def damaged(db, budget):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise JournalError("storage_corrupt")
        return original(db, budget)

    monkeypatch.setattr(storage, "_verify", damaged)
    destination = tmp_path / "unexposed.db"
    category("storage_corrupt", lambda: storage.restore(populated[0], destination))
    assert not destination.exists()
    assert not list(tmp_path.glob(".cmt-watchlist-journal-*.tmp"))


@pytest.mark.parametrize("operation", [storage.backup, storage.restore])
def test_post_link_unlink_failure_rolls_back_owned_publication(
    populated, tmp_path, monkeypatch, operation
):
    source = populated[0]
    before = source.read_bytes()
    destination = tmp_path / "failed-publication.db"
    unlink = Path.unlink
    injected = False

    def interrupted(path, *args, **kwargs):
        nonlocal injected
        if not injected and path.name.startswith(".cmt-watchlist-journal-"):
            assert destination.exists() and path.stat().st_nlink == 2
            injected = True
            raise OSError("synthetic post-link unlink failure")
        return unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", interrupted)
    category("storage_io", lambda: operation(source, destination, timeout=5))
    assert injected
    assert source.read_bytes() == before
    assert not destination.exists()
    assert not list(tmp_path.glob(".cmt-watchlist-journal-*.tmp"))
    assert storage.verify(source, timeout=5)["counts"] == {
        "sequences": 1,
        "evaluations": 2,
        "signals": 2,
    }
    assert operation(source, destination, timeout=5)["result"] == "ok"
    assert storage.verify(destination, timeout=5) == storage.verify(source, timeout=5)


@pytest.mark.parametrize("stage", [1, 2, 3])
def test_copy_deadline_at_each_fold_keeps_source_and_no_destination(
    populated, tmp_path, monkeypatch, stage
):
    source = populated[0]
    before = source.read_bytes()
    destination = tmp_path / "expired.db"
    verify = storage._verify
    calls = 0

    def expired(db, budget):
        nonlocal calls
        calls += 1
        if calls == stage:
            budget.deadline = 0
        return verify(db, budget)

    with monkeypatch.context() as scoped:
        scoped.setattr(storage, "_verify", expired)
        category("storage_timeout", lambda: storage.backup(source, destination, timeout=5))
    assert calls == stage
    assert source.read_bytes() == before
    assert not destination.exists()
    assert not list(tmp_path.glob(".cmt-watchlist-journal-*.tmp"))
    assert storage.verify(source, timeout=5)["result"] == "ok"


@pytest.mark.parametrize("operation", [storage.backup, storage.restore])
def test_copy_recomputes_every_row_once_in_each_independent_fold(
    populated, tmp_path, monkeypatch, operation
):
    source = populated[0]
    before = source.read_bytes()
    verify, evaluate = storage._verify, identity.evaluation.evaluate
    calls = 0
    per_fold = []
    connections = []

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return evaluate(*args, **kwargs)

    def measured(db, budget):
        start = calls
        connections.append(db)
        counts = verify(db, budget)
        per_fold.append(calls - start)
        assert counts == {"sequences": 1, "evaluations": 2, "signals": 2}
        return counts

    destination = tmp_path / "independent.db"
    with monkeypatch.context() as scoped:
        scoped.setattr(identity.evaluation, "evaluate", counted)
        scoped.setattr(storage, "_verify", measured)
        assert operation(source, destination, timeout=5)["result"] == "ok"
    assert per_fold == [2, 2, 2]
    assert len({id(db) for db in connections}) == 3
    assert source.read_bytes() == before
    assert storage.verify(destination, timeout=5) == storage.verify(source, timeout=5)


def test_post_link_rollback_preserves_replacement_destination(populated, tmp_path, monkeypatch):
    destination = tmp_path / "substituted.db"
    unlink = Path.unlink
    injected = False

    def replaced(path, *args, **kwargs):
        nonlocal injected
        if not injected and path.name.startswith(".cmt-watchlist-journal-"):
            injected = True
            unlink(destination)
            destination.write_bytes(b"foreign replacement must survive")
            raise OSError("synthetic replacement during publication")
        return unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", replaced)
    category("storage_io", lambda: storage.backup(populated[0], destination, timeout=5))
    assert destination.read_bytes() == b"foreign replacement must survive"
    assert not list(tmp_path.glob(".cmt-watchlist-journal-*.tmp"))


@pytest.mark.parametrize("sidecar_owner", ["destination", "provisional"])
def test_post_link_rollback_preserves_recovery_sidecars(
    populated, tmp_path, monkeypatch, sidecar_owner
):
    destination = tmp_path / "sidecar.db"
    unlink = Path.unlink
    sidecar = None

    def interrupted(path, *args, **kwargs):
        nonlocal sidecar
        if path.name.startswith(".cmt-watchlist-journal-") and destination.exists():
            owner = destination if sidecar_owner == "destination" else path
            sidecar = Path(str(owner) + "-journal")
            sidecar.write_bytes(b"foreign recovery evidence")
            raise OSError("synthetic recovery sidecar during publication")
        return unlink(path, *args, **kwargs)

    with monkeypatch.context() as scoped:
        scoped.setattr(Path, "unlink", interrupted)
        category("storage_io", lambda: storage.restore(populated[0], destination, timeout=5))
    assert sidecar is not None and sidecar.read_bytes() == b"foreign recovery evidence"
    assert destination.exists()
    assert len(list(tmp_path.glob(".cmt-watchlist-journal-*.tmp"))) == 1
    assert storage.verify(populated[0], timeout=5)["result"] == "ok"
