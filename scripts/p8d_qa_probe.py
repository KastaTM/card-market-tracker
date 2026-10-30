"""Independent P8d NONAUTHOR QA: genuine originals and independent byte oracles.

Run with PYTHONPATH=src and Python -B scripts/p8d_qa_probe.py --mode all.
No author tests/probe helpers are imported. Oracle mode imports no product.
Every database is a new isolated temporary fixture. No live transport is used.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import importlib.abc
import json
import os
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import patch

PRODUCT = "b980e1f7-9bae-432e-b02a-182dbcca478d"
ACK = "SYNTHETIC_HISTORICAL_DEMONSTRATION"
ALIAS = "independent-qa"
BOT, CHAT = 372114009, 681422703
LOCAL = 5.0
DELIVERY_KEYS = {
    "delivery_id",
    "alert_id",
    "signal_id",
    "state",
    "attempt_count",
    "current_attempt_id",
    "not_before",
    "first_prepared_at",
    "updated_at",
    "message_sha256",
    "evidence_sha256",
    "route_sha256",
    "consent_sha256",
    "binding_sha256",
    "send_quarantined",
    "last_error_category",
}


def canonical(value: object) -> str:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def commitment(domain: str, value: object) -> str:
    return sha(domain.encode("ascii") + bytes([0]) + canonical(value).encode("ascii"))


def require(value: object, explanation: str) -> None:
    if not value:
        raise AssertionError(explanation)


def rejected(action: Callable[[], object], categories: str | set[str]) -> str:
    allowed = {categories} if isinstance(categories, str) else categories
    try:
        action()
    except Exception as exc:
        category = getattr(exc, "category", None)
        require(category in allowed, "unexpected error category: " + str(category))
        return str(category)
    raise AssertionError("expected rejection: " + ",".join(sorted(allowed)))


class NoTelegram(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname: str, path: object = None, target: object = None) -> None:
        if fullname.startswith("card_market_tracker.telegram_delivery"):
            raise AssertionError("offline path imported Telegram")


def no_network(*args: object, **kwargs: object) -> None:
    raise AssertionError("QA product network tripwire")


def deny_socket_audit(event: str, arguments: tuple[object, ...]) -> None:
    del arguments
    if event.startswith("socket."):
        raise AssertionError("QA socket creation/network audit tripwire")


def token_guard() -> Any:
    original = type(os.environ).__getitem__

    def guarded(environment: Any, key: str) -> str:
        if key.upper() == "CMT_TELEGRAM_BOT_TOKEN":
            raise AssertionError("QA token access tripwire")
        return str(original(environment, key))

    return patch.object(type(os.environ), "__getitem__", guarded)


def oracle_vectors() -> None:
    # Explicit ASCII literal preimages; no production canonical/identity helper.
    prefix = b"CMT_WATCHLIST_TELEGRAM_DELIVERY_V1\x00"
    left = b'{"identity_version":1,"provider":"telegram","signal_id":"wsig1_'
    suffix = b'"}'
    vectors = (
        (b"0", "b08e2920077a2f36ba634b32c0f1215e952063c55cfc99320ab55fbbdf9d36f5"),
        (b"f", "810e8528fcea94a8ee848b56cb50ae04ff35bbaef05de8f667bddda896cac9d8"),
    )
    for digit, digest in vectors:
        preimage = prefix + left + digit * 64 + suffix
        require(
            len(preimage) == 164 and preimage.count(bytes([0])) == 1,
            "literal preimage length and NUL",
        )
        require(sha(preimage) == digest, "literal vector digest")
        require(
            preimage
            == prefix
            + canonical(
                {
                    "identity_version": 1,
                    "provider": "telegram",
                    "signal_id": "wsig1_" + digit.decode() * 64,
                }
            ).encode("ascii"),
            "independent canonical bytes",
        )


@dataclass
class Originals:
    watch: Path
    journal: Path
    outbox: Path
    manifest: dict[str, Any]
    entry: dict[str, Any]
    alerts: list[str]
    signals: list[str]

    def paths(self) -> tuple[Path, Path, Path]:
        return self.watch, self.journal, self.outbox

    def fingerprints(self) -> tuple[str, ...]:
        return tuple(sha(path.read_bytes()) for path in self.paths())


def originals(directory: Path, manifest: dict[str, Any], *, priority: str = "normal") -> Originals:
    """Five independent public-API checkpoints produce two price entry signals."""
    wa = importlib.import_module("card_market_tracker.watchlist.application")
    ws = importlib.import_module("card_market_tracker.watchlist.storage")
    ja = importlib.import_module("card_market_tracker.watchlist_journal.application")
    js = importlib.import_module("card_market_tracker.watchlist_journal.storage")
    aa = importlib.import_module("card_market_tracker.watchlist_alerts.application")
    az = importlib.import_module("card_market_tracker.watchlist_alerts.storage")
    directory.mkdir()
    watch, journal, outbox = (directory / name for name in ("w.sqlite", "j.sqlite", "o.sqlite"))
    ws.initialize(watch, timeout=LOCAL)
    config = {
        "target_price_minor": 1300,
        "restock_enabled": False,
        "priority": priority,
        "max_age_seconds": 3600,
        "enabled": True,
    }
    entry = wa.add(
        watch, manifest, PRODUCT, config, request_token="independent-p8d", timeout=LOCAL
    )["entry"]
    js.initialize(journal, timeout=LOCAL)
    previous = None
    signals: list[str] = []
    records = []
    for index, price in enumerate((1725, 875, 875, 1725, 875)):
        stamp = f"2026-06-17T09:{index:02d}:00Z"
        sample = {
            "version": 1,
            "provenance": "synthetic",
            "sample_id": f"qa-p8d-{index}",
            "cmt_id": PRODUCT,
            "series_key": "qa-p8d-price",
            "observed_at": stamp,
            "currency": "EUR",
            "unit_price_minor": price,
            "shipping_minor": 0,
            "stock": "AVAILABLE",
        }
        result = ja.record(
            journal,
            watch,
            manifest,
            entry["watch_id"],
            sample,
            previous,
            revision=1,
            as_of=stamp,
            timeout=LOCAL,
        )
        records.append((sample, previous, stamp, result))
        signals.extend(result["signal_ids"])
        previous = sample
    require(len(signals) == 2, "two distinct genuine price episodes")
    # Ancient source replay after the second episode must preserve local counts.
    before = js.verify(journal, timeout=LOCAL)
    sample, previous, stamp, saved = records[0]
    replay = ja.record(
        journal,
        watch,
        manifest,
        entry["watch_id"],
        sample,
        previous,
        revision=1,
        as_of=stamp,
        timeout=LOCAL,
    )
    require(replay["persisted_at"] == saved["persisted_at"], "ancient original replay")
    require(js.verify(journal, timeout=LOCAL) == before, "ancient replay nonmutation")
    az.initialize(outbox, timeout=LOCAL)
    alerts = [
        str(aa.enqueue(outbox, watch, journal, manifest, signal, ALIAS, timeout=LOCAL)["alert_id"])
        for signal in signals
    ]
    require(
        az.verify(outbox, timeout=LOCAL)["counts"] == {"alerts": 2, "evidence": 2},
        "independently valid complete original outbox",
    )
    for alert in alerts:
        aa.recompute(outbox, watch, journal, manifest, alert, timeout=LOCAL)
    return Originals(watch, journal, outbox, manifest, entry, alerts, signals)


def independent_review(src: Originals, index: int = 0, alias: str = ALIAS) -> dict[str, Any]:
    """Rebuild frozen commitments directly from original public P8c records."""
    az = importlib.import_module("card_market_tracker.watchlist_alerts.storage")
    alert = az.get(src.outbox, src.alerts[index], timeout=LOCAL)["alert"]
    evidence = az.evidence_get(src.outbox, src.alerts[index], timeout=LOCAL)["evidence"]
    semantic = {key: value for key, value in alert.items() if key != "first_prepared_at"}
    route = {
        "route_version": 1,
        "provider": "telegram",
        "destination_key": alias,
        "bot_id": BOT,
        "chat_id": CHAT,
        "chat_type": "private",
        "operator_attested": True,
    }
    route_hash = commitment("CMT_WATCHLIST_TELEGRAM_ROUTE_V1", route)
    entry_hash = sha(canonical(src.entry).encode("ascii"))
    evidence_hash = sha(canonical(evidence).encode("ascii"))
    intent_hash = sha(canonical(alert["intent"]).encode("ascii"))
    message_hash = sha(alert["message_text"].encode("utf-8"))
    source_hash = sha(canonical(semantic).encode("ascii"))
    consent = {
        "consent_version": 1,
        "acknowledgement": ACK,
        "alert_id": src.alerts[index],
        "signal_id": src.signals[index],
        "watch_id": src.entry["watch_id"],
        "revision": 1,
        "message_sha256": message_hash,
        "evidence_sha256": evidence_hash,
        "entry_sha256": entry_hash,
        "intent_sha256": intent_hash,
        "source_alert_sha256": source_hash,
        "route_sha256": route_hash,
    }
    identifier = "wtdl1_" + commitment(
        "CMT_WATCHLIST_TELEGRAM_DELIVERY_V1",
        {"identity_version": 1, "provider": "telegram", "signal_id": src.signals[index]},
    )
    binding = {
        "binding_version": 1,
        "provider": "telegram",
        "delivery_id": identifier,
        "alert_id": src.alerts[index],
        "destination_key": alias,
        "signal_id": src.signals[index],
        "watch_id": src.entry["watch_id"],
        "revision": 1,
        "cmt_id": PRODUCT,
        "policy_version": "watchlist_synthetic_alert_v1",
        "renderer_version": 1,
        "message_sha256": message_hash,
        "evidence_sha256": evidence_hash,
        "entry_sha256": entry_hash,
        "intent_sha256": intent_hash,
        "source_alert_sha256": source_hash,
        "route_sha256": route_hash,
        "consent_sha256": commitment("CMT_WATCHLIST_TELEGRAM_CONSENT_V1", consent),
    }
    return {
        **binding,
        "binding_sha256": commitment("CMT_WATCHLIST_TELEGRAM_BINDING_V1", binding),
        "acknowledgement": ACK,
        "historical_demonstration": True,
    }


def new_ledger(app: Any, path: Path) -> None:
    app.initialize(path, timeout=LOCAL)
    app.destination_add(path, ALIAS, BOT, CHAT, operator_private_owned=True, timeout=LOCAL)


def prepare(
    app: Any,
    ledger: Path,
    src: Originals,
    index: int = 0,
    *,
    alias: str = ALIAS,
    **overrides: object,
) -> dict[str, Any]:
    reviewed = independent_review(src, index, alias)
    consent = {
        "acknowledgement": ACK,
        "expected_signal_id": reviewed["signal_id"],
        "expected_revision": 1,
        "expected_message_sha256": reviewed["message_sha256"],
        "expected_evidence_sha256": reviewed["evidence_sha256"],
        "expected_route_sha256": reviewed["route_sha256"],
        "expected_binding_sha256": reviewed["binding_sha256"],
    }
    consent.update(overrides)
    return app.prepare(
        ledger, *src.paths(), src.manifest, src.alerts[index], alias, timeout=LOCAL, **consent
    )


def check_delivery(envelope: dict[str, Any]) -> None:
    item = envelope["delivery"]
    require(set(item) == DELIVERY_KEYS, "closed redacted delivery DTO")
    raw = canonical(envelope)
    require(str(BOT) not in raw and str(CHAT) not in raw, "route privacy")
    for forbidden in ("message_text", "entry_json", "owner", "accepted_at", "receipt"):
        require('"' + forbidden + '"' not in raw, "private field leaked: " + forbidden)


def public_cases(
    app: Any,
    root: Path,
    src: Originals,
    equivalent: Originals,
    incompatible: Originals,
    report: Callable[[str, Callable[[], None]], None],
) -> None:
    def consent_and_oracle() -> None:
        ledger = root / "consent.sqlite"
        new_ledger(app, ledger)
        fingerprints = src.fingerprints()
        reviewed = app.review(
            ledger, *src.paths(), src.manifest, src.alerts[0], ALIAS, timeout=LOCAL
        )
        require(reviewed["review"] == independent_review(src), "complete independent review oracle")
        baseline = ledger.read_bytes()
        for override in (
            {"acknowledgement": "yes"},
            {"expected_revision": True},
            {"expected_message_sha256": "0" * 64},
            {"expected_evidence_sha256": "1" * 64},
            {"expected_route_sha256": "2" * 64},
            {"expected_binding_sha256": "3" * 64},
        ):
            rejected(
                lambda override=override: prepare(app, ledger, src, **override), "consent_mismatch"
            )
            require(ledger.read_bytes() == baseline, "bad consent changed ledger bytes")
        inserted = prepare(app, ledger, src)
        check_delivery(inserted)
        require(inserted["result"] == "inserted", "first preparation")
        replay = prepare(app, ledger, src)
        require(
            replay["result"] == "replay" and replay["delivery"] == inserted["delivery"],
            "identical prepare replay retained original DTO",
        )
        require(src.fingerprints() == fingerprints, "public admission source nonmutation")

    def equivalent_case() -> None:
        ledger = root / "equivalent.sqlite"
        new_ledger(app, ledger)
        first = prepare(app, ledger, src)
        second = prepare(app, ledger, equivalent)
        require(
            second["result"] == "replay" and second["delivery"] == first["delivery"],
            "equivalent independent copies allowed",
        )
        app.recompute(
            ledger,
            *equivalent.paths(),
            equivalent.manifest,
            first["delivery"]["delivery_id"],
            timeout=LOCAL,
        )

    def rw01_case() -> None:
        ledger = root / "rw01.sqlite"
        new_ledger(app, ledger)
        require(
            src.entry["watch_id"] == incompatible.entry["watch_id"]
            and src.entry["revision"] == incompatible.entry["revision"]
            and canonical(src.entry) != canonical(incompatible.entry),
            "genuine incompatible same key",
        )
        first = prepare(app, ledger, src)
        # The incoming bundle independently verifies/recomputes before the conflict.
        app.review(
            ledger,
            *incompatible.paths(),
            incompatible.manifest,
            incompatible.alerts[0],
            ALIAS,
            timeout=LOCAL,
        )
        baseline = ledger.read_bytes()
        rejected(lambda: prepare(app, ledger, incompatible), "identity_conflict")
        require(ledger.read_bytes() == baseline, "RW01 rollback did not preserve bytes")
        require(
            app.get(ledger, first["delivery"]["delivery_id"], timeout=LOCAL)["delivery"]
            == first["delivery"],
            "RW01 retained delivery immutable",
        )
        counts = app.verify(ledger, timeout=LOCAL)["counts"]
        require(
            counts
            == {"destinations": 1, "watch_entries": 1, "deliveries": 1, "claims": 0, "results": 0},
            "RW01 full healthy retained counts",
        )
        target = root / "rw01-backup.sqlite"
        require(
            app.backup(ledger, target, timeout=LOCAL)["counts"] == counts,
            "RW01 healthy three-fold backup",
        )
        require(app.verify(target, timeout=LOCAL)["counts"] == counts, "RW01 backup reopened")

    def missing_original_case() -> None:
        ledger = root / "missing.sqlite"
        new_ledger(app, ledger)
        first = prepare(app, ledger, src)
        require(app.verify(ledger, timeout=LOCAL)["result"] == "ok", "healthy local verify")
        rejected(
            lambda: app.recompute(
                ledger,
                root / "absent.sqlite",
                src.journal,
                src.outbox,
                src.manifest,
                first["delivery"]["delivery_id"],
                timeout=LOCAL,
            ),
            "storage_missing",
        )
        rejected(
            lambda: app.recompute(
                ledger,
                incompatible.watch,
                src.journal,
                src.outbox,
                src.manifest,
                first["delivery"]["delivery_id"],
                timeout=LOCAL,
            ),
            "identity_conflict",
        )
        mutated = json.loads(canonical(src.manifest))
        mutated["entities"][0]["unexpected-field"] = "independent unrelated poison"
        baseline = ledger.read_bytes()
        rejected(
            lambda: app.review(ledger, *src.paths(), mutated, src.alerts[0], ALIAS, timeout=LOCAL),
            {"invalid_field", "invalid_shape"},
        )
        require(ledger.read_bytes() == baseline, "invalid complete manifest writes")

    def pagination_case() -> None:
        ledger = root / "paging.sqlite"
        new_ledger(app, ledger)
        for index in (0, 1):
            check_delivery(prepare(app, ledger, src, index))
        page = app.list_deliveries(ledger, limit=1, timeout=LOCAL)
        require(len(page["items"]) == 1 and page["next_cursor"], "bounded first page")
        next_page = app.list_deliveries(
            ledger, limit=1000, cursor=page["next_cursor"], timeout=LOCAL
        )
        require(
            len(next_page["items"]) == 1 and next_page["next_cursor"] is None,
            "bounded terminal page",
        )
        require(
            page["items"][0]["delivery_id"] < next_page["items"][0]["delivery_id"],
            "ascending keyset",
        )
        rejected(
            lambda: app.list_deliveries(
                ledger, state="ready", cursor=page["next_cursor"], timeout=LOCAL
            ),
            "invalid_cursor",
        )
        for limit in (True, 0, 1001):
            rejected(
                lambda limit=limit: app.list_deliveries(ledger, limit=limit, timeout=LOCAL),
                "invalid_field",
            )
        for timeout in (True, 0, float("nan"), float("inf"), 5.0001):
            rejected(lambda timeout=timeout: app.verify(ledger, timeout=timeout), "invalid_field")

    def stable_pair_and_detached_manifest() -> None:
        source_store = importlib.import_module("card_market_tracker.watchlist_alerts.storage")
        ledger = root / "snapshot-stability.sqlite"
        new_ledger(app, ledger)
        baseline = ledger.read_bytes()
        fingerprints = src.fingerprints()
        real_pair = source_store._get_pair
        reads = []

        def changed_operational_pair(*args: Any, **kwargs: Any) -> Any:
            pair = real_pair(*args, **kwargs)
            reads.append(pair)
            if len(reads) >= 3:
                pair = copy.deepcopy(pair)
                pair[0]["first_prepared_at"] = "2001-01-01T00:00:00Z"
            return pair

        with patch.object(source_store, "_get_pair", changed_operational_pair):
            rejected(lambda: prepare(app, ledger, src), "recompute_mismatch")
        require(
            len(reads) == 3 and ledger.read_bytes() == baseline,
            "full twelve-field before/recompute/after snapshot stability before writer",
        )
        real_verify = source_store.verify
        manifest = json.loads(canonical(src.manifest))
        poisoned = Originals(
            src.watch, src.journal, src.outbox, manifest, src.entry, src.alerts, src.signals
        )

        def mutate_caller(*args: Any, **kwargs: Any) -> Any:
            manifest["entities"][0]["unexpected-field"] = "after-detachment"
            return real_verify(*args, **kwargs)

        with patch.object(source_store, "verify", mutate_caller):
            inserted = prepare(app, ledger, poisoned)
        require(
            inserted["result"] == "inserted", "complete caller manifest detached before callbacks"
        )
        require(
            src.fingerprints() == fingerprints, "snapshot/manifest callback probes write no source"
        )

    report("public_consent_identity_privacy_source_nonmutation", consent_and_oracle)
    report(
        "complete_pair_operational_stability_and_manifest_detachment_before_callbacks",
        stable_pair_and_detached_manifest,
    )
    report("equivalent_independent_originals_replay_recompute", equivalent_case)
    report("rw01_genuine_incompatible_originals_rollback_verify_backup", rw01_case)
    report("missing_original_vs_local_verify_complete_manifest_poison", missing_original_case)
    report("bounded_keyset_cursor_filter_strict_limits", pagination_case)


def authority_cases(
    app: Any, root: Path, src: Originals, report: Callable[[str, Callable[[], None]], None]
) -> None:
    store = importlib.import_module("card_market_tracker.watchlist_delivery.storage")
    budget_module = importlib.import_module("card_market_tracker.watchlist_delivery.budget")

    def authority_attack() -> None:
        ledger = root / "authority.sqlite"
        other = root / "authority-other.sqlite"
        new_ledger(app, ledger)
        new_ledger(app, other)

        def capture() -> tuple[Any, Any]:
            captured = []

            def intercept(path: Path, receipt: object, budget: object) -> dict[str, object]:
                captured.append((receipt, budget))
                return {"captured": True}

            with patch.object(store, "_prepare_verified", intercept):
                prepare(app, ledger, src)
            require(len(captured) == 1, "one fresh public-admitted private receipt")
            return captured[0]

        def deny_write(*args: object, **kwargs: object) -> None:
            raise AssertionError("rejected authority reached writable open")

        receipt, budget = capture()
        with patch.object(store, "_connect", deny_write):
            for forged in (
                {"verified": True},
                app._Receipt(receipt.content_json),
                copy.copy(receipt),
                copy.deepcopy(receipt),
            ):
                rejected(
                    lambda forged=forged: store._prepare_verified(ledger, forged, budget),
                    "unsupported_evidence",
                )
            rejected(
                lambda: store._prepare_verified(ledger, receipt, budget_module.Budget(LOCAL)),
                "unsupported_evidence",
            )
            rejected(
                lambda: store._prepare_verified(other, receipt, budget), "unsupported_evidence"
            )
            rejected(
                lambda: app._consume_receipt(receipt, budget, "claim", ledger),
                "unsupported_evidence",
            )
        altered, altered_budget = capture()
        object.__setattr__(altered, "content_json", altered.content_json + " ")
        with patch.object(store, "_connect", deny_write):
            rejected(
                lambda: store._prepare_verified(ledger, altered, altered_budget),
                "unsupported_evidence",
            )
        expired, expired_budget = capture()
        with patch.object(
            budget_module.time, "monotonic", lambda: expired_budget.global_deadline + 1
        ):
            rejected(
                lambda: store._prepare_verified(ledger, expired, expired_budget), "storage_timeout"
            )
        missing, missing_budget = capture()
        saved = src.watch.with_suffix(".moved")
        src.watch.rename(saved)
        try:
            with patch.object(store, "_connect", deny_write):
                rejected(
                    lambda: store._prepare_verified(ledger, missing, missing_budget),
                    "unsupported_evidence",
                )
        finally:
            saved.rename(src.watch)
        # A genuine authority is consumed by a wrong-ledger writer attempt;
        # normal admission must issue a fresh receipt before the real writer.
        receipt, budget = capture()
        require(
            store._prepare_verified(ledger, receipt, budget)["result"] == "inserted",
            "genuine one-use receipt commits",
        )
        with patch.object(store, "_connect", deny_write):
            rejected(
                lambda: store._prepare_verified(ledger, receipt, budget), "unsupported_evidence"
            )
        app.verify(ledger, timeout=LOCAL)
        failed, failed_budget = capture()
        from card_market_tracker.watchlist_delivery.errors import DeliveryError

        with patch.object(store, "_connect", side_effect=DeliveryError("storage_locked")):
            rejected(
                lambda: store._prepare_verified(ledger, failed, failed_budget), "storage_locked"
            )
        with patch.object(store, "_connect", deny_write):
            rejected(
                lambda: store._prepare_verified(ledger, failed, failed_budget),
                "unsupported_evidence",
            )

    def quarantine_unknown() -> None:
        ledger = root / "quarantine-origin.sqlite"
        new_ledger(app, ledger)
        backup = root / "old-empty.sqlite"
        app.backup(ledger, backup, timeout=LOCAL)
        selected = prepare(app, ledger, src)["delivery"]["delivery_id"]
        restored = root / "old-restored.sqlite"
        result = app.restore(backup, restored, timeout=LOCAL)
        require(result["send_quarantined"] is True, "durably restored global quarantine")
        rejected(lambda: app.send(restored, selected), "send_quarantined")
        prepared = prepare(app, restored, src)
        require(
            prepared["delivery"]["send_quarantined"] is True,
            "new preparation retains restored quarantine",
        )
        rejected(
            lambda: app.send(
                restored,
                selected,
                watchlist_db=src.watch,
                journal_db=src.journal,
                outbox_db=src.outbox,
                manifest=src.manifest,
            ),
            "send_quarantined",
        )
        require(
            app.verify(restored, timeout=LOCAL)["send_quarantined"] is True,
            "global quarantine survives unknown/new records",
        )

    report(
        "original_issued_receipt_forge_copy_mutation_budget_operation_expiry_reuse",
        authority_attack,
    )
    report("old_empty_restore_global_quarantine_unknown_and_new_deliveries", quarantine_unknown)


class FakePort:
    def __init__(self, ledger: Path, outcome: object, source_text: str) -> None:
        self.ledger, self.outcome, self.source_text = ledger, outcome, source_text
        self.sends = 0
        self.bot_checks = 0
        self.allowances: list[float] = []
        self.on_send: Callable[[], None] | None = None

    def check_configuration(self) -> None:
        pass

    def validate_destination(self, bot_id: int, chat_id: int, *, timeout: float) -> None:
        require(
            (bot_id, chat_id) == (BOT, CHAT) and 0 < timeout < 30, "fake private route preflight"
        )
        self.allowances.append(timeout)

    def validate_bot(self, bot_id: int, *, timeout: float) -> None:
        require(bot_id == BOT and 0 < timeout < 30, "fake exact bot preflight")
        self.bot_checks += 1
        self.allowances.append(timeout)

    def send(self, bot_id: int, chat_id: int, message_text: str, *, timeout: float) -> object:
        require(
            (bot_id, chat_id, message_text) == (BOT, CHAT, self.source_text), "exact source message"
        )
        require(0 < timeout < 30, "remaining reserved network allowance")
        self.sends += 1
        with closing(sqlite3.connect(self.ledger, timeout=1)) as db:
            require(
                db.execute("SELECT state,attempt_count FROM wtd_state").fetchone()
                == ("in_flight", self.sends),
                "durable separate-connection claim before fake HTTP",
            )
            # A separate writer can acquire the lock during fake HTTP.
            db.execute("BEGIN IMMEDIATE")
            db.rollback()
        if self.on_send is not None:
            self.on_send()
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return self.outcome


def remote_cases(
    app: Any, root: Path, src: Originals, report: Callable[[str, Callable[[], None]], None]
) -> None:
    native = importlib.import_module("card_market_tracker.telegram_delivery.transport")
    store = importlib.import_module("card_market_tracker.watchlist_delivery.storage")
    az = importlib.import_module("card_market_tracker.watchlist_alerts.storage")
    text = az.get(src.outbox, src.alerts[0], timeout=LOCAL)["alert"]["message_text"]

    def setup(label: str, outcome: object) -> tuple[Path, str, FakePort]:
        ledger = root / (label + ".sqlite")
        new_ledger(app, ledger)
        did = prepare(app, ledger, src)["delivery"]["delivery_id"]
        fake = FakePort(ledger, outcome, text)
        with patch.object(app, "_transport_factory", lambda: fake):
            app.destination_validate(ledger, ALIAS)
        return ledger, did, fake

    def invoke(ledger: Path, did: str, fake: FakePort) -> dict[str, Any]:
        with patch.object(app, "_transport_factory", lambda: fake):
            return app.send(
                ledger,
                did,
                watchlist_db=src.watch,
                journal_db=src.journal,
                outbox_db=src.outbox,
                manifest=src.manifest,
            )

    def confirmed() -> None:
        outcome = native.TransportResult(
            "confirmed", receipt=native.Receipt(99071, 1800012345, BOT, CHAT)
        )
        ledger, did, fake = setup("fake-confirmed", outcome)
        result = invoke(ledger, did, fake)
        check_delivery(result)
        require(
            result["result"] == "ok" and result["delivery"]["state"] == "confirmed",
            "provider acceptance plus durable receipt confirmed",
        )
        require(fake.sends == 1 and fake.bot_checks == 1, "one fake HTTP and one bot preflight")
        app.verify(ledger, timeout=LOCAL)
        # Revalidation must not invalidate the retained historical claim snapshot.
        with patch.object(app, "_transport_factory", lambda: fake):
            app.destination_validate(ledger, ALIAS)
        app.verify(ledger, timeout=LOCAL)
        with patch.object(app, "_transport_factory", no_network):
            replay = app.send(ledger, did, watchlist_db=root / "unavailable", manifest=object())
        require(replay["result"] == "replay", "confirmed replay requires no originals/transport")
        restored = root / "confirmed-restored.sqlite"
        app.restore(ledger, restored, timeout=LOCAL)
        rejected(lambda: app.send(restored, did), "send_quarantined")

    def outcome_matrix() -> None:
        matrix = [
            (
                "timeout",
                native.TransportResult("uncertain", "transport_timeout"),
                "uncertain",
                "transport_timeout",
            ),
            (
                "exception",
                RuntimeError("private-exception-sentinel"),
                "uncertain",
                "network_uncertain",
            ),
            (
                "permanent",
                native.TransportResult("permanent_failure", "provider_rejection"),
                "permanent_failure",
                "provider_rejection",
            ),
            ("fake-dto", {"state": "confirmed"}, "uncertain", "provider_invalid"),
            (
                "wrong-chat",
                native.TransportResult("confirmed", receipt=native.Receipt(7, 1, BOT, CHAT + 1)),
                "uncertain",
                "provider_invalid",
            ),
            (
                "bool-receipt",
                native.TransportResult("confirmed", receipt=native.Receipt(True, 1, BOT, CHAT)),
                "uncertain",
                "provider_invalid",
            ),
            (
                "bool429",
                native.TransportResult("retryable", "provider_rate_limit", True),
                "uncertain",
                "provider_invalid",
            ),
            ("bad-success", native.TransportResult("confirmed"), "uncertain", "provider_invalid"),
        ]
        for label, outcome, state, category in matrix:
            ledger, did, fake = setup("matrix-" + label, outcome)
            result = invoke(ledger, did, fake)
            require(
                (result["delivery"]["state"], result["error_category"]) == (state, category),
                "conservative normalized result: " + label,
            )
            require(fake.sends == 1, "exactly one fake dispatch")
            rejected(
                lambda ledger=ledger, did=did, fake=fake: invoke(ledger, did, fake),
                "delivery_blocked",
            )
            require(fake.sends == 1, "uncertain/terminal invocation cannot resend")
            app.verify(ledger, timeout=LOCAL)

    def rate_limit() -> None:
        pol = importlib.import_module("card_market_tracker.watchlist_delivery.policy")
        outcome = native.TransportResult("retryable", "provider_rate_limit", 11)
        ledger, did, fake = setup("valid429", outcome)
        # FakePort's original claim check is specialized to first dispatch; later
        # attempts use a callback preserving the same independent lock observation.
        initial = invoke(ledger, did, fake)
        require(
            initial["delivery"]["state"] == "retryable"
            and initial["error_category"] == "rate_limited",
            "valid429 normalized retryable",
        )
        current = app.get(ledger, did, timeout=LOCAL)["delivery"]
        with closing(sqlite3.connect(ledger)) as db:
            high = db.execute("SELECT operational_high_water FROM wtd_metadata").fetchone()[0]
        require(
            high == current["updated_at"] and high < current["not_before"],
            "future cooldown excluded from event watermark",
        )
        rejected(lambda: invoke(ledger, did, fake), "retry_not_due")
        require(fake.sends == 1, "cooldown prevents dispatch")
        for ordinal in (2, 3):
            now = current["not_before"]
            with (
                patch.object(store, "_now", lambda now=now: now),
                patch.object(pol, "now", lambda now=now: now),
            ):
                if ordinal == 2:
                    with patch.object(app, "_transport_factory", lambda: fake):
                        app.destination_validate(ledger, ALIAS)
                    app.verify(ledger, timeout=LOCAL)
                result = invoke(ledger, did, fake)
            current = result["delivery"]
            require(
                current["attempt_count"] == ordinal and fake.sends == ordinal,
                "one new manual claim per valid429",
            )
            if ordinal == 2:
                require(current["state"] == "retryable", "second valid429 retryable")
            else:
                require(
                    current["state"] == "permanent_failure"
                    and result["error_category"] == "retry_exhausted"
                    and current["not_before"] is None,
                    "third valid429 lifetime cap",
                )
            app.verify(ledger, timeout=LOCAL)
        rejected(lambda: invoke(ledger, did, fake), "delivery_blocked")
        require(fake.sends == 3, "no fourth dispatch")

    def postclaim_clock() -> None:
        outcome = native.TransportResult("confirmed", receipt=native.Receipt(31, 1, BOT, CHAT))
        ledger, did, fake = setup("clock-rollback", outcome)
        # Only completion moves backward; original admission and claim remain genuine.
        clock_patch = patch.object(store, "_now", lambda: "2000-01-01T00:00:00.000000Z")
        fake.on_send = clock_patch.start
        try:
            result = invoke(ledger, did, fake)
        finally:
            clock_patch.stop()
        require(
            result["delivery"]["state"] == "uncertain" and result["error_category"] == "clock_skew",
            "postclaim acceptance cannot outrun clock skew",
        )
        app.verify(ledger, timeout=LOCAL)

    def missing_source_no_dispatch() -> None:
        ledger, did, fake = setup("missing-before-send", native.TransportResult("confirmed"))
        saved = src.watch.with_suffix(".absent")
        src.watch.rename(saved)
        try:
            rejected(lambda: invoke(ledger, did, fake), "storage_missing")
        finally:
            saved.rename(src.watch)
        require(
            fake.sends == 0 and fake.bot_checks == 0, "missing original fails before bot and claim"
        )
        require(
            app.get(ledger, did, timeout=LOCAL)["delivery"]["attempt_count"] == 0,
            "missing original creates no durable claim",
        )

    def fencing_recovery() -> None:
        outcome = native.TransportResult("confirmed", receipt=native.Receipt(831, 1, BOT, CHAT))
        real_finish = store._finish

        def captured_claim(label: str) -> tuple[Path, str, FakePort, list[Any]]:
            ledger, did, fake = setup(label, outcome)
            saved = []

            def unavailable(*args: Any) -> None:
                saved.append(args)
                raise RuntimeError("isolated-local-persistence-fault")

            with patch.object(store, "_finish", unavailable):
                rejected(lambda: invoke(ledger, did, fake), "local_commit_failed")
            require(
                len(saved) == 2 and fake.sends == 1, "one HTTP with bounded failed finalization"
            )
            require(
                app.get(ledger, did, timeout=LOCAL)["delivery"]["state"] == "in_flight",
                "failed receipt persistence leaves blocked in_flight",
            )
            return ledger, did, fake, saved[0]

        ledger, did, fake, arguments = captured_claim("recovery-fence")
        rejected(lambda: app.recover(ledger, did, timeout=LOCAL), "invalid_field")
        result = app.recover(ledger, did, worker_quiesced=True, timeout=LOCAL)
        require(
            result["delivery"]["state"] == "uncertain"
            and result["delivery"]["last_error_category"] == "recovered",
            "quiesced recovery only uncertain",
        )
        baseline = ledger.read_bytes()
        rejected(lambda: real_finish(*arguments), "stale_attempt")
        require(ledger.read_bytes() == baseline, "late success cannot overwrite recovered result")
        rejected(lambda: invoke(ledger, did, fake), "delivery_blocked")
        require(fake.sends == 1, "recovery never permits resend")
        ledger, did, fake, arguments = captured_claim("handle-fence")
        path, selected, handle, outcome, budget = arguments
        for forged in (object(), store._ClaimHandle("{}"), copy.copy(handle)):
            rejected(
                lambda forged=forged: real_finish(path, selected, forged, outcome, budget),
                "stale_attempt",
            )
        budget_module = importlib.import_module("card_market_tracker.watchlist_delivery.budget")
        rejected(
            lambda: real_finish(path, selected, handle, outcome, budget_module.Budget(LOCAL)),
            "stale_attempt",
        )
        finished = real_finish(*arguments)
        require(finished["state"] == "confirmed", "genuine owner handle permits one completion")
        rejected(lambda: real_finish(*arguments), "stale_attempt")
        app.verify(ledger, timeout=LOCAL)

    def deadline_phases() -> None:
        budget_module = importlib.import_module("card_market_tracker.watchlist_delivery.budget")
        source_store = importlib.import_module("card_market_tracker.watchlist_alerts.storage")
        # Real admission helpers see the identical Budget; two separate helpers
        # cumulatively spend six synthetic monotonic seconds of one five-second cap.
        ledger, did, fake = setup("origin-deadline", native.TransportResult("confirmed"))
        real_verify, real_pair = source_store.verify, source_store._get_pair
        clock = [time.monotonic()]
        budgets = []

        def delayed_verify(*args: Any, **kwargs: Any) -> Any:
            budgets.append(kwargs["_budget"])
            result = real_verify(*args, **kwargs)
            clock[0] += 3
            return result

        def delayed_pair(*args: Any, **kwargs: Any) -> Any:
            budgets.append(args[2])
            result = real_pair(*args, **kwargs)
            clock[0] += 3
            return result

        with (
            patch.object(budget_module.time, "monotonic", lambda: clock[0]),
            patch.object(source_store, "verify", delayed_verify),
            patch.object(source_store, "_get_pair", delayed_pair),
        ):
            rejected(lambda: invoke(ledger, did, fake), "storage_timeout")
        require(
            len(budgets) >= 2 and all(item is budgets[0] for item in budgets),
            "aggregate original helpers share one exact Budget",
        )
        require(fake.sends == 0 and fake.bot_checks == 0, "origin deadline precedes metadata/claim")
        require(
            app.get(ledger, did, timeout=LOCAL)["delivery"]["attempt_count"] == 0,
            "aggregate original ceiling cannot create claim",
        )
        # Expire only the pre-dispatch allowance after durable claim, leaving the
        # unchanged global reserve available for conservative durable finalization.
        ledger, did, fake = setup("reserve-deadline", native.TransportResult("confirmed"))
        clock = [time.monotonic()]
        real_claim = store._claim_verified

        def exhaust_reserved(*args: Any, **kwargs: Any) -> Any:
            result = real_claim(*args, **kwargs)
            budget = args[3]
            clock[0] = budget.global_deadline - budget.reserve + 0.01
            return result

        with (
            patch.object(budget_module.time, "monotonic", lambda: clock[0]),
            patch.object(store, "_claim_verified", exhaust_reserved),
        ):
            result = invoke(ledger, did, fake)
        require(
            result["delivery"]["state"] == "uncertain"
            and result["error_category"] == "deadline_exceeded"
            and fake.sends == 0,
            "postclaim reserve expiry prevents dispatch and conservatively finalizes",
        )
        require(
            app.verify(ledger, timeout=LOCAL)["counts"]["claims"] == 1,
            "deadline result retains one durable claim",
        )

    report("fake_confirmed_durable_claim_unlocked_http_revalidation_replay_quarantine", confirmed)
    report("fake_native_outcome_matrix_uncertainty_and_no_resend", outcome_matrix)
    report("valid429_exact_cooldown_thirdcap_event_watermark_historical_snapshot", rate_limit)
    report("owner_handle_fencing_late_finalize_quiesced_recovery_no_resend", fencing_recovery)
    report("same_budget_aggregate_origin_cap_postclaim_reserve_deadline", deadline_phases)
    report("postclaim_clock_rollback_overrides_provider_acceptance", postclaim_clock)
    report(
        "missing_original_unconfirmed_send_no_metadata_no_claim_no_dispatch",
        missing_source_no_dispatch,
    )


def local_tamper_and_alias_cases(
    app: Any, root: Path, src: Originals, report: Callable[[str, Callable[[], None]], None]
) -> None:
    def alias_conflict() -> None:
        aa = importlib.import_module("card_market_tracker.watchlist_alerts.application")
        alternate_alias = "independent-other-route"
        alert = aa.enqueue(
            src.outbox,
            src.watch,
            src.journal,
            src.manifest,
            src.signals[0],
            alternate_alias,
            timeout=LOCAL,
        )["alert_id"]
        alternate = Originals(
            src.watch, src.journal, src.outbox, src.manifest, src.entry, [alert], [src.signals[0]]
        )
        ledger = root / "alias-dedup.sqlite"
        new_ledger(app, ledger)
        app.destination_add(
            ledger, alternate_alias, BOT, CHAT, operator_private_owned=True, timeout=LOCAL
        )
        first = prepare(app, ledger, src)
        expected = independent_review(alternate, alias=alternate_alias)
        reviewed = app.review(
            ledger, *src.paths(), src.manifest, alert, alternate_alias, timeout=LOCAL
        )
        require(reviewed["review"] == expected, "independently valid alternate route binding")
        require(
            expected["delivery_id"] == first["delivery"]["delivery_id"],
            "identity excludes alias/route",
        )
        baseline = ledger.read_bytes()
        rejected(lambda: prepare(app, ledger, alternate, alias=alternate_alias), "conflict")
        require(
            ledger.read_bytes() == baseline, "provider+signal alias conflict immutable rollback"
        )
        require(
            app.verify(ledger, timeout=LOCAL)["counts"]["deliveries"] == 1,
            "one delivery despite multiple genuine previews",
        )

    def semantic_sql_tamper() -> None:
        for label in ("calendar", "message-bound", "global-entry"):
            ledger = root / ("negative-" + label + ".sqlite")
            new_ledger(app, ledger)
            prepare(app, ledger, src)
            with closing(sqlite3.connect(ledger)) as db:
                if label == "calendar":
                    db.execute(
                        "UPDATE wtd_metadata SET operational_high_water=?",
                        ("9999-02-30T00:00:00.000000Z",),
                    )
                else:
                    table = "wtd_deliveries" if label == "message-bound" else "wtd_watch_entries"
                    trigger = table + "_no_update"
                    original_trigger = db.execute(
                        "SELECT sql FROM sqlite_master WHERE type='trigger' AND name=?", (trigger,)
                    ).fetchone()[0]
                    db.execute("DROP TRIGGER " + trigger)
                    db.execute("PRAGMA ignore_check_constraints=ON")
                    if label == "message-bound":
                        db.execute("UPDATE wtd_deliveries SET message_text=?", ("Q" * 4097,))
                    else:
                        replacement = dict(src.entry, priority="high")
                        db.execute(
                            "UPDATE wtd_watch_entries SET entry_json=?,entry_sha256=?",
                            (canonical(replacement), sha(canonical(replacement).encode("ascii"))),
                        )
                    db.execute(original_trigger)
                db.commit()
            baseline = ledger.read_bytes()
            rejected(lambda ledger=ledger: app.verify(ledger, timeout=LOCAL), "storage_corrupt")
            rejected(lambda ledger=ledger: prepare(app, ledger, src, 1), "storage_corrupt")
            require(
                ledger.read_bytes() == baseline, "corrupt retained state never repaired or written"
            )

    def ancient_revision() -> None:
        wa = importlib.import_module("card_market_tracker.watchlist.application")
        later = wa.update(
            src.watch,
            src.manifest,
            src.entry["watch_id"],
            {"target_price_minor": 700, "restock_enabled": False, "priority": "low"},
            expected_revision=1,
            request_token="qa-later-head",
            timeout=LOCAL,
        )["entry"]
        require(
            later["revision"] == 2
            and later["target_price_minor"] != src.entry["target_price_minor"],
            "genuine later incompatible latest revision",
        )
        ledger = root / "ancient-revision.sqlite"
        new_ledger(app, ledger)
        original = src.fingerprints()
        selected = prepare(app, ledger, src)
        require(
            selected["delivery"]["evidence_sha256"] == independent_review(src)["evidence_sha256"],
            "historical signal retains exact original revision despite later latest",
        )
        app.recompute(
            ledger, *src.paths(), src.manifest, selected["delivery"]["delivery_id"], timeout=LOCAL
        )
        require(
            src.fingerprints() == original,
            "ancient original admission never rewrites current sources",
        )

    report("provider_signal_dedup_across_genuine_alternate_preview_routes", alias_conflict)
    report("ancient_original_revision_after_newer_incompatible_latest", ancient_revision)
    report("negative_sql_calendar_bounds_rehashed_entry_restored_inventory", semantic_sql_tamper)


def cli_cases(
    app: Any, root: Path, src: Originals, report: Callable[[str, Callable[[], None]], None]
) -> None:
    def cli_closed_privacy() -> None:
        ledger = root / "cli.sqlite"
        new_ledger(app, ledger)
        did = prepare(app, ledger, src)["delivery"]["delivery_id"]
        prefix = ["watchlist-telegram-delivery"]
        cases = [
            ([*prefix, "get", "--ledger-db", str(ledger), "--delivery-id", did], 0),
            ([*prefix, "list", "--ledger-db", str(ledger), "--limit", "1"], 0),
            ([*prefix, "verify", "--ledger-db", str(ledger)], 0),
            ([*prefix, "send", "--ledger-db", str(ledger), "--delivery-id", did], 2),
            ([*prefix, "verify", "--ledger-db", str(ledger), "--timeout", "nan"], 2),
            ([*prefix, "get", "--ledger", str(ledger), "--delivery-id", did], 2),
            ([*prefix, "force", "--ledger-db", str(ledger)], 2),
        ]
        for flags, expected_code in cases:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(Path(__file__).resolve()),
                    "--cli-arguments",
                    canonical(flags),
                ],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            require(completed.returncode == expected_code, "closed CLI error/exit mapping")
            require(len(completed.stdout.splitlines()) == 1, "one complete CLI envelope")
            payload = json.loads(completed.stdout)
            require(completed.stdout == canonical(payload) + "\n", "canonical ASCII JSON plus LF")
            require(payload["version"] == 1, "versioned CLI envelope")
            logs = completed.stderr.splitlines()
            require(len(logs) == 1, "one completion record per invocation")
            log = json.loads(logs[0])
            require(
                log["event"] == "watchlist.telegram_delivery.completed", "fixed completion event"
            )
            for forbidden in (
                str(BOT),
                str(CHAT),
                "SYNTHETIC",
                "message_text",
                "priority",
                "entry_json",
                "private-exception-sentinel",
                "SELECT ",
            ):
                require(
                    forbidden not in completed.stdout + completed.stderr, "CLI privacy sentinel"
                )
            for forbidden_key in (
                "alias",
                "path",
                "route_sha256",
                "binding_sha256",
                "message_sha256",
            ):
                require(forbidden_key not in log, "log privacy allowlist")
        for flags in (
            ["--help"],
            [*prefix, "--help"],
            [*prefix, "send", "--help"],
            ["watchlist-alert-outbox", "--help"],
        ):
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(Path(__file__).resolve()),
                    "--cli-arguments",
                    canonical(flags),
                ],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            require(
                completed.returncode == 0 and "usage:" in completed.stdout,
                "fresh offline help with Telegram/token/network denied",
            )

    report(
        "fresh_process_cli_closed_json_exits_one_completion_privacy_import_token_network_denied",
        cli_closed_privacy,
    )


def child_main(args: Any) -> int:
    """Fresh-process fake sender or strictly offline confirmed replay."""
    with (
        token_guard(),
        patch.object(socket.socket, "connect", no_network),
        patch.object(socket, "create_connection", no_network),
        patch.object(socket, "getaddrinfo", no_network),
    ):
        if args.cli_arguments is not None:
            sys.meta_path.insert(0, NoTelegram())
            from card_market_tracker.cli import main as cli_main

            return int(cli_main(json.loads(args.cli_arguments)))
        if args.replay_ledger is not None:
            deny = NoTelegram()
            sys.meta_path.insert(0, deny)
            app = importlib.import_module("card_market_tracker.watchlist_delivery.application")
            result = app.send(
                args.replay_ledger,
                args.delivery_id,
                watchlist_db=Path("nonexistent-qa-original"),
                manifest=object(),
            )
            require(result["result"] == "replay", "fresh offline confirmed replay")
            require(
                not any(
                    name.startswith("card_market_tracker.telegram_delivery") for name in sys.modules
                ),
                "fresh replay imported no Telegram",
            )
            print(canonical(result))
            return 0
        metadata = json.loads(args.worker.read_text("utf-8"))
        directory = args.worker.parent
        app = importlib.import_module("card_market_tracker.watchlist_delivery.application")
        native = importlib.import_module("card_market_tracker.telegram_delivery.transport")
        az = importlib.import_module("card_market_tracker.watchlist_alerts.storage")
        ledger = Path(metadata["ledger"])
        text = az.get(Path(metadata["outbox"]), metadata["alert"], timeout=LOCAL)["alert"][
            "message_text"
        ]
        fake = FakePort(
            ledger,
            native.TransportResult("confirmed", receipt=native.Receipt(7109, 1, BOT, CHAT)),
            text,
        )

        def dispatch() -> None:
            with (directory / ("http-" + args.worker_tag)).open("x", encoding="ascii") as stream:
                stream.write("durable-claim-observed-no-write-transaction")
            time.sleep(0.25)

        fake.on_send = dispatch
        (directory / ("ready-" + args.worker_tag)).write_text("ready", encoding="ascii")
        until = time.monotonic() + 12
        while not (directory / "start").exists():
            require(time.monotonic() < until, "parent barrier deadline")
            time.sleep(0.01)
        try:
            with patch.object(app, "_transport_factory", lambda: fake):
                result = app.send(
                    ledger,
                    metadata["delivery"],
                    watchlist_db=Path(metadata["watch"]),
                    journal_db=Path(metadata["journal"]),
                    outbox_db=Path(metadata["outbox"]),
                    manifest=metadata["manifest"],
                )
        except Exception as exc:
            category = getattr(exc, "category", None)
            require(
                category in {"delivery_blocked", "storage_locked", "stale_attempt"},
                "competing process unexpected rejection: " + str(category),
            )
            result = {
                "version": 1,
                "operation": "send",
                "result": "error",
                "error_category": category,
            }
        require(fake.sends <= 1, "one dispatch per process")
        print(canonical(result))
        return 0


def subprocess_cases(
    app: Any, root: Path, src: Originals, report: Callable[[str, Callable[[], None]], None]
) -> None:
    native = importlib.import_module("card_market_tracker.telegram_delivery.transport")
    az = importlib.import_module("card_market_tracker.watchlist_alerts.storage")
    text = az.get(src.outbox, src.alerts[0], timeout=LOCAL)["alert"]["message_text"]

    def multiprocess() -> None:
        directory = root / "sender-processes"
        directory.mkdir()
        ledger = directory / "ledger.sqlite"
        new_ledger(app, ledger)
        did = prepare(app, ledger, src)["delivery"]["delivery_id"]
        fake = FakePort(ledger, native.TransportResult("confirmed"), text)
        with patch.object(app, "_transport_factory", lambda: fake):
            app.destination_validate(ledger, ALIAS)
        metadata = directory / "worker.json"
        metadata.write_text(
            canonical(
                {
                    "ledger": str(ledger),
                    "delivery": did,
                    "watch": str(src.watch),
                    "journal": str(src.journal),
                    "outbox": str(src.outbox),
                    "manifest": src.manifest,
                    "alert": src.alerts[0],
                }
            ),
            encoding="utf-8",
        )
        children = []
        try:
            for tag in ("a", "b"):
                children.append(
                    subprocess.Popen(
                        [
                            sys.executable,
                            "-B",
                            str(Path(__file__).resolve()),
                            "--worker",
                            str(metadata),
                            "--worker-tag",
                            tag,
                        ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                )
            until = time.monotonic() + 15
            while not all((directory / ("ready-" + tag)).exists() for tag in ("a", "b")):
                require(time.monotonic() < until, "two actual child processes reached barrier")
                require(
                    all(process.poll() is None for process in children),
                    "worker exited before barrier",
                )
                time.sleep(0.01)
            (directory / "start").write_text("release", encoding="ascii")
            outcomes = []
            for process in children:
                output, errors = process.communicate(timeout=20)
                require(process.returncode == 0, "fake sender child failed: " + errors[-240:])
                outcomes.append(json.loads(output))
        finally:
            for process in children:
                if process.poll() is None:
                    process.kill()
                    process.communicate(timeout=5)
        require(
            len(list(directory.glob("http-*"))) == 1,
            "two processes produce one fake HTTP; outcomes=" + canonical(outcomes),
        )
        counts = app.verify(ledger, timeout=LOCAL)["counts"]
        require(counts["claims"] == 1 and counts["results"] == 1, "one durable fenced claim/result")
        require(
            app.get(ledger, did, timeout=LOCAL)["delivery"]["state"] == "confirmed",
            "competing sender durable receipt",
        )
        require(
            sum(result["result"] == "ok" for result in outcomes) == 1,
            "one process durably confirms",
        )
        # A brand-new interpreter denies Telegram import, token reads and network.
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(Path(__file__).resolve()),
                "--replay-ledger",
                str(ledger),
                "--delivery-id",
                did,
            ],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        require(
            completed.returncode == 0, "fresh replay process failed: " + completed.stderr[-240:]
        )
        replay = json.loads(completed.stdout)
        require(replay["result"] == "replay", "fresh-process offline confirmed replay")
        require(len(list(directory.glob("http-*"))) == 1, "fresh replay produced no extra HTTP")
        require(app.verify(ledger, timeout=LOCAL)["counts"] == counts, "fresh replay nonmutation")

    report(
        "two_real_sender_processes_one_durable_claim_one_fake_http_fresh_denied_replay",
        multiprocess,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("oracle", "origins", "all"), default="all")
    parser.add_argument("--fixtures", type=Path, default=Path("tests/fixtures"))
    parser.add_argument("--cli-arguments")
    parser.add_argument("--worker", type=Path)
    parser.add_argument("--worker-tag", default="")
    parser.add_argument("--replay-ledger", type=Path)
    parser.add_argument("--delivery-id")
    args = parser.parse_args()
    sys.addaudithook(deny_socket_audit)
    if args.worker is not None or args.replay_ledger is not None or args.cli_arguments is not None:
        return child_main(args)
    results: list[dict[str, str]] = []

    def report(name: str, action: Callable[[], None]) -> None:
        try:
            action()
        except Exception as exc:
            # Repro details stay bounded and sanitized, never raw source/provider data.
            results.append(
                {
                    "case": name,
                    "status": "FAIL",
                    "exception": type(exc).__name__,
                    "detail": str(exc)[:240]
                    if isinstance(exc, AssertionError)
                    else str(getattr(exc, "category", "uncategorized")),
                }
            )
        else:
            results.append({"case": name, "status": "PASS"})

    report("literal_identity_preimages_stdlib_oracle", oracle_vectors)
    if args.mode != "oracle":
        deny = NoTelegram()
        sys.meta_path.insert(0, deny)
        with (
            token_guard(),
            patch.object(socket.socket, "connect", no_network),
            patch.object(socket, "create_connection", no_network),
            patch.object(socket, "getaddrinfo", no_network),
            tempfile.TemporaryDirectory(prefix="cmt-p8d-independent-qa-") as temporary,
        ):
            root = Path(temporary)
            manifest = json.loads((args.fixtures / "synthetic_manifest.json").read_text("utf-8"))
            sources: list[Originals] = []

            def build() -> None:
                sources.extend(
                    (
                        originals(root / "first", manifest),
                        originals(root / "equivalent", manifest),
                        originals(root / "incompatible", manifest, priority="high"),
                    )
                )

            report("public_original_pipeline_ancient_replay_two_episodes", build)
            if args.mode == "all" and len(sources) == 3:
                try:
                    app = importlib.import_module(
                        "card_market_tracker.watchlist_delivery.application"
                    )
                except ModuleNotFoundError:
                    results.append(
                        {
                            "case": "p8d_public_api_cases",
                            "status": "BLOCKED",
                            "detail": "P8d application not present yet",
                        }
                    )
                else:
                    public_cases(app, root, *sources, report)
                    authority_cases(app, root, sources[0], report)
                    local_tamper_and_alias_cases(app, root, sources[0], report)
                    cli_cases(app, root, sources[0], report)
                    sys.meta_path.remove(deny)
                    remote_cases(app, root, sources[0], report)
                    subprocess_cases(app, root, sources[0], report)
            if deny in sys.meta_path:
                sys.meta_path.remove(deny)
    print(
        canonical(
            {"probe": "p8d-independent-qa", "results": results, "live": "NOT_AUTHORIZED_NOT_RUN"}
        )
    )
    return (
        1
        if any(r["status"] == "FAIL" for r in results)
        else (3 if any(r["status"] == "BLOCKED" for r in results) else 0)
    )


if __name__ == "__main__":
    raise SystemExit(main())
