"""Real owned SQLite snapshot reads: existence, consistency and fail-closed evidence."""

import sqlite3
import threading
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import pytest

from card_market_tracker.catalog.ingestion import RecordError
from card_market_tracker.discovery.errors import DiscoveryError
from card_market_tracker.persistence import sqlite_repository as storage
from card_market_tracker.persistence.application import build_batch, context_fingerprint
from card_market_tracker.persistence.errors import PersistenceError
from card_market_tracker.persistence.input import read_persistence

FIXTURES = Path(__file__).parent / "fixtures"


def batch(case="valid"):
    return read_persistence(
        FIXTURES / f"synthetic_persistence_{case}.json", FIXTURES / "synthetic_manifest.json"
    )


def seed(path, case="valid"):
    value = batch(case)
    storage.persist(path, value)
    return value


def assert_category(category, action):
    with pytest.raises((DiscoveryError, PersistenceError)) as caught:
        action()
    assert caught.value.category == category
    assert str(caught.value) == category


def test_existing_empty_has_metadata_missing_is_error_and_old_query_is_ambiguous(tmp_path):
    path = tmp_path / "empty.db"
    empty = seed(path, "empty")
    missing = str(uuid4())
    assert storage.query(path, batch_id=empty.batch_id) == storage.query(path, batch_id=missing)
    (snapshot,) = storage.read_snapshots(path, (empty.batch_id,))
    assert snapshot.batch_id == empty.batch_id
    assert snapshot.captured_at == empty.captured_at
    assert snapshot.result == "empty" and snapshot.input_count == 0
    assert snapshot.records == ()
    assert_category("batch_missing", lambda: storage.read_snapshots(path, (missing,)))


def test_manifest_fingerprint_cannot_attest_capture_scope():
    empty, valid = batch("empty"), batch()
    observation = next(
        record.observation
        for record in valid.records
        if record.observation is not None
        and record.observation.kind == "set"
        and record.observation.reference.language == "es"
    )
    spanish = build_batch(str(uuid4()), empty.captured_at, (observation,), empty.manifest)
    english_observation = replace(
        observation, reference=replace(observation.reference, language="en")
    )
    english = build_batch(str(uuid4()), empty.captured_at, (english_observation,), empty.manifest)
    assert spanish.records[0].status == english.records[0].status == "accepted"
    assert spanish.records[0].observation.reference != english.records[0].observation.reference
    assert (
        context_fingerprint(empty) == context_fingerprint(spanish) == context_fingerprint(english)
    )


@pytest.mark.parametrize("case", ["valid", "candidates", "mixed", "rejected"])
def test_complete_frozen_evidence_survives_read_without_mutation(tmp_path, case):
    path = tmp_path / "snapshots.db"
    original = seed(path, case)
    before = path.read_bytes()
    (snapshot,) = storage.read_snapshots(path, (original.batch_id,))
    assert path.read_bytes() == before
    assert snapshot.input_count == len(original.records)
    assert [(r.index, r.status, r.category, r.cmt_id, r.observation) for r in snapshot.records] == [
        (r.index, r.status, r.category, r.cmt_id, r.observation) for r in original.records
    ]
    assert snapshot.accepted_count + snapshot.candidate_count + snapshot.rejected_count == (
        snapshot.input_count
    )
    assert storage.read_snapshots(path, (original.batch_id,)) == (snapshot,)


def test_batch_order_is_canonical_and_every_selected_snapshot_complete(tmp_path):
    path = tmp_path / "order.db"
    current, empty = seed(path), seed(path, "empty")
    tokens = (current.batch_id, empty.batch_id)
    forward = storage.read_snapshots(path, tokens)
    assert forward == storage.read_snapshots(path, tuple(reversed(tokens)))
    assert [value.batch_id for value in forward] == sorted(tokens)
    assert sum(value.input_count for value in forward) == len(current.records)


