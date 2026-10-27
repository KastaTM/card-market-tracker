"""Independent P8c QA probe; stdlib oracles, original APIs as SUT only.

Run: .venv/Scripts/python.exe scripts/p8c_qa_probe.py --timeout 5
Optional --fixtures points to the committed synthetic fixture directory.
No production policy, identity, evaluator or renderer computes expected values.
Outputs one sanitized JSON object; no phase acceptance or closure is implied.
"""

from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import importlib.abc
import io
import json
import math
import platform
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import unicodedata
from contextlib import redirect_stderr, redirect_stdout
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch


def canonical(value):
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    )


def sha(value):
    return hashlib.sha256(value.encode("utf-8") if isinstance(value, str) else value).hexdigest()


def identity(prefix, domain, body):
    return prefix + sha(domain.encode("ascii") + b"\x00" + canonical(body).encode("ascii"))


def ref_alert(alias, signal):
    return identity(
        "walt1_",
        "CMT_WATCHLIST_ALERT_V1",
        {"identity_version": 1, "destination_key": alias, "signal_id": signal},
    )


def ref_result(entry, sample, previous, as_of):
    # Independent reference deliberately bounded to this probe's fresh synthetic fixture.
    def digest_sample(value):
        return (
            None
            if value is None
            else {"sample_id": value["sample_id"], "digest": sha(canonical(value))}
        )

    assert entry["enabled"] is True
    clock = datetime.fromisoformat(as_of)
    for value in (sample, previous):
        if value is not None:
            assert (
                0
                <= (clock - datetime.fromisoformat(value["observed_at"])).total_seconds()
                <= entry["max_age_seconds"]
            )
    stock = sample["stock"]
    if stock == "OUT_OF_STOCK":
        price = ("NO_MATCH", "current_out_of_stock")
    elif sample["unit_price_minor"] is None or sample["shipping_minor"] is None:
        price = ("INDETERMINATE", "price_unknown")
    elif sample["unit_price_minor"] + sample["shipping_minor"] <= entry["target_price_minor"]:
        price = ("MATCH", "at_or_below_target")
    else:
        price = ("NO_MATCH", "above_target")
    if stock == "OUT_OF_STOCK":
        restock = ("NO_MATCH", "current_out_of_stock")
    elif previous is None:
        restock = ("INDETERMINATE", "previous_missing")
    elif previous["stock"] == "OUT_OF_STOCK":
        restock = ("MATCH", "restocked")
    else:
        restock = ("NO_MATCH", "already_available")
    rules = [
        {"rule": name, "result": status, "reason": reason}
        for name, (status, reason) in (("price", price), ("restock", restock))
    ]
    statuses = {row["result"] for row in rules}
    return {
        "version": 1,
        "policy_version": "watchlist-rules-v1",
        "watch_id": entry["watch_id"],
        "revision": entry["revision"],
        "cmt_id": entry["cmt_id"],
        "as_of": as_of,
        "current_sample": digest_sample(sample),
        "previous_sample": digest_sample(previous),
        "result": "MATCH"
        if "MATCH" in statuses
        else "INDETERMINATE"
        if "INDETERMINATE" in statuses
        else "NO_MATCH",
        "rules": rules,
    }


def ref_point(entry, sample, previous, ordinal, predecessor):
    sequence = identity(
        "wjs1_",
        "CMT_WATCHLIST_JOURNAL_SEQUENCE_V1",
        {
            "watch_id": entry["watch_id"],
            "revision": entry["revision"],
            "policy_version": "watchlist-rules-v1",
            "series_key": sample["series_key"],
        },
    )
    snapshot = {
        "version": 1,
        "sequence_id": sequence,
        "policy_version": "watchlist-rules-v1",
        "entry": entry,
        "current": sample,
        "previous": previous,
        "as_of": sample["observed_at"],
    }
    return {
        "evaluation_id": identity("wje1_", "CMT_WATCHLIST_JOURNAL_EVALUATION_V1", snapshot),
        "sequence_id": sequence,
        "ordinal": ordinal,
        "predecessor_evaluation_id": predecessor,
        "snapshot": snapshot,
        "evaluation_result": ref_result(entry, sample, previous, snapshot["as_of"]),
    }


