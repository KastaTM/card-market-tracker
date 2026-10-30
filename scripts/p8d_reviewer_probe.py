"""Independent P8d reviewer probes; fake transport and fresh genuine originals only.
Run: .venv/Scripts/python.exe -B scripts/p8d_reviewer_probe.py
No author/QA tests or smoke helpers are imported. Outputs contain no route IDs/text.
"""

from __future__ import annotations

import base64
import contextlib
import copy
import hashlib
import io
import json
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from card_market_tracker.watchlist import application as wa
from card_market_tracker.watchlist import storage as ws
from card_market_tracker.watchlist_alerts import application as oa
from card_market_tracker.watchlist_alerts import storage as os_
from card_market_tracker.watchlist_delivery import application as app
from card_market_tracker.watchlist_delivery import policy, schema
from card_market_tracker.watchlist_delivery import storage as store
from card_market_tracker.watchlist_delivery.budget import Budget
from card_market_tracker.watchlist_delivery.errors import DeliveryError
from card_market_tracker.watchlist_journal import application as ja
from card_market_tracker.watchlist_journal import storage as js

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = {
    "version": 1,
    "entities": [
        {"kind": "sealed", "cmt_id": "91b4ca64-a8c3-4862-91c4-ef2f51427d18", "sealed_type": "box"}
    ],
    "bindings": [],
}
TARGET = MANIFEST["entities"][0]["cmt_id"]
FIXED = "2026-10-30T18:00:00.123456Z"
RESULTS = []


def check(name, operation):
    try:
        operation()
    except Exception as error:
        RESULTS.append(
            {
                "probe": name,
                "result": "FAIL",
                "exception": type(error).__name__,
                "category": getattr(error, "category", None),
            }
        )
    else:
        RESULTS.append({"probe": name, "result": "PASS"})


def rejected(category, operation):
    try:
        operation()
    except DeliveryError as error:
        assert error.category == category, error.category
    else:
        raise AssertionError("expected rejection")


def origin(directory, threshold=500, series="reviewer-series"):
    directory.mkdir()
    watch, journal, outbox = (directory / name for name in ("watch.db", "journal.db", "outbox.db"))
    ws.initialize(watch)
    entry = wa.add(
        watch, MANIFEST, TARGET, {"target_price_minor": threshold}, request_token="reviewer-add"
    )["entry"]
    js.initialize(journal)
    samples = []
    signal = None
    for index, price in enumerate((900, 100)):
        sample = {
            "version": 1,
            "provenance": "synthetic",
            "sample_id": f"reviewer-{index}",
            "cmt_id": TARGET,
            "series_key": series,
            "observed_at": f"2026-10-20T10:0{index}:00Z",
            "currency": "EUR",
            "unit_price_minor": price,
            "shipping_minor": 0,
            "stock": "AVAILABLE",
        }
        row = ja.record(
            journal,
            watch,
            MANIFEST,
            entry["watch_id"],
            sample,
            samples[-1] if samples else None,
            revision=1,
            as_of=sample["observed_at"],
        )
        samples.append(sample)
        if row["signal_ids"]:
            signal = row["signal_ids"][0]
    assert signal is not None
    os_.initialize(outbox)
    alert = oa.enqueue(outbox, watch, journal, MANIFEST, signal, "reviewer_private")["alert_id"]
    return watch, journal, outbox, alert


def ledger(directory, name="ledger.db"):
    path = directory / name
    app.initialize(path)
    app.destination_add(path, "reviewer_private", 11, 22, operator_private_owned=True)
    return path


def prepare(path, source):
    watch, journal, outbox, alert = source
    review = app.review(path, watch, journal, outbox, MANIFEST, alert, "reviewer_private")["review"]
    args = {"acknowledgement": "SYNTHETIC_HISTORICAL_DEMONSTRATION"}
    for field in (
        "signal_id",
        "revision",
        "message_sha256",
        "evidence_sha256",
        "route_sha256",
        "binding_sha256",
    ):
        args["expected_" + field] = review[field]
    return app.prepare(path, watch, journal, outbox, MANIFEST, alert, "reviewer_private", **args)


