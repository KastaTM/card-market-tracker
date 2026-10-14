"""Fixed safe error categories for the pinned repository boundary."""


class BundleError(ValueError):
    """Errors never contain source text, paths or arbitrary exception messages."""

    def __init__(self, category: str) -> None:
        self.category = category
        super().__init__(category)
