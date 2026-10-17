"""P4b complete capture-window reads, integrity, isolation and finite failure."""

import json
import sqlite3
import threading
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import pytest

from card_market_tracker.catalog.ingestion import ExternalReference, Observation, RecordError
from card_market_tracker.discovery.errors import DiscoveryError
from card_market_tracker.discovery.scoped_comparison import compare
from card_market_tracker.discovery.scoped_input import parse_request
from card_market_tracker.persistence import capture as capture_module
from card_market_tracker.persistence import schema
from card_market_tracker.persistence import sqlite_repository as storage
from card_market_tracker.persistence.application import build_batch
from card_market_tracker.persistence.capture import persist_bundle, persist_capture
from card_market_tracker.persistence.errors import PersistenceError
from card_market_tracker.persistence.input import read_persistence
from card_market_tracker.pinned_repository import approved_bundle_document

CAPTURE = "2026-10-14T17:53:09.118954Z"
MANIFEST = {"version": 1, "entities": [], "bindings": []}


def request(
    current, history=(), *, namespace="synthetic_scope", kind="set", language="es", selector="first"
):
    return parse_request(
        {
            "version": 2,
            "context": {"namespace": namespace, "kind": kind, "language": language},
            "current": {"batch_id": current, "selector": selector},
            "history": [{"batch_id": token, "selector": selector} for token in history],
        }
    )


def seed(path, *, second=False, empty=False, token=None):
    items = (
        ()
        if empty
        else tuple(
            Observation(
                "set",
                ExternalReference("synthetic_scope", "set", name, "es"),
                "Synthetic " + name,
                captured_at=CAPTURE,
                provenance="synthetic",
            )
            for name in (("a", "b") if second else ("a",))
        )
    )
    batch = build_batch(token or str(uuid4()), CAPTURE, items, MANIFEST)
    units = [
        {
            "namespace": "synthetic_scope",
            "kind": "set",
            "language": "es",
            "selector": "first",
            "selected": ["synthetic/a"],
            "completed": ["synthetic/a"],
            "record_indexes": [] if empty else [0],
        }
    ]
    if second:
        units.append(
            {
                **units[0],
                "selector": "second",
                "selected": ["synthetic/b"],
                "completed": ["synthetic/b"],
                "record_indexes": [1],
            }
        )
    scope = {
        "version": 1,
        "acquired_at": CAPTURE,
        "captured_at": CAPTURE,
        "outcome": "complete",
        "units": units,
    }
    persist_capture(path, batch, scope)
    return batch


def failure(category, action):
    with pytest.raises((DiscoveryError, PersistenceError)) as caught:
        action()
    assert caught.value.category == category
    assert str(caught.value) == category


def alter_capture(path, field, value):
    # Attack only temporary databases, restoring the exact required inventory.
    with closing(sqlite3.connect(path, autocommit=True)) as connection:
        connection.execute("PRAGMA ignore_check_constraints=ON")
        connection.execute("DROP TRIGGER capture_immutable_update")
        connection.execute(f"UPDATE captures SET {field}=?", (value,))
        connection.execute(
            next(
                sql
                for sql in schema.STATEMENTS
                if sql.startswith("CREATE TRIGGER capture_immutable_update")
            )
        )
        assert schema.inventory(connection) == schema.expected_inventory(2)


def test_complete_rows_all_units_and_read_only_authority(tmp_path, monkeypatch):
    path = tmp_path / "history.db"
    batch = seed(path, second=True)
    before = path.read_bytes()
    previous = storage._require_schema
    inside = []

    def check(connection, budget):
        inside.append(connection.in_transaction)
        assert connection.execute("PRAGMA query_only").fetchone()[0] == 1
        with pytest.raises(sqlite3.OperationalError):
            connection.execute("DELETE FROM batches")
        return previous(connection, budget)

    monkeypatch.setattr(storage, "_require_schema", check)
    (capture,) = storage.read_scoped_snapshots(path, request(batch.batch_id))
    assert inside == [True]
    assert path.read_bytes() == before
    assert capture.mode == "synthetic" and capture.evidence_state == "producer_declared"
    assert capture.snapshot.records[0].index == 0
    assert capture.snapshot.records[1].index == 1
    assert len(json.loads(capture.scope_json)["units"]) == 2
    assert capture.capture_fingerprint == capture.snapshot.fingerprint
    assert storage.read_scoped_snapshots(path, request(batch.batch_id)) == (capture,)


