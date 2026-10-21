"""Prepare local synthetic source evidence only; no token, Telegram call or send."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from multi_revision_metadata_smoke import SEED
from scoped_capture_discovery_smoke import OFFLINE
from telegram_delivery_smoke import PIPELINE


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, required=True)
    args = parser.parse_args()
    directory, fixtures = args.directory.absolute(), args.fixtures.resolve()
    directory.mkdir(mode=0o700, parents=False, exist_ok=False)
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("CMT_TELEGRAM_BOT_TOKEN", None)

    def execute(code: str, *values: str) -> str:
        result = subprocess.run(
            [sys.executable, "-I", "-c", OFFLINE + "\n" + code, *values],
            cwd=directory,
            env=environment,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if result.returncode:
            raise RuntimeError("offline_fixture_failed")
        return result.stdout

    execute(SEED, str(fixtures), str(directory))
    selection = json.loads(execute(PIPELINE, str(directory)))
    # The normal pipeline creates two synthetic outbox alerts; select exactly one.
    aid, cid = selection["alerts"][0], selection["comparison_id"]
    digest = execute(
        "from card_market_tracker.alerts import storage\n"
        "print(storage.get(Path(sys.argv[1]),sys.argv[2])['alert']['message_sha256'])",
        str(directory / "outbox.sqlite3"),
        aid,
    ).strip()
    execute(
        "from card_market_tracker.telegram_delivery import storage\n"
        "storage.initialize(Path(sys.argv[1]))",
        str(directory / "ledger.sqlite3"),
    )
    manifest = {
        "version": 1,
        "alias": "operator-private",
        "alert_id": aid,
        "comparison_id": cid,
        "message_sha256": digest,
        "status": "LIVE_UNVERIFIED",
        "transport_calls": 0,
        "send_attempts": 0,
    }
    (directory / "selection.json").write_text(
        json.dumps(manifest, sort_keys=True), encoding="ascii"
    )
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
