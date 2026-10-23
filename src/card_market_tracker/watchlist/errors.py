"""Sanitized error categories at watchlist public boundaries."""

from ..catalog.validation import ERROR_CATEGORIES as CATALOG_CATEGORIES

_LOCAL = frozenset(
    {
        "input_io",
        "unsafe_destination",
        "storage_missing",
        "storage_schema",
        "storage_corrupt",
        "storage_locked",
        "storage_timeout",
        "storage_io",
    }
)
ERROR_CATEGORIES = (
    CATALOG_CATEGORIES
    | _LOCAL
    | frozenset(
        {
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
        }
    )
)


class WatchlistError(ValueError):
    """Expose a stable category without retaining an untrusted input value."""

    def __init__(self, category: str) -> None:
        self.category = (
            category
            if isinstance(category, str) and category in ERROR_CATEGORIES
            else "invalid_field"
        )
        self.exit_code = 1 if self.category in _LOCAL else 2
        super().__init__(self.category)