class Fake:
    def __init__(self, result=None, before=None):
        self.result = result
        self.before = before
        self.calls = []

    def check_configuration(self):
        self.calls.append("configuration")

    def validate_destination(self, bot_id, chat_id, *, timeout):
        self.calls.append("destination")

    def validate_bot(self, bot_id, *, timeout):
        self.calls.append("bot")

    def send(self, bot_id, chat_id, message_text, *, timeout):
        self.calls.append("send")
        if self.before:
            self.before()
        from card_market_tracker.telegram_delivery.transport import Receipt, TransportResult

        if self.result is None:
            return TransportResult("confirmed", receipt=Receipt(33, 100, bot_id, chat_id))
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def send(path, did, source, fake):
    with patch.object(app, "_transport_factory", return_value=fake):
        app.destination_validate(path, "reviewer_private")
        return app.send(
            path,
            did,
            watchlist_db=source[0],
            journal_db=source[1],
            outbox_db=source[2],
            manifest=MANIFEST,
        )


def frozen_ddl():
    raw = (ROOT / "docs/data-contracts/WATCHLIST_TELEGRAM_DELIVERY_STORAGE_V1.md").read_text(
        encoding="utf-8"
    )
    section = raw.split("<!-- P8D_DDL_BEGIN -->")[1].split("<!-- P8D_DDL_END -->")[0]
    literal = tuple(re.findall(r"^```sql\n(.*?)\n```$", section, re.M | re.S))
    assert len(literal) == 34 and literal == schema.STATEMENTS
    expected = []
    for kind, name, table, authority in re.findall(
        r"^\| (table|index|trigger) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|$", raw, re.M
    ):
        value = authority.strip()
        expected.append(
            (
                kind,
                name.strip(),
                table.strip(),
                None if value == "NULL" else literal[int(value.split()[1]) - 1],
            )
        )
    assert len(expected) == 45 and tuple(sorted(expected)) == schema.expected_inventory()


def identity():
    for digit, expected in (
        ("0", "b08e2920077a2f36ba634b32c0f1215e952063c55cfc99320ab55fbbdf9d36f5"),
        ("f", "810e8528fcea94a8ee848b56cb50ae04ff35bbaef05de8f667bddda896cac9d8"),
    ):
        literal = (
            '{"identity_version":1,"provider":"telegram","signal_id":"wsig1_' + digit * 64 + '"}'
        ).encode("ascii")
        preimage = b"CMT_WATCHLIST_TELEGRAM_DELIVERY_V1\0" + literal
        assert len(preimage) == 164 and preimage.count(b"\0") == 1
        assert hashlib.sha256(preimage).hexdigest() == expected
        assert policy.delivery_id("wsig1_" + digit * 64) == "wtdl1_" + expected


def originals_and_rw01(directory):
    a, b, equivalent = (
        origin(directory / "a"),
        origin(directory / "b", 600, "another-series"),
        origin(directory / "equivalent"),
    )
    path = ledger(directory)
    first = prepare(path, a)
    assert prepare(path, equivalent)["result"] == "replay"
    rejected("identity_conflict", lambda: prepare(path, b))
    assert app.verify(path)["counts"] == {
        "destinations": 1,
        "watch_entries": 1,
        "deliveries": 1,
        "claims": 0,
        "results": 0,
    }
    app.backup(path, directory / "healthy-backup.db")
    assert app.get(path, first["delivery"]["delivery_id"])["delivery"]["state"] == "ready"
    return a


