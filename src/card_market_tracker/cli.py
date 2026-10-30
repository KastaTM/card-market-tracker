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
from card_market_tracker.alerts import cli as outbox_cli
from card_market_tracker.catalog.adapters.tcgdex import translate_batch
from card_market_tracker.catalog.manifest import parse_manifest, parse_reference
from card_market_tracker.catalog.resolver import resolve
from card_market_tracker.catalog.validation import CatalogError, read_json
from card_market_tracker.config import ConfigurationError, load_config
from card_market_tracker.discovery import journal_cli
from card_market_tracker.discovery.comparison import compare
from card_market_tracker.discovery.errors import DiscoveryError
from card_market_tracker.discovery.input import read_request
from card_market_tracker.discovery.scoped_comparison import compare as compare_scoped
from card_market_tracker.discovery.scoped_input import read_request as read_scoped_request
from card_market_tracker.logging_json import configure_logging
from card_market_tracker.persistence.errors import PersistenceError
from card_market_tracker.persistence.input import read_persistence
from card_market_tracker.persistence.sqlite_repository import (
    backup,
    initialize,
    persist,
    query,
    read_snapshots,
    restore,
    verify,
)
from card_market_tracker.watchlist import cli as watchlist_cli
from card_market_tracker.watchlist_journal import cli as watchlist_journal_cli


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> Never:
        del message
        raise ConfigurationError("arguments: invalid")


def _parser(
    *,
    watchlist_alert_only: bool = False,
    watchlist_delivery_only: bool = False,
    telegram_selected: bool = False,
) -> _Parser:
    parser = _Parser(prog="cmt", add_help=True)
    parser.add_argument("--version", action="store_true")
    commands = parser.add_subparsers(dest="command", parser_class=_Parser)
    if watchlist_delivery_only:
        from card_market_tracker.watchlist_delivery import cli as watchlist_delivery_cli

        watchlist_delivery_cli.register(commands)
        return parser
    if watchlist_alert_only:
        from card_market_tracker.watchlist_alerts import cli as watchlist_alert_cli

        watchlist_alert_cli.register(commands)
        return parser
    diagnose = commands.add_parser("diagnose")
    diagnose.add_argument("--env-file", type=Path)
    catalog = commands.add_parser("catalog")
    catalog.add_argument("--input", type=Path, required=True)
    catalog.add_argument("--manifest", type=Path, required=True)
    scoped = commands.add_parser("discover-scoped")
    scoped.add_argument("--db", type=Path, required=True)
    scoped.add_argument("--request", type=Path, required=True)
    multi = commands.add_parser("discover-multi-revision")
    multi.add_argument("--db", type=Path, required=True)
    multi.add_argument("--request", type=Path, required=True)
    discover = commands.add_parser("discover")
    discover.add_argument("--db", type=Path, required=True)
    discover.add_argument("--request", type=Path, required=True)
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
    bundle = commands.add_parser("bundle")
    bundle_operations = bundle.add_subparsers(
        dest="bundle_operation", required=True, parser_class=_Parser
    )
    for operation in ("verify", "import"):
        command = bundle_operations.add_parser(operation)
        command.add_argument("--input", type=Path, required=True)
        if operation == "import":
            command.add_argument("--db", type=Path, required=True)
            command.add_argument("--manifest", type=Path, required=True)
            command.add_argument("--batch-id", required=True)
    bundle_v2 = commands.add_parser("bundle-v2")
    multi_operations = bundle_v2.add_subparsers(
        dest="bundle_operation", required=True, parser_class=_Parser
    )
    for operation in ("verify", "import"):
        command = multi_operations.add_parser(operation)
        command.add_argument("--input", type=Path, required=True)
        if operation == "import":
            command.add_argument("--db", type=Path, required=True)
            command.add_argument("--manifest", type=Path, required=True)
            command.add_argument("--batch-id", required=True)
    captures = commands.add_parser("captures")
    captures.add_argument("--db", type=Path, required=True)
    captures.add_argument("--batch-id", required=True)
    database = commands.add_parser("db")
    operations = database.add_subparsers(dest="db_operation", required=True, parser_class=_Parser)
    for operation in ("init", "verify", "backup", "restore", "migrate"):
        command = operations.add_parser(operation)
        command.add_argument("--db", type=Path, required=True)
        if operation in ("backup", "restore", "migrate"):
            command.add_argument("--destination", type=Path, required=True)
    journal_cli.register(commands)
    outbox_cli.register(commands)
    from card_market_tracker.watchlist_alerts import cli as watchlist_alert_cli
    from card_market_tracker.watchlist_delivery import cli as watchlist_delivery_cli

    if telegram_selected:
        from card_market_tracker.telegram_delivery import cli as telegram_cli

        telegram_cli.register(commands)
    else:
        # Root help and unrelated offline routes need only this group name.
        commands.add_parser("telegram-delivery")
    watchlist_cli.register(commands)
    watchlist_journal_cli.register(commands)
    watchlist_alert_cli.register(commands)
    watchlist_delivery_cli.register(commands)
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


