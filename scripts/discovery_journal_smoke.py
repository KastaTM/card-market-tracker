"""Seventh offline harness: durable journal across independent installed processes."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from uuid import UUID, uuid4

from multi_revision_metadata_smoke import SEED
from scoped_capture_discovery_smoke import INSPECT, OFFLINE


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("installed", "docker", "compose"), required=True)
    parser.add_argument("--executable", default="cmt")
    parser.add_argument("--image", default="cmt-p4c-smoke")
    parser.add_argument("--platform", default="linux/amd64")
    parser.add_argument("--fixtures", type=Path, required=True)
    args = parser.parse_args()
    fixtures = args.fixtures.resolve()
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    volume = "cmt-p4c-smoke-" + uuid4().hex
    created = False
    with tempfile.TemporaryDirectory(prefix="cmt-p4c-smoke-") as outside:
        if args.mode == "installed":
            python = [sys.executable, "-I"]
            cli = [
                *python,
                "-c",
                OFFLINE
                + "\nfrom card_market_tracker.cli import main\nsys.exit(main(sys.argv[1:]))",
            ]
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
                cli = [*base, args.image]
                python = [*base, "--entrypoint", "python", args.image, "-I"]
            else:
                environment["CMT_PERSISTENCE_VOLUME"] = volume
                base = ["docker", "compose", "run", "--rm", "-T"]
                cli = [*base, "scoped"]
                python = [*base, "--entrypoint", "python", "scoped", "-I"]
        try:

            def run(command: list[str]) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    env=environment,
                    cwd=outside if args.mode == "installed" else None,
                    timeout=120,
                )

            def execute(code: str, *values: str) -> str:
                completed = run([*python, "-c", OFFLINE + "\n" + code, *values])
                assert completed.returncode == 0, (completed.stdout, completed.stderr)
                return completed.stdout

            def call(
                operation: str, *values: str, target: str | None = None, expected: int = 0
            ) -> dict:
                completed = run(
                    [
                        *cli,
                        "discovery-journal",
                        operation,
                        "--journal-db",
                        target or journal,
                        *values,
                    ]
                )
                assert completed.returncode == expected, (
                    operation,
                    completed.stdout,
                    completed.stderr,
                )
                payload = json.loads(completed.stdout)
                logs = [
                    json.loads(line)
                    for line in completed.stderr.splitlines()
                    if line.startswith("{")
                ]
                assert len(logs) == 1
                log = logs[0]
                UUID(log["run_id"])
                assert (
                    log["event"] == "discovery.journal.completed"
                    and log["result"] == payload["result"]
                )
                assert log["duration_ms"] >= 0 and log["operation"].startswith("discovery_journal_")
                for forbidden in (data, source, "tcgdex", "offline-demo", "swsh3", "22222222-2222"):
                    assert forbidden not in completed.stderr
                return payload

            print(execute(SEED, source, data).strip())
            execute(
                "import json\np=Path(sys.argv[1]); r=json.loads((p/'synthetic.json').read_text()); "
                "r['history']=r['history'][1:]; (p/'window.json').write_text(json.dumps(r)); "
                "r['history']=[]; (p/'baseline.json').write_text(json.dumps(r))",
                data,
            )
            if args.mode != "installed":
                print(
                    execute(
                        "import os,stat,sqlite3\ns=os.stat('/data')\n"
                        "assert os.getuid()==10001 and s.st_uid==10001 and s.st_gid==10001\n"
                        "assert stat.S_IMODE(s.st_mode)==0o700\n"
                        "print(sys.version.split()[0],sqlite3.sqlite_version,'uid=10001')"
                    ).strip()
                )
            captures, journal = f"{data}/multi.sqlite3", f"{data}/journal.sqlite3"
            original = json.loads(execute(INSPECT, captures))
            call("init")

            def record(case: str) -> dict:
                return call("record", "--captures-db", captures, "--request", f"{data}/{case}.json")

            first = record("synthetic")
            assert first["result"] == "inserted" and first["counts"]["occurrences"] == 2
            cid = first["comparison_id"]
            retained = call("get", "--comparison-id", cid)
            # Independent digest recipe, deliberately outside the product helper.
            import hashlib

            semantic = {
                "journal_version": 1,
                "request": retained["request"],
                "result": retained["comparison"],
            }
            encoded = json.dumps(
                semantic, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
            )
            assert hashlib.sha256(encoded.encode("ascii")).hexdigest() == retained["content_sha256"]
            replay = record("permuted")
            assert (
                replay["result"] == "replay"
                and replay["first_recorded_at"] == first["first_recorded_at"]
            )
            second = record("window")
            assert second["comparison_id"] != cid
            other = call("get", "--comparison-id", second["comparison_id"])
            event = retained["comparison"]["events"][0]
            assert event["event_id"] == other["comparison"]["events"][0]["event_id"]
            assert event["evidence"] != other["comparison"]["events"][0]["evidence"]
            page = call("event-occurrences", "--event-id", event["event_id"], "--limit", "1")
            assert len(page["items"]) == 1 and page["next_cursor"]
            following = call(
                "event-occurrences",
                "--event-id",
                event["event_id"],
                "--limit",
                "1",
                "--cursor",
                page["next_cursor"],
            )
            assert len(following["items"]) == 1 and following["next_cursor"] is None
            baseline = record("baseline")
            assert (
                call("get", "--comparison-id", baseline["comparison_id"])["comparison"]["result"]
                == "baseline"
            )
            for kind in ("set", "card"):
                for language in ("es", "en"):
                    real = record(f"{kind}-{language}")
                    pair = call("get", "--comparison-id", real["comparison_id"])["comparison"]
                    assert pair["result"] == "no_discoveries" and pair["events"] == []
                    call(
                        "recompute",
                        "--captures-db",
                        captures,
                        "--comparison-id",
                        real["comparison_id"],
                    )
            assert len(call("list")["items"]) == 7
            verified = call("verify")
            assert verified["level"] == "local" and verified["counts"] == {
                "comparisons": 7,
                "occurrences": 4,
            }
            backup, restored = f"{data}/backup.sqlite3", f"{data}/restored.sqlite3"
            # Explicit maximum for whole-journal copy/verification under emulation.
            call("backup", "--destination", backup, "--timeout", "5")
            call("restore", "--destination", restored, "--timeout", "5", target=backup)
            assert call("get", "--comparison-id", cid, target=restored) == retained
            call("verify", target=restored)
            call("recompute", "--captures-db", captures, "--comparison-id", cid, target=restored)
            assert json.loads(execute(INSPECT, captures)) == original
            assert call("list", target=f"{data}/missing.sqlite3", expected=1)["result"] == "error"
        finally:
            if created:
                subprocess.run(
                    ["docker", "volume", "rm", volume], check=True, capture_output=True, timeout=30
                )
    print(
        f"discovery journal {args.mode} smoke PASS; seven comparisons, repeated event windows, "
        "replay, local verify, source recompute, recovery; separate offline processes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