def authorities(directory, source):
    path = ledger(directory, "authority.db")
    budget = Budget(5)
    content, manifest = app._admit(
        path, *source[:3], MANIFEST, source[3], "reviewer_private", budget
    )

    def issued():
        return app._issue(content, budget, path, source[:3], manifest)

    receipt = issued()
    for fake in (copy.copy(receipt), copy.deepcopy(receipt), app._Receipt(receipt.content_json)):
        rejected(
            "unsupported_evidence", lambda fake=fake: store._prepare_verified(path, fake, budget)
        )
    rejected("unsupported_evidence", lambda: store._prepare_verified(path, receipt, Budget(5)))
    rejected("unsupported_evidence", lambda: app._consume_receipt(receipt, budget, "claim", path))
    store._prepare_verified(path, receipt, budget)
    rejected("unsupported_evidence", lambda: store._prepare_verified(path, receipt, budget))
    forged = issued()
    object.__setattr__(forged, "content_json", forged.content_json + " ")
    rejected("unsupported_evidence", lambda: store._prepare_verified(path, forged, budget))
    short = Budget(5)
    expired = app._issue(content, short, path, source[:3], manifest)
    with patch(
        "card_market_tracker.watchlist_delivery.budget.time.monotonic",
        return_value=short.global_deadline + 1,
    ):
        rejected("storage_timeout", lambda: store._prepare_verified(path, expired, short))


