"""Tenth offline harness: durable preferences and ephemeral synthetic evaluation."""

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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("installed", "docker", "compose"), required=True)
    parser.add_argument("--executable", default="cmt")
    parser.add_argument("--image", default="cmt-p5a-smoke")
    parser.add_argument("--platform", default="linux/amd64")
    parser.add_argument("--fixtures", type=Path, required=True)
    args = parser.parse_args()
    fixtures = args.fixtures.resolve()
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("CMT_TELEGRAM_BOT_TOKEN", None)
    volume = "cmt-p5a-smoke-" + uuid4().hex
    created = False
    with tempfile.TemporaryDirectory(prefix="cmt-p5a-smoke-") as outside:
        if args.mode == "installed":
            python = [sys.executable, "-I"]
            data, source = outside, str(fixtures)
        else:
            subprocess.run(
                ["docker", "volume", "create", volume], check=True, capture_output=True, timeout=30
            )
            created = True
            data, source = "/data", "/fixtures"
            if args.mode == "docker":
                base = [
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
                ]
                python = [*base, "--entrypoint", "python", args.image, "-I"]
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
            cli = [
                *python,
                "-c",
                OFFLINE + "\nfrom card_market_tracker.cli import main\n"
                "sys.exit(main(sys.argv[1:]))",
            ]
            db = f"{data}/watchlist.sqlite3"
            manifest = f"{source}/synthetic_manifest.json"

            def run(command, code=0):
                completed = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    env=environment,
                    cwd=outside,
                    timeout=120,
                )
                assert completed.returncode == code, (completed.stdout, completed.stderr)
                return completed

            def call(operation, *values, code=0, target=db):
                completed = run(
                    [
                        *cli,
                        "watchlist",
                        operation,
                        "--watchlist-db",
                        target,
                        "--timeout",
                        "5",
                        *map(str, values),
                    ],
                    code,
                )
                payload = json.loads(completed.stdout)
                log = json.loads(completed.stderr)
                assert payload["version"] == 1 and log["event"] == "watchlist.completed"
                assert log["operation"] == "watchlist_" + operation
                assert all(key not in log for key in ("cmt_id", "watch_id", "target_price_minor"))
                return payload

            call("init")
            add = (
                "--manifest",
                manifest,
                "--cmt-id",
                "541b9d13-9669-4973-8413-397bea14c045",
                "--input",
                f"{source}/synthetic_watchlist_config.json",
                "--request-token",
                "add",
            )
            first = call("add", *add)
            watch = first["entry"]["watch_id"]
            assert first["entry"]["revision"] == 1
            mutation = ("--manifest", manifest, "--watch-id", watch)
            edit = (
                *mutation,
                "--input",
                f"{source}/synthetic_watchlist_config.json",
                "--expected-revision",
                "1",
                "--request-token",
                "edit",
            )
            assert call("update", *edit)["entry"]["revision"] == 2
            assert call("add", *add)["replayed"] is True
            assert call("update", *edit)["replayed"] is True
            stale = call("update", *edit[:-1], "stale", code=2)
            assert stale["error_category"] == "revision_conflict"
            conflict = call(
                "disable", *mutation, "--expected-revision", "2", "--request-token", "edit", code=2
            )
            assert conflict["error_category"] == "replay_conflict"

            def snapshot(target):
                code = (
                    "import hashlib\np=Path(sys.argv[1]);"
                    "print(hashlib.sha256(p.read_bytes()).hexdigest())"
                )
                return run([*python, "-c", OFFLINE + "\n" + code, target]).stdout

            before = snapshot(db)
            evaluation = (
                *mutation,
                "--revision",
                "2",
                "--as-of",
                "2026-10-23T12:00:00Z",
                "--sample",
                f"{source}/synthetic_watchlist_current.json",
                "--previous",
                f"{source}/synthetic_watchlist_previous.json",
            )
            result = call("evaluate", *evaluation)
            assert result["result"] == "MATCH"
            assert all(rule["result"] == "MATCH" for rule in result["rules"])
            assert call("evaluate", *evaluation) == result and snapshot(db) == before
            assert call("get", "--watch-id", watch)["entry"]["revision"] == 2
            disabled = call(
                "disable", *mutation, "--expected-revision", "2", "--request-token", "disable"
            )
            assert disabled["entry"]["enabled"] is False
            assert call("evaluate", *evaluation[:5], "3", *evaluation[6:])["result"] == "SKIPPED"
            enabled = call(
                "enable", *mutation, "--expected-revision", "3", "--request-token", "enable"
            )
            assert enabled["entry"]["watch_id"] == watch
            assert call("list", "--limit", "1")["entries"][0]["watch_id"] == watch
            page = call("history", "--watch-id", watch, "--limit", "1")
            assert page["next_cursor"] is not None
            call("history", "--watch-id", watch, "--cursor", page["next_cursor"])
            backup, restored = f"{data}/backup.sqlite3", f"{data}/restored.sqlite3"
            call("backup", "--destination", backup)
            call("restore", "--destination", restored, target=backup)
            call("verify", target=restored)
            assert call("get", "--watch-id", watch, target=restored)["entry"] == enabled["entry"]
            assert (
                call("history", "--watch-id", watch, target=restored)["entries"]
                == call("history", "--watch-id", watch)["entries"]
            )
            inspect = (
                "import os,sqlite3\nc=sqlite3.connect(sys.argv[1]);"
                "assert len(c.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')"
                ".fetchall())==4\n"
                "assert os.name=='nt' or (os.stat(sys.argv[1]).st_mode & 0o077)==0\n"
                "assert sys.argv[2]=='installed' or os.getuid()==10001"
            )
            run([*python, "-c", OFFLINE + "\n" + inspect, restored, args.mode])
            print(
                "watchlist smoke PASS; synthetic-only, no sockets, separate processes and recovery"
            )
        finally:
            if created:
                subprocess.run(
                    ["docker", "volume", "rm", volume], check=True, capture_output=True, timeout=30
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
