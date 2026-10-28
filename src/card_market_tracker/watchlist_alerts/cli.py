"""Strict one-shot Watchlist preview CLI with a shared command deadline."""

from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path
from typing import Any

from ..catalog.validation import CatalogError
from ..persistence.errors import PersistenceError
from ..watchlist.errors import WatchlistError
from ..watchlist.validation import read_json
from ..watchlist_journal.errors import JournalError
from ..watchlist_journal.storage import Budget
from . import application, storage
from .errors import OutboxError

OPERATIONS = (
    "init",
    "enqueue",
    "get",
    "list",
    "evidence-get",
    "preview",
    "verify",
    "recompute",
    "backup",
    "restore",
)


def register(commands: argparse._SubParsersAction[Any]) -> None:
    group = commands.add_parser("watchlist-alert-outbox", allow_abbrev=False)
    operations = group.add_subparsers(dest="watchlist_alert_operation", required=True)
    for name in OPERATIONS:
        parser = operations.add_parser(name, allow_abbrev=False)
        parser.add_argument("--outbox-db", type=Path, required=True)
        parser.add_argument("--timeout", type=float, default=2.0)
        if name in ("enqueue", "recompute"):
            parser.add_argument("--watchlist-db", type=Path, required=True)
            parser.add_argument("--journal-db", type=Path, required=True)
            parser.add_argument("--manifest", type=Path, required=True)
        if name == "enqueue":
            parser.add_argument("--signal-id", required=True)
            parser.add_argument("--destination-key", required=True)
        if name in ("get", "evidence-get", "preview", "recompute"):
            parser.add_argument("--alert-id", required=True)
        if name == "list":
            parser.add_argument("--destination-key")
            parser.add_argument("--limit", type=int, default=100)
            parser.add_argument("--cursor")
        if name in ("backup", "restore"):
            parser.add_argument("--destination", type=Path, required=True)


def _report(
    payload: dict[str, object],
    operation: str,
    started: float,
    code: int,
    *,
    budget: Budget | None = None,
) -> int:
    try:
        output = json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        if len(output.encode("ascii")) + 1 > 1048576:
            raise OutboxError("input_limit")
        if budget is not None:
            budget.remaining()
    except (OutboxError, JournalError) as error:
        safe = OutboxError(error.category)
        code = safe.exit_code
        payload = {
            "version": 1,
            "operation": operation,
            "result": "error",
            "error_category": safe.category,
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
        output = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    extra: dict[str, object] = {
        "event": "watchlist.alert_outbox.completed",
        "component": "cli",
        "operation": "watchlist_alert_outbox_" + operation.replace("-", "_"),
        "result": "error" if code else "replay" if payload.get("result") == "replayed" else "ok",
        "duration_ms": max(0, round((time.perf_counter() - started) * 1000)),
    }
    if code:
        extra["error_category"] = payload["error_category"]
    else:
        counts = payload.get("counts")
        if isinstance(counts, dict):
            for key, field in (
                ("alerts", "watchlist_alerts_count"),
                ("evidence", "watchlist_alert_evidence_count"),
            ):
                extra[field] = counts.get(key)
        items = payload.get("items")
        if isinstance(items, list):
            extra["watchlist_alerts_count"] = len(items)
    # The deadline cutoff is the first stdout byte. Completion logging follows
    # the response and cannot retroactively change an already emitted outcome.
    if budget is not None and not code:
        try:
            budget.remaining()
        except (OutboxError, JournalError) as error:
            safe = OutboxError(error.category)
            return _report(
                {
                    "version": 1,
                    "operation": operation,
                    "result": "error",
                    "error_category": safe.category,
                },
                operation,
                started,
                safe.exit_code,
            )
    print(output)
    logging.getLogger("card_market_tracker").log(
        logging.ERROR if code else logging.INFO,
        "",
        extra=extra,
    )
    return code


def invalid_arguments(started: float) -> int:
    return _report(
        {
            "version": 1,
            "operation": "watchlist-alert-outbox",
            "result": "error",
            "error_category": "invalid_field",
        },
        "arguments",
        started,
        2,
    )


def dispatch(
    args: argparse.Namespace,
    started: float,
    *,
    started_monotonic: float,
) -> int:
    name: str = args.watchlist_alert_operation
    try:
        budget = Budget(args.timeout)
        budget.deadline = started_monotonic + args.timeout
        budget.remaining()
        path: Path = args.outbox_db
        manifest = read_json(args.manifest) if name in ("enqueue", "recompute") else None
        budget.remaining()
        if name == "init":
            payload = storage.initialize(path, _budget=budget)
        elif name == "enqueue":
            payload = application.enqueue(
                path,
                args.watchlist_db,
                args.journal_db,
                manifest,
                args.signal_id,
                args.destination_key,
                _budget=budget,
            )
        elif name == "recompute":
            payload = application.recompute(
                path,
                args.watchlist_db,
                args.journal_db,
                manifest,
                args.alert_id,
                _budget=budget,
            )
        elif name == "get":
            payload = storage.get(path, args.alert_id, _budget=budget)
        elif name == "list":
            payload = storage.list_alerts(
                path,
                destination_key=args.destination_key,
                limit=args.limit,
                cursor=args.cursor,
                _budget=budget,
            )
        elif name == "evidence-get":
            payload = storage.evidence_get(path, args.alert_id, _budget=budget)
        elif name == "preview":
            payload = storage.preview(path, args.alert_id, _budget=budget)
        elif name == "verify":
            payload = storage.verify(path, _budget=budget)
        elif name == "backup":
            payload = storage.backup(path, args.destination, _budget=budget)
        elif name == "restore":
            payload = storage.restore(path, args.destination, _budget=budget)
        else:
            raise OutboxError("invalid_field")
        return _report(payload, name, started, 0, budget=budget)
    except (OutboxError, JournalError, WatchlistError, CatalogError, PersistenceError) as error:
        safe = OutboxError(error.category)
        category, code = safe.category, safe.exit_code
    except Exception:
        category, code = "storage_io", 1
    return _report(
        {"version": 1, "operation": name, "result": "error", "error_category": category},
        name,
        started,
        code,
    )