def test_maximum_window_sorted_and_empty_scope_durable(tmp_path):
    path = tmp_path / "window.db"
    tokens = [seed(path, empty=True).batch_id for _ in range(33)]
    first = storage.read_scoped_snapshots(path, request(tokens[0], tokens[1:]))
    second = storage.read_scoped_snapshots(path, request(tokens[0], reversed(tokens[1:])))
    assert first == second and len(first) == 33
    assert [capture.snapshot.batch_id for capture in first] == sorted(tokens)
    assert all(capture.snapshot.records == () for capture in first)
    assert all(json.loads(capture.scope_json)["outcome"] == "complete" for capture in first)


def test_pinned_admission_remains_reconstructed_and_v1_rejects(tmp_path):
    path = tmp_path / "pinned.db"
    token = str(uuid4())
    persist_bundle(path, approved_bundle_document(), token, MANIFEST)
    (capture,) = storage.read_scoped_snapshots(path, request(token, namespace="tcgdex_repository"))
    assert capture.mode == "pinned"
    assert capture.evidence_state == "verified_local_pinned_bundle"
    assert len(capture.snapshot.records) == 4
    assert {record.observation.provenance for record in capture.snapshot.records} == {"observed"}
    assert len(json.loads(capture.scope_json)["units"]) == 4
    failure("synthetic_only", lambda: storage.read_snapshots(path, (token,)))


@pytest.mark.parametrize(
    "field,value",
    [
        ("evidence_state", "verified_local_pinned_bundle"),
        ("mode", "pinned"),
        ("evidence_state", "legacy_unverified"),
    ],
)
def test_mode_and_evidence_cannot_be_promoted_by_database_strings(tmp_path, field, value):
    path = tmp_path / "forged.db"
    batch = seed(path)
    alter_capture(path, field, value)
    before = path.read_bytes()
    failure("storage_corrupt", lambda: storage.read_scoped_snapshots(path, request(batch.batch_id)))
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE records SET name='Synthetic corruption in another unit' WHERE record_index=1",
        "UPDATE records SET provenance='observed' WHERE record_index=1",
        "UPDATE records SET captured_at='2026-10-15T00:00:00.000000Z' WHERE record_index=1",
        "DELETE FROM records WHERE record_index=1",
        "UPDATE batches SET candidate_count=0",
        "UPDATE batches SET resolver_version=2",
        "UPDATE batches SET input_version=2",
    ],
)
def test_other_unit_corruption_and_metadata_never_hidden_by_selection(tmp_path, sql):
    path = tmp_path / "corrupt.db"
    batch = seed(path, second=True)
    with closing(sqlite3.connect(path, autocommit=True)) as connection:
        connection.execute("PRAGMA ignore_check_constraints=ON")
        connection.execute(sql)
    before = path.read_bytes()
    failure("storage_corrupt", lambda: storage.read_scoped_snapshots(path, request(batch.batch_id)))
    assert path.read_bytes() == before


def test_legacy_and_schema1_cannot_infer_scope_or_migrate(tmp_path):
    for version in (1, 2):
        path = tmp_path / f"legacy{version}.db"
        if version == 1:
            with closing(sqlite3.connect(path, autocommit=True)) as connection:
                for statement in schema.V1_STATEMENTS:
                    connection.execute(statement)
                connection.execute("INSERT INTO storage_metadata VALUES (1,?,1)", (schema.OWNER,))
                connection.execute(f"PRAGMA application_id={schema.APPLICATION_ID}")
                connection.execute("PRAGMA user_version=1")
        batch = build_batch(str(uuid4()), CAPTURE, (), MANIFEST)
        storage.persist(path, batch)
        before = path.read_bytes()
        failure(
            "unsupported_evidence",
            lambda path=path, batch=batch: storage.read_scoped_snapshots(
                path, request(batch.batch_id)
            ),
        )
        assert path.read_bytes() == before


@pytest.mark.parametrize("attack", ["oversize", "utf8", "deep", "nodes", "string"])
def test_envelope_limits_apply_before_materialization_and_full_decode(
    tmp_path, monkeypatch, attack
):
    path = tmp_path / "bounded.db"
    batch = seed(path)
    malformed = {
        "oversize": '"' + "a" * 1_000_001 + '"',
        "utf8": '"' + "\U0001f680" * 300_000 + '"',
        "deep": "[" * 17 + "null" + "]" * 17,
        "nodes": "[" + ",".join("null" for _ in range(20_001)) + "]",
        "string": '"' + "a" * 1025 + '"',
    }[attack]
    alter_capture(path, "envelope", malformed)
    loads = capture_module.json.loads

    def decode(text, *args, **kwargs):
        if text == malformed and attack != "string":
            pytest.fail("hostile envelope reached complete JSON decoder")
        return loads(text, *args, **kwargs)

    monkeypatch.setattr(capture_module.json, "loads", decode)
    failure("storage_corrupt", lambda: storage.read_scoped_snapshots(path, request(batch.batch_id)))


