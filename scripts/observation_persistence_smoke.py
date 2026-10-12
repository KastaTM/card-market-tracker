"""Check durable SQLite content through separate installed/container invocations."""

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
    parser.add_argument("--image", default="cmt-p3a-smoke")
    parser.add_argument("--platform", default="linux/amd64")
    parser.add_argument("--fixtures", type=Path, required=True)
    args = parser.parse_args()
    fixtures = args.fixtures.resolve()
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    volume = f"cmt-p3a-smoke-{uuid4().hex}"
    created_volume = False
    with tempfile.TemporaryDirectory(prefix="cmt-p3a-smoke-") as outside:
        if args.mode == "installed":
            prefix = [args.executable]
            data_path, fixture_path = outside, str(fixtures)
        else:
            subprocess.run(
                ["docker", "volume", "create", volume], check=True, capture_output=True, timeout=30
            )
            created_volume = True
            data_path, fixture_path = "/data", "/fixtures"
            mount_options = [
                "--mount",
                f"type=volume,source={volume},target=/data",
                "--mount",
                f"type=bind,source={fixtures},target=/fixtures,readonly",
            ]
            if args.mode == "docker":
                prefix = [
                    "docker",
                    "run",
                    "--rm",
                    "--network",
                    "none",
                    "--platform",
                    args.platform,
                    *mount_options,
                    args.image,
                ]
                inspect_prefix = [
                    "docker",
                    "run",
                    "--rm",
                    "--network",
                    "none",
                    "--platform",
                    args.platform,
                    *mount_options,
                    "--entrypoint",
                    "python",
                    args.image,
                ]
            else:
                environment["CMT_PERSISTENCE_VOLUME"] = volume
                prefix = ["docker", "compose", "run", "--rm", "-T", "persistence"]
                inspect_prefix = [
                    "docker",
                    "compose",
                    "run",
                    "--rm",
                    "-T",
                    "--entrypoint",
                    "python",
                    "persistence",
                ]
        try:
            if args.mode != "installed":
                inspected = subprocess.run(
                    inspect_prefix
                    + [
                        "-c",
                        "import os,stat,sys,sqlite3; "
                        "s=os.stat('/data'); "
                        "assert os.getuid()==10001 and s.st_uid==10001 and s.st_gid==10001; "
                        "assert stat.S_IMODE(s.st_mode)==0o700; "
                        "print(sys.version.split()[0], sqlite3.sqlite_version, "
                        "'uid=10001 data=0700')",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    env=environment,
                    timeout=120,
                )
                print(f"persistence {args.mode} runtime: {inspected.stdout.strip()}")

            def call(command: list[str], expected: int = 0) -> dict:
                completed = subprocess.run(
                    prefix + command,
                    cwd=outside if args.mode == "installed" else None,
                    capture_output=True,
                    text=True,
                    env=environment,
                    timeout=120,
                )
                assert completed.returncode == expected, (
                    f"{args.mode} {command[0]}: exit {completed.returncode}, expected {expected}"
                )
                result = json.loads(completed.stdout)
                logs = [
                    json.loads(line)
                    for line in completed.stderr.splitlines()
                    if line.strip().startswith("{")
                ]
                events = [row for row in logs if row.get("event") == "persistence.completed"]
                assert len(events) == 1
                UUID(events[0]["run_id"])
                assert events[0]["duration_ms"] >= 0
                assert events[0]["result"] == result["result"]
                assert fixture_path not in completed.stderr and data_path not in completed.stderr
                if result["result"] == "error":
                    assert result["counts"] is None and result["committed"] is None
                    assert "new_observation_count" not in events[0]
                elif "committed" in result:
                    assert events[0]["new_observation_count"] == result["committed"]["observations"]
                return result

            database = f"{data_path}/history.sqlite3"
            if args.mode != "installed":
                denied = call(["db", "init", "--db", "/app/denied.sqlite3"], 1)
                assert denied["error_category"] == "storage_io"

            def write(case: str, expected: int = 0, target: str = database) -> dict:
                return call(
                    [
                        "persist",
                        "--db",
                        target,
                        "--input",
                        f"{fixture_path}/synthetic_persistence_{case}.json",
                        "--manifest",
                        f"{fixture_path}/synthetic_manifest.json",
                    ],
                    expected,
                )

            def read(target: str = database, *selector: str) -> dict:
                return call(["observations", "--db", target, "--limit", "1000", *selector])

            call(["db", "init", "--db", database])
            first = write("valid")
            assert first["result"] == "ok" and first["counts"]["accepted"] == 7
            assert first["committed"]["observations"] == 7
            rows = read(database, "--batch-id", first["batch_id"])["records"]
            assert len(rows) == 7
            assert all(
                row["observation"]["captured_at"] == "2026-10-10T09:00:00.000000Z" for row in rows
            )
            assert any(row["observation"]["provider_updated_at"] is not None for row in rows)
            original_ids = [row["cmt_id"] for row in rows]
            for cmt_id in original_ids:
                assert UUID(cmt_id).version == 4
            replay = write("valid")
            assert replay["result"] == "replay"
            assert replay["committed"] == {"entities": 0, "observations": 0}
            assert replay["first_persisted_at"] == first["first_persisted_at"]
            assert read(database, "--batch-id", first["batch_id"])["records"] == rows
            later = write("later")
            assert later["committed"]["observations"] == 7
            assert [
                row["cmt_id"] for row in read(database, "--batch-id", later["batch_id"])["records"]
            ] == original_ids
            assert len(read()["records"]) == 14
            mixed = write("mixed", 3)
            assert mixed["counts"] == {"input": 3, "accepted": 1, "candidates": 1, "rejected": 1}
            mixed_rows = read(database, "--batch-id", mixed["batch_id"])["records"]
            assert mixed_rows[1]["status"] == "candidate" and mixed_rows[1]["cmt_id"] is None
            assert mixed_rows[2]["status"] == "rejected" and mixed_rows[2]["observation"] is None
            assert write("candidates", 3)["counts"]["candidates"] == 2
            assert write("rejected", 3)["committed"]["observations"] == 0
            assert write("empty")["result"] == "empty"
            before = read()
            assert write("invalid", 2)["result"] == "error"
            assert write("conflict", 2)["error_category"] == "replay_conflict"
            assert write("documented", 2)["error_category"] == "synthetic_only"
            assert read() == before
            one = call(["observations", "--db", database, "--limit", "1"])
            assert len(one["records"]) == 1
            ordered = [
                (
                    row["observation"]["captured_at"]
                    if row["observation"]
                    else "2026-10-10T09:00:00.000000Z",
                    row["batch_id"],
                    row["index"],
                )
                for row in before["records"]
            ]
            assert ordered == sorted(ordered)
            missing = f"{data_path}/missing.sqlite3"
            assert call(["observations", "--db", missing], 1)["error_category"] == "storage_io"
            if args.mode == "installed":
                assert not Path(missing).exists()
            call(["db", "verify", "--db", database])
            copied, restored = f"{data_path}/backup.sqlite3", f"{data_path}/restored.sqlite3"
            call(["db", "backup", "--db", database, "--destination", copied])
            call(["db", "restore", "--db", copied, "--destination", restored])
            call(["db", "verify", "--db", restored])
            assert read(restored) == before and read(copied) == before
            assert write("valid", target=restored)["result"] == "replay"
            unsafe = call(["db", "backup", "--db", database, "--destination", copied], 1)
            assert unsafe["error_category"] == "unsafe_destination"
            assert read(copied) == before
            print(
                f"persistence {args.mode}: PASS (durable reopen/replay/later/mixed/empty/"
                "conflict/synthetic-only/bounds/integrity/backup/restore; distinct invocations)"
            )
        finally:
            if created_volume:
                subprocess.run(
                    ["docker", "volume", "rm", volume], check=True, capture_output=True, timeout=30
                )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (subprocess.SubprocessError, OSError):
        print("persistence smoke: FAIL (local infrastructure)", file=sys.stderr)
        raise SystemExit(1) from None
