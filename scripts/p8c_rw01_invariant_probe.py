"""P8c RW-01 public-API regression: same historical identity must remain consistent.
Run from candidate checkout with Python3.13:
python scripts/p8c_rw01_invariant_probe.py --fixtures tests/fixtures --timeout 5
Exits1 on original bug,0 on corrected behavior. No SQL/private writer/DTO authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import socket
import sqlite3
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    )


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", type=Path, default=Path("tests/fixtures"))
    parser.add_argument("--timeout", type=float, default=2.0)
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 13):
        raise RuntimeError("Python3.13 required")
    if not math.isfinite(args.timeout) or not 0 < args.timeout <= 5:
        raise ValueError("timeout must be positive finite and <=5")
    git = [
        "git",
        "--no-optional-locks",
        "-c",
        "safe.directory=" + str(Path.cwd()).replace("\\", "/"),
    ]

    def g(*values):
        return subprocess.check_output([*git, *values], text=True).strip()

    before = {
        "head": g("rev-parse", "HEAD"),
        "tree": g("rev-parse", "HEAD^{tree}"),
        "product_diff": g("diff", "--", "src/card_market_tracker"),
    }
    sockets = []

    def denied(*a, **k):
        sockets.append("attempt")
        raise AssertionError("product socket forbidden")

    socket.socket = denied
    socket.create_connection = denied
    from card_market_tracker.watchlist import application as wa
    from card_market_tracker.watchlist import storage as ws
    from card_market_tracker.watchlist_alerts import application as app
    from card_market_tracker.watchlist_alerts import storage as store
    from card_market_tracker.watchlist_alerts.errors import OutboxError
    from card_market_tracker.watchlist_journal import application as ja
    from card_market_tracker.watchlist_journal import storage as js

    manifest = json.loads((args.fixtures / "synthetic_manifest.json").read_text(encoding="utf-8"))
    config = json.loads(
        (args.fixtures / "synthetic_watchlist_config.json").read_text(encoding="utf-8")
    )
    sample = json.loads(
        (args.fixtures / "synthetic_watchlist_current.json").read_text(encoding="utf-8")
    )
    result = {
        "probe": "P8c-RW01-public-originals",
        "started_utc": datetime.now(UTC).isoformat(),
        "candidate": before,
        "python": platform.python_version(),
        "sqlite": sqlite3.sqlite_version,
        "probe_sha256": digest(Path(__file__).read_bytes()),
        "public_APIs_only": True,
    }
    timeout = {"timeout": args.timeout}

    def outcome(call):
        try:
            return {"response": call()}
        except OutboxError as error:
            return {"error_category": error.category, "exit_code": error.exit_code}

    with tempfile.TemporaryDirectory(prefix="cmt-p8c-rw01-legitimate-") as temporary:
        root = Path(temporary)
        pairs = []
        for label, target in (("a", 900), ("b", 1000)):
            watch, journal = root / (label + "-watch.sqlite"), root / (label + "-journal.sqlite")
            ws.initialize(watch, **timeout)
            selected = {**config, "target_price_minor": target, "restock_enabled": False}
            entry = wa.add(
                watch,
                manifest,
                sample["cmt_id"],
                selected,
                request_token="rw01-" + label,
                **timeout,
            )["entry"]
            js.initialize(journal, **timeout)
            old = {
                **sample,
                "sample_id": "rw01-baseline",
                "series_key": "rw01-series",
                "unit_price_minor": 1500,
                "shipping_minor": 0,
                "stock": "AVAILABLE",
                "observed_at": "2026-10-23T12:00:00Z",
            }
            current = {
                **old,
                "sample_id": "rw01-enter",
                "unit_price_minor": 500,
                "observed_at": "2026-10-23T12:01:00Z",
            }
            baseline = ja.record(
                journal,
                watch,
                manifest,
                entry["watch_id"],
                old,
                revision=entry["revision"],
                as_of=old["observed_at"],
                **timeout,
            )
            point = ja.record(
                journal,
                watch,
                manifest,
                entry["watch_id"],
                current,
                old,
                revision=entry["revision"],
                as_of=current["observed_at"],
                **timeout,
            )
            assert baseline["signal_ids"] == [] and len(point["signal_ids"]) == 1
            ws.verify(watch, **timeout)
            js.verify(journal, **timeout)
            pairs.append((watch, journal, entry, point["signal_ids"][0]))
        assert pairs[0][2]["watch_id"] == pairs[1][2]["watch_id"]
        assert pairs[0][2]["revision"] == pairs[1][2]["revision"] == 1
        assert canonical(pairs[0][2]) != canonical(pairs[1][2])
        assert pairs[0][3] != pairs[1][3]
        sources = {p.name: digest(p.read_bytes()) for pair in pairs for p in pair[:2]}
        outbox = root / "outbox.sqlite"
        store.initialize(outbox, **timeout)

        def enqueue(pair):
            return app.enqueue(
                outbox, pair[0], pair[1], manifest, pair[3], "rw01-preview", **timeout
            )

        first = enqueue(pairs[0])
        assert first["result"] == "recorded"
        original = store.get(outbox, first["alert_id"], **timeout)
        original_evidence = store.evidence_get(outbox, first["alert_id"], **timeout)
        assert store.verify(outbox, **timeout)["counts"] == {"alerts": 1, "evidence": 1}
        frozen_bytes = outbox.read_bytes()
        second = outcome(lambda: enqueue(pairs[1]))
        verify = outcome(lambda: store.verify(outbox, **timeout))
        backup = outcome(lambda: store.backup(outbox, root / "backup.sqlite", **timeout))
        same_bytes = outbox.read_bytes() == frozen_bytes
        same_alert = store.get(outbox, first["alert_id"], **timeout) == original
        same_evidence = (
            store.evidence_get(outbox, first["alert_id"], **timeout) == original_evidence
        )
        source_same = all(
            digest(p.read_bytes()) == sources[p.name] for pair in pairs for p in pair[:2]
        )
        defect = (
            second.get("response", {}).get("result") == "recorded"
            and verify.get("error_category") == "storage_corrupt"
            and backup.get("error_category") == "storage_corrupt"
        )
        healthy = (
            second.get("error_category") == "identity_conflict"
            and second.get("exit_code") == 2
            and same_bytes
            and same_alert
            and same_evidence
            and source_same
            and verify.get("response", {}).get("counts") == {"alerts": 1, "evidence": 1}
            and backup.get("response", {}).get("counts") == {"alerts": 1, "evidence": 1}
            and not sockets
        )
        result.update(
            {
                "same_watch_revision": True,
                "different_full_entries": True,
                "target_price_minor": [900, 1000],
                "different_signal_ids": True,
                "signal_ids": [pair[3] for pair in pairs],
                "first_enqueue": first,
                "second_enqueue": second,
                "verify": verify,
                "backup": backup,
                "outbox_bytes_preserved": same_bytes,
                "first_alert_timestamp_preserved": same_alert,
                "first_evidence_preserved": same_evidence,
                "all_four_sources_bytes_preserved": source_same,
                "source_sha256": sources,
                "socket_attempts": len(sockets),
                "defect_reproduced": defect,
                "invariant_test": "PASS" if healthy else "FAIL",
            }
        )
    assert g("rev-parse", "HEAD") == before["head"]
    result["completed_utc"] = datetime.now(UTC).isoformat()
    result["head_stable"] = True
    print(canonical(result))
    return 0 if healthy else 1


if __name__ == "__main__":
    raise SystemExit(main())
