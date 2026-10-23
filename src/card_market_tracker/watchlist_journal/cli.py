"""Explicit one-shot journal commands with bounded output and redacted logs."""

from __future__ import annotations

import argparse
import json
import logging
import math
import time
from pathlib import Path
from typing import Any

from ..catalog.validation import CatalogError, read_json
from ..persistence.errors import PersistenceError
from ..watchlist.errors import WatchlistError
from . import application, storage
from .errors import WatchlistJournalError

OPERATIONS = (
    "init",
    "record",
    "get",
    "list",
    "signal-get",
    "signal-list",
    "verify",
    "recompute",
    "backup",
    "restore",
)


def register(commands: argparse._SubParsersAction[Any]) -> None:
    group = commands.add_parser("watchlist-journal")
    operations = group.add_subparsers(dest="watchlist_journal_operation", required=True)
    for name in OPERATIONS:
        parser = operations.add_parser(name)
        parser.add_argument("--journal-db", type=Path, required=True)
        parser.add_argument("--timeout", type=float, default=2.0)
        if name in ("record", "recompute"):
            parser.add_argument("--watchlist-db", type=Path, required=True)
            parser.add_argument("--manifest", type=Path, required=True)
        if name == "record":
            parser.add_argument("--watch-id", required=True)
            parser.add_argument("--revision", type=int, required=True)
            parser.add_argument("--sample", type=Path, required=True)
            parser.add_argument("--previous", type=Path)
            parser.add_argument("--as-of", required=True)
        if name in ("get", "recompute"):
            parser.add_argument("--evaluation-id", required=True)
        if name == "signal-get":
            parser.add_argument("--signal-id", required=True)
        if name in ("list", "signal-list"):
            parser.add_argument("--sequence-id")
            parser.add_argument("--watch-id")
            parser.add_argument("--revision", type=int)
            parser.add_argument("--limit", type=int, default=100)
            parser.add_argument("--cursor")
        if name == "signal-list":
            parser.add_argument("--rule", choices=("price", "restock"))
        if name in ("backup", "restore"):
            parser.add_argument("--destination", type=Path, required=True)


def _report(
    payload: dict[str, object],
    operation: str,
    started: float,
    code: int,
    *,
    deadline: float | None = None,
) -> int:
    output = json.dumps(
        {**payload, "operation": operation},
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    if len(output.encode("utf-8")) > 1024 * 1024:
        payload = {"version": 1, "result": "error", "error_category": "input_limit"}
        output = json.dumps({**payload, "operation": operation}, separators=(",", ":"))
        code = 2
    if deadline is not None and time.monotonic() >= deadline:
        payload = {"version": 1, "result": "error", "error_category": "storage_timeout"}
        output = json.dumps({**payload, "operation": operation}, separators=(",", ":"))
        code = 1
    extra: dict[str, object] = {
        "event": "watchlist.journal.completed",
        "component": "cli",
        "operation": "watchlist_journal_" + operation.replace("-", "_"),
        "result": "error" if code else "replay" if payload.get("result") == "replayed" else "ok",
        "duration_ms": max(0, round((time.perf_counter() - started) * 1000)),
    }
    if "error_category" in payload:
        extra["error_category"] = payload["error_category"]
    for source, target in (
        ("evaluations", "journal_evaluations_count"),
        ("signals", "journal_signals_count"),
    ):
        items = payload.get(source)
        if isinstance(items, list):
            extra[target] = len(items)
    if type(payload.get("signals_count")) is int:
        extra["journal_signals_count"] = payload["signals_count"]
    logging.getLogger("card_market_tracker").log(
        logging.ERROR if code else logging.INFO,
        "",
        extra=extra,
    )
    print(output)
    return code


def invalid_arguments(started: float) -> int:
    return _report(
        {"version": 1, "result": "error", "error_category": "invalid_field"},
        "arguments",
        started,
        2,
    )


def dispatch(args: argparse.Namespace, started: float) -> int:
    name: str = args.watchlist_journal_operation
    try:
        timeout: float = args.timeout
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 5:
            raise WatchlistJournalError("invalid_field")
        deadline = time.monotonic() + timeout - max(0, time.perf_counter() - started)

        def remaining() -> float:
            available = deadline - time.monotonic()
            if available <= 0:
                raise WatchlistJournalError("storage_timeout")
            return available

        path: Path = args.journal_db
        manifest = read_json(args.manifest) if name in ("record", "recompute") else None
        current = read_json(args.sample) if name == "record" else None
        previous = read_json(args.previous) if name == "record" and args.previous else None
        timeout = remaining()
        if name == "init":
            payload = storage.initialize(path, timeout=timeout)
        elif name == "record":
            payload = application.record(
                path,
                args.watchlist_db,
                manifest,
                args.watch_id,
                current,
                previous,
                revision=args.revision,
                as_of=args.as_of,
                timeout=timeout,
            )
        elif name == "recompute":
            payload = application.recompute(
                path,
                args.watchlist_db,
                manifest,
                args.evaluation_id,
                timeout=timeout,
            )
        elif name == "get":
            payload = storage.get(path, args.evaluation_id, timeout=timeout)
        elif name == "signal-get":
            payload = storage.signal_get(path, args.signal_id, timeout=timeout)
        elif name in ("list", "signal-list"):
            filters: dict[str, Any] = {
                "sequence_id": args.sequence_id,
                "watch_id": args.watch_id,
                "revision": args.revision,
                "limit": args.limit,
                "cursor": args.cursor,
                "timeout": timeout,
            }
            if name == "list":
                payload = storage.list_evaluations(path, **filters)
            else:
                payload = storage.signal_list(path, rule=args.rule, **filters)
        elif name == "verify":
            payload = storage.verify(path, timeout=timeout)
        elif name == "backup":
            payload = storage.backup(path, args.destination, timeout=timeout)
        elif name == "restore":
            payload = storage.restore(path, args.destination, timeout=timeout)
        else:
            raise WatchlistJournalError("invalid_field")
        remaining()
        return _report(payload, name, started, 0, deadline=deadline)
    except (WatchlistJournalError, WatchlistError, CatalogError, PersistenceError) as error:
        safe = WatchlistJournalError(error.category)
        category, code = safe.category, safe.exit_code
    except Exception:
        category, code = "storage_io", 1
    return _report(
        {"version": 1, "result": "error", "error_category": category},
        name,
        started,
        code,
    )
