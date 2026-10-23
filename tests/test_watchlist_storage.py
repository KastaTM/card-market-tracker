"""DB author evidence: atomic history/replay, hostile storage and local recovery."""

import base64
import copy
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest

from card_market_tracker.catalog.manifest import parse_manifest
from card_market_tracker.watchlist import schema, storage, validation
from card_market_tracker.watchlist.errors import WatchlistError

FIXTURES = Path(__file__).parent / "fixtures"
PRODUCT = "541b9d13-9669-4973-8413-397bea14c045"
SEALED = "79b79554-edd4-4bdc-8120-859974c3df62"
CONFIG = {"target_price_minor": 1000}


def manifest():
    return json.loads((FIXTURES / "synthetic_manifest.json").read_text())


def write(path, *, action="add", expected=0, token="first", config=CONFIG, raw=None, cmt=PRODUCT):
    return storage.write(
        path,
        action=action,
        manifest=manifest() if raw is None else raw,
        cmt_id=cmt,
        config=config,
        expected_revision=expected,
        request_token=token,
    )


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "watchlist.db"
    storage.initialize(path)
    return path


@pytest.fixture
def populated(database):
    return database, write(database)["entry"]["watch_id"]


def category(expected, call):
    with pytest.raises(WatchlistError) as caught:
        call()
    assert caught.value.category == expected


def privileged(path, table, mutation, values=()):
    """Keep exact inventory while simulating privileged data corruption."""
    trigger = {
        "watchlist_entries": "watchlist_identity_immutable",
        "watchlist_revisions": "watchlist_revision_no_update",
        "watchlist_requests": "watchlist_request_no_update",
    }[table]
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA ignore_check_constraints=ON")
        db.execute("DROP TRIGGER " + trigger)
        db.execute(mutation, values)
        db.execute(next(stmt for stmt in schema.STATEMENTS if "CREATE TRIGGER " + trigger in stmt))


def test_exact_independent_schema_and_explicit_init(database, tmp_path):
    assert storage.verify(database)["counts"] == {"entries": 0, "revisions": 0, "requests": 0}
    with sqlite3.connect(database) as db:
        assert db.execute("PRAGMA application_id").fetchone() == (0x434D5457,)
        assert db.execute("PRAGMA user_version").fetchone() == (1,)
        assert (
            tuple(db.execute("SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"))
            == schema.expected_inventory()
        )
        assert all(
            row[5] == 1
            for row in db.execute("PRAGMA table_list")
            if row[1].startswith("watchlist_")
        )
    before = database.read_bytes()
    category("unsafe_destination", lambda: storage.initialize(database))
    assert database.read_bytes() == before
    absent = tmp_path / "absent.db"
    category("storage_missing", lambda: write(absent))
    assert not absent.exists()


def test_revision_replay_and_old_replay_never_reverts(populated):
    path, wid = populated
    expected_id = "wlt1_" + hashlib.sha256(("CMT_WATCHLIST_V1\0" + PRODUCT).encode()).hexdigest()
    assert wid == expected_id
    second = write(
        path, action="update", expected=1, token="second", config={"restock_enabled": True}
    )
    third = write(path, action="disable", expected=2, token="third", config=None)
    fourth = write(path, action="enable", expected=3, token="fourth", config=None)
    before = path.read_bytes()
    assert write(path)["replayed"] is True
    assert write(
        path, action="update", expected=1, token="second", config={"restock_enabled": True}
    ) == {
        **second,
        "replayed": True,
    }
    assert write(path, action="disable", expected=2, token="third", config=None) == {
        **third,
        "replayed": True,
    }
    assert storage.get(path, wid)["entry"] == fourth["entry"]
    assert path.read_bytes() == before
    assert storage.get(path, wid, revision=1)["entry"]["target_price_minor"] == 1000
    assert storage.verify(path)["counts"] == {"entries": 1, "revisions": 4, "requests": 4}
    category("already_exists", lambda: write(path, token="new-add"))
    category("replay_conflict", lambda: write(path, config={"target_price_minor": 999}))
    category("replay_conflict", lambda: write(path, token="first", cmt=SEALED))
    category("revision_conflict", lambda: write(path, action="update", expected=1, token="stale"))
    category(
        "revision_conflict",
        lambda: write(path, action="enable", expected=99, token="missing", config=None),
    )
    category("not_found", lambda: storage.get(path, wid, revision=5))
    category("not_found", lambda: storage.get(path, validation.make_watch_id(SEALED)))


