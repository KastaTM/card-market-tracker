"""Outbox owner, hostile cells, atomic rollback and real process recovery probes."""

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
from contextlib import closing
from copy import deepcopy

import pytest
from test_multi_revision_discovery import request
from test_scoped_discovery_core import MIDDLE, OLD, seed

from card_market_tracker.alerts import application, policy, schema, storage
from card_market_tracker.alerts.errors import OutboxError
from card_market_tracker.discovery import journal_application, journal_storage


def failure(category, call):
    with pytest.raises(OutboxError) as caught:
        call()
    assert caught.value.category == category
    assert str(caught.value) == category
    return caught.value


@pytest.fixture
def journal(tmp_path):
    captures, ledger = tmp_path / "captures.db", tmp_path / "journal.db"
    first, _ = seed(captures, (), capture=OLD)
    middle, _ = seed(captures, (), capture=MIDDLE)
    current, _ = seed(captures, ("new-a", "new-b"))
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(request(current.batch_id, (first.batch_id,)).to_dict()))
    journal_storage.initialize(ledger)
    outcome = journal_application.record(captures, ledger, request_path)
    return captures, ledger, request_path, outcome, current, first, middle


@pytest.fixture
def outbox(journal, tmp_path):
    captures, ledger, request_path, outcome, current, first, middle = journal
    path = tmp_path / "outbox.db"
    storage.initialize(path)
    prepared = application.enqueue(captures, ledger, path, outcome["comparison_id"], "local")
    return captures, ledger, path, prepared, current, first, middle


def test_schema_owner_exclusive_init_and_missing(tmp_path):
    path = tmp_path / "outbox.db"
    failure("storage_missing", lambda: storage.verify(path))
    failure("storage_missing", lambda: storage.list_alerts(path))
    assert not path.exists()
    assert storage.initialize(path)["schema_version"] == 1
    with closing(sqlite3.connect(path)) as db:
        assert db.execute("PRAGMA application_id").fetchone()[0] == 0x434D5441
        assert db.execute("PRAGMA user_version").fetchone()[0] == 1
        assert db.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
        assert (
            tuple(
                tuple(row)
                for row in db.execute(
                    "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
                )
            )
            == schema.expected_inventory()
        )
    before = path.read_bytes()
    failure("unsafe_destination", lambda: storage.initialize(path))
    assert path.read_bytes() == before
    assert storage.verify(path)["counts"] == {"alerts": 0, "associations": 0}


