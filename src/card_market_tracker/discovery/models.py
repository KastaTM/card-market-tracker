"""Frozen provider-independent Discovery v1 values; constructors are not validation."""

from dataclasses import dataclass
from typing import Literal

from ..catalog.ingestion import ExternalReference, Observation, ReferenceKind
from ..catalog.models import Language


@dataclass(frozen=True)
class DiscoveryContext:
    namespace: str
    kind: ReferenceKind
    language: Language | None

    def to_dict(self) -> dict[str, object]:
        return {"namespace": self.namespace, "kind": self.kind, "language": self.language}


@dataclass(frozen=True)
class DiscoveryRequest:
    version: int
    current_batch_id: str
    history_batch_ids: tuple[str, ...]
    context: DiscoveryContext

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "current_batch_id": self.current_batch_id,
            "history_batch_ids": list(self.history_batch_ids),
            "context": self.context.to_dict(),
        }


@dataclass(frozen=True)
class SnapshotRecord:
    index: int
    status: Literal["accepted", "candidate", "rejected"]
    category: str | None
    cmt_id: str | None
    observation: Observation | None


@dataclass(frozen=True)
class BatchSnapshot:
    version: int
    input_version: int
    resolver_version: int
    batch_id: str
    captured_at: str
    first_persisted_at: str
    fingerprint: str
    context_fingerprint: str
    input_count: int
    accepted_count: int
    candidate_count: int
    rejected_count: int
    result: Literal["ok", "empty", "mixed"]
    records: tuple[SnapshotRecord, ...]


@dataclass(frozen=True)
class BatchEvidence:
    batch_id: str
    captured_at: str
    scope_evidence: Literal["records_verified", "request_attested_empty"]

    def to_dict(self) -> dict[str, object]:
        return {
            "batch_id": self.batch_id,
            "captured_at": self.captured_at,
            "scope_evidence": self.scope_evidence,
        }


@dataclass(frozen=True)
class DiscoveryCounts:
    batches: int
    observations: int
    current_observations: int
    historical_observations: int
    current_references: int
    historical_references: int
    events: int

    def to_dict(self) -> dict[str, object]:
        return {
            "batches": self.batches,
            "observations": self.observations,
            "current_observations": self.current_observations,
            "historical_observations": self.historical_observations,
            "current_references": self.current_references,
            "historical_references": self.historical_references,
            "events": self.events,
        }


@dataclass(frozen=True)
class DiscoveryEvent:
    event_id: str
    type: Literal["SET_REFERENCE_FIRST_OBSERVED", "CANDIDATE_REFERENCE_FIRST_OBSERVED"]
    reference: ExternalReference
    status: Literal["accepted", "candidate"]
    category: str | None
    cmt_id: str | None
    current_batch_id: str
    captured_at: str
    first_observed_in_window_at: str
    comparison_id: str
    current_record_indexes: tuple[int, ...]
    history_batch_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        from .validation import reference_dict

        return {
            "event_id": self.event_id,
            "type": self.type,
            "reference": reference_dict(self.reference),
            "status": self.status,
            "category": self.category,
            "cmt_id": self.cmt_id,
            "current_batch_id": self.current_batch_id,
            "captured_at": self.captured_at,
            "first_observed_in_window_at": self.first_observed_in_window_at,
            "evidence": {
                "comparison_id": self.comparison_id,
                "current_record_indexes": list(self.current_record_indexes),
                "history_batch_ids": list(self.history_batch_ids),
            },
        }


@dataclass(frozen=True)
class DiscoveryResult:
    version: int
    result: Literal["baseline", "no_discoveries", "discoveries"]
    comparison_id: str
    context: DiscoveryContext
    current_batch_id: str
    captured_at: str
    history_batch_ids: tuple[str, ...]
    current: BatchEvidence
    history: tuple[BatchEvidence, ...]
    counts: DiscoveryCounts
    events: tuple[DiscoveryEvent, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "result": self.result,
            "comparison_id": self.comparison_id,
            "context": self.context.to_dict(),
            "current_batch_id": self.current_batch_id,
            "captured_at": self.captured_at,
            "history_batch_ids": list(self.history_batch_ids),
            "window": {
                "scope": "explicit_selected_history",
                "current": self.current.to_dict(),
                "history": [batch.to_dict() for batch in self.history],
            },
            "counts": self.counts.to_dict(),
            "events": [event.to_dict() for event in self.events],
        }
