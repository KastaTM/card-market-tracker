"""Explicit one-shot watchlist commands and redacted completion logging."""

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
from . import application, storage
from .errors import WatchlistError

OPERATIONS = (
    "init",
    "add",
    "get",
    "list",
    "update",
    "enable",
    "disable",
    "history",
    "evaluate",
    "verify",
    "backup",
    "restore",
)


def register(commands: argparse._SubParsersAction[Any]) -> None:
    group = commands.add_parser("watchlist")
    operations = group.add_subparsers(dest="watchlist_operation", required=True)
    for name in OPERATIONS:
        parser = operations.add_parser(name)
        parser.add_argument("--watchlist-db", type=Path, required=True)
        parser.add_argument("--timeout", type=float, default=2.0)
        if name in ("add", "update", "enable", "disable", "evaluate"):
            parser.add_argument("--manifest", type=Path, required=True)
        if name == "add":
            parser.add_argument("--cmt-id", required=True)
        if name in ("add", "update"):
            parser.add_argument("--input", type=Path, required=True)
        if name in ("get", "update", "enable", "disable", "history", "evaluate"):
            parser.add_argument("--watch-id", required=True)
        if name in ("update", "enable", "disable"):
            parser.add_argument("--expected-revision", type=int, required=True)
        if name in ("add", "update", "enable", "disable"):
            parser.add_argument("--request-token", required=True)
        if name == "evaluate":
            parser.add_argument("--revision", type=int, required=True)
            parser.add_argument("--sample", type=Path, required=True)
            parser.add_argument("--previous", type=Path)
            parser.add_argument("--as-of", required=True)
        if name in ("list", "history"):
            parser.add_argument("--limit", type=int, default=100)
            parser.add_argument("--cursor")
        if name == "list":
            parser.add_argument("--priority", choices=("high", "normal", "low"))
            parser.add_argument("--enabled", choices=("true", "false"))
        if name in ("backup", "restore"):
            parser.add_argument("--destination", type=Path, required=True)


def _report(payload: dict[str, object], operation: str, started: float, code: int) -> int:
    extra: dict[str, object] = {
        "event": "watchlist.completed",
        "component": "cli",
        "operation": "watchlist_" + operation,
        "result": "error" if code else "replay" if payload.get("replayed") else "ok",
        "duration_ms": max(0, round((time.perf_counter() - started) * 1000)),
    }
    if "error_category" in payload:
        extra["error_category"] = payload["error_category"]
    entries = payload.get("entries")
    if isinstance(entries, list):
        extra["watchlist_entries_count"] = len(entries)
    logging.getLogger("card_market_tracker").log(
        logging.ERROR if code else logging.INFO, "", extra=extra
    )
    print(
        json.dumps(
            {**payload, "operation": operation},
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    )
    return code


def invalid_arguments(started: float) -> int:
    return _report(
        {"version": 1, "result": "error", "error_category": "invalid_field"},
        "arguments",
        started,
        2,
    )


def dispatch(args: argparse.Namespace, started: float) -> int:
    name: str = args.watchlist_operation
    try:
        path: Path = args.watchlist_db
        timeout: float = args.timeout
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 5:
            raise WatchlistError("invalid_field")
        deadline = time.monotonic() + timeout

        def remaining() -> float:
            available = deadline - time.monotonic()
            if available <= 0:
                raise WatchlistError("storage_timeout")
            return available

        manifest = (
            read_json(args.manifest)
            if name in ("add", "update", "enable", "disable", "evaluate")
            else None
        )
        config = read_json(args.input) if name in ("add", "update") else None
        current = read_json(args.sample) if name == "evaluate" else None
        previous = read_json(args.previous) if name == "evaluate" and args.previous else None
        timeout = remaining()
        if name == "init":
            payload = storage.initialize(path, timeout=timeout)
        elif name == "add":
            payload = application.add(
                path,
                manifest,
                args.cmt_id,
                config,
                request_token=args.request_token,
                timeout=timeout,
            )
        elif name in ("update", "enable", "disable"):
            payload = application.update(
                path,
                manifest,
                args.watch_id,
                config,
                expected_revision=args.expected_revision,
                request_token=args.request_token,
                action=name,
                timeout=timeout,
            )
        elif name == "get":
            payload = storage.get(path, args.watch_id, timeout=timeout)
        elif name == "list":
            enabled = None if args.enabled is None else args.enabled == "true"
            payload = storage.list_entries(
                path,
                priority=args.priority,
                enabled=enabled,
                cursor=args.cursor,
                limit=args.limit,
                timeout=timeout,
            )
        elif name == "history":
            payload = storage.history(
                path, args.watch_id, cursor=args.cursor, limit=args.limit, timeout=timeout
            )
        elif name == "evaluate":
            payload = application.evaluate(
                path,
                manifest,
                args.watch_id,
                current,
                previous,
                revision=args.revision,
                as_of=args.as_of,
                timeout=timeout,
            )
        elif name == "verify":
            payload = storage.verify(path, timeout=timeout)
        elif name == "backup":
            payload = storage.backup(path, args.destination, timeout=timeout)
        elif name == "restore":
            payload = storage.restore(path, args.destination, timeout=timeout)
        else:
            raise WatchlistError("invalid_field")
        return _report(payload, name, started, 0)
    except (WatchlistError, CatalogError, PersistenceError) as error:
        safe = WatchlistError(error.category)
    except Exception:
        safe = WatchlistError("storage_io")
    return _report(
        {"version": 1, "result": "error", "error_category": safe.category},
        name,
        started,
        safe.exit_code,
    )
