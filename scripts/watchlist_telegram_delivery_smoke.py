"""Thirteenth harness: genuine synthetic Watchlist delivery, fake provider only."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

from scoped_capture_discovery_smoke import OFFLINE

NO_TELEGRAM = """
import importlib.abc, os


class Denied(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith("card_market_tracker.telegram_delivery"):
            raise AssertionError("Telegram imported offline")


sys.meta_path.insert(0, Denied())
original_get = os.environ.get
original_item = type(os.environ).__getitem__


def get(key, *args):
    if key == "CMT_TELEGRAM_BOT_TOKEN":
        raise AssertionError("token read")
    return original_get(key, *args)


def item(self, key):
    if key == "CMT_TELEGRAM_BOT_TOKEN":
        raise AssertionError("token read")
    return original_item(self, key)


os.environ.get = get
type(os.environ).__getitem__ = item
"""

SEED = """
import hashlib, json, os
from card_market_tracker.watchlist import application as w, storage as ws
from card_market_tracker.watchlist_journal import application as j, storage as js
from card_market_tracker.watchlist_alerts import application as a, storage as als
from card_market_tracker.watchlist_delivery import application as d

fixtures, data = map(Path, sys.argv[1:])
os.umask(0o077)
manifest = json.loads((fixtures / "synthetic_manifest.json").read_text())
config = json.loads((fixtures / "synthetic_watchlist_config.json").read_text())
base = json.loads((fixtures / "synthetic_watchlist_current.json").read_text())
watch, journal, outbox, ledger = [
    data / (name + ".sqlite3") for name in ("watch", "journal", "outbox", "ledger")
]
ws.initialize(watch, timeout=5)
entry = w.add(watch, manifest, base["cmt_id"], config, request_token="p8d-smoke", timeout=5)[
    "entry"
]
js.initialize(journal, timeout=5)
previous = None
signals = []
for index, stock in enumerate(
    ("OUT_OF_STOCK", "AVAILABLE", "AVAILABLE", "OUT_OF_STOCK", "AVAILABLE")
):
    current = dict(
        base,
        sample_id="p8d-smoke-" + str(index),
        stock=stock,
        observed_at="2026-10-23T12:0" + str(index) + ":00Z",
    )
    result = j.record(
        journal,
        watch,
        manifest,
        entry["watch_id"],
        current,
        previous,
        revision=1,
        as_of=current["observed_at"],
        timeout=5,
    )
    assert result["signals_count"] == (2 if index in (1, 4) else 0)
    signals.extend(result["signal_ids"])
    previous = current
assert len(signals) == 4
als.initialize(outbox, timeout=5)
alerts = [
    a.enqueue(outbox, watch, journal, manifest, s, "local-preview", timeout=5)["alert_id"]
    for s in signals
]
assert als.verify(outbox, timeout=5)["counts"] == {"alerts": 4, "evidence": 4}
d.initialize(ledger, timeout=5)
d.destination_add(ledger, "local-preview", 1, 2, operator_private_owned=True, timeout=5)
d.backup(ledger, data / "empty-backup.sqlite3", timeout=5)


def prepare(path, alert):
    review = d.review(path, watch, journal, outbox, manifest, alert, "local-preview", timeout=5)[
        "review"
    ]
    consent = {"acknowledgement": review["acknowledgement"]}
    for key in (
        "signal_id",
        "revision",
        "message_sha256",
        "evidence_sha256",
        "route_sha256",
        "binding_sha256",
    ):
        consent["expected_" + key] = review[key]
    return d.prepare(
        path, watch, journal, outbox, manifest, alert, "local-preview", timeout=5, **consent
    )["delivery"]["delivery_id"]


selected = prepare(ledger, alerts[0])
recovery = prepare(ledger, alerts[1])
saved = {
    "selected": selected,
    "recovery": recovery,
    "alerts": alerts,
    "sources": {
        name: hashlib.sha256(path.read_bytes()).hexdigest()
        for name, path in (("watch", watch), ("journal", journal), ("outbox", outbox))
    },
}
(data / "selection.json").write_text(json.dumps(saved), encoding="utf-8")
print("five checkpoints; four genuine signals/previews; selected historical delivery prepared")
"""

FAKE_SEND = """
import json, sqlite3
from card_market_tracker.watchlist_delivery import application as d
from card_market_tracker.telegram_delivery.transport import Receipt, TransportResult
from card_market_tracker.watchlist_alerts import storage as a

data = Path(sys.argv[1])
mode = sys.argv[2]
saved = json.loads((data / "selection.json").read_text())
ledger = data / "ledger.sqlite3"
did = saved["selected"] if mode == "confirm" else saved["recovery"]
expected = a.get(
    data / "outbox.sqlite3", saved["alerts"][0 if mode == "confirm" else 1], timeout=5
)["alert"]["message_text"]
calls = {"metadata": 0, "send": 0}


class Fake:
    def check_configuration(self):
        pass

    def validate_destination(self, bot, chat, *, timeout):
        assert (bot, chat) == (1, 2) and timeout > 0
        calls["metadata"] += 2

    def validate_bot(self, bot, *, timeout):
        assert bot == 1 and timeout > 0
        calls["metadata"] += 1

    def send(self, bot, chat, message, *, timeout):
        assert message == expected and (bot, chat) == (1, 2) and timeout > 0
        with sqlite3.connect(ledger) as db:
            assert db.execute(
                "SELECT state,attempt_count FROM wtd_state WHERE delivery_id=?", (did,)
            ).fetchone() == ("in_flight", 1)
            db.execute("BEGIN IMMEDIATE")
            db.rollback()
        calls["send"] += 1
        if mode == "crash":
            raise SystemExit(77)
        return TransportResult("confirmed", receipt=Receipt(3, 1, bot, chat))


d._transport_factory = lambda: Fake()
if mode == "confirm":
    d.destination_validate(ledger, "local-preview")
try:
    result = d.send(
        ledger,
        did,
        watchlist_db=data / "watch.sqlite3",
        journal_db=data / "journal.sqlite3",
        outbox_db=data / "outbox.sqlite3",
        manifest=json.loads((Path(sys.argv[3]) / "synthetic_manifest.json").read_text()),
    )
except SystemExit as error:
    assert mode == "crash" and error.code == 77
else:
    assert mode == "confirm" and result["delivery"]["state"] == "confirmed"
assert calls["send"] == 1
print(
    json.dumps(
        {
            "fake_only": True,
            "mode": mode,
            "send_attempts": calls["send"],
            "metadata_upper_bound": calls["metadata"],
        }
    )
)
"""

REPLAY = """
import json
from card_market_tracker.cli import main

data = Path(sys.argv[1])
saved = json.loads((data / "selection.json").read_text())


def forbidden():
    raise AssertionError("factory used on replay")


from card_market_tracker.watchlist_delivery import application as d

d._transport_factory = forbidden
sys.exit(
    main(
        [
            "watchlist-telegram-delivery",
            "send",
            "--ledger-db",
            str(data / "ledger.sqlite3"),
            "--delivery-id",
            saved["selected"],
            "--timeout",
            "5",
            "--manifest",
            str(data / "does-not-exist.json"),
        ]
    )
)
"""

RECOVER = """
import json
import time
from card_market_tracker.watchlist_delivery import application as d

data, fixtures = map(Path, sys.argv[1:])
saved = json.loads((data / "selection.json").read_text())
ledger = data / "ledger.sqlite3"
assert d.get(ledger, saved["recovery"], timeout=5)["delivery"]["state"] == "in_flight"
assert (
    d.recover(ledger, saved["recovery"], worker_quiesced=True, timeout=5)["delivery"]["state"]
    == "uncertain"
)
manifest = json.loads((fixtures / "synthetic_manifest.json").read_text())
assert (
    d.recompute(
        ledger,
        data / "watch.sqlite3",
        data / "journal.sqlite3",
        data / "outbox.sqlite3",
        manifest,
        saved["selected"],
        timeout=5,
    )["result"]
    == "ok"
)
timings = []
for index in range(3):
    backup = data / ("backup-" + str(index) + ".sqlite3")
    restored = data / ("restore-" + str(index) + ".sqlite3")
    began = time.monotonic()
    d.backup(ledger, backup, timeout=5)
    copied = time.monotonic()
    assert d.restore(backup, restored, timeout=5)["send_quarantined"] is True
    reopened = time.monotonic()
    timings.append({
        "control": index + 1, "backup_ms": round((copied - began) * 1000, 3),
        "restore_ms": round((reopened - copied) * 1000, 3)
    })
    assert d.verify(restored, timeout=5)["send_quarantined"] is True
    try:
        d.send(restored, saved["selected"])
    except ValueError as error:
        assert str(error) == "send_quarantined"
    else:
        raise AssertionError("restored confirmed replay allowed")
old = data / "old-restored.sqlite3"
d.restore(data / "empty-backup.sqlite3", old, timeout=5)
review = d.review(
    old,
    data / "watch.sqlite3",
    data / "journal.sqlite3",
    data / "outbox.sqlite3",
    manifest,
    saved["alerts"][3],
    "local-preview",
    timeout=5,
)["review"]
consent = {"acknowledgement": review["acknowledgement"]}
for key in (
    "signal_id",
    "revision",
    "message_sha256",
    "evidence_sha256",
    "route_sha256",
    "binding_sha256",
):
    consent["expected_" + key] = review[key]
unknown = d.prepare(
    old,
    data / "watch.sqlite3",
    data / "journal.sqlite3",
    data / "outbox.sqlite3",
    manifest,
    saved["alerts"][3],
    "local-preview",
    timeout=5,
    **consent,
)["delivery"]["delivery_id"]
for did in (unknown, saved["selected"]):
    try:
        d.send(old, did)
    except ValueError as error:
        assert str(error) == "send_quarantined"
    else:
        raise AssertionError("unknown post-backup signal sent")
print(
    "recompute, quiesced recovery, three full backup/restore controls, "
    "global unknown-row quarantine"
)
print(json.dumps({"recovery_controls_ms": timings, "local_budget_seconds": 5}))
"""

INSPECT = """
import hashlib, json, os, sqlite3

data = Path(sys.argv[1])
saved = json.loads((data / "selection.json").read_text())
for name, digest in saved["sources"].items():
    assert hashlib.sha256((data / (name + ".sqlite3")).read_bytes()).hexdigest() == digest
p = data / "ledger.sqlite3"
with sqlite3.connect(p.as_uri() + "?mode=ro", uri=True) as db:
    assert db.execute("PRAGMA application_id").fetchone()[0] == 0x434D545A
    assert db.execute("PRAGMA user_version").fetchone()[0] == 1
    assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert db.execute("SELECT count(*) FROM wtd_claims").fetchone()[0] == 2
    assert db.execute("SELECT count(*) FROM wtd_results").fetchone()[0] == 2
    assert db.execute("SELECT state FROM wtd_state ORDER BY state").fetchall() == [
        ("confirmed",),
        ("uncertain",),
    ]
assert os.name == "nt" or p.stat().st_mode & 0o077 == 0
assert sys.argv[2] == "installed" or os.getuid() == 10001
print("sources byte-identical; receipt/attempt history durable; private nonroot files")
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("installed", "docker", "compose"), required=True)
    parser.add_argument("--executable", default="cmt")
    parser.add_argument("--image", default="cmt-p8d-smoke")
    parser.add_argument("--platform", default="linux/amd64")
    parser.add_argument("--fixtures", type=Path, required=True)
    args = parser.parse_args()
    fixtures = args.fixtures.resolve()
    environment = {
        key: os.environ[key]
        for key in (
            "PATH",
            "HOME",
            "USERPROFILE",
            "SYSTEMROOT",
            "WINDIR",
            "TEMP",
            "TMP",
            "APPDATA",
            "LOCALAPPDATA",
            "DOCKER_HOST",
            "DOCKER_CONTEXT",
            "DOCKER_CERT_PATH",
            "DOCKER_TLS_VERIFY",
        )
        if key in os.environ
    }
    volume = "cmt-p8d-smoke-" + uuid4().hex
    created = False
    with tempfile.TemporaryDirectory(prefix="cmt-p8d-smoke-") as outside:
        if args.mode == "installed":
            python, data, source = [sys.executable, "-I"], outside, str(fixtures)
        else:
            subprocess.run(
                ["docker", "volume", "create", volume], check=True, capture_output=True, timeout=30
            )
            created = True
            data, source = "/data", "/fixtures"
            if args.mode == "docker":
                python = [
                    "docker",
                    "run",
                    "--rm",
                    "--network",
                    "none",
                    "--platform",
                    args.platform,
                    "--mount",
                    f"type=volume,source={volume},target=/data",
                    "--mount",
                    f"type=bind,source={fixtures},target=/fixtures,readonly",
                    "--entrypoint",
                    "python",
                    args.image,
                    "-I",
                ]
            else:
                environment["CMT_PERSISTENCE_VOLUME"] = volume
                python = [
                    "docker",
                    "compose",
                    "run",
                    "--rm",
                    "-T",
                    "--entrypoint",
                    "python",
                    "scoped",
                    "-I",
                ]
        try:

            def run(
                code: str, *values: str, offline: bool = True
            ) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [*python, "-c", OFFLINE + (NO_TELEGRAM if offline else "") + code, *values],
                    capture_output=True,
                    text=True,
                    env=environment,
                    cwd=outside if args.mode == "installed" else None,
                    timeout=180,
                    check=True,
                )

            run(SEED, source, data)
            fake = json.loads(run(FAKE_SEND, data, "confirm", source, offline=False).stdout)
            assert fake["fake_only"] and fake["send_attempts"] == 1
            replay = run(REPLAY, data)
            payload, event = json.loads(replay.stdout), json.loads(replay.stderr)
            assert payload["result"] == "replay" and payload["delivery"]["attempt_count"] == 1
            assert event["event"] == "watchlist.telegram_delivery.completed"
            run(FAKE_SEND, data, "crash", source, offline=False)
            recovery = run(RECOVER, data, source)
            metrics = json.loads(recovery.stdout.splitlines()[-1])
            assert len(metrics["recovery_controls_ms"]) == 3
            print(json.dumps({"mode": args.mode, "platform": args.platform, **metrics}))
            run(INSPECT, data, args.mode)
            print(
                "watchlist Telegram delivery smoke PASS; five checkpoints/four signals; "
                "exact fake send/receipt; tokenless/import-denied/network-denied "
                "persistent replay; "
                "recompute/quiesced recovery/three backup-restore controls/"
                "global quarantine; sources intact"
            )
        finally:
            if created:
                subprocess.run(
                    ["docker", "volume", "rm", volume], check=True, capture_output=True, timeout=30
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