@pytest.mark.parametrize(
    "tokens,category",
    [
        ([], "invalid_shape"),
        ((), "input_limit"),
        (("bad",), "invalid_field"),
        (("';DROP TABLE records;--",), "invalid_field"),
        ((True,), "invalid_field"),
        (("11111111-1111-4111-8111-111111111111",) * 2, "invalid_field"),
        (tuple(str(uuid4()) for _ in range(34)), "input_limit"),
    ],
)
def test_public_token_boundary_fails_before_missing_db_creation(tmp_path, tokens, category):
    path = tmp_path / "absent.db"
    assert_category(category, lambda: storage.read_snapshots(path, tokens))
    assert not path.exists()


def test_valid_missing_db_never_creates_and_invalid_timeout_never_opens(tmp_path):
    path = tmp_path / "absent.db"
    tokens = (str(uuid4()),)
    assert_category("storage_io", lambda: storage.read_snapshots(path, tokens))
    for timeout in (True, 0, 6, float("nan"), "2"):
        assert_category(
            "invalid_field",
            lambda timeout=timeout: storage.read_snapshots(path, tokens, timeout=timeout),
        )
    assert not path.exists()


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM records WHERE record_index=0",
        "UPDATE records SET record_index=999 WHERE record_index=0",
        "UPDATE batches SET fingerprint='" + "g" * 64 + "'",
        "UPDATE batches SET captured_at='2026-99-99T09:00:00.000000Z'",
        "UPDATE records SET namespace='invalid namespace' WHERE record_index=0",
        "UPDATE records SET captured_at='2026-10-11T09:00:00.000000Z' WHERE record_index=0",
        "UPDATE entities SET language='en' WHERE kind='printing' AND variant='holo'",
        "UPDATE entities SET set_id=(SELECT cmt_id FROM entities WHERE kind='card' LIMIT 1) "
        "WHERE kind='card'",
    ],
)
def test_business_tampering_rejected_even_when_sql_constraints_allow_it(tmp_path, sql):
    path = tmp_path / "tampered.db"
    original = seed(path)
    with closing(sqlite3.connect(path, autocommit=True)) as connection:
        connection.execute(sql)
    assert_category("storage_corrupt", lambda: storage.read_snapshots(path, (original.batch_id,)))


def test_foreign_future_corrupt_and_fk_damage_never_become_empty(tmp_path):
    token = str(uuid4())
    for case in ("foreign", "future", "corrupt", "fk"):
        path = tmp_path / f"{case}.db"
        if case == "corrupt":
            path.write_bytes(b"synthetic damaged sqlite")
        elif case == "foreign":
            with closing(sqlite3.connect(path, autocommit=True)) as connection:
                connection.execute("CREATE TABLE foreign_table(value)")
        else:
            original = seed(path)
            with closing(sqlite3.connect(path, autocommit=True)) as connection:
                connection.execute(
                    "PRAGMA user_version=3" if case == "future" else "DELETE FROM batches"
                )
            token = original.batch_id
        before = path.read_bytes()
        assert_category(
            "storage_schema" if case in ("foreign", "future") else "storage_corrupt",
            lambda path=path, token=token: storage.read_snapshots(path, (token,)),
        )
        assert path.read_bytes() == before


def test_read_transaction_is_query_only_and_schema_is_inside_transaction(tmp_path, monkeypatch):
    path = tmp_path / "readonly.db"
    original = seed(path)
    previous = storage._require_schema
    observed = []

    def check(connection, budget):
        observed.append(connection.in_transaction)
        assert connection.execute("PRAGMA query_only").fetchone()[0] == 1
        with pytest.raises(sqlite3.OperationalError):
            connection.execute("DELETE FROM batches")
        return previous(connection, budget)

    monkeypatch.setattr(storage, "_require_schema", check)
    storage.read_snapshots(path, (original.batch_id,))
    assert observed == [True]


