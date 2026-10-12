"""Compose validated synthetic evidence and resolution, independent of SQLite."""

import hashlib
from dataclasses import replace

from ..catalog.ingestion import Observation, RecordError
from ..catalog.manifest import Manifest
from ..catalog.resolver import resolve
from ..catalog.validation import (
    ERROR_CATEGORIES,
    MAX_RECORDS,
    CatalogError,
    uuid_value,
    version_one,
)
from .errors import PersistenceError
from .input import (
    bounded_value,
    canonical_json,
    entity_dict,
    observation_dict,
    reference_value,
    utc_timestamp,
    validated_manifest,
)
from .models import PersistedRecord, PersistenceBatch


def _capture(value: object) -> str:
    captured_at = utc_timestamp(value, required=True)
    assert captured_at is not None
    return captured_at


def _items(
    observations: tuple[Observation | RecordError, ...], captured_at: str
) -> tuple[Observation | RecordError, ...]:
    if not isinstance(observations, tuple):
        raise CatalogError("invalid_shape")
    if len(observations) > MAX_RECORDS:
        raise CatalogError("input_limit")
    # Check every producer claim before any record can become a safe rejection.
    for item in observations:
        if isinstance(item, Observation) and item.provenance != "synthetic":
            raise PersistenceError("synthetic_only")
    serialized: list[object] = []
    for index, item in enumerate(observations):
        if isinstance(item, RecordError):
            if type(item.index) is not int or item.index != index:
                raise PersistenceError("resolution_mismatch")
            if not isinstance(item.category, str) or item.category not in ERROR_CATEGORIES:
                raise CatalogError("invalid_field")
            serialized.append({"index": index, "category": item.category})
        elif isinstance(item, Observation):
            serialized.append(observation_dict(item))
        else:
            raise CatalogError("invalid_shape")
    bounded_value(serialized)
    normalized: list[Observation | RecordError] = []
    for index, item in enumerate(observations):
        if isinstance(item, RecordError):
            normalized.append(item)
            continue
        declared = utc_timestamp(item.captured_at)
        if declared is not None and declared != captured_at:
            raise PersistenceError("capture_conflict")
        try:
            updated = utc_timestamp(item.provider_updated_at)
        except PersistenceError:
            normalized.append(RecordError(index, "invalid_field"))
            continue
        normalized.append(replace(item, captured_at=captured_at, provider_updated_at=updated))
    return tuple(normalized)


def build_batch(
    batch_id: object,
    captured_at: object,
    observations: tuple[Observation | RecordError, ...],
    manifest: object,
) -> PersistenceBatch:
    """Build a persistible batch from generic P1a evidence, including sealed.

    RecordErrors are trusted categorical producer assertions: no original invalid
    payload exists here to independently reconstruct their validation outcome.
    """
    try:
        token = uuid_value(batch_id)
        capture = _capture(captured_at)
        curated = validated_manifest(manifest)
        normalized = _items(observations, capture)
        result = resolve(normalized, curated)
        if len(result.records) != len(normalized):
            raise PersistenceError("resolution_mismatch")
        records: list[PersistedRecord] = []
        for index, row in enumerate(result.records):
            if type(row.index) is not int or row.index != index:
                raise PersistenceError("resolution_mismatch")
            item = normalized[index]
            observation: Observation | None = None
            if row.status != "rejected":
                if (
                    not isinstance(item, Observation)
                    or row.reference != item.reference
                    or row.provenance != item.provenance
                ):
                    raise PersistenceError("resolution_mismatch")
                observation = item
            records.append(
                PersistedRecord(index, row.status, row.category, row.cmt_id, observation)
            )
        return PersistenceBatch(1, token, capture, curated, tuple(records), result.entities)
    except CatalogError as error:
        raise PersistenceError(error.category) from None


def validate_batch(batch: PersistenceBatch) -> PersistenceBatch:
    """Reparse authority and recompute snapshots for every public write."""
    try:
        if not isinstance(batch, PersistenceBatch):
            raise CatalogError("invalid_shape")
        version_one(batch.version)
        if not isinstance(batch.records, tuple) or not isinstance(batch.entities, tuple):
            raise CatalogError("invalid_shape")
        if len(batch.records) > MAX_RECORDS:
            raise CatalogError("input_limit")
        observations: list[Observation | RecordError] = []
        for index, row in enumerate(batch.records):
            if not isinstance(row, PersistedRecord):
                raise CatalogError("invalid_shape")
            if type(row.index) is not int or row.index != index:
                raise PersistenceError("resolution_mismatch")
            if row.status == "rejected":
                if row.observation is not None or row.cmt_id is not None:
                    raise PersistenceError("resolution_mismatch")
                if not isinstance(row.category, str) or row.category not in ERROR_CATEGORIES:
                    raise CatalogError("invalid_field")
                observations.append(RecordError(index, row.category))
            elif row.status in ("accepted", "candidate"):
                if not isinstance(row.observation, Observation):
                    raise PersistenceError("resolution_mismatch")
                observations.append(row.observation)
            else:
                raise CatalogError("invalid_field")
        verified = build_batch(
            batch.batch_id, batch.captured_at, tuple(observations), batch.manifest
        )
        for actual, expected in zip(batch.records, verified.records, strict=True):
            if (actual.index, actual.status, actual.category, actual.cmt_id) != (
                expected.index,
                expected.status,
                expected.category,
                expected.cmt_id,
            ):
                raise PersistenceError("resolution_mismatch")
        supplied = validated_manifest(Manifest(batch.entities, ())).entities
        if supplied != verified.entities:
            raise PersistenceError("resolution_mismatch")
        return verified
    except CatalogError as error:
        raise PersistenceError(error.category) from None


def _context(batch: PersistenceBatch) -> dict[str, object]:
    bindings = [
        {"reference": reference_value(binding.reference), "cmt_id": binding.cmt_id}
        for binding in batch.manifest.bindings
    ]
    return {
        "manifest_version": 1,
        "entities": [
            entity_dict(entity)
            for entity in sorted(batch.manifest.entities, key=lambda e: e.cmt_id)
        ],
        "bindings": sorted(bindings, key=canonical_json),
    }


def canonical_payload(batch: PersistenceBatch) -> dict[str, object]:
    verified = validate_batch(batch)
    return {
        "version": verified.version,
        "ingestion_version": 1,
        "resolver_version": 1,
        "captured_at": verified.captured_at,
        "context": _context(verified),
        "entities": [entity_dict(entity) for entity in verified.entities],
        "records": [
            {
                "index": row.index,
                "status": row.status,
                "category": row.category,
                "cmt_id": row.cmt_id,
                "observation": None
                if row.observation is None
                else observation_dict(row.observation),
            }
            for row in verified.records
        ],
    }


def fingerprint(batch: PersistenceBatch) -> str:
    return hashlib.sha256(canonical_json(canonical_payload(batch)).encode("ascii")).hexdigest()


def context_fingerprint(batch: PersistenceBatch) -> str:
    return hashlib.sha256(
        canonical_json(_context(validate_batch(batch))).encode("ascii")
    ).hexdigest()