def ref_signal(before, after, rule):
    body = {
        "version": 1,
        "kind": "WATCHLIST_RULE_ENTERED_MATCH",
        "mode": "synthetic",
        "sequence_id": after["sequence_id"],
        "rule": rule,
        "from_evaluation_id": before["evaluation_id"],
        "to_evaluation_id": after["evaluation_id"],
    }
    return {**body, "signal_id": identity("wsig1_", "CMT_WATCHLIST_SIGNAL_V1", body)}


def ref_intent(evidence):
    signal = evidence["signal"]
    entry = evidence["current"]["snapshot"]["entry"]
    return {
        "version": 1,
        "policy_version": "watchlist_synthetic_alert_v1",
        "renderer_version": 1,
        "channel": "offline_preview",
        "state": "pending",
        **{
            key: signal[key]
            for key in (
                "signal_id",
                "kind",
                "mode",
                "rule",
                "sequence_id",
                "from_evaluation_id",
                "to_evaluation_id",
            )
        },
        **{key: entry[key] for key in ("watch_id", "revision", "cmt_id")},
    }


def safe(value):
    return "".join(
        json.dumps(c, ensure_ascii=True)[1:-1]
        if not c.isprintable() or unicodedata.category(c).startswith("C")
        else "\\\\"
        if c == "\\"
        else c
        for c in str(value)
    )


def ref_message(intent, evidence):
    a, b = [evidence[key]["snapshot"] for key in ("predecessor", "current")]
    lines = [
        "SYNTHETIC — DEMONSTRATION ONLY",
        "Not a real offer or commercial notification.",
        "Historical Watchlist simulation; not current notification authorization.",
    ]
    fields = [
        (key, intent[ikey])
        for key, ikey in (
            ("cmt_id", "cmt_id"),
            ("watch_id", "watch_id"),
            ("historical_revision", "revision"),
            ("rule", "rule"),
            ("signal_id", "signal_id"),
            ("sequence_id", "sequence_id"),
            ("from_evaluation_id", "from_evaluation_id"),
            ("to_evaluation_id", "to_evaluation_id"),
        )
    ]
    for label, snap in (("predecessor", a), ("current", b)):
        fields.extend(
            [
                (label + "_current_observed_at", snap["current"]["observed_at"]),
                (
                    label + "_previous_observed_at",
                    "none" if snap["previous"] is None else snap["previous"]["observed_at"],
                ),
                (label + "_as_of", snap["as_of"]),
            ]
        )
    for label in ("predecessor", "current"):
        rule = next(
            x for x in evidence[label]["evaluation_result"]["rules"] if x["rule"] == intent["rule"]
        )
        fields.extend(
            [(label + "_rule_result", rule["result"]), (label + "_rule_reason", rule["reason"])]
        )
    lines.extend(key + ": " + safe(value) for key, value in fields)
    if intent["rule"] == "price":
        lines.extend(
            [
                "Synthetic price rule entered MATCH.",
                "currency: EUR",
                "target_price_minor: " + str(b["entry"]["target_price_minor"]),
            ]
        )
        for label, sample in (("predecessor", a["current"]), ("current", b["current"])):
            unit, ship = sample["unit_price_minor"], sample["shipping_minor"]
            for key, value in (
                ("unit_price_minor", unit),
                ("shipping_minor", ship),
                ("effective_cost_minor", None if unit is None or ship is None else unit + ship),
            ):
                lines.append(
                    label + "_" + key + ": " + ("unknown" if value is None else str(value))
                )
    else:
        lines.append("Synthetic restock rule entered MATCH; no real shop availability is asserted.")
        lines.extend(
            key + ": " + str(value)
            for key, value in (
                (
                    "predecessor_previous_stock",
                    "none" if a["previous"] is None else a["previous"]["stock"],
                ),
                ("predecessor_current_stock", a["current"]["stock"]),
                ("current_previous_stock", b["previous"]["stock"]),
                ("current_current_stock", b["current"]["stock"]),
            )
        )
    return "\n".join(lines)


def prepared(alias, evidence):
    intent = ref_intent(evidence)
    message = ref_message(intent, evidence)
    return {
        "version": 1,
        "alert_id": ref_alert(alias, evidence["signal"]["signal_id"]),
        "destination_key": alias,
        "signal_id": evidence["signal"]["signal_id"],
        "policy_version": "watchlist_synthetic_alert_v1",
        "renderer_version": 1,
        "channel": "offline_preview",
        "state": "pending",
        "intent_json": canonical(intent),
        "intent_sha256": sha(canonical(intent)),
        "evidence_json": canonical(evidence),
        "evidence_sha256": sha(canonical(evidence)),
        "message_text": message,
        "message_sha256": sha(message),
    }


