"""Pure window-relative reference discovery over validated frozen snapshots."""

import hashlib
from dataclasses import replace
from typing import Literal

from ..catalog.ingestion import ExternalReference
from .errors import DiscoveryError
from .input import validate_request
from .models import (
    BatchEvidence,
    BatchSnapshot,
    DiscoveryCounts,
    DiscoveryEvent,
    DiscoveryRequest,
    DiscoveryResult,
    SnapshotRecord,
)
from .validation import (
    MAX_EVENTS,
    MAX_HISTORY,
    MAX_OBSERVATIONS,
    canonical_json,
    record_dict,
    reference_dict,
    snapshot_dict,
    validate_snapshot,
)


def _hash(prefix: str, value: object) -> str:
    return prefix + hashlib.sha256(canonical_json(value).encode("ascii")).hexdigest()


def _scope(batch: BatchSnapshot) -> BatchEvidence:
    return BatchEvidence(
        batch.batch_id,
        batch.captured_at,
        "records_verified" if batch.records else "request_attested_empty",
    )


def _group(
    batch: BatchSnapshot, request: DiscoveryRequest
) -> dict[ExternalReference, tuple[SnapshotRecord, tuple[int, ...]]]:
    grouped: dict[ExternalReference, tuple[SnapshotRecord, tuple[int, ...]]] = {}
    if batch.rejected_count:
        raise DiscoveryError("incomplete_evidence")
    for record in batch.records:
        observation = record.observation
        assert observation is not None  # guaranteed by snapshot business validation
        reference = observation.reference
        if (reference.namespace, reference.kind, reference.language) != (
            request.context.namespace,
            request.context.kind,
            request.context.language,
        ):
            raise DiscoveryError("context_mismatch")
        previous = grouped.get(reference)
        if previous is None:
            grouped[reference] = (record, (record.index,))
        else:
            # Index is positional evidence, not part of duplicate compatibility.
            if record_dict(replace(record, index=0)) != record_dict(replace(previous[0], index=0)):
                raise DiscoveryError("contradictory_snapshot")
            grouped[reference] = (previous[0], (*previous[1], record.index))
    return grouped


def _key(reference: ExternalReference) -> tuple[str, str, str, str, str]:
    return (
        reference.namespace,
        reference.kind,
        reference.external_id,
        reference.language or "",
        reference.variant,
    )


def compare(request: DiscoveryRequest, snapshots: tuple[BatchSnapshot, ...]) -> DiscoveryResult:
    """No storage, provider, resolver, runtime clock or mutable event state is used."""
    verified = validate_request(request)
    if not isinstance(snapshots, tuple):
        raise DiscoveryError("storage_corrupt")
    if len(snapshots) > MAX_HISTORY + 1:
        raise DiscoveryError("input_limit")
    validated = tuple(validate_snapshot(snapshot) for snapshot in snapshots)
    if sum(batch.input_count for batch in validated) > MAX_OBSERVATIONS:
        raise DiscoveryError("input_limit")
    by_id = {batch.batch_id: batch for batch in validated}
    if len(by_id) != len(validated):
        raise DiscoveryError("storage_corrupt")
    selected = {verified.current_batch_id, *verified.history_batch_ids}
    if set(by_id) - selected:
        raise DiscoveryError("storage_corrupt")
    if selected - set(by_id):
        raise DiscoveryError("batch_missing")
    current = by_id[verified.current_batch_id]
    history = tuple(by_id[batch_id] for batch_id in verified.history_batch_ids)
    if any(batch.captured_at >= current.captured_at for batch in history):
        raise DiscoveryError("chronology")
    # Validate every batch even on bootstrap; a malformed baseline cannot succeed.
    grouped = {batch.batch_id: _group(batch, verified) for batch in validated}
    current_refs = grouped[current.batch_id]
    seen = {reference for batch in history for reference in grouped[batch.batch_id]}
    comparison_id = _hash(
        "cmp1:",
        {
            "identity_version": 1,
            "request": verified.to_dict(),
            "snapshots": [
                snapshot_dict(batch)
                for batch in sorted(validated, key=lambda batch: batch.batch_id)
            ],
        },
    )
    events: list[DiscoveryEvent] = []
    if history:
        for reference in sorted(current_refs, key=_key):
            if reference in seen:
                continue
            record, indexes = current_refs[reference]
            event_type: Literal[
                "SET_REFERENCE_FIRST_OBSERVED", "CANDIDATE_REFERENCE_FIRST_OBSERVED"
            ]
            if record.status == "candidate":
                event_type = "CANDIDATE_REFERENCE_FIRST_OBSERVED"
            elif record.status == "accepted" and reference.kind == "set":
                event_type = "SET_REFERENCE_FIRST_OBSERVED"
            else:
                continue
            event_id = _hash(
                "evt1:",
                {
                    "identity_version": 1,
                    "type": event_type,
                    "context": verified.context.to_dict(),
                    "reference": reference_dict(reference),
                    "current_batch_id": current.batch_id,
                    "captured_at": current.captured_at,
                },
            )
            events.append(
                DiscoveryEvent(
                    event_id,
                    event_type,
                    reference,
                    record.status,
                    record.category,
                    record.cmt_id,
                    current.batch_id,
                    current.captured_at,
                    current.captured_at,
                    comparison_id,
                    indexes,
                    verified.history_batch_ids,
                )
            )
    if len(events) > MAX_EVENTS:
        raise DiscoveryError("input_limit")
    historical_observations = sum(batch.input_count for batch in history)
    return DiscoveryResult(
        1,
        "baseline" if not history else "discoveries" if events else "no_discoveries",
        comparison_id,
        verified.context,
        current.batch_id,
        current.captured_at,
        verified.history_batch_ids,
        _scope(current),
        tuple(_scope(batch) for batch in history),
        DiscoveryCounts(
            len(validated),
            current.input_count + historical_observations,
            current.input_count,
            historical_observations,
            len(current_refs),
            len(seen),
            len(events),
        ),
        tuple(events),
    )