def test_two_windows_destinations_replay_preview_and_recovery(outbox, tmp_path):
    captures, ledger, path, initial, current, _, middle = outbox
    before_captures, before_journal, before_outbox = (
        captures.read_bytes(),
        ledger.read_bytes(),
        path.read_bytes(),
    )
    assert initial["alerts_new"] == initial["associations_new"] == initial["events"] == 2
    replay = application.enqueue(captures, ledger, path, initial["comparison_id"], "local")
    assert replay["result"] == "replay" and replay["associations_existing"] == 2
    assert path.read_bytes() == before_outbox
    alerts = storage.list_alerts(path)["items"]
    retained = {item["alert_id"]: storage.get(path, item["alert_id"])["alert"] for item in alerts}
    for aid, alert in retained.items():
        preimage = {
            "identity_version": 1,
            "destination_key": "local",
            "event_id": alert["event_id"],
        }
        digest = hashlib.sha256(
            json.dumps(
                preimage, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode()
        ).hexdigest()
        assert aid == "alt1:" + digest
        assert storage.preview(path, aid)["message_text"] == alert["message_text"]
    assert path.read_bytes() == before_outbox
    second_req = tmp_path / "other-window.json"
    second_req.write_text(json.dumps(request(current.batch_id, (middle.batch_id,)).to_dict()))
    second = journal_application.record(captures, ledger, second_req)
    prepared = application.enqueue(captures, ledger, path, second["comparison_id"], "local")
    assert prepared["alerts_existing"] == prepared["associations_new"] == 2
    assert prepared["alerts_new"] == prepared["associations_existing"] == 0
    for aid in retained:
        assert storage.get(path, aid)["alert"] == retained[aid]
        first_page = storage.evidence_list(path, aid, limit=1)
        assert first_page["next_cursor"]
        following = storage.evidence_list(path, aid, cursor=first_page["next_cursor"])
        assert following["next_cursor"] is None
        cids = {first_page["items"][0]["comparison_id"], following["items"][0]["comparison_id"]}
        assert cids == {initial["comparison_id"], second["comparison_id"]}
        evidence = [storage.evidence_get(path, aid, cid) for cid in sorted(cids)]
        assert evidence[0]["event"]["event_id"] == evidence[1]["event"]["event_id"]
        assert evidence[0]["event"]["evidence"] != evidence[1]["event"]["evidence"]
    another = application.enqueue(captures, ledger, path, initial["comparison_id"], "another")
    assert another["alerts_new"] == another["associations_new"] == 2
    assert storage.verify(path)["counts"] == {"alerts": 4, "associations": 6}
    assert captures.read_bytes() == before_captures
    assert before_journal != ledger.read_bytes()  # only explicit second record changed journal
    copied, restored = tmp_path / "backup.db", tmp_path / "restored.db"
    assert storage.backup(path, copied)["counts"] == {"alerts": 4, "associations": 6}
    assert storage.restore(copied, restored)["counts"] == {"alerts": 4, "associations": 6}
    assert (
        application.enqueue(captures, ledger, restored, initial["comparison_id"], "local")["result"]
        == "replay"
    )
    assert storage.list_alerts(restored) == storage.list_alerts(path)
    failure("unsafe_destination", lambda: storage.backup(path, copied))
    failure("unsafe_destination", lambda: storage.restore(copied, path))


@pytest.mark.parametrize("failure_at", ["alert", "evidence", "commit"])
def test_rollback_after_partial_write_and_expired_handler(
    journal, tmp_path, monkeypatch, failure_at
):
    captures, ledger, _, recorded, *_ = journal
    path = tmp_path / "new.db"
    storage.initialize(path)
    previous = storage._execute

    def injected(db, budget, sql, values=()):
        if (
            (failure_at == "alert" and sql.startswith("INSERT INTO alerts"))
            or (failure_at == "evidence" and sql.startswith("INSERT INTO alert_evidence"))
            or (failure_at == "commit" and sql == "COMMIT")
        ):
            db.set_progress_handler(lambda: 1, 1)
            raise OutboxError("storage_timeout")
        return previous(db, budget, sql, values)

    monkeypatch.setattr(storage, "_execute", injected)
    failure(
        "storage_timeout",
        lambda: application.enqueue(captures, ledger, path, recorded["comparison_id"], "local"),
    )
    monkeypatch.setattr(storage, "_execute", previous)
    assert storage.verify(path)["counts"] == {"alerts": 0, "associations": 0}


def test_valid_intrinsic_collision_rolls_back_new_rows(outbox, monkeypatch):
    _, ledger, path, initial, *_ = outbox
    events = journal_storage.get(ledger, initial["comparison_id"])["comparison"]["events"]
    changed = deepcopy(events[1])
    changed["reference"]["external_id"] = "different-reference"
    rows = [
        policy.prepare_event(events[0], "fresh", initial["comparison_id"]),
        policy.prepare_event(changed, "local", initial["comparison_id"]),
    ]
    retained = journal_storage.get(ledger, initial["comparison_id"])
    monkeypatch.setattr(
        application,
        "_consume_receipt",
        lambda receipt, budget: (initial["comparison_id"], retained["content_sha256"], rows),
    )
    before = path.read_bytes()
    failure("conflict", lambda: storage._enqueue_verified(path, object(), storage.Budget()))
    assert path.read_bytes() == before
    assert storage.verify(path)["counts"] == {"alerts": 2, "associations": 2}


@pytest.mark.parametrize(
    "sql,values,category",
    [
        ("PRAGMA user_version=2", (), "storage_schema"),
        ("PRAGMA application_id=1129133130", (), "storage_schema"),
        ("CREATE TABLE extra(value TEXT)", (), "storage_schema"),
        ("UPDATE outbox_metadata SET owner=?", ("x" * 200000,), "storage_schema"),
        (
            "UPDATE alerts SET alert_id=? WHERE rowid=(SELECT MIN(rowid) FROM alerts)",
            ("x" * 200000,),
            "storage_corrupt",
        ),
        ("UPDATE alerts SET destination_key=?", ("x" * 200000,), "storage_corrupt"),
        (
            "UPDATE alerts SET event_id=? WHERE rowid=(SELECT MIN(rowid) FROM alerts)",
            ("x" * 200000,),
            "storage_corrupt",
        ),
        ("UPDATE alerts SET intent_json=?", ("x" * 65537,), "storage_corrupt"),
        ("UPDATE alerts SET message_text=?", ("x" * 4097,), "storage_corrupt"),
        ("UPDATE alerts SET intent_sha256=?", ("0" * 64,), "storage_corrupt"),
        ("UPDATE alerts SET message_sha256=?", ("0" * 64,), "storage_corrupt"),
        (
            "UPDATE alerts SET first_prepared_at=?",
            ("2026-99-99T00:00:00.000000Z",),
            "storage_corrupt",
        ),
        ("UPDATE alerts SET state='sent'", (), "storage_corrupt"),
        ("UPDATE alerts SET renderer_version=2", (), "storage_corrupt"),
        ("UPDATE alerts SET policy_version='other'", (), "storage_corrupt"),
        ("UPDATE alert_evidence SET comparison_id=?", ("x" * 200000,), "storage_corrupt"),
        (
            "UPDATE alert_evidence SET event_json=?",
            ("x" * (16 * 1024 * 1024 + 1),),
            "storage_corrupt",
        ),
        ("UPDATE alert_evidence SET event_sha256=?", ("0" * 64,), "storage_corrupt"),
        ("UPDATE alert_evidence SET journal_content_sha256=?", ("x" * 200000,), "storage_corrupt"),
        ("DELETE FROM alert_evidence", (), "storage_corrupt"),
        (
            "UPDATE alert_evidence SET alert_id=? "
            "WHERE rowid=(SELECT MIN(rowid) FROM alert_evidence)",
            ("alt1:" + "0" * 64,),
            "storage_corrupt",
        ),
    ],
)
def test_hostile_cells_relationships_and_inventory(outbox, sql, values, category):
    _, _, path, *_ = outbox
    with closing(sqlite3.connect(path, autocommit=True)) as db:
        db.execute("PRAGMA ignore_check_constraints=ON")
        db.execute(sql, values)
    before = path.read_bytes()
    failure(category, lambda: storage.verify(path, timeout=5))
    assert path.read_bytes() == before


def test_oversized_payload_blocked_before_decoder(outbox, monkeypatch):
    _, _, path, *_ = outbox
    aid = storage.list_alerts(path)["items"][0]["alert_id"]
    with closing(sqlite3.connect(path, autocommit=True)) as db:
        db.execute("PRAGMA ignore_check_constraints=ON")
        db.execute("UPDATE alerts SET intent_json=?", ("x" * 65537,))
    monkeypatch.setattr(storage, "_decode", lambda *args: pytest.fail("oversized cell decoded"))
    failure("storage_corrupt", lambda: storage.get(path, aid))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"limit": True},
        {"limit": 0},
        {"limit": 1001},
        {"cursor": "ALT1:" + "a" * 64},
        {"destination_key": "real@example.com"},
    ],
)
def test_strict_page_inputs(outbox, kwargs):
    failure("invalid_field", lambda: storage.list_alerts(outbox[2], **kwargs))


