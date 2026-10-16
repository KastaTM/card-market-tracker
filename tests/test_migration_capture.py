"""Exact v1 migration, recovery and explicit version boundaries."""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from card_market_tracker.persistence import schema
from card_market_tracker.persistence import sqlite_repository as storage
from card_market_tracker.persistence.capture import query_capture
from card_market_tracker.persistence.errors import PersistenceError
from card_market_tracker.persistence.input import read_persistence

FIXTURES = Path(__file__).parent / "fixtures"


def seed_v1(path):
    with closing(sqlite3.connect(path, autocommit=True)) as connection:
        for statement in schema.V1_STATEMENTS:
            connection.execute(statement)
        connection.execute("INSERT INTO storage_metadata VALUES (1,?,1)", (schema.OWNER,))
        connection.execute(f"PRAGMA application_id={schema.APPLICATION_ID}")
        connection.execute("PRAGMA user_version=1")
    batch = read_persistence(
        FIXTURES / "synthetic_persistence_valid.json", FIXTURES / "synthetic_manifest.json"
    )
    storage.persist(path, batch)
    return batch


def raw_rows(path):
    with closing(sqlite3.connect(path)) as connection:
        return tuple(
            tuple(connection.execute(f"SELECT * FROM {table} ORDER BY 1,2"))
            for table in ("entities", "batches", "records")
        )


def test_explicit_migration_preserves_rows_fingerprints_and_backup(tmp_path):
    path, backup = tmp_path / "old.db", tmp_path / "backup.db"
    batch = seed_v1(path)
    original = path.read_bytes()
    before = raw_rows(path)
    assert storage.initialize(path)["schema_version"] == 1
    assert storage.verify(path)["schema_version"] == 1
    assert path.read_bytes() == original
    assert query_capture(path, batch.batch_id)["evidence_state"] == "legacy_unverified"
    assert storage.migrate(path, backup)["schema_version"] == 2
    assert backup.read_bytes() == original
    assert raw_rows(path) == raw_rows(backup) == before
    assert storage.verify(path)["schema_version"] == 2
    assert query_capture(path, batch.batch_id)["capture"]["scope"] is None
    assert storage.persist(path, batch).result == "replay"
    storage.restore(backup, tmp_path / "recovery.db")
    assert storage.verify(tmp_path / "recovery.db")["schema_version"] == 1


@pytest.mark.parametrize(
    "point",
    [
        "DROP TRIGGER record_context",
        "INSERT INTO records SELECT * FROM records_v1",
        "PRAGMA user_version=2",
        "COMMIT",
    ],
)
def test_failure_rolls_back_ddl_and_keeps_verified_backup(tmp_path, monkeypatch, point):
    path, backup = tmp_path / "old.db", tmp_path / "backup.db"
    seed_v1(path)
    before = path.read_bytes()
    execute = storage._execute
    fired = False

    def fail(connection, budget, sql, values=()):
        nonlocal fired
        if sql == point and not fired:
            fired = True
            raise PersistenceError("storage_io")
        return execute(connection, budget, sql, values)

    monkeypatch.setattr(storage, "_execute", fail)
    with pytest.raises(PersistenceError):
        storage.migrate(path, backup)
    assert fired
    assert path.read_bytes() == before
    assert backup.read_bytes() == before
    assert storage.verify(path)["schema_version"] == 1


def test_backup_collision_and_held_reader_leave_original(tmp_path):
    path, backup = tmp_path / "old.db", tmp_path / "backup.db"
    seed_v1(path)
    before = path.read_bytes()
    backup.write_bytes(b"existing")
    with pytest.raises(PersistenceError, match="unsafe_destination"):
        storage.migrate(path, backup)
    assert path.read_bytes() == before and backup.read_bytes() == b"existing"
    backup.unlink()
    with closing(sqlite3.connect(path, autocommit=True)) as reader:
        reader.execute("BEGIN")
        reader.execute("SELECT * FROM batches").fetchall()
        with pytest.raises(PersistenceError, match="storage_locked"):
            storage.migrate(path, backup, timeout=0.05)
    assert path.read_bytes() == before and not backup.exists()


def test_v2_migration_rejected_without_destination_creation(tmp_path):
    path, backup = tmp_path / "new.db", tmp_path / "backup.db"
    storage.initialize(path)
    before = path.read_bytes()
    with pytest.raises(PersistenceError, match="storage_schema"):
        storage.migrate(path, backup)
    assert path.read_bytes() == before and not backup.exists()


@pytest.mark.parametrize("point", ["INSERT INTO records SELECT * FROM records_v1", "COMMIT"])
def test_process_termination_rolls_back_hot_journal(tmp_path, point):
    import subprocess
    import sys

    path, backup = tmp_path / "old.db", tmp_path / "backup.db"
    seed_v1(path)
    before = raw_rows(path)
    script = """
import os, sys
from pathlib import Path
from card_market_tracker.persistence import sqlite_repository as db
original = db._execute
def terminate(connection, budget, sql, values=()):
    if sql == sys.argv[3]:
        os._exit(71)
    return original(connection, budget, sql, values)
db._execute = terminate
db.migrate(Path(sys.argv[1]), Path(sys.argv[2]))
"""
    process = subprocess.run(
        [sys.executable, "-c", script, str(path), str(backup), point], check=False
    )
    assert process.returncode == 71
    # A writable open lets SQLite recover its own journal; no manual journal removal.
    assert storage.initialize(path)["schema_version"] == 1
    assert storage.verify(path)["schema_version"] == 1
    assert raw_rows(path) == raw_rows(backup) == before
