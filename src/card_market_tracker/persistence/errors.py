"""Safe fixed persistence categories; exceptions never carry source values."""

from ..catalog.validation import ERROR_CATEGORIES as CATALOG_CATEGORIES

ERROR_CATEGORIES = CATALOG_CATEGORIES | frozenset(
    {
        "synthetic_only",
        "capture_required",
        "capture_conflict",
        "resolution_mismatch",
        "storage_schema",
        "storage_locked",
        "storage_io",
        "storage_corrupt",
        "storage_timeout",
        "unsafe_destination",
        "replay_conflict",
    }
)
_LOCAL = frozenset(
    {
        "input_io",
        "storage_schema",
        "storage_locked",
        "storage_io",
        "storage_corrupt",
        "storage_timeout",
        "unsafe_destination",
    }
)


class PersistenceError(ValueError):
    """A stable public error with no raw exception text or input attached."""

    def __init__(self, category: str) -> None:
        self.category = (
            category
            if isinstance(category, str) and category in ERROR_CATEGORIES
            else "invalid_field"
        )
        self.exit_code = 1 if self.category in _LOCAL else 2
        super().__init__(self.category)
