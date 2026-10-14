"""Reviewed real admission, direct-object attacks and synthetic scope evidence."""

import json
import sqlite3
from contextlib import closing
from dataclasses import replace
from uuid import uuid4

import pytest

from card_market_tracker.catalog.ingestion import ExternalReference, Observation, RecordError
from card_market_tracker.discovery.errors import DiscoveryError
from card_market_tracker.persistence import sqlite_repository as storage
from card_market_tracker.persistence.application import build_batch
from card_market_tracker.persistence.capture import persist_bundle, persist_capture, query_capture
from card_market_tracker.persistence.errors import PersistenceError
from card_market_tracker.pinned_repository import (
    BundleError,
    VerifiedBundle,
    approved_bundle_document,
    observations,
    validate_bundle,
)

CAPTURE = "2026-10-14T17:53:09.118954Z"


def manifest():
    token = "f9743b79-20e3-4815-98d3-bb06f0c8195f"
    return {
        "version": 1,
        "entities": [{"kind": "set", "cmt_id": token}],
        "bindings": [
            {
                "reference": {
                    "namespace": "tcgdex_repository",
                    "kind": "set",
                    "external_id": "swsh3",
                    "language": language,
                    "variant": "unknown",
                },
                "cmt_id": token,
                "reason": "Synthetic curator mapping for offline integration",
            }
            for language in ("es", "en")
        ],
    }


def test_pinned_capture_reopen_replay_restore_and_discovery_boundary(tmp_path):
    path, backup, restored = (tmp_path / name for name in ("history.db", "backup.db", "restore.db"))
    token = str(uuid4())
    document = approved_bundle_document()
    result = persist_bundle(path, document, token, manifest())
    assert (result.accepted_count, result.candidate_count, result.rejected_count) == (2, 2, 0)
    original = query_capture(path, token)
    assert original["evidence_state"] == "verified_local_pinned_bundle"
    assert original["capture"]["scope"]["counts"] == {
        "input": 4,
        "accepted": 2,
        "candidates": 2,
        "rejected": 0,
    }
    assert len(original["capture"]["scope"]["units"]) == 4
    assert {row["observation"]["provenance"] for row in original["records"]} == {"observed"}
    first = result.first_persisted_at
    assert (
        persist_bundle(path, validate_bundle(document), token, manifest()).first_persisted_at
        == first
    )
    assert storage.verify(path)["schema_version"] == 2
    assert len(storage.query(path)["records"]) == 4
    with pytest.raises(DiscoveryError, match="synthetic_only"):
        storage.read_snapshots(path, (token,))
    storage.backup(path, backup)
    storage.restore(backup, restored)
    assert query_capture(restored, token) == original
    assert persist_bundle(restored, document, token, manifest()).result == "replay"


@pytest.mark.parametrize("attack", ["name", "clock", "revision", "empty", "extra", "direct"])
def test_public_object_and_document_bypass_never_creates_database(tmp_path, attack):
    document = approved_bundle_document()
    if attack == "name":
        document["projection"][0]["name"] = "Synthetic tampering"
    elif attack == "clock":
        document["captured_at"] = "2026-10-15T00:00:00.000000Z"
    elif attack == "revision":
        document["revision"] = "0" * 40
    elif attack == "empty":
        document["projection"] = []
    else:
        document["not_authorized"] = "synthetic excluded field"
    value = VerifiedBundle(json.dumps(document)) if attack == "direct" else document
    path = tmp_path / "never.db"
    with pytest.raises(BundleError):
        persist_bundle(path, value, str(uuid4()), manifest())
    assert not path.exists()


def test_manifest_replay_conflict_and_synthetic_guard(tmp_path):
    path = tmp_path / "history.db"
    token = str(uuid4())
    bundle = validate_bundle(approved_bundle_document())
    persist_bundle(path, bundle, token, manifest())
    before = path.read_bytes()
    changed = manifest()
    changed["bindings"].pop()
    with pytest.raises(PersistenceError, match="replay_conflict"):
        persist_bundle(path, bundle, token, changed)
    assert path.read_bytes() == before
    with pytest.raises(PersistenceError, match="synthetic_only"):
        build_batch(str(uuid4()), CAPTURE, observations(bundle), manifest())


