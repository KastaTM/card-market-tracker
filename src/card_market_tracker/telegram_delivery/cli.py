"""Strict manual Telegram delivery CLI with fixed redacted JSON diagnostics."""

from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path
from typing import Any

from ..alerts.errors import OutboxError
from ..catalog.validation import CatalogError
from ..discovery.errors import DiscoveryError
from ..discovery.journal_errors import JournalError
from ..persistence.errors import PersistenceError
from . import application, storage
from .errors import DeliveryError

OPERATIONS = (
    "init",
    "destination-add",
    "destination-validate",
    "prepare",
    "send",
    "get",
    "list",
    "verify",
    "recompute",
    "recover",
    "backup",
    "restore",
)


def register(commands: argparse._SubParsersAction[Any]) -> None:
    group = commands.add_parser("telegram-delivery")
    operations = group.add_subparsers(dest="telegram_delivery_operation", required=True)
    for name in OPERATIONS:
        parser = operations.add_parser(name, allow_abbrev=False)
        parser.add_argument("--ledger-db", type=Path, required=True)
        parser.add_argument(
            "--timeout",
            type=float,
            default=15.0 if name in ("send", "destination-validate") else 2.0,
        )
        if name in ("prepare", "send", "recompute"):
            for label in ("captures", "journal", "outbox"):
                parser.add_argument("--" + label + "-db", type=Path, required=True)
        if name in ("destination-add", "destination-validate", "prepare"):
            parser.add_argument("--alias", required=True)
        if name == "destination-add":
            parser.add_argument("--bot-id", type=int, required=True)
            parser.add_argument("--chat-id", type=int, required=True)
            parser.add_argument("--operator-private-owned", action="store_true", required=True)
        if name == "prepare":
            parser.add_argument("--alert-id", required=True)
            parser.add_argument("--comparison-id", required=True)
        if name in ("send", "get", "recompute", "recover"):
            parser.add_argument("--delivery-id", required=True)
        if name == "recover":
            parser.add_argument("--worker-quiesced", action="store_true", required=True)
        if name == "list":
            parser.add_argument(
                "--state",
                choices=(
                    "ready",
                    "in_flight",
                    "retryable",
                    "confirmed",
                    "permanent_failure",
                    "uncertain",
                ),
            )
            parser.add_argument("--limit", type=int, default=100)
            parser.add_argument("--cursor")
        if name in ("backup", "restore"):
            parser.add_argument("--destination", type=Path, required=True)


def _report(payload: dict[str, object], operation: str, started: float, code: int) -> int:
    extra: dict[str, object] = {
        "event": "telegram.delivery.completed",
        "component": "cli",
        "operation": "telegram_delivery_" + operation.replace("-", "_"),
        "result": payload["result"],
        "duration_ms": max(0, round((time.perf_counter() - started) * 1000)),
    }
    if "error_category" in payload:
        extra["error_category"] = payload["error_category"]
    nested = payload.get("delivery")
    delivery = nested if isinstance(nested, dict) else {}
    for key in ("delivery_id", "attempt_id", "state", "attempt_count"):
        if key in payload:
            extra[key] = payload[key]
        elif key in delivery:
            extra[key] = delivery[key]
    logging.getLogger("card_market_tracker").log(
        logging.ERROR if code else logging.INFO, "", extra=extra
    )
    print(
        json.dumps(
            payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
    )
    return code


def invalid_arguments(started: float) -> int:
    return _report(
        {
            "version": 1,
            "operation": "telegram-delivery",
            "result": "error",
            "error_category": "invalid_field",
        },
        "arguments",
        started,
        2,
    )


def dispatch(args: argparse.Namespace, started: float) -> int:
    name: str = args.telegram_delivery_operation
    try:
        path, timeout = args.ledger_db, args.timeout
        if name == "init":
            payload = storage.initialize(path, timeout=timeout)
        elif name == "destination-add":
            payload = storage.destination_add(
                path,
                args.alias,
                args.bot_id,
                args.chat_id,
                operator_private_owned=args.operator_private_owned,
                timeout=timeout,
            )
        elif name == "destination-validate":
            payload = application.destination_validate(path, args.alias, timeout=timeout)
        elif name == "prepare":
            payload = application.prepare(
                args.captures_db,
                args.journal_db,
                args.outbox_db,
                path,
                args.alert_id,
                args.comparison_id,
                args.alias,
                timeout=timeout,
            )
        elif name == "send":
            payload = application.send(
                args.captures_db,
                args.journal_db,
                args.outbox_db,
                path,
                args.delivery_id,
                timeout=timeout,
            )
        elif name == "get":
            payload = storage.get(path, args.delivery_id, timeout=timeout)
        elif name == "list":
            payload = storage.list_deliveries(
                path, state=args.state, cursor=args.cursor, limit=args.limit, timeout=timeout
            )
        elif name == "verify":
            payload = storage.verify(path, timeout=timeout)
        elif name == "recompute":
            payload = application.recompute(
                args.captures_db,
                args.journal_db,
                args.outbox_db,
                path,
                args.delivery_id,
                timeout=timeout,
            )
        elif name == "recover":
            payload = storage.recover(
                path, args.delivery_id, worker_quiesced=args.worker_quiesced, timeout=timeout
            )
        elif name == "backup":
            payload = storage.backup(path, args.destination, timeout=timeout)
        elif name == "restore":
            payload = storage.restore(path, args.destination, timeout=timeout)
        else:
            raise DeliveryError("invalid_field")
        state = payload.get("state") if name == "send" else None
        code = (
            1 if state in ("uncertain", "retryable") else 2 if state == "permanent_failure" else 0
        )
        return _report(payload, name, started, code)
    except (
        DeliveryError,
        OutboxError,
        CatalogError,
        DiscoveryError,
        JournalError,
        PersistenceError,
    ) as error:
        safe = DeliveryError(error.category)
    except Exception:
        safe = DeliveryError("storage_io")
    return _report(
        {"version": 1, "operation": name, "result": "error", "error_category": safe.category},
        name,
        started,
        safe.exit_code,
    )
