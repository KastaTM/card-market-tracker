"""Independent P5b acceptance oracle; emits a commit/tree-bound JSON report.

Uses only stdlib. Run with the project's Python 3.13 environment. Product CLI
and injection workers run in separate audited processes against private DBs.
--provisional explicitly permits a dirty tree and never produces final QA PASS.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import runpy
import sqlite3
import subprocess
import sys
import tempfile
import time
import traceback
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
POLICY = "watchlist-rules-v1"
SCRIPT = Path(__file__).resolve()


def canonical(value: Any) -> str:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    )


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def identity(prefix: str, domain: str, value: Any) -> str:
    return prefix + sha(domain.encode("ascii") + bytes([0]) + canonical(value).encode("utf-8"))


def oracle(
    entry: dict[str, Any], current: dict[str, Any], previous: Any, clock: str
) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Independent full P5a rule result plus P5b input identity, no product helpers."""
    sid = identity(
        "wjs1_",
        "CMT_WATCHLIST_JOURNAL_SEQUENCE_V1",
        {
            "watch_id": entry["watch_id"],
            "revision": entry["revision"],
            "policy_version": POLICY,
            "series_key": current["series_key"],
        },
    )
    snapshot = {
        "version": 1,
        "sequence_id": sid,
        "policy_version": POLICY,
        "entry": entry,
        "current": current,
        "previous": previous,
        "as_of": clock,
    }
    result = {
        "version": 1,
        "policy_version": POLICY,
        "watch_id": entry["watch_id"],
        "revision": entry["revision"],
        "cmt_id": entry["cmt_id"],
        "as_of": clock,
        "current_sample": {
            "sample_id": current["sample_id"],
            "digest": sha(canonical(current).encode()),
        },
        "previous_sample": None
        if previous is None
        else {"sample_id": previous["sample_id"], "digest": sha(canonical(previous).encode())},
    }
    if not entry["enabled"]:
        result.update(result="SKIPPED", rules=[], reason="disabled")
    else:

        def fresh(sample: Any) -> bool:
            return (
                sample is not None
                and 0
                <= (
                    datetime.fromisoformat(clock) - datetime.fromisoformat(sample["observed_at"])
                ).total_seconds()
                <= entry["max_age_seconds"]
            )

        rules = []
        if entry["target_price_minor"] is not None:
            if not fresh(current):
                status, reason = "INDETERMINATE", "current_stale"
            elif current["stock"] == "OUT_OF_STOCK":
                status, reason = "NO_MATCH", "current_out_of_stock"
            elif current["stock"] == "UNKNOWN":
                status, reason = "INDETERMINATE", "current_stock_unknown"
            elif current["unit_price_minor"] is None or current["shipping_minor"] is None:
                status, reason = "INDETERMINATE", "price_unknown"
            elif (
                current["unit_price_minor"] + current["shipping_minor"]
                <= entry["target_price_minor"]
            ):
                status, reason = "MATCH", "at_or_below_target"
            else:
                status, reason = "NO_MATCH", "above_target"
            rules.append({"rule": "price", "result": status, "reason": reason})
        if entry["restock_enabled"]:
            if not fresh(current):
                status, reason = "INDETERMINATE", "current_stale"
            elif current["stock"] == "OUT_OF_STOCK":
                status, reason = "NO_MATCH", "current_out_of_stock"
            elif current["stock"] == "UNKNOWN":
                status, reason = "INDETERMINATE", "current_stock_unknown"
            elif previous is None:
                status, reason = "INDETERMINATE", "previous_missing"
            elif not fresh(previous):
                status, reason = "INDETERMINATE", "previous_stale"
            elif previous["stock"] == "UNKNOWN":
                status, reason = "INDETERMINATE", "previous_stock_unknown"
            elif previous["stock"] == "OUT_OF_STOCK":
                status, reason = "MATCH", "restocked"
            else:
                status, reason = "NO_MATCH", "already_available"
            rules.append({"rule": "restock", "result": status, "reason": reason})
        statuses = {rule["result"] for rule in rules}
        result.update(
            rules=rules,
            result="MATCH"
            if "MATCH" in statuses
            else "INDETERMINATE"
            if "INDETERMINATE" in statuses
            else "NO_MATCH",
        )
    return snapshot, result, identity("wje1_", "CMT_WATCHLIST_JOURNAL_EVALUATION_V1", snapshot)


