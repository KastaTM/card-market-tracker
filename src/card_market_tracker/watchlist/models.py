"""Versioned watchlist policy constants; JSON dictionaries carry no authority."""

from typing import Literal

JsonObject = dict[str, object]
RuleStatus = Literal["MATCH", "NO_MATCH", "INDETERMINATE"]
POLICY_VERSION = "watchlist-rules-v1"
MAX_MONEY = 1_000_000_000
MAX_TOTAL = 2 * MAX_MONEY
MAX_REVISION = 2_147_483_647
DEFAULT_MAX_AGE = 86_400
MAX_AGE = 604_800
CONFIG_FIELDS = frozenset(
    {"priority", "enabled", "target_price_minor", "restock_enabled", "max_age_seconds"}
)
