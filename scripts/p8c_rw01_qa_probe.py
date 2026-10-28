"""Independent RW-01 QA; original fixtures use only public P5a/P5b/P8c APIs.

Run: python scripts/p8c_rw01_qa_probe.py --fixtures tests/fixtures --timeout 5
SQL is confined to explicitly negative outbox fixtures and lock coordination.
No product oracle, author tests, or other probe helpers are imported.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

from card_market_tracker.watchlist import application as wa
from card_market_tracker.watchlist import storage as ws
from card_market_tracker.watchlist_alerts import application as aa
from card_market_tracker.watchlist_alerts import storage as az
from card_market_tracker.watchlist_alerts.errors import OutboxError
from card_market_tracker.watchlist_journal import application as ja
from card_market_tracker.watchlist_journal import storage as js

PRODUCT = "541b9d13-9669-4973-8413-397bea14c045"
OTHER_PRODUCT = "b980e1f7-9bae-432e-b02a-182dbcca478d"
BASE = {"target_price_minor": 1000, "restock_enabled": False}


def canonical(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    )


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def check(condition: object, label: str) -> None:
    if not condition:
        raise AssertionError(label)


def error(call: Callable[[], object], category: str, code: int) -> None:
    try:
        call()
    except OutboxError as exc:
        check((exc.category, exc.exit_code) == (category, code), "error category or exit code")
    else:
        raise AssertionError("expected " + category)


@dataclass
class Source:
    watch: Path
    journal: Path
    entry: dict[str, Any]
    points: list[dict[str, Any]]
    samples: list[dict[str, Any]]
    manifest: dict[str, Any]
    timeout: float

    @property
    def signal(self) -> str:
        signals = self.points[-1]["signal_ids"]
        check(len(signals) == 1, "one genuine selected price signal")
        return str(signals[0])

    def enqueue(self, outbox: Path, alias: str = "qa-local") -> dict[str, object]:
        return aa.enqueue(
            outbox,
            self.watch,
            self.journal,
            self.manifest,
            self.signal,
            alias,
            timeout=self.timeout,
        )

    def original_bytes(self) -> tuple[bytes, bytes]:
        return self.watch.read_bytes(), self.journal.read_bytes()

    def append(self, price: int) -> None:
        ordinal = len(self.samples) + 1
        sample = {
            "version": 1,
            "provenance": "synthetic",
            "sample_id": f"qa-sample-{ordinal}",
            "cmt_id": self.entry["cmt_id"],
            "series_key": self.samples[0]["series_key"],
            "observed_at": f"2026-10-25T12:0{ordinal}:00Z",
            "currency": "EUR",
            "unit_price_minor": price,
            "shipping_minor": 0,
            "stock": "AVAILABLE",
        }
        self.points.append(
            ja.record(
                self.journal,
                self.watch,
                self.manifest,
                self.entry["watch_id"],
                sample,
                self.samples[-1],
                revision=self.entry["revision"],
                as_of=sample["observed_at"],
                timeout=self.timeout,
            )
        )
        self.samples.append(sample)


def source(
    directory: Path,
    manifest: dict[str, Any],
    timeout: float,
    *,
    config: dict[str, Any] | None = None,
    series: str = "qa-series",
    product: str = PRODUCT,
    revision: int = 1,
    sample_prefix: str = "qa-sample",
) -> Source:
    directory.mkdir()
    watch, journal = directory / "watch.sqlite", directory / "journal.sqlite"
    ws.initialize(watch, timeout=timeout)
    entry = wa.add(watch, manifest, product, BASE, request_token="qa-add", timeout=timeout)["entry"]
    chosen = dict(BASE if config is None else config)
    if revision == 1 and chosen != BASE:
        # Independent stores, each genuinely created through the public add API.
        watch = directory / "independent-watch.sqlite"
        ws.initialize(watch, timeout=timeout)
        entry = wa.add(
            watch,
            manifest,
            product,
            chosen,
            request_token="qa-config",
            timeout=timeout,
        )["entry"]
    if revision == 2:
        entry = wa.update(
            watch,
            manifest,
            entry["watch_id"],
            chosen,
            expected_revision=1,
            request_token="qa-update",
            timeout=timeout,
        )["entry"]
    js.initialize(journal, timeout=timeout)
    points, samples = [], []
    for ordinal, price in enumerate((1200, 800), 1):
        sample = {
            "version": 1,
            "provenance": "synthetic",
            "sample_id": f"{sample_prefix}-{ordinal}",
            "cmt_id": product,
            "series_key": series,
            "observed_at": f"2026-10-25T12:0{ordinal}:00Z",
            "currency": "EUR",
            "unit_price_minor": price,
            "shipping_minor": 0,
            "stock": "AVAILABLE",
        }
        points.append(
            ja.record(
                journal,
                watch,
                manifest,
                entry["watch_id"],
                sample,
                samples[-1] if samples else None,
                revision=revision,
                as_of=sample["observed_at"],
                timeout=timeout,
            )
        )
        samples.append(sample)
    check(all(item["result"] == "recorded" for item in points), "genuine source creation")
    return Source(watch, journal, entry, points, samples, manifest, timeout)


def state(outbox: Path, alert_id: object, timeout: float) -> tuple[bytes, str, str, str]:
    return (
        outbox.read_bytes(),
        canonical(az.get(outbox, alert_id, timeout=timeout)),
        canonical(az.evidence_get(outbox, alert_id, timeout=timeout)),
        canonical(az.list_alerts(outbox, timeout=timeout)),
    )


def healthy(outbox: Path, count: int, timeout: float, label: str) -> None:
    expected = {"alerts": count, "evidence": count}
    check(az.verify(outbox, timeout=timeout)["counts"] == expected, "healthy verify counts")
    backup = outbox.with_name(label + "-backup.sqlite")
    check(az.backup(outbox, backup, timeout=timeout)["counts"] == expected, "backup counts")
    check(az.verify(backup, timeout=timeout)["counts"] == expected, "backup reopened")


def oracle(outbox: Path, response: dict[str, object], src: Source, alias: str) -> None:
    signal = src.signal
    expected = "walt1_" + digest(
        b"CMT_WATCHLIST_ALERT_V1\x00"
        + canonical({"identity_version": 1, "destination_key": alias, "signal_id": signal}).encode()
    )
    check(response["alert_id"] == expected, "independent domain-separated alert identity")
    item = az.get(outbox, expected, timeout=src.timeout)["alert"]
    bundle = az.evidence_get(outbox, expected, timeout=src.timeout)
    check(item["message_sha256"] == digest(item["message_text"].encode()), "message digest")
    check(item["intent_sha256"] == digest(canonical(item["intent"]).encode()), "intent digest")
    check(
        bundle["evidence_sha256"] == digest(canonical(bundle["evidence"]).encode()),
        "evidence digest",
    )
    for side in ("predecessor", "current"):
        check(
            canonical(bundle["evidence"][side]["snapshot"]["entry"]) == canonical(src.entry),
            "complete source entry retained",
        )


def conflict_case(
    root: Path,
    manifest: dict[str, Any],
    timeout: float,
    name: str,
    change: dict[str, Any],
    *,
    alias: str = "qa-local",
    series: str = "qa-series",
) -> None:
    area = root / name
    area.mkdir()
    left = source(area / "a", manifest, timeout)
    right = source(area / "b", manifest, timeout, config=BASE | change, series=series)
    check(left.entry["watch_id"] == right.entry["watch_id"], "same genuine watch identity")
    check(left.entry["revision"] == right.entry["revision"] == 1, "same original revision")
    check(canonical(left.entry) != canonical(right.entry), "independently different full entry")
    check(left.signal != right.signal, "different genuine signal identities")
    originals = left.original_bytes(), right.original_bytes()
    box = area / "outbox.sqlite"
    az.initialize(box, timeout=timeout)
    first = left.enqueue(box)
    check(first["result"] == "recorded", "first recorded")
    oracle(box, first, left, "qa-local")
    before = state(box, first["alert_id"], timeout)
    error(lambda: right.enqueue(box, alias), "identity_conflict", 2)
    check(
        state(box, first["alert_id"], timeout) == before,
        "all bytes/time/evidence/cardinality unchanged",
    )
    healthy(box, 1, timeout, "rejected")
    check(
        (left.original_bytes(), right.original_bytes()) == originals,
        "both original pairs unchanged",
    )


def coexist_case(
    root: Path, manifest: dict[str, Any], timeout: float, name: str, **options: Any
) -> None:
    area = root / name
    area.mkdir()
    a = source(area / "a", manifest, timeout)
    alias = options.pop("alias", "qa-local")
    b = source(area / "b", manifest, timeout, **options)
    before = a.original_bytes(), b.original_bytes()
    box = area / "outbox.sqlite"
    az.initialize(box, timeout=timeout)
    first, second = a.enqueue(box), b.enqueue(box, alias)
    check(
        (first["result"], second["result"]) == ("recorded", "recorded"), "both compatible recorded"
    )
    check(first["alert_id"] != second["alert_id"], "distinct compatible alert identities")
    oracle(box, second, b, alias)
    healthy(box, 2, timeout, "coexist")
    check((a.original_bytes(), b.original_bytes()) == before, "coexisting sources unchanged")


def ancient(root: Path, manifest: dict[str, Any], timeout: float) -> None:
    area = root / "ancient"
    area.mkdir()
    src = source(area / "source", manifest, timeout)
    box = area / "outbox.sqlite"
    az.initialize(box, timeout=timeout)
    first = src.enqueue(box)
    old_signal = src.signal
    saved = state(box, first["alert_id"], timeout)
    src.append(1200)
    src.append(800)
    wa.update(
        src.watch,
        manifest,
        src.entry["watch_id"],
        BASE | {"priority": "high"},
        expected_revision=1,
        request_token="qa-new-head",
        timeout=timeout,
    )
    originals = src.original_bytes()
    replay = aa.enqueue(
        box, src.watch, src.journal, manifest, old_signal, "qa-local", timeout=timeout
    )
    check(replay == first | {"result": "replayed"}, "ancient exact replay response")
    check(state(box, first["alert_id"], timeout) == saved, "ancient replay preserves everything")
    check(src.original_bytes() == originals, "ancient admission read-only")
    healthy(box, 1, timeout, "ancient")


def command(box: Path, src: Source, manifest_file: Path, timeout: float) -> list[str]:
    return [
        sys.executable,
        "-m",
        "card_market_tracker.cli",
        "watchlist-alert-outbox",
        "enqueue",
        "--outbox-db",
        str(box),
        "--watchlist-db",
        str(src.watch),
        "--journal-db",
        str(src.journal),
        "--manifest",
        str(manifest_file),
        "--signal-id",
        src.signal,
        "--destination-key",
        "qa-local",
        "--timeout",
        str(timeout),
    ]


def race(root: Path, manifest: dict[str, Any], timeout: float) -> None:
    area = root / "real-process-race"
    area.mkdir()
    a = source(area / "a", manifest, timeout)
    b = source(area / "b", manifest, timeout, config=BASE | {"priority": "high"})
    originals = a.original_bytes(), b.original_bytes()
    manifest_file = area / "manifest.json"
    manifest_file.write_text(canonical(manifest), encoding="ascii")
    box = area / "outbox.sqlite"
    az.initialize(box, timeout=timeout)
    # Coordination only: hold the outbox lock while both real standard CLI processes start.
    with sqlite3.connect(box, autocommit=True) as lock:
        lock.execute("BEGIN IMMEDIATE")
        children = [
            subprocess.Popen(
                command(box, s, manifest_file, timeout),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for s in (a, b)
        ]
        time.sleep(min(0.2, timeout / 10))
        lock.execute("ROLLBACK")
    lock.close()
    outcomes = []
    for child in children:
        stdout, _ = child.communicate(timeout=15)
        body = json.loads(stdout)
        outcomes.append((child.returncode, body.get("result"), body.get("error_category")))
    check(
        sorted(outcomes, key=lambda item: item[0])
        == [(0, "recorded", None), (2, "error", "identity_conflict")],
        "two-process serialized conflict",
    )
    healthy(box, 1, timeout, "race")
    check((a.original_bytes(), b.original_bytes()) == originals, "race source preservation")


def negative_union(root: Path, manifest: dict[str, Any], timeout: float) -> None:
    area = root / "NEGATIVE-SQL-corrupt-union"
    area.mkdir()
    a = source(area / "a", manifest, timeout)
    b = source(area / "b", manifest, timeout, config=BASE | {"target_price_minor": 900})
    originals = a.original_bytes(), b.original_bytes()
    boxes = [area / "a.sqlite", area / "b.sqlite"]
    for box, src in zip(boxes, (a, b), strict=True):
        az.initialize(box, timeout=timeout)
        src.enqueue(box)
    # Explicitly negative local-outbox fixture: combine genuine, separately admitted rows.
    with sqlite3.connect(boxes[1]) as other, sqlite3.connect(boxes[0]) as dest:
        row = other.execute(
            "SELECT alert_id,destination_key,signal_id,policy_version,renderer_version,"
            "channel,state,intent_json,intent_sha256,message_text,message_sha256,"
            "first_prepared_at FROM watchlist_alerts"
        ).fetchone()
        evidence = other.execute(
            "SELECT alert_id,evidence_json,evidence_sha256 FROM watchlist_alert_evidence"
        ).fetchone()
        dest.execute("INSERT INTO watchlist_alerts VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", row)
        dest.execute("INSERT INTO watchlist_alert_evidence VALUES (?,?,?)", evidence)
    other.close()
    dest.close()
    before = boxes[0].read_bytes()
    error(lambda: a.enqueue(boxes[0]), "storage_corrupt", 1)
    error(lambda: b.enqueue(boxes[0], "qa-other"), "storage_corrupt", 1)
    error(lambda: az.verify(boxes[0], timeout=timeout), "storage_corrupt", 1)
    backup = area / "forbidden-backup.sqlite"
    error(lambda: az.backup(boxes[0], backup, timeout=timeout), "storage_corrupt", 1)
    check(not backup.exists(), "no corrupted recovery publication")
    check(boxes[0].read_bytes() == before, "corrupt store preserved")
    check((a.original_bytes(), b.original_bytes()) == originals, "negative union sources untouched")


def negative_replay(root: Path, manifest: dict[str, Any], timeout: float) -> None:
    area = root / "NEGATIVE-SQL-valid-local-replay-conflict"
    area.mkdir()
    src = source(area / "source", manifest, timeout)
    src.append(1200)
    src.append(800)
    originals = src.original_bytes()
    box = area / "outbox.sqlite"
    az.initialize(box, timeout=timeout)
    first = src.enqueue(box)
    # The two-evaluation local proof permits omitted earlier ancestry to remain opaque.
    # Alter only that local link, rehash, and restore the literal immutable trigger.
    with sqlite3.connect(box) as db:
        trigger = db.execute(
            "SELECT sql FROM sqlite_master WHERE name='watchlist_alert_evidence_no_update'"
        ).fetchone()[0]
        evidence = json.loads(
            db.execute("SELECT evidence_json FROM watchlist_alert_evidence").fetchone()[0]
        )
        evidence["predecessor"]["predecessor_evaluation_id"] = "wje1_" + "e" * 64
        raw = canonical(evidence)
        db.execute("DROP TRIGGER watchlist_alert_evidence_no_update")
        db.execute(
            "UPDATE watchlist_alert_evidence SET evidence_json=?,evidence_sha256=?",
            (raw, digest(raw.encode())),
        )
        db.execute(trigger)
    db.close()
    check(
        az.verify(box, timeout=timeout)["result"] == "ok",
        "locally valid alternate omitted ancestry",
    )
    before = state(box, first["alert_id"], timeout)
    error(lambda: src.enqueue(box), "replay_conflict", 2)
    check(state(box, first["alert_id"], timeout) == before, "replay conflict preserves stored pair")
    healthy(box, 1, timeout, "replay-conflict")
    check(src.original_bytes() == originals, "negative replay originals untouched")


def rollback_fault(root: Path, manifest: dict[str, Any], timeout: float) -> None:
    area = root / "injected-stdlib-write-failure"
    area.mkdir()
    src = source(area / "source", manifest, timeout)
    originals = src.original_bytes()
    box = area / "outbox.sqlite"
    az.initialize(box, timeout=timeout)
    before = box.read_bytes()
    reached: list[bool] = []
    real_connect = sqlite3.connect

    class FaultConnection(sqlite3.Connection):
        def execute(self, sql: str, parameters: Any = (), /) -> sqlite3.Cursor:
            if sql.startswith("INSERT INTO watchlist_alert_evidence"):
                reached.append(self.in_transaction)
                raise sqlite3.OperationalError("injected independent QA fault")
            return super().execute(sql, parameters)

    def connect(*args: Any, **kwargs: Any) -> sqlite3.Connection:
        if str(args[0]).startswith(box.as_uri() + "?mode=rw"):
            kwargs["factory"] = FaultConnection
        return real_connect(*args, **kwargs)

    with patch.object(sqlite3, "connect", connect):
        error(lambda: src.enqueue(box), "storage_io", 1)
    check(reached == [True], "failure reached between inserts inside transaction")
    check(box.read_bytes() == before, "precommit failure byte-exact rollback")
    healthy(box, 0, timeout, "fault")
    check(src.enqueue(box)["result"] == "recorded", "fresh original admission after rollback")
    healthy(box, 1, timeout, "recovered")
    check(src.original_bytes() == originals, "fault originals untouched")


def deadlines(root: Path, manifest: dict[str, Any], timeout: float) -> None:
    area = root / "deadline-validation"
    area.mkdir()
    src = source(area / "source", manifest, timeout)
    box = area / "outbox.sqlite"
    az.initialize(box, timeout=timeout)
    before = box.read_bytes(), src.original_bytes()
    for invalid in (0.0, -1.0, 5.001, float("inf"), float("nan"), True):
        error(
            lambda invalid=invalid: aa.enqueue(
                box,
                src.watch,
                src.journal,
                manifest,
                src.signal,
                "qa-local",
                timeout=invalid,
            ),
            "invalid_field",
            2,
        )
    error(
        lambda: aa.enqueue(
            box,
            src.watch,
            src.journal,
            manifest,
            src.signal,
            "qa-local",
            timeout=1e-12,
        ),
        "storage_timeout",
        1,
    )
    check(
        (box.read_bytes(), src.original_bytes()) == before, "invalid/expired budgets do not write"
    )
    healthy(box, 0, timeout, "deadline")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", type=Path, default=Path("tests/fixtures"))
    parser.add_argument("--timeout", type=float, default=2.0)
    args = parser.parse_args()
    if not math.isfinite(args.timeout) or not 0 < args.timeout <= 5:
        parser.error("timeout must be positive finite and at most 5")
    started = datetime.now(UTC).isoformat()
    manifest = json.loads((args.fixtures / "synthetic_manifest.json").read_text(encoding="utf-8"))
    checks: list[str] = []
    with tempfile.TemporaryDirectory(prefix="cmt-rw01-independent-qa-") as temporary:
        root = Path(temporary)
        cases = [
            ("target", {"target_price_minor": 900}, {}),
            ("destination", {"target_price_minor": 900}, {"alias": "qa-other"}),
            ("series", {"target_price_minor": 900}, {"series": "qa-other-series"}),
            ("priority", {"priority": "high"}, {}),
            ("freshness", {"max_age_seconds": 600}, {}),
            ("rule-config", {"restock_enabled": True}, {}),
        ]
        for name, change, options in cases:
            conflict_case(root, manifest, args.timeout, name, change, **options)
            checks.append(name + "-conflict-preserves-healthy-store")
        for name, options in [
            ("compatible-alias", {"alias": "qa-other"}),
            ("compatible-series", {"series": "qa-other-series"}),
            ("compatible-samples", {"sample_prefix": "independent-sample"}),
            ("different-revision", {"revision": 2, "config": BASE | {"target_price_minor": 900}}),
            ("different-product", {"product": OTHER_PRODUCT}),
        ]:
            coexist_case(root, manifest, args.timeout, name, **options)
            checks.append(name)
        for name, operation in [
            ("ancient-replay", ancient),
            ("real-process-conflicting-race", race),
            ("negative-outbox-corruption-priority", negative_union),
            ("negative-local-valid-replay-conflict", negative_replay),
            ("precommit-stdlib-write-failure-rollback", rollback_fault),
            ("unchanged-budget-limits-and-expiry", deadlines),
        ]:
            operation(root, manifest, args.timeout)
            checks.append(name)
    print(
        canonical(
            {
                "version": 1,
                "probe": "p8c-rw01-independent-qa",
                "result": "PASS",
                "started_at": started,
                "finished_at": datetime.now(UTC).isoformat(),
                "python": sys.version.split()[0],
                "sqlite": sqlite3.sqlite_version,
                "timeout": args.timeout,
                "checks_count": len(checks),
                "checks": checks,
                "original_fixture_authority": "public-P5a-P5b-APIs-only",
                "oracle": "independent-stdlib-canonicalization-hashes-and-complete-entry-equality",
                "negative_sql_scope": "outbox-negative-fixtures-and-race-lock-only",
                "fault_scope": "stdlib-sqlite-connection-injected-before-evidence-insert",
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