def _discovery_error(category: str) -> dict[str, object]:
    return {
        "version": 1,
        "result": "error",
        "error_category": category,
        "counts": None,
        "events": [],
    }


def _report_discovery(payload: dict[str, object], started: float, exit_code: int) -> int:
    metrics: dict[str, object] = {
        "event": "discovery.completed",
        "component": "cli",
        "result": payload["result"],
        "duration_ms": max(0, round((time.perf_counter() - started) * 1000)),
    }
    if "error_category" in payload:
        metrics["error_category"] = payload["error_category"]
    counts = payload.get("counts")
    if isinstance(counts, dict):
        metrics.update(
            {
                "batch_count": counts["batches"],
                "discovery_observation_count": counts["observations"],
                "event_count": counts["events"],
            }
        )
    logging.getLogger("card_market_tracker").log(
        logging.ERROR if exit_code else logging.INFO, "", extra=metrics
    )
    print(json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return exit_code


def _discover(database: Path, request_path: Path, started: float) -> int:
    try:
        request = read_request(request_path)
        snapshots = read_snapshots(database, (request.current_batch_id, *request.history_batch_ids))
        payload = compare(request, snapshots).to_dict()
        exit_code = 0
    except DiscoveryError as error:
        payload = _discovery_error(error.category)
        exit_code = error.exit_code
    except PersistenceError as error:
        payload = _discovery_error(error.category)
        exit_code = error.exit_code
    except CatalogError as error:
        payload = _discovery_error(error.category)
        exit_code = 2
    except Exception:
        payload = _discovery_error("local_execution")
        exit_code = 1
    return _report_discovery(payload, started, exit_code)


def _scoped_error(category: str) -> dict[str, object]:
    return {
        "version": 2,
        "result": "error",
        "error_category": category,
        "counts": None,
        "events": [],
    }


def _report_scoped(payload: dict[str, object], started: float, exit_code: int) -> int:
    multi = payload["version"] == 3
    metrics: dict[str, object] = {
        "event": "discovery.multi.completed" if multi else "discovery.scoped.completed",
        "component": "cli",
        "operation": "discover_multi_revision" if multi else "discover_scoped",
        "result": payload["result"],
        "duration_ms": max(0, round((time.perf_counter() - started) * 1000)),
    }
    if "error_category" in payload:
        metrics["error_category"] = payload["error_category"]
    counts = payload.get("counts")
    if isinstance(counts, dict):
        metrics.update(
            {
                "batch_count": counts["validated_batches"],
                "scoped_validated_record_count": counts["validated_records"],
                "scoped_selected_record_count": counts["current_selected_records"]
                + counts["historical_selected_records"],
                "event_count": counts["events"],
            }
        )
    logging.getLogger("card_market_tracker").log(
        logging.ERROR if exit_code else logging.INFO, "", extra=metrics
    )
    print(json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
    return exit_code


def _discover_scoped(database: Path, request_path: Path, started: float) -> int:
    from card_market_tracker.persistence.sqlite_repository import read_scoped_snapshots

    try:
        request = read_scoped_request(request_path)
        payload = compare_scoped(request, read_scoped_snapshots(database, request)).to_dict()
        exit_code = 0
    except (DiscoveryError, PersistenceError) as error:
        payload, exit_code = _scoped_error(error.category), error.exit_code
    except CatalogError as error:
        payload, exit_code = _scoped_error(error.category), 2
    except Exception:
        payload, exit_code = _scoped_error("local_execution"), 1
    return _report_scoped(payload, started, exit_code)


def _discover_multi(database: Path, request_path: Path, started: float) -> int:
    from card_market_tracker.discovery.multi_comparison import compare as compare_multi
    from card_market_tracker.discovery.multi_input import read_request as read_multi
    from card_market_tracker.persistence.sqlite_repository import read_multi_revision_snapshots

    try:
        request = read_multi(request_path)
        payload = compare_multi(request, read_multi_revision_snapshots(database, request)).to_dict()
        exit_code = 0
    except (DiscoveryError, PersistenceError) as error:
        payload, exit_code = _scoped_error(error.category), error.exit_code
    except CatalogError as error:
        payload, exit_code = _scoped_error(error.category), 2
    except Exception:
        payload, exit_code = _scoped_error("local_execution"), 1
    payload["version"] = 3
    return _report_scoped(payload, started, exit_code)


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
        elif operation == "migrate":
            from card_market_tracker.persistence.sqlite_repository import migrate

            payload = migrate(args.db, args.destination)
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


def _pinned(args: argparse.Namespace, started: float) -> int:
    from card_market_tracker.persistence.capture import persist_bundle, query_capture
    from card_market_tracker.pinned_repository import BundleError, validate_bundle

    operation = "capture_read" if args.command == "captures" else "bundle_" + args.bundle_operation
    try:
        if args.command == "captures":
            payload = query_capture(args.db, args.batch_id)
        else:
            bundle = validate_bundle(read_json(args.input))
            if args.bundle_operation == "verify":
                payload = {"version": 1, "result": "ok", "evidence": "verified_local_pinned_bundle"}
            else:
                manifest = parse_manifest(read_json(args.manifest))
                payload = persist_bundle(args.db, bundle, args.batch_id, manifest).to_dict()
        exit_code = 3 if payload["result"] == "mixed" else 0
    except BundleError as error:
        payload = _persistence_error(error.category)
        exit_code = 1 if error.category == "approved_package_io" else 2
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


def _pinned_multi(args: argparse.Namespace, started: float) -> int:
    from card_market_tracker.persistence.capture import persist_bundle_v2
    from card_market_tracker.pinned_repository.bundle_v2 import validate_bundle_v2
    from card_market_tracker.pinned_repository.errors import BundleError

    operation = "bundle_v2_" + args.bundle_operation
    try:
        bundle = validate_bundle_v2(read_json(args.input))
        if args.bundle_operation == "verify":
            payload = {"version": 2, "result": "ok", "evidence": "verified_local_pinned_bundle"}
        else:
            manifest = parse_manifest(read_json(args.manifest))
            payload = persist_bundle_v2(args.db, bundle, args.batch_id, manifest).to_dict()
        exit_code = 3 if payload["result"] == "mixed" else 0
    except BundleError as error:
        payload = _persistence_error(error.category)
        exit_code = 1 if error.category == "approved_package_io" else 2
    except PersistenceError as error:
        payload, exit_code = _persistence_error(error.category), error.exit_code
    except CatalogError as error:
        payload = _persistence_error(error.category)
        exit_code = 1 if error.category == "input_io" else 2
    except Exception:
        payload, exit_code = _persistence_error("local_execution"), 1
    payload["version"] = 2
    return _report_persistence(payload, operation, started, exit_code)


def main(argv: list[str] | None = None) -> int:
    started_monotonic = time.monotonic()
    started = time.perf_counter()
    run_id = str(uuid4())
    logger = configure_logging(run_id)
    actual_argv = sys.argv[1:] if argv is None else argv
    try:
        selected = next((value for value in actual_argv if value != "--version"), None)
        try:
            args = _parser(
                watchlist_alert_only=selected == "watchlist-alert-outbox",
                watchlist_delivery_only=selected == "watchlist-telegram-delivery",
                telegram_selected=selected == "telegram-delivery",
            ).parse_args(actual_argv)
        except SystemExit as error:
            if selected == "watchlist-telegram-delivery" and error.code == 0:
                from card_market_tracker.watchlist_delivery import cli as watchlist_delivery_cli

                watchlist_delivery_cli.help_completed(started)
                return 0
            raise
        if args.version:
            print(f"cmt {__version__}")
            logger.info("", extra={"event": "cli.version", "component": "cli"})
            return 0
        if args.command == "watchlist-telegram-delivery":
            from card_market_tracker.watchlist_delivery import cli as watchlist_delivery_cli

            return watchlist_delivery_cli.dispatch(
                args, started, started_monotonic=started_monotonic
            )
        if args.command == "watchlist-alert-outbox":
            from card_market_tracker.watchlist_alerts import cli as watchlist_alert_cli

            return watchlist_alert_cli.dispatch(args, started, started_monotonic=started_monotonic)
        if args.command == "catalog":
            return _catalog(args.input, args.manifest, started)
        if args.command == "discovery-journal":
            return journal_cli.dispatch(args, started)
        if args.command == "alert-outbox":
            return outbox_cli.dispatch(args, started)
        if args.command == "telegram-delivery":
            from card_market_tracker.telegram_delivery import cli as telegram_cli

            return telegram_cli.dispatch(args, started)
        if args.command == "watchlist":
            return watchlist_cli.dispatch(args, started)
        if args.command == "watchlist-journal":
            return watchlist_journal_cli.dispatch(args, started)
        if args.command == "discover-scoped":
            return _discover_scoped(args.db, args.request, started)
        if args.command == "discover-multi-revision":
            return _discover_multi(args.db, args.request, started)
        if args.command == "discover":
            return _discover(args.db, args.request, started)
        if args.command in ("bundle", "captures"):
            return _pinned(args, started)
        if args.command == "bundle-v2":
            return _pinned_multi(args, started)
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
        selected = next((value for value in actual_argv if value != "--version"), None)
        if selected == "watchlist-telegram-delivery":
            from card_market_tracker.watchlist_delivery import cli as watchlist_delivery_cli

            return watchlist_delivery_cli.invalid_arguments(started)
        if selected == "watchlist-alert-outbox":
            from card_market_tracker.watchlist_alerts import cli as watchlist_alert_cli

            return watchlist_alert_cli.invalid_arguments(started)
        if actual_argv and actual_argv[0] == "watchlist-journal":
            return watchlist_journal_cli.invalid_arguments(started)
        if actual_argv and actual_argv[0] == "watchlist":
            return watchlist_cli.invalid_arguments(started)
        if actual_argv and actual_argv[0] == "telegram-delivery":
            from card_market_tracker.telegram_delivery import cli as telegram_cli

            return telegram_cli.invalid_arguments(started)
        if actual_argv and actual_argv[0] == "alert-outbox":
            return outbox_cli.invalid_arguments(started)
        if actual_argv and actual_argv[0] == "discovery-journal":
            return journal_cli.invalid_arguments(started)
        if actual_argv and actual_argv[0] == "discover-multi-revision":
            return _report_scoped({**_scoped_error("invalid_field"), "version": 3}, started, 2)
        if actual_argv and actual_argv[0] == "bundle-v2":
            operation = (
                "bundle_v2_import"
                if len(actual_argv) > 1 and actual_argv[1] == "import"
                else "bundle_v2_verify"
            )
            return _report_persistence(
                {**_persistence_error("invalid_field"), "version": 2}, operation, started, 2
            )
        if actual_argv and actual_argv[0] == "discover-scoped":
            return _report_scoped(_scoped_error("invalid_field"), started, 2)
        if actual_argv and actual_argv[0] == "discover":
            return _report_discovery(_discovery_error("invalid_field"), started, 2)
        if actual_argv and actual_argv[0] in (
            "persist",
            "observations",
            "db",
            "bundle",
            "captures",
        ):
            operation = {
                "persist": "persist",
                "observations": "read",
                "db": "init",
                "bundle": "bundle_verify",
                "captures": "capture_read",
            }[actual_argv[0]]
            if actual_argv[0] == "bundle" and len(actual_argv) > 1 and actual_argv[1] == "import":
                operation = "bundle_import"
            if (
                actual_argv[0] == "db"
                and len(actual_argv) > 1
                and actual_argv[1] in ("init", "verify", "backup", "restore", "migrate")
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
