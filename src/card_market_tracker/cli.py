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
from card_market_tracker.catalog.manifest import parse_manifest
from card_market_tracker.catalog.resolver import resolve
from card_market_tracker.catalog.validation import CatalogError, read_json
from card_market_tracker.config import ConfigurationError, load_config
from card_market_tracker.logging_json import configure_logging


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


def main(argv: list[str] | None = None) -> int:
    started = time.perf_counter()
    run_id = str(uuid4())
    logger = configure_logging(run_id)
    try:
        args = _parser().parse_args(argv)
        if args.version:
            print(f"cmt {__version__}")
            logger.info("", extra={"event": "cli.version", "component": "cli"})
            return 0
        if args.command == "catalog":
            return _catalog(args.input, args.manifest, started)
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