def synthetic_batch(items=()):
    return build_batch(str(uuid4()), CAPTURE, items, {"version": 1, "entities": [], "bindings": []})


def scope(batch, *, complete=True, outcome=None):
    return {
        "version": 1,
        "acquired_at": CAPTURE,
        "captured_at": CAPTURE,
        "outcome": outcome or ("complete" if complete else "partial"),
        "units": [
            {
                "namespace": "synthetic_scope",
                "kind": "set",
                "language": "es",
                "selector": "explicit selection",
                "selected": ["synthetic/a", "synthetic/b"],
                "completed": ["synthetic/a", "synthetic/b"] if complete else ["synthetic/a"],
                "record_indexes": list(range(len(batch.records))),
            }
        ],
    }


@pytest.mark.parametrize("case", ["empty", "candidate", "rejected", "partial", "failed"])
def test_exact_generic_scopes_persist_empty_partial_rejected(tmp_path, case):
    item = Observation(
        "set",
        ExternalReference("synthetic_scope", "set", "a", "es"),
        "Synthetic set",
        captured_at=CAPTURE,
        provenance="synthetic",
    )
    batch = synthetic_batch(
        (item,)
        if case in ("candidate", "partial")
        else (RecordError(0, "invalid_field"),)
        if case == "rejected"
        else ()
    )
    evidence = scope(
        batch,
        complete=case not in ("partial", "failed"),
        outcome="failed" if case == "failed" else None,
    )
    path = tmp_path / "synthetic.db"
    persist_capture(path, batch, evidence)
    capture = query_capture(path, batch.batch_id)
    assert capture["evidence_state"] == "producer_declared"
    assert capture["capture"]["scope"]["outcome"] == evidence["outcome"]
    assert persist_capture(path, batch, evidence).result == "replay"
    assert storage.verify(path)["result"] == "ok"


@pytest.mark.parametrize("attack", ["false_complete", "context", "index", "selected", "capture"])
def test_generic_scope_cannot_mislabel_missing_or_mixed_context(tmp_path, attack):
    item = Observation(
        "set",
        ExternalReference("synthetic_scope", "set", "a", "es"),
        "Synthetic set",
        captured_at=CAPTURE,
        provenance="synthetic",
    )
    batch = synthetic_batch((item,))
    evidence = scope(batch, complete=False)
    if attack == "false_complete":
        evidence["outcome"] = "complete"
    elif attack == "context":
        evidence["units"][0]["language"] = "en"
    elif attack == "index":
        evidence["units"][0]["record_indexes"] = []
    elif attack == "selected":
        evidence["units"][0]["completed"] = ["unknown"]
    else:
        evidence["captured_at"] = "2026-10-15T00:00:00.000000Z"
    with pytest.raises(PersistenceError):
        persist_capture(tmp_path / "never.db", batch, evidence)
    assert not (tmp_path / "never.db").exists()


@pytest.mark.parametrize(
    "alteration",
    [
        "UPDATE records SET name='Synthetic tamper' WHERE record_index=0",
        "UPDATE batches SET fingerprint='" + "0" * 64 + "'",
        "UPDATE records SET provenance='synthetic'",
        "DELETE FROM records WHERE record_index=0",
    ],
)
def test_v2_business_corruption_blocks_verify_query_backup_restore(tmp_path, alteration):
    path = tmp_path / "damaged.db"
    token = str(uuid4())
    persist_bundle(path, approved_bundle_document(), token, manifest())
    with closing(sqlite3.connect(path, autocommit=True)) as connection:
        connection.execute(alteration)
    for action in (
        lambda: storage.verify(path),
        lambda: storage.query(path),
        lambda: query_capture(path, token),
        lambda: persist_bundle(path, approved_bundle_document(), token, manifest()),
        lambda: storage.backup(path, tmp_path / "never.db"),
        lambda: storage.restore(path, tmp_path / "never.db"),
    ):
        with pytest.raises(PersistenceError, match="storage_corrupt"):
            action()
    assert not (tmp_path / "never.db").exists()


