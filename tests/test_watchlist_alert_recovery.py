"""DB author recovery probes: independent folds, exclusive publication and safe residue."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pytest
from test_watchlist_alert_storage import category
from test_watchlist_alert_storage import database as _database
from test_watchlist_alert_storage import evidence as _evidence
from test_watchlist_alert_storage import populated as _populated

from card_market_tracker.watchlist_alerts import policy, storage

database, evidence, populated = _database, _evidence, _populated


@pytest.mark.parametrize("operation", ["backup", "restore"])
def test_three_fresh_connections_and_reconstructions_before_fsync_publication(
    populated, tmp_path, monkeypatch, operation
):
    source, _, _ = populated
    before = source.read_bytes()
    destination = tmp_path / "copy.db"
    events, connections, preparations = [], [], []
    fold, prepare, fsync, publish = (
        storage._verify,
        policy.prepare,
        storage._fsync,
        storage._publish,
    )
    budget = storage.Budget(5)

    def prepared(*args, **kwargs):
        preparations.append(None)
        return prepare(*args, **kwargs)

    def verified(db, supplied):
        assert supplied is budget and not destination.exists()
        connections.append(db)
        start = len(preparations)
        result = fold(db, supplied)
        assert len(preparations) > start
        events.append("fold")
        return result

    def synced(path, identity):
        assert events == ["fold"] * 3 and not destination.exists()
        events.append("fsync")
        return fsync(path, identity)

    def published(path, target, identity):
        assert events == ["fold"] * 3 + ["fsync"]
        events.append("publish")
        return publish(path, target, identity)

    with monkeypatch.context() as patch:
        patch.setattr(policy, "prepare", prepared)
        patch.setattr(storage, "_verify", verified)
        patch.setattr(storage, "_fsync", synced)
        patch.setattr(storage, "_publish", published)
        assert getattr(storage, operation)(source, destination, _budget=budget)["counts"] == {
            "alerts": 1,
            "evidence": 1,
        }
    assert len({id(db) for db in connections}) == 3
    assert events == ["fold"] * 3 + ["fsync", "publish"]
    assert storage.verify(destination)["counts"] == {"alerts": 1, "evidence": 1}
    assert source.read_bytes() == before
    assert not list(tmp_path.glob(".cmt-watchlist-alert-outbox-*.tmp"))


def test_corruption_between_copy_and_reopened_fold_fails_before_exposure(
    populated, tmp_path, monkeypatch
):
    source, _, _ = populated
    before = source.read_bytes()
    destination = tmp_path / "corrupted.db"
    connect = storage._connect
    changed = []

    @contextmanager
    def corrupted(path, budget, *, writable=False):
        if path.name.endswith(".tmp") and not writable:
            with sqlite3.connect(path) as db:
                db.execute("DROP TRIGGER watchlist_alerts_no_update")
                db.execute(
                    "UPDATE watchlist_alerts SET message_text=?,message_sha256=?",
                    ("rehashed invalid rendering", policy.digest("rehashed invalid rendering")),
                )
                db.execute(
                    next(
                        s
                        for s in storage.schema.STATEMENTS
                        if "CREATE TRIGGER watchlist_alerts_no_update" in s
                    )
                )
            db.close()
            changed.append(path)
        with connect(path, budget, writable=writable) as db:
            yield db

    monkeypatch.setattr(storage, "_connect", corrupted)
    category("storage_corrupt", lambda: storage.backup(source, destination))
    assert len(changed) == 1 and not destination.exists()
    assert not list(tmp_path.glob(".cmt-watchlist-alert-outbox-*.tmp"))
    assert source.read_bytes() == before


@pytest.mark.parametrize("stage", [1, 2, 3])
@pytest.mark.parametrize("operation", ["backup", "restore"])
def test_shared_deadline_at_each_fold_cleans_only_reserved_copy(
    populated, tmp_path, monkeypatch, stage, operation
):
    source, _, _ = populated
    before = source.read_bytes()
    destination = tmp_path / "timeout.db"
    fold, calls = storage._verify, []
    budget = storage.Budget(5)

    def expired(db, supplied):
        assert supplied is budget
        calls.append(db)
        if len(calls) == stage:
            supplied.deadline = 0
        return fold(db, supplied)

    monkeypatch.setattr(storage, "_verify", expired)
    category(
        "storage_timeout", lambda: getattr(storage, operation)(source, destination, _budget=budget)
    )
    assert len(calls) == stage and not destination.exists()
    assert not list(tmp_path.glob(".cmt-watchlist-alert-outbox-*.tmp"))
    assert source.read_bytes() == before


@pytest.mark.parametrize("fault", ["fsync", "link", "exists"])
@pytest.mark.parametrize("operation", ["backup", "restore"])
def test_fsync_link_and_exclusive_creation_failures_keep_source(
    populated, tmp_path, monkeypatch, fault, operation
):
    source, _, _ = populated
    before = source.read_bytes()
    destination = tmp_path / "failed.db"

    def denied(*args, **kwargs):
        if fault == "exists":
            raise FileExistsError("controlled publication collision")
        raise OSError("controlled filesystem failure")

    if fault == "fsync":
        monkeypatch.setattr(storage.os, "fsync", denied)
    else:
        monkeypatch.setattr(storage.os, "link", denied)
    category(
        "unsafe_destination" if fault == "exists" else "storage_io",
        lambda: getattr(storage, operation)(source, destination),
    )
    assert not destination.exists() and source.read_bytes() == before
    assert not list(tmp_path.glob(".cmt-watchlist-alert-outbox-*.tmp"))


@pytest.mark.parametrize("operation", ["backup", "restore"])
def test_post_link_unlink_failure_safely_compensates_owned_destination(
    populated, tmp_path, monkeypatch, operation
):
    source, _, _ = populated
    before = source.read_bytes()
    destination = tmp_path / "unlink-failure.db"
    unlink, attempts = Path.unlink, []

    def fail_once(path, *args, **kwargs):
        if path.name.endswith(".tmp") and not attempts:
            attempts.append(path)
            assert destination.exists()
            assert path.stat().st_nlink == destination.stat().st_nlink == 2
            raise OSError("controlled first unlink failure")
        return unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_once)
    category("storage_io", lambda: getattr(storage, operation)(source, destination))
    assert len(attempts) == 1 and not destination.exists()
    assert not list(tmp_path.glob(".cmt-watchlist-alert-outbox-*.tmp"))
    assert source.read_bytes() == before


@pytest.mark.parametrize("side", ["provisional", "destination"])
@pytest.mark.parametrize("operation", ["backup", "restore"])
def test_post_link_sidecar_preserves_both_names_and_recovery_evidence(
    populated, tmp_path, monkeypatch, side, operation
):
    source, _, _ = populated
    before = source.read_bytes()
    destination = tmp_path / "sidecar.db"
    unlink, observed = Path.unlink, []

    def interfere(path, *args, **kwargs):
        if path.name.endswith(".tmp") and not observed:
            observed.append(path)
            name = path if side == "provisional" else destination
            Path(str(name) + "-journal").write_bytes(b"preserve foreign recovery evidence")
            raise OSError("controlled unlink with sidecar")
        return unlink(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "unlink", interfere)
        category("storage_io", lambda: getattr(storage, operation)(source, destination))
    provisional = observed[0]
    assert provisional.exists() and destination.exists()
    assert provisional.stat().st_nlink == destination.stat().st_nlink == 2
    name = provisional if side == "provisional" else destination
    assert Path(str(name) + "-journal").read_bytes() == b"preserve foreign recovery evidence"
    assert source.read_bytes() == before


def test_post_link_foreign_replacement_is_never_deleted(populated, tmp_path, monkeypatch):
    source, _, _ = populated
    destination = tmp_path / "foreign.db"
    unlink, changed = Path.unlink, []

    def replace(path, *args, **kwargs):
        if path.name.endswith(".tmp") and not changed:
            changed.append(path)
            unlink(destination)
            destination.write_bytes(b"foreign replacement")
            raise OSError("controlled substituted destination")
        return unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", replace)
    category("storage_io", lambda: storage.backup(source, destination))
    assert destination.read_bytes() == b"foreign replacement"
    assert not changed[0].exists()


def test_post_link_extra_hardlink_is_preserved(populated, tmp_path, monkeypatch):
    source, _, _ = populated
    destination, extra = tmp_path / "destination.db", tmp_path / "extra.db"
    unlink, observed = Path.unlink, []

    def extra_link(path, *args, **kwargs):
        if path.name.endswith(".tmp") and not observed:
            observed.append(path)
            os.link(path, extra)
            raise OSError("controlled extra link")
        return unlink(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "unlink", extra_link)
        category("storage_io", lambda: storage.backup(source, destination))
    assert all(p.exists() and p.stat().st_nlink == 3 for p in (observed[0], destination, extra))


def test_compensation_failure_preserves_original_exception_identity(tmp_path, monkeypatch):
    provisional, destination = tmp_path / "owned.tmp", tmp_path / "owned.db"
    identity = storage.paths._reserve(provisional)
    original = OSError("primary unlink failure")
    unlink = Path.unlink

    def denied(path, *args, **kwargs):
        if path == provisional:
            raise original
        if path == destination:
            raise OSError("secondary compensation failure")
        return unlink(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "unlink", denied)
        with pytest.raises(OSError) as caught:
            storage._publish(provisional, destination, identity)
    assert caught.value is original
    assert provisional.stat().st_nlink == destination.stat().st_nlink == 2


def test_deadline_after_fsync_prevents_publication(populated, tmp_path, monkeypatch):
    source, _, _ = populated
    destination = tmp_path / "late.db"
    budget = storage.Budget(5)
    fsync = storage._fsync

    def expired(path, identity):
        fsync(path, identity)
        budget.deadline = 0

    monkeypatch.setattr(storage, "_fsync", expired)
    category("storage_timeout", lambda: storage.backup(source, destination, _budget=budget))
    assert not destination.exists()
    assert not list(tmp_path.glob(".cmt-watchlist-alert-outbox-*.tmp"))


def test_deadline_after_publication_reports_failure_but_preserves_complete_copy(
    populated, tmp_path, monkeypatch
):
    source, _, _ = populated
    destination = tmp_path / "published.db"
    budget, publish = storage.Budget(5), storage._publish

    def expired(path, target, identity):
        publish(path, target, identity)
        budget.deadline = 0

    monkeypatch.setattr(storage, "_publish", expired)
    category("storage_timeout", lambda: storage.backup(source, destination, _budget=budget))
    assert storage.verify(destination)["counts"] == {"alerts": 1, "evidence": 1}


def test_existing_destination_and_sidecar_never_overwritten(populated, tmp_path):
    source, _, _ = populated
    destination = tmp_path / "existing.db"
    destination.write_bytes(b"foreign")
    category("unsafe_destination", lambda: storage.restore(source, destination))
    assert destination.read_bytes() == b"foreign"
    destination.unlink()
    sidecar = Path(str(destination) + "-wal")
    sidecar.write_bytes(b"foreign wal")
    category("unsafe_destination", lambda: storage.backup(source, destination))
    assert sidecar.read_bytes() == b"foreign wal" and not destination.exists()
