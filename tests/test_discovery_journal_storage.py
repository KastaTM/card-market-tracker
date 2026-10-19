"""Journal ownership, hostile SQL rows, transaction failures and consistent copies."""

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

from card_market_tracker.discovery import journal_application as application
from card_market_tracker.discovery import journal_schema as schema
from card_market_tracker.discovery import journal_storage as storage
from card_market_tracker.discovery.journal_errors import JournalError


def failure(category, call):
    with pytest.raises(JournalError) as caught:
        call()
    assert caught.value.category == category
    assert str(caught.value) == category
    return caught.value


@pytest.fixture
def journal(tmp_path):
    captures, path = tmp_path / "captures.db", tmp_path / "journal.db"
    first, _ = seed(captures, (), capture=OLD)
    middle, _ = seed(captures, (), capture=MIDDLE)
    current, _ = seed(captures, ("new-a", "new-b"))
    req = request(current.batch_id, (first.batch_id,))
    request_path = tmp_path / "request.json"
    request_path.write_text(json.dumps(req.to_dict()), encoding="utf-8")
    storage.initialize(path)
    outcome = application.record(captures, path, request_path)
    return captures, path, request_path, outcome, current, first, middle


def receipt(request_value, result_value):
    # Deliberate private test seam: all normal fixture admission above used captures.
    left, right = storage.canonical_json(request_value), storage.canonical_json(result_value)
    issued = application._Receipt(left, right)
    object.__setattr__(
        issued, "_authority", (application._AUTHORITY, application._seal(left, right))
    )
    return issued


def test_initialize_exact_owner_inventory_no_implicit_or_foreign_creation(tmp_path):
    path = tmp_path / "journal.db"
    failure("storage_missing", lambda: storage.verify(path))
    failure("storage_missing", lambda: storage.list_comparisons(path))
    assert not path.exists()
    assert storage.initialize(path)["schema_version"] == 1
    with closing(sqlite3.connect(path)) as db:
        objects = tuple(
            tuple(row)
            for row in db.execute(
                "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
            )
        )
        assert objects == schema.expected_inventory()
        assert db.execute("PRAGMA application_id").fetchone()[0] == 0x434D544A
        assert db.execute("PRAGMA user_version").fetchone()[0] == 1
        assert db.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
        assert len([row for row in objects if row[0] == "table"]) == 3
    before = path.read_bytes()
    failure("unsafe_destination", lambda: storage.initialize(path))
    assert path.read_bytes() == before
    foreign = tmp_path / "foreign.db"
    foreign.write_bytes(b"unrelated owner")
    before = foreign.read_bytes()
    failure("unsafe_destination", lambda: storage.initialize(foreign))
    failure("storage_corrupt", lambda: storage.verify(foreign))
    assert foreign.read_bytes() == before
    assert storage.verify(path)["counts"] == {"comparisons": 0, "occurrences": 0}


