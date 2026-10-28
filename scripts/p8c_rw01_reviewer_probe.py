"""Independent RW-01 reviewer probe; public original admission and stdlib oracles.

Run: python scripts/p8c_rw01_reviewer_probe.py --fixtures tests/fixtures --timeout 5
SQL mutation is confined to a clearly labelled local-outbox corruption negative.
Failure injection wraps sqlite3.connect, not production writer/admission helpers.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import multiprocessing
import sqlite3
import sys
import tempfile
import time
from contextlib import closing, contextmanager
from functools import partial
from pathlib import Path
from unittest.mock import patch

from card_market_tracker.watchlist import application as wa
from card_market_tracker.watchlist import storage as ws
from card_market_tracker.watchlist_alerts import application as aa
from card_market_tracker.watchlist_alerts import storage as als
from card_market_tracker.watchlist_alerts.errors import OutboxError
from card_market_tracker.watchlist_journal import application as ja
from card_market_tracker.watchlist_journal import storage as js

PRODUCT = "541b9d13-9669-4973-8413-397bea14c045"
OTHER = "b980e1f7-9bae-432e-b02a-182dbcca478d"


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )


def identity(signal, alias):
    payload = {"identity_version": 1, "signal_id": signal, "destination_key": alias}
    return (
        "walt1_"
        + hashlib.sha256(
            b"CMT_WATCHLIST_ALERT_V1\x00" + canonical(payload).encode("ascii")
        ).hexdigest()
    )


def original(
    directory,
    manifest,
    *,
    change=None,
    series="review-series",
    token="a",
    product=PRODUCT,
    revision=1,
):
    directory.mkdir()
    watch, journal = directory / "watch.db", directory / "journal.db"
    ws.initialize(watch)
    config = {"target_price_minor": 1000, "restock_enabled": True, **(change or {})}
    entry = wa.add(watch, manifest, product, config, request_token="review-create")["entry"]
    if revision == 2:
        entry = wa.update(
            watch,
            manifest,
            entry["watch_id"],
            config,
            expected_revision=1,
            request_token="review-update",
        )["entry"]
    js.initialize(journal)
    previous = None
    for index, stock in enumerate(("OUT_OF_STOCK", "AVAILABLE"), 1):
        current = {
            "version": 1,
            "provenance": "synthetic",
            "sample_id": f"{token}-{index}",
            "cmt_id": product,
            "series_key": series,
            "observed_at": f"2026-10-23T09:0{index}:00Z",
            "currency": "EUR",
            "unit_price_minor": 800,
            "shipping_minor": 100,
            "stock": stock,
        }
        result = ja.record(
            journal,
            watch,
            manifest,
            entry["watch_id"],
            current,
            previous,
            revision=revision,
            as_of=current["observed_at"],
        )
        previous = current
    signal = next(
        key
        for key in result["signal_ids"]
        if js.signal_get(journal, key)["signal"]["rule"] == "price"
    )
    return {
        "watch": watch,
        "journal": journal,
        "manifest": manifest,
        "entry": entry,
        "signal": signal,
        "sample": current,
    }


def ancestry_original(directory, manifest, earlier):
    """Genuine journals share the selected pair snapshots but retain different ancestry."""
    directory.mkdir()
    watch, journal = directory / "watch.db", directory / "journal.db"
    ws.initialize(watch)
    entry = wa.add(
        watch,
        manifest,
        PRODUCT,
        {"target_price_minor": 1000, "restock_enabled": True},
        request_token="same-id-original",
    )["entry"]
    js.initialize(journal)
    samples = [
        {
            "version": 1,
            "provenance": "synthetic",
            "sample_id": f"ancestry-{index}",
            "cmt_id": PRODUCT,
            "series_key": "ancestry-series",
            "observed_at": f"2026-10-23T08:0{index}:00Z",
            "currency": "EUR",
            "unit_price_minor": 800,
            "shipping_minor": 100,
            "stock": stock,
        }
        for index, stock in enumerate(("AVAILABLE", "OUT_OF_STOCK", "AVAILABLE"), 1)
    ]
    for index in range(0 if earlier else 1, 3):
        result = ja.record(
            journal,
            watch,
            manifest,
            entry["watch_id"],
            samples[index],
            None if index == 0 else samples[index - 1],
            revision=1,
            as_of=samples[index]["observed_at"],
        )
    signal = next(
        key
        for key in result["signal_ids"]
        if js.signal_get(journal, key)["signal"]["rule"] == "price"
    )
    return {
        "watch": watch,
        "journal": journal,
        "manifest": manifest,
        "entry": entry,
        "signal": signal,
        "sample": samples[-1],
    }


def admit(outbox, source, alias="review-preview", timeout=2.0):
    result = aa.enqueue(
        outbox,
        source["watch"],
        source["journal"],
        source["manifest"],
        source["signal"],
        alias,
        timeout=timeout,
    )
    assert result["alert_id"] == identity(source["signal"], alias)
    return result


def unchanged_sources(*sources):
    return tuple(p.read_bytes() for s in sources for p in (s["watch"], s["journal"]))


def retained(outbox, alert, timeout):
    return (
        outbox.read_bytes(),
        als.get(outbox, alert, timeout=timeout),
        als.evidence_get(outbox, alert, timeout=timeout),
        als.list_alerts(outbox, timeout=timeout),
    )


def error(category, operation):
    try:
        operation()
    except OutboxError as exc:
        assert exc.category == category, (category, exc.category)
        assert exc.exit_code == (2 if category in ("identity_conflict", "replay_conflict") else 1)
        return
    raise AssertionError("Expected " + category)


def healthy(outbox, count, destination, timeout):
    expected = {"alerts": count, "evidence": count}
    assert als.verify(outbox, timeout=timeout)["counts"] == expected
    # Own whole-entry consistency oracle over public retained evidence.
    entries = {}
    for row in als.list_alerts(outbox, timeout=timeout)["items"]:
        evidence = als.evidence_get(outbox, row["alert_id"], timeout=timeout)["evidence"]
        before = evidence["predecessor"]["snapshot"]["entry"]
        entry = evidence["current"]["snapshot"]["entry"]
        assert canonical(before) == canonical(entry)
        key = (entry["watch_id"], entry["revision"])
        assert entries.setdefault(key, canonical(entry)) == canonical(entry)
    assert als.backup(outbox, destination, timeout=timeout)["counts"] == expected
    assert als.verify(destination, timeout=timeout)["counts"] == expected


def race_worker(outbox, source, ready, start, result, timeout):
    ready.put(True)
    if not start.wait(10):
        result.put({"fatal": "start deadline"})
        return
    try:
        saved = admit(outbox, source, timeout=timeout)
        result.put({"result": saved["result"]})
    except OutboxError as exc:
        result.put({"error": exc.category, "exit": exc.exit_code})


@contextmanager
def injected_fault(outbox, stage, mode, timeout):
    connect, monotonic = sqlite3.connect, time.monotonic
    reached, expired = [], [False]

    class FaultConnection(sqlite3.Connection):
        def execute(self, sql, parameters=()):
            if sql == stage or sql.startswith(stage):
                assert self.in_transaction
                reached.append(sql)
                if mode == "io":
                    raise sqlite3.OperationalError("controlled reviewer failure")
                expired[0] = True
            return super().execute(sql, parameters)

    def controlled_connect(database, *positional, **kwargs):
        if str(database).startswith(outbox.as_uri() + "?"):
            kwargs["factory"] = FaultConnection
        return connect(database, *positional, **kwargs)

    def clock():
        return monotonic() + (timeout + 1 if expired[0] else 0)

    with patch("sqlite3.connect", controlled_connect), patch("time.monotonic", clock):
        yield reached


def run(args):
    manifest = json.loads((args.fixtures / "synthetic_manifest.json").read_text("utf-8"))
    checks = []
    timeout = args.timeout
    with tempfile.TemporaryDirectory(prefix="cmt-rw01-reviewer-") as raw:
        root = Path(raw)
        base = original(root / "base", manifest)
        conflict = original(root / "conflict", manifest, change={"target_price_minor": 1200})
        changed_manifest = copy.deepcopy(manifest)
        next(e for e in changed_manifest["entities"] if e.get("kind") == "card")["card_number"] = (
            "REVIEW-002"
        )
        variants = [
            ("target", {"change": {"target_price_minor": 1200}}),
            ("priority", {"change": {"priority": "high"}}),
            ("freshness", {"change": {"max_age_seconds": 120}}),
            ("restock", {"change": {"restock_enabled": False}}),
            ("canonical-identity", {"manifest": changed_manifest}),
        ]
        for name, variant_options in variants:
            for distinct in ("signal", "destination", "series"):
                directory = root / (name + "-" + distinct)
                options = dict(variant_options)
                selected_manifest = options.pop("manifest", manifest)
                if distinct == "series":
                    options["series"] = "review-other-series"
                source = original(directory, selected_manifest, **options)
                assert source["entry"]["watch_id"] == base["entry"]["watch_id"]
                assert source["entry"]["revision"] == base["entry"]["revision"]
                assert canonical(source["entry"]) != canonical(base["entry"])
                assert source["signal"] != base["signal"]
                outbox = root / (name + "-" + distinct + ".db")
                als.initialize(outbox)
                saved = admit(outbox, base, timeout=timeout)
                state = retained(outbox, saved["alert_id"], timeout)
                sources = unchanged_sources(base, source)
                alias = "review-other" if distinct == "destination" else "review-preview"
                error("identity_conflict", partial(admit, outbox, source, alias, timeout))
                assert retained(outbox, saved["alert_id"], timeout) == state
                healthy(outbox, 1, outbox.with_suffix(".backup"), timeout)
                assert unchanged_sources(base, source) == sources
                checks.append(name + "-" + distinct)
        for name, options, alias in (
            ("same-semantic-destination", {}, "review-other"),
            ("same-semantic-signal", {"token": "independent"}, "review-preview"),
            ("same-semantic-series", {"series": "same-entry-series"}, "review-preview"),
            ("revision", {"revision": 2, "change": {"target_price_minor": 1300}}, "review-preview"),
            (
                "product",
                {"product": OTHER, "change": {"target_price_minor": 1300}},
                "review-preview",
            ),
        ):
            source = original(root / name, manifest, **options)
            if name.startswith("same-semantic"):
                assert canonical(source["entry"]) == canonical(base["entry"])
            outbox = root / (name + ".db")
            als.initialize(outbox)
            sources = unchanged_sources(base, source)
            assert admit(outbox, base, timeout=timeout)["result"] == "recorded"
            assert admit(outbox, source, alias, timeout)["result"] == "recorded"
            healthy(outbox, 2, outbox.with_suffix(".backup"), timeout)
            assert unchanged_sources(base, source) == sources
            checks.append(name)
        # Ancient replay following legitimate source growth and a rejected conflict.
        outbox = root / "ancient.db"
        als.initialize(outbox)
        saved = admit(outbox, base, timeout=timeout)
        state = retained(outbox, saved["alert_id"], timeout)
        previous = base["sample"]
        for index, stock in enumerate(("OUT_OF_STOCK", "AVAILABLE"), 3):
            sample = dict(
                previous,
                sample_id=f"grown-{index}",
                stock=stock,
                observed_at=f"2026-10-23T09:0{index}:00Z",
            )
            ja.record(
                base["journal"],
                base["watch"],
                manifest,
                base["entry"]["watch_id"],
                sample,
                previous,
                revision=1,
                as_of=sample["observed_at"],
            )
            previous = sample
        wa.update(
            base["watch"],
            manifest,
            base["entry"]["watch_id"],
            {"target_price_minor": 1700},
            expected_revision=1,
            request_token="grown-revision",
        )
        sources = unchanged_sources(base, conflict)
        error("identity_conflict", lambda: admit(outbox, conflict, timeout=timeout))
        assert admit(outbox, base, timeout=timeout)["result"] == "replayed"
        assert retained(outbox, saved["alert_id"], timeout) == state
        healthy(outbox, 1, outbox.with_suffix(".backup"), timeout)
        assert unchanged_sources(base, conflict) == sources
        checks.append("ancient-replay")

        # Same signal/alert identity, valid different journal ancestry: replay wins.
        left = ancestry_original(root / "ancestry-left", manifest, False)
        right = ancestry_original(root / "ancestry-right", manifest, True)
        assert left["signal"] == right["signal"]
        outbox = root / "same-id.db"
        als.initialize(outbox)
        saved = admit(outbox, left, timeout=timeout)
        state, sources = (
            retained(outbox, saved["alert_id"], timeout),
            unchanged_sources(left, right),
        )
        error("replay_conflict", partial(admit, outbox, right, timeout=timeout))
        assert retained(outbox, saved["alert_id"], timeout) == state
        healthy(outbox, 1, outbox.with_suffix(".backup"), timeout)
        assert unchanged_sources(left, right) == sources
        checks.append("same-id-replay-conflict-precedence")

        # Real spawned processes enter the public operation from one release gate.
        outbox = root / "race.db"
        als.initialize(outbox)
        sources = unchanged_sources(base, conflict)
        context = multiprocessing.get_context("spawn")
        ready, results, start = context.Queue(), context.Queue(), context.Event()
        processes = [
            context.Process(target=race_worker, args=(outbox, item, ready, start, results, timeout))
            for item in (base, conflict)
        ]
        try:
            for process in processes:
                process.start()
            for _ in processes:
                assert ready.get(timeout=15) is True
            start.set()
            observed = [results.get(timeout=20) for _ in processes]
            for process in processes:
                process.join(timeout=10)
                assert process.exitcode == 0
        finally:
            for process in processes:
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=5)
            ready.close()
            results.close()
        assert sum(row.get("result") == "recorded" for row in observed) == 1, observed
        assert (
            sum(row.get("error") == "identity_conflict" and row["exit"] == 2 for row in observed)
            == 1
        ), observed
        healthy(outbox, 1, outbox.with_suffix(".backup"), timeout)
        assert unchanged_sources(base, conflict) == sources
        checks.append("atomic-process-race")

        # Controlled negative: SQL graft only in local outboxes, never sources.
        corrupt, separate = root / "corrupt.db", root / "separate.db"
        als.initialize(corrupt)
        als.initialize(separate)
        admit(corrupt, base, timeout=timeout)
        admit(separate, conflict, timeout=timeout)
        with closing(sqlite3.connect(corrupt)) as left, closing(sqlite3.connect(separate)) as right:
            left.execute(
                "INSERT INTO watchlist_alerts VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                right.execute("SELECT * FROM watchlist_alerts").fetchone(),
            )
            left.execute(
                "INSERT INTO watchlist_alert_evidence VALUES (?,?,?)",
                right.execute("SELECT * FROM watchlist_alert_evidence").fetchone(),
            )
            left.commit()
        before, sources = corrupt.read_bytes(), unchanged_sources(base, conflict)
        error("storage_corrupt", lambda: als.verify(corrupt, timeout=timeout))
        error("storage_corrupt", lambda: admit(corrupt, base, timeout=timeout))
        error("storage_corrupt", lambda: admit(corrupt, conflict, "other", timeout))
        error(
            "storage_corrupt",
            lambda: als.backup(corrupt, root / "must-not-publish.db", timeout=timeout),
        )
        assert not (root / "must-not-publish.db").exists()
        assert corrupt.read_bytes() == before
        assert unchanged_sources(base, conflict) == sources
        checks.append("preexisting-corruption-precedence")

        # Faults affect only outbox SQLite connections during a public enqueue.
        # A stdlib fake monotonic clock expires the same issued Budget after the
        # first row has been inserted. No production helper or Budget is patched.
        same = original(root / "failure-original", manifest, token="fresh-independent")

        for stage, mode in (
            ("INSERT INTO watchlist_alerts ", "io"),
            ("INSERT INTO watchlist_alert_evidence ", "io"),
            ("COMMIT", "io"),
            ("INSERT INTO watchlist_alert_evidence ", "timeout"),
        ):
            outbox = root / ("fault-" + str(len(checks)) + ".db")
            als.initialize(outbox)
            saved = admit(outbox, base, timeout=timeout)
            before = retained(outbox, saved["alert_id"], timeout)
            sources = unchanged_sources(base, same)
            with injected_fault(outbox, stage, mode, timeout) as reached:
                error(
                    "storage_io" if mode == "io" else "storage_timeout",
                    partial(admit, outbox, same, timeout=timeout),
                )
            assert len(reached) == 1, reached
            assert retained(outbox, saved["alert_id"], timeout) == before
            healthy(outbox, 1, outbox.with_suffix(".backup"), timeout)
            assert unchanged_sources(base, same) == sources
            checks.append("precommit-" + mode + "-" + stage.strip())
        return checks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", type=Path, default=Path("tests/fixtures"))
    parser.add_argument("--timeout", type=float, default=2.0)
    args = parser.parse_args()
    if not 0 < args.timeout <= 5:
        parser.error("timeout must be positive and at most 5")
    checks = run(args)
    print(
        canonical(
            {
                "result": "PASS",
                "python": sys.version.split()[0],
                "sqlite": sqlite3.sqlite_version,
                "checks": checks,
                "count": len(checks),
            }
        )
    )


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
