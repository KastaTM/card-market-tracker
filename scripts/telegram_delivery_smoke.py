"""Ninth offline harness: installed processes, fake transport and durable fencing."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

from multi_revision_metadata_smoke import SEED
from scoped_capture_discovery_smoke import OFFLINE

PIPELINE = """
import json
from card_market_tracker.discovery import journal_application, journal_storage
from card_market_tracker.alerts import application, storage
p=Path(sys.argv[1]); captures=p/'multi.sqlite3'
journal=p/'journal.sqlite3'; outbox=p/'outbox.sqlite3'
journal_storage.initialize(journal)
cid=journal_application.record(captures,journal,p/'synthetic.json')['comparison_id']
storage.initialize(outbox)
application.enqueue(captures,journal,outbox,cid,'operator-private',timeout=5)
alerts=storage.list_alerts(outbox)['items']
print(json.dumps({'comparison_id':cid,'alerts':[r['alert_id'] for r in alerts]}))
"""

FAKE = """
import json,os
from card_market_tracker.telegram_delivery import application
from card_market_tracker.telegram_delivery.transport import Receipt,TransportResult
from card_market_tracker.alerts import storage as outbox_storage
data=Path(sys.argv[1]); operation=sys.argv[2]; selected=sys.argv[3]
def counted(method):
    with (data/'calls.jsonl').open('a',encoding='ascii') as calls:
        calls.write(json.dumps({'method':method})+'\\n')
class Fake:
    def check_configuration(self): pass
    def validate_destination(self,bot_id,chat_id,*,timeout):
        assert (bot_id,chat_id)==(7001,8001)
        counted('getMe'); counted('getChat')
    def validate_bot(self,bot_id,*,timeout):
        assert bot_id==7001
        counted('getMe')
    def send(self,bot_id,chat_id,message_text,*,timeout):
        from card_market_tracker.telegram_delivery import storage
        delivery=storage.load_delivery(data/'ledger.sqlite3',selected)
        alert=outbox_storage.get(data/'outbox.sqlite3',delivery['alert_id'])['alert']
        assert message_text==alert['message_text'] and 'SYNTHETIC' in message_text
        assert (bot_id,chat_id)==(7001,8001)
        counted('sendMessage')
        if operation=='crash': os._exit(23)
        return TransportResult(state='confirmed',receipt=Receipt(
            message_id=91,accepted_at=1800000000,bot_id=bot_id,chat_id=chat_id))
if operation=='validate':
    result=application.destination_validate(data/'ledger.sqlite3','operator-private',transport=Fake())
else:
    result=application.send(data/'multi.sqlite3',data/'journal.sqlite3',data/'outbox.sqlite3',
                            data/'ledger.sqlite3',selected,transport=Fake())