def test_real_writer_cannot_commit_between_metadata_and_rows(tmp_path, monkeypatch):
    path = tmp_path / "concurrent.db"
    original = batch()
    observation = original.records[0].observation
    one = build_batch(str(uuid4()), original.captured_at, (observation,), original.manifest)
    storage.persist(path, one)
    ready, done = threading.Event(), threading.Event()
    errors = []
    writer_thread = None
    execute = storage._execute

    def writer():
        try:
            with closing(sqlite3.connect(path, autocommit=True, timeout=2)) as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute("DELETE FROM records WHERE batch_id=?", (one.batch_id,))
                connection.execute(
                    "UPDATE batches SET input_count=0,accepted_count=0,candidate_count=0,"
                    "rejected_count=0,result='empty' WHERE batch_id=?",
                    (one.batch_id,),
                )
                ready.set()
                connection.execute("COMMIT")
                done.set()
        except BaseException as error:
            errors.append(error)
            ready.set()
            done.set()

    def interleave(connection, budget, sql, values=()):
        nonlocal writer_thread
        cursor = execute(connection, budget, sql, values)
        if sql == "SELECT * FROM batches WHERE batch_id=?" and writer_thread is None:
            writer_thread = threading.Thread(target=writer)
            writer_thread.start()
            assert ready.wait(1), "writer did not reach commit"
            assert not done.is_set(), "writer committed inside reader transaction"
        return cursor

    monkeypatch.setattr(storage, "_execute", interleave)
    try:
        (snapshot,) = storage.read_snapshots(path, (one.batch_id,))
        assert snapshot.input_count == len(snapshot.records) == 1
    finally:
        if writer_thread is not None:
            writer_thread.join(3)
            assert not writer_thread.is_alive()
    assert not errors and done.is_set()
    (later,) = storage.read_snapshots(path, (one.batch_id,))
    assert later.input_count == 0 and snapshot.input_count == 1


def test_lock_deadline_and_python_validation_failure_release_reader(tmp_path, monkeypatch):
    path = tmp_path / "budget.db"
    original = seed(path)
    with closing(sqlite3.connect(path, autocommit=True)) as holder:
        holder.execute("BEGIN EXCLUSIVE")
        assert_category(
            "storage_locked",
            lambda: storage.read_snapshots(path, (original.batch_id,), timeout=0.02),
        )
        holder.execute("ROLLBACK")
    validate = storage.validate_snapshot

    def expired(snapshot):
        result = validate(snapshot)
        patched.setattr(storage.time, "monotonic", lambda: float("inf"))
        return result

    with monkeypatch.context() as patched:
        patched.setattr(storage, "validate_snapshot", expired)
        assert_category(
            "storage_timeout", lambda: storage.read_snapshots(path, (original.batch_id,))
        )
    # A failure must release its reader lock so an independent writer can commit.
    with closing(sqlite3.connect(path, autocommit=True, timeout=0.05)) as writer:
        writer.execute("BEGIN IMMEDIATE")
        writer.execute("COMMIT")


def test_maximum_batch_size_and_selected_batch_bound(tmp_path):
    path = tmp_path / "max.db"
    original = batch()
    # 1000 safe rejection summaries fit P3a's unchanged 20k structural-node budget.
    # 1000 full normalized observations exceed that separate input budget.
    maximum = build_batch(
        str(uuid4()),
        original.captured_at,
        tuple(RecordError(index, "invalid_field") for index in range(1000)),
        original.manifest,
    )
    storage.persist(path, maximum)
    tokens = [maximum.batch_id]
    for _ in range(32):
        empty = build_batch(str(uuid4()), original.captured_at, (), original.manifest)
        storage.persist(path, empty)
        tokens.append(empty.batch_id)
    snapshots = storage.read_snapshots(path, tuple(tokens))
    assert len(snapshots) == 33
    assert sum(len(snapshot.records) for snapshot in snapshots) == 1000
