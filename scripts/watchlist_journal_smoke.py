"""Eleventh offline harness: installed processes, journal episodes and recovery."""

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
print('seeded synthetic checkpoints')
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("installed", "docker", "compose"), required=True)
    parser.add_argument("--executable", default="cmt")
    parser.add_argument("--image", default="cmt-p5b-smoke")
    parser.add_argument("--platform", default="linux/amd64")
    parser.add_argument("--fixtures", type=Path, required=True)
    args = parser.parse_args()
    fixtures = args.fixtures.resolve()
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("CMT_TELEGRAM_BOT_TOKEN", None)
    volume = "cmt-p5b-smoke-" + uuid4().hex
    created = False
    with tempfile.TemporaryDirectory(prefix="cmt-p5b-smoke-") as outside:
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

            def run(command):
                completed = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    env=environment,
                    cwd=outside if args.mode == "installed" else None,
                    timeout=120,
                )
                assert completed.returncode == 0, (completed.stdout, completed.stderr)
                return completed

            run([*python, "-c", OFFLINE + SEED, source, data])
            cli = [
                *python,
                "-c",
                OFFLINE + "\nfrom card_market_tracker.cli import main\n"
                "sys.exit(main(sys.argv[1:]))",
            ]
            watchlist, journal = f"{data}/watchlist.sqlite3", f"{data}/journal.sqlite3"
            manifest = f"{source}/synthetic_manifest.json"

            def call(group, operation, *flags, target=None):
                database = journal if group == "watchlist-journal" else watchlist
                db_flag = "--journal-db" if group == "watchlist-journal" else "--watchlist-db"
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
                    ]
                )
                payload, log = json.loads(completed.stdout), json.loads(completed.stderr)
                assert payload["version"] == 1
                event = (
                    "watchlist.journal.completed"
                    if group == "watchlist-journal"
                    else "watchlist.completed"
                )
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
            stored = call("watchlist-journal", "get", "--evaluation-id", second["evaluation_id"])
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
            backup, restored = f"{data}/backup.sqlite3", f"{data}/restored.sqlite3"
            call("watchlist-journal", "backup", "--destination", backup)
            call("watchlist-journal", "restore", "--destination", restored, target=backup)
            call("watchlist-journal", "verify", target=restored)
            assert (
                call(
                    "watchlist-journal",
                    "get",
                    "--evaluation-id",
                    second["evaluation_id"],
                    target=restored,
                )
                == stored
            )
            assert fingerprint(watchlist) == original
            inspection = """
import os,sqlite3
p=Path(sys.argv[1]); c=sqlite3.connect(p.as_uri()+'?mode=ro',uri=True)
assert len(c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())==4
assert c.execute('PRAGMA application_id').fetchone()[0]==0x434d5451
assert os.name=='nt' or (p.stat().st_mode & 0o077)==0
assert sys.argv[2]=='installed' or os.getuid()==10001
"""
            run([*python, "-c", OFFLINE + inspection, restored, args.mode])
            print(
                "watchlist journal smoke PASS; two episodes, 4 signals, "
                "old replay, no sockets, recovery"
            )
        finally:
            if created:
                subprocess.run(
                    ["docker", "volume", "rm", volume], check=True, capture_output=True, timeout=30
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
