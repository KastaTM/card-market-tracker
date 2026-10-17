"""V2 structural validation preserves actual provenance; grants no admission authority."""

import re

from ..catalog.ingestion import Observation
from ..catalog.manifest import parse_reference
from ..catalog.validation import (
    ERROR_CATEGORIES,
    MAX_RECORDS,
    CatalogError,
    date_value,
    string_value,
    uuid_value,
    version_one,
)
from .errors import DiscoveryError
from .models import BatchSnapshot, SnapshotRecord
from .validation import (
    CANDIDATE_CATEGORIES,
    bounded_value,
    canonical_timestamp,
    record_dict,
    reference_dict,
)


def _observation(observation: Observation, captured_at: str, provenance: str) -> None:
    reference = parse_reference(reference_dict(observation.reference))
    if observation.kind != reference.kind or observation.provenance != provenance:
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


def _record(record: SnapshotRecord, index: int, capture: str, provenance: str) -> None:
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
        _observation(record.observation, capture, provenance)
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


def validate_scoped_snapshot(snapshot: object, *, provenance: str) -> BatchSnapshot:
    """Malformed frozen business evidence is corruption; bounds fail input_limit."""
    try:
        if provenance not in ("observed", "synthetic") or not isinstance(snapshot, BatchSnapshot):
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
            _record(record, index, capture, provenance)
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
