"""Eighth offline harness: durable alerts across independent installed processes."""

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

FILE_DIGEST = "import hashlib\nprint(hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest())"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode", choices=("installed", "docker", "compose", "wheel", "container"), required=True
    )
    parser.add_argument("--executable", default="cmt")
    parser.add_argument("--image", default="cmt-p8a-smoke")
    parser.add_argument("--platform", default="linux/amd64")
    parser.add_argument("--fixtures", type=Path, required=True)
    args = parser.parse_args()
    args.mode = {"wheel": "installed", "container": "docker"}.get(args.mode, args.mode)
    fixtures = args.fixtures.resolve()
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    volume = "cmt-p8a-smoke-" + uuid4().hex
    created = False
    with tempfile.TemporaryDirectory(prefix="cmt-p8a-smoke-") as outside:
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
                        "alert-outbox",
                        operation,
                        "--outbox-db",
                        target or outbox,
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
                    log["event"] == "alert.outbox.completed" and log["result"] == payload["result"]
                )
                assert log["duration_ms"] >= 0 and log["operation"].startswith("alert_outbox_")
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
            captures, journal, outbox = (
                f"{data}/{name}.sqlite3" for name in ("multi", "journal", "outbox")
            )
            original = json.loads(execute(INSPECT, captures))
            execute(
                "from card_market_tracker.discovery.journal_storage import initialize\n"
                "initialize(Path(sys.argv[1]))",
                journal,
            )
            call("init")

            def record(case: str) -> dict:
                return json.loads(
                    execute(
                        "import json\n"
                        "from card_market_tracker.discovery.journal_application import record\n"
                        "print(json.dumps(record(*map(Path,sys.argv[1:]))))",
                        captures,
                        journal,
                        f"{data}/{case}.json",
                    )
                )

            def enqueue(cid: str, target: str | None = None) -> dict:
                return call(
                    "enqueue",
                    "--captures-db",
                    captures,
                    "--journal-db",
                    journal,
                    "--comparison-id",
                    cid,
                    "--destination-key",
                    "local-preview",
                    "--timeout",
                    "5",
                    target=target,
                )

            def recompute(aid: str, cid: str, target: str | None = None) -> dict:
                return call(
                    "recompute",
                    "--captures-db",
                    captures,
                    "--journal-db",
                    journal,
                    "--alert-id",
                    aid,
                    "--comparison-id",
                    cid,
                    "--timeout",
                    "5",
                    target=target,
                )

            first = record("synthetic")
            cid = first["comparison_id"]
            journal_before = execute(FILE_DIGEST, journal)
            prepared = enqueue(cid)
            assert prepared["alerts_new"] == 2 and prepared["associations_new"] == 2
            page = call("list", "--limit", "1")
            assert len(page["items"]) == 1 and page["next_cursor"]
            assert len(call("list", "--cursor", page["next_cursor"])["items"]) == 1
            aid = page["items"][0]["alert_id"]
            retained = call("get", "--alert-id", aid)
            alert = retained["alert"]
            # Independent identity recipe; do not import production helpers.
            import hashlib

            identity = json.dumps(
                {
                    "identity_version": 1,
                    "destination_key": "local-preview",
                    "event_id": alert["event_id"],
                },
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            assert aid == "alt1:" + hashlib.sha256(identity.encode("ascii")).hexdigest()
            before = execute(FILE_DIGEST, outbox)
            preview = call("preview", "--alert-id", aid)
            assert preview["message_text"] == alert["message_text"]
            assert "SYNTHETIC" in preview["message_text"]
            assert "selected comparison window" in preview["message_text"]
            assert preview["state"] == "pending"
            assert enqueue(cid)["result"] == "replay"
            recompute(aid, cid)
            assert execute(FILE_DIGEST, outbox) == before
            assert execute(FILE_DIGEST, journal) == journal_before
            second = record("window")
            other = second["comparison_id"]
            assert cid != other
            result = enqueue(other)
            assert result["alerts_new"] == 0 and result["alerts_existing"] == 2
            assert result["associations_new"] == 2 and result["associations_existing"] == 0
            assert call("get", "--alert-id", aid) == retained
            evidence = call("evidence-list", "--alert-id", aid, "--limit", "1")
            assert len(evidence["items"]) == 1 and evidence["next_cursor"]
            following = call(
                "evidence-list", "--alert-id", aid, "--cursor", evidence["next_cursor"]
            )
            assert len(following["items"]) == 1 and following["next_cursor"] is None
            e1 = call("evidence-get", "--alert-id", aid, "--comparison-id", cid)
            e2 = call("evidence-get", "--alert-id", aid, "--comparison-id", other)
            assert e1["event"]["event_id"] == e2["event"]["event_id"]
            assert e1["event"]["evidence"] != e2["event"]["evidence"]
            for case in ("baseline", "set-es", "set-en", "card-es", "card-en"):
                no_events = record(case)
                empty = enqueue(no_events["comparison_id"])
                assert empty["events"] == 0 and empty["result"] == "replay"
            assert call("verify", "--timeout", "5")["counts"] == {"alerts": 2, "associations": 4}
            backup, restored = f"{data}/backup.sqlite3", f"{data}/restored.sqlite3"
            call("backup", "--destination", backup, "--timeout", "5")
            call("restore", "--destination", restored, "--timeout", "5", target=backup)
            assert call("get", "--alert-id", aid, target=restored) == retained
            call("verify", "--timeout", "5", target=restored)
            assert enqueue(cid, target=restored)["result"] == "replay"
            recompute(aid, other, target=restored)
            assert json.loads(execute(INSPECT, captures)) == original
            assert call("list", target=f"{data}/missing.sqlite3", expected=1)["result"] == "error"
        finally:
            if created:
                subprocess.run(
                    ["docker", "volume", "rm", volume], check=True, capture_output=True, timeout=30
                )
    print(
        f"alert outbox {args.mode} smoke PASS; two synthetic alerts, four window associations, "
        "four real zero-alert comparisons, preview, replay, origin recompute and recovery; "
        "separate offline processes"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
