"""Closed, redacted P8d error taxonomy."""

_OPERATIONAL = frozenset(
    {
        "input_io",
        "unsafe_destination",
        "storage_missing",
        "storage_schema",
        "storage_corrupt",
        "storage_locked",
        "storage_timeout",
        "storage_io",
        "recompute_mismatch",
        "transport_timeout",
        "transport_failure",
        "provider_rate_limit",
        "provider_invalid",
        "rate_limited",
        "network_uncertain",
        "deadline_exceeded",
        "local_commit_failed",
    }
)
_VALIDATION = frozenset(
    {
        "invalid_json",
        "duplicate_key",
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
        "no_rules",
        "invalid_timestamp",
        "invalid_target",
        "unsupported_evidence",
        "incompatible_context",
        "future_sample",
        "invalid_chronology",
        "replay_conflict",
        "revision_conflict",
        "already_exists",
        "not_found",
        "invalid_cursor",
        "conflict",
        "invalid_transition",
        "invalid_destination",
        "not_validated",
        "consent_mismatch",
        "send_quarantined",
        "delivery_blocked",
        "retry_not_due",
        "attempt_limit",
        "stale_attempt",
        "token_configuration",
        "bot_mismatch",
        "destination_mismatch",
        "provider_rejection",
        "retry_exhausted",
        "clock_skew",
    }
)
ERROR_CATEGORIES = _OPERATIONAL | _VALIDATION | {"recovered"}


class DeliveryError(ValueError):
    """Preserve only contract categories, never original exception text."""

    def __init__(self, category: str) -> None:
        self.category = (
            category if type(category) is str and category in ERROR_CATEGORIES else "invalid_field"
        )
        self.exit_code = 1 if self.category in _OPERATIONAL else 2
        super().__init__(self.category)