def test_full_manifest_identity_revalidated_at_storage(populated):
    path, wid = populated
    raw = manifest()
    raw["entities"][0]["names"]["es"] = "Changed localization"
    raw["entities"][0]["release_date"] = "2026-01-01"
    raw["bindings"][0]["reason"] = "Different review text"
    assert write(path, raw=raw)["replayed"]
    raw["entities"][2]["card_number"] = "002"
    category(
        "identity_conflict",
        lambda: write(path, action="update", expected=1, token="changed", raw=raw),
    )
    bad = manifest()
    bad["entities"].append(copy.deepcopy(bad["entities"][0]))
    with pytest.raises(WatchlistError):
        write(path, raw=bad)
    with pytest.raises(WatchlistError):
        write(path, raw=parse_manifest(manifest()))
    assert storage.get(path, wid)["entry"]["revision"] == 1


def test_equivalent_defaults_and_action_are_bound(populated):
    path, _ = populated
    full = validation.parse_config(CONFIG)
    assert write(path, config=full)["replayed"]
    write(path, action="disable", config=None, expected=1, token="off")
    category(
        "replay_conflict",
        lambda: write(path, action="enable", config=None, expected=1, token="off"),
    )
    category(
        "invalid_field",
        lambda: write(path, action="disable", expected=2, config=CONFIG, token="bad"),
    )


def test_failed_transaction_rolls_back_all_three_tables(populated, monkeypatch):
    path, wid = populated
    execute = storage._execute

    def fail(db, budget, sql, values=()):
        if sql.startswith("INSERT INTO watchlist_requests"):
            # History exists inside this transaction while the public pointer
            # still addresses the earlier committed revision.
            assert db.execute("SELECT current_revision FROM watchlist_entries").fetchone()[0] == 1
            assert db.execute("SELECT COUNT(*) FROM watchlist_revisions").fetchone()[0] == 2
            raise WatchlistError("storage_io")
        return execute(db, budget, sql, values)

    monkeypatch.setattr(storage, "_execute", fail)
    category("storage_io", lambda: write(path, action="update", expected=1, token="failed"))
    monkeypatch.setattr(storage, "_execute", execute)
    assert storage.get(path, wid)["entry"]["revision"] == 1
    assert storage.verify(path)["counts"] == {"entries": 1, "revisions": 1, "requests": 1}
    assert write(path, action="update", expected=1, token="failed")["entry"]["revision"] == 2


def test_failure_after_history_and_request_before_current_rolls_back(populated, monkeypatch):
    path, wid = populated
    execute = storage._execute

    def fail(db, budget, sql, values=()):
        if sql.startswith("UPDATE watchlist_entries SET current_revision"):
            assert db.execute("SELECT COUNT(*) FROM watchlist_requests").fetchone()[0] == 2
            assert db.execute("SELECT COUNT(*) FROM watchlist_revisions").fetchone()[0] == 2
            raise WatchlistError("storage_io")
        return execute(db, budget, sql, values)

    monkeypatch.setattr(storage, "_execute", fail)
    category("storage_io", lambda: write(path, action="update", expected=1, token="failed"))
    monkeypatch.setattr(storage, "_execute", execute)
    assert storage.get(path, wid)["entry"]["revision"] == 1
    assert storage.verify(path)["counts"] == {"entries": 1, "revisions": 1, "requests": 1}