def fold(prior: Any, current: tuple[Any, Any, str]) -> list[dict[str, Any]]:
    if prior is None:
        return []
    old, old_result, old_id = prior
    new, result, eid = current
    clock = datetime.fromisoformat(new["as_of"])
    if any(
        not 0
        <= (clock - datetime.fromisoformat(row["current"]["observed_at"])).total_seconds()
        <= new["entry"]["max_age_seconds"]
        for row in (old, new)
    ):
        return []
    old_rules = {row["rule"]: row["result"] for row in old_result["rules"]}
    signals = []
    for row in result["rules"]:
        if old_rules.get(row["rule"]) == "NO_MATCH" and row["result"] == "MATCH":
            body = {
                "version": 1,
                "kind": "WATCHLIST_RULE_ENTERED_MATCH",
                "mode": "synthetic",
                "sequence_id": new["sequence_id"],
                "rule": row["rule"],
                "from_evaluation_id": old_id,
                "to_evaluation_id": eid,
            }
            signals.append(
                {**body, "signal_id": identity("wsig1_", "CMT_WATCHLIST_SIGNAL_V1", body)}
            )
    return signals


def worker(request_path: Path, start: Path | None) -> int:
    request = json.loads(request_path.read_text(encoding="utf-8"))
    attempts: list[str] = []

    def audit(event: str, args: Any) -> None:
        if event.startswith("socket."):
            attempts.append(event)
            raise RuntimeError("QA rejects product socket access")

    sys.addaudithook(audit)
    sys.path.insert(0, str(ROOT / "src"))
    try:
        if start is not None:
            deadline = time.monotonic() + 15
            while not start.exists():
                if time.monotonic() > deadline:
                    raise TimeoutError("worker start gate")
                time.sleep(0.005)
        if request["mode"] == "cli":
            from card_market_tracker.cli import main

            return main(request["args"])
        from card_market_tracker.watchlist_journal import application, storage

        if request["mode"] == "midfold-timeout":
            load = storage._load_evaluation

            def slow_load(*values: Any) -> Any:
                time.sleep(0.03)
                return load(*values)

            storage._load_evaluation = slow_load
            try:
                storage.verify(Path(request["journal"]), timeout=0.02)
            except Exception as error:
                print(canonical({"category": getattr(error, "category", type(error).__name__)}))
                return 0
            raise AssertionError("mid-fold deadline returned success")
        if request["mode"] == "cross-series-conflict":
            try:
                storage._record_validated(Path(request["journal"]), request["snapshot"])
            except Exception as error:
                print(canonical({"category": getattr(error, "category", type(error).__name__)}))
                return 0
            raise AssertionError("cross-series revision identity changed")
        original = storage._execute

        def injected(db: Any, budget: Any, sql: str, values: Any = ()) -> Any:
            if sql.startswith(request["stage"]):
                if request["mode"] == "crash":
                    original(db, budget, sql, values)
                    request_path.with_suffix(".audit.json").write_text(
                        canonical({"socket_attempts": attempts}), encoding="utf-8"
                    )
                    os._exit(73)
                raise OSError("QA injected local failure")
            return original(db, budget, sql, values)

        storage._execute = injected
        try:
            application.record(
                Path(request["journal"]),
                Path(request["origin"]),
                request["manifest"],
                request["watch_id"],
                request["current"],
                request["previous"],
                revision=1,
                as_of=request["current"]["observed_at"],
                timeout=5,
            )
        except Exception as error:
            print(canonical({"category": getattr(error, "category", type(error).__name__)}))
            return 0
        raise AssertionError("injected failure unexpectedly committed")
    finally:
        request_path.with_suffix(".audit.json").write_text(
            canonical({"socket_attempts": attempts}), encoding="utf-8"
        )


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-head")
    parser.add_argument("--expected-tree")
    parser.add_argument("--provisional", action="store_true")
    parser.add_argument("--worker", type=Path, help=argparse.SUPPRESS)
    parser.add_argument("--start", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        return worker(args.worker, args.start)
    if not args.expected_head or not args.expected_tree:
        parser.error("--expected-head and --expected-tree are required")
    checks: list[str] = []
    report: dict[str, Any] = {
        "role": "independent QA; no product authorship",
        "profile_requested": "gpt-6.1-sol/high",
        "backend_internals": "unverified",
        "provisional": args.provisional,
        "expected_head": args.expected_head,
        "expected_tree": args.expected_tree,
        "checks": checks,
    }

    def check(name: str, condition: Any = True) -> None:
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    before = (git("rev-parse", "HEAD"), git("rev-parse", "HEAD^{tree}"))
    try:
        check("candidate head/tree before", before == (args.expected_head, args.expected_tree))
        dirty = git("diff", "--name-only", "HEAD")
        check("tracked worktree clean or explicitly provisional", args.provisional or not dirty)
        check(
            "product, fixtures and QA script all committed or provisional",
            args.provisional
            or not git(
                "status",
                "--porcelain",
                "--untracked-files=all",
                "--",
                "src/card_market_tracker",
                "tests/fixtures",
                "scripts/p5b_qa_probe.py",
            ),
        )
        vectors = json.loads((FIXTURES / "p5b_identity_vectors_v1.json").read_text())["vectors"]
        check(
            "literal golden preimages independently hashed",
            all(
                vector["preimage_text"].encode()
                == vector["domain"].encode() + bytes([0]) + canonical(vector["object"]).encode()
                and vector["id"].split("_", 1)[1] == sha(vector["preimage_text"].encode())
                for vector in vectors.values()
            ),
        )
        public_digest = sha(
            canonical(vectors["baseline"]["object"]["entry"]["canonical_identity"]).encode()
        )
        scanner = runpy.run_path(str(ROOT / "scripts" / "check_secret_scan.py"))
        detector = scanner["_reviewed_public_candidate"]
        candidate = {
            "type": "Hex High Entropy String",
            "hashed_secret": hashlib.sha1(public_digest.encode()).hexdigest(),
        }
        public_path = "tests/fixtures/p5b_identity_vectors_v1.json"
        check(
            "secret-scan exception is independently derived exact detector/path/value",
            scanner["_PUBLIC_DIGESTS"][public_path] == {public_digest}
            and detector(public_path, candidate)
            and not detector("tests/fixtures/unreviewed.json", candidate)
            and not detector(public_path, {**candidate, "type": "Secret Keyword"})
            and not detector(public_path, {**candidate, "hashed_secret": "0" * 40}),
        )
        with tempfile.TemporaryDirectory(prefix="cmt-p5b-independent-qa-") as temporary:
            folder = Path(temporary)
            counter = 0
            audits: list[Path] = []
            logs: list[dict[str, Any]] = []

            def launch(
                request: dict[str, Any], start: Path | None = None
            ) -> tuple[subprocess.Popen[str], Path]:
                nonlocal counter
                counter += 1
                path = folder / f"request-{counter}.json"
                path.write_text(canonical(request), encoding="utf-8")
                audits.append(path.with_suffix(".audit.json"))
                command = [sys.executable, "-I", str(SCRIPT), "--worker", str(path)]
                if start:
                    command += ["--start", str(start)]
                return subprocess.Popen(
                    command, cwd=folder, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                ), path

            def finish(
                child: tuple[subprocess.Popen[str], Path], expected: int | None = 0
            ) -> tuple[dict[str, Any], int]:
                process, path = child
                out, err = process.communicate(timeout=30)
                if expected is not None and process.returncode != expected:
                    raise AssertionError((path.name, process.returncode, out, err))
                for line in err.splitlines():
                    logs.append(json.loads(line))
                return json.loads(out), process.returncode

            def call(
                group: str, operation: str, db: Path, *flags: Any, expected: int | None = 0
            ) -> tuple[dict[str, Any], int]:
                db_flag = "--journal-db" if group == "watchlist-journal" else "--watchlist-db"
                return finish(
                    launch(
                        {
                            "mode": "cli",
                            "args": [
                                group,
                                operation,
                                db_flag,
                                str(db),
                                "--timeout",
                                "5",
                                *map(str, flags),
                            ],
                        }
                    ),
                    expected,
                )

            origin, journal = folder / "origin.db", folder / "journal.db"
            manifest_path = FIXTURES / "synthetic_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            call("watchlist", "init", origin)
            entry = call(
                "watchlist",
                "add",
                origin,
                "--manifest",
                manifest_path,
                "--cmt-id",
                "541b9d13-9669-4973-8413-397bea14c045",
                "--input",
                FIXTURES / "synthetic_watchlist_config.json",
                "--request-token",
                "qa-origin",
            )[0]["entry"]
            call("watchlist-journal", "init", journal)
            origin_digest = sha(origin.read_bytes())
            check(
                "separate CMTQ owner, strict tables and exact object count", inspect_schema(journal)
            )
            base = json.loads(
                (FIXTURES / "synthetic_watchlist_current.json").read_text(encoding="utf-8")
            )
            samples = []
            for index, stock in enumerate(
                ("OUT_OF_STOCK", "AVAILABLE", "AVAILABLE", "OUT_OF_STOCK", "AVAILABLE")
            ):
                sample = {
                    **base,
                    "sample_id": f"qa-sensitive-{index}",
                    "observed_at": f"2026-10-23T12:0{index}:00Z",
                    "stock": stock,
                }
                path = folder / f"sample-{index}.json"
                path.write_text(canonical(sample), encoding="utf-8")
                samples.append((sample, path))

            def record_args(
                index: int,
                *,
                target: Path = journal,
                sample_path: Path | None = None,
                previous: Path | None = None,
                revision: int = 1,
                chosen_manifest: Path = manifest_path,
                as_of: str | None = None,
            ) -> list[str]:
                flags = [
                    "watchlist-journal",
                    "record",
                    "--journal-db",
                    str(target),
                    "--timeout",
                    "5",
                    "--watchlist-db",
                    str(origin),
                    "--manifest",
                    str(chosen_manifest),
                    "--watch-id",
                    entry["watch_id"],
                    "--revision",
                    str(revision),
                    "--sample",
                    str(sample_path or samples[index][1]),
                    "--as-of",
                    as_of or samples[index][0]["observed_at"],
                ]
                if previous or index:
                    flags += ["--previous", str(previous or samples[index - 1][1])]
                return flags

            def record(index: int, **kwargs: Any) -> dict[str, Any]:
                return finish(launch({"mode": "cli", "args": record_args(index, **kwargs)}))[0]

            records, expected_signals, prior = [], [], None
            for index in range(5):
                record_result = record(index)
                expected = oracle(
                    entry,
                    samples[index][0],
                    None if index == 0 else samples[index - 1][0],
                    samples[index][0]["observed_at"],
                )
                signals = fold(prior, expected)
                stored = call(
                    "watchlist-journal",
                    "get",
                    journal,
                    "--evaluation-id",
                    record_result["evaluation_id"],
                )[0]["evaluation"]
                check(
                    f"checkpoint {index}: independent snapshot/result/identity/fold",
                    stored["snapshot"] == expected[0]
                    and stored["evaluation_result"] == expected[1]
                    and record_result["evaluation_id"] == expected[2]
                    and sorted(record_result["signal_ids"])
                    == sorted(item["signal_id"] for item in signals),
                )
                records.append(record_result)
                expected_signals.extend(signals)
                prior = expected
            actual_signals = call("watchlist-journal", "signal-list", journal)[0]["signals"]
            check(
                "two independent rules and two episodes exact signal set",
                sorted(actual_signals, key=lambda row: row["signal_id"])
                == sorted(expected_signals, key=lambda row: row["signal_id"])
                and len(actual_signals) == 4,
            )
            # Independent series for continuity boundaries; retained historical
            # P5a revision 1 remains explicit authority throughout.
            for scenario, stocks, minutes, offsets, expected_count in (
                ("first-match", ("AVAILABLE",), (0,), (0,), 0),
                ("unknown-reset", ("UNKNOWN", "AVAILABLE"), (0, 1), (0, 0), 0),
                ("stale-prior", ("OUT_OF_STOCK", "AVAILABLE"), (0, 1441), (0, 0), 0),
                ("freshness-inclusive", ("OUT_OF_STOCK", "AVAILABLE"), (0, 1440), (0, 0), 2),
                (
                    "indeterminate-reset",
                    ("OUT_OF_STOCK", "AVAILABLE", "AVAILABLE"),
                    (0, 1, 2),
                    (1441, 1441, 1441),
                    0,
                ),
            ):
                checkpoint_prior = None
                actual_ids, oracle_ids = [], []
                previous_path = None
                for position, (stock, minute, offset) in enumerate(
                    zip(stocks, minutes, offsets, strict=True)
                ):
                    from datetime import timedelta

                    instant = datetime.fromisoformat("2026-10-20T12:00:00Z") + timedelta(
                        minutes=minute
                    )
                    observed = instant.isoformat().replace("+00:00", "Z")
                    clock = (instant + timedelta(minutes=offset)).isoformat().replace("+00:00", "Z")
                    sample = {
                        **base,
                        "series_key": "qa-" + scenario,
                        "sample_id": f"qa-{scenario}-{position}",
                        "stock": stock,
                        "observed_at": observed,
                    }
                    path = folder / f"{scenario}-{position}.json"
                    path.write_text(canonical(sample), encoding="utf-8")
                    flags = record_args(0, sample_path=path, previous=previous_path, as_of=clock)
                    answer = finish(launch({"mode": "cli", "args": flags}))[0]
                    expected = oracle(
                        entry,
                        sample,
                        None if checkpoint_prior is None else checkpoint_prior[0]["current"],
                        clock,
                    )
                    oracle_ids.extend(row["signal_id"] for row in fold(checkpoint_prior, expected))
                    actual_ids.extend(answer["signal_ids"])
                    checkpoint_prior, previous_path = expected, path
                check(
                    "continuity oracle: " + scenario,
                    sorted(actual_ids) == sorted(oracle_ids) and len(actual_ids) == expected_count,
                )
            changed_entry = {**entry, "priority": "low"}
            changed_current = {**samples[0][0], "series_key": "qa-incompatible-series"}
            changed_snapshot = oracle(
                changed_entry, changed_current, None, changed_current["observed_at"]
            )[0]
            unchanged = sha(journal.read_bytes())
            denied, _ = finish(
                launch(
                    {
                        "mode": "cross-series-conflict",
                        "journal": str(journal),
                        "snapshot": changed_snapshot,
                    }
                )
            )
            check(
                "same revision entry cannot fork across series",
                denied["category"] == "identity_conflict"
                and sha(journal.read_bytes()) == unchanged,
            )
            fingerprint = sha(journal.read_bytes())
            replay = record(0)
            check(
                "ancient replay preserves DB bytes/time/head",
                replay == {**records[0], "result": "replayed"}
                and sha(journal.read_bytes()) == fingerprint,
            )

            def reject(name: str, argv: list[str], category: str | None = None) -> None:
                before_bytes = sha(journal.read_bytes())
                result, code = finish(launch({"mode": "cli", "args": argv}), expected=None)
                check(
                    name,
                    code != 0
                    and result["result"] == "error"
                    and (category is None or result["error_category"] == category)
                    and sha(journal.read_bytes()) == before_bytes,
                )

            reject(
                "same sample with changed as_of conflicts",
                record_args(4, as_of="2026-10-23T12:05:00Z"),
                "replay_conflict",
            )
            bad_manifest = copy.deepcopy(manifest)
            bad_manifest["qa_unrelated_extra"] = True
            bad_manifest_path = folder / "bad-manifest.json"
            bad_manifest_path.write_text(canonical(bad_manifest), encoding="utf-8")
            reject(
                "ancient replay revalidates complete original manifest",
                record_args(0, chosen_manifest=bad_manifest_path),
            )
            reject("missing exact original revision rejected", record_args(0, revision=100))
            check(
                "P5a origin unchanged through enabled recording and failure cases",
                sha(origin.read_bytes()) == origin_digest,
            )
            # Revision isolation and disabled validation use an actual P5a mutation.
            call(
                "watchlist",
                "disable",
                origin,
                "--manifest",
                manifest_path,
                "--watch-id",
                entry["watch_id"],
                "--expected-revision",
                "1",
                "--request-token",
                "qa-disable",
            )
            origin_digest = sha(origin.read_bytes())
            malformed = folder / "malformed.json"
            malformed.write_text(
                canonical({**samples[0][0], "unit_price_minor": True}), encoding="utf-8"
            )
            reject(
                "disabled revision still rejects malformed sample",
                record_args(0, revision=2, sample_path=malformed),
            )
            disabled = record(0, revision=2)
            check(
                "explicit revision starts signal-free separate sequence",
                disabled["sequence_id"] != records[0]["sequence_id"]
                and disabled["signals_count"] == 0,
            )
            check(
                "historical enabled revision still replays",
                record(0)["evaluation_id"] == records[0]["evaluation_id"],
            )

            # Synchronized independent process writers, same input then forked successors.
            race_db = folder / "race.db"
            call("watchlist-journal", "init", race_db)
            gate = folder / "race-start"
            pair = [
                launch({"mode": "cli", "args": record_args(0, target=race_db)}, gate)
                for _ in range(2)
            ]
            gate.touch()
            outcomes = [finish(child)[0] for child in pair]
            check(
                "two processes identical: one append one replay",
                sorted(row["result"] for row in outcomes) == ["recorded", "replayed"],
            )
            fork_sample = {**samples[1][0], "sample_id": "qa-fork"}
            fork_path = folder / "fork.json"
            fork_path.write_text(canonical(fork_sample), encoding="utf-8")
            gate = folder / "fork-start"
            pair = [
                launch(
                    {"mode": "cli", "args": record_args(1, target=race_db, sample_path=path)}, gate
                )
                for path in (samples[1][1], fork_path)
            ]
            gate.touch()
            outcomes = [finish(child, expected=None) for child in pair]
            race_counts = call("watchlist-journal", "verify", race_db)[0]["counts"]
            check(
                "two divergent successors: at most one committed with complete fold",
                sorted(code for _, code in outcomes) == [0, 2]
                and race_counts == {"sequences": 1, "evaluations": 2, "signals": 2},
            )

            for stage in (
                "INSERT INTO wl_journal_evaluations",
                "INSERT INTO wl_journal_signals",
                "UPDATE wl_journal_sequences",
                "COMMIT",
            ):
                injected_db = folder / f"injected-{counter}.db"
                call("watchlist-journal", "init", injected_db)
                record(0, target=injected_db)
                before_bytes = sha(injected_db.read_bytes())
                result, _ = finish(
                    launch(
                        {
                            "mode": "inject",
                            "stage": stage,
                            "journal": str(injected_db),
                            "origin": str(origin),
                            "manifest": manifest,
                            "watch_id": entry["watch_id"],
                            "current": samples[1][0],
                            "previous": samples[0][0],
                        }
                    )
                )
                check(
                    "rollback/reopen after " + stage,
                    result["category"] == "storage_io"
                    and sha(injected_db.read_bytes()) == before_bytes
                    and call("watchlist-journal", "verify", injected_db)[0]["counts"]["evaluations"]
                    == 1,
                )
            crash_db = folder / "crash.db"
            call("watchlist-journal", "init", crash_db)
            record(0, target=crash_db)
            crashed, _ = launch(
                {
                    "mode": "crash",
                    "stage": "INSERT INTO wl_journal_signals",
                    "journal": str(crash_db),
                    "origin": str(origin),
                    "manifest": manifest,
                    "watch_id": entry["watch_id"],
                    "current": samples[1][0],
                    "previous": samples[0][0],
                }
            )
            crash_out, crash_err = crashed.communicate(timeout=30)
            check(
                "process interruption occurs after uncommitted signal insertion",
                crashed.returncode == 73 and not crash_out and not crash_err,
            )
            # A crashed DELETE journal may need SQLite's writable recovery before
            # read-only verification; record performs that recovery transaction.
            recovered = record(1, target=crash_db)
            crash_counts = call("watchlist-journal", "verify", crash_db)[0]["counts"]
            check(
                "crash recovery rolls back partial append before retry",
                recovered["signals_count"] == 2
                and crash_counts == {"sequences": 1, "evaluations": 2, "signals": 2},
            )
            slow, _ = finish(launch({"mode": "midfold-timeout", "journal": str(journal)}))
            check(
                "mid-fold deadline never returns partial PASS",
                slow["category"] == "storage_timeout",
            )

            backup = folder / "backup.db"
            restored = folder / "restored.db"
            call("watchlist-journal", "backup", journal, "--destination", backup)
            call("watchlist-journal", "restore", backup, "--destination", restored)
            check(
                "exclusive verified backup/restore exact retained records",
                call(
                    "watchlist-journal",
                    "get",
                    restored,
                    "--evaluation-id",
                    records[1]["evaluation_id"],
                )[0]
                == call(
                    "watchlist-journal",
                    "get",
                    journal,
                    "--evaluation-id",
                    records[1]["evaluation_id"],
                )[0],
            )
            reject(
                "restore refuses existing destination",
                [
                    "watchlist-journal",
                    "restore",
                    "--journal-db",
                    str(backup),
                    "--destination",
                    str(restored),
                ],
                "unsafe_destination",
            )
            collision = folder / "collision.db"
            sidecar = Path(str(collision) + "-journal")
            sidecar.write_bytes(b"QA recovery evidence")
            reject(
                "restore preserves existing destination sidecar",
                [
                    "watchlist-journal",
                    "restore",
                    "--journal-db",
                    str(backup),
                    "--destination",
                    str(collision),
                ],
                "unsafe_destination",
            )
            check(
                "foreign sidecar retained without target publication",
                sidecar.read_bytes() == b"QA recovery evidence" and not collision.exists(),
            )
            hardlink = folder / "hardlink.db"
            os.link(backup, hardlink)
            result, code = call("watchlist-journal", "verify", hardlink, expected=None)
            check(
                "multiply linked database rejected",
                code != 0 and result["error_category"] == "unsafe_destination",
            )
            hardlink.unlink()

            for name, sql, trigger in (
                ("unknown index", "CREATE INDEX qa_extra ON wl_journal_evaluations(as_of)", None),
                (
                    "missing signal",
                    "DELETE FROM wl_journal_signals WHERE rule='price'",
                    "wl_journal_signal_no_delete",
                ),
                (
                    "stale head",
                    "UPDATE wl_journal_sequences SET head_ordinal=1",
                    "wl_journal_sequence_immutable",
                ),
                (
                    "history link",
                    "UPDATE wl_journal_evaluations SET prior_eval_id=NULL WHERE ordinal=2",
                    "wl_journal_evaluation_no_update",
                ),
                (
                    "forged recalculated verdict",
                    "UPDATE wl_journal_evaluations SET "
                    "result_json=replace(result_json,'MATCH','NO_MATCH') WHERE ordinal=2",
                    "wl_journal_evaluation_no_update",
                ),
                (
                    "malformed stored JSON",
                    "UPDATE wl_journal_evaluations SET snapshot_json='{' WHERE ordinal=2",
                    "wl_journal_evaluation_no_update",
                ),
            ):
                tampered = folder / f"tampered-{counter}.db"
                tampered.write_bytes(backup.read_bytes())
                with closing(sqlite3.connect(tampered)) as db, db:
                    db.execute("PRAGMA ignore_check_constraints=ON")
                    saved = (
                        db.execute(
                            "SELECT sql FROM sqlite_master WHERE type='trigger' AND name=?",
                            (trigger,),
                        ).fetchone()
                        if trigger
                        else None
                    )
                    if trigger:
                        db.execute("DROP TRIGGER " + trigger)
                    db.execute(sql)
                    if saved:
                        db.execute(saved[0])
                before_bytes = sha(tampered.read_bytes())
                result, code = call("watchlist-journal", "verify", tampered, expected=None)
                check(
                    "deep verification rejects " + name,
                    code != 0
                    and result["error_category"] in ("storage_schema", "storage_corrupt")
                    and sha(tampered.read_bytes()) == before_bytes,
                )

            call(
                "watchlist-journal",
                "recompute",
                journal,
                "--watchlist-db",
                origin,
                "--manifest",
                manifest_path,
                "--evaluation-id",
                records[1]["evaluation_id"],
            )
            missing_origin = folder / "missing-origin.db"
            result, code = call(
                "watchlist-journal",
                "recompute",
                journal,
                "--watchlist-db",
                missing_origin,
                "--manifest",
                manifest_path,
                "--evaluation-id",
                records[1]["evaluation_id"],
                expected=None,
            )
            check(
                "origin recompute fails missing source while local verify succeeds",
                code != 0
                and not missing_origin.exists()
                and call("watchlist-journal", "verify", journal)[0]["result"] == "ok",
            )
            page = call("watchlist-journal", "list", journal, "--limit", "1")[0]
            next_page = call(
                "watchlist-journal",
                "list",
                journal,
                "--limit",
                "1",
                "--cursor",
                page["next_cursor"],
            )[0]
            check(
                "bounded keyset pages advance",
                len(page["evaluations"]) == len(next_page["evaluations"]) == 1
                and page["evaluations"][0]["evaluation_id"]
                != next_page["evaluations"][0]["evaluation_id"],
            )
            reject(
                "cursor bound to filters/order",
                [
                    "watchlist-journal",
                    "list",
                    "--journal-db",
                    str(journal),
                    "--sequence-id",
                    records[0]["sequence_id"],
                    "--cursor",
                    page["next_cursor"],
                ],
                "invalid_cursor",
            )
            reject(
                "page maximum enforced",
                ["watchlist-journal", "list", "--journal-db", str(journal), "--limit", "1001"],
                "invalid_field",
            )
            reject(
                "deadline exhaustion never partial PASS",
                [
                    "watchlist-journal",
                    "verify",
                    "--journal-db",
                    str(journal),
                    "--timeout",
                    "0.000000001",
                ],
                "storage_timeout",
            )
            oversized = folder / "oversized.json"
            oversized.write_text(" " * (1048576 + 1), encoding="utf-8")
            reject("public parser byte limit", record_args(0, sample_path=oversized), "input_limit")
            check(
                "P5a origin byte nonmutation after read-only journal operations",
                sha(origin.read_bytes()) == origin_digest,
            )
            forbidden = (
                "qa-sensitive",
                entry["watch_id"],
                str(folder),
                "unit_price_minor",
                "target_price_minor",
                "canonical_identity",
                "SELECT ",
                "QA injected",
            )
            check(
                "structured completion logs redact evidence/paths/SQL",
                all(not any(secret in canonical(log) for secret in forbidden) for log in logs),
            )
            check(
                "all product processes attempted zero sockets",
                all(json.loads(path.read_text())["socket_attempts"] == [] for path in audits),
            )
            report.update(
                product_processes=counter,
                log_events=len(logs),
                socket_attempts=0,
                signal_oracle_count=len(expected_signals),
            )
        after = (git("rev-parse", "HEAD"), git("rev-parse", "HEAD^{tree}"))
        check("candidate head/tree after unchanged", before == after)
        check(
            "tracked worktree remains clean or provisional",
            args.provisional or not git("diff", "--name-only", "HEAD"),
        )
        report.update(
            observed_head=after[0],
            observed_tree=after[1],
            result="PROVISIONAL_PASS" if args.provisional else "PASS",
            check_count=len(checks),
        )
    except Exception as error:
        report.update(
            result="FAIL",
            check_count=len(checks),
            failure=type(error).__name__,
            detail=str(error),
            traceback=traceback.format_exc(),
        )
    print(canonical(report))
    return 0 if report["result"] in ("PASS", "PROVISIONAL_PASS") else 1


def inspect_schema(path: Path) -> bool:
    with closing(sqlite3.connect(path)) as db:
        return (
            db.execute("PRAGMA application_id").fetchone()[0] == 0x434D5451
            and db.execute("PRAGMA user_version").fetchone()[0] == 1
            and db.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()[0] == 23
            and sum(
                row[5]
                for row in db.execute("PRAGMA table_list")
                if row[1].startswith("wl_journal_")
            )
            == 4
        )


if __name__ == "__main__":
    raise SystemExit(main())
