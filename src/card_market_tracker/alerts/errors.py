"""Fixed redacted categories for the independent offline alert outbox surface."""

from ..discovery.journal_errors import JournalError
from ..discovery.scoped_errors import SCOPED_CATEGORIES

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
        "recompute_mismatch",
    }
)
ERROR_CATEGORIES = SCOPED_CATEGORIES | _LOCAL | frozenset({"conflict", "invalid_profile"})


class OutboxError(JournalError):
    """No paths, SQL, payloads or underlying exception messages are retained."""

    def __init__(self, category: str) -> None:
        self.category = (
            category
            if isinstance(category, str) and category in ERROR_CATEGORIES
            else "invalid_field"
        )
        self.exit_code = 1 if self.category in _LOCAL else 2
        super().__init__(self.category)
