"""One-shot local CLI; no network or market integrations."""

from __future__ import annotations

import argparse
import sys
import tempfile
import time
from pathlib import Path
from typing import Never
from uuid import uuid4

from card_market_tracker import __version__
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
    return parser


def _check_work_dir(path: Path) -> None:
    with tempfile.TemporaryFile(dir=path):
        pass


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
