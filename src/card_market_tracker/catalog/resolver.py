"""Conservative exact-reference resolution, without mutation or name matching."""

from dataclasses import dataclass
from typing import Literal

from .ingestion import ExternalReference, Observation, Provenance, RecordError
from .manifest import Manifest, parse_reference
from .models import Entity
from .validation import (
    ERROR_CATEGORIES,
    MAX_RECORDS,
    CatalogError,
    date_value,
    string_value,
    timestamp_value,
)


@dataclass(frozen=True)
class Resolution:
    index: int
    status: Literal["accepted", "candidate", "rejected"]
    category: str | None = None
    cmt_id: str | None = None
    reference: ExternalReference | None = None
    provenance: Provenance | None = None


def reference_dict(reference: ExternalReference) -> dict[str, object]:
    return {
        "namespace": reference.namespace,
        "kind": reference.kind,
        "external_id": reference.external_id,
        "language": reference.language,
        "variant": reference.variant,
    }


@dataclass(frozen=True)
class BatchResult:
    records: tuple[Resolution, ...]
    entities: tuple[Entity, ...]

    @property
    def accepted(self) -> int:
        return sum(row.status == "accepted" for row in self.records)

    @property
    def candidates(self) -> int:
        return sum(row.status == "candidate" for row in self.records)

    @property
    def rejected(self) -> int:
        return sum(row.status == "rejected" for row in self.records)

    def to_dict(self) -> dict[str, object]:
        return {
            "version": 1,
            "counts": {
                "input": len(self.records),
                "accepted": self.accepted,
                "candidates": self.candidates,
                "rejected": self.rejected,
                "entities": len(self.entities),
            },
            "entities": [
                {
                    "cmt_id": row.cmt_id,
                    "kind": row.kind,
                    "set_id": row.set_id,
                    "card_id": row.card_id,
                    "card_number": row.card_number,
                    "language": row.language,
                    "variant": row.variant,
                    "release_date": row.release_date,
                    "sealed_type": row.sealed_type,
                }
                for row in self.entities
            ],
            "records": [
                {
                    "index": row.index,
                    "status": row.status,
                    "category": row.category,
                    "cmt_id": row.cmt_id,
                    "reference": None if row.reference is None else reference_dict(row.reference),
                    "provenance": row.provenance,
                }
                for row in self.records
            ],
        }


def _validate_observation(observation: Observation) -> None:
    reference = parse_reference(reference_dict(observation.reference))
    if observation.kind != reference.kind:
        raise CatalogError("invalid_field")
    string_value(observation.name)
    if observation.provenance not in ("synthetic", "documented", "observed"):
        raise CatalogError("invalid_field")
    date_value(observation.release_date)
    timestamp_value(observation.provider_updated_at)
    timestamp_value(observation.captured_at)
    if observation.set_reference is not None:
        set_reference = parse_reference(reference_dict(observation.set_reference))
        if set_reference.kind != "set":
            raise CatalogError("invalid_field")
    if observation.kind == "card":
        if observation.set_reference is None or observation.card_number is None:
            raise CatalogError("invalid_field")
        string_value(observation.card_number, 64)
    elif observation.card_number is not None:
        raise CatalogError("invalid_field")


def _resolve_one(
    index: int,
    observation: Observation,
    by_id: dict[str, Entity],
    bindings: dict[ExternalReference, str],
) -> Resolution:
    _validate_observation(observation)
    reference = observation.reference
    # Check immutable facts against explicitly mapped variants before ambiguity handling.
    # This detects poisoning without promoting an unknown variant to a known printing.
    if observation.kind == "card":
        contextual_targets = {
            target_id
            for external, target_id in bindings.items()
            if external.namespace == reference.namespace
            and external.kind == reference.kind
            and external.external_id == reference.external_id
            and external.language == reference.language
        }
        for contextual_id in contextual_targets:
            printing = by_id[contextual_id]
            card = by_id[printing.card_id or ""]
            if card.card_number != observation.card_number:
                raise CatalogError("identity_conflict")
            observed_set_id = (
                bindings.get(observation.set_reference) if observation.set_reference else None
            )
            if observed_set_id is not None and observed_set_id != card.set_id:
                raise CatalogError("identity_conflict")
    if observation.kind == "card" and reference.variant == "unknown":
        return Resolution(
            index,
            "candidate",
            "unknown_variant",
            reference=reference,
            provenance=observation.provenance,
        )
    if observation.kind in ("card", "sealed") and reference.language is None:
        return Resolution(
            index,
            "candidate",
            "unknown_language",
            reference=reference,
            provenance=observation.provenance,
        )
    target_id = bindings.get(reference)
    if target_id is None:
        return Resolution(
            index,
            "candidate",
            "missing_binding",
            reference=reference,
            provenance=observation.provenance,
        )
    target = by_id[target_id]
    expected_set_id = target.set_id
    if target.kind == "printing":
        card = by_id[target.card_id or ""]
        expected_set_id = card.set_id
        if card.card_number != observation.card_number:
            raise CatalogError("identity_conflict")
    if observation.set_reference is not None:
        observed_set_id = bindings.get(observation.set_reference)
        if observed_set_id is None:
            return Resolution(
                index,
                "candidate",
                "missing_binding",
                reference=reference,
                provenance=observation.provenance,
            )
        if observed_set_id != expected_set_id:
            raise CatalogError("identity_conflict")
    if (
        observation.release_date is not None
        and target.release_date is not None
        and observation.release_date != target.release_date
    ):
        raise CatalogError("identity_conflict")
    return Resolution(
        index, "accepted", cmt_id=target_id, reference=reference, provenance=observation.provenance
    )


def resolve(observations: tuple[Observation | RecordError, ...], manifest: Manifest) -> BatchResult:
    if len(observations) > MAX_RECORDS:
        raise CatalogError("input_limit")
    by_id = {entity.cmt_id: entity for entity in manifest.entities}
    bindings = {binding.reference: binding.cmt_id for binding in manifest.bindings}
    records: list[Resolution] = []
    accepted: set[str] = set()
    for index, item in enumerate(observations):
        if isinstance(item, RecordError):
            category = item.category if item.category in ERROR_CATEGORIES else "invalid_field"
            records.append(Resolution(index, "rejected", category))
            continue
        try:
            row = _resolve_one(index, item, by_id, bindings)
        except CatalogError as error:
            row = Resolution(index, "rejected", error.category)
        records.append(row)
        if row.cmt_id is not None:
            accepted.add(row.cmt_id)
    # Include required parents so exported entities form a coherent catalog slice.
    pending = list(accepted)
    while pending:
        entity = by_id[pending.pop()]
        for parent in (entity.card_id, entity.set_id):
            if parent is not None and parent not in accepted:
                accepted.add(parent)
                pending.append(parent)
    return BatchResult(tuple(records), tuple(by_id[cmt_id] for cmt_id in sorted(accepted)))