def test_missing_foreign_future_and_corrupt_storage_cannot_be_baseline(tmp_path):
    missing = tmp_path / "absent.db"
    current = str(uuid4())
    failure("storage_io", lambda: storage.read_scoped_snapshots(missing, request(current)))
    assert not missing.exists()
    for case in ("foreign", "future", "corrupt"):
        path = tmp_path / f"{case}.db"
        if case == "corrupt":
            path.write_bytes(b"synthetic corrupt database")
        elif case == "foreign":
            with closing(sqlite3.connect(path)) as connection:
                connection.execute("CREATE TABLE foreign_data(a)")
        else:
            seed(path)
            with closing(sqlite3.connect(path)) as connection:
                connection.execute("PRAGMA user_version=3")
        before = path.read_bytes()
        failure(
            "storage_corrupt" if case == "corrupt" else "storage_schema",
            lambda path=path: storage.read_scoped_snapshots(path, request(current)),
        )
        assert path.read_bytes() == before
    path = tmp_path / "existing.db"
    seed(path)
    failure("batch_missing", lambda: storage.read_scoped_snapshots(path, request(current)))


def test_public_request_and_timeout_revalidated_without_creating_db(tmp_path):
    path = tmp_path / "absent.db"
    original = request(str(uuid4()))
    for invalid in (None, {}, replace(original, version=True)):
        failure(
            "invalid_shape"
            if invalid is None or isinstance(invalid, dict)
            else "unsupported_version",
            lambda invalid=invalid: storage.read_scoped_snapshots(path, invalid),
        )
    for timeout in (True, 0, 6, float("nan"), "2"):
        failure(
            "invalid_field",
            lambda timeout=timeout: storage.read_scoped_snapshots(path, original, timeout=timeout),
        )
    assert not path.exists()


def test_lock_and_expired_python_validation_cleanup_release_reader(tmp_path, monkeypatch):
    from card_market_tracker.discovery import scoped_snapshot

    path = tmp_path / "locked.db"
    batch = seed(path)
    with closing(sqlite3.connect(path, autocommit=True)) as holder:
        holder.execute("BEGIN EXCLUSIVE")
        failure(
            "storage_locked",
            lambda: storage.read_scoped_snapshots(path, request(batch.batch_id), timeout=0.02),
        )
        holder.execute("ROLLBACK")
    validate = scoped_snapshot.validate_scoped_snapshot

    def expire(snapshot, *, provenance):
        result = validate(snapshot, provenance=provenance)
        patched.setattr(storage.time, "monotonic", lambda: float("inf"))
        return result

    with monkeypatch.context() as patched:
        patched.setattr(scoped_snapshot, "validate_scoped_snapshot", expire)
        failure(
            "storage_timeout", lambda: storage.read_scoped_snapshots(path, request(batch.batch_id))
        )
    with closing(sqlite3.connect(path, autocommit=True, timeout=0.05)) as writer:
        writer.execute("BEGIN IMMEDIATE")
        writer.execute("COMMIT")


def test_one_snapshot_covers_all_requested_capture_rows_and_envelopes(tmp_path, monkeypatch):
    path = tmp_path / "concurrent.db"
    first, second = seed(path, second=True), seed(path, second=True)
    selected = request(first.batch_id, (second.batch_id,))
    original = storage.read_scoped_snapshots(path, selected)
    ready, committed = threading.Event(), threading.Event()
    errors = []
    writer_thread = None
    execute = storage._execute

    def writer():
        try:
            with closing(sqlite3.connect(path, autocommit=True, timeout=2)) as connection:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    "UPDATE records SET name='Synthetic later corruption' WHERE record_index=1"
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
            assert ready.wait(1)
            assert not committed.is_set()
        return cursor

    monkeypatch.setattr(storage, "_execute", interleave)
    try:
        assert storage.read_scoped_snapshots(path, selected) == original
    finally:
        if writer_thread is not None:
            writer_thread.join(3)
            assert not writer_thread.is_alive()
    assert committed.is_set() and not errors
    failure("storage_corrupt", lambda: storage.read_scoped_snapshots(path, selected))


def test_replay_backup_restore_preserve_generic_evidence(tmp_path):
    path, backup, restored = (tmp_path / name for name in ("history.db", "copy.db", "restored.db"))
    token = str(uuid4())
    batch = seed(path, second=True, token=token)
    selected = request(batch.batch_id)
    original = storage.read_scoped_snapshots(path, selected)
    seed(path, second=True, token=token)
    assert storage.read_scoped_snapshots(path, selected) == original
    storage.backup(path, backup)
    storage.restore(backup, restored)
    assert storage.read_scoped_snapshots(restored, selected) == original


