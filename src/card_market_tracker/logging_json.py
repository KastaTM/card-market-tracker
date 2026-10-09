"""Structured logging contract v1: only allowlisted fields leave the process."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from uuid import UUID, uuid4

_LOGGER_NAME = "card_market_tracker"
_EVENTS = frozenset({"cli.version", "diagnose.completed", "config.invalid", "catalog.completed"})


class JsonFormatter(logging.Formatter):
    def __init__(self, run_id: str) -> None:
        super().__init__()
        self.run_id = run_id

    def format(self, record: logging.LogRecord) -> str:
        event = getattr(record, "event", "unstructured")
        component = getattr(record, "component", "cli")
        payload: dict[str, str | int] = {
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "event": event if isinstance(event, str) and event in _EVENTS else "unstructured",
            "component": component if isinstance(component, str) and component == "cli" else "cli",
            "run_id": self.run_id,
        }
        category = getattr(record, "error_category", None)
        if isinstance(category, str) and category in {
            "configuration",
            "local_execution",
            "logging",
            "duplicate_key",
            "invalid_json",
            "input_io",
            "input_limit",
            "invalid_shape",
            "unsupported_version",
            "invalid_field",
            "duplicate_id",
            "broken_relation",
            "contradictory_binding",
            "duplicate_identity",
            "identity_conflict",
            "missing_binding",
            "unknown_variant",
            "unknown_language",
            "ambiguous_reference",
        }:
            payload["error_category"] = category
        result = getattr(record, "result", None)
        if isinstance(result, str) and result in {"ok", "error", "mixed", "empty"}:
            payload["result"] = result
        duration = getattr(record, "duration_ms", None)
        if isinstance(duration, int) and not isinstance(duration, bool) and duration >= 0:
            payload["duration_ms"] = duration
        for field in ("input_count", "accepted_count", "candidate_count", "rejected_count"):
            value = getattr(record, field, None)
            if isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 10000:
                payload[field] = value
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def configure_logging(run_id: str, level: str = "INFO") -> logging.Logger:
    try:
        safe_run_id = str(UUID(run_id))
    except (TypeError, ValueError, AttributeError):
        safe_run_id = str(uuid4())
    logger = logging.getLogger(_LOGGER_NAME)
    logger.setLevel(level)
    logger.propagate = False
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter(safe_run_id))
    logger.addHandler(handler)
    return logger
