"""Immutable values at the independently validated persistence boundary."""

from dataclasses import dataclass
from typing import Literal

from ..catalog.ingestion import Observation
from ..catalog.manifest import Manifest
from ..catalog.models import Entity


@dataclass(frozen=True)
class PersistedRecord:
    index: int
    status: Literal["accepted", "candidate", "rejected"]
    category: str | None
    cmt_id: str | None
    observation: Observation | None


@dataclass(frozen=True)
class PersistenceBatch:
    version: int
    batch_id: str
    captured_at: str
    manifest: Manifest
    records: tuple[PersistedRecord, ...]
    entities: tuple[Entity, ...]


@dataclass(frozen=True)
class WriteResult:
    result: Literal["ok", "empty", "mixed", "replay"]
    batch_id: str
    first_persisted_at: str
    input_count: int
    accepted_count: int
    candidate_count: int
    rejected_count: int
    committed_observations: int
    committed_entities: int

    def to_dict(self) -> dict[str, object]:
        return {
            "version": 1,
            "result": self.result,
            "batch_id": self.batch_id,
            "first_persisted_at": self.first_persisted_at,
            "counts": {
                "input": self.input_count,
                "accepted": self.accepted_count,
                "candidates": self.candidate_count,
                "rejected": self.rejected_count,
            },
            "committed": {
                "observations": self.committed_observations,
                "entities": self.committed_entities,
            },
        }