def test_capture_envelope_is_sql_immutable_and_missing_scope_rejected(tmp_path):
    path = tmp_path / "history.db"
    token = str(uuid4())
    persist_bundle(path, approved_bundle_document(), token, manifest())
    with closing(sqlite3.connect(path, autocommit=True)) as connection:
        for statement in ("DELETE FROM captures", "UPDATE captures SET envelope='{}'"):
            with pytest.raises(sqlite3.IntegrityError):
                connection.execute(statement)
        connection.execute("DROP TRIGGER capture_immutable_delete")
        connection.execute("DELETE FROM captures")
    with pytest.raises(PersistenceError, match="storage_schema"):
        storage.verify(path)


def test_real_resolver_rejections_preserve_nonempty_complete_source_counts(tmp_path):
    document = manifest()
    document["entities"][0]["release_date"] = "2000-01-01"
    path = tmp_path / "rejected.db"
    token = str(uuid4())
    written = persist_bundle(path, approved_bundle_document(), token, document)
    assert written.rejected_count == 2
    capture = query_capture(path, token)
    assert capture["capture"]["scope"]["source_count"] == 4
    assert sum(unit["rejected_count"] for unit in capture["capture"]["scope"]["units"]) == 2
    assert storage.verify(path)["result"] == "ok"
    with pytest.raises(DiscoveryError, match="synthetic_only"):
        storage.read_snapshots(path, (token,))


def test_observed_direct_batch_bypass_and_v1_are_rejected_without_migration(tmp_path):
    from test_migration_capture import seed_v1

    from card_market_tracker.persistence.models import PersistedRecord

    observation = Observation(
        "set",
        ExternalReference("synthetic_scope", "set", "a", "es"),
        "Synthetic set",
        captured_at=CAPTURE,
        provenance="synthetic",
    )
    valid = synthetic_batch((observation,))
    forged = replace(
        valid,
        records=(
            PersistedRecord(
                0, "candidate", "missing_binding", None, replace(observation, provenance="observed")
            ),
        ),
    )
    path = tmp_path / "never.db"
    for action in (
        lambda: storage.persist(path, forged),
        lambda: persist_capture(path, forged, scope(valid)),
    ):
        with pytest.raises(PersistenceError, match="synthetic_only"):
            action()
    assert not path.exists()
    seed_v1(path)
    before = path.read_bytes()
    with pytest.raises(PersistenceError, match="storage_schema"):
        persist_bundle(path, approved_bundle_document(), str(uuid4()), manifest())
    assert path.read_bytes() == before
    assert storage.verify(path)["schema_version"] == 1


@pytest.mark.parametrize("alteration", ["row", "context", "envelope"])
def test_discovery_validates_selected_v2_scoped_capture_evidence(tmp_path, alteration):
    from card_market_tracker.persistence import schema

    observation = Observation(
        "set",
        ExternalReference("synthetic_scope", "set", "a", "es"),
        "Synthetic set",
        captured_at=CAPTURE,
        provenance="synthetic",
    )
    batch = synthetic_batch((observation,))
    path = tmp_path / "scoped.db"
    persist_capture(path, batch, scope(batch))
    assert (
        storage.read_snapshots(path, (batch.batch_id,))[0].records[0].observation.name
        == "Synthetic set"
    )
    with closing(sqlite3.connect(path, autocommit=True)) as connection:
        if alteration == "row":
            connection.execute("UPDATE records SET name='Synthetic tamper'")
        elif alteration == "context":
            connection.execute("UPDATE batches SET context_fingerprint=?", ("0" * 64,))
        else:
            connection.execute("DROP TRIGGER capture_immutable_update")
            connection.execute("UPDATE captures SET envelope='{}'")
            connection.execute(
                next(
                    sql
                    for sql in schema.STATEMENTS
                    if sql.startswith("CREATE TRIGGER capture_immutable_update")
                )
            )
    before = path.read_bytes()
    with pytest.raises(DiscoveryError, match="storage_corrupt"):
        storage.read_snapshots(path, (batch.batch_id,))
    assert path.read_bytes() == before


