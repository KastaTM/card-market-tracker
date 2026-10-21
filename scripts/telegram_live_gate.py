"""Operator-only production qualification; one explicit send, no retry loop."""

from __future__ import annotations

import argparse
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--operation", choices=("validate", "send", "replay"), required=True)
    parser.add_argument("--operator-authorized", action="store_true", required=True)
    args = parser.parse_args()
    from card_market_tracker.cli import main as cli_main
    from card_market_tracker.telegram_delivery import application, storage
    from card_market_tracker.telegram_delivery.transport import TelegramTransport

    directory = args.directory.resolve()
    selection = json.loads((directory / "selection.json").read_text(encoding="ascii"))
    ledger = directory / "ledger.sqlite3"
    did = storage.delivery_id(selection["alert_id"])
    if args.operation == "send":
        current = storage.load_delivery(ledger, did)
        if current["state"] != "ready" or current["attempt_count"] != 0:
            raise RuntimeError("qualification_budget_already_used_or_not_ready")
    evidence_path = directory / ("live-" + args.operation + ".json")
    # Reserve the evidence BEFORE any network so concurrent/repeated runs fail closed.
    evidence_output = evidence_path.open("x", encoding="ascii")
    counters = {"metadata_request_upper_bound": 0, "send_message_invocations": 0}

    class ObservedProductionTransport(TelegramTransport):
        def validate_destination(self, bot_id: int, chat_id: int, *, timeout: float = 15) -> None:
            if args.operation == "replay":
                raise RuntimeError("unexpected_metadata_on_replay")
            counters["metadata_request_upper_bound"] += 2
            return super().validate_destination(bot_id, chat_id, timeout=timeout)

        def validate_bot(self, bot_id: int, *, timeout: float = 15) -> None:
            if args.operation == "replay":
                raise RuntimeError("unexpected_metadata_on_replay")
            counters["metadata_request_upper_bound"] += 1
            return super().validate_bot(bot_id, timeout=timeout)

        def send(self, bot_id: int, chat_id: int, message_text: str, *, timeout: float = 15):
            if args.operation != "send":
                raise RuntimeError("unexpected_send")
            counters["send_message_invocations"] += 1
            return super().send(bot_id, chat_id, message_text, timeout=timeout)

    # Instrument the production API entry, without changing worker/network behavior.
    # Counters are conservative request bounds on errors and exact after success.
    application.TelegramTransport = ObservedProductionTransport
    base = ["telegram-delivery"]
    if args.operation == "validate":
        command = [
            *base,
            "destination-validate",
            "--ledger-db",
            str(ledger),
            "--alias",
            selection["alias"],
        ]
    else:
        command = [
            *base,
            "send",
            "--ledger-db",
            str(ledger),
            "--delivery-id",
            did,
            "--captures-db",
            str(directory / "multi.sqlite3"),
            "--journal-db",
            str(directory / "journal.sqlite3"),
            "--outbox-db",
            str(directory / "outbox.sqlite3"),
        ]
    with redirect_stdout(io.StringIO()) as captured:
        code = cli_main(command)
    payload = json.loads(captured.getvalue())
    if args.operation == "replay" and (payload["result"] != "replay" or any(counters.values())):
        code = 2
    evidence = {
        "version": 1,
        "operation": args.operation,
        "exit_code": code,
        "message_sha256": selection["message_sha256"],
        "delivery_id": did,
        **counters,
        "response": payload,
    }
    if args.operation in {"send", "replay"}:
        evidence["local_receipt_and_history"] = storage.get(ledger, did)
    with evidence_output:
        json.dump(evidence, evidence_output, ensure_ascii=True, sort_keys=True)
    print(json.dumps(evidence, ensure_ascii=True, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