def test_replay_digest_readonly_and_backup_restore(journal, tmp_path):
    captures, path, request_path, first, *_ = journal
    cid = first["comparison_id"]
    before_captures, before_journal = captures.read_bytes(), path.read_bytes()
    replay = application.record(captures, path, request_path)
    assert replay == {**first, "result": "replay"}
    retained = storage.get(path, cid)
    independently_encoded = json.dumps(
        {"journal_version": 1, "request": retained["request"], "result": retained["comparison"]},
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    assert (
        retained["content_sha256"]
        == hashlib.sha256(independently_encoded.encode("ascii")).hexdigest()
    )
    assert storage.verify(path)["counts"] == {"comparisons": 1, "occurrences": 2}
    assert path.read_bytes() == before_journal
    assert captures.read_bytes() == before_captures
    copy, restored = tmp_path / "copy.db", tmp_path / "restored.db"
    assert storage.backup(path, copy)["counts"]["occurrences"] == 2
    assert storage.restore(copy, restored)["counts"]["comparisons"] == 1
    assert storage.get(restored, cid) == retained
    assert application.recompute(captures, restored, cid)["result"] == "ok"
    failure("unsafe_destination", lambda: storage.backup(path, copy))
    failure("unsafe_destination", lambda: storage.restore(copy, path))


def test_same_event_in_distinct_windows_retains_full_evidence(journal, tmp_path):
    captures, path, _, initial, current, _, middle = journal
    second_request = tmp_path / "second.json"
    second_request.write_text(
        json.dumps(request(current.batch_id, (middle.batch_id,)).to_dict()), encoding="utf-8"
    )
    second = application.record(captures, path, second_request)
    first_payload = storage.get(path, initial["comparison_id"])["comparison"]
    second_payload = storage.get(path, second["comparison_id"])["comparison"]
    assert initial["comparison_id"] != second["comparison_id"]
    for first_event, second_event in zip(
        first_payload["events"], second_payload["events"], strict=True
    ):
        assert first_event["event_id"] == second_event["event_id"]
        assert first_event["evidence"] != second_event["evidence"]
        result = storage.event_occurrences(path, first_event["event_id"], limit=1)
        assert len(result["items"]) == 1 and result["next_cursor"]
        following = storage.event_occurrences(
            path, first_event["event_id"], cursor=result["next_cursor"]
        )
        assert following["next_cursor"] is None
        assert {result["items"][0]["comparison_id"], following["items"][0]["comparison_id"]} == {
            initial["comparison_id"],
            second["comparison_id"],
        }
    assert storage.verify(path)["counts"] == {"comparisons": 2, "occurrences": 4}


def test_semantic_collision_is_explicit_zero_mutation(journal):
    _, path, _, outcome, *_ = journal
    retained = storage.get(path, outcome["comparison_id"])
    changed = deepcopy(retained["comparison"])
    changed["current"]["acquisition"]["acquired_at"] = "2026-01-02T23:59:59.000000Z"
    for event in changed["events"]:
        event["evidence"]["current"] = deepcopy(changed["current"])
    issued = receipt(retained["request"], changed)
    before = path.read_bytes()
    error = failure("conflict", lambda: storage._record_verified(path, issued, storage.Budget()))
    assert error.exit_code == 2
    assert path.read_bytes() == before
    assert storage.get(path, outcome["comparison_id"]) == retained


@pytest.mark.parametrize("fail_insert", ["comparison", "first_event", "second_event", "commit"])
def test_atomic_rollback_disables_expired_handlers(journal, tmp_path, monkeypatch, fail_insert):
    _, original, _, outcome, *_ = journal
    retained = storage.get(original, outcome["comparison_id"])
    target = tmp_path / "empty.db"
    storage.initialize(target)
    previous = storage._execute
    events = 0

    def injected(db, budget, sql, values=()):
        nonlocal events
        if sql.startswith("INSERT INTO event_occurrences"):
            events += 1
        if (
            (fail_insert == "comparison" and sql.startswith("INSERT INTO comparisons"))
            or (fail_insert == "first_event" and events == 1)
            or (fail_insert == "second_event" and events == 2)
            or (fail_insert == "commit" and sql == "COMMIT")
        ):
            # Simulate an interruption with VM callbacks preventing normal SQL.
            db.set_progress_handler(lambda: 1, 1)
            raise JournalError("storage_timeout")
        return previous(db, budget, sql, values)

    monkeypatch.setattr(storage, "_execute", injected)
    failure(
        "storage_timeout",
        lambda: storage._record_verified(
            target, receipt(retained["request"], retained["comparison"]), storage.Budget()
        ),
    )
    monkeypatch.setattr(storage, "_execute", previous)
    assert storage.verify(target)["counts"] == {"comparisons": 0, "occurrences": 0}


@pytest.mark.parametrize(
    "sql,values",
    [
        ("UPDATE comparisons SET content_sha256=?", ("0" * 64,)),
        ("UPDATE comparisons SET first_recorded_at=?", ("2026-99-99T00:00:00.000000Z",)),
        ("UPDATE comparisons SET result_json=?", ('{"events":[],"version":3}',)),
        ("UPDATE comparisons SET request_json=?", ('{"version":3,"version":3}',)),
        ("UPDATE comparisons SET request_json=?", ('{"version":NaN}',)),
        ("UPDATE event_occurrences SET ordinal=ordinal+10", ()),
        ("UPDATE event_occurrences SET event_json=?", ("{}",)),
        ("DELETE FROM event_occurrences WHERE ordinal=0", ()),
        ("UPDATE event_occurrences SET comparison_id=?", ("cmp3:" + "a" * 64,)),
    ],
)
def test_verify_rejects_digest_json_clock_ordinal_orphans(journal, sql, values):
    _, path, _, _, *_ = journal
    with closing(sqlite3.connect(path, autocommit=True)) as db:
        db.execute("PRAGMA ignore_check_constraints=ON")
        db.execute(sql, values)
    before = path.read_bytes()
    failure("storage_corrupt", lambda: storage.verify(path))
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "sql,values,category",
    [
        ("PRAGMA user_version=2", (), "storage_schema"),
        ("PRAGMA application_id=1129133105", (), "storage_schema"),
        ("UPDATE journal_metadata SET owner=?", ("x" * 200000,), "storage_schema"),
        ("CREATE TABLE extra(payload TEXT)", (), "storage_schema"),
        ("UPDATE comparisons SET comparison_id=?", ("c" * 200000,), "storage_corrupt"),
        ("UPDATE comparisons SET content_sha256=?", ("x" * 200000,), "storage_corrupt"),
        ("UPDATE comparisons SET first_recorded_at=?", ("x" * 200000,), "storage_corrupt"),
        (
            "UPDATE event_occurrences SET event_id=? WHERE ordinal=0",
            ("x" * 200000,),
            "storage_corrupt",
        ),
        ("UPDATE comparisons SET request_json=?", ("x" * (1024 * 1024 + 1),), "storage_corrupt"),
        (
            "UPDATE comparisons SET result_json=?",
            ("x" * (16 * 1024 * 1024 + 1),),
            "storage_corrupt",
        ),
        (
            "UPDATE event_occurrences SET event_json=? WHERE ordinal=0",
            ("x" * (16 * 1024 * 1024 + 1),),
            "storage_corrupt",
        ),
    ],
)
def test_hostile_scalars_and_payloads_are_rejected_before_decode(
    journal, monkeypatch, sql, values, category
):
    _, path, _, outcome, *_ = journal
    with closing(sqlite3.connect(path, autocommit=True)) as db:
        db.execute("PRAGMA ignore_check_constraints=ON")
        db.execute(sql, values)
    failure(category, lambda: storage.verify(path, timeout=5))
    # Direct lookup also rejects malformed scalar/payload columns before parsing.
    if "UPDATE comparisons SET" in sql and "comparison_id" not in sql:
        from card_market_tracker.discovery import journal_validation

        monkeypatch.setattr(
            journal_validation,
            "decode_json",
            lambda *a, **kw: pytest.fail("decoded oversized SQL cell"),
        )
        failure("storage_corrupt", lambda: storage.get(path, outcome["comparison_id"], timeout=5))


