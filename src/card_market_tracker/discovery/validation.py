"""Revalidate frozen generic snapshots without SQLite, providers or resolution."""

import json
import re
from datetime import UTC, datetime

from ..catalog.ingestion import ExternalReference, Observation
from ..catalog.manifest import parse_reference
from ..catalog.validation import (
    ERROR_CATEGORIES,
    MAX_BYTES,
    MAX_RECORDS,
    CatalogError,
    date_value,
    string_value,
    uuid_value,
    validate_structure,
    version_one,
)
from .errors import DiscoveryError
from .models import BatchSnapshot, SnapshotRecord

MAX_HISTORY = 32
MAX_OBSERVATIONS = 33_000
MAX_EVENTS = 1000
CANDIDATE_CATEGORIES = frozenset({"missing_binding", "unknown_variant", "unknown_language"})


def canonical_json(value: object) -> str:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def bounded_value(value: object) -> None:
    """P1a budgets apply to a request or one record, never the whole history."""
    validate_structure(value)
    if len(json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")) > MAX_BYTES:
        raise CatalogError("input_limit")


def canonical_timestamp(value: object) -> str:
    text = string_value(value, 40)
    try:
        instant = datetime.fromisoformat(text)
        normalized = (
            instant.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
        )
        if instant.tzinfo is None or text != normalized:
            raise ValueError
    except (ValueError, OverflowError, OSError):
        raise CatalogError("invalid_field") from None
    return text


def reference_dict(reference: ExternalReference) -> dict[str, object]:
    if not isinstance(reference, ExternalReference):
        raise CatalogError("invalid_shape")
    return {
        "namespace": reference.namespace,
        "kind": reference.kind,
        "external_id": reference.external_id,
        "language": reference.language,
        "variant": reference.variant,
    }


def observation_dict(observation: Observation) -> dict[str, object]:
    if not isinstance(observation, Observation):
        raise CatalogError("invalid_shape")
    return {
        "kind": observation.kind,
        "reference": reference_dict(observation.reference),
        "name": observation.name,
        "set_reference": None
        if observation.set_reference is None
        else reference_dict(observation.set_reference),
        "card_number": observation.card_number,
        "release_date": observation.release_date,
        "provider_updated_at": observation.provider_updated_at,
        "captured_at": observation.captured_at,
        "provenance": observation.provenance,
    }


def record_dict(record: SnapshotRecord) -> dict[str, object]:
    if not isinstance(record, SnapshotRecord):
        raise CatalogError("invalid_shape")
    return {
        "index": record.index,
        "status": record.status,
        "category": record.category,
        "cmt_id": record.cmt_id,
        "observation": None if record.observation is None else observation_dict(record.observation),
    }


def snapshot_dict(snapshot: BatchSnapshot) -> dict[str, object]:
    """Pertinent validated comparison content, independent of persistence time."""
    return {
        "version": snapshot.version,
        "input_version": snapshot.input_version,
        "resolver_version": snapshot.resolver_version,
        "batch_id": snapshot.batch_id,
        "captured_at": snapshot.captured_at,
        "fingerprint": snapshot.fingerprint,
        "context_fingerprint": snapshot.context_fingerprint,
        "input_count": snapshot.input_count,
        "accepted_count": snapshot.accepted_count,
        "candidate_count": snapshot.candidate_count,
        "rejected_count": snapshot.rejected_count,
        "result": snapshot.result,
        "records": [record_dict(record) for record in snapshot.records],
    }


def _observation(observation: Observation, captured_at: str) -> None:
    reference = parse_reference(reference_dict(observation.reference))
    if observation.kind != reference.kind or observation.provenance != "synthetic":
        raise CatalogError("invalid_field")
    string_value(observation.name)
    date_value(observation.release_date)
    if observation.provider_updated_at is not None:
        canonical_timestamp(observation.provider_updated_at)
    if canonical_timestamp(observation.captured_at) != captured_at:
        raise CatalogError("invalid_field")
    if observation.set_reference is not None:
        parent = parse_reference(reference_dict(observation.set_reference))
        if parent.kind != "set":
            raise CatalogError("invalid_field")
    if observation.kind == "card":
        if observation.set_reference is None or observation.card_number is None:
            raise CatalogError("invalid_field")
        string_value(observation.card_number, 64)
    elif observation.card_number is not None:
        raise CatalogError("invalid_field")


def _record(record: SnapshotRecord, index: int, capture: str) -> None:
    bounded_value(record_dict(record))
    if type(record.index) is not int or record.index != index:
        raise CatalogError("invalid_field")
    if record.status == "accepted":
        if record.category is not None:
            raise CatalogError("invalid_field")
        uuid_value(record.cmt_id)
    elif record.status in ("candidate", "rejected"):
        if (
            record.cmt_id is not None
            or not isinstance(record.category, str)
            or record.category
            not in (CANDIDATE_CATEGORIES if record.status == "candidate" else ERROR_CATEGORIES)
        ):
            raise CatalogError("invalid_field")
    else:
        raise CatalogError("invalid_field")
    if record.status == "rejected":
        if record.observation is not None:
            raise CatalogError("invalid_field")
    else:
        if not isinstance(record.observation, Observation):
            raise CatalogError("invalid_shape")
        _observation(record.observation, capture)
        reference = record.observation.reference
        if record.status == "accepted" and (
            (reference.kind in ("card", "sealed") and reference.language is None)
            or (reference.kind == "card" and reference.variant == "unknown")
        ):
            raise CatalogError("invalid_field")
        if record.category == "unknown_variant" and not (
            reference.kind == "card" and reference.variant == "unknown"
        ):
            raise CatalogError("invalid_field")
        if record.category == "unknown_language" and not (
            reference.kind in ("card", "sealed")
            and reference.language is None
            and not (reference.kind == "card" and reference.variant == "unknown")
        ):
            raise CatalogError("invalid_field")
        if record.category == "missing_binding" and (
            (reference.kind == "card" and reference.variant == "unknown")
            or (reference.kind in ("card", "sealed") and reference.language is None)
        ):
            # Resolver v1 reports unknown variant/language before checking bindings.
            # These frozen facts require no manifest or historical re-resolution.
            raise CatalogError("invalid_field")


def validate_snapshot(snapshot: object) -> BatchSnapshot:
    """Malformed frozen business evidence is corruption; bounds fail input_limit."""
    try:
        if not isinstance(snapshot, BatchSnapshot):
            raise CatalogError("invalid_shape")
        for version in (snapshot.version, snapshot.input_version, snapshot.resolver_version):
            version_one(version)
        uuid_value(snapshot.batch_id)
        capture = canonical_timestamp(snapshot.captured_at)
        canonical_timestamp(snapshot.first_persisted_at)
        for fingerprint in (snapshot.fingerprint, snapshot.context_fingerprint):
            if (
                not isinstance(fingerprint, str)
                or re.fullmatch(r"[0-9a-f]{64}", fingerprint) is None
            ):
                raise CatalogError("invalid_field")
        if not isinstance(snapshot.records, tuple):
            raise CatalogError("invalid_shape")
        if len(snapshot.records) > MAX_RECORDS:
            raise CatalogError("input_limit")
        counts = (
            snapshot.input_count,
            snapshot.accepted_count,
            snapshot.candidate_count,
            snapshot.rejected_count,
        )
        if any(type(count) is not int or count < 0 for count in counts):
            raise CatalogError("invalid_field")
        if any(count > MAX_RECORDS for count in counts):
            raise CatalogError("input_limit")
        if snapshot.input_count != len(snapshot.records):
            raise CatalogError("invalid_field")
        for index, record in enumerate(snapshot.records):
            _record(record, index, capture)
        actual = tuple(
            sum(record.status == status for record in snapshot.records)
            for status in ("accepted", "candidate", "rejected")
        )
        if counts[1:] != actual or sum(actual) != snapshot.input_count:
            raise CatalogError("invalid_field")
        expected = (
            "empty"
            if not snapshot.records
            else ("ok" if snapshot.accepted_count == snapshot.input_count else "mixed")
        )
        if snapshot.result != expected:
            raise CatalogError("invalid_field")
        return snapshot
    except CatalogError as error:
        raise DiscoveryError(
            "input_limit" if error.category == "input_limit" else "storage_corrupt"
        ) from None
    except (AttributeError, TypeError, ValueError, UnicodeError, RecursionError):
        raise DiscoveryError("storage_corrupt") from None
