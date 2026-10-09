"""Provider-independent catalog entities (catalog contract v1)."""

from dataclasses import dataclass
from typing import Literal

Language = Literal["es", "en"]
Variant = Literal["normal", "holo", "reverse", "unknown"]
EntityKind = Literal["set", "card", "printing", "sealed"]


@dataclass(frozen=True)
class Localization:
    language: Language
    name: str


@dataclass(frozen=True)
class Entity:
    cmt_id: str
    kind: EntityKind
    names: tuple[Localization, ...] = ()
    set_id: str | None = None
    card_id: str | None = None
    card_number: str | None = None
    language: Language | None = None
    variant: Variant = "unknown"
    release_date: str | None = None
    sealed_type: str | None = None
