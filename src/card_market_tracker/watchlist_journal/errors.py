"""Fixed, redacted errors at the journal's public boundaries."""

from ..watchlist.errors import ERROR_CATEGORIES as WATCHLIST_CATEGORIES

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
ERROR_CATEGORIES = WATCHLIST_CATEGORIES | _LOCAL


class WatchlistJournalError(ValueError):
    """Carry a stable category without preserving potentially sensitive inputs."""

    def __init__(self, category: str) -> None:
        self.category = (
            category
            if isinstance(category, str) and category in ERROR_CATEGORIES
            else "invalid_field"
        )
        self.exit_code = 1 if self.category in _LOCAL else 2
        super().__init__(self.category)


JournalError = WatchlistJournalError