def test_static_and_live_keysets_and_missing_association(outbox):
    captures, ledger, path, outcome, *_ = outbox
    first = storage.list_alerts(path, limit=1)
    assert first["next_cursor"] == first["items"][-1]["alert_id"]
    following = storage.list_alerts(path, cursor=first["next_cursor"])
    assert following["next_cursor"] is None and len(following["items"]) == 1
    application.enqueue(captures, ledger, path, outcome["comparison_id"], "new-destination")
    live = storage.list_alerts(path, cursor=first["next_cursor"])
    assert all(item["alert_id"] > first["next_cursor"] for item in live["items"])
    assert storage.list_alerts(path, destination_key="new-destination")["items"]
    aid = first["items"][0]["alert_id"]
    failure("storage_missing", lambda: storage.evidence_get(path, aid, "cmp3:" + "0" * 64))
    failure("storage_missing", lambda: storage.evidence_list(path, "alt1:" + "0" * 64))
    failure("storage_missing", lambda: storage.preview(path, "alt1:" + "0" * 64))


@pytest.mark.parametrize("timeout", [0, -1, True, float("nan"), float("inf"), 5.1, "2"])
def test_invalid_deadlines(tmp_path, timeout):
    failure("invalid_field", lambda: storage.verify(tmp_path / "none.db", timeout=timeout))


