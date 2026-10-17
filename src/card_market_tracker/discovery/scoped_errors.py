"""Safe version-two categories, separate from the unchanged v1 surface."""

from .errors import ERROR_CATEGORIES, DiscoveryError

SCOPED_CATEGORIES = ERROR_CATEGORIES | frozenset(
    {
        "unsupported_evidence",
        "scope_mismatch",
        "unit_missing",
        "ambiguous_unit",
    }
)


class ScopedDiscoveryError(DiscoveryError):
    def __init__(self, category: str) -> None:
        if category in SCOPED_CATEGORIES - ERROR_CATEGORIES:
            self.category = category
            self.exit_code = 2
            ValueError.__init__(self, category)
        else:
            super().__init__(category)
            if self.category == "input_io":
                self.exit_code = 1