def test_discovery_validates_selected_v2_legacy_capture_envelope(tmp_path):
    from card_market_tracker.persistence import schema

    batch = synthetic_batch()
    path = tmp_path / "legacy.db"
    storage.persist(path, batch)
    assert storage.read_snapshots(path, (batch.batch_id,))[0].input_count == 0
    with closing(sqlite3.connect(path, autocommit=True)) as connection:
        connection.execute("DROP TRIGGER capture_immutable_update")
        connection.execute("UPDATE captures SET capture_fingerprint=?", ("0" * 64,))
        connection.execute(
            next(
                sql
                for sql in schema.STATEMENTS
                if sql.startswith("CREATE TRIGGER capture_immutable_update")
            )
        )
    with pytest.raises(DiscoveryError, match="storage_corrupt"):
        storage.read_snapshots(path, (batch.batch_id,))


def test_discovery_selected_real_and_mixed_rows_keep_explicit_synthetic_rejection(tmp_path):
    observation = Observation(
        "set",
        ExternalReference("synthetic_scope", "set", "a", "es"),
        "Synthetic set",
        captured_at=CAPTURE,
        provenance="synthetic",
    )
    batch = synthetic_batch((observation, observation))
    path = tmp_path / "mixed.db"
    persist_capture(path, batch, scope(batch))
    real_token = str(uuid4())
    persist_bundle(path, approved_bundle_document(), real_token, manifest())
    with pytest.raises(DiscoveryError, match="synthetic_only"):
        storage.read_snapshots(path, (batch.batch_id, real_token))
    with closing(sqlite3.connect(path, autocommit=True)) as connection:
        connection.execute(
            "UPDATE records SET provenance='observed' WHERE batch_id=? AND record_index=0",
            (batch.batch_id,),
        )
    with pytest.raises(DiscoveryError, match="synthetic_only"):
        storage.read_snapshots(path, (batch.batch_id,))


@pytest.mark.parametrize("attack", ["oversize", "utf8_bytes", "deep", "nodes", "string"])
def test_hostile_envelope_bounds_precede_full_json_decode(tmp_path, monkeypatch, attack):
    from card_market_tracker.catalog.validation import MAX_NODES, MAX_STRING
    from card_market_tracker.persistence import capture as capture_module
    from card_market_tracker.persistence import schema

    batch = synthetic_batch()
    path = tmp_path / "hostile.db"
    persist_capture(path, batch, scope(batch))
    malformed = {
        "oversize": '"' + "a" * (2 * 1024 * 1024) + '"',
        "utf8_bytes": '"' + "\U0001f680" * 300_000 + '"',
        "deep": "[" * 100 + "null" + "]" * 100,
        "nodes": "[" + ",".join("null" for _ in range(MAX_NODES + 1)) + "]",
        "string": '"' + "a" * (MAX_STRING + 1) + '"',
    }[attack]
    with closing(sqlite3.connect(path, autocommit=True)) as connection:
        connection.execute("PRAGMA ignore_check_constraints=ON")
        connection.execute("DROP TRIGGER capture_immutable_update")
        connection.execute("UPDATE captures SET envelope=?", (malformed,))
        connection.execute(
            next(
                sql
                for sql in schema.STATEMENTS
                if sql.startswith("CREATE TRIGGER capture_immutable_update")
            )
        )
        assert schema.inventory(connection) == schema.expected_inventory(2)
    loads = capture_module.json.loads

    def bounded_decode(text, *args, **kwargs):
        if text == malformed and attack != "string":
            pytest.fail("complete hostile envelope reached JSON decoder")
        return loads(text, *args, **kwargs)

    monkeypatch.setattr(capture_module.json, "loads", bounded_decode)
    before = path.read_bytes()
    for action in (
        lambda: query_capture(path, batch.batch_id),
        lambda: storage.read_snapshots(path, (batch.batch_id,)),
        lambda: storage.verify(path),
    ):
        with pytest.raises((PersistenceError, DiscoveryError), match="storage_corrupt"):
            action()
    assert path.read_bytes() == before
    # The scalar SQL byte guard also protects internal callers before SELECT *.
    if attack in ("oversize", "utf8_bytes"):
        with storage._connection(path, writable=False) as (connection, budget):
            with pytest.raises(PersistenceError, match="storage_corrupt"):
                capture_module._capture_row(connection, budget, batch.batch_id)


