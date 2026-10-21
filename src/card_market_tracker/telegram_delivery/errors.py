"""Fixed, redacted delivery failures; provider details never become diagnostics."""

from ..alerts.errors import ERROR_CATEGORIES as OUTBOX_CATEGORIES

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
        "token_configuration",
        "transport_timeout",
        "transport_failure",
        "confirmation_failed",
        "provider_rate_limit",
        "rate_limited",
        "network_uncertain",
        "malformed_response",
        "deadline_exceeded",
        "local_commit_failed",
        "clock_skew",
        "provider_invalid",
    }
)
ERROR_CATEGORIES = (
    OUTBOX_CATEGORIES
    | _OPERATIONAL
    | frozenset(
        {
            "invalid_destination",
            "not_validated",
            "send_quarantined",
            "delivery_blocked",
            "retry_not_due",
            "attempt_limit",
            "stale_attempt",
            "bot_mismatch",
            "destination_mismatch",
            "provider_rejection",
            "provider_rejected",
            "retry_exhausted",
            "recovered",
        }
    )
)


class DeliveryError(ValueError):
    """Retain only a known category, never paths, payloads, credentials or exceptions."""

    def __init__(self, category: str) -> None:
        self.category = (
            category if type(category) is str and category in ERROR_CATEGORIES else "invalid_field"
        )
        self.exit_code = 1 if self.category in _OPERATIONAL else 2
        super().__init__(self.category)
