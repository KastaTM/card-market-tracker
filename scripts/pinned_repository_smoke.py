"""Offline pinned import/migration/recovery across distinct CLI processes."""

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
    parser.add_argument("--image", default="cmt-p1b-smoke")
    parser.add_argument("--platform", default="linux/amd64")
    parser.add_argument("--fixtures", type=Path, required=True)
    args = parser.parse_args()
    fixtures = args.fixtures.resolve()
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    volume = f"cmt-p1b-smoke-{uuid4().hex}"
    created_volume = False
    with tempfile.TemporaryDirectory(prefix="cmt-p1b-smoke-") as outside:
        if args.mode == "installed":
            # -I excludes checkout/PYTHONPATH; the audit hook rejects socket
            # connections throughout every installed CLI operation, including
            # migration/restore. Existing wheel smokes exercise the console script.
            offline_cli = (
                "import sys; "
                "sys.addaudithook(lambda event,args: "
                "(_ for _ in ()).throw(RuntimeError('network denied')) "
                "if event.startswith('socket.') else None); "
                "from pathlib import Path; import card_market_tracker; "
                "assert Path(card_market_tracker.__file__).is_relative_to(Path(sys.prefix)); "
                "from card_market_tracker.cli import main; sys.exit(main(sys.argv[1:]))"
            )
            prefix, inspect_prefix = (
                [sys.executable, "-I", "-c", offline_cli],
                [sys.executable, "-I"],
            )
            data_path, fixture_path = outside, str(fixtures)
        else:
            subprocess.run(
                ["docker", "volume", "create", volume],
                check=True,
                capture_output=True,
                timeout=30,
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
                prefix = ["docker", "compose", "run", "--rm", "-T", "pinned"]
                inspect_prefix = [
                    "docker",
                    "compose",
                    "run",
                    "--rm",
                    "-T",
                    "--entrypoint",
                    "python",
                    "pinned",
                ]
        try:

            def call(command: list[str], expected: int = 0) -> dict:
                completed = subprocess.run(
                    [*prefix, *command],
                    capture_output=True,
                    text=True,
                    cwd=outside if args.mode == "installed" else None,
                    env=environment,
                    timeout=120,
                )
                assert completed.returncode == expected, (
                    f"pinned {args.mode} {command[0]} exit {completed.returncode}, "
                    f"expected {expected}"
                )
                result = json.loads(completed.stdout)
                events = [
                    json.loads(line)
                    for line in completed.stderr.splitlines()
                    if line.strip().startswith("{")
                ]
                events = [row for row in events if row.get("event") == "persistence.completed"]
                assert len(events) == 1
                UUID(events[0]["run_id"])
                assert events[0]["duration_ms"] >= 0 and events[0]["result"] == result["result"]
                assert fixture_path not in completed.stderr and data_path not in completed.stderr
                assert "tcgdex" not in completed.stderr and "swsh3" not in completed.stderr
                if result["result"] == "error":
                    assert result["counts"] is None and result["committed"] is None
                return result

            database = f"{data_path}/pinned.sqlite3"
            bundle = f"{fixture_path}/pinned_repository_bundle_v1.json"
            manifest = f"{fixture_path}/synthetic_manifest.json"
            token = "bd9cc4b8-eace-4567-8364-93cc4eccddc5"
            call(["bundle", "verify", "--input", bundle])
            call(["db", "init", "--db", database])
            import_command = [
                "bundle",
                "import",
                "--db",
                database,
                "--input",
                bundle,
                "--manifest",
                manifest,
                "--batch-id",
                token,
            ]
            first = call(import_command, 3)
            assert first["counts"] == {"input": 4, "accepted": 0, "candidates": 4, "rejected": 0}
            assert first["committed"] == {"observations": 4, "entities": 0}
            before = call(["captures", "--db", database, "--batch-id", token])
            assert before["evidence_state"] == "verified_local_pinned_bundle"
            assert len(before["records"]) == 4
            replay = call(import_command)
            assert replay["result"] == "replay" and replay["committed"] == {
                "observations": 0,
                "entities": 0,
            }
            assert replay["first_persisted_at"] == first["first_persisted_at"]
            conflict = list(import_command)
            conflict[conflict.index("--manifest") + 1] = (
                f"{fixture_path}/synthetic_discovery_manifest.json"
            )
            assert call(conflict, 2)["error_category"] == "replay_conflict"
            assert call(["captures", "--db", database, "--batch-id", token]) == before
            rows = call(["observations", "--db", database, "--batch-id", token])["records"]
            assert len(rows) == 4 and all(row["cmt_id"] is None for row in rows)
            assert all(row["observation"]["provenance"] == "observed" for row in rows)
            assert all(row["observation"]["reference"]["variant"] == "unknown" for row in rows)
            assert call(["db", "verify", "--db", database])["schema_version"] == 2
            saved, restored = (
                f"{data_path}/pinned.backup.sqlite3",
                f"{data_path}/pinned.restored.sqlite3",
            )
            call(["db", "backup", "--db", database, "--destination", saved])
            call(["db", "restore", "--db", saved, "--destination", restored])
            assert call(["captures", "--db", restored, "--batch-id", token]) == before
            restored_import = list(import_command)
            restored_import[restored_import.index("--db") + 1] = restored
            assert call(restored_import)["result"] == "replay"

            legacy = f"{data_path}/legacy.sqlite3"
            seed = (
                "import sqlite3,sys; "
                "from card_market_tracker.persistence.schema import V1_STATEMENTS; "
                "c=sqlite3.connect(sys.argv[1],autocommit=True); "
                "[c.execute(s) for s in V1_STATEMENTS]; "
                "c.execute(\"INSERT INTO storage_metadata VALUES(1,'card-market-tracker',1)\"); "
                "c.execute('PRAGMA application_id=1129141297'); "
                "c.execute('PRAGMA user_version=1'); c.close()"
            )
            seeded = subprocess.run(
                [*inspect_prefix, "-c", seed, legacy],
                check=True,
                capture_output=True,
                text=True,
                env=environment,
                timeout=120,
            )
            assert not seeded.stdout
            old = call(
                [
                    "persist",
                    "--db",
                    legacy,
                    "--input",
                    f"{fixture_path}/synthetic_persistence_valid.json",
                    "--manifest",
                    manifest,
                ]
            )
            old_rows = call(["observations", "--db", legacy, "--batch-id", old["batch_id"]])
            assert call(["db", "init", "--db", legacy])["schema_version"] == 1
            call(
                [
                    "db",
                    "migrate",
                    "--db",
                    legacy,
                    "--destination",
                    f"{data_path}/legacy.v1.sqlite3",
                ]
            )
            assert call(["observations", "--db", legacy, "--batch-id", old["batch_id"]]) == old_rows
            legacy_scope = call(["captures", "--db", legacy, "--batch-id", old["batch_id"]])
            assert legacy_scope["evidence_state"] == "legacy_unverified"
            migrated_import = list(import_command)
            migrated_import[migrated_import.index("--db") + 1] = legacy
            call(migrated_import, 3)
            call(["db", "verify", "--db", legacy])
            if args.mode != "installed":
                checked = subprocess.run(
                    [
                        *inspect_prefix,
                        "-c",
                        "import os; assert os.geteuid()==10001; print('uid=10001')",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                    env=environment,
                    timeout=120,
                )
                assert checked.stdout.strip() == "uid=10001"
        finally:
            if created_volume:
                subprocess.run(
                    ["docker", "volume", "rm", volume],
                    check=True,
                    capture_output=True,
                    timeout=30,
                )
    print(f"pinned {args.mode} smoke PASS; separate processes, migration, replay and recovery")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
