"""Structured logging contract v1: only allowlisted fields leave the process."""

from __future__ import annotations

import json
import logging
import re
import sys
from datetime import UTC, datetime
from uuid import UUID, uuid4

_LOGGER_NAME = "card_market_tracker"
_EVENTS = frozenset(
    {
        "cli.version",
        "diagnose.completed",
        "config.invalid",
        "catalog.completed",
        "persistence.completed",
        "discovery.completed",
        "discovery.scoped.completed",
        "discovery.multi.completed",
        "discovery.journal.completed",
        "alert.outbox.completed",
        "telegram.delivery.completed",
        "watchlist.completed",
    }
)


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
            "capture_required",
            "capture_conflict",
            "synthetic_only",
            "replay_conflict",
            "storage_schema",
            "storage_locked",
            "storage_io",
            "storage_corrupt",
            "storage_timeout",
            "unsafe_destination",
            "resolution_mismatch",
            "batch_missing",
            "incomplete_evidence",
            "context_mismatch",
            "chronology",
            "contradictory_snapshot",
            "invalid_encoding",
            "unsupported_syntax",
            "invalid_import",
            "duplicate_field",
            "invalid_selection",
            "missing_field",
            "missing_translation",
            "invalid_relation",
            "unapproved_bundle",
            "approved_package_io",
            "unsupported_evidence",
            "scope_mismatch",
            "unit_missing",
            "ambiguous_unit",
            "conflict",
            "invalid_profile",
            "storage_missing",
            "recompute_mismatch",
            "invalid_destination",
            "not_validated",
            "send_quarantined",
            "delivery_blocked",
            "retry_not_due",
            "attempt_limit",
            "stale_attempt",
            "token_configuration",
            "bot_mismatch",
            "destination_mismatch",
            "transport_timeout",
            "transport_failure",
            "provider_rejection",
            "provider_rate_limit",
            "provider_invalid",
            "confirmation_failed",
            "provider_rejected",
            "rate_limited",
            "retry_exhausted",
            "network_uncertain",
            "malformed_response",
            "deadline_exceeded",
            "recovered",
            "local_commit_failed",
            "clock_skew",
            "revision_conflict",
            "future_sample",
            "no_rules",
            "invalid_timestamp",
            "invalid_target",
            "incompatible_context",
            "invalid_chronology",
            "already_exists",
            "not_found",
            "invalid_cursor",
        }:
            payload["error_category"] = category
        result = getattr(record, "result", None)
        if isinstance(result, str) and result in {
            "ok",
            "error",
            "mixed",
            "empty",
            "replay",
            "baseline",
            "no_discoveries",
            "discoveries",
            "inserted",
        }:
            payload["result"] = result
        operation = getattr(record, "operation", None)
        if isinstance(operation, str) and operation in {
            "init",
            "persist",
            "read",
            "verify",
            "backup",
            "restore",
            "migrate",
            "bundle_verify",
            "bundle_import",
            "capture_read",
            "discover_scoped",
            "discover_multi_revision",
            "bundle_v2_verify",
            "bundle_v2_import",
            "discovery_journal_arguments",
            "discovery_journal_init",
            "discovery_journal_record",
            "discovery_journal_get",
            "discovery_journal_list",
            "discovery_journal_event_occurrences",
            "discovery_journal_verify",
            "discovery_journal_recompute",
            "discovery_journal_backup",
            "discovery_journal_restore",
            "alert_outbox_arguments",
            "alert_outbox_init",
            "alert_outbox_enqueue",
            "alert_outbox_get",
            "alert_outbox_list",
            "alert_outbox_evidence_list",
            "alert_outbox_evidence_get",
            "alert_outbox_preview",
            "alert_outbox_verify",
            "alert_outbox_recompute",
            "alert_outbox_backup",
            "alert_outbox_restore",
            "telegram_delivery_arguments",
            "telegram_delivery_init",
            "telegram_delivery_destination_add",
            "telegram_delivery_destination_validate",
            "telegram_delivery_prepare",
            "telegram_delivery_send",
            "telegram_delivery_get",
            "telegram_delivery_list",
            "telegram_delivery_verify",
            "telegram_delivery_recompute",
            "telegram_delivery_recover",
            "telegram_delivery_backup",
            "telegram_delivery_restore",
            "watchlist_arguments",
            "watchlist_init",
            "watchlist_add",
            "watchlist_get",
            "watchlist_list",
            "watchlist_update",
            "watchlist_enable",
            "watchlist_disable",
            "watchlist_history",
            "watchlist_evaluate",
            "watchlist_verify",
            "watchlist_backup",
            "watchlist_restore",
        }:
            payload["operation"] = operation
        duration = getattr(record, "duration_ms", None)
        if isinstance(duration, int) and not isinstance(duration, bool) and duration >= 0:
            payload["duration_ms"] = duration
        for field in (
            "input_count",
            "accepted_count",
            "candidate_count",
            "rejected_count",
            "new_batch_count",
            "new_entity_count",
            "new_observation_count",
            "observation_count",
        ):
            value = getattr(record, field, None)
            if isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 10000:
                payload[field] = value
        for field, maximum in (
            ("batch_count", 33),
            ("discovery_observation_count", 33000),
            ("event_count", 1000),
            ("scoped_validated_record_count", 33000),
            ("scoped_selected_record_count", 33000),
            ("journal_comparisons_count", 100000000),
            ("journal_occurrences_count", 100000000),
            ("outbox_alerts_count", 100000000),
            ("outbox_associations_count", 100000000),
            ("outbox_events_count", 1000),
            ("watchlist_entries_count", 1000),
        ):
            value = getattr(record, field, None)
            if type(value) is int and 0 <= value <= maximum:
                payload[field] = value
        for field, prefix in (("delivery_id", "tdl1:"), ("attempt_id", "tat1:")):
            value = getattr(record, field, None)
            if type(value) is str and re.fullmatch(prefix + r"[0-9a-f]{64}", value):
                payload[field] = value
        states = {"ready", "in_flight", "retryable", "confirmed", "permanent_failure", "uncertain"}
        for field in ("state", "previous_state"):
            value = getattr(record, field, None)
            if type(value) is str and value in states:
                payload[field] = value
        attempts = getattr(record, "attempt_count", None)
        if type(attempts) is int and 0 <= attempts <= 3:
            payload["attempt_count"] = attempts
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
