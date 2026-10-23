"""Independent reviewer probes; run with uv run --frozen python and explicit Git IDs.

Only runtime public APIs are imported. Hashes, predicate reasons and sequence fold
are calculated here, without journal identity/transition/verifier helpers. Private
SQLite copies are deliberately corrupted with original triggers restored. Product
verification must reject them. JSON stdout is evidence, never phase acceptance.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import traceback
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = "541b9d13-9669-4973-8413-397bea14c045"
POLICY = "watchlist-rules-v1"


def canonical(value):
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    )


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def identity(kind, value):
    domain, prefix = {
        "sequence": ("CMT_WATCHLIST_JOURNAL_SEQUENCE_V1", "wjs1_"),
        "evaluation": ("CMT_WATCHLIST_JOURNAL_EVALUATION_V1", "wje1_"),
        "signal": ("CMT_WATCHLIST_SIGNAL_V1", "wsig1_"),
    }[kind]
    return prefix + hashlib.sha256(domain.encode() + b"\0" + canonical(value).encode()).hexdigest()


def clock(value):
    return datetime.fromisoformat(value)


def predicate(snapshot):
    """Independent P5a result oracle from documented rules, including full reasons."""
    entry, current, previous = (snapshot[key] for key in ("entry", "current", "previous"))
    now = clock(snapshot["as_of"])

    def fresh(sample):
        return sample is not None and (
            0 <= (now - clock(sample["observed_at"])).total_seconds() <= entry["max_age_seconds"]
        )

    result = {
        "version": 1,
        "policy_version": POLICY,
        "watch_id": entry["watch_id"],
        "revision": entry["revision"],
        "cmt_id": entry["cmt_id"],
        "as_of": snapshot["as_of"],
        "current_sample": {"sample_id": current["sample_id"], "digest": digest(current)},
        "previous_sample": None
        if previous is None
        else {"sample_id": previous["sample_id"], "digest": digest(previous)},
    }
    if not entry["enabled"]:
        return {**result, "result": "SKIPPED", "rules": [], "reason": "disabled"}
    rules = []
    for rule, configured in (
        ("price", entry["target_price_minor"] is not None),
        ("restock", entry["restock_enabled"]),
    ):
        if not configured:
            continue
        if not fresh(current):
            status, reason = "INDETERMINATE", "current_stale"
        elif current["stock"] == "OUT_OF_STOCK":
            status, reason = "NO_MATCH", "current_out_of_stock"
        elif current["stock"] == "UNKNOWN":
            status, reason = "INDETERMINATE", "current_stock_unknown"
        elif rule == "price":
            if current["unit_price_minor"] is None or current["shipping_minor"] is None:
                status, reason = "INDETERMINATE", "price_unknown"
            elif (
                current["unit_price_minor"] + current["shipping_minor"]
                <= entry["target_price_minor"]
            ):
                status, reason = "MATCH", "at_or_below_target"
            else:
                status, reason = "NO_MATCH", "above_target"
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
        rules.append({"rule": rule, "result": status, "reason": reason})
    statuses = {row["result"] for row in rules}
    aggregate = next(
        (status for status in ("MATCH", "INDETERMINATE") if status in statuses), "NO_MATCH"
    )
    return {**result, "result": aggregate, "rules": rules}


def fold(snapshots):
    expected = []
    for prior, current in zip(snapshots, snapshots[1:], strict=False):
        old_rules = {row["rule"]: row["result"] for row in predicate(prior)["rules"]}
        maximum = current["entry"]["max_age_seconds"]
        ages = [
            (clock(current["as_of"]) - clock(item["current"]["observed_at"])).total_seconds()
            for item in (prior, current)
        ]
        if not all(0 <= age <= maximum for age in ages):
            continue
        for row in predicate(current)["rules"]:
            if old_rules.get(row["rule"]) == "NO_MATCH" and row["result"] == "MATCH":
                body = {
                    "version": 1,
                    "kind": "WATCHLIST_RULE_ENTERED_MATCH",
                    "mode": "synthetic",
                    "sequence_id": current["sequence_id"],
                    "rule": row["rule"],
                    "from_evaluation_id": identity("evaluation", prior),
                    "to_evaluation_id": identity("evaluation", current),
                }
                expected.append({**body, "signal_id": identity("signal", body)})
    return sorted(expected, key=lambda row: row["signal_id"])


def block_network():
    def blocked(*args, **kwargs):
        raise AssertionError("reviewer detected product socket attempt")

    socket.socket = blocked
    socket.create_connection = blocked
    socket.getaddrinfo = blocked


def imports():
    from card_market_tracker.watchlist import application as origin_app
    from card_market_tracker.watchlist import storage as origin_store
    from card_market_tracker.watchlist_journal import application as journal_app
    from card_market_tracker.watchlist_journal import storage as journal_store
    from card_market_tracker.watchlist_journal.errors import JournalError

    return origin_app, origin_store, journal_app, journal_store, JournalError


def worker(payload_path):
    block_network()
    _, _, app, _, error_type = imports()
    payload = json.loads(Path(payload_path).read_text(encoding="utf-8"))
    try:
        response = app.record(
            Path(payload["journal"]),
            Path(payload["origin"]),
            payload["manifest"],
            payload["watch_id"],
            payload["current"],
            payload["previous"],
            revision=1,
            as_of=payload["current"]["observed_at"],
            timeout=5,
        )
        print(json.dumps({"result": response["result"]}))
    except error_type as error:
        print(json.dumps({"error": error.category}))
    return 0


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def source_fingerprint():
    files = list((ROOT / "src").rglob("*.py")) + [Path(__file__)]
    return digest(
        {
            str(path.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in sorted(files)
        }
    )


def exercise(folder, checks):
    origin_app, origin_store, app, store, error_type = imports()
    manifest = json.loads((ROOT / "tests/fixtures/synthetic_manifest.json").read_text())
    origin, journal = folder / "origin.sqlite", folder / "journal.sqlite"
    origin_store.initialize(origin, timeout=5)
    entry = origin_app.add(
        origin,
        manifest,
        TARGET,
        {
            "target_price_minor": 1000,
            "restock_enabled": True,
            "max_age_seconds": 3600,
            "priority": "high",
        },
        request_token="reviewer-origin",
        timeout=5,
    )["entry"]
    store.initialize(journal, timeout=5)
    original_bytes = origin.read_bytes()

    def check(name, action):
        try:
            detail = action()
            checks.append({"name": name, "result": "PASS", "detail": detail})
        except Exception as error:
            checks.append(
                {
                    "name": name,
                    "result": "FAIL",
                    "exception": type(error).__name__,
                    "detail": str(error),
                    "traceback": traceback.format_exc(),
                }
            )

    def reject(action, categories=None):
        try:
            action()
        except error_type as error:
            assert categories is None or error.category in categories, error.category
            return error.category
        raise AssertionError("invalid operation was accepted")

    start = datetime(2026, 10, 23, 11, tzinfo=UTC)

    def sample(index, stock="AVAILABLE", series="reviewer-series", **changes):
        return {
            "version": 1,
            "provenance": "synthetic",
            "sample_id": f"reviewer-{index}",
            "cmt_id": TARGET,
            "series_key": series,
            "observed_at": (start + timedelta(minutes=index)).isoformat().replace("+00:00", "Z"),
            "currency": "EUR",
            "unit_price_minor": 900,
            "shipping_minor": 100,
            "stock": stock,
            **changes,
        }

    def record(current, previous=None, **changes):
        return app.record(
            journal,
            origin,
            changes.pop("manifest", manifest),
            entry["watch_id"],
            current,
            previous,
            revision=changes.pop("revision", 1),
            as_of=changes.pop("as_of", current["observed_at"]),
            timeout=5,
            **changes,
        )

    saved, snapshots = [], []

    def main_sequence():
        samples = [
            sample(i, stock)
            for i, stock in enumerate(
                (
                    "OUT_OF_STOCK",
                    "AVAILABLE",
                    "AVAILABLE",
                    "OUT_OF_STOCK",
                    "AVAILABLE",
                    "UNKNOWN",
                    "AVAILABLE",
                    "OUT_OF_STOCK",
                    "AVAILABLE",
                )
            )
        ]
        for index, current in enumerate(samples):
            previous = samples[index - 1] if index else None
            response = record(current, previous)
            sid = identity(
                "sequence",
                {
                    "watch_id": entry["watch_id"],
                    "revision": 1,
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
                "as_of": current["observed_at"],
            }
            assert response["sequence_id"] == sid
            assert response["evaluation_id"] == identity("evaluation", snapshot)
            loaded = store.get(journal, response["evaluation_id"], timeout=5)["evaluation"]
            assert loaded["snapshot"] == snapshot
            assert loaded["evaluation_result"] == predicate(snapshot)
            snapshots.append(snapshot)
            saved.append(response)
        expected = fold(snapshots)
        assert len(expected) == 6
        assert saved[0]["signals_count"] == 0
        assert saved[6]["signals_count"] == 0
        actual = store.signal_list(journal, sequence_id=saved[0]["sequence_id"], timeout=5)[
            "signals"
        ]
        assert actual == expected, (actual, expected)
        return {
            "evaluations": len(saved),
            "signals": len(expected),
            "oracle": "own full predicate reasons and domain-separated SHA/fold",
        }

    check("independent_identity_predicate_and_per_rule_fold", main_sequence)
    if not saved:
        return

    def golden_vectors():
        vectors = json.loads((ROOT / "tests/fixtures/p5b_identity_vectors_v1.json").read_text())[
            "vectors"
        ]
        for vector in vectors.values():
            preimage = vector["domain"] + "\0" + canonical(vector["object"])
            assert vector["preimage_text"] == preimage
            prefix = vector["id"].split("_", 1)[0] + "_"
            assert prefix + hashlib.sha256(preimage.encode()).hexdigest() == vector["id"]
        return {"literal_preimages_independently_hashed": len(vectors)}

    check("supplied_literal_golden_preimages", golden_vectors)

    def public_fixture_digest_exception():
        syntax = ast.parse((ROOT / "scripts/check_secret_scan.py").read_text())
        registered = next(
            ast.literal_eval(node.value)
            for node in syntax.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "_P5B_IDENTITY"
                for target in node.targets
            )
        )
        vectors = json.loads((ROOT / "tests/fixtures/p5b_identity_vectors_v1.json").read_text())[
            "vectors"
        ]
        entries = [row["object"]["entry"] for row in vectors.values() if "entry" in row["object"]]
        assert entries
        for selected in entries:
            assert registered == selected["identity_digest"]
            assert registered == digest(selected["canonical_identity"])
        return {
            "registry": "_P5B_IDENTITY",
            "canonical_projection_sha256": registered,
            "reason": "public synthetic equality digest independently recomputed",
        }

    check("secret_scan_exact_public_projection_digest", public_fixture_digest_exception)

    def freshness_and_or():
        scenarios = {
            "inclusive": (
                [sample(0, "OUT_OF_STOCK", "inclusive"), sample(60, series="inclusive")],
                2,
            ),
            "expired": ([sample(0, "OUT_OF_STOCK", "expired"), sample(61, series="expired")], 0),
            "or": (
                [
                    sample(0, "OUT_OF_STOCK", "or"),
                    sample(1, series="or", unit_price_minor=1500),
                    sample(2, series="or"),
                ],
                2,
            ),
            "first-match": ([sample(1, series="first-match")], 0),
        }
        details = {}
        for name, (samples, count) in scenarios.items():
            local = []
            for index, current in enumerate(samples):
                previous = samples[index - 1] if index else None
                if name == "first-match":
                    previous = sample(0, "OUT_OF_STOCK", "first-match")
                response = record(current, previous)
                loaded = store.get(journal, response["evaluation_id"], timeout=5)["evaluation"]
                assert loaded["evaluation_result"] == predicate(loaded["snapshot"])
                local.append(loaded["snapshot"])
            actual = store.signal_list(journal, sequence_id=response["sequence_id"], timeout=5)[
                "signals"
            ]
            assert actual == fold(local)
            assert len(actual) == count, (name, actual)
            if name == "or":
                assert predicate(local[1])["result"] == predicate(local[2])["result"] == "MATCH"
                assert {row["rule"] for row in actual} == {"price", "restock"}
            details[name] = count
        return details

    check("inclusive_freshness_expiry_first_match_and_or_nonmasking", freshness_and_or)

    def replay():
        before = journal.read_bytes()
        actual = record(snapshots[0]["current"])
        assert {key: value for key, value in actual.items() if key != "result"} == {
            key: value for key, value in saved[0].items() if key != "result"
        }
        assert actual["result"] == "replayed"
        assert journal.read_bytes() == before
        return "ancient replay preserves bytes, original persisted_at, links, signal IDs and head"

    check("ancient_replay", replay)

    def conflicts():
        before = journal.read_bytes()
        errors = []
        errors.append(reject(lambda: record(snapshots[0]["current"], as_of="2026-10-23T11:00:01Z")))
        errors.append(reject(lambda: record(sample(9), snapshots[0]["current"])))
        errors.append(
            reject(lambda: record(sample(10, provenance="real"), snapshots[-1]["current"]))
        )
        malformed = copy.deepcopy(manifest)
        malformed["entities"][-1]["unrelated_invalid"] = True
        errors.append(reject(lambda: record(snapshots[0]["current"], manifest=malformed)))
        errors.append(reject(lambda: record(sample(10, result="MATCH"), snapshots[-1]["current"])))
        assert journal.read_bytes() == before
        return errors

    check("conflicts_and_full_manifest_admission_are_nonmutating", conflicts)

    def origin_boundary():
        before = journal.read_bytes()
        assert (
            app.recompute(journal, origin, manifest, saved[1]["evaluation_id"], timeout=5)["result"]
            == "ok"
        )
        result = reject(
            lambda: app.recompute(
                journal, folder / "absent.sqlite", manifest, saved[1]["evaluation_id"], timeout=5
            ),
            {"storage_missing"},
        )
        alternate = folder / "alternate.sqlite"
        origin_store.initialize(alternate, timeout=5)
        origin_app.add(
            alternate,
            manifest,
            TARGET,
            {"target_price_minor": 2000},
            request_token="different",
            timeout=5,
        )
        reject(
            lambda: app.recompute(
                journal, alternate, manifest, saved[1]["evaluation_id"], timeout=5
            ),
            {"identity_conflict"},
        )
        assert store.verify(journal, timeout=5)["result"] == "ok"
        assert journal.read_bytes() == before
        return {
            "missing_origin": result,
            "local_verify": "ok",
            "recompute": "original immutable revision only",
        }

    check("local_consistency_vs_original_source_read_only", origin_boundary)

    def pagination():
        all_ids, cursor = [], None
        while True:
            page = store.list_evaluations(
                journal, sequence_id=saved[0]["sequence_id"], limit=2, cursor=cursor, timeout=5
            )
            all_ids.extend(item["evaluation_id"] for item in page["evaluations"])
            cursor = page["next_cursor"]
            if cursor is None:
                break
            reject(
                lambda current_cursor=cursor: store.list_evaluations(
                    journal, watch_id=entry["watch_id"], cursor=current_cursor, timeout=5
                ),
                {"invalid_cursor"},
            )
        assert all_ids == sorted(row["evaluation_id"] for row in saved)
        assert len(set(all_ids)) == len(saved)
        return {"items": len(all_ids), "cursor_filter_change": "rejected"}

    check("pagination_and_cursor_binding", pagination)

    def copy_for_attack(name):
        target = folder / f"attack-{name}.sqlite"
        shutil.copyfile(journal, target)
        return target

    def tamper(name, mutation, schema_attack=False):
        target = copy_for_attack(name)
        with closing(sqlite3.connect(target)) as db:
            triggers = list(db.execute("SELECT name,sql FROM sqlite_master WHERE type='trigger'"))
            for trigger, _ in triggers:
                db.execute(f'DROP TRIGGER "{trigger}"')
            mutation(db)
            if not schema_attack:
                for _, sql in triggers:
                    db.execute(sql)
            db.commit()
        return reject(
            lambda: store.verify(target, timeout=5), {"storage_corrupt", "storage_schema"}
        )

    def result_attack(db):
        row = db.execute(
            "SELECT evaluation_id,result_json FROM wl_journal_evaluations LIMIT 1"
        ).fetchone()
        result = json.loads(row[1])
        result["result"] = "MATCH" if result["result"] != "MATCH" else "NO_MATCH"
        db.execute(
            "UPDATE wl_journal_evaluations SET result_json=? WHERE evaluation_id=?",
            (canonical(result), row[0]),
        )

    check("forged_result_with_valid_input_identity", lambda: tamper("result", result_attack))
    check(
        "missing_signal_with_exact_schema_restored",
        lambda: tamper(
            "missing-signal",
            lambda db: db.execute(
                "DELETE FROM wl_journal_signals WHERE signal_id="
                "(SELECT signal_id FROM wl_journal_signals LIMIT 1)"
            ),
        ),
    )

    def signal_attack(db):
        row = db.execute("SELECT signal_id,body_json FROM wl_journal_signals LIMIT 1").fetchone()
        body = json.loads(row[1])
        body["from_evaluation_id"] = saved[2]["evaluation_id"]
        db.execute(
            "UPDATE wl_journal_signals SET signal_id=?,from_eval_id=?,body_json=? "
            "WHERE signal_id=?",
            (identity("signal", body), body["from_evaluation_id"], canonical(body), row[0]),
        )

    check("coherently_rehashed_signal_wrong_transition", lambda: tamper("signal", signal_attack))

    def snapshot_rehash_attack(db):
        old_id = saved[-1]["evaluation_id"]
        snapshot = copy.deepcopy(snapshots[-1])
        snapshot["current"]["unit_price_minor"] = 1500
        new_id = identity("evaluation", snapshot)
        db.execute(
            "UPDATE wl_journal_evaluations SET evaluation_id=?,snapshot_json=? "
            "WHERE evaluation_id=?",
            (new_id, canonical(snapshot), old_id),
        )
        db.execute(
            "UPDATE wl_journal_sequences SET head_eval_id=? WHERE head_eval_id=?",
            (new_id, old_id),
        )
        for old_signal_id, raw in list(
            db.execute(
                "SELECT signal_id,body_json FROM wl_journal_signals WHERE to_eval_id=?", (old_id,)
            )
        ):
            body = json.loads(raw)
            body["to_evaluation_id"] = new_id
            db.execute(
                "UPDATE wl_journal_signals SET signal_id=?,to_eval_id=?,body_json=? "
                "WHERE signal_id=?",
                (identity("signal", body), new_id, canonical(body), old_signal_id),
            )
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []

    check(
        "rehashed_snapshot_evaluation_head_signals_cannot_authorize_forged_result",
        lambda: tamper("input-rehash", snapshot_rehash_attack),
    )
    check(
        "head_rewind_with_exact_schema_restored",
        lambda: tamper(
            "head",
            lambda db: db.execute(
                "UPDATE wl_journal_sequences SET head_eval_id=?,head_observed_at=?,"
                "head_as_of=?,head_ordinal=1",
                (
                    saved[0]["evaluation_id"],
                    snapshots[0]["current"]["observed_at"],
                    snapshots[0]["as_of"],
                ),
            ),
        ),
    )
    check(
        "schema_missing_immutable_triggers",
        lambda: tamper("schema", lambda db: None, schema_attack=True),
    )
    check(
        "schema_unrecognized_object",
        lambda: tamper(
            "extra-index",
            lambda db: db.execute("CREATE INDEX reviewer_extra ON wl_journal_evaluations(as_of)"),
        ),
    )

    def exact_schema():
        # Parse frozen literal DDL ourselves, without schema.expected_inventory().
        syntax = ast.parse(
            (ROOT / "src/card_market_tracker/watchlist_journal/schema.py").read_text()
        )
        statements = next(
            ast.literal_eval(node.value)
            for node in syntax.body
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "STATEMENTS"
                for target in node.targets
            )
        )
        query = "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
        with (
            closing(sqlite3.connect(":memory:")) as oracle,
            closing(sqlite3.connect(journal)) as actual,
        ):
            for statement in statements:
                oracle.execute(statement)
            expected = list(oracle.execute(query))
            assert list(actual.execute(query)) == expected
            assert len(expected) == 23
            assert actual.execute("PRAGMA application_id").fetchone()[0] == 0x434D5451
            assert actual.execute("PRAGMA user_version").fetchone()[0] == 1
            assert len(actual.execute("PRAGMA table_list").fetchall()) == 6
        return {
            "inventory_count": len(expected),
            "inventory_sha256": digest(expected),
            "authority": "versioned literal DDL parsed independently",
        }

    check("exact_normalized_schema_inventory", exact_schema)

    def recovery():
        backup, restored = folder / "backup.sqlite", folder / "restored.sqlite"
        source = journal.read_bytes()
        assert store.backup(journal, backup, timeout=5)["result"] == "ok"
        assert store.restore(backup, restored, timeout=5)["result"] == "ok"
        assert (
            store.verify(restored, timeout=5)["counts"]
            == store.verify(journal, timeout=5)["counts"]
        )
        restored_bytes = restored.read_bytes()
        reject(lambda: store.restore(backup, restored, timeout=5), {"unsafe_destination"})
        collision = folder / "collision.sqlite"
        sidecar = Path(str(collision) + "-journal")
        sidecar.write_bytes(b"reviewer sidecar evidence")
        reject(lambda: store.restore(backup, collision, timeout=5), {"unsafe_destination"})
        assert sidecar.read_bytes() == b"reviewer sidecar evidence"
        assert not collision.exists()
        assert restored.read_bytes() == restored_bytes
        assert journal.read_bytes() == source
        return "verified backup/restore, existing destination and unrelated sidecar preserved"

    check("exclusive_recovery_and_sidecar_preservation", recovery)

    def process_races():
        race_origin = {
            "journal": str(journal),
            "origin": str(origin),
            "manifest": manifest,
            "watch_id": entry["watch_id"],
        }

        def run_pair(samples, previous):
            paths = []
            for index, current in enumerate(samples):
                path = folder / f"worker-{index}.json"
                path.write_text(
                    json.dumps({**race_origin, "current": current, "previous": previous}),
                    encoding="utf-8",
                )
                paths.append(path)

            def execute(path):
                result = subprocess.run(
                    [sys.executable, str(Path(__file__)), "--worker", str(path)],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                assert result.returncode == 0, result.stderr
                return json.loads(result.stdout)

            with ThreadPoolExecutor(max_workers=2) as pool:
                return list(pool.map(execute, paths))

        current = sample(0, "OUT_OF_STOCK", series="reviewer-race")
        same = run_pair([current, current], None)
        assert sorted(item.get("result", "") for item in same) == ["recorded", "replayed"], same
        competing = run_pair(
            [sample(1, series="reviewer-race"), sample(2, series="reviewer-race")], current
        )
        assert sum(item.get("result") == "recorded" for item in competing) == 1, competing
        assert sum("error" in item for item in competing) == 1, competing
        store.verify(journal, timeout=5)
        return {"identical": same, "incompatible_successors": competing}

    check("two_process_identical_replay_and_competing_head_cas", process_races)
    check(
        "origin_nonmutation_and_zero_product_sockets",
        lambda: original_bytes == origin.read_bytes()
        or (_ for _ in ()).throw(AssertionError("origin changed")),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-head")
    parser.add_argument("--expected-tree")
    parser.add_argument("--worker", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        return worker(args.worker)
    if not args.expected_head or not args.expected_tree:
        parser.error("--expected-head and --expected-tree are required")
    checks = []
    before = {
        "head": git("rev-parse", "HEAD"),
        "tree": git("rev-parse", "HEAD^{tree}"),
        "status": git("status", "--porcelain"),
        "source_sha256": source_fingerprint(),
    }
    evidence = {
        "version": 1,
        "role": "independent REVIEWER; neither product author nor QA",
        "model_profile": {
            "requested": "GPT-6.1 Sol / High",
            "selection_observed": (
                "requested profile supplied in reviewer assignment; effective backend not exposed"
            ),
            "backend_verified": False,
        },
        "expected": {"head": args.expected_head, "tree": args.expected_tree},
        "before": before,
        "checks": checks,
    }
    try:
        assert before["head"] == args.expected_head, "unexpected HEAD"
        assert before["tree"] == args.expected_tree, "unexpected tree"
        block_network()
        with tempfile.TemporaryDirectory(prefix="cmt-p5b-reviewer-") as outside:
            exercise(Path(outside), checks)
    except Exception as error:
        checks.append(
            {
                "name": "probe_setup_or_binding",
                "result": "FAIL",
                "detail": str(error),
                "traceback": traceback.format_exc(),
            }
        )
    after = {
        "head": git("rev-parse", "HEAD"),
        "tree": git("rev-parse", "HEAD^{tree}"),
        "status": git("status", "--porcelain"),
        "source_sha256": source_fingerprint(),
    }
    evidence["after"] = after
    stable = before == after
    checks.append(
        {
            "name": "head_tree_worktree_and_runtime_source_unchanged",
            "result": "PASS" if stable else "FAIL",
        }
    )
    failed = any(item["result"] != "PASS" for item in checks)
    evidence["result"] = (
        "FAIL" if failed else "PROVISIONAL_WORKTREE_PASS" if before["status"] else "PASS"
    )
    evidence["limits"] = [
        "PASS covers these reviewer probes only; not CI, all acceptance criteria or phase closure",
        "dirty worktree results never attest the commit tree",
        "zero sockets enforced for imports, runtime calls and race child processes",
        "schema oracle consumes frozen literal authority but independently normalizes inventory",
        "does not certify native ARM64 hardware or electrical power-loss durability",
    ]
    print(json.dumps(evidence, indent=2, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