def test_page_over_one_thousand_rows_without_omissions(journal):
    _, path, _, outcome, *_ = journal
    retained = storage.get(path, outcome["comparison_id"])
    # Populate explicit storage fixtures without repeating expensive capture imports.
    with closing(sqlite3.connect(path, autocommit=True)) as db:
        db.execute("BEGIN")
        for index in range(1005):
            cid = "cmp3:" + f"{index:064x}"
            db.execute(
                "INSERT INTO comparisons VALUES(?,?,?,?,?)",
                (
                    cid,
                    storage.canonical_json(retained["request"]),
                    "{}",
                    "a" * 64,
                    retained["first_recorded_at"],
                ),
            )
            db.execute(
                "INSERT INTO event_occurrences VALUES(?,?,?,?)",
                (cid, "evt3:" + "f" * 64, 0, "{}"),
            )
        db.execute("COMMIT")
    items = storage.list_comparisons(path, limit=1000)
    after = storage.list_comparisons(path, cursor=items["next_cursor"], limit=1000)
    ids = [row["comparison_id"] for row in [*items["items"], *after["items"]]]
    assert len(ids) == len(set(ids)) == 1006 and ids == sorted(ids)
    assert after["next_cursor"] is None
    events = storage.event_occurrences(path, "evt3:" + "f" * 64, limit=1000)
    final = storage.event_occurrences(path, "evt3:" + "f" * 64, cursor=events["next_cursor"])
    assert len(events["items"]) == 1000 and len(final["items"]) == 5
    assert final["next_cursor"] is None


