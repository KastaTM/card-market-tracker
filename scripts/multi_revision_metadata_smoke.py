"""Offline persisted-scope comparison in distinct installed/container processes."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from uuid import UUID, uuid4

from scoped_capture_discovery_smoke import COPY, INSPECT, OFFLINE

SEED = r"""
import json
from card_market_tracker.catalog.manifest import parse_manifest
from card_market_tracker.catalog.validation import read_json
from card_market_tracker.persistence.input import parse_persistence
from card_market_tracker.persistence.capture import persist_capture, persist_bundle_v2
from card_market_tracker.pinned_repository.bundle_v2 import approved_bundle_document_v2
fixtures, directory = map(Path, sys.argv[1:])
database = directory / "multi.sqlite3"
manifest = parse_manifest({"version":1,"entities":[],"bindings":[]})
tokens = ["bd9cc4b8-eace-4567-8364-93cc4eccddc5", "bd9cc4b8-eace-4567-8364-93cc4eccddc6"]
for token,member in zip(tokens,("r0","r1"), strict=True):
    persist_bundle_v2(database, approved_bundle_document_v2(member), token, manifest)
def save(name,value):
    (directory/(name+".json")).write_text(json.dumps(value),encoding="utf-8")
save("manifest", {"version":1,"entities":[],"bindings":[]})
for kind,selector in (("set","swsh3"),("card","swsh3-136")):
    for language in ("es","en"):
        req={"version":3,"profile":"tcgdex_swsh3_136_r0_r1_v1",
             "context":{"namespace":"tcgdex_repository","kind":kind,"language":language},
             "current":{"batch_id":tokens[1],"selector":selector},
             "history":[{"batch_id":tokens[0],"selector":selector}]}
        save(kind+"-"+language,req)
        if kind=="set" and language=="es":
            save("reverse",{**req,"current":req["history"][0],"history":[req["current"]]})
            save("equal",{**req,"history":[{"batch_id":"bd9cc4b8-eace-4567-8364-93cc4eccddc7","selector":selector}]})
            save("v2",{k:(2 if k=="version" else v) for k,v in req.items() if k!="profile"})
# Explicit synthetic positive proof, distinct from the reviewed real pair.
manifest=parse_manifest(read_json(fixtures/"synthetic_discovery_manifest.json"))
for case in ("history","empty","current"):
    batch=parse_persistence(read_json(fixtures/("synthetic_discovery_"+case+".json")),manifest)
    scope={"version":1,"acquired_at":batch.captured_at,"captured_at":batch.captured_at,
           "outcome":"complete","units":[{"namespace":"tcgdex","kind":"set","language":"es",
           "selector":"offline-demo","selected":["synthetic/sets"],"completed":["synthetic/sets"],
           "record_indexes":list(range(len(batch.records)))}]}
    persist_capture(database,batch,scope)
