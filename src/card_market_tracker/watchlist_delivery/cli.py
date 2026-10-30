"""Bounded one-shot CLI for the independent Watchlist delivery authority."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

from . import application
from .budget import Budget
from .errors import DeliveryError

OPERATIONS = (
    "init",
    "destination-add",
    "destination-validate",
    "review",
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
_ORIGINS = ("review", "prepare", "recompute")


def register(commands: argparse._SubParsersAction[Any]) -> None:
    group = commands.add_parser("watchlist-telegram-delivery", allow_abbrev=False)
    operations = group.add_subparsers(dest="watchlist_delivery_operation", required=True)
    for name in OPERATIONS:
        parser = operations.add_parser(name, allow_abbrev=False)
        parser.add_argument("--ledger-db", type=Path, required=True)
        parser.add_argument(
            "--timeout",
            type=float,
            default=15.0 if name in ("send", "destination-validate") else 2.0,
        )
        if name in (*_ORIGINS, "send"):
            for flag in ("watchlist-db", "journal-db", "outbox-db", "manifest"):
                parser.add_argument("--" + flag, type=Path, required=name != "send")
        if name in ("review", "prepare"):
            parser.add_argument("--alert-id", required=True)
        if name in ("destination-add", "destination-validate", "review", "prepare"):
            parser.add_argument("--alias", required=True)
        if name == "destination-add":
            parser.add_argument("--bot-id", type=int, required=True)
            parser.add_argument("--chat-id", type=int, required=True)
            parser.add_argument("--operator-private-owned", action="store_true", required=True)
        if name == "prepare":
            parser.add_argument("--acknowledge-historical-demonstration", required=True)
            parser.add_argument("--expected-signal-id", required=True)
            parser.add_argument("--expected-revision", type=int, required=True)
            for field in ("message", "evidence", "route", "binding"):
                parser.add_argument("--expected-" + field + "-sha256", required=True)
        if name in ("send", "get", "recompute", "recover"):
            parser.add_argument("--delivery-id", required=True)
        if name == "recover":
            parser.add_argument("--worker-quiesced", action="store_true", required=True)
        if name == "list":
            parser.add_argument("--state")
            parser.add_argument("--limit", type=int, default=100)
            parser.add_argument("--cursor")
        if name in ("backup", "restore"):
            parser.add_argument("--destination", type=Path, required=True)


def _complete(payload: dict[str, object], operation: str, started: float, code: int) -> None:
    extra: dict[str, object] = {
        "event": "watchlist.telegram_delivery.completed",
        "component": "cli",
        "operation": "watchlist_telegram_delivery_" + operation.replace("-", "_"),
        "result": payload.get("result", "error"),
        "duration_ms": max(0, round((time.perf_counter() - started) * 1000)),
    }
    if code:
        extra["result"] = "error"
        extra["error_category"] = payload.get("error_category", "storage_io")
    delivery = payload.get("delivery")
    if type(delivery) is dict:
        for key in ("delivery_id", "state", "attempt_count"):
            extra[key] = delivery.get(key)
        extra["attempt_id"] = delivery.get("current_attempt_id")
    items = payload.get("items")
    if type(items) is list:
        extra["delivery_count"] = len(items)
    logging.getLogger("card_market_tracker").log(
        logging.ERROR if code else logging.INFO, "", extra=extra
    )


def _report(
    payload: dict[str, object],
    operation: str,
    started: float,
    code: int,
    budget: Budget | None = None,
) -> int:
    try:
        output = json.dumps(
            payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        if len(output.encode("ascii")) + 1 > 1048576:
            raise DeliveryError("input_limit")
        if budget is not None and not code:
            budget.remaining()
    except DeliveryError as error:
        code = error.exit_code
        payload = {
            "version": 1,
            "operation": operation,
            "result": "error",
            "error_category": error.category,
        }
        output = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    except Exception:
        code = 1
        payload = {
            "version": 1,
            "operation": operation,
            "result": "error",
            "error_category": "storage_io",
        }
        output = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    try:
        sys.stdout.write(output + "\n")
    except (OSError, UnicodeError):
        code = 1
        payload = {"result": "error", "error_category": "storage_io"}
    _complete(payload, operation, started, code)
    return code


def invalid_arguments(started: float) -> int:
    return _report(
        {
            "version": 1,
            "operation": "watchlist-telegram-delivery",
            "result": "error",
            "error_category": "invalid_field",
        },
        "arguments",
        started,
        2,
    )


def help_completed(started: float) -> None:
    _complete({"result": "ok"}, "arguments", started, 0)


def _selected_manifest(args: argparse.Namespace, budget: Budget) -> object:
    return application._manifest_file(args.manifest, budget)


def _invoke(args: argparse.Namespace, budget: Budget) -> dict[str, object]:
    name: str = args.watchlist_delivery_operation
    path: Path = args.ledger_db
    timeout: float = args.timeout
    for value in vars(args).values():
        if isinstance(value, Path) and str(value) == "-":
            raise DeliveryError("invalid_field")
    budget.remaining()
    if name == "init":
        return application.initialize(path, timeout=timeout)
    if name == "destination-add":
        return application.destination_add(
            path,
            args.alias,
            args.bot_id,
            args.chat_id,
            operator_private_owned=args.operator_private_owned,
            timeout=timeout,
        )
    if name == "destination-validate":
        return application.destination_validate(path, args.alias, timeout=timeout)
    if name in ("review", "prepare"):
        manifest = _selected_manifest(args, budget)
        if name == "review":
            return application.review(
                path,
                args.watchlist_db,
                args.journal_db,
                args.outbox_db,
                manifest,
                args.alert_id,
                args.alias,
                timeout=timeout,
            )
        return application.prepare(
            path,
            args.watchlist_db,
            args.journal_db,
            args.outbox_db,
            manifest,
            args.alert_id,
            args.alias,
            acknowledgement=args.acknowledge_historical_demonstration,
            expected_signal_id=args.expected_signal_id,
            expected_revision=args.expected_revision,
            expected_message_sha256=args.expected_message_sha256,
            expected_evidence_sha256=args.expected_evidence_sha256,
            expected_route_sha256=args.expected_route_sha256,
            expected_binding_sha256=args.expected_binding_sha256,
            timeout=timeout,
        )
    if name == "send":
        # The wrapper performs no file I/O. Application quarantine/replay decides
        # before materializing any optional source or manifest.
        manifest = _selected_manifest(args, budget) if args.manifest is not None else None
        return application.send(
            path,
            args.delivery_id,
            watchlist_db=args.watchlist_db,
            journal_db=args.journal_db,
            outbox_db=args.outbox_db,
            manifest=manifest,
            timeout=timeout,
        )
    if name == "get":
        return application.get(path, args.delivery_id, timeout=timeout)
    if name == "list":
        return application.list_deliveries(
            path, state=args.state, limit=args.limit, cursor=args.cursor, timeout=timeout
        )
    if name == "verify":
        return application.verify(path, timeout=timeout)
    if name == "recompute":
        return application.recompute(
            path,
            args.watchlist_db,
            args.journal_db,
            args.outbox_db,
            _selected_manifest(args, budget),
            args.delivery_id,
            timeout=timeout,
        )
    if name == "recover":
        return application.recover(
            path, args.delivery_id, worker_quiesced=args.worker_quiesced, timeout=timeout
        )
    if name == "backup":
        return application.backup(path, args.destination, timeout=timeout)
    if name == "restore":
        return application.restore(path, args.destination, timeout=timeout)
    raise DeliveryError("invalid_field")


def dispatch(args: argparse.Namespace, started: float, *, started_monotonic: float) -> int:
    name: str = args.watchlist_delivery_operation
    token = None
    try:
        budget = Budget(
            args.timeout,
            30.0 if name in ("send", "destination-validate") else 5.0,
            started=started_monotonic,
        )
        budget.remaining()
        token = application._invocation_budget.set(budget)
        payload = _invoke(args, budget)
        code = 0
        if payload.get("result") == "error":
            category = payload.get("error_category")
            code = DeliveryError(category if type(category) is str else "storage_io").exit_code
        return _report(payload, name, started, code, budget)
    except DeliveryError as error:
        payload = {
            "version": 1,
            "operation": name,
            "result": "error",
            "error_category": error.category,
        }
        return _report(payload, name, started, error.exit_code)
    except Exception:
        return _report(
            {"version": 1, "operation": name, "result": "error", "error_category": "storage_io"},
            name,
            started,
            1,
        )
    finally:
        if token is not None:
            application._invocation_budget.reset(token)
