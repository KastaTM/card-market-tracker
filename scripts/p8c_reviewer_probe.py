"""Independent P8c reviewer regression/oracles; run with --fixtures tests/fixtures --timeout 5.

No author/QA helpers, production policy/render/schema or writing oracle supplies expected values.
Only disposable synthetic files are created. Each product operation keeps its own <=5s budget.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def expected_id(alias, signal):
    body = encoded({"identity_version": 1, "destination_key": alias, "signal_id": signal})
    return "walt1_" + hashlib.sha256(b"CMT_WATCHLIST_ALERT_V1\0" + body.encode("ascii")).hexdigest()


def expect_error(category, action):
    from card_market_tracker.watchlist_alerts.errors import OutboxError

    try:
        action()
    except OutboxError as error:
        assert error.category == category, (category, error.category)
    else:
        raise AssertionError("expected " + category)


def golden(entry, old, current, signal, before_id, after_id, sequence):
    # Literal frozen renderer lines; values derive from our authored scenario.
    rule = signal["rule"]
    pairs = [
        ("cmt_id", current["cmt_id"]),
        ("watch_id", entry["watch_id"]),
        ("historical_revision", 1),
        ("rule", rule),
        ("signal_id", signal["signal_id"]),
        ("sequence_id", sequence),
        ("from_evaluation_id", before_id),
        ("to_evaluation_id", after_id),
        ("predecessor_current_observed_at", old["observed_at"]),
        ("predecessor_previous_observed_at", "none"),
        ("predecessor_as_of", old["observed_at"]),
        ("current_current_observed_at", current["observed_at"]),
        ("current_previous_observed_at", old["observed_at"]),
        ("current_as_of", current["observed_at"]),
        ("predecessor_rule_result", "NO_MATCH"),
        ("predecessor_rule_reason", "current_out_of_stock"),
        ("current_rule_result", "MATCH"),
        ("current_rule_reason", "at_or_below_target" if rule == "price" else "restocked"),
    ]
    lines = [
        "SYNTHETIC — DEMONSTRATION ONLY",
        "Not a real offer or commercial notification.",
        "Historical Watchlist simulation; not current notification authorization.",
        *(f"{name}: {value}" for name, value in pairs),
    ]
    if rule == "price":
        lines += [
            "Synthetic price rule entered MATCH.",
            "currency: EUR",
            "target_price_minor: 1000",
            "predecessor_unit_price_minor: unknown",
            "predecessor_shipping_minor: unknown",
            "predecessor_effective_cost_minor: unknown",
            "current_unit_price_minor: 1000",
            "current_shipping_minor: 0",
            "current_effective_cost_minor: 1000",
        ]
    else:
        lines += [
            "Synthetic restock rule entered MATCH; no real shop availability is asserted.",
            "predecessor_previous_stock: none",
            "predecessor_current_stock: OUT_OF_STOCK",
            "current_previous_stock: OUT_OF_STOCK",
            "current_current_stock: AVAILABLE",
        ]
    return "\n".join(lines)


CRASH = r"""
import os, sqlite3, sys
connection = sqlite3.connect(sys.argv[1])
connection.execute('PRAGMA synchronous=FULL')
connection.execute('PRAGMA cache_size=2')
connection.execute('BEGIN IMMEDIATE')
connection.execute('CREATE TABLE reviewer_uncommitted(payload BLOB)')
for _ in range(48):
    connection.execute('INSERT INTO reviewer_uncommitted VALUES (zeroblob(8192))')
