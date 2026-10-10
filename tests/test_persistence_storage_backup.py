"""Consistent backup/restore and hostile-path drills use only temporary files."""

import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest

from card_market_tracker.persistence import sqlite_repository as storage
from card_market_tracker.persistence.errors import PersistenceError
from card_market_tracker.persistence.input import read_persistence

FIXTURES = Path(__file__).parent / "fixtures"


def admitted():
    return read_persistence(
        FIXTURES / "synthetic_persistence_mixed.json", FIXTURES / "synthetic_manifest.json"
    )


def assert_category(category, action):
    with pytest.raises(PersistenceError) as error:
        action()
    assert error.value.category == category


@pytest.fixture
def source(tmp_path):
    path = tmp_path / "source.db"
    storage.persist(path, admitted())
    return path


def test_backup_restore_reopen_exact_content_ids_candidates_replay(source, tmp_path):
    original = storage.query(source)
    backup = tmp_path / "backup.db"
    restored = tmp_path / "restored.db"
    assert storage.backup(source, backup)["result"] == "ok"
    assert storage.restore(backup, restored)["result"] == "ok"
    assert storage.query(backup) == storage.query(restored) == original
    for path in (backup, restored):
        assert storage.verify(path)["schema_version"] == 1
        replay = storage.persist(path, admitted())
        assert replay.result == "replay"
        assert replay.committed_entities == replay.committed_observations == 0
        assert replay.first_persisted_at == original["records"][0]["first_persisted_at"]
    process = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys;from pathlib import Path;"
            "from card_market_tracker.persistence.sqlite_repository import verify;"
            "assert verify(Path(sys.argv[1]))['result']=='ok'",
            str(restored),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert process.stdout == ""


@pytest.mark.parametrize("operation", [storage.backup, storage.restore])
@pytest.mark.parametrize("destination_kind", ["source", "existing", "directory", "sidecar"])
def test_copy_never_overwrites_existing_file_directory_or_sidecar(
    source, tmp_path, operation, destination_kind
):
    destination = tmp_path / "destination.db"
    preserved = None
    if destination_kind == "source":
        destination = source
        preserved = source.read_bytes()
    elif destination_kind == "existing":
        destination.write_bytes(b"preserve existing user file")
        preserved = destination.read_bytes()
    elif destination_kind == "directory":
        destination.mkdir()
    else:
        Path(str(destination) + "-journal").write_bytes(b"preserve existing user journal")
    assert_category("unsafe_destination", lambda: operation(source, destination))
    if preserved is not None:
        assert destination.read_bytes() == preserved
    if destination_kind == "sidecar":
        assert not destination.exists()
        assert Path(str(destination) + "-journal").read_bytes() == b"preserve existing user journal"
    assert storage.verify(source)["result"] == "ok"


@pytest.mark.parametrize("suffix", ["-journal", "-wal", "-shm"])
def test_new_database_refuses_preexisting_sqlite_sidecars(tmp_path, suffix):
    path = tmp_path / "new.db"
    sidecar = Path(str(path) + suffix)
    sidecar.write_bytes(b"unrelated file")
    assert_category("unsafe_destination", lambda: storage.persist(path, admitted()))
    assert not path.exists() and sidecar.read_bytes() == b"unrelated file"


def test_hardlinks_refused_for_sources_writes_and_destinations(source, tmp_path):
    alias = tmp_path / "hardlink.db"
    os.link(source, alias)
    before = source.read_bytes()
    for operation in (storage.query, storage.initialize):
        assert_category("unsafe_destination", lambda operation=operation: operation(alias))
    assert_category("unsafe_destination", lambda: storage.backup(alias, tmp_path / "new.db"))
    assert_category("unsafe_destination", lambda: storage.restore(source, alias))
    assert source.read_bytes() == before


def test_existing_database_hardlinked_journal_is_not_modified(source, tmp_path):
    unrelated = tmp_path / "unrelated"
    unrelated.write_bytes(b"journal not owned by database")
    sidecar = Path(str(source) + "-journal")
    os.link(unrelated, sidecar)
    before = source.read_bytes()
    assert_category("unsafe_destination", lambda: storage.initialize(source))
    assert (
        source.read_bytes() == before and unrelated.read_bytes() == b"journal not owned by database"
    )


def test_symlink_final_ancestor_dangling_and_journal_refused(source, tmp_path):
    link = tmp_path / "link.db"
    try:
        link.symlink_to(source)
    except OSError as error:
        pytest.skip(f"Host cannot create symlinks: {type(error).__name__}")
    assert_category("unsafe_destination", lambda: storage.query(link))
    assert_category("unsafe_destination", lambda: storage.backup(source, link))
    dangling = tmp_path / "dangling.db"
    dangling.symlink_to(tmp_path / "absent.db")
    assert_category("unsafe_destination", lambda: storage.backup(source, dangling))
    parent = tmp_path / "redirected"
    parent.symlink_to(tmp_path, target_is_directory=True)
    assert_category("unsafe_destination", lambda: storage.restore(source, parent / "new.db"))
    assert not (tmp_path / "new.db").exists()
    journal = Path(str(source) + "-journal")
    journal.symlink_to(tmp_path / "absent-journal")
    assert_category("unsafe_destination", lambda: storage.initialize(source))