print(json.dumps(result))
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("installed", "docker", "compose"), required=True)
    parser.add_argument("--executable", default="cmt")
    parser.add_argument("--image", default="cmt-p8b-smoke")
    parser.add_argument("--platform", default="linux/amd64")
    parser.add_argument("--fixtures", type=Path, required=True)
    args = parser.parse_args()
    fixtures = args.fixtures.resolve()
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("CMT_TELEGRAM_BOT_TOKEN", None)
    volume = "cmt-p8b-smoke-" + uuid4().hex
    created = False
    with tempfile.TemporaryDirectory(prefix="cmt-p8b-smoke-") as outside:
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
            ledger = f"{data}/ledger.sqlite3"
            origins = [
                "--captures-db",
                f"{data}/multi.sqlite3",
                "--journal-db",
                f"{data}/journal.sqlite3",
                "--outbox-db",
                f"{data}/outbox.sqlite3",
            ]

            def run(command: list[str], expected: int = 0) -> subprocess.CompletedProcess[str]:
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

            def execute(code: str, *values: str, expected: int = 0) -> str:
                return run([*python, "-c", OFFLINE + "\n" + code, *values], expected).stdout

            def call(operation: str, *values: str, target: str = ledger, expected: int = 0) -> dict:
                completed = run(
                    [
                        *cli,
                        "telegram-delivery",
                        operation,
                        "--ledger-db",
                        target,
                        *values,
                    ],
                    expected,
                )
                payload = json.loads(completed.stdout)
                logs = [
                    json.loads(line)
                    for line in completed.stderr.splitlines()
                    if line.startswith("{")
                ]
                assert len(logs) == 1 and logs[0]["event"] == "telegram.delivery.completed"
                for forbidden in (
                    "7001",
                    "8001",
                    "SYNTHETIC",
                    data,
                    "api.telegram.org",
                    "message_text",
                ):
                    assert forbidden not in completed.stderr and forbidden not in completed.stdout
                return payload

            def calls() -> list:
                return json.loads(
                    execute(
                        "import json\np=Path(sys.argv[1])/'calls.jsonl'; "
                        "rows=[json.loads(r) for r in p.read_text().splitlines()] "
                        "if p.exists() else []; "
                        "print(json.dumps(rows))",
                        data,
                    )
                )

            def digests() -> str:
                return execute(
                    "import hashlib,json\np=Path(sys.argv[1]); print(json.dumps(["
                    "hashlib.sha256((p/name).read_bytes()).hexdigest() for name in "
                    "('multi.sqlite3','journal.sqlite3','outbox.sqlite3')]))",
                    data,
                )

            execute(SEED, source, data)
            selection = json.loads(execute(PIPELINE, data))
            before = digests()
            if args.mode != "installed":
                execute(
                    "import os,stat\ns=Path('/data').stat(); assert os.getuid()==10001 "
                    "and s.st_uid==10001 and stat.S_IMODE(s.st_mode)==0o700",
                )
            call("init")
            call(
                "destination-add",
                "--alias",
                "operator-private",
                "--bot-id",
                "7001",
                "--chat-id",
                "8001",
                "--operator-private-owned",
            )
            execute(FAKE, data, "validate", "unused")
            cid, aids = selection["comparison_id"], selection["alerts"]

            def prepare(aid: str, target: str = ledger) -> str:
                result = call(
                    "prepare",
                    *origins,
                    "--alert-id",
                    aid,
                    "--comparison-id",
                    cid,
                    "--alias",
                    "operator-private",
                    "--timeout",
                    "5",
                    target=target,
                )
                did = result["delivery_id"]
                preimage = json.dumps(
                    {"identity_version": 1, "alert_id": aid, "provider": "telegram"},
                    ensure_ascii=True,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                assert did == "tdl1:" + hashlib.sha256(preimage.encode("ascii")).hexdigest()
                return did

            did = prepare(aids[0])
            assert prepare(aids[0]) == did
            backup, restored = f"{data}/backup.sqlite3", f"{data}/restored.sqlite3"
            call("backup", "--destination", backup)
            sent = json.loads(execute(FAKE, data, "send", did))
            assert sent["state"] == "confirmed"
            counted = calls()
            assert sum(r["method"] == "sendMessage" for r in counted) == 1
            replay = json.loads(execute(FAKE, data, "send", did))
            assert replay["result"] == "replay" and calls() == counted
            call("get", "--delivery-id", did)
            call("recompute", *origins, "--delivery-id", did, "--timeout", "5")
            second = prepare(aids[1])
            execute(FAKE, data, "crash", second, expected=23)
            call("recover", "--delivery-id", second, "--worker-quiesced")
            counted = calls()
            call("send", *origins, "--delivery-id", second, expected=2)
            assert calls() == counted
            page = call("list", "--limit", "1")
            assert len(page["items"]) == 1 and page["next_cursor"]
            assert len(call("list", "--cursor", page["next_cursor"])["items"]) == 1
            call("verify")
            call("restore", "--destination", restored, target=backup)
            prepare(aids[1], restored)  # absent from stale snapshot; still globally blocked
            for aid in aids:
                restored_did = prepare(aid, restored)
                blocked = call(
                    "send", *origins, "--delivery-id", restored_did, target=restored, expected=2
                )
                assert blocked["error_category"] == "send_quarantined"
            assert calls() == counted
            assert call("verify", target=restored)["send_quarantined"] is True
            assert digests() == before
        finally:
            if created:
                subprocess.run(
                    ["docker", "volume", "rm", volume], check=True, capture_output=True, timeout=30
                )
    print(
        f"telegram delivery {args.mode} smoke PASS; normal synthetic pipeline, exact text, "
        "durable receipt/replay, interrupted worker/recovery, stale restore global quarantine; "
        "separate offline installed processes, fake transport only"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