@pytest.mark.parametrize("limit", [True, False, 0, 1001, 1.0, "1"])
def test_page_invalid_limits(journal, limit):
    failure("invalid_field", lambda: storage.list_comparisons(journal[1], limit=limit))


@pytest.mark.parametrize(
    "token", ["", "cmp3:" + "A" * 64, "evt3:" + "a" * 64, "cmp3:" + "0" * 63, True]
)
def test_invalid_cursors_and_ids(journal, token):
    failure("invalid_field", lambda: storage.list_comparisons(journal[1], cursor=token))
    failure("invalid_field", lambda: storage.get(journal[1], token))


@pytest.mark.parametrize("timeout", [True, False, 0, -1, 5.01, float("nan"), float("inf"), "2"])
def test_finite_timeout_and_expiry(journal, timeout):
    failure("invalid_field", lambda: storage.verify(journal[1], timeout=timeout))


def test_deadline_and_bounded_sql_lock(journal):
    _, path, _, outcome, *_ = journal
    budget = storage.Budget()
    budget.deadline = 0
    failure("storage_timeout", budget.remaining)
    with closing(sqlite3.connect(path, autocommit=True)) as db:
        db.execute("BEGIN EXCLUSIVE")
        error = failure(
            "storage_locked", lambda: storage.get(path, outcome["comparison_id"], timeout=0.05)
        )
        assert error.exit_code == 1
        db.execute("ROLLBACK")


def test_samefile_capture_owner_hardlinks_and_unsafe_paths(journal, tmp_path):
    captures, path, _, _, *_ = journal
    before = captures.read_bytes()
    failure("unsafe_destination", lambda: storage.reject_same_file(path, path))
    failure("storage_schema", lambda: storage.verify(captures))
    failure("unsafe_destination", lambda: storage.backup(path, path))
    failure("unsafe_destination", lambda: storage.initialize(tmp_path / ".." / "unsafe.db"))
    link = tmp_path / "hardlink.db"
    os.link(path, link)
    try:
        failure("unsafe_destination", lambda: storage.verify(link))
        failure("unsafe_destination", lambda: storage.verify(path))
    finally:
        link.unlink()
    if os.name != "nt":
        symlink = tmp_path / "link.db"
        symlink.symlink_to(path)
        failure("unsafe_destination", lambda: storage.verify(symlink))
        destination = tmp_path / "destination.db"
        destination.symlink_to(captures)
        failure("unsafe_destination", lambda: storage.backup(path, destination))
    assert captures.read_bytes() == before


def test_backup_failure_cleans_only_reserved_target(journal, tmp_path, monkeypatch):
    target = tmp_path / "incomplete.db"
    previous = storage._verify
    calls = 0

    def injected(db, budget):
        nonlocal calls
        calls += 1
        if calls == 3:
            raise JournalError("storage_corrupt")
        return previous(db, budget)

    monkeypatch.setattr(storage, "_verify", injected)
    failure("storage_corrupt", lambda: storage.backup(journal[1], target))
    assert not target.exists()
    assert not list(tmp_path.glob("incomplete.db-*"))