@pytest.mark.skipif(os.name != "nt", reason="Windows junction requires Windows host")
def test_windows_junction_ancestor_refused(source, tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    junction = tmp_path / "junction"
    process = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(junction), str(target)],
        capture_output=True,
        text=True,
    )
    assert process.returncode == 0, process.stderr
    assert junction.is_junction()
    assert_category("unsafe_destination", lambda: storage.backup(source, junction / "copy.db"))
    assert not (target / "copy.db").exists()
    junction.rmdir()
    assert target.is_dir()


def test_sqlite_backup_reads_committed_snapshot_during_uncommitted_writer(source, tmp_path):
    expected = storage.query(source)
    holder = sqlite3.connect(source, autocommit=True)
    try:
        holder.execute("BEGIN IMMEDIATE")
        holder.execute("DELETE FROM records")
        destination = tmp_path / "while-writing.db"
        assert storage.backup(source, destination)["result"] == "ok"
        assert storage.query(destination) == expected
    finally:
        holder.execute("ROLLBACK")
        holder.close()


def test_backup_api_busy_retries_have_total_deadline_and_remove_partial(
    source, tmp_path, monkeypatch
):
    holder = sqlite3.connect(source, autocommit=True)
    original = storage._reserve

    def lock_after_source_verification(path):
        reserved = original(path)
        holder.execute("BEGIN EXCLUSIVE")
        return reserved

    destination = tmp_path / "contended.db"
    monkeypatch.setattr(storage, "_reserve", lock_after_source_verification)
    try:
        start = time.monotonic()
        assert_category(
            "storage_timeout", lambda: storage.backup(source, destination, timeout=0.12)
        )
        assert time.monotonic() - start < 1.5
        assert not destination.exists()
        assert not any(path.exists() for path in storage._sidecars(destination))
    finally:
        holder.execute("ROLLBACK")
        holder.close()
    assert storage.verify(source)["result"] == "ok"


def test_backup_source_lock_has_finite_safe_failure_without_destination(source, tmp_path):
    holder = sqlite3.connect(source, autocommit=True)
    destination = tmp_path / "never-created.db"
    try:
        holder.execute("BEGIN EXCLUSIVE")
        start = time.monotonic()
        assert_category("storage_locked", lambda: storage.backup(source, destination, timeout=0.12))
        assert time.monotonic() - start < 1.5
        assert not destination.exists()
    finally:
        holder.execute("ROLLBACK")
        holder.close()


def test_simulated_backup_verification_io_failure_removes_owned_copy_only(
    source, tmp_path, monkeypatch
):
    destination = tmp_path / "incomplete.db"
    preserved = tmp_path / "preserve.db"
    preserved.write_bytes(b"untouched unrelated backup")
    original = storage._verify
    checks = []

    def injected(connection, budget):
        checks.append(connection.execute("SELECT count(*) FROM records").fetchone()[0])
        original(connection, budget)
        if len(checks) == 2:
            raise sqlite3.OperationalError("simulated disk-full destination verification failure")

    monkeypatch.setattr(storage, "_verify", injected)
    assert_category("storage_io", lambda: storage.backup(source, destination))
    assert checks == [3, 3]  # An actual SQLite backup completed before failure injection.
    assert not destination.exists() and preserved.read_bytes() == b"untouched unrelated backup"


def test_missing_corrupt_foreign_source_refuses_to_make_backup(tmp_path):
    for kind in ("missing", "corrupt", "foreign"):
        source = tmp_path / f"{kind}.db"
        if kind == "corrupt":
            source.write_bytes(b"corrupt fixture")
        elif kind == "foreign":
            with sqlite3.connect(source) as connection:
                connection.execute("CREATE TABLE foreign_data(x)")
        destination = tmp_path / f"{kind}-copy.db"
        expected = {
            "missing": "storage_io",
            "corrupt": "storage_corrupt",
            "foreign": "storage_schema",
        }
        assert_category(
            expected[kind],
            lambda source=source, destination=destination: storage.backup(source, destination),
        )
        assert not destination.exists()


def test_destination_parent_missing_io_is_safe_and_does_not_affect_source(source, tmp_path):
    destination = tmp_path / "missing" / "copy.db"
    before = storage.query(source)
    assert_category("storage_io", lambda: storage.backup(source, destination))
    assert storage.query(source) == before


def test_failed_copy_cleanup_does_not_remove_replaced_destination(tmp_path):
    path = tmp_path / "reserved.db"
    identity = storage._reserve(path)
    replacement = tmp_path / "replacement.db"
    replacement.write_bytes(b"replacement file owned by another operation")
    os.replace(replacement, path)
    storage._remove_owned(path, identity)
    assert path.read_bytes() == b"replacement file owned by another operation"