def test_busy_writer_is_bounded_and_no_writes(outbox):
    captures, ledger, path, outcome, *_ = outbox
    before = path.read_bytes()
    with closing(sqlite3.connect(path, autocommit=True)) as blocker:
        blocker.execute("BEGIN IMMEDIATE")
        started = time.monotonic()
        error = failure(
            "storage_locked",
            lambda: application.enqueue(
                captures, ledger, path, outcome["comparison_id"], "other", timeout=1.0
            ),
        )
        assert error.exit_code == 1
        assert time.monotonic() - started < 2
        blocker.execute("ROLLBACK")
    assert path.read_bytes() == before


def test_real_two_process_writers(journal, tmp_path):
    captures, ledger, _, outcome, *_ = journal
    path = tmp_path / "concurrent.db"
    storage.initialize(path)
    code = (
        "import json,sys; from pathlib import Path; "
        "from card_market_tracker.alerts.application import enqueue; "
        "print(json.dumps(enqueue(*map(Path,sys.argv[1:4]),sys.argv[4],'local',timeout=5)))"
    )
    arguments = [
        sys.executable,
        "-c",
        code,
        str(captures),
        str(ledger),
        str(path),
        outcome["comparison_id"],
    ]
    processes = [
        subprocess.Popen(arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for _ in range(2)
    ]
    results = []
    for process in processes:
        stdout, stderr = process.communicate(timeout=15)
        assert process.returncode == 0, stderr
        results.append(json.loads(stdout))
    assert sorted(item["result"] for item in results) == ["inserted", "replay"]
    assert sum(item["alerts_new"] for item in results) == 2
    assert sum(item["associations_new"] for item in results) == 2
    assert storage.verify(path)["counts"] == {"alerts": 2, "associations": 2}


def test_real_process_termination_mid_transaction_recovers(journal, tmp_path):
    captures, ledger, _, outcome, *_ = journal
    path, signal = tmp_path / "interrupted.db", tmp_path / "inserted.signal"
    storage.initialize(path)
    code = """
import sys,time
from pathlib import Path
from card_market_tracker.alerts import storage,application
previous=storage._execute
def injected(db,budget,sql,values=()):
    result=previous(db,budget,sql,values)
    if sql.startswith('INSERT INTO alert_evidence'):
        Path(sys.argv[5]).write_text('uncommitted')
        while True:
            time.sleep(0.01)
    return result
storage._execute=injected
application.enqueue(*map(Path,sys.argv[1:4]),sys.argv[4],'local',timeout=5)
"""
    process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            code,
            str(captures),
            str(ledger),
            str(path),
            outcome["comparison_id"],
            str(signal),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 10
        while not signal.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.01)
        assert signal.exists(), process.communicate(timeout=1)
        process.kill()
        process.communicate(timeout=5)
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)
    assert storage.verify(path)["counts"] == {"alerts": 0, "associations": 0}
    assert (
        application.enqueue(captures, ledger, path, outcome["comparison_id"], "local")["alerts_new"]
        == 2
    )
    assert storage.verify(path)["counts"] == {"alerts": 2, "associations": 2}


