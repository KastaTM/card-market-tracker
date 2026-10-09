"""Normalized source evidence, separate from canonical domain identity."""

from dataclasses import dataclass, field
from typing import Literal

from .models import Language, Variant

ReferenceKind = Literal["set", "card", "sealed"]
Provenance = Literal["synthetic", "documented", "observed"]


@dataclass(frozen=True)
class ExternalReference:
    namespace: str
    kind: ReferenceKind
    external_id: str
    language: Language | None
    variant: Variant = "unknown"


@dataclass(frozen=True)
class Observation:
    kind: ReferenceKind
    reference: ExternalReference
    name: str
    set_reference: ExternalReference | None = None
    card_number: str | None = None
    release_date: str | None = None
    provider_updated_at: str | None = None
    captured_at: str | None = None
    provenance: Provenance = field(kw_only=True)


@dataclass(frozen=True)
class RecordError:
    index: int
    category: str