def test_capture_scope_and_rows_share_one_concurrent_snapshot(tmp_path, monkeypatch):
    import threading

    from card_market_tracker.persistence import schema

    observation = Observation(
        "set",
        ExternalReference("synthetic_scope", "set", "a", "es"),
        "Synthetic original",
        captured_at=CAPTURE,
        provenance="synthetic",
    )
    batch = synthetic_batch((observation,))
    path, replacement_path = tmp_path / "history.db", tmp_path / "replacement.db"
    persist_capture(path, batch, scope(batch))
    original = query_capture(path, batch.batch_id)
    replacement_batch = build_batch(
        batch.batch_id,
        CAPTURE,
        (replace(observation, name="Synthetic replacement"),),
        batch.manifest,
    )
    replacement_scope = scope(replacement_batch)
    replacement_scope["units"][0]["selector"] = "different explicit selection"
    persist_capture(replacement_path, replacement_batch, replacement_scope)
    replacement = query_capture(replacement_path, batch.batch_id)
    with closing(sqlite3.connect(replacement_path)) as connection:
        replacement_metadata = tuple(connection.execute("SELECT * FROM batches").fetchone())
        replacement_capture = tuple(connection.execute("SELECT * FROM captures").fetchone())
        replacement_record = tuple(connection.execute("SELECT * FROM records").fetchone())
    ready, committed = threading.Event(), threading.Event()
    errors = []
    writer_thread = None
    execute = storage._execute

    def writer():
        try:
            with closing(sqlite3.connect(path, autocommit=True, timeout=2)) as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute("DROP TRIGGER capture_immutable_update")
                connection.execute("DELETE FROM records WHERE batch_id=?", (batch.batch_id,))
                metadata_fields = (
                    "input_version",
                    "resolver_version",
                    "captured_at",
                    "first_persisted_at",
                    "fingerprint",
                    "context_fingerprint",
                    "input_count",
                    "accepted_count",
                    "candidate_count",
                    "rejected_count",
                    "result",
                )
                connection.execute(
                    "UPDATE batches SET "
                    + ",".join(field + "=?" for field in metadata_fields)
                    + " WHERE batch_id=?",
                    (*replacement_metadata[1:], batch.batch_id),
                )
                connection.execute(
                    "UPDATE captures SET mode=?,evidence_state=?,envelope=?,capture_fingerprint=? "
                    "WHERE batch_id=?",
                    (*replacement_capture[1:], batch.batch_id),
                )
                connection.execute(
                    "INSERT INTO records VALUES ("
                    + ",".join("?" for _ in replacement_record)
                    + ")",
                    replacement_record,
                )
                connection.execute(
                    next(
                        sql
                        for sql in schema.STATEMENTS
                        if sql.startswith("CREATE TRIGGER capture_immutable_update")
                    )
                )
                ready.set()
                connection.execute("COMMIT")
                committed.set()
        except BaseException as error:
            errors.append(error)
            ready.set()
            committed.set()

    def interleave(connection, budget, sql, values=()):
        nonlocal writer_thread
        cursor = execute(connection, budget, sql, values)
        if sql == "SELECT * FROM batches WHERE batch_id=?" and writer_thread is None:
            writer_thread = threading.Thread(target=writer)
            writer_thread.start()
            assert ready.wait(1), "writer did not reach commit"
            assert not committed.is_set(), "writer committed before scope and rows were read"
        return cursor

    monkeypatch.setattr(storage, "_execute", interleave)
    try:
        snapshot = query_capture(path, batch.batch_id)
        assert snapshot == original
    finally:
        if writer_thread is not None:
            writer_thread.join(3)
            assert not writer_thread.is_alive()
    assert not errors and committed.is_set()
    assert query_capture(path, batch.batch_id) == replacement
