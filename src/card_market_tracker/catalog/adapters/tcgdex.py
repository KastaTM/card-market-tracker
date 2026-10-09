"""Offline translation of a deliberately bounded minimum TCGdex REST shape."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import cast

from ..ingestion import ExternalReference, Observation, Provenance, RecordError
from ..models import Language, Variant
from ..validation import MAX_RECORDS, CatalogError, string_value, token_value, validate_structure

_WRAPPER_FIELDS = frozenset({"kind", "language", "data", "variant"})
_FLAGS = ("normal", "holo", "reverse", "firstEdition", "wPromo", "jumbo", "preRelease")


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise CatalogError("invalid_field")
    return cast(dict[str, object], value)


def _text(value: object) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 256:
        raise CatalogError("invalid_field")
    if any(ord(char) < 32 for char in value):
        raise CatalogError("invalid_field")
    return value


def _language(value: object) -> Language | None:
    if value is None:
        return None
    if value not in ("es", "en"):
        raise CatalogError("invalid_field")
    return value


def _variant(value: object) -> Variant:
    if value is None:
        return "unknown"
    if value not in ("normal", "holo", "reverse", "unknown"):
        raise CatalogError("invalid_field")
    return value


def _date(value: object) -> str | None:
    if value is None:
        return None
    result = _text(value)
    try:
        parsed = date.fromisoformat(result)
    except ValueError:
        raise CatalogError("invalid_field") from None
    if parsed.isoformat() != result:
        raise CatalogError("invalid_field")
    return result


def _timestamp(value: object) -> str | None:
    if value is None:
        return None
    result = _text(value)
    try:
        parsed = datetime.fromisoformat(result)
        if parsed.tzinfo is None or "T" not in result:
            raise ValueError
        return parsed.astimezone(UTC).isoformat().replace("+00:00", "Z")
    except (ValueError, OverflowError):
        raise CatalogError("invalid_field") from None


def _translate_record(
    value: object, provenance: Provenance, captured_at: str | None
) -> Observation:
    wrapper = _object(value)
    if set(wrapper) - _WRAPPER_FIELDS or not {"kind", "language", "data"} <= set(wrapper):
        raise CatalogError("invalid_field")
    kind = wrapper["kind"]
    if kind not in ("set", "card"):
        raise CatalogError("invalid_field")
    language = _language(wrapper["language"])
    variant = _variant(wrapper.get("variant"))
    if kind == "set" and variant != "unknown":
        raise CatalogError("invalid_field")
    data = _object(wrapper["data"])
    external_id = token_value(data.get("id"))
    name = _text(data.get("name"))
    reference = ExternalReference("tcgdex", kind, external_id, language, variant)
    if kind == "set":
        return Observation(
            kind="set",
            reference=reference,
            name=name,
            release_date=_date(data.get("releaseDate")),
            captured_at=captured_at,
            provenance=provenance,
        )
    set_data = _object(data.get("set"))
    set_reference = ExternalReference("tcgdex", "set", token_value(set_data.get("id")), language)
    number = string_value(_text(data.get("localId")), 64)
    if "variants" in data:
        flags = _object(data["variants"])
        for key in _FLAGS:
            if key in flags and not isinstance(flags[key], bool):
                raise CatalogError("invalid_field")
    return Observation(
        kind="card",
        reference=reference,
        name=name,
        set_reference=set_reference,
        card_number=number,
        provider_updated_at=_timestamp(data.get("updated")),
        captured_at=captured_at,
        provenance=provenance,
    )


def translate_batch(document: object) -> tuple[Observation | RecordError, ...]:
    """Keep record failures explicit; an invalid envelope fails the whole operation.

    Provider extras are discarded. Availability flags never select a variant.
    No input URL is fetched and no source record is written or logged.
    """
    validate_structure(document)
    envelope = _object(document)
    required = {"version", "provenance", "records"}
    if not required <= set(envelope) or set(envelope) - required - {"captured_at"}:
        raise CatalogError("invalid_field")
    if type(envelope["version"]) is not int or envelope["version"] != 1:
        raise CatalogError("unsupported_version")
    provenance = envelope["provenance"]
    if provenance not in ("synthetic", "documented", "observed"):
        raise CatalogError("invalid_field")
    captured_at = _timestamp(envelope.get("captured_at"))
    records = envelope["records"]
    if not isinstance(records, list):
        raise CatalogError("invalid_field")
    if len(records) > MAX_RECORDS:
        raise CatalogError("input_limit")
    translated: list[Observation | RecordError] = []
    for index, record in enumerate(records):
        try:
            translated.append(_translate_record(record, provenance, captured_at))
        except CatalogError as exc:
            translated.append(RecordError(index, exc.category))
    return tuple(translated)


translate_tcgdex = translate_batch