def test_real_processes_compare_and_swap_one_winner(populated):
    path, wid = populated
    script = """
import json,sys
from pathlib import Path
from card_market_tracker.watchlist import storage
from card_market_tracker.watchlist.errors import WatchlistError
try:
 storage.write(Path(sys.argv[1]),action='update',manifest=json.loads(Path(sys.argv[2]).read_text()),
 cmt_id=sys.argv[3],config={'target_price_minor':2000},expected_revision=1,request_token=sys.argv[4])
 print('ok')
except WatchlistError as error:
 print(error.category)
"""
    processes = [
        subprocess.Popen(
            [
                sys.executable,
                "-c",
                script,
                str(path),
                str(FIXTURES / "synthetic_manifest.json"),
                PRODUCT,
                str(n),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for n in range(2)
    ]
    results = [process.communicate(timeout=15) for process in processes]
    assert sorted(stdout.strip() for stdout, _ in results) == ["ok", "revision_conflict"]
    assert all(not stderr for _, stderr in results)
    assert storage.get(path, wid)["entry"]["revision"] == 2
    assert storage.verify(path)["counts"]["requests"] == 2


def test_real_process_same_token_one_revision(populated):
    path, _ = populated
    script = """
import json,sys
from pathlib import Path
from card_market_tracker.watchlist import storage
result=storage.write(Path(sys.argv[1]),action='update',manifest=json.loads(Path(sys.argv[2]).read_text()),
cmt_id=sys.argv[3],config={'restock_enabled':True},expected_revision=1,request_token='simultaneous')
print(result['replayed'])
"""
    processes = [
        subprocess.Popen(
            [
                sys.executable,
                "-c",
                script,
                str(path),
                str(FIXTURES / "synthetic_manifest.json"),
                PRODUCT,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for _ in range(2)
    ]
    results = [process.communicate(timeout=15) for process in processes]
    assert sorted(stdout.strip() for stdout, _ in results) == ["False", "True"]
    assert all(not stderr for _, stderr in results)
    assert storage.verify(path)["counts"]["revisions"] == 2


def test_process_termination_inside_transaction_recovers(populated):
    path, wid = populated
    script = """
import sqlite3,sys,time
db=sqlite3.connect(sys.argv[1]); db.execute('BEGIN IMMEDIATE')
db.execute('UPDATE watchlist_entries SET current_revision=2')
print('ready',flush=True)
time.sleep(60)
"""
    process = subprocess.Popen(
        [sys.executable, "-c", script, str(path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert process.stdout.readline().strip() == "ready"
    finally:
        process.terminate()
        process.communicate(timeout=10)
    assert storage.get(path, wid)["entry"]["revision"] == 1
    assert storage.verify(path)["counts"]["revisions"] == 1


def test_locked_write_bounded_and_reopen(populated):
    path, wid = populated
    with sqlite3.connect(path) as blocker:
        blocker.execute("BEGIN IMMEDIATE")
        started = time.monotonic()
        category(
            "storage_locked",
            lambda: storage.write(
                path,
                action="update",
                manifest=manifest(),
                cmt_id=PRODUCT,
                config=CONFIG,
                expected_revision=1,
                request_token="lock",
                timeout=0.02,
            ),
        )
        assert time.monotonic() - started < 1
        blocker.rollback()
    assert storage.get(path, wid)["entry"]["revision"] == 1


@pytest.mark.parametrize("timeout", [0, -1, 5.01, float("nan"), float("inf"), True, "2", None])
def test_timeout_is_finite_bounded_exact(database, timeout):
    category("invalid_field", lambda: storage.verify(database, timeout=timeout))


def test_budget_includes_manifest_parsing(database, monkeypatch):
    projection = validation.identity_projection

    def slow(*args):
        time.sleep(0.02)
        return projection(*args)

    monkeypatch.setattr(validation, "identity_projection", slow)
    category(
        "storage_timeout",
        lambda: storage.write(
            database,
            action="add",
            manifest=manifest(),
            cmt_id=PRODUCT,
            config=CONFIG,
            expected_revision=0,
            request_token="slow",
            timeout=0.005,
        ),
    )
    assert storage.verify(database)["counts"]["entries"] == 0


@pytest.mark.parametrize(
    "change",
    [
        "PRAGMA application_id=0",
        "PRAGMA user_version=2",
        "CREATE TABLE alien (x INTEGER) STRICT",
        "CREATE INDEX extra ON watchlist_entries(cmt_id)",
        "DROP INDEX watchlist_by_priority",
        "DROP TRIGGER watchlist_request_no_update",
        "PRAGMA journal_mode=WAL",
        "UPDATE watchlist_metadata SET owner='alien'",
        "DELETE FROM watchlist_metadata",
    ],
)
def test_exact_schema_corruption_rejected(populated, change):
    path, wid = populated
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA ignore_check_constraints=ON")
        db.execute(change)
    category("storage_schema", lambda: storage.verify(path))
    category("storage_schema", lambda: storage.get(path, wid))


@pytest.mark.parametrize(
    "table,mutation,values",
    [
        ("watchlist_entries", "UPDATE watchlist_entries SET identity_digest=?", ("f" * 64,)),
        ("watchlist_entries", "UPDATE watchlist_entries SET priority_rank=0", ()),
        ("watchlist_entries", "UPDATE watchlist_entries SET enabled=0", ()),
        ("watchlist_entries", "UPDATE watchlist_entries SET current_revision=2", ()),
        ("watchlist_revisions", "UPDATE watchlist_revisions SET entry_json='{}'", ()),
        ("watchlist_revisions", "UPDATE watchlist_revisions SET action='update'", ()),
        ("watchlist_revisions", "UPDATE watchlist_revisions SET request_token='orphan'", ()),
        ("watchlist_requests", "UPDATE watchlist_requests SET command_json='{}'", ()),
        ("watchlist_requests", "UPDATE watchlist_requests SET command_digest=?", ("0" * 64,)),
        ("watchlist_requests", "UPDATE watchlist_requests SET revision=2", ()),
        ("watchlist_revisions", "UPDATE watchlist_revisions SET entry_json=?", ("x" * 150000,)),
    ],
)
def test_deep_data_corruption_rejected(populated, table, mutation, values):
    path, wid = populated
    privileged(path, table, mutation, values)
    category("storage_corrupt", lambda: storage.verify(path))
    category("storage_corrupt", lambda: storage.get(path, wid))
    category("storage_corrupt", lambda: write(path, action="update", expected=1, token="new"))


def test_locally_rehashed_command_corruption_rejected(populated):
    path, _ = populated
    with sqlite3.connect(path) as db:
        command = json.loads(
            db.execute("SELECT command_json FROM watchlist_requests").fetchone()[0]
        )
    command["expected_revision"] = 100
    raw = validation.canonical(command)
    privileged(
        path,
        "watchlist_requests",
        "UPDATE watchlist_requests SET command_json=?,command_digest=?",
        (raw, hashlib.sha256(raw.encode()).hexdigest()),
    )
    category("storage_corrupt", lambda: storage.verify(path))


def test_corrupt_old_revision_detected_even_when_current_valid(populated):
    path, wid = populated
    write(path, action="update", expected=1, token="second")
    privileged(
        path,
        "watchlist_revisions",
        "UPDATE watchlist_revisions SET entry_json='{}' WHERE revision=1",
    )
    category("storage_corrupt", lambda: storage.get(path, wid))


def test_history_and_requests_are_immutable_at_sql_boundary(populated):
    path, _ = populated
    for statement in (
        "UPDATE watchlist_revisions SET action='update'",
        "DELETE FROM watchlist_revisions",
        "UPDATE watchlist_requests SET command_json='{}'",
        "DELETE FROM watchlist_requests",
        "DELETE FROM watchlist_entries",
        "UPDATE watchlist_entries SET cmt_id='x'",
    ):
        with sqlite3.connect(path) as db, pytest.raises(sqlite3.IntegrityError):
            db.execute(statement)
    assert storage.verify(path)["counts"]["entries"] == 1


def test_corrupt_and_foreign_files_never_mutated(tmp_path):
    for name, content in (("garbage", b"not sqlite"), ("foreign", None)):
        path = tmp_path / name
        if content is None:
            with sqlite3.connect(path) as db:
                db.execute("CREATE TABLE unrelated (x TEXT)")
        else:
            path.write_bytes(content)
        before = path.read_bytes()
        category(
            "storage_corrupt" if content else "storage_schema",
            lambda path=path: storage.verify(path),
        )
        category("storage_corrupt" if content else "storage_schema", lambda path=path: write(path))
        assert path.read_bytes() == before


def test_pagination_priority_keysets_and_filter_binding(database):
    ids = [
        PRODUCT,
        SEALED,
        "b980e1f7-9bae-432e-b02a-182dbcca478d",
        "4eb24fea-4c89-4249-95dd-ab254d253ce7",
    ]
    priorities = ["low", "high", "normal", "high"]
    for cmt, priority in zip(ids, priorities, strict=True):
        write(database, cmt=cmt, token=cmt, config={"priority": priority, "restock_enabled": True})
    complete = storage.list_entries(database)["entries"]
    assert [entry["priority"] for entry in complete] == ["high", "high", "normal", "low"]
    assert complete[0]["watch_id"] < complete[1]["watch_id"]
    items, cursor = [], None
    while True:
        page = storage.list_entries(database, cursor=cursor, limit=1)
        items.extend(page["entries"])
        cursor = page["next_cursor"]
        if cursor is None:
            break
    assert items == complete
    cursor = storage.list_entries(database, priority="high", limit=1)["next_cursor"]
    category("invalid_field", lambda: storage.list_entries(database, cursor=cursor))
    category(
        "invalid_field",
        lambda: storage.list_entries(database, priority="high", enabled=True, cursor=cursor),
    )
    assert len(storage.list_entries(database, priority="high")["entries"]) == 2
    assert storage.list_entries(database, enabled=False)["entries"] == []


@pytest.mark.parametrize(
    "cursor", ["", "%%%", "A" * 2049, "e30=", base64.urlsafe_b64encode(b"[]").decode()]
)
def test_invalid_cursors(database, cursor):
    category("invalid_field", lambda: storage.list_entries(database, cursor=cursor))


@pytest.mark.parametrize("limit", [0, 1001, True, 1.5, "1"])
def test_page_size_exact_integer(populated, limit):
    path, wid = populated
    category("invalid_field", lambda: storage.list_entries(path, limit=limit))
    category("invalid_field", lambda: storage.history(path, wid, limit=limit))


def test_history_ascending_cursor_bound_to_watch_id(populated):
    path, wid = populated
    write(path, action="update", expected=1, token="two")
    write(path, action="disable", expected=2, token="three", config=None)
    write(path, cmt=SEALED, token="sealed")
    first = storage.history(path, wid, limit=2)
    second = storage.history(path, wid, cursor=first["next_cursor"])
    assert [entry["revision"] for entry in first["entries"] + second["entries"]] == [1, 2, 3]
    assert [entry["action"] for entry in first["entries"] + second["entries"]] == [
        "add",
        "update",
        "disable",
    ]
    assert second["next_cursor"] is None
    category(
        "invalid_field",
        lambda: storage.history(
            path, validation.make_watch_id(SEALED), cursor=first["next_cursor"]
        ),
    )
    category("not_found", lambda: storage.history(path, "wlt1_" + "0" * 64))


def seed_dense(path, *, count, history=False):
    """Efficiently prepare valid large data, independent of the pagination under test."""
    raw = {"version": 1, "entities": [], "bindings": []}
    for _index in range(count if not history else 1):
        raw["entities"].append(
            {"kind": "sealed", "cmt_id": str(uuid.uuid4()), "sealed_type": "box"}
        )
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA foreign_keys=ON")
        for index in range(count):
            cmt = raw["entities"][0 if history else index]["cmt_id"]
            identity = validation.identity_projection(raw, cmt)
            wid = validation.make_watch_id(cmt)
            revision = index + 1 if history else 1
            token = "seed-" + str(index)
            entry = {
                "version": 1,
                "cmt_id": cmt,
                "watch_id": wid,
                "canonical_identity": identity,
                "identity_digest": validation.digest(identity),
                "revision": revision,
                **validation.parse_config(CONFIG),
            }
            action = "add" if revision == 1 else "update"
            command = validation.canonical(storage._command(action, entry, revision - 1))
            if revision == 1:
                db.execute(
                    "INSERT INTO watchlist_entries VALUES (?,?,?,?,?,?,?)",
                    (
                        wid,
                        cmt,
                        validation.canonical(identity),
                        validation.digest(identity),
                        1,
                        1,
                        1,
                    ),
                )
            else:
                db.execute(
                    "UPDATE watchlist_entries SET current_revision=? WHERE watch_id=?",
                    (revision, wid),
                )
            db.execute(
                "INSERT INTO watchlist_revisions VALUES (?,?,?,?,?)",
                (wid, revision, validation.canonical(entry), action, token),
            )
            db.execute(
                "INSERT INTO watchlist_requests VALUES (?,?,?,?,?)",
                (token, command, hashlib.sha256(command.encode()).hexdigest(), wid, revision),
            )
    return wid


@pytest.mark.parametrize("is_history", [False, True])
def test_large_output_pages_do_not_inherit_input_node_limit(database, is_history):
    wid = seed_dense(database, count=400, history=is_history)
    result = (
        storage.history(database, wid, limit=1000, timeout=5)
        if is_history
        else storage.list_entries(database, limit=1000, timeout=5)
    )
    assert len(result["entries"]) == 400
    assert len(json.dumps(result).encode()) < 1024 * 1024


@pytest.mark.parametrize("is_history", [False, True])
def test_page_byte_limit_returns_cursor_instead_of_failing(database, monkeypatch, is_history):
    wid = seed_dense(database, count=8, history=is_history)
    monkeypatch.setattr(storage, "MAX_PAGE_BYTES", 2500)
    cursor, gathered = None, []
    while True:
        result = (
            storage.history(database, wid, cursor=cursor)
            if is_history
            else storage.list_entries(database, cursor=cursor)
        )
        assert len(json.dumps(result, ensure_ascii=True, separators=(",", ":")).encode()) <= 2500
        gathered.extend(result["entries"])
        cursor = result["next_cursor"]
        if cursor is None:
            break
    assert len(gathered) == 8


def test_backup_restore_reopen_and_no_overwrite(populated, tmp_path):
    path, wid = populated
    write(path, action="update", expected=1, token="second")
    before = path.read_bytes()
    backup, restored = tmp_path / "copy.db", tmp_path / "restored.db"
    assert storage.backup(path, backup)["counts"]["revisions"] == 2
    assert path.read_bytes() == before
    assert storage.restore(backup, restored)["counts"]["revisions"] == 2
    assert storage.get(restored, wid) == storage.get(path, wid)
    assert write(restored, action="update", expected=2, token="new")["entry"]["revision"] == 3
    assert storage.get(path, wid)["entry"]["revision"] == 2
    category("unsafe_destination", lambda: storage.restore(backup, restored))
    category("unsafe_destination", lambda: storage.backup(path, path))
    assert not list(tmp_path.glob(".cmt-watchlist-*"))


def test_restore_validates_provisional_before_destination_exists(populated, tmp_path, monkeypatch):
    path, _ = populated
    target = tmp_path / "restored.db"
    publish = storage._publish
    calls = []

    def inspect(provisional, destination, identity):
        assert not target.exists()
        assert storage.verify(provisional)["counts"]["entries"] == 1
        calls.append(provisional)
        publish(provisional, destination, identity)

    monkeypatch.setattr(storage, "_publish", inspect)
    storage.restore(path, target)
    assert len(calls) == 1 and target.exists() and not calls[0].exists()


def test_copy_failure_preserves_foreign_files_and_sidecars(populated, tmp_path, monkeypatch):
    path, _ = populated
    target = tmp_path / "target.db"

    def competing_destination(provisional, destination, identity):
        destination.write_bytes(b"foreign evidence")
        raise WatchlistError("unsafe_destination")

    monkeypatch.setattr(storage, "_publish", competing_destination)
    category("unsafe_destination", lambda: storage.restore(path, target))
    assert target.read_bytes() == b"foreign evidence"
    assert not list(tmp_path.glob(".cmt-watchlist-*"))
    second = tmp_path / "second.db"
    sidecar = Path(str(second) + "-journal")
    sidecar.write_bytes(b"foreign sidecar")
    category("unsafe_destination", lambda: storage.backup(path, second))
    assert sidecar.read_bytes() == b"foreign sidecar" and not second.exists()


def test_invalid_source_never_exposes_recovery_destination(populated, tmp_path):
    path, _ = populated
    privileged(
        path, "watchlist_requests", "UPDATE watchlist_requests SET command_digest=?", ("f" * 64,)
    )
    target = tmp_path / "restore.db"
    category("storage_corrupt", lambda: storage.restore(path, target))
    assert not target.exists() and not list(tmp_path.glob(".cmt-watchlist-*"))


@pytest.mark.parametrize("stage", ["reopen", "fsync", "publish"])
def test_copy_failure_before_publication_is_clean_and_bounded(
    populated, tmp_path, monkeypatch, stage
):
    path, _ = populated
    target = tmp_path / "restore.db"
    if stage == "reopen":
        verify = storage._verify
        calls = 0

        def fail_verify(db, budget):
            nonlocal calls
            calls += 1
            if calls == 3:
                raise WatchlistError("storage_corrupt")
            return verify(db, budget)

        monkeypatch.setattr(storage, "_verify", fail_verify)
    else:

        def fail_io(*args, **kwargs):
            raise OSError("sensitive local path must never escape")

        monkeypatch.setattr(storage.os, "fsync" if stage == "fsync" else "link", fail_io)
    category(
        "storage_corrupt" if stage == "reopen" else "storage_io",
        lambda: storage.restore(path, target),
    )
    assert not target.exists() and not list(tmp_path.glob(".cmt-watchlist-*"))


def test_initializer_failure_removes_only_its_reserved_file(tmp_path, monkeypatch):
    target = tmp_path / "init.db"
    monkeypatch.setattr(schema, "STATEMENTS", ("INVALID SQL",))
    category("storage_io", lambda: storage.initialize(target))
    assert not target.exists()


def test_publish_competing_destination_never_overwritten(tmp_path):
    provisional, target = tmp_path / "provisional", tmp_path / "target"
    provisional.write_bytes(b"complete verified copy")
    information = provisional.stat()
    identity = information.st_dev, information.st_ino
    target.write_bytes(b"foreign")
    category("unsafe_destination", lambda: storage._publish(provisional, target, identity))
    assert provisional.read_bytes() == b"complete verified copy"
    assert target.read_bytes() == b"foreign"


def test_publish_preserves_provisional_sidecar_evidence(tmp_path):
    provisional, target = tmp_path / "provisional", tmp_path / "target"
    provisional.write_bytes(b"copy")
    information = provisional.stat()
    sidecar = Path(str(provisional) + "-journal")
    sidecar.write_bytes(b"recovery")
    category(
        "unsafe_destination",
        lambda: storage._publish(provisional, target, (information.st_dev, information.st_ino)),
    )
    assert not target.exists() and provisional.exists() and sidecar.read_bytes() == b"recovery"


def test_cleanup_never_removes_changed_inode_or_sidecars(tmp_path):
    target = tmp_path / "reserved"
    target.write_bytes(b"ours")
    info = target.stat()
    identity = info.st_dev, info.st_ino
    sidecar = Path(str(target) + "-journal")
    sidecar.write_bytes(b"evidence")
    storage._cleanup_reserved(target, identity)
    assert target.exists() and sidecar.exists()
    sidecar.unlink()
    storage._cleanup_reserved(target, (identity[0], identity[1] + 1))
    assert target.exists()
    storage._cleanup_reserved(target, identity)
    assert not target.exists()


def test_hardlink_and_symlink_aliases_rejected(populated, tmp_path):
    path, _ = populated
    alias = tmp_path / "alias.db"
    try:
        os.link(path, alias)
    except OSError:
        pytest.skip("filesystem does not support hard links")
    category("unsafe_destination", lambda: storage.verify(alias))
    alias.unlink()
    try:
        alias.symlink_to(path)
    except OSError:
        return
    category("unsafe_destination", lambda: storage.verify(alias))


@pytest.mark.parametrize(
    "field,value",
    [
        ("action", "delete"),
        ("expected_revision", True),
        ("expected_revision", -1),
        ("request_token", ""),
        ("request_token", "x" * 129),
        ("request_token", "DROP TABLE;--"),
        ("request_token", "é"),
        ("config", {"target_price_minor": True}),
        ("config", {"target_price_minor": 0}),
        ("config", {"target_price_minor": 1.5}),
        ("config", {"target_price_minor": 1000000001}),
        ("config", {"restock_enabled": True, "SQL": "x"}),
    ],
)
def test_hostile_write_inputs_are_rejected_without_mutation(database, field, value):
    arguments = {
        "action": "add",
        "manifest": manifest(),
        "cmt_id": PRODUCT,
        "config": CONFIG,
        "expected_revision": 0,
        "request_token": "token",
    }
    arguments[field] = value
    before = database.read_bytes()
    with pytest.raises(WatchlistError):
        storage.write(database, **arguments)
    assert database.read_bytes() == before
