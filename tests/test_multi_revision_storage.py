"""Exact-pair admission, immutable R0 compatibility and schema2 reconstruction."""

import json
import sqlite3
from contextlib import closing
from copy import deepcopy
from uuid import uuid4

import pytest

from card_market_tracker.catalog.validation import MAX_BYTES
from card_market_tracker.discovery.multi_input import parse_request
from card_market_tracker.discovery.multi_models import REVIEWED_PAIR_PROFILE, SYNTHETIC_PROFILE
from card_market_tracker.discovery.scoped_errors import ScopedDiscoveryError
from card_market_tracker.discovery.scoped_input import parse_request as parse_v2
from card_market_tracker.persistence import sqlite_repository as storage
from card_market_tracker.persistence.capture import persist_bundle, persist_bundle_v2, query_capture
from card_market_tracker.persistence.errors import PersistenceError
from card_market_tracker.pinned_repository import BundleError, approved_bundle_document
from card_market_tracker.pinned_repository.bundle_v2 import (
    VerifiedBundleV2,
    approved_bundle_document_v2,
    bundle_document_v2,
    capture_evidence_v2,
    observations_v2,
    validate_bundle_v2,
)

MANIFEST = {"version": 1, "entities": [], "bindings": []}


def request(current, history=(), *, profile=REVIEWED_PAIR_PROFILE):
    return parse_request(
        {
            "version": 3,
            "profile": profile,
            "context": {"namespace": "tcgdex_repository", "kind": "set", "language": "es"},
            "current": {"batch_id": current, "selector": "swsh3"},
            "history": [{"batch_id": token, "selector": "swsh3"} for token in history],
        }
    )


def test_both_packages_verify_query_reopen_backup_restore_and_replay(tmp_path):
    path, backup, restored = (tmp_path / name for name in ("history.db", "backup.db", "restore.db"))
    r0, r1 = str(uuid4()), str(uuid4())
    original = approved_bundle_document()
    second = approved_bundle_document_v2()
    persist_bundle(path, original, r0, MANIFEST)
    before_r0 = query_capture(path, r0)
    assert persist_bundle_v2(path, original, r0, MANIFEST).result == "replay"
    assert query_capture(path, r0) == before_r0
    first = persist_bundle_v2(path, validate_bundle_v2(second), r1, MANIFEST)
    assert (first.accepted_count, first.candidate_count, first.rejected_count) == (0, 4, 0)
    before_r1 = query_capture(path, r1)
    assert before_r1["capture"]["version"] == before_r1["capture"]["scope"]["version"] == 2
    assert before_r1["batch"]["captured_at"] == second["captured_at"]
    replay = persist_bundle_v2(path, second, r1, MANIFEST)
    assert replay.result == "replay" and replay.first_persisted_at == first.first_persisted_at
    assert storage.verify(path)["schema_version"] == 2
    assert len(storage.query(path)["records"]) == 8
    with closing(sqlite3.connect(path)) as connection:
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_schema WHERE type='table'")
        }
    assert tables == {"storage_metadata", "entities", "batches", "records", "captures"}
    captures = storage.read_multi_revision_snapshots(path, request(r1, (r0,)))
    assert len(captures) == 2
    assert {value.profile for value in captures} == {REVIEWED_PAIR_PROFILE}
    assert {json.loads(value.capture.scope_json)["revision"] for value in captures} == {
        original["revision"],
        second["revision"],
    }
    storage.backup(path, backup)
    storage.restore(backup, restored)
    assert query_capture(restored, r0) == before_r0
    assert query_capture(restored, r1) == before_r1
    assert storage.read_multi_revision_snapshots(restored, request(r1, (r0,))) == captures


@pytest.mark.parametrize(
    "field", ["revision", "captured_at", "policy_version", "extra", "registry"]
)
def test_unauthorized_package_and_forged_value_fail_before_database(tmp_path, field):
    document = approved_bundle_document_v2()
    document[field] = "unauthorized"
    path = tmp_path / "never.db"
    for value in (document, VerifiedBundleV2(json.dumps(document))):
        with pytest.raises(BundleError, match="unapproved_bundle"):
            persist_bundle_v2(path, value, str(uuid4()), MANIFEST)
    assert not path.exists()


def test_all_v2_consumers_revalidate_and_r0_stays_exact():
    original = approved_bundle_document()
    verified = validate_bundle_v2(original)
    assert approved_bundle_document_v2("r0") == bundle_document_v2(verified) == original
    assert capture_evidence_v2(verified)["version"] == 1
    assert len(observations_v2(verified)) == 4
    forged = VerifiedBundleV2('{"version":2}')
    for consumer in (bundle_document_v2, capture_evidence_v2, observations_v2):
        with pytest.raises(BundleError):
            consumer(forged)
    with pytest.raises(BundleError, match="invalid_shape"):
        bundle_document_v2(object())
    with pytest.raises(BundleError, match="unapproved_bundle"):
        approved_bundle_document_v2("r2")