def alter_database(path, statements):
    # Restore literal original triggers so failure must come from a semantic fold.
    with sqlite3.connect(path) as db:
        triggers = db.execute("SELECT name,sql FROM sqlite_master WHERE type='trigger'").fetchall()
        for name, _ in triggers:
            db.execute('DROP TRIGGER "' + name + '"')
        for statement, values in statements:
            db.execute(statement, values)
        for _, sql in triggers:
            db.execute(sql)


def worker(args):
    attempts = {"socket": 0, "telegram_import": 0}

    class DenyTelegram(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname.startswith("card_market_tracker.telegram_delivery"):
                attempts["telegram_import"] += 1
                raise AssertionError("forbidden_telegram_import")

    def deny_socket(*unused, **unused_keywords):
        attempts["socket"] += 1
        raise AssertionError("forbidden_socket")

    sys.meta_path.insert(0, DenyTelegram())
    socket.socket = deny_socket
    socket.create_connection = deny_socket
    socket.getaddrinfo = deny_socket
    if args.cli_case:
        from card_market_tracker.cli import main as fresh_main

        with tempfile.TemporaryDirectory(prefix="cmt-p8c-qa-cli-") as temporary:
            options = {
                "help": ["watchlist-alert-outbox", "--help"],
                "invalid": ["watchlist-alert-outbox", "get"],
                "init": [
                    "watchlist-alert-outbox",
                    "init",
                    "--outbox-db",
                    str(Path(temporary) / "outbox.sqlite"),
                    "--timeout",
                    str(args.timeout),
                ],
            }[args.cli_case]
            with redirect_stdout(io.StringIO()) as output, redirect_stderr(io.StringIO()):
                try:
                    code = fresh_main(options)
                except SystemExit as error:
                    code = error.code
            assert code == (2 if args.cli_case == "invalid" else 0), "fresh_cli_exit"
            assert attempts == {"socket": 0, "telegram_import": 0}, "fresh_cli_tripwires"
            if args.cli_case != "help":
                response = json.loads(output.getvalue())
                assert response["result"] == ("error" if args.cli_case == "invalid" else "ok"), (
                    "fresh_cli_response"
                )
        return {"status": "observations_pass", "case": args.cli_case, "tripwires": attempts}
    from card_market_tracker.cli import main as cli
    from card_market_tracker.watchlist import application as wa
    from card_market_tracker.watchlist import storage as ws
    from card_market_tracker.watchlist_alerts import application as app
    from card_market_tracker.watchlist_alerts import storage as store
    from card_market_tracker.watchlist_alerts.errors import OutboxError
    from card_market_tracker.watchlist_journal import application as ja
    from card_market_tracker.watchlist_journal import storage as js

    checks = []

    def ok(name, condition=True):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    def rejected(name, action, categories):
        try:
            action()
        except OutboxError as error:
            ok(name, error.category in categories)
        else:
            raise AssertionError(name)

    for alias, signal, expected in (
        (
            "local-preview",
            "wsig1_d9f9c7f0d4ca8767a6cdb9a917cc27a61c369cecea629c790ed42fd4421bf4f0",
            "walt1_6bd35f464dd126efb7f31ef6070ea7d3257799d294d5dd3dea21c3445ef0a1af",
        ),
        (
            "local-preview",
            "wsig1_4bd7f7a2ca57d7e8c9e340dc5f3c27aa5f3dbe433c7ef01a0ac897675e4e8bd4",
            "walt1_89548632c3d10ccb112ab72af5ca10e5819b7cd938ffbd120a3b19d5c4c87450",
        ),
        (
            "qa-preview",
            "wsig1_d9f9c7f0d4ca8767a6cdb9a917cc27a61c369cecea629c790ed42fd4421bf4f0",
            "walt1_338382e5b05bc41b635fe296acc7757a60756871790a6aacd29cec051bdfe1ae",
        ),
    ):
        ok("independent_frozen_vector_" + str(len(checks)), ref_alert(alias, signal) == expected)
    manifest = json.loads((args.fixtures / "synthetic_manifest.json").read_text(encoding="utf-8"))
    config = json.loads(
        (args.fixtures / "synthetic_watchlist_config.json").read_text(encoding="utf-8")
    )
    base = json.loads(
        (args.fixtures / "synthetic_watchlist_current.json").read_text(encoding="utf-8")
    )
    with tempfile.TemporaryDirectory(prefix="cmt-p8c-independent-qa-") as temporary:
        root = Path(temporary)
        watch, journal, outbox = [
            root / name for name in ("watch.sqlite", "journal.sqlite", "outbox.sqlite")
        ]
        ws.initialize(watch, timeout=args.timeout)
        entry = wa.add(
            watch,
            manifest,
            base["cmt_id"],
            config,
            request_token="independent-qa",
            timeout=args.timeout,
        )["entry"]
        js.initialize(journal, timeout=args.timeout)
        store.initialize(outbox, timeout=args.timeout)
        samples, points, signals = [], [], []

        def enqueue(signal, alias="local-preview", raw=manifest, w=watch, j=journal, target=outbox):
            return app.enqueue(target, w, j, raw, signal, alias, timeout=args.timeout)

        for index, stock in enumerate(
            ("OUT_OF_STOCK", "AVAILABLE", "AVAILABLE", "OUT_OF_STOCK", "AVAILABLE")
        ):
            sample = {
                **base,
                "sample_id": "independent-qa-" + str(index),
                "stock": stock,
                "observed_at": "2026-10-23T12:0" + str(index) + ":00Z",
            }
            # Explicitly cover valid null predecessor monetary fields and known free shipping.
            sample.update(
                unit_price_minor=None if stock == "OUT_OF_STOCK" else 900,
                shipping_minor=None if stock == "OUT_OF_STOCK" else 0,
            )
            samples.append(sample)
            normalized = copy.deepcopy(sample)
            normalized["observed_at"] = (
                datetime.fromisoformat(sample["observed_at"])
                .astimezone(UTC)
                .isoformat()
                .replace("+00:00", "Z")
            )
            previous = None if index == 0 else points[-1]["snapshot"]["current"]
            point = ref_point(
                entry,
                normalized,
                previous,
                index + 1,
                None if not points else points[-1]["evaluation_id"],
            )
            actual = ja.record(
                journal,
                watch,
                manifest,
                entry["watch_id"],
                sample,
                None if index == 0 else samples[index - 1],
                revision=1,
                as_of=sample["observed_at"],
                timeout=args.timeout,
            )
            ok(
                "checkpoint_identity_" + str(index),
                actual["evaluation_id"] == point["evaluation_id"],
            )
            expected_signals = (
                []
                if index not in (1, 4)
                else [ref_signal(points[-1], point, rule) for rule in ("price", "restock")]
            )
            ok(
                "checkpoint_signals_" + str(index),
                set(actual["signal_ids"]) == {s["signal_id"] for s in expected_signals},
            )
            points.append(point)
            signals.extend(expected_signals)
            if index == 1:
                early = enqueue(signals[0]["signal_id"])
                early_alert = store.get(outbox, early["alert_id"], timeout=args.timeout)
        ok("five_checkpoints_four_signals", len(points) == 5 and len(signals) == 4)
        frozen_watch = watch.read_bytes()
        frozen_journal = journal.read_bytes()
        all_ids = set()
        for number, signal in enumerate(signals):
            before, after = (points[0], points[1]) if number < 2 else (points[3], points[4])
            evidence = {"version": 1, "signal": signal, "predecessor": before, "current": after}
            for alias in ("local-preview", "qa-preview"):
                expected = prepared(alias, evidence)
                response = enqueue(signal["signal_id"], alias)
                aid = response["alert_id"]
                all_ids.add(aid)
                actual = store.get(outbox, aid, timeout=args.timeout)["alert"]
                ok("independent_id_" + str(number) + "_" + alias, aid == expected["alert_id"])
                ok(
                    "independent_content_" + str(number) + "_" + alias,
                    actual["intent"] == ref_intent(evidence)
                    and actual["intent_sha256"] == expected["intent_sha256"]
                    and actual["message_text"].encode("utf-8")
                    == expected["message_text"].encode("utf-8")
                    and actual["message_sha256"] == expected["message_sha256"],
                )
                saved = store.evidence_get(outbox, aid, timeout=args.timeout)
                ok(
                    "independent_evidence_" + str(number) + "_" + alias,
                    canonical(saved["evidence"]) == canonical(evidence)
                    and saved["evidence_sha256"] == expected["evidence_sha256"],
                )
        ok("alias_rule_episode_isolation", len(all_ids) == 8)
        selected, signal = early["alert_id"], signals[0]["signal_id"]
        ok(
            "ancient_bytes_before_revision",
            store.get(outbox, selected, timeout=args.timeout) == early_alert,
        )
        wa.update(
            watch,
            manifest,
            entry["watch_id"],
            {**config, "target_price_minor": 800},
            expected_revision=1,
            request_token="independent-qa-revision",
            timeout=args.timeout,
        )
        after_revision = watch.read_bytes()
        before_replay = outbox.read_bytes()
        ok(
            "ancient_replay_after_append_revision",
            enqueue(signal)["result"] == "replayed"
            and store.get(outbox, selected, timeout=args.timeout) == early_alert
            and before_replay == outbox.read_bytes(),
        )
        app.recompute(outbox, watch, journal, manifest, selected, timeout=args.timeout)
        ok("origin_recompute_historical_revision")
        for name, mutate, categories in (
            (
                "unrelated_duplicate_id",
                lambda m: m["entities"].append(copy.deepcopy(m["entities"][1])),
                {"duplicate_id"},
            ),
            (
                "unrelated_broken_relation",
                lambda m: m["entities"][4].update(set_id="11111111-1111-4111-8111-111111111111"),
                {"broken_relation"},
            ),
            (
                "selected_identity_change",
                lambda m: m["entities"][5].update(variant="holo"),
                {"identity_conflict", "duplicate_identity"},
            ),
            (
                "unrelated_binding_invalid",
                lambda m: m["bindings"][-1].update(cmt_id="11111111-1111-4111-8111-111111111111"),
                {"broken_relation", "missing_binding"},
            ),
            ("strict_manifest_version", lambda m: m.update(version=True), {"unsupported_version"}),
        ):
            invalid = copy.deepcopy(manifest)
            mutate(invalid)
            rejected(
                "replay_rejects_" + name,
                lambda invalid=invalid: enqueue(signal, raw=invalid),
                categories,
            )
        other = root / "other-watch.sqlite"
        ws.initialize(other, timeout=args.timeout)
        wa.add(
            other,
            manifest,
            base["cmt_id"],
            {**config, "target_price_minor": 800},
            request_token="other",
            timeout=args.timeout,
        )
        rejected(
            "different_exact_original_revision",
            lambda: enqueue(signal, w=other),
            {"identity_conflict"},
        )
        rejected("fabricated_baseline_signal", lambda: enqueue("wsig1_" + "0" * 64), {"not_found"})
        rejected("same_source_paths", lambda: enqueue(signal, w=journal), {"unsafe_destination"})
        for bad in ("Upper", "x/y", "a\n", "a" * 65, True):
            rejected(
                "invalid_alias_" + str(len(checks)),
                lambda bad=bad: enqueue(signal, alias=bad),
                {"invalid_field"},
            )
        # Full manifest must be detached before the source callback can mutate it.
        mutable = copy.deepcopy(manifest)
        original_bundle = js._verified_signal_bundle

        def mutate_caller(*positional, **keywords):
            mutable.clear()
            return original_bundle(*positional, **keywords)

        with patch.object(js, "_verified_signal_bundle", mutate_caller):
            ok("detached_manifest_callback", enqueue(signal, raw=mutable)["result"] == "replayed")
        # Instrument actual admission: one full source fold, one held read connection.
        fold_calls, connection_calls, budget_ids = [], [], []
        original_verify, original_connect = js._verify, js._connect

        def track_verify(db, budget):
            fold_calls.append(db)
            budget_ids.append(id(budget))
            return original_verify(db, budget)

        def track_connect(path, budget, **keywords):
            connection_calls.append(path)
            return original_connect(path, budget, **keywords)

        with patch.object(js, "_verify", track_verify), patch.object(js, "_connect", track_connect):
            enqueue(signal)
        ok(
            "single_held_journal_fold",
            len(fold_calls) == len(connection_calls) == len(set(budget_ids)) == 1,
        )
        evidence = {
            "version": 1,
            "signal": signals[0],
            "predecessor": points[0],
            "current": points[1],
        }
        content = prepared("local-preview", evidence)
        budget = app.Budget(args.timeout)
        receipt = app._issue(content, budget)
        for name, value, used_budget in (
            ("plain_dictionary", content, budget),
            ("counterfeit_receipt", app._Receipt(canonical(content)), budget),
            ("copied_receipt", copy.copy(receipt), budget),
            ("different_budget", receipt, app.Budget(args.timeout)),
        ):
            rejected(
                "authority_" + name,
                lambda value=value, used_budget=used_budget: store._enqueue_verified(
                    outbox, value, used_budget
                ),
                {"unsupported_evidence"},
            )
        altered = app._issue(content, budget)
        object.__setattr__(altered, "content_json", altered.content_json + " ")
        rejected(
            "authority_mutation",
            lambda: store._enqueue_verified(outbox, altered, budget),
            {"unsupported_evidence"},
        )
        ok(
            "authority_genuine_once",
            store._enqueue_verified(outbox, receipt, budget)["result"] == "replayed",
        )
        rejected(
            "authority_single_use",
            lambda: store._enqueue_verified(outbox, receipt, budget),
            {"unsupported_evidence"},
        )
        expired = app.Budget(args.timeout)
        exp_receipt = app._issue(content, expired)
        expired.deadline = time.monotonic() - 1
        rejected(
            "authority_issued_deadline",
            lambda: store._enqueue_verified(outbox, exp_receipt, expired),
            {"storage_timeout"},
        )
        page = store.list_alerts(
            outbox, destination_key="local-preview", limit=1, timeout=args.timeout
        )
        cursor = json.loads(base64.urlsafe_b64decode(page["next_cursor"]))
        ok(
            "independent_cursor_bytes",
            base64.urlsafe_b64encode(canonical(cursor).encode("ascii")).decode("ascii")
            == page["next_cursor"]
            and cursor
            == {
                "version": 1,
                "filters": {"destination_key": "local-preview"},
                "last_alert_id": page["items"][0]["alert_id"],
            },
        )
        rejected(
            "cursor_filter_binding",
            lambda: store.list_alerts(
                outbox,
                destination_key="qa-preview",
                cursor=page["next_cursor"],
                timeout=args.timeout,
            ),
            {"invalid_cursor"},
        )
        # Coherently rehash invalid local results and restore all schema triggers.
        corrupted = root / "corrupt.sqlite"
        corrupted.write_bytes(outbox.read_bytes())
        bad = copy.deepcopy(evidence)
        bad["current"]["evaluation_result"]["rules"][0]["reason"] = "above_target"
        raw = canonical(bad)
        alter_database(
            corrupted,
            [
                (
                    "UPDATE watchlist_alert_evidence SET evidence_json=?,evidence_sha256=? "
                    "WHERE alert_id=?",
                    (raw, sha(raw), selected),
                )
            ],
        )
        rejected(
            "rehashed_invalid_result_local_fold",
            lambda: store.verify(corrupted, timeout=args.timeout),
            {"storage_corrupt"},
        )
        # Locally coherent omitted ancestry cannot prove the original historical ordinal.
        coherent = root / "coherent.sqlite"
        coherent.write_bytes(outbox.read_bytes())
        alternate = copy.deepcopy(evidence)
        alternate["predecessor"].update(ordinal=3, predecessor_evaluation_id="wje1_" + "f" * 64)
        alternate["current"]["ordinal"] = 4
        raw = canonical(alternate)
        alter_database(
            coherent,
            [
                (
                    "UPDATE watchlist_alert_evidence SET evidence_json=?,evidence_sha256=? "
                    "WHERE alert_id=?",
                    (raw, sha(raw), selected),
                )
            ],
        )
        ok(
            "local_coherent_ancestry_is_not_origin_proof",
            store.verify(coherent, timeout=args.timeout)["counts"] == {"alerts": 8, "evidence": 8},
        )
        rejected(
            "coherent_local_origin_mismatch",
            lambda: app.recompute(
                coherent, watch, journal, manifest, selected, timeout=args.timeout
            ),
            {"recompute_mismatch"},
        )
        backup, restored = root / "backup.sqlite", root / "restored.sqlite"
        recovery_connections = []
        original_outbox_verify = store._verify

        def observe_recovery(db, budget):
            ok(
                "recovery_no_early_publication_" + str(len(recovery_connections)),
                not backup.exists(),
            )
            recovery_connections.append(db)
            return original_outbox_verify(db, budget)

        with patch.object(store, "_verify", observe_recovery):
            store.backup(outbox, backup, timeout=args.timeout)
        ok(
            "three_fresh_recovery_fold_connections",
            len(recovery_connections) == 3 and len({id(db) for db in recovery_connections}) == 3,
        )
        store.restore(backup, restored, timeout=args.timeout)
        ok(
            "exclusive_recovery_contents",
            store.get(restored, selected, timeout=args.timeout) == early_alert,
        )
        rejected(
            "recovery_no_overwrite",
            lambda: store.backup(outbox, restored, timeout=args.timeout),
            {"unsafe_destination"},
        )
        ok(
            "quiescent_source_bytes",
            watch.read_bytes() == after_revision
            and journal.read_bytes() == frozen_journal
            and outbox.read_bytes() == before_replay
            and frozen_watch != after_revision,
        )
        absent_watch, absent_journal = root / "absent-watch.sqlite", root / "absent-journal.sqlite"
        watch.rename(root / "held-watch.sqlite")
        journal.rename(root / "held-journal.sqlite")
        ok(
            "local_preview_without_originals",
            store.preview(outbox, selected, timeout=args.timeout)["message_text"]
            == early_alert["alert"]["message_text"]
            and store.verify(outbox, timeout=args.timeout)["counts"]
            == {"alerts": 8, "evidence": 8},
        )
        rejected(
            "missing_originals_replay_rejected",
            lambda: enqueue(signal, w=absent_watch, j=absent_journal),
            {"storage_missing"},
        )
        rejected(
            "missing_originals_recompute_rejected",
            lambda: app.recompute(
                outbox, absent_watch, absent_journal, manifest, selected, timeout=args.timeout
            ),
            {"storage_missing"},
        )
        # Distinct actual revision/series/product histories must retain isolated IDs.
        iso_watch, iso_journal, iso_outbox = [
            root / name
            for name in (
                "isolation-watch.sqlite",
                "isolation-journal.sqlite",
                "isolation-outbox.sqlite",
            )
        ]
        ws.initialize(iso_watch, timeout=args.timeout)
        js.initialize(iso_journal, timeout=args.timeout)
        store.initialize(iso_outbox, timeout=args.timeout)
        original_entry = wa.add(
            iso_watch,
            manifest,
            base["cmt_id"],
            config,
            request_token="isolation-original",
            timeout=args.timeout,
        )["entry"]
        revised_entry = wa.update(
            iso_watch,
            manifest,
            original_entry["watch_id"],
            {**config, "target_price_minor": 950},
            expected_revision=1,
            request_token="isolation-revision",
            timeout=args.timeout,
        )["entry"]
        other_entry = wa.add(
            iso_watch,
            manifest,
            "b980e1f7-9bae-432e-b02a-182dbcca478d",
            config,
            request_token="isolation-product",
            timeout=args.timeout,
        )["entry"]
        isolated_ids = set()
        for case, selected_entry, series in (
            ("base", original_entry, "isolation-series"),
            ("revision", revised_entry, "isolation-series"),
            ("series", original_entry, "other-series"),
            ("product", other_entry, "isolation-series"),
        ):
            pair = []
            for index, stock in enumerate(("OUT_OF_STOCK", "AVAILABLE")):
                sample = {
                    **base,
                    "cmt_id": selected_entry["cmt_id"],
                    "series_key": series,
                    "sample_id": "isolation-" + case + str(index),
                    "observed_at": "2026-10-23T13:0" + str(index) + ":00Z",
                    "stock": stock,
                    "shipping_minor": 0,
                }
                prior = None if not pair else pair[0]["snapshot"]["current"]
                point = ref_point(
                    selected_entry,
                    sample,
                    prior,
                    index + 1,
                    None if not pair else pair[0]["evaluation_id"],
                )
                actual = ja.record(
                    iso_journal,
                    iso_watch,
                    manifest,
                    selected_entry["watch_id"],
                    sample,
                    prior,
                    revision=selected_entry["revision"],
                    as_of=sample["observed_at"],
                    timeout=args.timeout,
                )
                ok(
                    "isolation_evaluation_" + case + str(index),
                    actual["evaluation_id"] == point["evaluation_id"],
                )
                pair.append(point)
            for rule in ("price", "restock"):
                expected_signal = ref_signal(pair[0], pair[1], rule)
                actual = app.enqueue(
                    iso_outbox,
                    iso_watch,
                    iso_journal,
                    manifest,
                    expected_signal["signal_id"],
                    "local-preview",
                    timeout=args.timeout,
                )
                ok(
                    "isolation_alert_" + case + "_" + rule,
                    actual["alert_id"] == ref_alert("local-preview", expected_signal["signal_id"]),
                )
                isolated_ids.add(actual["alert_id"])
        ok("revision_series_product_isolation", len(isolated_ids) == 8)
        for arguments, code in (
            (["watchlist-alert-outbox", "--help"], 0),
            (["watchlist-alert-outbox", "get"], 2),
            (
                [
                    "watchlist-alert-outbox",
                    "verify",
                    "--outbox-db",
                    str(outbox),
                    "--timeout",
                    str(args.timeout),
                ],
                0,
            ),
        ):
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                try:
                    result = cli(arguments)
                except SystemExit as error:
                    result = error.code
            ok("cli_import_socket_tripwire_" + str(len(checks)), result == code)
        ok("zero_sockets_telegram_imports", attempts == {"socket": 0, "telegram_import": 0})
    return {
        "status": "preliminary_observations_pass",
        "check_count": len(checks),
        "checks": checks,
        "tripwires": attempts,
        "independent_reference_scope": (
            "fresh synthetic fixtures; exact hashes, identities, full results and renderer bytes"
        ),
        "limits": [
            "no Docker or CI execution",
            "no physical Pi qualification",
            "final candidate attestation required",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixtures", type=Path, default=Path(__file__).resolve().parents[1] / "tests" / "fixtures"
    )
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--cli-case", choices=("help", "invalid", "init"), help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or not 0 < args.timeout <= 5:
        print(canonical({"status": "fail", "check": "timeout_must_be_positive_max5"}))
        return 2
    try:
        if args.worker:
            payload = worker(args)
        else:
            repo = Path(__file__).resolve().parents[1]

            def git(*arguments):
                return subprocess.run(
                    ["git", *arguments],
                    cwd=repo,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=True,
                ).stdout.strip()

            started = datetime.now(UTC).isoformat()

            def working_bytes():
                inventory = {}
                for relative in git("ls-files", "-z").split("\0"):
                    path = repo / relative
                    if relative and path.is_file():
                        inventory[relative] = sha(path.read_bytes())
                return sha(canonical(inventory))

            before = {
                "head": git("rev-parse", "HEAD"),
                "tree": git("rev-parse", "HEAD^{tree}"),
                "status_sha256": sha(git("status", "--porcelain=v1")),
                "clean": not bool(git("status", "--porcelain=v1")),
                "working_bytes_sha256": working_bytes(),
            }
            child = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(Path(__file__).resolve()),
                    "--worker",
                    "--fixtures",
                    str(args.fixtures.resolve()),
                    "--timeout",
                    str(args.timeout),
                ],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if child.returncode:
                payload = {
                    "status": "fail",
                    "worker_exit": child.returncode,
                    "worker": json.loads(child.stdout) if child.stdout.strip() else None,
                    "stderr_present": bool(child.stderr),
                }
            else:
                payload = json.loads(child.stdout)
                payload["fresh_cli_processes"] = []
                for case in ("help", "invalid", "init"):
                    fresh = subprocess.run(
                        [
                            sys.executable,
                            "-B",
                            str(Path(__file__).resolve()),
                            "--worker",
                            "--cli-case",
                            case,
                            "--timeout",
                            str(args.timeout),
                        ],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    observed = (
                        json.loads(fresh.stdout)
                        if fresh.stdout.strip()
                        else {"status": "fail", "check": "fresh_cli_no_json"}
                    )
                    payload["fresh_cli_processes"].append(observed)
                    if fresh.returncode:
                        payload["status"] = "fail"
            payload.update(
                {
                    "started_utc": started,
                    "completed_utc": datetime.now(UTC).isoformat(),
                    "candidate": before,
                    "head_stable": before["head"] == git("rev-parse", "HEAD"),
                    "working_bytes_stable": before["working_bytes_sha256"] == working_bytes(),
                    "script_sha256": sha(Path(__file__).read_bytes()),
                    "python": platform.python_version(),
                    "platform": platform.platform(),
                    "sut_location": (
                        "managed interpreter import; no expected-value production helpers"
                    ),
                    "final_qa_acceptance": False,
                }
            )
    except Exception as error:
        payload = {
            "status": "fail",
            "error_type": type(error).__name__,
            "check": str(error) if isinstance(error, AssertionError) else "probe_execution_error",
        }
    print(canonical(payload))
    return 1 if payload["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
