"""Deterministic provider/SQLite-independent comparison over explicit scoped captures."""

import hashlib
from dataclasses import replace

from ..catalog.ingestion import ExternalReference
from .models import SnapshotRecord
from .scoped_errors import ScopedDiscoveryError
from .scoped_input import validate_request
from .scoped_models import ScopedCapture, ScopedDiscoveryRequest, ScopedDiscoveryResult
from .scoped_validation import SelectedCapture, validate_capture
from .validation import (
    MAX_EVENTS,
    MAX_HISTORY,
    MAX_OBSERVATIONS,
    canonical_json,
    record_dict,
    reference_dict,
    snapshot_dict,
)


def _hash(prefix: str, value: object) -> str:
    return prefix + hashlib.sha256(canonical_json(value).encode("ascii")).hexdigest()


def _identity(selected: SelectedCapture) -> dict[str, object]:
    capture = selected.capture
    return {
        "snapshot": snapshot_dict(capture.snapshot),
        "mode": capture.mode,
        "evidence_state": capture.evidence_state,
        "scope": selected.scope,
        "capture_fingerprint": capture.capture_fingerprint,
        "selection": selected.selection.to_dict(),
    }


def _group(
    selected: SelectedCapture,
) -> dict[ExternalReference, tuple[SnapshotRecord, tuple[int, ...]]]:
    grouped: dict[ExternalReference, tuple[SnapshotRecord, tuple[int, ...]]] = {}
    for record in selected.records:
        observation = record.observation
        assert observation is not None
        reference = observation.reference
        previous = grouped.get(reference)
        if previous is None:
            grouped[reference] = (record, (record.index,))
        else:
            if record_dict(replace(record, index=0)) != record_dict(replace(previous[0], index=0)):
                raise ScopedDiscoveryError("contradictory_snapshot")
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


def compare(
    request: ScopedDiscoveryRequest, captures: tuple[ScopedCapture, ...]
) -> ScopedDiscoveryResult:
    """Validate even a baseline; never consult SQLite, provider code or a manifest."""
    verified = validate_request(request)
    if not isinstance(captures, tuple):
        raise ScopedDiscoveryError("storage_corrupt")
    if len(captures) > MAX_HISTORY + 1:
        raise ScopedDiscoveryError("input_limit")
    if any(not isinstance(capture, ScopedCapture) for capture in captures):
        raise ScopedDiscoveryError("storage_corrupt")
    try:
        by_id = {capture.snapshot.batch_id: capture for capture in captures}
    except (AttributeError, TypeError):
        raise ScopedDiscoveryError("storage_corrupt") from None
    if len(by_id) != len(captures):
        raise ScopedDiscoveryError("storage_corrupt")
    selections = (verified.current, *verified.history)
    required = {selection.batch_id for selection in selections}
    if set(by_id) - required:
        raise ScopedDiscoveryError("storage_corrupt")
    if required - set(by_id):
        raise ScopedDiscoveryError("batch_missing")
    selected = tuple(
        validate_capture(by_id[selection.batch_id], verified, selection) for selection in selections
    )
    if sum(item.capture.snapshot.input_count for item in selected) > MAX_OBSERVATIONS:
        raise ScopedDiscoveryError("input_limit")
    current, *history = selected
    if any(item.compatibility != current.compatibility for item in history):
        raise ScopedDiscoveryError("scope_mismatch")
    batch = current.capture.snapshot
    if any(item.capture.snapshot.captured_at >= batch.captured_at for item in history):
        raise ScopedDiscoveryError("chronology")
    grouped = {item.selection.batch_id: _group(item) for item in selected}
    current_refs = grouped[batch.batch_id]
    seen = {ref for item in history for ref in grouped[item.selection.batch_id]}
    comparison_id = _hash(
        "cmp2:",
        {
            "identity_version": 2,
            "request": verified.to_dict(),
            "captures": [
                _identity(item)
                for item in sorted(selected, key=lambda item: item.selection.batch_id)
            ],
        },
    )
    events: list[dict[str, object]] = []
    if history:
        for reference in sorted(current_refs, key=_key):
            if reference in seen:
                continue
            record, indexes = current_refs[reference]
            if record.status == "candidate":
                event_type = "CANDIDATE_REFERENCE_FIRST_OBSERVED"
            elif record.status == "accepted" and reference.kind == "set":
                event_type = "SET_REFERENCE_FIRST_OBSERVED"
            else:
                continue
            event_id = _hash(
                "evt2:",
                {
                    "identity_version": 2,
                    "type": event_type,
                    "context": verified.context.to_dict(),
                    "reference": reference_dict(reference),
                    "current": _identity(current),
                    "record": record_dict(replace(record, index=0)),
                    "record_indexes": list(indexes),
                },
            )
            events.append(
                {
                    "event_id": event_id,
                    "type": event_type,
                    "reference": reference_dict(reference),
                    "status": record.status,
                    "category": record.category,
                    "cmt_id": record.cmt_id,
                    "current_batch_id": batch.batch_id,
                    "captured_at": batch.captured_at,
                    "first_observed_in_window_at": batch.captured_at,
                    "evidence": {
                        "comparison_id": comparison_id,
                        "current_record_indexes": list(indexes),
                        "current": current.evidence(),
                        "history": [item.evidence() for item in history],
                    },
                }
            )
    if len(events) > MAX_EVENTS:
        raise ScopedDiscoveryError("input_limit")
    return ScopedDiscoveryResult(
        {
            "version": 2,
            "result": "baseline" if not history else "discoveries" if events else "no_discoveries",
            "comparison_id": comparison_id,
            "context": verified.context.to_dict(),
            "current": current.evidence(),
            "history": [item.evidence() for item in history],
            "window": {"scope": "explicit_selected_capture_units"},
            "counts": {
                "validated_batches": len(selected),
                "validated_records": sum(item.capture.snapshot.input_count for item in selected),
                "current_selected_records": len(current.records),
                "historical_selected_records": sum(len(item.records) for item in history),
                "current_selected_references": len(current_refs),
                "historical_selected_references": len(seen),
                "events": len(events),
            },
            "events": events,
        }
    )