def test_unsafe_paths_and_existing_copy_never_damage(outbox, tmp_path):
    _, _, path, *_ = outbox
    foreign = tmp_path / "foreign.db"
    foreign.write_bytes(b"foreign owner")
    before = foreign.read_bytes()
    failure("unsafe_destination", lambda: storage.backup(path, foreign))
    failure("storage_corrupt", lambda: storage.verify(foreign))
    assert foreign.read_bytes() == before
    sidecar_target = tmp_path / "sidecar.db"
    sidecar = tmp_path / "sidecar.db-journal"
    sidecar.write_bytes(b"unrelated sidecar")
    failure("unsafe_destination", lambda: storage.initialize(sidecar_target))
    assert sidecar.read_bytes() == b"unrelated sidecar" and not sidecar_target.exists()
    linked = tmp_path / "hardlink.db"
    os.link(path, linked)
    failure("unsafe_destination", lambda: storage.verify(linked))
    linked.unlink()


def test_deadline_survives_reused_journal_json_boundary():
    budget = storage.Budget()
    budget.deadline = time.monotonic() - 1
    error = failure("storage_timeout", lambda: storage._decode("{}", 65536, budget))
    assert error.exit_code == 1


def test_comparison_digest_collision_fails_before_new_destination_rows(outbox, monkeypatch):
    _, ledger, path, initial, *_ = outbox
    result = journal_storage.get(ledger, initial["comparison_id"])["comparison"]
    rows = [
        policy.prepare_event(event, "another", initial["comparison_id"])
        for event in result["events"]
    ]
    monkeypatch.setattr(
        application,
        "_consume_receipt",
        lambda receipt, budget: (initial["comparison_id"], "0" * 64, rows),
    )
    before = path.read_bytes()
    failure("conflict", lambda: storage._enqueue_verified(path, object(), storage.Budget()))
    assert path.read_bytes() == before


def test_verify_rejects_disagreeing_comparison_digests(outbox):
    path = outbox[2]
    with closing(sqlite3.connect(path, autocommit=True)) as db:
        db.execute(
            "UPDATE alert_evidence SET journal_content_sha256=? "
            "WHERE rowid=(SELECT MIN(rowid) FROM alert_evidence)",
            ("0" * 64,),
        )
    failure("storage_corrupt", lambda: storage.verify(path))


def test_page_output_ceiling_no_partial_success(outbox, monkeypatch):
    aid = storage.list_alerts(outbox[2])["items"][0]["alert_id"]
    monkeypatch.setattr(storage, "MAX_PAGE_BYTES", 100)
    failure("input_limit", lambda: storage.list_alerts(outbox[2]))
    failure("input_limit", lambda: storage.evidence_list(outbox[2], aid))


def test_failed_init_cleans_only_reserved_destination(tmp_path, monkeypatch):
    path = tmp_path / "new.db"
    previous = storage._execute

    def injected(db, budget, sql, values=()):
        if sql.startswith("CREATE TABLE alerts"):
            raise OutboxError("storage_io")
        return previous(db, budget, sql, values)

    monkeypatch.setattr(storage, "_execute", injected)
    failure("storage_io", lambda: storage.initialize(path))
    assert not path.exists()
    assert not (tmp_path / "new.db-journal").exists()


