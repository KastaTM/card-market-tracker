"""Author storage probes: state reconstruction, fencing, contention and quarantine.

Private sealed envelopes here isolate the ledger contract; application tests own
original-capture admission. No test contacts Telegram.
"""

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
from contextlib import closing

import pytest

from card_market_tracker.alerts.policy import alert_id
from card_market_tracker.telegram_delivery import application, schema, storage
from card_market_tracker.telegram_delivery.errors import DeliveryError


def failure(category, call):
    with pytest.raises(DeliveryError) as caught:
        call()
    assert caught.value.category == category
    assert str(caught.value) == category
    return caught.value


def binding(*, alias="local", event="a", comparison="b"):
    item = dict.fromkeys(storage.BINDING_FIELDS, "c" * 64)
    item.update(alias=alias, event_id="evt3:" + event * 64, comparison_id="cmp3:" + comparison * 64)
    item["alert_id"] = alert_id(alias, item["event_id"])
    return item


def sealed(item):
    content = json.dumps(item, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    receipt = application._Receipt(content)
    object.__setattr__(
        receipt,
        "_authority",
        (application._AUTHORITY, id(receipt), hashlib.sha256(content.encode("ascii")).hexdigest()),
    )
    return receipt


def add_route(path, alias="local", bot_id=101, chat_id=202):
    storage.destination_add(path, alias, bot_id, chat_id, operator_private_owned=True)
    storage.destination_validated(path, alias, bot_id, chat_id)


@pytest.fixture
def ledger(tmp_path):
    path = tmp_path / "delivery.db"
    storage.initialize(path)
    add_route(path)
    bound = binding()
    prepared = storage._prepare_verified(path, sealed(bound))
    return path, bound, prepared["delivery_id"]


def claim(ledger):
    path, bound, did = ledger
    return storage._claim_verified(path, did, sealed(bound))


def test_exact_owner_missing_noncreating_inventory_and_exclusive_init(tmp_path):
    path = tmp_path / "new.db"
    failure("storage_missing", lambda: storage.verify(path))
    assert not path.exists()
    storage.initialize(path)
    with closing(sqlite3.connect(path)) as db:
        assert db.execute("PRAGMA application_id").fetchone()[0] == 0x434D5444
        assert db.execute("PRAGMA user_version").fetchone()[0] == 1
        assert db.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
        assert (
            tuple(db.execute("SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"))
            == schema.expected_inventory()
        )
    before = path.read_bytes()
    failure("unsafe_destination", lambda: storage.initialize(path))
    assert before == path.read_bytes()
    assert storage.verify(path)["counts"] == {
        "destinations": 0,
        "deliveries": 0,
        "attempts": 0,
        "results": 0,
    }


def test_identity_oracle_and_immutable_route_attestation_validation(tmp_path):
    aid = "alt1:" + "0" * 64
    expected = "tdl1:df549d47dc58e3404ca349cb0328939dd8c8f6cb619e592bd1302c743b4cb6bf"
    assert storage.delivery_id(aid) == expected
    path = tmp_path / "routes.db"
    storage.initialize(path)
    failure("invalid_destination", lambda: storage.destination_add(path, "local", 101, 202))
    for bot, chat in ((True, 202), (101, True), (0, 202), (101, 2**52)):
        failure(
            "invalid_field",
            lambda bot=bot, chat=chat: storage.destination_add(
                path, "local", bot, chat, operator_private_owned=True
            ),
        )
    storage.destination_add(path, "local", 101, 202, operator_private_owned=True)
    failure("not_validated", lambda: storage._prepare_verified(path, sealed(binding())))
    failure("conflict", lambda: storage.destination_validated(path, "local", 102, 202))
    storage.destination_validated(path, "local", 101, 202)
    before = storage.load_destination(path, "local")
    assert storage.destination_validated(path, "local", 101, 202)["result"] == "replay"
    assert (
        storage.destination_add(path, "local", 101, 202, operator_private_owned=True)["result"]
        == "replay"
    )
    assert storage.load_destination(path, "local") == before
    failure(
        "conflict",
        lambda: storage.destination_add(path, "local", 102, 202, operator_private_owned=True),
    )
    route = {
        key: before[key]
        for key in (
            "alias",
            "provider",
            "bot_id",
            "chat_id",
            "chat_type",
            "operator_attested_owner",
        )
    }
    assert (
        before["route_sha256"]
        == hashlib.sha256(
            json.dumps(
                route, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode("ascii")
        ).hexdigest()
    )


def test_preparation_replay_all_bindings_and_cross_alias_event_dedup(ledger):
    path, bound, did = ledger
    initial = storage.get(path, did)
    assert storage._prepare_verified(path, sealed(bound))["result"] == "replay"
    assert storage.get(path, did) == initial
    for key in storage.BINDING_FIELDS[4:] + ("comparison_id",):
        changed = {**bound, key: ("cmp3:" if key == "comparison_id" else "") + "d" * 64}
        failure(
            "conflict", lambda changed=changed: storage._prepare_verified(path, sealed(changed))
        )
    add_route(path, "other", 303, 404)
    failure("conflict", lambda: storage._prepare_verified(path, sealed(binding(alias="other"))))
    assert storage.verify(path)["counts"]["deliveries"] == 1
    failure("unsupported_evidence", lambda: storage._prepare_verified(path, bound))
    failure(
        "unsupported_evidence", lambda: storage._prepare_verified(path, application._Receipt("{}"))
    )


def test_claim_receipt_confirmation_reopen_replay_and_redacted_history(ledger):
    path, bound, did = ledger
    intent = claim(ledger)
    failure("delivery_blocked", lambda: claim(ledger))
    failure(
        "conflict",
        lambda: storage.finish(
            path,
            did,
            intent["attempt_id"],
            state="confirmed",
            receipt={"message_id": 77, "accepted_at": 1, "bot_id": 101, "chat_id": 999},
        ),
    )
    assert storage.load_delivery(path, did)["state"] == "in_flight"
    storage.finish(
        path,
        did,
        intent["attempt_id"],
        state="confirmed",
        receipt={"message_id": 77, "accepted_at": 1, "bot_id": 101, "chat_id": 202},
    )
    assert storage._claim_verified(path, did, sealed(bound))["result"] == "replay"
    public = storage.get(path, did)
    encoded = json.dumps(public)
    assert '"bot_id"' not in encoded and '"chat_id"' not in encoded
    assert public["delivery"]["attempts"][0]["result"]["message_id"] == 77
    assert storage.verify(path)["counts"] == {
        "destinations": 1,
        "deliveries": 1,
        "attempts": 1,
        "results": 1,
    }
    failure(
        "stale_attempt",
        lambda: storage.finish(
            path, did, intent["attempt_id"], state="uncertain", error_category="network_uncertain"
        ),
    )


def test_429_cooldown_three_attempts_and_old_owner_fencing(ledger, monkeypatch):
    path, _, did = ledger
    clock = ["2026-10-21T12:00:00.000000Z"]
    monkeypatch.setattr(storage, "_now", lambda: clock[0])
    # The fixture clock may be later than our deterministic test clock.
    with closing(sqlite3.connect(path)) as db:
        db.execute("UPDATE destinations SET validated_at=?", (clock[0],))
        db.execute("UPDATE deliveries SET created_at=?,updated_at=?", (clock[0], clock[0]))
        db.commit()
    old_id = None
    for ordinal in range(1, 4):
        intent = claim(ledger)
        assert intent["ordinal"] == ordinal
        if old_id is not None:
            failure(
                "stale_attempt",
                lambda old_id=old_id: storage.finish(
                    path,
                    did,
                    old_id,
                    state="confirmed",
                    receipt={"message_id": 1, "accepted_at": 1, "bot_id": 101, "chat_id": 202},
                ),
            )
        outcome = storage.finish(
            path,
            did,
            intent["attempt_id"],
            state="retryable",
            error_category="provider_rate_limit",
            retry_after=10,
        )
        if ordinal < 3:
            assert outcome["state"] == "retryable" and outcome["error_category"] == "rate_limited"
            failure("retry_not_due", lambda: claim(ledger))
            clock[0] = storage._after(clock[0], 10)
        else:
            assert outcome["state"] == "permanent_failure"
            assert outcome["error_category"] == "retry_exhausted"
        old_id = intent["attempt_id"]
    failure("delivery_blocked", lambda: claim(ledger))
    assert storage.verify(path)["counts"]["attempts"] == 3


def test_crash_recovery_requires_quiescence_fences_worker_and_never_reopens(ledger):
    path, _, did = ledger
    intent = claim(ledger)
    failure("delivery_blocked", lambda: storage.recover(path, did))
    assert storage.recover(path, did, worker_quiesced=True)["state"] == "uncertain"
    failure("delivery_blocked", lambda: claim(ledger))
    failure(
        "stale_attempt",
        lambda: storage.finish(
            path,
            did,
            intent["attempt_id"],
            state="confirmed",
            receipt={"message_id": 1, "accepted_at": 1, "bot_id": 101, "chat_id": 202},
        ),
    )
    assert (
        storage.load_delivery(path, did)["attempts"][0]["result"]["error_category"] == "recovered"
    )


@pytest.mark.parametrize(
    "stage",
    [
        "claim_insert",
        "claim_update",
        "claim_commit",
        "result_insert",
        "result_update",
        "result_commit",
    ],
)
def test_faults_rollback_intent_or_receipt_and_conserve_history(ledger, monkeypatch, stage):
    path, _, did = ledger
    finalizing = stage.startswith("result")
    intent = claim(ledger) if finalizing else None
    baseline = storage.verify(path)
    execute = storage._execute

    def injected(db, budget, sql, values=()):
        hit = (
            (stage == "claim_insert" and sql.startswith("INSERT INTO delivery_attempts"))
            or (
                stage == "claim_update"
                and sql.startswith("UPDATE deliveries SET state='in_flight'")
            )
            or (stage == "result_insert" and sql.startswith("INSERT INTO delivery_attempt_results"))
            or (stage == "result_update" and sql.startswith("UPDATE deliveries SET state=?"))
            or (stage.endswith("commit") and sql == "COMMIT")
        )
        if hit:
            db.set_progress_handler(lambda: 1, 1)
            raise DeliveryError("storage_io")
        return execute(db, budget, sql, values)

    monkeypatch.setattr(storage, "_execute", injected)
    failure(
        "storage_io",
        lambda: storage.finish(
            path,
            did,
            intent["attempt_id"],
            state="confirmed",
            receipt={"message_id": 1, "accepted_at": 1, "bot_id": 101, "chat_id": 202},
        )
        if finalizing
        else claim(ledger),
    )
    monkeypatch.setattr(storage, "_execute", execute)
    assert storage.verify(path) == baseline
    assert storage.load_delivery(path, did)["state"] == ("in_flight" if finalizing else "ready")
    if finalizing:
        storage.recover(path, did, worker_quiesced=True)
        assert storage.load_delivery(path, did)["state"] == "uncertain"


@pytest.mark.parametrize(
    "sql,category",
    [
        ("PRAGMA application_id=1", "storage_schema"),
        ("PRAGMA user_version=2", "storage_schema"),
        ("CREATE INDEX extra ON deliveries(alert_id)", "storage_schema"),
        ("UPDATE deliveries SET message_sha256='g'||substr(message_sha256,2)", "storage_corrupt"),
        ("UPDATE destinations SET bot_id=102", "storage_corrupt"),
        ("UPDATE deliveries SET route_sha256='d'||substr(route_sha256,2)", "storage_corrupt"),
        ("UPDATE deliveries SET attempt_count=1,state='uncertain'", "storage_corrupt"),
        ("UPDATE deliveries SET updated_at='9999-99-99T00:00:00.000000Z'", "storage_corrupt"),
        ("UPDATE deliveries SET not_before=printf('%0200000d',1)", "storage_corrupt"),
        ("UPDATE destinations SET validated_at=printf('%0200000d',1)", "storage_corrupt"),
        ("UPDATE deliveries SET current_attempt_id=printf('%0200000d',1)", "storage_corrupt"),
    ],
)
def test_foreign_schema_corrupt_semantics_and_hostile_optional_cells(ledger, sql, category):
    path, _, _ = ledger
    with closing(sqlite3.connect(path)) as db:
        db.execute("PRAGMA ignore_check_constraints=ON")
        db.execute(sql)
        db.commit()
    failure(category, lambda: storage.verify(path))


def test_local_verify_does_not_claim_to_recompute_unretained_source_hash(ledger):
    path, _, did = ledger
    # Source digests are opaque binding commitments. Local verification cannot
    # reproduce content intentionally retained only in the immutable P8a DBs.
    with closing(sqlite3.connect(path)) as db:
        db.execute("UPDATE deliveries SET message_sha256=?", ("d" * 64,))
        db.commit()
    assert storage.verify(path)["level"] == "local"
    failure("conflict", lambda: claim(ledger))
    assert storage.get(path, did)["delivery"]["state"] == "ready"


def test_history_reconstruction_detects_coherent_count_or_wrong_receipt(ledger):
    path, _, did = ledger
    intent = claim(ledger)
    storage.finish(
        path,
        did,
        intent["attempt_id"],
        state="confirmed",
        receipt={"message_id": 1, "accepted_at": 1, "bot_id": 101, "chat_id": 202},
    )
    with closing(sqlite3.connect(path)) as db:
        db.execute("UPDATE delivery_attempt_results SET chat_id=303")
        db.commit()
    failure("storage_corrupt", lambda: storage.verify(path))


def test_backup_stale_restore_global_quarantine_even_absent_delivery(tmp_path):
    path = tmp_path / "live.db"
    storage.initialize(path)
    add_route(path)
    before = tmp_path / "before.db"
    storage.backup(path, before)
    bound = binding()
    prepared = storage._prepare_verified(path, sealed(bound))
    did = prepared["delivery_id"]
    intent = storage._claim_verified(path, did, sealed(bound))
    storage.finish(
        path,
        did,
        intent["attempt_id"],
        state="confirmed",
        receipt={"message_id": 1, "accepted_at": 1, "bot_id": 101, "chat_id": 202},
    )
    restored = tmp_path / "restored.db"
    assert storage.restore(before, restored)["send_quarantined"] is True
    assert storage.verify(restored)["counts"]["deliveries"] == 0
    storage._prepare_verified(restored, sealed(bound))
    failure("send_quarantined", lambda: storage._claim_verified(restored, did, sealed(bound)))
    failure("unsafe_destination", lambda: storage.initialize(restored))
    twice = tmp_path / "again.db"
    assert storage.backup(restored, twice)["send_quarantined"] is True
    assert storage.verify(twice)["send_quarantined"] is True
    assert not list(tmp_path.glob(".*.restore-*"))
    failure("unsafe_destination", lambda: storage.restore(before, restored))


def test_restore_snapshot_never_exposes_unquarantined_final_path(ledger, tmp_path, monkeypatch):
    path, bound, did = ledger
    restored = tmp_path / "restored.db"
    snapshot = storage._snapshot
    observed = []

    def intercepted(reader, writer, budget):
        snapshot(reader, writer, budget)
        filename = writer.execute("PRAGMA database_list").fetchone()[2]
        if os.path.samefile(filename, restored) if restored.exists() else False:
            observed.append(storage.verify(restored)["send_quarantined"])
            failure(
                "send_quarantined", lambda: storage._claim_verified(restored, did, sealed(bound))
            )

    monkeypatch.setattr(storage, "_snapshot", intercepted)
    storage.restore(path, restored)
    assert observed == [True]


def test_pagination_state_bounds_read_nonmutation_and_clock_rollback(ledger, monkeypatch):
    path, _, did = ledger
    for event in ("d", "e"):
        storage._prepare_verified(path, sealed(binding(event=event)))
    page = storage.list_deliveries(path, limit=1)
    following = storage.list_deliveries(path, cursor=page["next_cursor"], limit=2)
    assert len(following["items"]) == 2 and following["next_cursor"] is None
    assert set(item["delivery_id"] for item in page["items"] + following["items"]) == set(
        item["delivery_id"] for item in storage.list_deliveries(path)["items"]
    )
    before = path.read_bytes()
    storage.get(path, did)
    storage.verify(path)
    assert path.read_bytes() == before
    for limit in (True, 0, 1001):
        failure("invalid_field", lambda limit=limit: storage.list_deliveries(path, limit=limit))
    failure("invalid_field", lambda: storage.list_deliveries(path, state="sent"))
    failure("invalid_field", lambda: storage.list_deliveries(path, cursor="anything"))
    monkeypatch.setattr(storage, "_now", lambda: "2000-01-01T00:00:00.000000Z")
    failure("delivery_blocked", lambda: claim(ledger))


def test_two_independent_processes_one_claim_and_crash_after_intent(ledger, tmp_path):
    path, bound, did = ledger
    gate = tmp_path / "go"
    code = """
import hashlib,json,os,sys,time
from pathlib import Path
from card_market_tracker.telegram_delivery import application,storage
from card_market_tracker.telegram_delivery.errors import DeliveryError
path,did,content,gate,ready=sys.argv[1:]
receipt=application._Receipt(content)
object.__setattr__(receipt,'_authority',(application._AUTHORITY,id(receipt),hashlib.sha256(content.encode('ascii')).hexdigest()))
Path(ready).touch()
while not Path(gate).exists(): time.sleep(0.005)
try:
 result=storage._claim_verified(Path(path),did,receipt)
 print(result['result'],flush=True)
except DeliveryError as error: print(error.category,flush=True)
"""
    content = json.dumps(bound, sort_keys=True, separators=(",", ":"))
    workers = [
        subprocess.Popen(
            [
                sys.executable,
                "-c",
                code,
                str(path),
                did,
                content,
                str(gate),
                str(tmp_path / f"ready{i}"),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for i in range(2)
    ]
    try:
        deadline = time.monotonic() + 10
        while not all((tmp_path / f"ready{i}").exists() for i in range(2)):
            assert time.monotonic() < deadline
            time.sleep(0.01)
        gate.touch()
        outputs = [worker.communicate(timeout=10) for worker in workers]
    finally:
        for worker in workers:
            if worker.poll() is None:
                worker.kill()
                worker.wait(timeout=5)
    assert sorted(output[0].strip() for output in outputs) == ["claimed", "delivery_blocked"]
    assert all(worker.returncode == 0 for worker in workers)
    assert all(not output[1] for output in outputs)
    assert storage.verify(path)["counts"]["attempts"] == 1
    failure("delivery_blocked", lambda: claim(ledger))
    storage.recover(path, did, worker_quiesced=True)
    assert storage.get(path, did)["delivery"]["state"] == "uncertain"


def test_finite_writer_contention_and_sidecar_preservation(ledger):
    path, _, _ = ledger
    with closing(sqlite3.connect(path)) as writer:
        writer.execute("BEGIN IMMEDIATE")
        failure(
            "storage_locked",
            lambda: storage.destination_validated(path, "local", 101, 202, timeout=0.03),
        )
        writer.rollback()
    sidecar = path.with_name(path.name + "-wal")
    sidecar.write_bytes(b"foreign recovery evidence")
    failure("storage_schema", lambda: storage.verify(path))
    assert sidecar.read_bytes() == b"foreign recovery evidence"


@pytest.mark.parametrize("mode", ["after_claim", "before_receipt_commit"])
def test_actual_process_exit_preserves_blocked_durable_intent(ledger, mode):
    path, bound, did = ledger
    code = """
import hashlib,os,sys
from pathlib import Path
from card_market_tracker.telegram_delivery import application,storage
path,did,content,mode=sys.argv[1:]
receipt=application._Receipt(content)
object.__setattr__(receipt,'_authority',(application._AUTHORITY,id(receipt),hashlib.sha256(content.encode('ascii')).hexdigest()))
claimed=storage._claim_verified(Path(path),did,receipt)
if mode=='after_claim': os._exit(23)
execute=storage._execute
def interrupted(db,budget,sql,values=()):
 if sql=='COMMIT': os._exit(23)
 return execute(db,budget,sql,values)
storage._execute=interrupted
storage.finish(Path(path),did,claimed['attempt_id'],state='confirmed',receipt={'message_id':1,'accepted_at':1,'bot_id':101,'chat_id':202})
"""
    worker = subprocess.run(
        [
            sys.executable,
            "-c",
            code,
            str(path),
            did,
            json.dumps(bound, sort_keys=True, separators=(",", ":")),
            mode,
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert worker.returncode == 23 and not worker.stdout and not worker.stderr
    assert storage.load_delivery(path, did)["state"] == "in_flight"
    assert storage.verify(path)["counts"] == {
        "destinations": 1,
        "deliveries": 1,
        "attempts": 1,
        "results": 0,
    }
    failure("delivery_blocked", lambda: claim(ledger))
    storage.recover(path, did, worker_quiesced=True)
    assert storage.load_delivery(path, did)["state"] == "uncertain"


@pytest.mark.parametrize(
    "code,category",
    [
        (sqlite3.SQLITE_FULL, "storage_io"),
        (sqlite3.SQLITE_IOERR, "storage_io"),
        (sqlite3.SQLITE_BUSY, "storage_locked"),
        (sqlite3.SQLITE_CORRUPT, "storage_corrupt"),
        (sqlite3.SQLITE_INTERRUPT, "storage_timeout"),
    ],
)
def test_sqlite_failures_redact_messages_and_rollback(ledger, monkeypatch, code, category):
    path, _, did = ledger
    execute = storage._execute

    def fault(db, budget, sql, values=()):
        if sql.startswith("INSERT INTO delivery_attempts"):
            error = sqlite3.OperationalError("private token reflected by device")
            error.sqlite_errorcode = code
            raise error
        return execute(db, budget, sql, values)

    monkeypatch.setattr(storage, "_execute", fault)
    caught = failure(category, lambda: claim(ledger))
    assert "private" not in str(caught)
    monkeypatch.setattr(storage, "_execute", execute)
    assert storage.verify(path)["counts"]["attempts"] == 0
    assert storage.load_delivery(path, did)["state"] == "ready"


@pytest.mark.parametrize(
    "receipt",
    [
        {},
        {"message_id": True, "accepted_at": 1, "bot_id": 101, "chat_id": 202},
        {"message_id": 1, "accepted_at": 0, "bot_id": 101, "chat_id": 202},
        {"message_id": 1, "accepted_at": 1, "bot_id": True, "chat_id": 202},
        {"message_id": 1, "accepted_at": 1, "bot_id": 101, "chat_id": 202, "extra": "private"},
    ],
)
def test_invalid_receipts_do_not_finalize_or_overwrite(ledger, receipt):
    path, _, did = ledger
    intent = claim(ledger)
    failure(
        "invalid_field",
        lambda: storage.finish(path, did, intent["attempt_id"], state="confirmed", receipt=receipt),
    )
    assert storage.verify(path)["counts"]["results"] == 0
    assert storage.load_delivery(path, did)["state"] == "in_flight"


@pytest.mark.parametrize("seconds", [True, 0, -1, 86401, 1.0])
def test_invalid429_does_not_grant_retry(ledger, seconds):
    path, _, did = ledger
    intent = claim(ledger)
    failure(
        "invalid_field",
        lambda: storage.finish(
            path,
            did,
            intent["attempt_id"],
            state="retryable",
            error_category="provider_rate_limit",
            retry_after=seconds,
        ),
    )
    assert storage.load_delivery(path, did)["state"] == "in_flight"


def test_uncertain_and_permanent_rejections_remain_terminal(ledger):
    path, _, did = ledger
    intent = claim(ledger)
    storage.finish(
        path,
        did,
        intent["attempt_id"],
        state="permanent_failure",
        error_category="provider_rejection",
    )
    failure("delivery_blocked", lambda: claim(ledger))
    assert storage.verify(path)["counts"]["results"] == 1


def test_restore_empty_ledger_and_failed_staging_preserved(tmp_path, monkeypatch):
    source, restored = tmp_path / "empty.db", tmp_path / "restored.db"
    storage.initialize(source)
    assert storage.restore(source, restored)["send_quarantined"] is True
    assert storage.verify(restored)["counts"]["deliveries"] == 0
    snapshot = storage._snapshot

    def broken(reader, writer, budget):
        snapshot(reader, writer, budget)
        raise DeliveryError("storage_io")

    monkeypatch.setattr(storage, "_snapshot", broken)
    failed = tmp_path / "failed.db"
    failure("storage_io", lambda: storage.restore(source, failed))
    assert not failed.exists()
    assert len(list(tmp_path.glob(".failed.db.restore-*"))) == 1


def test_read_only_source_copy_preserves_bytes_and_exclusive_sidecars(ledger, tmp_path):
    path, _, _ = ledger
    before = path.read_bytes()
    destination = tmp_path / "copy.db"
    sidecar = tmp_path / "copy.db-journal"
    sidecar.write_bytes(b"retained")
    failure("unsafe_destination", lambda: storage.backup(path, destination))
    assert sidecar.read_bytes() == b"retained" and not destination.exists()
    assert path.read_bytes() == before


@pytest.mark.parametrize("timeout", [True, 0, -1, 5.1, float("nan"), float("inf")])
def test_finite_budget_strict_fields(timeout):
    failure("invalid_field", lambda: storage.Budget(timeout))
