"""Twelfth offline harness: original-backed Watchlist previews and recovery."""

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

SEED = """
import json
fixtures, data = map(Path, sys.argv[1:])
base = json.loads((fixtures/'synthetic_watchlist_current.json').read_text())
for index, stock in enumerate(('OUT_OF_STOCK','AVAILABLE','AVAILABLE','OUT_OF_STOCK','AVAILABLE')):
    sample = dict(base, sample_id='journal-smoke-'+str(index), stock=stock,
                  observed_at='2026-10-23T12:0'+str(index)+':00Z')
    (data/('sample-'+str(index)+'.json')).write_text(json.dumps(sample),encoding='utf-8')
config = json.loads((fixtures/'synthetic_watchlist_config.json').read_text())
config['target_price_minor'] += 100
(data/'rw01-config.json').write_text(json.dumps(config),encoding='utf-8')
print('seeded synthetic checkpoints')
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("installed", "docker", "compose"), required=True)
    parser.add_argument("--executable", default="cmt")
    parser.add_argument("--image", default="cmt-p8c-smoke")
    parser.add_argument("--platform", default="linux/amd64")
    parser.add_argument("--fixtures", type=Path, required=True)
    args = parser.parse_args()
    fixtures = args.fixtures.resolve()
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("CMT_TELEGRAM_BOT_TOKEN", None)
    volume = "cmt-p8c-smoke-" + uuid4().hex
    created = False
    with tempfile.TemporaryDirectory(prefix="cmt-p8c-smoke-") as outside:
        if args.mode == "installed":
            python = [sys.executable, "-I"]
            data, source = outside, str(fixtures)
        else:
            subprocess.run(
                ["docker", "volume", "create", volume],
                check=True,
                capture_output=True,
                timeout=30,
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

            def run(command, expected=0):
                completed = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    env=environment,
                    cwd=outside if args.mode == "installed" else None,
                    timeout=120,
                )
                assert completed.returncode == expected, (completed.stdout, completed.stderr)
                return completed

            run([*python, "-c", OFFLINE + SEED, source, data])
            cli = [
                *python,
                "-c",
                OFFLINE + "\nfrom card_market_tracker.cli import main\n"
                "sys.exit(main(sys.argv[1:]))",
            ]
            watchlist, journal = f"{data}/watchlist.sqlite3", f"{data}/journal.sqlite3"
            outbox = f"{data}/outbox.sqlite3"
            manifest = f"{source}/synthetic_manifest.json"

            def call(group, operation, *flags, target=None, expected=0):
                database, db_flag = {
                    "watchlist": (watchlist, "--watchlist-db"),
                    "watchlist-journal": (journal, "--journal-db"),
                    "watchlist-alert-outbox": (outbox, "--outbox-db"),
                }[group]
                completed = run(
                    [
                        *cli,
                        group,
                        operation,
                        db_flag,
                        target or database,
                        "--timeout",
                        "5",
                        *map(str, flags),
                    ],
                    expected=expected,
                )
                payload, log = json.loads(completed.stdout), json.loads(completed.stderr)
                assert payload["version"] == 1
                event = {
                    "watchlist": "watchlist.completed",
                    "watchlist-journal": "watchlist.journal.completed",
                    "watchlist-alert-outbox": "watchlist.alert_outbox.completed",
                }[group]
                assert log["event"] == event
                assert all(
                    key not in log for key in ("sample_id", "watch_id", "target_price_minor")
                )
                return payload

            call("watchlist", "init")
            entry = call(
                "watchlist",
                "add",
                "--manifest",
                manifest,
                "--cmt-id",
                "541b9d13-9669-4973-8413-397bea14c045",
                "--input",
                f"{source}/synthetic_watchlist_config.json",
                "--request-token",
                "journal-smoke",
            )["entry"]
            call("watchlist-journal", "init")

            def fingerprint(path):
                code = (
                    "\nimport hashlib\n"
                    "print(hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest())"
                )
                return run([*python, "-c", OFFLINE + code, path]).stdout

            original = fingerprint(watchlist)

            def record(index):
                flags = [
                    "--watchlist-db",
                    watchlist,
                    "--manifest",
                    manifest,
                    "--watch-id",
                    entry["watch_id"],
                    "--revision",
                    "1",
                    "--sample",
                    f"{data}/sample-{index}.json",
                    "--as-of",
                    f"2026-10-23T12:0{index}:00Z",
                ]
                if index:
                    flags += ["--previous", f"{data}/sample-{index - 1}.json"]
                return call("watchlist-journal", "record", *flags)

            first = record(0)
            assert first["signals_count"] == 0
            second = record(1)
            assert second["signals_count"] == 2
            assert record(2)["signals_count"] == 0
            assert record(3)["signals_count"] == 0
            assert record(4)["signals_count"] == 2
            before = call("watchlist-journal", "verify")
            replay = record(0)
            assert (
                replay["result"] == "replayed" and replay["persisted_at"] == first["persisted_at"]
            )
            assert call("watchlist-journal", "verify") == before
            records = call("watchlist-journal", "list", "--limit", "1")
            assert records["next_cursor"]
            call("watchlist-journal", "list", "--cursor", records["next_cursor"])
            signals = call("watchlist-journal", "signal-list")
            assert len(signals["signals"]) == 4
            call("watchlist-journal", "signal-get", "--signal-id", second["signal_ids"][0])
            call("watchlist-journal", "get", "--evaluation-id", second["evaluation_id"])
            call(
                "watchlist-journal",
                "recompute",
                "--evaluation-id",
                second["evaluation_id"],
                "--watchlist-db",
                watchlist,
                "--manifest",
                manifest,
            )
            journal_original = fingerprint(journal)
            call("watchlist-alert-outbox", "init")
            prepared = []
            for signal in signals["signals"]:
                prepared.append(
                    call(
                        "watchlist-alert-outbox",
                        "enqueue",
                        "--watchlist-db",
                        watchlist,
                        "--journal-db",
                        journal,
                        "--manifest",
                        manifest,
                        "--signal-id",
                        signal["signal_id"],
                        "--destination-key",
                        "local-preview",
                    )
                )
            assert len(prepared) == 4
            selected = prepared[0]["alert_id"]
            frozen = call("watchlist-alert-outbox", "get", "--alert-id", selected)
            original_outbox = fingerprint(outbox)
            replay = call(
                "watchlist-alert-outbox",
                "enqueue",
                "--watchlist-db",
                watchlist,
                "--journal-db",
                journal,
                "--manifest",
                manifest,
                "--signal-id",
                prepared[0]["signal_id"],
                "--destination-key",
                "local-preview",
            )
            assert replay["result"] == "replayed"
            assert fingerprint(outbox) == original_outbox
            preview = call("watchlist-alert-outbox", "preview", "--alert-id", selected)
            assert preview["message_text"].startswith("SYNTHETIC ")
            assert preview["message_text"] == frozen["alert"]["message_text"]
            evidence = call("watchlist-alert-outbox", "evidence-get", "--alert-id", selected)
            assert evidence["evidence"]["signal"]["signal_id"] == prepared[0]["signal_id"]
            page = call("watchlist-alert-outbox", "list", "--limit", "1")
            assert len(page["items"]) == 1 and page["next_cursor"]
            assert call("watchlist-alert-outbox", "list", "--cursor", page["next_cursor"])["items"]
            assert call("watchlist-alert-outbox", "verify")["counts"] == {
                "alerts": 4,
                "evidence": 4,
            }
            call(
                "watchlist-alert-outbox",
                "recompute",
                "--alert-id",
                selected,
                "--watchlist-db",
                watchlist,
                "--journal-db",
                journal,
                "--manifest",
                manifest,
            )
            # RW-01: a second genuine source pair shares the historical key but
            # has incompatible preferences. Different alias/IDs grant no exception.
            conflicting_watch = f"{data}/rw01-watchlist.sqlite3"
            conflicting_journal = f"{data}/rw01-journal.sqlite3"
            call("watchlist", "init", target=conflicting_watch)
            conflicting_entry = call(
                "watchlist",
                "add",
                "--manifest",
                manifest,
                "--cmt-id",
                entry["cmt_id"],
                "--input",
                f"{data}/rw01-config.json",
                "--request-token",
                "rw01-independent",
                target=conflicting_watch,
            )["entry"]
            assert conflicting_entry["watch_id"] == entry["watch_id"]
            assert conflicting_entry["revision"] == entry["revision"] == 1
            assert conflicting_entry != entry
            call("watchlist-journal", "init", target=conflicting_journal)
            for index in (0, 1):
                flags = [
                    "--watchlist-db",
                    conflicting_watch,
                    "--manifest",
                    manifest,
                    "--watch-id",
                    conflicting_entry["watch_id"],
                    "--revision",
                    "1",
                    "--sample",
                    f"{data}/sample-{index}.json",
                    "--as-of",
                    f"2026-10-23T12:0{index}:00Z",
                ]
                if index:
                    flags += ["--previous", f"{data}/sample-0.json"]
                conflicting_point = call(
                    "watchlist-journal",
                    "record",
                    *flags,
                    target=conflicting_journal,
                )
            conflicting_signal = conflicting_point["signal_ids"][0]
            assert conflicting_signal not in {item["signal_id"] for item in prepared}
            conflicting_bytes = (fingerprint(conflicting_watch), fingerprint(conflicting_journal))
            rejected = call(
                "watchlist-alert-outbox",
                "enqueue",
                "--watchlist-db",
                conflicting_watch,
                "--journal-db",
                conflicting_journal,
                "--manifest",
                manifest,
                "--signal-id",
                conflicting_signal,
                "--destination-key",
                "rw01-other",
                expected=2,
            )
            assert rejected["result"] == "error"
            assert rejected["error_category"] == "identity_conflict"
            assert fingerprint(outbox) == original_outbox
            assert call("watchlist-alert-outbox", "get", "--alert-id", selected) == frozen
            assert (
                call("watchlist-alert-outbox", "evidence-get", "--alert-id", selected) == evidence
            )
            assert call("watchlist-alert-outbox", "verify")["counts"] == {
                "alerts": 4,
                "evidence": 4,
            }
            assert conflicting_bytes == (
                fingerprint(conflicting_watch),
                fingerprint(conflicting_journal),
            )
            backup, restored = f"{data}/backup.sqlite3", f"{data}/restored.sqlite3"
            call("watchlist-alert-outbox", "backup", "--destination", backup)
            call("watchlist-alert-outbox", "restore", "--destination", restored, target=backup)
            assert call("watchlist-alert-outbox", "verify", target=restored)["counts"] == {
                "alerts": 4,
                "evidence": 4,
            }
            assert (
                call("watchlist-alert-outbox", "get", "--alert-id", selected, target=restored)
                == frozen
            )
            assert fingerprint(watchlist) == original
            assert fingerprint(journal) == journal_original
            assert fingerprint(outbox) == original_outbox
            inspection = """
import os,sqlite3
p=Path(sys.argv[1]); c=sqlite3.connect(p.as_uri()+'?mode=ro',uri=True)
assert len(c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())==3
assert c.execute('PRAGMA application_id').fetchone()[0]==0x434d5459
assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
assert os.name=='nt' or (p.stat().st_mode & 0o077)==0
assert sys.argv[2]=='installed' or os.getuid()==10001
"""
            run([*python, "-c", OFFLINE + inspection, restored, args.mode])
            print(
                "watchlist alert outbox smoke PASS; five checkpoints, four signals, "
                "four previews, replay, recompute, no sockets, exclusive recovery; "
                "RW-01 incompatible originals rejected without mutation"
            )
        finally:
            if created:
                subprocess.run(
                    ["docker", "volume", "rm", volume], check=True, capture_output=True, timeout=30
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
