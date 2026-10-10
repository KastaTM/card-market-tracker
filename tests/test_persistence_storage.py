"""Actual temporary SQLite files: durability, replay, constraints and rollback risks."""

import json
import sqlite3
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import pytest

from card_market_tracker.catalog.ingestion import ExternalReference, Observation
from card_market_tracker.catalog.manifest import parse_manifest
from card_market_tracker.persistence import sqlite_repository as storage
from card_market_tracker.persistence.application import build_batch
from card_market_tracker.persistence.errors import PersistenceError
from card_market_tracker.persistence.input import observation_dict, read_persistence
from card_market_tracker.persistence.schema import inventory

FIXTURES = Path(__file__).parent / "fixtures"
CAPTURE = "2026-10-10T09:00:00.000000Z"


def batch(case="valid"):
    return read_persistence(
        FIXTURES / f"synthetic_persistence_{case}.json", FIXTURES / "synthetic_manifest.json"
    )


def manifest_document():
    return json.loads((FIXTURES / "synthetic_manifest.json").read_text(encoding="utf-8"))


def counts(path):
    with sqlite3.connect(path) as connection:
        return tuple(
            connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            for table in ("entities", "batches", "records")
        )


def assert_category(category, action):
    with pytest.raises(PersistenceError) as error:
        action()
    assert error.value.category == category
    assert str(error.value) == category


