"""One-shot local CLI; no network or market integrations."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import tempfile
import time
from pathlib import Path
from typing import Never
from uuid import uuid4

from card_market_tracker import __version__
from card_market_tracker.catalog.adapters.tcgdex import translate_batch
from card_market_tracker.catalog.manifest import parse_manifest, parse_reference
from card_market_tracker.catalog.resolver import resolve
from card_market_tracker.catalog.validation import CatalogError, read_json
from card_market_tracker.config import ConfigurationError, load_config
from card_market_tracker.logging_json import configure_logging
from card_market_tracker.persistence.errors import PersistenceError
from card_market_tracker.persistence.input import read_persistence
from card_market_tracker.persistence.sqlite_repository import (
    backup,
    initialize,
    persist,
    query,
    restore,
    verify,
)


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        del message
        raise ConfigurationError("arguments: invalid")


def _parser() -> _Parser:
    parser = _Parser(prog="cmt", add_help=True)
    parser.add_argument("--version", action="store_true")
    commands = parser.add_subparsers(dest="command", parser_class=_Parser)
    diagnose = commands.add_parser("diagnose")
    diagnose.add_argument("--env-file", type=Path)
    catalog = commands.add_parser("catalog")
    catalog.add_argument("--input", type=Path, required=True)
    catalog.add_argument("--manifest", type=Path, required=True)
    persistence = commands.add_parser("persist")
    persistence.add_argument("--db", type=Path, required=True)
    persistence.add_argument("--input", type=Path, required=True)
    persistence.add_argument("--manifest", type=Path, required=True)
    observations = commands.add_parser("observations")
    observations.add_argument("--db", type=Path, required=True)
    selector = observations.add_mutually_exclusive_group()
    selector.add_argument("--batch-id")
    selector.add_argument("--cmt-id")
    selector.add_argument("--candidate-reference", type=Path)
    observations.add_argument("--limit", type=int, default=100)
    database = commands.add_parser("db")
    operations = database.add_subparsers(dest="db_operation", required=True, parser_class=_Parser)
    for operation in ("init", "verify", "backup", "restore"):
        command = operations.add_parser(operation)
        command.add_argument("--db", type=Path, required=True)
        if operation in ("backup", "restore"):
            command.add_argument("--destination", type=Path, required=True)
    return parser


def _check_work_dir(path: Path) -> None:
    with tempfile.TemporaryFile(dir=path):
        pass


def _catalog(input_path: Path, manifest_path: Path, started: float) -> int:
    logger = logging.getLogger("card_market_tracker")
    try:
        manifest = parse_manifest(read_json(manifest_path))
        batch = resolve(translate_batch(read_json(input_path)), manifest)
        count = len(batch.records)
        outcome = "mixed" if batch.candidates or batch.rejected else "ok" if count else "empty"
        payload = batch.to_dict()
        payload["result"] = outcome
        metrics: dict[str, object] = {
            "input_count": count,
            "accepted_count": batch.accepted,
            "candidate_count": batch.candidates,
            "rejected_count": batch.rejected,
        }
        categories = sorted(
            {
                record.category
                for record in batch.records
                if record.status == "rejected" and record.category is not None
            }
        )
        if categories:
            metrics["error_category"] = categories[0]
        exit_code = 3 if outcome == "mixed" else 0
    except CatalogError as error:
        outcome = "error"
        payload = {
            "version": 1,
            "result": outcome,
            "error_category": error.category,
            "counts": None,
            "records": [],
            "entities": [],
        }
        metrics = {"error_category": error.category}
        exit_code = 2
    except Exception:
        outcome = "error"
        payload = {
            "version": 1,
            "result": outcome,
            "error_category": "local_execution",
            "counts": None,
            "records": [],
            "entities": [],
        }
        metrics = {"error_category": "local_execution"}
        exit_code = 1
    metrics.update(
        {
            "event": "catalog.completed",
            "component": "cli",
            "result": outcome,
            "duration_ms": max(0, round((time.perf_counter() - started) * 1000)),
        }
    )
    logger.log(logging.ERROR if exit_code else logging.INFO, "", extra=metrics)
    print(json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return exit_code


def _persistence_error(category: str) -> dict[str, object]:
    return {
        "version": 1,
        "result": "error",
        "error_category": category,
        "counts": None,
        "committed": None,
    }


def _report_persistence(
    payload: dict[str, object], operation: str, started: float, exit_code: int
) -> int:
    metrics: dict[str, object] = {
        "event": "persistence.completed",
        "operation": operation,
        "component": "cli",
        "result": payload["result"],
        "duration_ms": max(0, round((time.perf_counter() - started) * 1000)),
    }
    if "error_category" in payload:
        metrics["error_category"] = payload["error_category"]
    counts = payload.get("counts")
    if isinstance(counts, dict):
        for name, field in (
            ("input", "input_count"),
            ("accepted", "accepted_count"),
            ("candidates", "candidate_count"),
            ("rejected", "rejected_count"),
        ):
            metrics[field] = counts[name]
    committed = payload.get("committed")
    if isinstance(committed, dict):
        metrics["new_observation_count"] = committed["observations"]
        metrics["new_entity_count"] = committed["entities"]
        metrics["new_batch_count"] = 0 if payload["result"] == "replay" else 1
    records = payload.get("records")
    if operation == "read" and isinstance(records, list):
        metrics["observation_count"] = sum(
            isinstance(row, dict) and row.get("observation") is not None for row in records
        )
    logging.getLogger("card_market_tracker").log(
        logging.ERROR if exit_code else logging.INFO, "", extra=metrics
    )
    print(json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return exit_code


def _persistence(args: argparse.Namespace, started: float) -> int:
    operation = (
        "persist"
        if args.command == "persist"
        else "read"
        if args.command == "observations"
        else args.db_operation
    )
    try:
        if operation == "persist":
            batch = read_persistence(args.input, args.manifest)
            payload = persist(args.db, batch).to_dict()
        elif operation == "read":
            reference = (
                None
                if args.candidate_reference is None
                else parse_reference(read_json(args.candidate_reference))
            )
            payload = query(
                args.db,
                batch_id=args.batch_id,
                cmt_id=args.cmt_id,
                candidate_reference=reference,
                limit=args.limit,
            )
        elif operation == "init":
            payload = initialize(args.db)
        elif operation == "verify":
            payload = verify(args.db)
        elif operation == "backup":
            payload = backup(args.db, args.destination)
        else:
            payload = restore(args.db, args.destination)
        exit_code = 3 if payload["result"] == "mixed" else 0
    except PersistenceError as error:
        payload = _persistence_error(error.category)
        exit_code = error.exit_code
    except CatalogError as error:
        payload = _persistence_error(error.category)
        exit_code = 1 if error.category == "input_io" else 2
    except Exception:
        payload = _persistence_error("local_execution")
        exit_code = 1
    return _report_persistence(payload, operation, started, exit_code)


def main(argv: list[str] | None = None) -> int:
    started = time.perf_counter()
    run_id = str(uuid4())
    logger = configure_logging(run_id)
    actual_argv = sys.argv[1:] if argv is None else argv
    try:
        args = _parser().parse_args(actual_argv)
        if args.version:
            print(f"cmt {__version__}")
            logger.info("", extra={"event": "cli.version", "component": "cli"})
            return 0
        if args.command == "catalog":
            return _catalog(args.input, args.manifest, started)
        if args.command in ("persist", "observations", "db"):
            return _persistence(args, started)
        if args.command != "diagnose":
            raise ConfigurationError("arguments: expected diagnose or --version")
        config = load_config(env_file=args.env_file)
        logger.setLevel(config.log_level)
        _check_work_dir(config.work_dir)
        duration = max(0, round((time.perf_counter() - started) * 1000))
        logger.info(
            "",
            extra={
                "event": "diagnose.completed",
                "component": "cli",
                "result": "ok",
                "duration_ms": duration,
            },
        )
        print("diagnose: ok (configuration, local work directory)")
        return 0
    except ConfigurationError:
        if actual_argv and actual_argv[0] in ("persist", "observations", "db"):
            operation = {"persist": "persist", "observations": "read", "db": "init"}[actual_argv[0]]
            if (
                actual_argv[0] == "db"
                and len(actual_argv) > 1
                and actual_argv[1] in ("init", "verify", "backup", "restore")
            ):
                operation = actual_argv[1]
            return _report_persistence(_persistence_error("invalid_field"), operation, started, 2)
        logger.error(
            "",
            extra={
                "event": "config.invalid",
                "component": "cli",
                "error_category": "configuration",
            },
        )
        return 2
    except Exception:
        logger.error(
            "",
            extra={
                "event": "diagnose.completed",
                "component": "cli",
                "result": "error",
                "duration_ms": max(0, round((time.perf_counter() - started) * 1000)),
                "error_category": "local_execution",
            },
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