def claim_no_lock_replay(directory, source):
    path = ledger(directory, "confirmed.db")
    did = prepare(path, source)["delivery"]["delivery_id"]

    def inspect():
        with contextlib.closing(sqlite3.connect(path, autocommit=True, timeout=0.1)) as db:
            assert db.execute("SELECT state FROM wtd_state").fetchone()[0] == "in_flight"
            assert db.execute("SELECT count(*) FROM wtd_claims").fetchone()[0] == 1
            db.execute("BEGIN IMMEDIATE")
            db.execute("ROLLBACK")

    response = send(path, did, source, Fake(before=inspect))
    assert response["delivery"]["state"] == "confirmed"
    code = """import importlib.abc, os, socket, sys
class Deny(importlib.abc.MetaPathFinder):
 def find_spec(self, fullname, path=None, target=None):
  if "telegram_delivery" in fullname: raise AssertionError("transport import")
sys.meta_path.insert(0,Deny())
original=os._Environ.__getitem__
def item(self,key):
 if key=="CMT_TELEGRAM_BOT_TOKEN": raise AssertionError("token access")
 return original(self,key)
os._Environ.__getitem__=item
def socket_denied(*a,**k): raise AssertionError("socket access")
socket.socket=socket_denied
from pathlib import Path
from card_market_tracker.watchlist_delivery.application import send
assert send(Path(sys.argv[1]),sys.argv[2])["result"]=="replay"
print("tokenless socketless transportless replay PASS")"""
    completed = subprocess.run(
        [sys.executable, "-B", "-c", code, str(path), did],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert completed.returncode == 0, completed.stderr
    restored = directory / "restored.db"
    app.restore(path, restored)
    rejected("send_quarantined", lambda: app.send(restored, did))
    rejected("send_quarantined", lambda: app.send(restored, "wtdl1_" + "0" * 64))
    return path


def cooldown(directory, source):
    from card_market_tracker.telegram_delivery.transport import TransportResult

    path = ledger(directory, "rate.db")
    did = prepare(path, source)["delivery"]["delivery_id"]
    retry = Fake(TransportResult("retryable", error_category="provider_rate_limit", retry_after=10))
    for ordinal in (1, 2, 3):
        moment = f"2026-10-30T18:00:{ordinal * 10:02d}.123456Z"
        with patch.object(policy, "now", return_value=moment):
            response = send(path, did, source, retry)
        row = response["delivery"]
        assert row["attempt_count"] == ordinal
        if ordinal < 3:
            assert row["state"] == "retryable"
            with contextlib.closing(sqlite3.connect(path)) as db:
                high = db.execute("SELECT operational_high_water FROM wtd_metadata").fetchone()[0]
            assert high == moment and row["not_before"] > high
            with patch.object(policy, "now", return_value=moment):
                rejected(
                    "retry_not_due",
                    lambda: app.send(
                        path,
                        did,
                        watchlist_db=source[0],
                        journal_db=source[1],
                        outbox_db=source[2],
                        manifest=MANIFEST,
                    ),
                )
        else:
            assert (
                row["state"] == "permanent_failure"
                and row["last_error_category"] == "retry_exhausted"
            )
    assert retry.calls.count("send") == 3


def cli_durable_error(directory, source):
    from card_market_tracker.cli import main
    from card_market_tracker.telegram_delivery.transport import TransportResult

    path = ledger(directory, "cli-error.db")
    did = prepare(path, source)["delivery"]["delivery_id"]
    manifest = directory / "manifest.json"
    manifest.write_text(json.dumps(MANIFEST), encoding="utf-8")
    fake = Fake(TransportResult("retryable", error_category="provider_rate_limit", retry_after=1))
    with patch.object(app, "_transport_factory", return_value=fake):
        app.destination_validate(path, "reviewer_private")
        output, logs = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(logs):
            code = main(
                [
                    "watchlist-telegram-delivery",
                    "send",
                    "--ledger-db",
                    str(path),
                    "--delivery-id",
                    did,
                    "--watchlist-db",
                    str(source[0]),
                    "--journal-db",
                    str(source[1]),
                    "--outbox-db",
                    str(source[2]),
                    "--manifest",
                    str(manifest),
                ]
            )
    payload = json.loads(output.getvalue())
    assert payload["result"] == "error" and payload["error_category"] == "rate_limited"
    assert code == 1, "durable rate limit must exit1"
    event = json.loads(logs.getvalue())
    assert event["error_category"] == "rate_limited" and event["result"] == "error"


def missing_receipt(directory, source):
    from card_market_tracker.telegram_delivery.transport import TransportResult

    path = ledger(directory, "missing-receipt.db")
    did = prepare(path, source)["delivery"]["delivery_id"]
    fake = Fake(TransportResult("confirmed"))
    response = send(path, did, source, fake)
    assert response["delivery"]["state"] == "uncertain"
    assert response["delivery"]["last_error_category"] == "provider_invalid"
    rejected("delivery_blocked", lambda: app.send(path, did))
    assert fake.calls.count("send") == 1


def tamper_bounds(directory, source):
    base = ledger(directory, "tamper-base.db")
    prepare(base, source)
    for index, (table, column, replacement) in enumerate(
        (
            ("wtd_deliveries", "message_text", "x" * 4097),
            ("wtd_results", "owner", "f" * 65),
            ("wtd_destinations", "validated_at", "x" * 28),
            ("wtd_watch_entries", "entry_json", "x" * 65537),
        )
    ):
        if table == "wtd_results":
            continue
        target = directory / f"tampered-{index}.db"
        app.backup(base, target)
        with contextlib.closing(sqlite3.connect(target, autocommit=True)) as db:
            triggers = list(db.execute("SELECT name,sql FROM sqlite_master WHERE type='trigger'"))
            for name, _ in triggers:
                db.execute('DROP TRIGGER "' + name + '"')
            db.execute("PRAGMA ignore_check_constraints=ON")
            db.execute("UPDATE " + table + " SET " + column + "=?", (replacement,))
            for _, statement in triggers:
                db.execute(statement)
        rejected("storage_corrupt", lambda target=target: app.verify(target))


def recovery_fencing_clock(directory, source):
    path = ledger(directory, "fencing.db")
    did = prepare(path, source)["delivery"]["delivery_id"]
    store._destination_validated(path, "reviewer_private")
    budget = Budget(15, 30)
    with budget.origins():
        content, manifest = app._admit(
            path, *source[:3], MANIFEST, source[3], "reviewer_private", budget, operation="claim"
        )
    receipt = app._issue(content, budget, path, source[:3], manifest)
    claimed = store._claim_verified(path, did, receipt, budget)
    rejected("invalid_field", lambda: app.recover(path, did))
    with patch.object(policy, "now", return_value="0001-01-01T00:00:00.000000Z"):
        recovered = app.recover(path, did, worker_quiesced=True)
    assert recovered["delivery"]["state"] == "uncertain"
    assert recovered["delivery"]["last_error_category"] == "clock_skew"
    outcome = {
        "state": "confirmed",
        "error_category": None,
        "retry_after": None,
        "receipt": {"message_id": 33, "accepted_at": 100, "bot_id": 11, "chat_id": 22},
    }
    rejected("stale_attempt", lambda: store._finish(path, did, claimed["_handle"], outcome, budget))
    assert app.get(path, did)["delivery"]["last_error_category"] == "clock_skew"
    path2 = ledger(directory, "rollback-before.db")
    did2 = prepare(path2, source)["delivery"]["delivery_id"]
    store._destination_validated(path2, "reviewer_private")
    with patch.object(policy, "now", return_value="0001-01-01T00:00:00.000000Z"):
        rejected(
            "clock_skew",
            lambda: app.send(
                path2,
                did2,
                watchlist_db=source[0],
                journal_db=source[1],
                outbox_db=source[2],
                manifest=MANIFEST,
            ),
        )
    assert app.get(path2, did2)["delivery"]["attempt_count"] == 0


def historic_route_snapshot(directory, source):
    from card_market_tracker.telegram_delivery.transport import TransportResult

    path = ledger(directory, "snapshot.db")
    did = prepare(path, source)["delivery"]["delivery_id"]
    fake = Fake(TransportResult("retryable", error_category="provider_rate_limit", retry_after=1))
    with patch.object(policy, "now", return_value="2026-10-30T20:00:00.000000Z"):
        send(path, did, source, fake)
    with patch.object(policy, "now", return_value="2026-10-30T20:01:00.000000Z"):
        with patch.object(app, "_transport_factory", return_value=Fake()):
            app.destination_validate(path, "reviewer_private")
        assert app.verify(path)["counts"]["claims"] == 1
        with patch.object(app, "_transport_factory", return_value=Fake()):
            assert (
                app.send(
                    path,
                    did,
                    watchlist_db=source[0],
                    journal_db=source[1],
                    outbox_db=source[2],
                    manifest=MANIFEST,
                )["delivery"]["state"]
                == "confirmed"
            )


def old_restore_new_preparation(directory, source):
    path = ledger(directory, "old.db")
    backup = directory / "old-backup.db"
    app.backup(path, backup)
    did = prepare(path, source)["delivery"]["delivery_id"]
    restored = directory / "old-restored.db"
    app.restore(backup, restored)
    rejected("send_quarantined", lambda: app.send(restored, did))
    assert prepare(restored, source)["result"] == "inserted"
    rejected("send_quarantined", lambda: app.send(restored, did))
    assert app.verify(restored)["send_quarantined"] is True


def aggregate_budget():
    clock = [100.0]
    with patch(
        "card_market_tracker.watchlist_delivery.budget.time.monotonic", side_effect=lambda: clock[0]
    ):
        parent = Budget(15, 30)
        assert parent.global_deadline == 115 and parent.reserve == 0.5
        with parent.reserved():
            with parent.origins():
                assert parent.deadline == 105
                clock[0] = 104.999
                assert 0 < parent.remaining() < 0.002
                clock[0] = 105
                rejected("storage_timeout", parent.remaining)
                clock[0] = 104
            assert parent.deadline == 114.5
            rejected("unsupported_evidence", lambda: parent.origins().__enter__())
        clock[0] = 114.6
        rejected("deadline_exceeded", parent.preclaim)
        assert parent.remaining() > 0
        clock[0] = 115
        rejected("storage_timeout", parent.remaining)
    for invalid in (True, 0, -1, float("nan"), float("inf"), 5.01):
        rejected("invalid_field", lambda invalid=invalid: Budget(invalid))


def cursor_oracle(directory, source):
    path = ledger(directory, "cursor.db")
    did = prepare(path, source)["delivery"]["delivery_id"]
    literal = ('{"filters":{"state":null},"last_delivery_id":"' + did + '","version":1}').encode(
        "ascii"
    )
    token = base64.urlsafe_b64encode(literal).decode("ascii")
    assert app.list_deliveries(path, cursor=token)["items"] == []
    for invalid in (
        token.rstrip("="),
        token + "=",
        base64.urlsafe_b64encode(literal.replace(b"null", b"false")).decode("ascii"),
        "!",
        "x" * 2049,
    ):
        if invalid != token:
            rejected(
                "invalid_cursor", lambda invalid=invalid: app.list_deliveries(path, cursor=invalid)
            )
    rejected("invalid_cursor", lambda: app.list_deliveries(path, cursor=token, state="ready"))
    rejected("invalid_field", lambda: app.list_deliveries(path, limit=True))


def catalog_materialization_bounds(directory, source):
    path = ledger(directory, "catalog-guard.db")
    queries = []
    original = store._execute

    def recording(db, budget, sql, values=()):
        if "FROM sqlite_master ORDER BY type,name" in sql:
            queries.append(sql)
        return original(db, budget, sql, values)

    with patch.object(store, "_execute", side_effect=recording):
        app.verify(path)
    assert queries
    for sql in queries:
        for column in ("type", "name", "tbl_name"):
            assert f"length(CAST({column} AS BLOB)) BETWEEN 1 AND 128" in sql
        assert "length(CAST(sql AS BLOB)) BETWEEN 1 AND 32768" in sql


def manifest_hardlink_safety(directory, source):
    import os

    path = ledger(directory, "manifest-safety.db")
    original = directory / "manifest-safe.json"
    linked = directory / "manifest-linked.json"
    original.write_text(json.dumps(MANIFEST), encoding="utf-8")
    os.link(original, linked)
    assert original.stat().st_nlink == 2
    budget = Budget(5)
    token = app._invocation_budget.set(budget)
    try:
        rejected(
            "unsafe_destination",
            lambda: app.review(
                path, *source[:3], app._manifest_file(linked, budget), source[3], "reviewer_private"
            ),
        )
    finally:
        app._invocation_budget.reset(token)


def child_send(arguments):
    import os

    path, watch, journal, outbox, did, marker, action = arguments

    def effect():
        descriptor = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            os.write(descriptor, b"fake-send\n")
        finally:
            os.close(descriptor)
        if action == "crash":
            os._exit(77)

    fake = Fake(before=effect)
    try:
        with patch.object(app, "_transport_factory", return_value=fake):
            response = app.send(
                Path(path),
                did,
                watchlist_db=Path(watch),
                journal_db=Path(journal),
                outbox_db=Path(outbox),
                manifest=MANIFEST,
            )
        print(json.dumps({"result": response["result"]}))
    except DeliveryError as error:
        print(json.dumps({"error_category": error.category}))
    return 0


def process_race_crash(directory, source):
    path = ledger(directory, "race.db")
    did = prepare(path, source)["delivery"]["delivery_id"]
    store._destination_validated(path, "reviewer_private")
    marker = directory / "fake-effects.txt"
    command = [
        sys.executable,
        "-B",
        str(Path(__file__).resolve()),
        "--child-send",
        str(path),
        *map(str, source[:3]),
        did,
        str(marker),
        "accept",
    ]
    children = [
        subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        for _ in range(2)
    ]
    outcomes = []
    for child in children:
        stdout, stderr = child.communicate(timeout=20)
        assert child.returncode == 0 and not stderr
        outcomes.append(json.loads(stdout))
    assert marker.read_text().splitlines() == ["fake-send"]
    assert app.get(path, did)["delivery"]["state"] == "confirmed"
    assert app.verify(path)["counts"]["claims"] == 1
    assert any(item.get("result") == "ok" for item in outcomes)
    crash_path = ledger(directory, "crashed.db")
    crash_did = prepare(crash_path, source)["delivery"]["delivery_id"]
    store._destination_validated(crash_path, "reviewer_private")
    crash_marker = directory / "crash-fake-effect.txt"
    command = [
        sys.executable,
        "-B",
        str(Path(__file__).resolve()),
        "--child-send",
        str(crash_path),
        *map(str, source[:3]),
        crash_did,
        str(crash_marker),
        "crash",
    ]
    crashed = subprocess.run(command, capture_output=True, text=True, timeout=20)
    assert crashed.returncode == 77
    assert crash_marker.read_text().splitlines() == ["fake-send"]
    assert app.get(crash_path, crash_did)["delivery"]["state"] == "in_flight"
    rejected("delivery_blocked", lambda: app.send(crash_path, crash_did))
    assert (
        app.recover(crash_path, crash_did, worker_quiesced=True)["delivery"]["state"] == "uncertain"
    )
    rejected("delivery_blocked", lambda: app.send(crash_path, crash_did))


def assert_originals(fingerprints):
    for path, expected in fingerprints.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected


def main():
    evidence = ROOT / "docs/evidence/P8D_REVIEWER"
    evidence.mkdir(parents=True, exist_ok=True)
    check("frozen_34_DDL_45_catalog_exact", frozen_ddl)
    check("literal_NUL_identity_oracle", identity)
    check("one_global_budget_nonrenewable_origins_reserve", aggregate_budget)
    with tempfile.TemporaryDirectory(prefix="reviewer-", dir=evidence) as temporary:
        directory = Path(temporary)
        holder = []
        check(
            "genuine_equivalent_copy_and_incompatible_RW01_rollback",
            lambda: holder.append(originals_and_rw01(directory)),
        )
        if holder:
            source = holder[0]
            fingerprints = {
                path: hashlib.sha256(path.read_bytes()).hexdigest() for path in source[:3]
            }
            for name, function in (
                ("one_use_authority_forgery_copy_budget_deadline", authorities),
                (
                    "durable_claim_no_SQL_lock_confirmed_replay_global_quarantine",
                    claim_no_lock_replay,
                ),
                ("three429_event_watermark_exact_cooldown", cooldown),
                ("durable_error_CLI_exit_log", cli_durable_error),
                ("missing_receipt_uncertain_no_resend", missing_receipt),
                (
                    "historic_route_validation_snapshot_survives_revalidation",
                    historic_route_snapshot,
                ),
                ("guarded_overlength_tamper", tamper_bounds),
                ("quiesced_recovery_clock_clamp_stale_finish", recovery_fencing_clock),
                ("old_restore_missing_then_new_delivery_quarantined", old_restore_new_preparation),
                ("independent_cursor_canonical_filter_oracle", cursor_oracle),
                ("independent_process_sender_race_and_postclaim_crash", process_race_crash),
                ("manifest_multiple_hardlinks_refused", manifest_hardlink_safety),
                (
                    "catalog_names128_SQL32768_before_materialization",
                    catalog_materialization_bounds,
                ),
            ):
                check(name, lambda function=function: function(directory, source))
            check("original_source_bytes_unchanged", lambda: assert_originals(fingerprints))
    print(
        json.dumps(
            {
                "scope": (
                    "independent probes; fake transport only; "
                    "working tree must be matched separately"
                ),
                "head": subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
                ).strip(),
                "tree": subprocess.check_output(
                    ["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT, text=True
                ).strip(),
                "python": sys.version.split()[0],
                "sqlite": sqlite3.sqlite_version,
                "checks": RESULTS,
            },
            sort_keys=True,
        )
    )
    return int(any(result["result"] != "PASS" for result in RESULTS))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--child-send":
        sys.exit(child_send(sys.argv[2:]))
    sys.exit(main())
