"""Strict offline-outbox command group and redacted result logging."""

from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path
from typing import Any

from ..catalog.validation import CatalogError
from ..discovery.errors import DiscoveryError
from ..discovery.journal_errors import JournalError
from ..persistence.errors import PersistenceError
from . import storage
from .application import enqueue, recompute
from .errors import OutboxError

OPERATIONS = (
    "init",
    "enqueue",
    "get",
    "list",
    "evidence-list",
    "evidence-get",
    "preview",
    "verify",
    "recompute",
    "backup",
    "restore",
)


def register(commands: argparse._SubParsersAction[Any]) -> None:
    group = commands.add_parser("alert-outbox")
    operations = group.add_subparsers(dest="outbox_operation", required=True)
    for name in OPERATIONS:
        parser = operations.add_parser(name)
        parser.add_argument("--outbox-db", type=Path, required=True)
        parser.add_argument("--timeout", type=float, default=2.0)
        if name in ("enqueue", "recompute"):
            parser.add_argument("--captures-db", type=Path, required=True)
            parser.add_argument("--journal-db", type=Path, required=True)
        if name in ("enqueue", "evidence-get", "recompute"):
            parser.add_argument("--comparison-id", required=True)
        if name in ("get", "evidence-list", "evidence-get", "preview", "recompute"):
            parser.add_argument("--alert-id", required=True)
        if name in ("enqueue", "list"):
            parser.add_argument("--destination-key", required=name == "enqueue")
        if name in ("list", "evidence-list"):
            parser.add_argument("--limit", type=int, default=100)
            parser.add_argument("--cursor")
        if name in ("backup", "restore"):
            parser.add_argument("--destination", type=Path, required=True)


def _report(payload: dict[str, object], operation: str, started: float, code: int) -> int:
    extra: dict[str, object] = {
        "event": "alert.outbox.completed",
        "component": "cli",
        "operation": "alert_outbox_" + operation.replace("-", "_"),
        "result": payload["result"],
        "duration_ms": max(0, round((time.perf_counter() - started) * 1000)),
    }
    if "error_category" in payload:
        extra["error_category"] = payload["error_category"]
    counts = payload.get("counts")
    if isinstance(counts, dict):
        for key in ("alerts", "associations"):
            if key in counts:
                extra["outbox_" + key + "_count"] = counts[key]
    if "events" in payload:
        extra["outbox_events_count"] = payload["events"]
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
            "operation": "alert-outbox",
            "result": "error",
            "error_category": "invalid_field",
        },
        "arguments",
        started,
        2,
    )


def dispatch(args: argparse.Namespace, started: float) -> int:
    name: str = args.outbox_operation
    try:
        path, timeout = args.outbox_db, args.timeout
        if name == "init":
            payload = storage.initialize(path, timeout=timeout)
        elif name == "enqueue":
            payload = enqueue(
                args.captures_db,
                args.journal_db,
                path,
                args.comparison_id,
                args.destination_key,
                timeout=timeout,
            )
        elif name == "get":
            payload = storage.get(path, args.alert_id, timeout=timeout)
        elif name == "list":
            payload = storage.list_alerts(
                path,
                cursor=args.cursor,
                limit=args.limit,
                destination_key=args.destination_key,
                timeout=timeout,
            )
        elif name == "evidence-list":
            payload = storage.evidence_list(
                path, args.alert_id, cursor=args.cursor, limit=args.limit, timeout=timeout
            )
        elif name == "evidence-get":
            payload = storage.evidence_get(path, args.alert_id, args.comparison_id, timeout=timeout)
        elif name == "preview":
            payload = storage.preview(path, args.alert_id, timeout=timeout)
        elif name == "verify":
            payload = storage.verify(path, timeout=timeout)
        elif name == "recompute":
            payload = recompute(
                args.captures_db,
                args.journal_db,
                path,
                args.alert_id,
                args.comparison_id,
                timeout=timeout,
            )
        elif name == "backup":
            payload = storage.backup(path, args.destination, timeout=timeout)
        elif name == "restore":
            payload = storage.restore(path, args.destination, timeout=timeout)
        else:
            raise OutboxError("invalid_field")
        return _report(payload, name, started, 0)
    except (OutboxError, CatalogError, DiscoveryError, JournalError, PersistenceError) as error:
        safe = OutboxError(error.category)
    except Exception:
        safe = OutboxError("storage_io")
    return _report(
        {"version": 1, "operation": name, "result": "error", "error_category": safe.category},
        name,
        started,
        safe.exit_code,
    )
