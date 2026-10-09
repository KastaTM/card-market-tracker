"""Versioned explicit curated identity registry, with no generated identities."""

from dataclasses import dataclass
from typing import cast

from .ingestion import ExternalReference
from .models import Entity, Language, Localization, Variant
from .validation import (
    MAX_BINDINGS,
    MAX_ENTITIES,
    CatalogError,
    array_value,
    date_value,
    object_value,
    string_value,
    token_value,
    uuid_value,
    validate_structure,
    version_one,
)


@dataclass(frozen=True)
class Binding:
    reference: ExternalReference
    cmt_id: str
    reason: str


@dataclass(frozen=True)
class Manifest:
    entities: tuple[Entity, ...]
    bindings: tuple[Binding, ...]


def language_value(value: object) -> Language | None:
    if value is None or value in ("es", "en"):
        return value
    raise CatalogError("invalid_field")


def variant_value(value: object) -> Variant:
    if value not in ("normal", "holo", "reverse", "unknown"):
        raise CatalogError("invalid_field")
    return value


def _keys(mapping: dict[str, object], allowed: set[str], required: set[str]) -> None:
    if set(mapping) - allowed or not required <= set(mapping):
        raise CatalogError("invalid_shape")


def parse_reference(value: object) -> ExternalReference:
    row = object_value(value)
    fields = {"namespace", "kind", "external_id", "language", "variant"}
    _keys(row, fields, fields)
    kind = row["kind"]
    if kind not in ("set", "card", "sealed"):
        raise CatalogError("invalid_field")
    variant = variant_value(row["variant"])
    if kind != "card" and variant != "unknown":
        raise CatalogError("invalid_field")
    return ExternalReference(
        token_value(row["namespace"]),
        kind,
        token_value(row["external_id"]),
        language_value(row["language"]),
        variant,
    )


def _optional_uuid(value: object) -> str | None:
    return None if value is None else uuid_value(value)


def _entity(value: object) -> Entity:
    row = object_value(value)
    allowed = {
        "cmt_id",
        "kind",
        "names",
        "set_id",
        "card_id",
        "card_number",
        "language",
        "variant",
        "release_date",
        "sealed_type",
    }
    _keys(row, allowed, {"cmt_id", "kind"})
    kind = row["kind"]
    if kind not in ("set", "card", "printing", "sealed"):
        raise CatalogError("invalid_field")
    names = object_value(row.get("names", {}))
    if any(key not in ("es", "en") for key in names):
        raise CatalogError("invalid_field")
    entity = Entity(
        cmt_id=uuid_value(row["cmt_id"]),
        kind=kind,
        names=tuple(
            Localization(cast(Language, key), string_value(names[key])) for key in sorted(names)
        ),
        set_id=_optional_uuid(row.get("set_id")),
        card_id=_optional_uuid(row.get("card_id")),
        card_number=None
        if row.get("card_number") is None
        else string_value(row["card_number"], 64),
        language=language_value(row.get("language")),
        variant=variant_value(row.get("variant", "unknown")),
        release_date=date_value(row.get("release_date")),
        sealed_type=None
        if row.get("sealed_type") is None
        else string_value(row["sealed_type"], 32),
    )
    if kind == "card":
        if entity.set_id is None or entity.card_number is None:
            raise CatalogError("broken_relation")
    elif entity.card_number is not None:
        raise CatalogError("invalid_field")
    if kind == "printing":
        if entity.card_id is None or entity.set_id is not None:
            raise CatalogError("broken_relation")
    elif entity.card_id is not None:
        raise CatalogError("invalid_field")
    if kind in ("set", "card") and (entity.language is not None or entity.variant != "unknown"):
        raise CatalogError("invalid_field")
    if kind == "set" and entity.set_id is not None:
        raise CatalogError("invalid_field")
    if kind == "sealed":
        if entity.variant != "unknown" or entity.sealed_type not in (
            "booster_pack",
            "box",
            "bundle",
            "collection",
            "unknown",
        ):
            raise CatalogError("invalid_field")
    elif entity.sealed_type is not None:
        raise CatalogError("invalid_field")
    return entity


def parse_manifest(value: object) -> Manifest:
    validate_structure(value)
    document = object_value(value)
    _keys(document, {"version", "entities", "bindings"}, {"version", "entities", "bindings"})
    version_one(document["version"])
    entities = tuple(_entity(row) for row in array_value(document["entities"], MAX_ENTITIES))
    by_id: dict[str, Entity] = {}
    identities: set[tuple[object, ...]] = set()
    for entity in entities:
        if entity.cmt_id in by_id:
            raise CatalogError("duplicate_id")
        by_id[entity.cmt_id] = entity
        key: tuple[object, ...] | None = None
        if entity.kind == "card":
            key = ("card", entity.set_id, entity.card_number)
        elif entity.kind == "printing":
            key = ("printing", entity.card_id, entity.language, entity.variant)
        if key is not None:
            if key in identities:
                raise CatalogError("duplicate_identity")
            identities.add(key)
    for entity in entities:
        if entity.set_id is not None:
            target = by_id.get(entity.set_id)
            if target is None or target.kind != "set":
                raise CatalogError("broken_relation")
        if entity.card_id is not None:
            target = by_id.get(entity.card_id)
            if target is None or target.kind != "card":
                raise CatalogError("broken_relation")
    bindings: list[Binding] = []
    references: set[ExternalReference] = set()
    card_contexts: dict[tuple[str, str, str | None], str | None] = {}
    for item in array_value(document["bindings"], MAX_BINDINGS):
        row = object_value(item)
        _keys(row, {"reference", "cmt_id", "reason"}, {"reference", "cmt_id", "reason"})
        reference = parse_reference(row["reference"])
        cmt_id = uuid_value(row["cmt_id"])
        reason = string_value(row["reason"], 256)
        if reference in references:
            raise CatalogError("contradictory_binding")
        references.add(reference)
        target = by_id.get(cmt_id)
        expected_kind = "printing" if reference.kind == "card" else reference.kind
        if target is None or target.kind != expected_kind:
            raise CatalogError("broken_relation")
        if target.kind in ("printing", "sealed") and target.language != reference.language:
            raise CatalogError("contradictory_binding")
        if target.kind == "printing" and target.variant != reference.variant:
            raise CatalogError("contradictory_binding")
        if target.kind == "printing":
            context = (reference.namespace, reference.external_id, reference.language)
            if context in card_contexts and card_contexts[context] != target.card_id:
                raise CatalogError("contradictory_binding")
            card_contexts[context] = target.card_id
        bindings.append(Binding(reference, cmt_id, reason))
    return Manifest(entities, tuple(bindings))