def test_two_process_writers_insert_and_replay(journal, tmp_path):
    captures, _, request_path, _, *_ = journal
    target = tmp_path / "concurrent.db"
    storage.initialize(target)
    script = (
        "import json,sys;from pathlib import Path;"
        "from card_market_tracker.discovery.journal_application import record;"
        "print(json.dumps(record(*(Path(p) for p in sys.argv[1:]),timeout=5)))"
    )
    commands = [sys.executable, "-c", script, str(captures), str(target), str(request_path)]
    processes = [
        subprocess.Popen(commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for _ in range(2)
    ]
    results = [process.communicate(timeout=15) for process in processes]
    assert [process.returncode for process in processes] == [0, 0], results
    assert sorted(json.loads(stdout)["result"] for stdout, _ in results) == ["inserted", "replay"]
    assert storage.verify(target)["counts"] == {"comparisons": 1, "occurrences": 2}


def test_killed_writer_before_commit_recovers_empty_then_records(journal, tmp_path):
    captures, _, request_path, _, *_ = journal
    target, ready = tmp_path / "interrupted.db", tmp_path / "before-commit"
    storage.initialize(target)
    script = """
import sys,time
from pathlib import Path
from card_market_tracker.discovery import journal_storage as storage
from card_market_tracker.discovery.journal_application import record
original=storage._execute
def interrupted(db,budget,sql,values=()):
    if sql=='COMMIT':
        assert db.execute('SELECT COUNT(*) FROM comparisons').fetchone()[0]==1
        assert db.execute('SELECT COUNT(*) FROM event_occurrences').fetchone()[0]==2
        Path(sys.argv[4]).write_text('ready',encoding='ascii')
        while True:
            time.sleep(0.05)
    return original(db,budget,sql,values)
storage._execute=interrupted
record(*(Path(p) for p in sys.argv[1:4]),timeout=5)
"""
    process = subprocess.Popen(
        [sys.executable, "-c", script, str(captures), str(target), str(request_path), str(ready)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        deadline = time.monotonic() + 10
        while not ready.exists() and process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.01)
        assert ready.exists(), process.communicate(timeout=1)
        process.kill()
        process.communicate(timeout=5)
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)
    assert storage.verify(target)["counts"] == {"comparisons": 0, "occurrences": 0}
    assert application.record(captures, target, request_path)["result"] == "inserted"
    assert storage.verify(target)["counts"] == {"comparisons": 1, "occurrences": 2}


def test_canonical_byte_limit_deadline_and_fixed_categories():
    assert storage.bounded_canonical_json({"x": "é"}, 14, storage.Budget()) == '{"x":"\\u00e9"}'
    error = failure(
        "input_limit", lambda: storage.bounded_canonical_json({"x": "é"}, 13, storage.Budget())
    )
    assert error.exit_code == 2
    expired = storage.Budget()
    expired.deadline = 0
    failure("storage_timeout", lambda: storage.bounded_canonical_json({}, 2, expired))
    failure("storage_corrupt", lambda: storage.canonical_json(float("nan")))
    failure("storage_corrupt", lambda: storage.content_digest({}, object()))
    assert JournalError("unknown").category == "invalid_field"


def test_summary_byte_limit_fails_instead_of_truncating(journal, monkeypatch):
    monkeypatch.setattr(storage, "MAX_PAGE_BYTES", 1)
    failure("input_limit", lambda: storage.list_comparisons(journal[1]))


def test_existing_sidecar_foreign_copy_and_corrupt_schema_inventory(journal, tmp_path):
    captures, path, *_ = journal
    new = tmp_path / "new.db"
    sidecar = tmp_path / "new.db-wal"
    sidecar.write_bytes(b"foreign sidecar")
    failure("unsafe_destination", lambda: storage.initialize(new))
    assert not new.exists() and sidecar.read_bytes() == b"foreign sidecar"
    destination = tmp_path / "foreign-copy.db"
    failure("storage_schema", lambda: storage.backup(captures, destination))
    assert not destination.exists()
    with closing(sqlite3.connect(path, autocommit=True)) as db:
        # Large attacker-created identifier and SQL are guarded as scalars too.
        db.execute('CREATE TABLE "' + "x" * 100000 + '" (payload TEXT)')
    # SQL_LENGTH also bounds SQLite's initial schema parse before our inventory
    # reader runs, so an oversized schema is classified as corrupt by SQLite.
    failure("storage_corrupt", lambda: storage.verify(path, timeout=5))


def test_failed_initializer_cleans_exclusively_owned_reservation(tmp_path, monkeypatch):
    path = tmp_path / "failed-init.db"
    original = storage._execute

    def interrupted(db, budget, sql, values=()):
        if sql.startswith("CREATE TABLE comparisons"):
            raise JournalError("storage_timeout")
        return original(db, budget, sql, values)

    monkeypatch.setattr(storage, "_execute", interrupted)
    failure("storage_timeout", lambda: storage.initialize(path))
    assert not path.exists() and not list(tmp_path.glob("failed-init.db-*"))