req=read_json(fixtures/"synthetic_scoped_discovery_request.json")
save("synthetic",{**req,"version":3,"profile":"synthetic_multi_revision_v1"})
save("permuted",{**req,"version":3,"profile":"synthetic_multi_revision_v1","history":list(reversed(req["history"]))})
print("seed: reviewed real unchanged pair and explicit synthetic transitions")
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("installed", "docker", "compose"), required=True)
    parser.add_argument("--executable", default="cmt")
    parser.add_argument("--image", default="cmt-p1c-smoke")
    parser.add_argument("--platform", default="linux/amd64")
    parser.add_argument("--fixtures", type=Path, required=True)
    args = parser.parse_args()
    fixtures = args.fixtures.resolve()
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    volume = f"cmt-p1c-smoke-{uuid4().hex}"
    created = False
    with tempfile.TemporaryDirectory(prefix="cmt-p1c-smoke-") as outside:
        if args.mode == "installed":
            python = [sys.executable, "-I"]
            cli = [
                *python,
                "-c",
                OFFLINE + "\nfrom card_market_tracker.cli import main\n"
                "sys.exit(main(sys.argv[1:]))",
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
                assert completed.returncode == 0, completed.stderr
                return completed.stdout

            def call(command: list[str], expected: int = 0) -> dict:
                completed = run([*cli, *command])
                assert completed.returncode == expected, (
                    command[0],
                    completed.returncode,
                    completed.stdout,
                    completed.stderr,
                )
                payload = json.loads(completed.stdout)
                events = [
                    json.loads(line)
                    for line in completed.stderr.splitlines()
                    if line.startswith("{")
                ]
                assert len(events) == 1
                event = events[0]
                UUID(event["run_id"])
                assert event["result"] == payload["result"] and event["duration_ms"] >= 0
                for forbidden in (
                    source,
                    data,
                    "tcgdex",
                    "offline-demo",
                    "swsh3",
                    "11111111-1111",
                    "22222222-2222",
                    "bd9cc4b8-eace",
                ):
                    assert forbidden not in completed.stderr
                if payload["result"] == "error":
                    assert payload["counts"] is None
                    if command[0].startswith("discover"):
                        assert payload["events"] == []
                return payload

            print(execute(SEED, source, data).strip())
            if args.mode != "installed":
                print(
                    execute(
                        "import os,stat,sqlite3\ns=os.stat('/data')\n"
                        "assert os.getuid()==10001 and s.st_uid==10001 and s.st_gid==10001\n"
                        "assert stat.S_IMODE(s.st_mode)==0o700\n"
                        "print(sys.version.split()[0],sqlite3.sqlite_version,'uid=10001')"
                    ).strip()
                )
            database = f"{data}/multi.sqlite3"
            before = json.loads(execute(INSPECT, database))

            def discover(case: str, expected: int = 0, target: str = database) -> dict:
                return call(
                    ["discover-multi-revision", "--db", target, "--request", f"{data}/{case}.json"],
                    expected,
                )

            result = discover("synthetic")
            assert result["version"] == 3 and result["result"] == "discoveries"
            assert result["comparison_id"].startswith("cmp3:") and len(result["events"]) == 2
            assert all(event["event_id"].startswith("evt3:") for event in result["events"])
            assert discover("permuted") == result
            for kind in ("set", "card"):
                for language in ("es", "en"):
                    pair = discover(f"{kind}-{language}")
                    assert pair["result"] == "no_discoveries" and pair["events"] == []
                    assert len(pair["current"]["extraction_proof"]["fields"]) == 8
                    assert (
                        pair["current"]["extraction_proof"]
                        == pair["history"][0]["extraction_proof"]
                    )
                    assert (
                        pair["current"]["acquisition"]["revision"]
                        != pair["history"][0]["acquisition"]["revision"]
                    )
                    assert (
                        pair["current"]["acquisition"]["bundle_sha256"]
                        != pair["history"][0]["acquisition"]["bundle_sha256"]
                    )
            assert discover("reverse", 2)["error_category"] == "chronology"
            assert (
                call(["discover-scoped", "--db", database, "--request", f"{data}/v2.json"], 2)[
                    "error_category"
                ]
                == "unsupported_evidence"
            )
            for token, outcome in (
                ("bd9cc4b8-eace-4567-8364-93cc4eccddc6", "replay"),
                ("bd9cc4b8-eace-4567-8364-93cc4eccddc7", "mixed"),
            ):
                imported = call(
                    [
                        "bundle-v2",
                        "import",
                        "--db",
                        database,
                        "--input",
                        f"{source}/pinned_repository_bundle_v2.json",
                        "--manifest",
                        f"{data}/manifest.json",
                        "--batch-id",
                        token,
                    ],
                    0 if outcome == "replay" else 3,
                )
                assert imported["result"] == outcome
                if outcome == "replay":
                    assert json.loads(execute(INSPECT, database)) == before
            assert discover("equal", 2)["error_category"] == "chronology"
            before = json.loads(execute(INSPECT, database))
            assert json.loads(execute(INSPECT, database)) == before
            backup, restored = f"{data}/backup.sqlite3", f"{data}/restored.sqlite3"
            for operation, origin, destination in (
                ("backup", database, backup),
                ("restore", backup, restored),
            ):
                copied = json.loads(execute(COPY, operation, origin, destination))
                assert copied["result"] == "ok" and copied["schema_version"] == 2
            print("verified backup/restore: explicit 5s budget; CLI/read default remains 2s")
            assert discover("synthetic", target=restored) == result
            assert discover("set-es", target=restored) == discover("set-es")
            assert json.loads(execute(INSPECT, restored)) == before
            assert json.loads(execute(INSPECT, database)) == before
        finally:
            if created:
                subprocess.run(
                    ["docker", "volume", "rm", volume], check=True, capture_output=True, timeout=30
                )
    print(
        f"multi-revision {args.mode} smoke PASS; separate offline processes, real unchanged pair, "
        "synthetic transitions, v2 guard, replay, chronology, nonmutation and restore"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