def test_failed_copy_cleans_reserved_destination_and_preserves_source(
    outbox, tmp_path, monkeypatch
):
    path = outbox[2]
    before = path.read_bytes()
    target = tmp_path / "failed-copy.db"
    previous = storage._verify
    calls = 0

    def injected(db, budget):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OutboxError("storage_timeout")
        return previous(db, budget)

    monkeypatch.setattr(storage, "_verify", injected)
    failure("storage_timeout", lambda: storage.backup(path, target))
    assert path.read_bytes() == before and not target.exists()


@pytest.mark.parametrize("tampered", ["event", "message"])
def test_coherent_checksum_cannot_hide_parent_or_renderer_mismatch(outbox, tampered):
    path = outbox[2]
    with closing(sqlite3.connect(path, autocommit=True)) as db:
        aid = db.execute("SELECT alert_id FROM alerts ORDER BY alert_id LIMIT 1").fetchone()[0]
        if tampered == "message":
            replacement = "a coherently hashed but invented message"
            digest = hashlib.sha256(replacement.encode()).hexdigest()
            db.execute(
                "UPDATE alerts SET message_text=?,message_sha256=? WHERE alert_id=?",
                (replacement, digest, aid),
            )
        else:
            replacement = db.execute(
                "SELECT event_json FROM alert_evidence WHERE alert_id!=? LIMIT 1", (aid,)
            ).fetchone()[0]
            digest = hashlib.sha256(replacement.encode()).hexdigest()
            db.execute(
                "UPDATE alert_evidence SET event_json=?,event_sha256=? WHERE alert_id=?",
                (replacement, digest, aid),
            )
    failure("storage_corrupt", lambda: storage.verify(path))


@pytest.mark.parametrize(
    "table,column,category",
    (
        ("alerts", "renderer_version", "storage_corrupt"),
        ("outbox_metadata", "schema_version", "storage_schema"),
    ),
)
def test_hostile_numeric_cells_are_guarded_before_materialization(
    outbox, monkeypatch, table, column, category
):
    path = outbox[2]
    aid = storage.list_alerts(path)["items"][0]["alert_id"]
    # Hostile files can bypass STRICT by temporarily changing their stored DDL.
    with closing(sqlite3.connect(path)) as db:
        original = db.execute("SELECT sql FROM sqlite_master WHERE name=?", (table,)).fetchone()[0]
        replaced = original.replace(column + " INTEGER", column + " TEXT")
        assert replaced != original
        db.execute("PRAGMA writable_schema=ON")
        db.execute("UPDATE sqlite_master SET sql=? WHERE name=?", (replaced, table))
        db.commit()
    with closing(sqlite3.connect(path)) as db:
        db.execute("PRAGMA ignore_check_constraints=ON")
        db.execute(f"UPDATE {table} SET {column}=?", ("x" * (2 * 1024 * 1024),))
        db.commit()
    with closing(sqlite3.connect(path)) as db:
        db.execute("PRAGMA writable_schema=ON")
        db.execute("UPDATE sqlite_master SET sql=? WHERE name=?", (original, table))
        db.commit()
    execute = storage._execute
    loaded_sizes = []

    class ObservedCursor:
        def __init__(self, cursor):
            self.cursor = cursor

        def inspect(self, row):
            if row is not None:
                loaded_sizes.extend(len(value) for value in row if type(value) is str)
            return row

        def fetchone(self):
            return self.inspect(self.cursor.fetchone())

        def __iter__(self):
            for row in self.cursor:
                yield self.inspect(row)

    def observe(*args, **kwargs):
        return ObservedCursor(execute(*args, **kwargs))

    monkeypatch.setattr(storage, "_execute", observe)
    failure(category, lambda: storage.get(path, aid))
    assert max(loaded_sizes, default=0) < 64 * 1024
