"""Bounded strict JSON and shared safe catalog validation."""

import json
import math
import re
import stat
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import cast
from uuid import UUID

MAX_BYTES = 1_048_576
MAX_DEPTH = 16
MAX_NODES = 20_000
MAX_RECORDS = 1000
MAX_ENTITIES = 1000
MAX_BINDINGS = 2000
MAX_STRING = 1024
ERROR_CATEGORIES = frozenset(
    {
        "invalid_json",
        "duplicate_key",
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
    }
)


class CatalogError(ValueError):
    """Carries a stable category, never an input value or arbitrary exception text."""

    def __init__(self, category: str) -> None:
        self.category = category if category in ERROR_CATEGORIES else "invalid_field"
        super().__init__(self.category)


def object_value(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise CatalogError("invalid_shape")
    return cast(dict[str, object], value)


def array_value(value: object, limit: int = MAX_RECORDS) -> list[object]:
    if not isinstance(value, list):
        raise CatalogError("invalid_shape")
    if len(value) > limit:
        raise CatalogError("input_limit")
    return cast(list[object], value)


def string_value(value: object, limit: int = MAX_STRING) -> str:
    if not isinstance(value, str) or not value or len(value) > limit:
        raise CatalogError("invalid_field")
    if any(ord(char) < 32 or 0xD800 <= ord(char) <= 0xDFFF for char in value):
        raise CatalogError("invalid_field")
    return value


def token_value(value: object) -> str:
    token = string_value(value, 128)
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]*", token) is None:
        raise CatalogError("invalid_field")
    return token


def uuid_value(value: object) -> str:
    token = string_value(value, 36)
    try:
        parsed = UUID(token)
    except ValueError:
        raise CatalogError("invalid_field") from None
    if str(parsed) != token or parsed.version != 4:
        raise CatalogError("invalid_field")
    return token


def date_value(value: object) -> str | None:
    if value is None:
        return None
    result = string_value(value, 10)
    try:
        if date.fromisoformat(result).isoformat() != result:
            raise ValueError
    except ValueError:
        raise CatalogError("invalid_field") from None
    return result


def timestamp_value(value: object) -> str | None:
    if value is None:
        return None
    result = string_value(value, 40)
    try:
        parsed = datetime.fromisoformat(result)
        if "T" not in result or parsed.utcoffset() != timedelta(0):
            raise ValueError
    except ValueError:
        raise CatalogError("invalid_field") from None
    return result


def version_one(value: object) -> None:
    if type(value) is not int or value != 1:
        raise CatalogError("unsupported_version")


def validate_structure(value: object) -> None:
    """Bound direct Python inputs as well as decoded JSON; no recursive traversal."""
    pending: list[tuple[object, int]] = [(value, 0)]
    visited = 0
    while pending:
        node, depth = pending.pop()
        visited += 1
        if visited > MAX_NODES or depth > MAX_DEPTH:
            raise CatalogError("input_limit")
        if isinstance(node, dict):
            mapping = object_value(node)
            if len(mapping) > MAX_NODES:
                raise CatalogError("input_limit")
            pending.extend((item, depth + 1) for item in mapping.values())
            pending.extend((key, depth + 1) for key in mapping)
        elif isinstance(node, list):
            if len(node) > MAX_NODES:
                raise CatalogError("input_limit")
            pending.extend((item, depth + 1) for item in node)
        elif isinstance(node, str):
            if len(node) > MAX_STRING:
                raise CatalogError("input_limit")
            if any(0xD800 <= ord(char) <= 0xDFFF for char in node):
                raise CatalogError("invalid_json")
        elif isinstance(node, float):
            if not math.isfinite(node):
                raise CatalogError("invalid_json")
        elif node is not None and not isinstance(node, (bool, int)):
            raise CatalogError("invalid_shape")


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise CatalogError("duplicate_key")
        result[key] = value
    return result


def _constant(_: str) -> object:
    raise CatalogError("invalid_json")


def _preflight(text: str) -> None:
    depth = 0
    quoted = False
    escaped = False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > MAX_DEPTH:
                raise CatalogError("input_limit")
        elif char in "]}":
            depth -= 1


def read_json(path: Path) -> object:
    """Read at most 1 MiB from a regular local file, reject duplicate keys globally."""
    try:
        if not stat.S_ISREG(path.stat().st_mode):
            raise CatalogError("input_io")
        with path.open("rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
    except OSError:
        raise CatalogError("input_io") from None
    if len(raw) > MAX_BYTES:
        raise CatalogError("input_limit")
    try:
        text = raw.decode("utf-8")
        _preflight(text)
        result: object = json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant)
    except (UnicodeDecodeError, ValueError, RecursionError) as error:
        if isinstance(error, CatalogError):
            raise
        raise CatalogError("invalid_json") from None
    validate_structure(result)
    return result