os._exit(83)
"""


def hot_journal(path):
    result = subprocess.run([sys.executable, "-c", CRASH, str(path)], timeout=20)
    assert result.returncode == 83
    journal = Path(str(path) + "-journal")
    assert journal.read_bytes()[:8] == bytes.fromhex("d9d505f920a163d7")
    return journal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=5)
    args = parser.parse_args()
    assert 0 < args.timeout <= 5

    def no_socket(*arguments, **keywords):
        raise AssertionError("product socket attempt")

    socket.socket = no_socket
    socket.create_connection = no_socket
    from card_market_tracker.watchlist import application as watches
    from card_market_tracker.watchlist import storage as watch_store
    from card_market_tracker.watchlist_alerts import application as app
    from card_market_tracker.watchlist_alerts import storage as store
    from card_market_tracker.watchlist_journal import application as journals
    from card_market_tracker.watchlist_journal import storage as journal_store

    timeout = {"timeout": args.timeout}
    results = []
    # Reviewer's original failure was success emitted AFTER logging exhausted the
    # deadline. Audit the actual first stdout write, without prescribing log order.
    from card_market_tracker.watchlist_alerts import cli

    report_budget = store.Budget(args.timeout)
    first_writes, completed_logs = [], []

    class DeadlineOutput(io.StringIO):
        def write(self, text):
            if text and not first_writes:
                report_budget.remaining()
                first_writes.append(True)
            return super().write(text)

    captured_stdout = DeadlineOutput()

    def expiry_during_log(*arguments, **keywords):
        completed_logs.append(keywords["extra"])
        report_budget.deadline = 0

    with (
        contextlib.redirect_stdout(captured_stdout),
        patch("logging.Logger.log", expiry_during_log),
    ):
        code = cli._report(
            {"version": 1, "operation": "verify", "result": "ok"},
            "verify",
            time.perf_counter(),
            0,
            budget=report_budget,
        )
    assert code == 0 and first_writes == [True]
    assert json.loads(captured_stdout.getvalue()) == {
        "version": 1,
        "operation": "verify",
        "result": "ok",
    }
    assert len(completed_logs) == 1 and completed_logs[0]["result"] == "ok"
    assert report_budget.deadline == 0
    results.append("deadline-at-first-stdout-byte-single-completion-log")

    # Expiry while encoding must still produce only a redacted error on stdout.
    report_budget = store.Budget(args.timeout)
    original_dumps = cli.json.dumps
    completed_logs.clear()

    def expire_encoding(value, *arguments, **keywords):
        text = original_dumps(value, *arguments, **keywords)
        if value.get("result") == "ok":
            report_budget.deadline = 0
        return text

    captured_stdout = io.StringIO()
    with (
        contextlib.redirect_stdout(captured_stdout),
        patch.object(cli.json, "dumps", expire_encoding),
        patch("logging.Logger.log", expiry_during_log),
    ):
        code = cli._report(
            {"version": 1, "operation": "verify", "result": "ok", "counts": {"alerts": 2}},
            "verify",
            time.perf_counter(),
            0,
            budget=report_budget,
        )
    assert code == 1
    assert json.loads(captured_stdout.getvalue()) == {
        "version": 1,
        "operation": "verify",
        "result": "error",
        "error_category": "storage_timeout",
    }
    assert len(completed_logs) == 1 and completed_logs[0]["result"] == "error"
    assert not any(name.endswith("_count") for name in completed_logs[0])
    results.append("serialization-expiry-no-partial-success-or-error-counts")
    with tempfile.TemporaryDirectory(prefix="cmt-p8c-reviewer-") as directory:
        root = Path(directory)
        watchlist, journal, outbox = (root / (name + ".db") for name in ("watch", "journal", "out"))
        manifest = json.loads((args.fixtures / "synthetic_manifest.json").read_text("utf-8"))
        target = "541b9d13-9669-4973-8413-397bea14c045"
        watch_store.initialize(watchlist, **timeout)
        entry = watches.add(
            watchlist,
            manifest,
            target,
            {"target_price_minor": 1000, "restock_enabled": True},
            request_token="reviewer-case",
            **timeout,
        )["entry"]
        journal_store.initialize(journal, **timeout)
        old = {
            "version": 1,
            "provenance": "synthetic",
            "sample_id": "reviewer-absent",
            "cmt_id": target,
            "series_key": "reviewer-series",
            "observed_at": "2026-10-24T09:00:00Z",
            "currency": "EUR",
            "unit_price_minor": None,
            "shipping_minor": None,
            "stock": "OUT_OF_STOCK",
        }
        current = dict(
            old,
            sample_id="reviewer-present",
            observed_at="2026-10-24T09:01:00Z",
            unit_price_minor=1000,
            shipping_minor=0,
            stock="AVAILABLE",
        )
        first = journals.record(
            journal,
            watchlist,
            manifest,
            entry["watch_id"],
            old,
            None,
            revision=1,
            as_of=old["observed_at"],
            **timeout,
        )
        second = journals.record(
            journal,
            watchlist,
            manifest,
            entry["watch_id"],
            current,
            old,
            revision=1,
            as_of=current["observed_at"],
            **timeout,
        )
        assert first["signals_count"] == 0 and second["signals_count"] == 2
        store.initialize(outbox, **timeout)
        originals = watchlist.read_bytes(), journal.read_bytes()
        saved = []
        for signal_id in second["signal_ids"]:
            signal = journal_store.signal_get(journal, signal_id, **timeout)["signal"]
            response = app.enqueue(
                outbox, watchlist, journal, manifest, signal_id, "reviewer-local", **timeout
            )
            assert response["alert_id"] == expected_id("reviewer-local", signal_id)
            alert = store.get(outbox, response["alert_id"], **timeout)["alert"]
            message = golden(
                entry,
                old,
                current,
                signal,
                first["evaluation_id"],
                second["evaluation_id"],
                second["sequence_id"],
            )
            assert alert["message_text"].encode("utf-8") == message.encode("utf-8")
            assert alert["message_sha256"] == hashlib.sha256(message.encode("utf-8")).hexdigest()
            assert (
                alert["intent_sha256"]
                == hashlib.sha256(encoded(alert["intent"]).encode()).hexdigest()
            )
            saved.append(response)
        results.append("independent-identity-and-both-renderer-byte-oracles")
        frozen = outbox.read_bytes()
        for response in saved:
            assert (
                app.enqueue(
                    outbox,
                    watchlist,
                    journal,
                    manifest,
                    response["signal_id"],
                    "reviewer-local",
                    **timeout,
                )["result"]
                == "replayed"
            )
        assert outbox.read_bytes() == frozen
        assert (watchlist.read_bytes(), journal.read_bytes()) == originals
        results.append("nullable-money-free-shipping-replay-source-byte-nonmutation")

        # Wrong source owner must be rejected before SQLite can recover a foreign crash.
        foreign = root / "foreign.db"
        foreign.write_bytes(watchlist.read_bytes())
        foreign_journal = hot_journal(foreign)
        before = foreign.read_bytes(), foreign_journal.read_bytes()
        expect_error(
            "storage_schema",
            lambda: app.enqueue(
                foreign, watchlist, journal, manifest, saved[0]["signal_id"], "foreign", **timeout
            ),
        )
        assert (foreign.read_bytes(), foreign_journal.read_bytes()) == before
        # The matching CMTY owner must retain its genuine crash recovery path.
        owned = root / "owned.db"
        store.initialize(owned, **timeout)
        hot_journal(owned)
        assert (
            app.enqueue(
                owned,
                watchlist,
                journal,
                manifest,
                saved[0]["signal_id"],
                "owner-recovery",
                **timeout,
            )["result"]
            == "recorded"
        )
        assert store.verify(owned, **timeout)["counts"] == {"alerts": 1, "evidence": 1}
        results.append("foreign-hot-journal-preserved-genuine-owner-recovery")

        # Capture a genuinely admitted receipt without issuing synthetic private authority.
        captured = []

        class Capture(Exception):
            pass

        def capture(path, receipt, budget):
            captured.append((receipt, budget))
            raise Capture

        with patch.object(store, "_enqueue_verified", capture):
            try:
                app.enqueue(
                    outbox,
                    watchlist,
                    journal,
                    manifest,
                    saved[0]["signal_id"],
                    "receipt-deadline",
                    **timeout,
                )
            except Capture:
                pass
        receipt, budget = captured.pop()
        budget.deadline = 0
        with patch.object(store, "_connect", side_effect=AssertionError("writer opened")):
            expect_error(
                "unsupported_evidence",
                lambda: store._enqueue_verified(outbox, receipt, store.Budget(args.timeout)),
            )
            expect_error(
                "storage_timeout", lambda: store._enqueue_verified(outbox, receipt, budget)
            )
        assert outbox.read_bytes() == frozen
        results.append("issuing-budget-authority-before-writer-and-expiration")

        # Timeout after a complete independent reopened fold must block publication.
        budget, fold = store.Budget(args.timeout), store._verify
        calls = []
        destination = root / "expired-copy.db"

        def expire_last(db, supplied):
            assert supplied is budget and not destination.exists()
            calls.append(db)
            counts = fold(db, supplied)
            if len(calls) == 3:
                supplied.deadline = 0
            return counts

        with patch.object(store, "_verify", expire_last):
            expect_error(
                "storage_timeout", lambda: store.backup(outbox, destination, _budget=budget)
            )
        assert len({id(connection) for connection in calls}) == 3
        assert not destination.exists()
        assert not list(root.glob(".cmt-watchlist-alert-outbox-*.tmp"))
        assert outbox.read_bytes() == frozen
        results.append("three-distinct-folds-expiry-before-publication")

        # Link-time resource failure rolls back only the private provisional; retry is healthy.
        destination = root / "retry-copy.db"
        with patch.object(store.os, "link", side_effect=OSError(28, "controlled disk-full")):
            expect_error("storage_io", lambda: store.backup(outbox, destination, **timeout))
        assert not destination.exists()
        assert not list(root.glob(".cmt-watchlist-alert-outbox-*.tmp"))
        assert store.backup(outbox, destination, **timeout)["counts"] == {
            "alerts": 2,
            "evidence": 2,
        }
        assert store.verify(destination, **timeout)["counts"] == {"alerts": 2, "evidence": 2}
        results.append("disk-full-publication-safe-cleanup-and-retry")

        # A local valid copy grants no original-backed recompute when originals disappear.
        parked = root / "parked.db"
        journal.rename(parked)
        try:
            assert store.verify(outbox, **timeout)["counts"] == {"alerts": 2, "evidence": 2}
            expect_error(
                "storage_missing",
                lambda: app.recompute(
                    outbox, watchlist, journal, manifest, saved[0]["alert_id"], **timeout
                ),
            )
        finally:
            parked.rename(journal)
        assert (watchlist.read_bytes(), journal.read_bytes()) == originals
        results.append("local-verification-is-not-original-authority")

    print(encoded({"probe": "p8c-independent-reviewer", "result": "PASS", "checks": results}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
