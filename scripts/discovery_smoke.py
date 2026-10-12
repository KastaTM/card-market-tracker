"""Assert offline Discovery after distinct installed/container persistence processes."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from uuid import UUID, uuid4


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("installed", "docker", "compose"), required=True)
    parser.add_argument("--executable", default="cmt")
    parser.add_argument("--image", default="cmt-p4a-smoke")
    parser.add_argument("--platform", default="linux/amd64")
    parser.add_argument("--fixtures", type=Path, required=True)
    args = parser.parse_args()
    fixtures = args.fixtures.resolve()
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    volume = f"cmt-p4a-smoke-{uuid4().hex}"
    created_volume = False
    with tempfile.TemporaryDirectory(prefix="cmt-p4a-smoke-") as outside:
        if args.mode == "installed":
            prefix = [args.executable]
            inspect_prefix = [sys.executable]
            data_path, fixture_path = outside, str(fixtures)
        else:
            subprocess.run(
                ["docker", "volume", "create", volume], check=True, capture_output=True, timeout=30
            )
            created_volume = True
            data_path, fixture_path = "/data", "/fixtures"
            mounts = [
                "--mount",
                f"type=volume,source={volume},target=/data",
                "--mount",
                f"type=bind,source={fixtures},target=/fixtures,readonly",
            ]
            if args.mode == "docker":
                base = ["docker", "run", "--rm", "--network", "none", "--platform", args.platform]
                prefix = [*base, *mounts, args.image]
                inspect_prefix = [*base, *mounts, "--entrypoint", "python", args.image]
            else:
                environment["CMT_PERSISTENCE_VOLUME"] = volume
                prefix = ["docker", "compose", "run", "--rm", "-T", "discovery"]
                inspect_prefix = [
                    "docker",
                    "compose",
                    "run",
                    "--rm",
                    "-T",
                    "--entrypoint",
                    "python",
                    "discovery",
                ]
        try:

            def call(command: list[str], expected: int = 0) -> dict:
                completed = subprocess.run(
                    [*prefix, *command],
                    cwd=outside if args.mode == "installed" else None,
                    capture_output=True,
                    text=True,
                    env=environment,
                    timeout=120,
                )
                assert completed.returncode == expected, (
                    f"discovery {args.mode} {command[0]} exit {completed.returncode}, "
                    f"expected {expected}"
                )
                result = json.loads(completed.stdout)
                event_name = (
                    "discovery.completed" if command[0] == "discover" else "persistence.completed"
                )
                events = [
                    json.loads(line)
                    for line in completed.stderr.splitlines()
                    if line.strip().startswith("{")
                ]
                events = [row for row in events if row.get("event") == event_name]
                assert len(events) == 1
                event = events[0]
                UUID(event["run_id"])
                assert event["duration_ms"] >= 0 and event["result"] == result["result"]
                assert fixture_path not in completed.stderr and data_path not in completed.stderr
                if command[0] == "discover":
                    if result["result"] == "error":
                        assert result["counts"] is None and result["events"] == []
                        assert "event_count" not in event
                    else:
                        assert event["event_count"] == len(result["events"])
                        assert event["batch_count"] == result["counts"]["batches"]
                        assert (
                            event["discovery_observation_count"] == result["counts"]["observations"]
                        )
                    for forbidden in ("11111111-1111", "22222222-2222", "tcgdex", "new-alias"):
                        assert forbidden not in completed.stderr
                return result

            database = f"{data_path}/discovery.sqlite3"
            for case, expected in (("history", 0), ("empty", 0), ("current", 3), ("rejected", 3)):
                call(
                    [
                        "persist",
                        "--db",
                        database,
                        "--input",
                        f"{fixture_path}/synthetic_discovery_{case}.json",
                        "--manifest",
                        f"{fixture_path}/synthetic_discovery_manifest.json",
                    ],
                    expected,
                )

            def inspect(target: str) -> dict:
                # Logical content, schema objects and versions, not just row counts.
                script = (
                    "import json,os,sys,sqlite3; from pathlib import Path; "
                    "c=sqlite3.connect(Path(sys.argv[1]).as_uri()+'?mode=ro',uri=True); "
                    "c.execute('PRAGMA query_only=ON'); c.execute('BEGIN'); "
                    "p={'inventory':c.execute('SELECT type,name,tbl_name,sql FROM sqlite_schema "
                    "ORDER BY type,name').fetchall(),'versions':"
                    "[c.execute('PRAGMA application_id').fetchone()[0],"
                    "c.execute('PRAGMA user_version').fetchone()[0]],"
                    "'content':{t:c.execute('SELECT * FROM '+t+' ORDER BY 1,2').fetchall() "
                    "for t in ('storage_metadata','entities','batches','records')}}; "
                    "c.execute('ROLLBACK'); c.close(); print(json.dumps(p,sort_keys=True))"
                )
                completed = subprocess.run(
                    [*inspect_prefix, "-c", script, target],
                    capture_output=True,
                    text=True,
                    env=environment,
                    timeout=120,
                )
                assert completed.returncode == 0, "discovery logical inspection failed"
                return json.loads(completed.stdout)

            if args.mode != "installed":
                runtime = subprocess.run(
                    [
                        *inspect_prefix,
                        "-c",
                        "import os,stat,sys,sqlite3; s=os.stat('/data'); "
                        "assert os.getuid()==10001 and s.st_uid==10001 and s.st_gid==10001; "
                        "assert stat.S_IMODE(s.st_mode)==0o700; "
                        "print(sys.version.split()[0],sqlite3.sqlite_version,"
                        "'uid=10001 data=0700')",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    env=environment,
                    timeout=120,
                )
                print(f"discovery {args.mode} runtime: {runtime.stdout.strip()}")
            before = inspect(database)

            def discover(case: str, expected: int = 0, target: str = database) -> dict:
                filename = "request" if case == "main" else f"{case}_request"
                return call(
                    [
                        "discover",
                        "--db",
                        target,
                        "--request",
                        f"{fixture_path}/synthetic_discovery_{filename}.json",
                    ],
                    expected,
                )

            result = discover("main")
            assert result["result"] == "discoveries" and len(result["events"]) == 2
            accepted, candidate = [
                next(e for e in result["events"] if e["status"] == status)
                for status in ("accepted", "candidate")
            ]
            assert accepted["type"] == "SET_REFERENCE_FIRST_OBSERVED"
            assert accepted["cmt_id"] is not None and accepted["reference"]["kind"] == "set"
            assert candidate["type"] == "CANDIDATE_REFERENCE_FIRST_OBSERVED"
            assert candidate["cmt_id"] is None and candidate["reference"]["kind"] == "set"
            assert all("product_new" not in event for event in result["events"])
            assert discover("main") == result
            assert discover("baseline")["result"] == "baseline"
            assert discover("no_discoveries")["result"] == "no_discoveries"
            empty = discover("empty")
            assert empty["result"] == "discoveries" and len(empty["events"]) == 3
            assert empty["window"]["history"][0]["scope_evidence"] == "request_attested_empty"
            assert discover("rejected", 2)["error_category"] == "incomplete_evidence"
            assert discover("context", 2)["error_category"] == "context_mismatch"
            absent = call(
                [
                    "discover",
                    "--db",
                    f"{data_path}/absent.sqlite3",
                    "--request",
                    f"{fixture_path}/synthetic_discovery_request.json",
                ],
                1,
            )
            assert absent["error_category"] == "storage_io"
            if args.mode == "installed":
                assert not Path(f"{data_path}/absent.sqlite3").exists()
            assert inspect(database) == before
            copied, restored = f"{data_path}/copy.sqlite3", f"{data_path}/restored.sqlite3"
            call(["db", "backup", "--db", database, "--destination", copied])
            call(["db", "restore", "--db", copied, "--destination", restored])
            assert discover("main", target=restored) == result
            assert inspect(restored) == before and inspect(database) == before
            print(
                f"discovery {args.mode}: PASS (new set alias/targetless candidate/baseline/"
                "no discoveries/attested empty/incomplete/context/replay/nonmutation/"
                "backup restore; distinct processes)"
            )
        finally:
            if created_volume:
                subprocess.run(
                    ["docker", "volume", "rm", volume], check=True, capture_output=True, timeout=30
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