@pytest.mark.parametrize("bound", [False, True])
def test_four_real_units_baseline_original_indexes_and_reimport_clock(tmp_path, bound):
    path = tmp_path / "real-window.db"
    target = "f9743b79-20e3-4815-98d3-bb06f0c8195f"
    manifest = {
        "version": 1,
        "entities": [{"kind": "set", "cmt_id": target}] if bound else [],
        "bindings": [
            {
                "reference": {
                    "namespace": "tcgdex_repository",
                    "kind": "set",
                    "external_id": "swsh3",
                    "language": language,
                    "variant": "unknown",
                },
                "cmt_id": target,
                "reason": "Explicit synthetic curator binding for reviewed unit",
            }
            for language in ("es", "en")
        ]
        if bound
        else [],
    }
    original, replayed = str(uuid4()), str(uuid4())
    bundle = approved_bundle_document()
    persist_bundle(path, bundle, original, manifest)
    persist_bundle(path, bundle, replayed, manifest)
    before = path.read_bytes()
    for index, projection in enumerate(bundle["projection"]):
        selected = request(
            original,
            namespace="tcgdex_repository",
            kind=projection["kind"],
            language=projection["language"],
            selector=projection["external_id"],
        )
        result = compare(selected, storage.read_scoped_snapshots(path, selected)).to_dict()
        assert result["result"] == "baseline" and result["events"] == []
        assert result["counts"]["validated_batches"] == 1
        assert result["counts"]["validated_records"] == 4
        assert result["counts"]["current_selected_records"] == 1
        assert result["current"]["scope"]["record_indexes"] == [index]
        assert result["current"]["captured_at"] == CAPTURE
        assert result["current"]["evidence_state"] == "verified_local_pinned_bundle"
        window = replace(
            selected,
            current=replace(selected.current, batch_id=replayed),
            history=(selected.current,),
        )
        captures = storage.read_scoped_snapshots(path, window)
        assert {capture.snapshot.captured_at for capture in captures} == {CAPTURE}
        failure("chronology", lambda window=window, captures=captures: compare(window, captures))
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE entities SET language='en' WHERE kind='printing' AND variant='holo'",
        "UPDATE entities SET card_number='002' WHERE kind='card' AND card_number='001'",
        "UPDATE entities SET set_id=(SELECT cmt_id FROM entities WHERE kind='card' LIMIT 1) "
        "WHERE kind='card'",
    ],
)
def test_scoped_reader_revalidates_accepted_identity_parent_closure(tmp_path, sql):
    fixtures = Path(__file__).parent / "fixtures"
    batch = read_persistence(
        fixtures / "synthetic_persistence_valid.json", fixtures / "synthetic_manifest.json"
    )
    path = tmp_path / "identity.db"
    units = {}
    for row in batch.records:
        observation = row.observation
        key = (observation.reference.namespace, observation.kind, observation.reference.language)
        if key not in units:
            units[key] = {
                "namespace": key[0],
                "kind": key[1],
                "language": key[2],
                "selector": "first",
                "selected": ["synthetic/unit"],
                "completed": ["synthetic/unit"],
                "record_indexes": [],
            }
        units[key]["record_indexes"].append(row.index)
    scope = {
        "version": 1,
        "acquired_at": batch.captured_at,
        "captured_at": batch.captured_at,
        "outcome": "complete",
        "units": list(units.values()),
    }
    persist_capture(path, batch, scope)
    selected = request(batch.batch_id, namespace="tcgdex", kind="set", language="es")
    assert storage.read_scoped_snapshots(path, selected)[0].snapshot.accepted_count == 7
    with closing(sqlite3.connect(path, autocommit=True)) as connection:
        connection.execute(sql)
    failure("storage_corrupt", lambda: storage.read_scoped_snapshots(path, selected))


def test_large_complete_batch_still_keeps_all_original_rows(tmp_path):
    path = tmp_path / "large.db"
    # Full duplicated retained evidence shares the unchanged 20,000-node budget.
    batch = build_batch(
        str(uuid4()), CAPTURE, tuple(RecordError(i, "invalid_field") for i in range(800)), MANIFEST
    )
    scope = {
        "version": 1,
        "acquired_at": CAPTURE,
        "captured_at": CAPTURE,
        "outcome": "complete",
        "units": [
            {
                "namespace": "synthetic_scope",
                "kind": "set",
                "language": "es",
                "selector": "first",
                "selected": ["synthetic/a"],
                "completed": ["synthetic/a"],
                "record_indexes": list(range(800)),
            }
        ],
    }
    persist_capture(path, batch, scope)
    (capture,) = storage.read_scoped_snapshots(path, request(batch.batch_id))
    assert len(capture.snapshot.records) == 800
    assert tuple(record.index for record in capture.snapshot.records) == tuple(range(800))
    failure("incomplete_evidence", lambda: compare(request(batch.batch_id), (capture,)))
