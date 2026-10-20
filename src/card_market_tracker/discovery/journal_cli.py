"""Separate journal command group, with fixed redacted responses and logs."""

from __future__ import annotations

import argparse
import json
import logging
import time
from pathlib import Path
from typing import Any

from ..catalog.validation import CatalogError
from ..persistence.errors import PersistenceError
from . import journal_storage as storage
from .errors import DiscoveryError
from .journal_application import recompute, record
from .journal_errors import JournalError

OPERATIONS = (
    "init",
    "record",
    "get",
    "list",
    "event-occurrences",
    "verify",
    "recompute",
    "backup",
    "restore",
)


def register(commands: argparse._SubParsersAction[Any]) -> None:
    group = commands.add_parser("discovery-journal")
    operations = group.add_subparsers(dest="journal_operation", required=True)
    for name in OPERATIONS:
        parser = operations.add_parser(name)
        parser.add_argument("--journal-db", type=Path, required=True)
        parser.add_argument("--timeout", type=float, default=2.0)
        if name in ("record", "recompute"):
            parser.add_argument("--captures-db", type=Path, required=True)
        if name == "record":
            parser.add_argument("--request", type=Path, required=True)
        if name in ("get", "recompute"):
            parser.add_argument("--comparison-id", required=True)
        if name == "event-occurrences":
            parser.add_argument("--event-id", required=True)
        if name in ("list", "event-occurrences"):
            parser.add_argument("--limit", type=int, default=100)
            parser.add_argument("--cursor")
        if name in ("backup", "restore"):
            parser.add_argument("--destination", type=Path, required=True)


def _report(payload: dict[str, object], operation: str, started: float, code: int) -> int:
    extra: dict[str, object] = {
        "event": "discovery.journal.completed",
        "component": "cli",
        "operation": "discovery_journal_" + operation.replace("-", "_"),
        "result": payload["result"],
        "duration_ms": max(0, round((time.perf_counter() - started) * 1000)),
    }
    if "error_category" in payload:
        extra["error_category"] = payload["error_category"]
    counts = payload.get("counts")
    if isinstance(counts, dict):
        for key in ("comparisons", "occurrences"):
            extra["journal_" + key + "_count"] = counts.get(key)
    logging.getLogger("card_market_tracker").log(
        logging.ERROR if code else logging.INFO, "", extra=extra
    )
    print(json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return code


def invalid_arguments(started: float) -> int:
    return _report(
        {
            "version": 1,
            "operation": "discovery-journal",
            "result": "error",
            "error_category": "invalid_field",
        },
        "arguments",
        started,
        2,
    )


def dispatch(args: argparse.Namespace, started: float) -> int:
    name: str = args.journal_operation
    try:
        journal, timeout = args.journal_db, args.timeout
        if name == "init":
            payload = storage.initialize(journal, timeout=timeout)
        elif name == "record":
            payload = record(args.captures_db, journal, args.request, timeout=timeout)
        elif name == "get":
            payload = storage.get(journal, args.comparison_id, timeout=timeout)
        elif name == "list":
            payload = storage.list_comparisons(
                journal, cursor=args.cursor, limit=args.limit, timeout=timeout
            )
        elif name == "event-occurrences":
            payload = storage.event_occurrences(
                journal, args.event_id, cursor=args.cursor, limit=args.limit, timeout=timeout
            )
        elif name == "verify":
            payload = storage.verify(journal, timeout=timeout)
        elif name == "recompute":
            payload = recompute(args.captures_db, journal, args.comparison_id, timeout=timeout)
        elif name == "backup":
            payload = storage.backup(journal, args.destination, timeout=timeout)
        elif name == "restore":
            payload = storage.restore(journal, args.destination, timeout=timeout)
        else:
            raise JournalError("invalid_field")
        return _report(payload, name, started, 0)
    except (JournalError, CatalogError, DiscoveryError, PersistenceError) as error:
        safe = JournalError(error.category)
    except Exception:
        safe = JournalError("storage_io")
    return _report(
        {
            "version": 1,
            "operation": name,
            "result": "error",
            "error_category": safe.category,
        },
        name,
        started,
        safe.exit_code,
    )