def test_r1_cannot_enter_old_admission_or_v2_discovery_baseline(tmp_path):
    path = tmp_path / "history.db"
    r1 = str(uuid4())
    second = approved_bundle_document_v2()
    with pytest.raises(BundleError, match="unapproved_bundle"):
        persist_bundle(path, second, r1, MANIFEST)
    assert not path.exists()
    persist_bundle_v2(path, second, r1, MANIFEST)
    scoped = parse_v2(
        {key: value for key, value in request(r1).to_dict().items() if key != "profile"}
        | {"version": 2}
    )
    with pytest.raises(ScopedDiscoveryError, match="unsupported_evidence"):
        storage.read_scoped_snapshots(path, scoped)
    with pytest.raises(ScopedDiscoveryError, match="unsupported_evidence"):
        storage.read_multi_revision_snapshots(path, request(r1, profile=SYNTHETIC_PROFILE))


def test_cross_revision_replay_conflicts_without_overwrite(tmp_path):
    path = tmp_path / "history.db"
    token = str(uuid4())
    persist_bundle_v2(path, approved_bundle_document_v2("r0"), token, MANIFEST)
    before = path.read_bytes()
    with pytest.raises(PersistenceError, match="replay_conflict"):
        persist_bundle_v2(path, approved_bundle_document_v2(), token, MANIFEST)
    assert path.read_bytes() == before


def test_corruption_in_unselected_unit_rejects_read_query_verify_backup(tmp_path):
    path = tmp_path / "history.db"
    token = str(uuid4())
    persist_bundle_v2(path, approved_bundle_document_v2(), token, MANIFEST)
    with closing(sqlite3.connect(path)) as connection:
        connection.execute(
            "UPDATE records SET name='corrupt' WHERE batch_id=? AND record_index=3", (token,)
        )
        connection.commit()
    for action in (
        lambda: query_capture(path, token),
        lambda: storage.verify(path),
        lambda: storage.backup(path, tmp_path / "backup.db"),
        lambda: storage.read_multi_revision_snapshots(path, request(token)),
    ):
        with pytest.raises(PersistenceError, match="storage_corrupt"):
            action()


def test_altered_manifest_conflicts_and_no_new_package_clock(tmp_path):
    path = tmp_path / "history.db"
    token = str(uuid4())
    bundle = approved_bundle_document_v2()
    persist_bundle_v2(path, bundle, token, MANIFEST)
    changed = deepcopy(MANIFEST)
    changed["entities"] = [{"kind": "set", "cmt_id": str(uuid4())}]
    with pytest.raises(PersistenceError, match="replay_conflict"):
        persist_bundle_v2(path, bundle, token, changed)
    assert query_capture(path, token)["batch"]["captured_at"] == bundle["captured_at"]


def test_previously_migrated_database_preserves_legacy_rows_and_both_packages(tmp_path):
    from test_migration_capture import raw_rows, seed_v1

    path = tmp_path / "history.db"
    legacy = seed_v1(path)
    before = raw_rows(path)
    storage.migrate(path, tmp_path / "v1-backup.db")
    r0, r1 = str(uuid4()), str(uuid4())
    persist_bundle_v2(path, approved_bundle_document_v2("r0"), r0, MANIFEST)
    persist_bundle_v2(path, approved_bundle_document_v2(), r1, MANIFEST)
    current = raw_rows(path)
    assert all(set(old) <= set(new) for old, new in zip(before, current, strict=True))
    assert query_capture(path, legacy.batch_id)["evidence_state"] == "legacy_unverified"
    assert storage.verify(path)["schema_version"] == 2
    assert len(storage.read_multi_revision_snapshots(path, request(r1, (r0,)))) == 2


def test_r1_partial_write_failure_rolls_back_all_evidence(tmp_path, monkeypatch):
    path = tmp_path / "history.db"
    r0, r1 = str(uuid4()), str(uuid4())
    persist_bundle_v2(path, approved_bundle_document_v2("r0"), r0, MANIFEST)
    before = path.read_bytes()
    execute = storage._execute

    def fail(connection, budget, sql, values=()):
        if sql.startswith("INSERT INTO records") and values[0] == r1 and values[1] == 2:
            raise PersistenceError("storage_io")
        return execute(connection, budget, sql, values)

    with monkeypatch.context() as patch:
        patch.setattr(storage, "_execute", fail)
        with pytest.raises(PersistenceError, match="storage_io"):
            persist_bundle_v2(path, approved_bundle_document_v2(), r1, MANIFEST)
    assert path.read_bytes() == before
    assert storage.verify(path)["schema_version"] == 2
    assert len(storage.query(path)["records"]) == 4
    with pytest.raises(PersistenceError, match="invalid_field"):
        query_capture(path, r1)


@pytest.mark.parametrize(
    "raw,category",
    [
        ('{"version":2,"version":2}', "duplicate_key"),
        ('{"x":' + "[" * 17 + "0" + "]" * 17 + "}", "input_limit"),
        ("x" * (MAX_BYTES + 1), "input_limit"),
    ],
    ids=["duplicate-key", "nesting-bound", "encoded-byte-bound"],
)
def test_v2_direct_value_lexical_limits(raw, category):
    with pytest.raises(BundleError, match=category):
        bundle_document_v2(VerifiedBundleV2(raw))