def test_durable_normalized_snapshots_reopen_and_distinct_process(tmp_path):
    path = tmp_path / "history.db"
    admitted = batch()
    written = storage.persist(path, admitted)
    assert written.committed_observations == 7 and written.committed_entities == 8
    result = storage.query(path)
    assert [item["observation"] for item in result["records"]] == [
        observation_dict(item.observation) for item in admitted.records
    ]
    assert result["records"][2]["observation"]["provider_updated_at"] == (
        "2026-10-09T09:30:00.000000Z"
    )
    child = subprocess.run(
        [
            sys.executable,
            "-c",
            "import json,sys;from pathlib import Path;"
            "from card_market_tracker.persistence.sqlite_repository import query,verify;"
            "p=Path(sys.argv[1]);verify(p);print(json.dumps(query(p),sort_keys=True))",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert json.loads(child.stdout) == result
    assert storage.verify(path)["result"] == "ok"


@pytest.mark.parametrize(
    "case,outcome,expected",
    [
        ("mixed", "mixed", (1, 1, 1)),
        ("candidates", "mixed", (0, 2, 0)),
        ("rejected", "mixed", (0, 0, 2)),
        ("empty", "empty", (0, 0, 0)),
    ],
)
def test_safe_partial_candidate_rejected_and_empty_snapshots(tmp_path, case, outcome, expected):
    path = tmp_path / "partial.db"
    written = storage.persist(path, batch(case))
    assert written.result == outcome
    assert (written.accepted_count, written.candidate_count, written.rejected_count) == expected
    rows = storage.query(path)["records"]
    for row in rows:
        if row["status"] == "candidate":
            assert row["cmt_id"] is None and row["observation"] is not None
        elif row["status"] == "rejected":
            assert row["cmt_id"] is None and row["observation"] is None
    raw = path.read_bytes()
    assert b"Dato rechazado" not in raw and b"synthetic-broken" not in raw
    first = written.first_persisted_at
    replay = storage.persist(path, batch(case))
    assert replay.result == "replay" and replay.first_persisted_at == first
    assert replay.committed_entities == replay.committed_observations == 0


def test_replay_content_context_conflict_and_later_capture(tmp_path):
    path = tmp_path / "history.db"
    admitted = batch()
    first = storage.persist(path, admitted)
    before = counts(path), storage.query(path)
    original = tuple(record.observation for record in admitted.records)
    changed = build_batch(
        admitted.batch_id,
        admitted.captured_at,
        (replace(original[0], name="Changed evidence"), *original[1:]),
        admitted.manifest,
    )
    assert_category("replay_conflict", lambda: storage.persist(path, changed))
    document = manifest_document()
    document["bindings"][2]["reference"]["external_id"] = "unrelated-context-change"
    context_changed = build_batch(admitted.batch_id, admitted.captured_at, original, document)
    assert_category("replay_conflict", lambda: storage.persist(path, context_changed))
    assert (counts(path), storage.query(path)) == before
    later = build_batch(
        str(uuid4()),
        "2026-10-11T09:00:00Z",
        tuple(replace(item, captured_at=None) for item in original),
        admitted.manifest,
    )
    result = storage.persist(path, later)
    assert result.committed_observations == 7 and result.committed_entities == 0
    assert counts(path) == (8, 2, 14)
    assert storage.persist(path, admitted).first_persisted_at == first.first_persisted_at


def test_query_exact_context_null_not_wildcard_and_limits(tmp_path):
    path = tmp_path / "queries.db"
    curated = parse_manifest(manifest_document())
    base = Observation(
        "sealed",
        ExternalReference("synthetic", "sealed", "unmapped", None),
        "Synthetic box",
        provenance="synthetic",
    )
    observations = (base, replace(base, reference=replace(base.reference, language="es")))
    admitted = build_batch(str(uuid4()), CAPTURE, observations, curated)
    storage.persist(path, admitted)
    selected = storage.query(path, candidate_reference=base.reference)["records"]
    assert len(selected) == 1 and selected[0]["observation"]["reference"]["language"] is None
    assert len(storage.query(path, limit=1)["records"]) == 1
    assert len(storage.query(path, batch_id=admitted.batch_id)["records"]) == 2
    assert storage.query(path, cmt_id=str(uuid4()))["result"] == "empty"
    assert_category(
        "invalid_shape",
        lambda: storage.query(path, batch_id=admitted.batch_id, cmt_id=str(uuid4())),
    )
    for value in (0, 1001, True, "100", 1.5):
        assert_category("invalid_field", lambda value=value: storage.query(path, limit=value))
    for value in ("bad", "';DROP TABLE records;--"):
        assert_category("invalid_field", lambda value=value: storage.query(path, batch_id=value))
    assert_category("invalid_field", lambda: storage.query(path, candidate_reference=object()))


def test_order_capture_token_index_duplicates_and_target(tmp_path):
    path = tmp_path / "ordering.db"
    original = batch().records[2].observation
    curated = batch().manifest
    tokens = ["ffffffff-ffff-4fff-8fff-ffffffffffff", "00000000-0000-4000-8000-000000000001"]
    for token in tokens:
        admitted = build_batch(token, CAPTURE, (original, original), curated)
        storage.persist(path, admitted)
    rows = storage.query(path, cmt_id=batch().records[2].cmt_id)["records"]
    assert [(row["batch_id"], row["index"]) for row in rows] == [
        (tokens[1], 0),
        (tokens[1], 1),
        (tokens[0], 0),
        (tokens[0], 1),
    ]
    assert counts(path) == (3, 2, 4)


def test_public_repository_revalidates_manual_dataclasses_before_file_creation(tmp_path):
    path = tmp_path / "absent.db"
    admitted = batch()
    forged = replace(admitted, records=(replace(admitted.records[0], cmt_id=str(uuid4())),))
    with pytest.raises(PersistenceError):
        storage.persist(path, forged)
    assert not path.exists()
    forged = replace(
        admitted,
        records=(
            replace(
                admitted.records[0],
                observation=replace(admitted.records[0].observation, provenance="observed"),
            ),
            *admitted.records[1:],
        ),
    )
    assert_category("synthetic_only", lambda: storage.persist(path, forged))
    assert not path.exists()


@pytest.mark.parametrize(
    "failure", [sqlite3.OperationalError("simulated disk full"), OSError("simulated IO failure")]
)
def test_simulated_failure_after_real_intermediate_write_rolls_back_entire_batch(
    tmp_path, monkeypatch, failure
):
    path = tmp_path / "rollback.db"
    storage.initialize(path)
    original = storage._execute
    saw_real_intermediate_write = []

    def inject(connection, budget, sql, values=()):
        cursor = original(connection, budget, sql, values)
        if sql.startswith("INSERT INTO records"):
            saw_real_intermediate_write.append(
                connection.execute("SELECT count(*) FROM entities").fetchone()[0]
            )
            raise failure
        return cursor

    monkeypatch.setattr(storage, "_execute", inject)
    assert_category("storage_io", lambda: storage.persist(path, batch()))
    assert saw_real_intermediate_write == [8]
    assert counts(path) == (0, 0, 0)
    assert storage.verify(path)["result"] == "ok"


def test_initialization_ddl_version_metadata_rollback_and_current_noop(tmp_path, monkeypatch):
    path = tmp_path / "initial.db"
    original = storage._execute

    def inject(connection, budget, sql, values=()):
        result = original(connection, budget, sql, values)
        if sql.startswith("CREATE TABLE entities"):
            assert connection.execute("SELECT name FROM sqlite_schema").fetchall()
            raise sqlite3.OperationalError("simulated initialization failure")
        return result

    with monkeypatch.context() as changes:
        changes.setattr(storage, "_execute", inject)
        assert_category("storage_io", lambda: storage.initialize(path))
    with sqlite3.connect(path) as connection:
        assert inventory(connection) == ()
        assert connection.execute("PRAGMA application_id").fetchone() == (0,)
        assert connection.execute("PRAGMA user_version").fetchone() == (0,)
    storage.initialize(path)
    initial = path.read_bytes()
    assert storage.initialize(path)["result"] == "ok"
    assert path.read_bytes() == initial


@pytest.mark.parametrize(
    "alteration",
    [
        "PRAGMA user_version=2",
        "PRAGMA application_id=0",
        "DROP INDEX candidate_context",
        "CREATE TABLE unrelated(x)",
        "DROP TRIGGER record_context",
        "DELETE FROM storage_metadata",
        "PRAGMA journal_mode=WAL",
    ],
)
def test_incompatible_owned_schema_is_rejected_without_reset(tmp_path, alteration):
    path = tmp_path / "modified.db"
    storage.initialize(path)
    with sqlite3.connect(path) as connection:
        connection.executescript(alteration)
    before = path.read_bytes()
    for operation in (storage.initialize, storage.query, storage.verify):
        assert_category("storage_schema", lambda operation=operation: operation(path))
        assert path.read_bytes() == before


def test_foreign_database_and_corruption_never_become_empty_or_reset(tmp_path):
    foreign = tmp_path / "foreign.db"
    with sqlite3.connect(foreign) as connection:
        connection.execute("CREATE TABLE private_data(value)")
        connection.execute("INSERT INTO private_data VALUES ('untouched')")
    before = foreign.read_bytes()
    assert_category("storage_schema", lambda: storage.persist(foreign, batch()))
    assert foreign.read_bytes() == before
    corrupt = tmp_path / "corrupt.db"
    corrupt.write_bytes(b"synthetic corrupted SQLite file")
    for operation in (storage.initialize, storage.query, storage.verify):
        assert_category("storage_corrupt", lambda operation=operation: operation(corrupt))
    assert corrupt.read_bytes() == b"synthetic corrupted SQLite file"


def test_missing_reads_do_not_create_file_and_timeout_values_are_bounded(tmp_path):
    path = tmp_path / "missing.db"
    for operation in (storage.query, storage.verify):
        assert_category("storage_io", lambda operation=operation: operation(path))
        assert not path.exists()
    for timeout in (0, -1, 5.1, True, "2", float("nan")):
        assert_category(
            "invalid_field", lambda timeout=timeout: storage.initialize(path, timeout=timeout)
        )
    assert not path.exists()


def test_each_connection_fk_full_delete_and_read_only_mode(tmp_path):
    path = tmp_path / "settings.db"
    storage.initialize(path)
    for writable in (False, True):
        with storage._connection(path, writable=writable) as (connection, budget):
            assert connection.autocommit is True
            assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
            assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
            if writable:
                storage._initialize(connection, budget)
                assert connection.execute("PRAGMA synchronous").fetchone()[0] == 2
            else:
                assert connection.execute("PRAGMA query_only").fetchone()[0] == 1
                with pytest.raises(sqlite3.OperationalError):
                    connection.execute("INSERT INTO storage_metadata VALUES (2,'bad',1)")


def test_database_enforces_required_snapshot_fields_and_foreign_keys(tmp_path):
    path = tmp_path / "constraints.db"
    admitted = batch("mixed")
    storage.persist(path, admitted)
    with sqlite3.connect(path, autocommit=True) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        accepted = list(storage._record_values(admitted.batch_id, admitted.records[0]))
        candidate = list(storage._record_values(admitted.batch_id, admitted.records[1]))
        # Delete the original rows only in this temporary constraint drill.
        connection.execute("DELETE FROM records")
        sql = "INSERT INTO records VALUES (" + ",".join("?" for _ in accepted) + ")"
        for position in (5, 6, 7, 9, 10, 17, 18):
            changed = accepted.copy()
            changed[position] = None
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(sql, changed)
        changed = candidate.copy()
        changed[3] = None
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(sql, changed)
        changed = accepted.copy()
        changed[0] = str(uuid4())
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(sql, changed)
        changed = accepted.copy()
        changed[4] = str(uuid4())
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(sql, changed)
        changed = candidate.copy()
        changed[4] = admitted.records[0].cmt_id
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(sql, changed)


def test_identity_same_uuid_changed_relation_and_different_uuid_same_identity(tmp_path):
    path = tmp_path / "identity.db"
    admitted = batch()
    observation = admitted.records[2].observation
    first = build_batch(str(uuid4()), CAPTURE, (observation,), admitted.manifest)
    storage.persist(path, first)
    before = counts(path), storage.query(path)
    document = manifest_document()
    document["entities"][2]["card_number"] = "002"
    conflicting = build_batch(
        str(uuid4()), CAPTURE, (replace(observation, card_number="002"),), document
    )
    assert conflicting.records[0].status == "accepted"
    assert_category("identity_conflict", lambda: storage.persist(path, conflicting))
    document = manifest_document()
    previous_id = document["entities"][2]["cmt_id"]
    replacement_id = str(uuid4())
    document["entities"][2]["cmt_id"] = replacement_id
    for entity in document["entities"]:
        if entity.get("card_id") == previous_id:
            entity["card_id"] = replacement_id
    colliding = build_batch(str(uuid4()), CAPTURE, (observation,), document)
    assert_category("identity_conflict", lambda: storage.persist(path, colliding))
    assert (counts(path), storage.query(path)) == before


def test_parameterized_hostile_name_is_retained_as_evidence_only(tmp_path):
    path = tmp_path / "injection.db"
    admitted = batch()
    hostile = "Robert'); DROP TABLE entities; --"
    original = admitted.records[0].observation
    changed = build_batch(
        str(uuid4()), CAPTURE, (replace(original, name=hostile),), admitted.manifest
    )
    storage.persist(path, changed)
    assert storage.query(path)["records"][0]["observation"]["name"] == hostile
    assert storage.verify(path)["result"] == "ok"


def test_finite_writer_lock_and_commit_reader_contention_roll_back(tmp_path):
    path = tmp_path / "locked.db"
    storage.initialize(path)
    holder = sqlite3.connect(path, autocommit=True)
    try:
        holder.execute("BEGIN IMMEDIATE")
        start = time.monotonic()
        assert_category("storage_locked", lambda: storage.persist(path, batch(), timeout=0.12))
        assert time.monotonic() - start < 1.5
        holder.execute("ROLLBACK")
        holder.execute("BEGIN")
        holder.execute("SELECT * FROM entities").fetchall()
        start = time.monotonic()
        assert_category("storage_locked", lambda: storage.persist(path, batch(), timeout=0.12))
        assert time.monotonic() - start < 1.5
        holder.execute("ROLLBACK")
    finally:
        holder.close()
    assert counts(path) == (0, 0, 0)


@pytest.mark.parametrize("after_commit", [False, True])
def test_process_termination_before_or_after_commit_recovers_coherent_state(tmp_path, after_commit):
    path = tmp_path / "process.db"
    storage.initialize(path)
    script = r"""
import os, sys
from pathlib import Path
from card_market_tracker.persistence import sqlite_repository as storage
from card_market_tracker.persistence.input import read_persistence
admitted = read_persistence(Path(sys.argv[2]), Path(sys.argv[3]))
if sys.argv[4] == 'before':
    original = storage._execute
    def execute(connection, budget, sql, values=()):
        result = original(connection, budget, sql, values)
        if sql.startswith('INSERT INTO records'):
            os._exit(71)
        return result
    storage._execute = execute
storage.persist(Path(sys.argv[1]), admitted)
os._exit(72)
"""
    child = subprocess.run(
        [
            sys.executable,
            "-c",
            script,
            str(path),
            str(FIXTURES / "synthetic_persistence_valid.json"),
            str(FIXTURES / "synthetic_manifest.json"),
            "after" if after_commit else "before",
        ],
        capture_output=True,
        text=True,
    )
    assert child.returncode == (72 if after_commit else 71), child.stderr
    # Opening writable permits normal SQLite rollback journal recovery after abrupt exit.
    storage.initialize(path)
    assert storage.verify(path)["result"] == "ok"
    assert counts(path) == ((8, 1, 7) if after_commit else (0, 0, 0))


def test_integrity_foreign_key_damage_detected_as_corruption(tmp_path):
    path = tmp_path / "broken-relation.db"
    storage.persist(path, batch())
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys=OFF")
        connection.execute("DELETE FROM entities WHERE kind='set'")
    assert_category("storage_corrupt", lambda: storage.verify(path))


def test_database_paths_refuse_directory_and_parent_traversal(tmp_path):
    assert_category("unsafe_destination", lambda: storage.initialize(tmp_path))
    assert_category("unsafe_destination", lambda: storage.initialize(tmp_path / ".." / "other.db"))
    assert_category("invalid_field", lambda: storage.initialize("string-is-not-Path"))
    assert_category("unsafe_destination", lambda: storage.initialize(tmp_path / "nul\x00.db"))
    assert_category("storage_io", lambda: storage.initialize(tmp_path / "absent" / "file.db"))


def test_simulated_permission_error_is_safe_and_not_empty(tmp_path, monkeypatch):
    path = tmp_path / "denied.db"
    storage.initialize(path)

    def denied(*args, **kwargs):
        raise PermissionError("simulated sensitive host path")

    monkeypatch.setattr(storage, "_checked_path", denied)
    assert_category("storage_io", lambda: storage.query(path))


def test_total_operation_deadline_interrupts_work_and_rolls_back(tmp_path, monkeypatch):
    path = tmp_path / "deadline.db"
    storage.initialize(path)
    original = storage._execute

    def slow(connection, budget, sql, values=()):
        result = original(connection, budget, sql, values)
        if sql.startswith("INSERT INTO entities"):
            time.sleep(0.03)
        return result

    monkeypatch.setattr(storage, "_execute", slow)
    assert_category("storage_timeout", lambda: storage.persist(path, batch(), timeout=0.02))
    assert counts(path) == (0, 0, 0)
