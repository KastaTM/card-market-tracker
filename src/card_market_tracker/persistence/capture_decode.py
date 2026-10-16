"""Decode retained normalized synthetic observations, without a provider adapter."""

from typing import cast

from ..catalog.ingestion import Observation, Provenance, ReferenceKind
from ..catalog.manifest import parse_reference
from ..catalog.validation import object_value


def decode_observation(value: object) -> Observation:
    row = object_value(value)
    return Observation(
        cast(ReferenceKind, row["kind"]),
        parse_reference(row["reference"]),
        cast(str, row["name"]),
        None if row["set_reference"] is None else parse_reference(row["set_reference"]),
        cast(str | None, row["card_number"]),
        cast(str | None, row["release_date"]),
        cast(str | None, row["provider_updated_at"]),
        cast(str | None, row["captured_at"]),
        provenance=cast(Provenance, row["provenance"]),
    )
