"""Full manifest authority and bounded, strict watchlist JSON validation."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from ..catalog.manifest import parse_manifest
from ..catalog.models import Entity
from ..catalog.validation import (
    MAX_BYTES,
    CatalogError,
    object_value,
    token_value,
    uuid_value,
    validate_structure,
)
from ..catalog.validation import (
    read_json as catalog_read_json,
)
from .errors import WatchlistError
from .models import CONFIG_FIELDS, DEFAULT_MAX_AGE, MAX_AGE, MAX_MONEY, MAX_REVISION


def canonical(value: object) -> str:
    """Bound direct Python inputs, then produce the sole canonical representation."""
    try:
        validate_structure(value)
        result = json.dumps(
            value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
        )
    except CatalogError as error:
        raise WatchlistError(error.category) from None
    except (ValueError, TypeError, OverflowError, RecursionError):
        raise WatchlistError("invalid_json") from None
    if len(result.encode("ascii")) > MAX_BYTES:
        raise WatchlistError("input_limit")
    return result


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value).encode("ascii")).hexdigest()


def read_json(path: Path) -> object:
    try:
        result = catalog_read_json(path)
        canonical(result)
        return result
    except CatalogError as error:
        raise WatchlistError(error.category) from None


def _object(value: object) -> dict[str, object]:
    canonical(value)
    try:
        return object_value(value)
    except CatalogError as error:
        raise WatchlistError(error.category) from None


def _keys(
    row: dict[str, object], allowed: set[str] | frozenset[str], required: set[str] | frozenset[str]
) -> None:
    if set(row) - allowed or not required <= set(row):
        raise WatchlistError("invalid_shape")


def validate_cmt_id(value: object) -> str:
    try:
        return uuid_value(value)
    except CatalogError as error:
        raise WatchlistError(error.category) from None


def token(value: object) -> str:
    try:
        return token_value(value)
    except CatalogError as error:
        raise WatchlistError(error.category) from None


def validate_watch_id(value: object) -> str:
    if type(value) is not str or re.fullmatch(r"wlt1_[0-9a-f]{64}", value) is None:
        raise WatchlistError("invalid_field")
    return value


def make_watch_id(value: object) -> str:
    return (
        "wlt1_"
        + hashlib.sha256(
            ("CMT_WATCHLIST_V1\0" + validate_cmt_id(value)).encode("utf-8")
        ).hexdigest()
    )


def validate_revision(value: object, *, allow_zero: bool = False) -> int:
    if type(value) is not int or not (0 if allow_zero else 1) <= value <= MAX_REVISION:
        raise WatchlistError("invalid_field")
    return value


watch_id = validate_watch_id
revision = validate_revision
cmt_id = validate_cmt_id


def _integer(value: object, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise WatchlistError("invalid_field")
    return value


def parse_config(value: object) -> dict[str, object]:
    row = _object(value)
    _keys(row, CONFIG_FIELDS, set())
    priority = row.get("priority", "normal")
    enabled = row.get("enabled", True)
    target = row.get("target_price_minor")
    restock = row.get("restock_enabled", False)
    age = _integer(row.get("max_age_seconds", DEFAULT_MAX_AGE), 1, MAX_AGE)
    if (
        priority not in ("high", "normal", "low")
        or type(enabled) is not bool
        or type(restock) is not bool
    ):
        raise WatchlistError("invalid_field")
    if target is not None:
        target = _integer(target, 1, MAX_MONEY)
    if target is None and not restock:
        raise WatchlistError("no_rules")
    return {
        "priority": priority,
        "enabled": enabled,
        "target_price_minor": target,
        "restock_enabled": restock,
        "max_age_seconds": age,
    }


def timestamp(value: object) -> str:
    if (
        type(value) is not str
        or len(value) > 40
        or re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)",
            value,
        )
        is None
    ):
        raise WatchlistError("invalid_timestamp")
    try:
        parsed = datetime.fromisoformat(value).astimezone(UTC)
    except (ValueError, OverflowError):
        raise WatchlistError("invalid_timestamp") from None
    return parsed.isoformat().replace("+00:00", "Z")


def _target(entity: Entity) -> dict[str, object]:
    if entity.kind == "printing":
        return {
            "cmt_id": entity.cmt_id,
            "kind": entity.kind,
            "card_id": entity.card_id,
            "language": entity.language,
            "variant": entity.variant,
        }
    return {
        "cmt_id": entity.cmt_id,
        "kind": entity.kind,
        "set_id": entity.set_id,
        "language": entity.language,
        "sealed_type": entity.sealed_type,
    }


def identity_projection(manifest_input: object, cmt_id: object) -> dict[str, object]:
    """Reparse the entire raw manifest; a Manifest dataclass is never authority."""
    wanted = validate_cmt_id(cmt_id)
    canonical(manifest_input)
    try:
        manifest = parse_manifest(manifest_input)
    except CatalogError as error:
        raise WatchlistError(error.category) from None
    entities = {entity.cmt_id: entity for entity in manifest.entities}
    entity = entities.get(wanted)
    if entity is None or entity.kind not in ("printing", "sealed"):
        raise WatchlistError("invalid_target")
    parents: list[dict[str, object]] = []
    if entity.kind == "printing":
        card = entities[cast(str, entity.card_id)]
        parents.append(
            {
                "cmt_id": card.cmt_id,
                "kind": "card",
                "set_id": card.set_id,
                "card_number": card.card_number,
            }
        )
        parent_set = entities[cast(str, card.set_id)]
        parents.append({"cmt_id": parent_set.cmt_id, "kind": "set"})
    elif entity.set_id is not None:
        parents.append({"cmt_id": entity.set_id, "kind": "set"})
    return {"version": 1, "target": _target(entity), "parents": parents}


def _projection(value: object, wanted: str) -> dict[str, object]:
    row = _object(value)
    _keys(row, {"version", "target", "parents"}, {"version", "target", "parents"})
    if type(row["version"]) is not int or row["version"] != 1:
        raise WatchlistError("unsupported_version")
    parents = row["parents"]
    if type(parents) is not list or len(parents) > 2:
        raise WatchlistError("invalid_shape")
    raw = {"version": 1, "entities": [row["target"], *parents], "bindings": []}
    expected = identity_projection(raw, wanted)
    if row != expected:
        raise WatchlistError("identity_conflict")
    return expected


def parse_entry(value: object) -> dict[str, object]:
    row = _object(value)
    fields = CONFIG_FIELDS | {
        "version",
        "cmt_id",
        "watch_id",
        "canonical_identity",
        "identity_digest",
        "revision",
    }
    _keys(row, fields, fields)
    if type(row["version"]) is not int or row["version"] != 1:
        raise WatchlistError("unsupported_version")
    wanted = cmt_id(row["cmt_id"])
    key = validate_watch_id(row["watch_id"])
    projection = _projection(row["canonical_identity"], wanted)
    if key != make_watch_id(wanted) or row["identity_digest"] != digest(projection):
        raise WatchlistError("identity_conflict")
    config = parse_config({field: row[field] for field in CONFIG_FIELDS})
    return {
        "version": 1,
        "cmt_id": wanted,
        "watch_id": key,
        "canonical_identity": projection,
        "identity_digest": digest(projection),
        "revision": validate_revision(row["revision"]),
        **config,
    }


def parse_sample(value: object) -> dict[str, object]:
    row = _object(value)
    fields = {
        "version",
        "provenance",
        "sample_id",
        "cmt_id",
        "series_key",
        "observed_at",
        "currency",
        "unit_price_minor",
        "shipping_minor",
        "stock",
    }
    _keys(row, fields, fields)
    if type(row["version"]) is not int or row["version"] != 1:
        raise WatchlistError("unsupported_version")
    if row["provenance"] != "synthetic" or row["currency"] != "EUR":
        raise WatchlistError("unsupported_evidence")
    if row["stock"] not in ("AVAILABLE", "OUT_OF_STOCK", "UNKNOWN"):
        raise WatchlistError("invalid_field")
    unit = row["unit_price_minor"]
    shipping = row["shipping_minor"]
    return {
        "version": 1,
        "provenance": "synthetic",
        "sample_id": token(row["sample_id"]),
        "cmt_id": cmt_id(row["cmt_id"]),
        "series_key": token(row["series_key"]),
        "observed_at": timestamp(row["observed_at"]),
        "currency": "EUR",
        "unit_price_minor": None if unit is None else _integer(unit, 1, MAX_MONEY),
        "shipping_minor": None if shipping is None else _integer(shipping, 0, MAX_MONEY),
        "stock": row["stock"],
    }
