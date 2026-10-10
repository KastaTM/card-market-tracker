"""Bounded local wrapper and serialization, without a storage dependency."""

import json
from datetime import UTC, datetime
from pathlib import Path

from ..catalog.adapters.tcgdex import translate_batch
from ..catalog.ingestion import ExternalReference, Observation
from ..catalog.manifest import Manifest, parse_manifest
from ..catalog.models import Entity, Localization
from ..catalog.resolver import reference_dict
from ..catalog.validation import (
    MAX_BINDINGS,
    MAX_BYTES,
    MAX_ENTITIES,
    CatalogError,
    object_value,
    read_json,
    string_value,
    validate_structure,
    version_one,
)
from .errors import PersistenceError
from .models import PersistenceBatch


def canonical_json(value: object) -> str:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def bounded_value(value: object) -> None:
    """Apply JSON complexity and encoded-byte bounds to direct Python input."""
    validate_structure(value)
    try:
        encoded = json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (ValueError, UnicodeError):
        raise CatalogError("invalid_json") from None
    if len(encoded) > MAX_BYTES:
        raise CatalogError("input_limit")


def utc_timestamp(value: object, *, required: bool = False) -> str | None:
    if value is None:
        if required:
            raise PersistenceError("capture_required")
        return None
    try:
        text = string_value(value, 40)
        instant = datetime.fromisoformat(text)
        if "T" not in text or instant.tzinfo is None or instant.utcoffset() is None:
            raise ValueError
        return instant.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
    except (CatalogError, ValueError, OverflowError):
        raise PersistenceError("invalid_field") from None


def reference_value(reference: ExternalReference) -> dict[str, object]:
    if not isinstance(reference, ExternalReference):
        raise CatalogError("invalid_shape")
    return reference_dict(reference)


def observation_dict(observation: Observation) -> dict[str, object]:
    if not isinstance(observation, Observation):
        raise CatalogError("invalid_shape")
    return {
        "kind": observation.kind,
        "reference": reference_value(observation.reference),
        "name": observation.name,
        "set_reference": None
        if observation.set_reference is None
        else reference_value(observation.set_reference),
        "card_number": observation.card_number,
        "release_date": observation.release_date,
        "provider_updated_at": observation.provider_updated_at,
        "captured_at": observation.captured_at,
        "provenance": observation.provenance,
    }


def entity_dict(entity: Entity, *, include_names: bool = False) -> dict[str, object]:
    if not isinstance(entity, Entity):
        raise CatalogError("invalid_shape")
    row: dict[str, object] = {
        "cmt_id": entity.cmt_id,
        "kind": entity.kind,
        "set_id": entity.set_id,
        "card_id": entity.card_id,
        "card_number": entity.card_number,
        "language": entity.language,
        "variant": entity.variant,
        "release_date": entity.release_date,
        "sealed_type": entity.sealed_type,
    }
    if include_names:
        if not isinstance(entity.names, tuple) or len(entity.names) > 2:
            raise CatalogError("invalid_field")
        names: dict[str, object] = {}
        for name in entity.names:
            if not isinstance(name, Localization) or name.language not in ("es", "en"):
                raise CatalogError("invalid_field")
            if name.language in names:
                raise CatalogError("invalid_field")
            names[name.language] = name.name
        row["names"] = names
    return row


def validated_manifest(value: object) -> Manifest:
    if isinstance(value, Manifest):
        if not isinstance(value.entities, tuple) or not isinstance(value.bindings, tuple):
            raise CatalogError("invalid_shape")
        if len(value.entities) > MAX_ENTITIES or len(value.bindings) > MAX_BINDINGS:
            raise CatalogError("input_limit")
        # Serialize every field, including fields excluded from replay context.
        from ..catalog.manifest import Binding

        bindings: list[dict[str, object]] = []
        for binding in value.bindings:
            if not isinstance(binding, Binding):
                raise CatalogError("invalid_shape")
            bindings.append(
                {
                    "reference": reference_value(binding.reference),
                    "cmt_id": binding.cmt_id,
                    "reason": binding.reason,
                }
            )
        value = {
            "version": 1,
            "entities": [entity_dict(entity, include_names=True) for entity in value.entities],
            "bindings": bindings,
        }
    bounded_value(value)
    return parse_manifest(value)


def parse_persistence(document: object, manifest: object) -> PersistenceBatch:
    """Translate the strict local v1 wrapper; P1a semantics stay unchanged."""
    from .application import build_batch

    try:
        bounded_value(document)
        wrapper = object_value(document)
        required = {"version", "batch_id", "captured_at", "ingestion"}
        if set(wrapper) != required:
            if "captured_at" not in wrapper:
                raise PersistenceError("capture_required")
            raise CatalogError("invalid_shape")
        version_one(wrapper["version"])
        captured_at = utc_timestamp(wrapper["captured_at"], required=True)
        ingestion = object_value(wrapper["ingestion"])
        provenance = ingestion.get("provenance")
        if provenance not in ("synthetic", "documented", "observed"):
            raise CatalogError("invalid_field")
        if provenance != "synthetic":
            raise PersistenceError("synthetic_only")
        declared = utc_timestamp(ingestion.get("captured_at"))
        if declared is not None and declared != captured_at:
            raise PersistenceError("capture_conflict")
        prepared = dict(ingestion)
        prepared["captured_at"] = captured_at
        return build_batch(wrapper["batch_id"], captured_at, translate_batch(prepared), manifest)
    except CatalogError as error:
        raise PersistenceError(error.category) from None


def read_persistence(input_path: Path, manifest_path: Path) -> PersistenceBatch:
    try:
        document = read_json(input_path)
        manifest = read_json(manifest_path)
        return parse_persistence(document, manifest)
    except CatalogError as error:
        raise PersistenceError(error.category) from None
