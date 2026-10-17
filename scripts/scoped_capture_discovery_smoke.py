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

OFFLINE = """
import sys
sys.addaudithook(lambda event, args: (_ for _ in ()).throw(RuntimeError('network denied'))
                if event.startswith('socket.') else None)
from pathlib import Path
import card_market_tracker
assert Path(card_market_tracker.__file__).is_relative_to(Path(sys.prefix))
"""

SEED = """
import json
from card_market_tracker.catalog.manifest import parse_manifest
from card_market_tracker.catalog.validation import read_json
from card_market_tracker.persistence.input import parse_persistence
from card_market_tracker.persistence.capture import persist_capture, persist_bundle
fixtures, directory = map(Path, sys.argv[1:])
database = directory / 'scoped.sqlite3'
manifest = parse_manifest(read_json(fixtures / 'synthetic_discovery_manifest.json'))
for case in ('history', 'empty', 'current', 'rejected'):
    document = read_json(fixtures / ('synthetic_discovery_' + case + '.json'))
    batch = parse_persistence(document, manifest)
    scope = {'version': 1, 'acquired_at': batch.captured_at,
             'captured_at': batch.captured_at, 'outcome': 'complete',
             'units': [{'namespace': 'tcgdex', 'kind': 'set', 'language': 'es',
                        'selector': 'offline-demo', 'selected': ['synthetic/sets'],
                        'completed': ['synthetic/sets'],
                        'record_indexes': list(range(len(batch.records)))}]}
    persist_capture(database, batch, scope)
request = read_json(fixtures / 'synthetic_scoped_discovery_request.json')
def save(name, value):
    (directory / (name + '.json')).write_text(json.dumps(value), encoding='utf-8')
save('main', request)
save('permuted', {**request, 'history': list(reversed(request['history']))})
save('baseline', {**request, 'history': []})
save('empty', {**request, 'history': [request['history'][0]]})
save('rejected', {**request, 'current': {
    'batch_id': read_json(fixtures / 'synthetic_discovery_rejected.json')['batch_id'],
    'selector': 'offline-demo'}})
bundle = read_json(fixtures / 'pinned_repository_bundle_v1.json')
empty_manifest = parse_manifest({'version': 1, 'entities': [], 'bindings': []})
tokens = ['bd9cc4b8-eace-4567-8364-93cc4eccddc5',
          'bd9cc4b8-eace-4567-8364-93cc4eccddc6']
for token in tokens:
    persist_bundle(database, bundle, token, empty_manifest)
for kind, selector in [('set', 'swsh3'), ('card', 'swsh3-136')]:
    for language in ('es', 'en'):
        real = {'version': 2, 'context': {'namespace': 'tcgdex_repository',
                'kind': kind, 'language': language},
                'current': {'batch_id': tokens[0], 'selector': selector}, 'history': []}
        save(kind + '-' + language, real)
        if kind == 'set' and language == 'es':
            save('chronology', {**real, 'history': [
                {'batch_id': tokens[1], 'selector': selector}]})
            save('v1', {'version': 1, 'context': real['context'],
                        'current_batch_id': tokens[0], 'history_batch_ids': []})
print('seed complete; synthetic transitions and fixed real baselines')
"""

INSPECT = """
import json, sqlite3
c = sqlite3.connect(Path(sys.argv[1]).as_uri() + '?mode=ro', uri=True, autocommit=True)
c.execute('PRAGMA query_only=ON')
c.execute('BEGIN')
payload = {'inventory': c.execute('SELECT type,name,tbl_name,sql FROM sqlite_schema '
                                'ORDER BY type,name').fetchall(),
           'versions': [c.execute('PRAGMA application_id').fetchone()[0],
                        c.execute('PRAGMA user_version').fetchone()[0]],
           'content': {table: c.execute('SELECT * FROM ' + table + ' ORDER BY 1,2').fetchall()
                       for table in ('storage_metadata','entities','batches','records','captures')}}
c.execute('ROLLBACK')
c.close()
print(json.dumps(payload, sort_keys=True))
"""

COPY = """
import json
from card_market_tracker.persistence.sqlite_repository import DEFAULT_TIMEOUT, backup, restore
assert DEFAULT_TIMEOUT == 2.0
operation, source, destination = sys.argv[1:]
# Reconstructing all six captures repeatedly during verified copy costs more
# under QEMU. Exercise the already supported explicit maximum, without changing
# CLI/reader defaults, retrying failures or skipping any verification.
result = {'backup': backup, 'restore': restore}[operation](
    Path(source), Path(destination), timeout=5.0)
assert result['result'] == 'ok' and result['schema_version'] == 2
print(json.dumps(result))
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("installed", "docker", "compose"), required=True)
    parser.add_argument("--executable", default="cmt")
    parser.add_argument("--image", default="cmt-p4b-smoke")
    parser.add_argument("--platform", default="linux/amd64")
    parser.add_argument("--fixtures", type=Path, required=True)
    args = parser.parse_args()
    fixtures = args.fixtures.resolve()
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    volume = f"cmt-p4b-smoke-{uuid4().hex}"
    created = False
    with tempfile.TemporaryDirectory(prefix="cmt-p4b-smoke-") as outside:
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
            database = f"{data}/scoped.sqlite3"
            before = json.loads(execute(INSPECT, database))

            def discover(case: str, expected: int = 0, target: str = database) -> dict:
                return call(
                    ["discover-scoped", "--db", target, "--request", f"{data}/{case}.json"],
                    expected,
                )

            result = discover("main")
            assert result["version"] == 2 and result["result"] == "discoveries"
            assert result["comparison_id"].startswith("cmp2:") and len(result["events"]) == 2
            assert {event["type"] for event in result["events"]} == {
                "SET_REFERENCE_FIRST_OBSERVED",
                "CANDIDATE_REFERENCE_FIRST_OBSERVED",
            }
            assert all(event["event_id"].startswith("evt2:") for event in result["events"])
            assert discover("main") == result and discover("permuted") == result
            assert discover("baseline")["result"] == "baseline"
            assert len(discover("empty")["events"]) == 3
            assert discover("rejected", 2)["error_category"] == "incomplete_evidence"
            for kind in ("set", "card"):
                for language in ("es", "en"):
                    baseline = discover(f"{kind}-{language}")
                    assert baseline["result"] == "baseline" and baseline["events"] == []
            assert discover("chronology", 2)["error_category"] == "chronology"
            assert (
                call(["discover", "--db", database, "--request", f"{data}/v1.json"], 2)[
                    "error_category"
                ]
                == "synthetic_only"
            )
            assert json.loads(execute(INSPECT, database)) == before
            backup, restored = f"{data}/backup.sqlite3", f"{data}/restored.sqlite3"
            for operation, origin, destination in (
                ("backup", database, backup),
                ("restore", backup, restored),
            ):
                copied = json.loads(execute(COPY, operation, origin, destination))
                assert copied["result"] == "ok" and copied["schema_version"] == 2
            print("verified backup/restore: explicit 5s budget; CLI/read default remains 2s")
            assert discover("main", target=restored) == result
            assert json.loads(execute(INSPECT, restored)) == before
            assert json.loads(execute(INSPECT, database)) == before
        finally:
            if created:
                subprocess.run(
                    ["docker", "volume", "rm", volume], check=True, capture_output=True, timeout=30
                )
    print(
        f"scoped {args.mode} smoke PASS; separate offline processes, real baseline only, "
        "synthetic transitions, v1 guard, nonmutation and restore"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
