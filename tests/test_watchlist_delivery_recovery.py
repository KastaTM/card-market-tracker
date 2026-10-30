"""P8d DB author tests: three folds, fault boundaries and global quarantine."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pytest
from test_watchlist_delivery_storage import claim, outcome, prepared

from card_market_tracker.watchlist_delivery import application as app
from card_market_tracker.watchlist_delivery import storage
from card_market_tracker.watchlist_delivery.errors import DeliveryError


def test_three_independent_full_folds_and_restore_quarantine(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    context = prepared(tmp_path / "one")
    path = context["ledger"]
    before = path.read_bytes()
    original = storage._fold
    seen = []

    def counted(db: sqlite3.Connection, budget: Any) -> Any:
        seen.append(db)
        return original(db, budget)

    monkeypatch.setattr(storage, "_fold", counted)
    backup = tmp_path / "backup.db"
    storage.backup(path, backup)
    assert len(seen) == 3 and len({id(db) for db in seen}) == 3
    seen.clear()
    restored = tmp_path / "restored.db"
    storage.restore(backup, restored)
    assert len(seen) == 3 and len({id(db) for db in seen}) == 3
    assert storage.verify(restored)["send_quarantined"] is True
    for did in (context["did"], "wtdl1_" + "f" * 64):
        with pytest.raises(DeliveryError, match="send_quarantined"):
            app.send(restored, did)
    assert path.read_bytes() == before
    assert storage.verify(path)["counts"] == storage.verify(backup)["counts"]


def test_old_empty_restore_blocks_later_and_new_prepared_deliveries(tmp_path: Path) -> None:
    empty = tmp_path / "empty.db"
    storage.initialize(empty)
    storage.destination_add(empty, "private", 1, 2, operator_private_owned=True)
    restored = tmp_path / "restored.db"
    storage.restore(empty, restored)
    later = prepared(tmp_path / "one", ledger=restored)
    assert later["result"]["delivery"]["state"] == "ready"
    with pytest.raises(DeliveryError, match="send_quarantined"):
        app.send(restored, later["did"])
    with pytest.raises(DeliveryError, match="send_quarantined"):
        app.send(restored, "wtdl1_" + "a" * 64)


def test_recover_requires_quiescence_and_late_result_is_fenced(tmp_path: Path) -> None:
    context = prepared(tmp_path / "one")
    budget, claimed = claim(context)
    with pytest.raises(DeliveryError, match="invalid_field"):
        storage.recover(context["ledger"], context["did"])
    result = storage.recover(context["ledger"], context["did"], worker_quiesced=True)
    assert result["delivery"]["state"] == "uncertain"
    assert result["delivery"]["last_error_category"] == "recovered"
    with pytest.raises(DeliveryError, match="stale_attempt"):
        storage._finish(context["ledger"], context["did"], claimed["_handle"], outcome(), budget)
    assert storage.verify(context["ledger"])["counts"]["results"] == 1


def test_copy_logical_rows_must_match_even_when_counts_match(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    context = prepared(tmp_path / "one")
    original = storage._fold
    calls = 0

    def changed(db: sqlite3.Connection, budget: Any) -> Any:
        nonlocal calls
        calls += 1
        result = original(db, budget)
        if calls == 2:
            return *result[:3], "f" * 64
        return result

    monkeypatch.setattr(storage, "_fold", changed)
    target = tmp_path / "bad-copy.db"
    with pytest.raises(DeliveryError, match="storage_corrupt"):
        storage.backup(context["ledger"], target)
    assert not target.exists()
    assert not list(tmp_path.glob(".cmt-watchlist-delivery-*"))


def test_fsync_failure_prevents_publication_and_preserves_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    context = prepared(tmp_path / "one")
    before = context["ledger"].read_bytes()
    target = tmp_path / "failed.db"

    def denied(*args: Any) -> None:
        raise OSError("injected disk full")

    monkeypatch.setattr(storage, "_fsync", denied)
    with pytest.raises(DeliveryError, match="storage_io"):
        storage.backup(context["ledger"], target)
    assert not target.exists() and context["ledger"].read_bytes() == before


def test_foreign_sidecar_residue_is_never_deleted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    context = prepared(tmp_path / "one")
    original = storage._fsync
    evidence = []

    def sidecar(path: Path, identity: tuple[int, int]) -> None:
        original(path, identity)
        foreign = path.with_name(path.name + "-journal")
        foreign.write_bytes(b"foreign evidence")
        evidence.append(foreign)

    monkeypatch.setattr(storage, "_fsync", sidecar)
    with pytest.raises(DeliveryError):
        storage.backup(context["ledger"], tmp_path / "failed.db")
    assert evidence and evidence[0].read_bytes() == b"foreign evidence"
    assert evidence[0].with_name(evidence[0].name.removesuffix("-journal")).exists()


def test_backup_existing_target_and_hardlinks_fail(tmp_path: Path) -> None:
    context = prepared(tmp_path / "one")
    target = tmp_path / "existing.db"
    target.write_bytes(b"foreign")
    with pytest.raises(DeliveryError, match="unsafe_destination"):
        storage.backup(context["ledger"], target)
    assert target.read_bytes() == b"foreign"
    linked = tmp_path / "linked.db"
    linked.hardlink_to(context["ledger"])
    with pytest.raises(DeliveryError, match="unsafe_destination"):
        storage.verify(context["ledger"])


def test_post_link_unlink_failure_compensates_only_owned_final(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    provisional = tmp_path / "provisional.db"
    identity = storage.paths._reserve(provisional)
    provisional.write_bytes(b"owned bytes")
    destination = tmp_path / "final.db"
    unlink = Path.unlink

    def denied(path: Path, *args: Any, **kwargs: Any) -> None:
        if path == provisional:
            raise OSError("injected provisional unlink refusal")
        unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", denied)
    with pytest.raises(OSError):
        storage._publish(provisional, destination, identity)
    assert not destination.exists() and provisional.read_bytes() == b"owned bytes"


def test_post_link_foreign_sidecar_prevents_destructive_compensation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    provisional = tmp_path / "provisional.db"
    identity = storage.paths._reserve(provisional)
    provisional.write_bytes(b"owned bytes")
    destination = tmp_path / "final.db"
    unlink = Path.unlink

    def denied(path: Path, *args: Any, **kwargs: Any) -> None:
        if path == provisional:
            destination.with_name(destination.name + "-journal").write_bytes(b"foreign evidence")
            raise OSError("injected provisional unlink refusal")
        unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", denied)
    with pytest.raises(OSError):
        storage._publish(provisional, destination, identity)
    assert destination.read_bytes() == provisional.read_bytes() == b"owned bytes"
    assert destination.with_name(destination.name + "-journal").read_bytes() == b"foreign evidence"


def test_sql_claim_result_and_cache_are_immutable(tmp_path: Path) -> None:
    context = prepared(tmp_path / "one")
    budget, claimed = claim(context)
    storage._finish(context["ledger"], context["did"], claimed["_handle"], outcome(), budget)
    with sqlite3.connect(context["ledger"]) as db:
        for statement in (
            "UPDATE wtd_claims SET owner='" + "f" * 64 + "'",
            "DELETE FROM wtd_results",
            "UPDATE wtd_state SET state='ready'",
            "UPDATE wtd_metadata SET send_quarantined=-1",
        ):
            with pytest.raises(sqlite3.IntegrityError):
                db.execute(statement)
        assert db.execute("SELECT count(*) FROM wtd_results").fetchone() == (1,)
    storage.verify(context["ledger"])
