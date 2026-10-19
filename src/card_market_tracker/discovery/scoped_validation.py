"""Pure validation of a complete capture and its exact selected unit."""

import json
import re
from dataclasses import dataclass, replace
from typing import cast

from ..catalog.validation import (
    MAX_BYTES,
    CatalogError,
    _pairs,
    _preflight,
    array_value,
    object_value,
    string_value,
    token_value,
)
from .errors import DiscoveryError
from .models import SnapshotRecord
from .scoped_errors import ScopedDiscoveryError
from .scoped_models import (
    ScopedCapture,
    ScopedDiscoveryRequest,
    ScopedSelection,
    _has_storage_authority,
)
from .scoped_snapshot import validate_scoped_snapshot
from .validation import bounded_value, canonical_json, canonical_timestamp, record_dict

_SYNTHETIC_KEYS = {"version", "acquired_at", "captured_at", "outcome", "units"}
_PINNED_KEYS = {
    "version",
    "source",
    "method",
    "revision",
    "namespace",
    "policy_version",
    "extractor_version",
    "acquired_at",
    "captured_at",
    "timestamp_convention",
    "artifacts",
    "selected_paths",
    "completed_paths",
    "units",
    "source_count",
    "result",
    "evidence_status",
    "bundle_sha256",
    "projection_sha256",
    "counts",
}
_UNIT_KEYS = {"namespace", "kind", "language", "selector", "record_indexes"}
_PINNED_UNIT_KEYS = {
    "selected_paths",
    "completed_paths",
    "source_count",
    "result",
    "accepted_count",
    "candidate_count",
    "rejected_count",
}


@dataclass(frozen=True)
class SelectedCapture:
    capture: ScopedCapture
    selection: ScopedSelection
    scope: dict[str, object]
    unit: dict[str, object]
    records: tuple[SnapshotRecord, ...]
    compatibility: str

    def evidence(self) -> dict[str, object]:
        return {
            **self.selection.to_dict(),
            "captured_at": self.capture.snapshot.captured_at,
            "mode": self.capture.mode,
            "evidence_state": self.capture.evidence_state,
            "scope": self.unit,
            "scope_semantics": json.loads(self.compatibility),
        }


def _paths(value: object) -> list[str]:
    paths = [string_value(path, 256) for path in array_value(value)]
    if len(set(paths)) != len(paths):
        raise CatalogError("invalid_field")
    return sorted(paths)


def _integer(value: object) -> int:
    if type(value) is not int or value < 0:
        raise CatalogError("invalid_field")
    return value


def validate_capture(
    capture: object, request: ScopedDiscoveryRequest, selection: ScopedSelection
) -> SelectedCapture:
    return _validate_capture(capture, request, selection)


def _validate_capture(
    capture: object,
    request: ScopedDiscoveryRequest,
    selection: ScopedSelection,
    *,
    multi_revision: bool = False,
) -> SelectedCapture:
    """No Python constructor, enum or self-attested digest grants DB verification."""
    try:
        if not isinstance(capture, ScopedCapture):
            raise ScopedDiscoveryError("unsupported_evidence")
        if (capture.mode, capture.evidence_state) not in (
            ("synthetic", "producer_declared"),
            ("pinned", "verified_local_pinned_bundle"),
        ):
            raise ScopedDiscoveryError("unsupported_evidence")
        pinned = capture.mode == "pinned"
        batch = validate_scoped_snapshot(
            capture.snapshot, provenance="observed" if pinned else "synthetic"
        )
        if batch.batch_id != selection.batch_id:
            raise CatalogError("invalid_field")
        if re.fullmatch("[0-9a-f]{64}", capture.capture_fingerprint) is None:
            raise CatalogError("invalid_field")
        if not isinstance(capture.scope_json, str):
            raise CatalogError("invalid_shape")
        if len(capture.scope_json.encode("utf-8")) > MAX_BYTES:
            raise CatalogError("input_limit")
        _preflight(capture.scope_json)
        scope = object_value(json.loads(capture.scope_json, object_pairs_hook=_pairs))
        bounded_value(scope)
        if not _has_storage_authority(capture):
            raise ScopedDiscoveryError("unsupported_evidence")
        if set(scope) != (_PINNED_KEYS if pinned else _SYNTHETIC_KEYS):
            raise CatalogError("invalid_shape")
        versions = (1, 2) if pinned and multi_revision else (1,)
        if type(scope["version"]) is not int or scope["version"] not in versions:
            raise CatalogError("unsupported_version")
        if canonical_timestamp(scope["captured_at"]) != batch.captured_at:
            raise CatalogError("invalid_field")
        canonical_timestamp(scope["acquired_at"])
        units = array_value(scope["units"], 32)
        if not units:
            raise CatalogError("invalid_field")
        seen: set[int] = set()
        contexts: set[str] = set()
        normalized_units: list[dict[str, object]] = []
        selected_units: list[dict[str, object]] = []
        for item in units:
            unit = object_value(item)
            if set(unit) != _UNIT_KEYS | (
                _PINNED_UNIT_KEYS if pinned else {"selected", "completed"}
            ):
                raise CatalogError("invalid_shape")
            token_value(unit["namespace"])
            if unit["kind"] not in ("set", "card", "sealed") or unit["language"] not in (
                "es",
                "en",
                None,
            ):
                raise CatalogError("invalid_field")
            string_value(unit["selector"], 256)
            context_key = canonical_json(
                [unit[key] for key in ("namespace", "kind", "language", "selector")]
            )
            if context_key in contexts:
                raise ScopedDiscoveryError("ambiguous_unit")
            contexts.add(context_key)
            selected_key, completed_key = (
                ("selected_paths", "completed_paths") if pinned else ("selected", "completed")
            )
            paths, completed = _paths(unit[selected_key]), _paths(unit[completed_key])
            if not paths or not set(completed) <= set(paths):
                raise CatalogError("invalid_field")
            indexes = array_value(unit["record_indexes"])
            for index in indexes:
                index = _integer(index)
                if index >= len(batch.records) or index in seen:
                    raise CatalogError("invalid_field")
                seen.add(index)
                observation = batch.records[index].observation
                if observation is not None and (
                    observation.reference.namespace,
                    observation.kind,
                    observation.reference.language,
                ) != (unit["namespace"], unit["kind"], unit["language"]):
                    raise CatalogError("invalid_field")
            normalized = {
                **unit,
                selected_key: paths,
                completed_key: completed,
                "record_indexes": sorted(cast(list[int], indexes)),
            }
            if pinned:
                unit_records = [batch.records[index] for index in cast(list[int], indexes)]
                if (
                    _integer(unit["source_count"]) != len(unit_records)
                    or not unit_records
                    or unit["result"] != "complete_nonempty"
                    or paths != completed
                    or tuple(
                        _integer(unit[key])
                        for key in ("accepted_count", "candidate_count", "rejected_count")
                    )
                    != tuple(
                        sum(row.status == status for row in unit_records)
                        for status in ("accepted", "candidate", "rejected")
                    )
                ):
                    raise CatalogError("invalid_field")
            # Contradictions are invalid evidence even in an unselected unit.
            # The explicit selection must not hide an internally inconsistent batch.
            reference_records: dict[str, dict[str, object]] = {}
            for index in cast(list[int], indexes):
                row = batch.records[index]
                if row.observation is None:
                    continue
                key = canonical_json(
                    {
                        "namespace": row.observation.reference.namespace,
                        "kind": row.observation.reference.kind,
                        "external_id": row.observation.reference.external_id,
                        "language": row.observation.reference.language,
                        "variant": row.observation.reference.variant,
                    }
                )
                content = record_dict(replace(row, index=0))
                if key in reference_records and reference_records[key] != content:
                    raise ScopedDiscoveryError("contradictory_snapshot")
                reference_records[key] = content
            normalized_units.append(normalized)
            if (unit["namespace"], unit["kind"], unit["language"], unit["selector"]) == (
                request.context.namespace,
                request.context.kind,
                request.context.language,
                selection.selector,
            ):
                selected_units.append(normalized)
        if seen != set(range(len(batch.records))):
            raise CatalogError("invalid_field")
        scope = {**scope, "units": sorted(normalized_units, key=canonical_json)}
        if not selected_units:
            raise ScopedDiscoveryError("unit_missing")
        selected = selected_units[0]
        if pinned:
            if (
                scope["result"] != "complete_nonempty"
                or scope["evidence_status"] != capture.evidence_state
                or _integer(scope["source_count"]) != batch.input_count
                or object_value(scope["counts"])
                != {
                    "input": batch.input_count,
                    "accepted": batch.accepted_count,
                    "candidates": batch.candidate_count,
                    "rejected": batch.rejected_count,
                }
                or _paths(scope["selected_paths"]) != _paths(scope["completed_paths"])
            ):
                raise CatalogError("invalid_field")
            semantics = {
                key: scope[key]
                for key in (
                    "version",
                    "source",
                    "method",
                    "revision",
                    "namespace",
                    "policy_version",
                    "extractor_version",
                    "timestamp_convention",
                    "evidence_status",
                    "bundle_sha256",
                    "projection_sha256",
                    "artifacts",
                )
            }
            if multi_revision:
                # Storage's content-bound profile receipt authorizes this exact
                # pair. Acquisition evidence stays intact in scope/identity;
                # only the compatibility key omits per-capture differences.
                semantics = {
                    key: scope[key]
                    for key in (
                        "source",
                        "method",
                        "namespace",
                        "policy_version",
                        "extractor_version",
                        "timestamp_convention",
                        "evidence_status",
                    )
                }
            scope["selected_paths"] = _paths(scope["selected_paths"])
            scope["completed_paths"] = _paths(scope["completed_paths"])
        else:
            if scope["outcome"] not in ("complete", "partial", "failed"):
                raise CatalogError("invalid_field")
            if scope["outcome"] != "complete":
                raise ScopedDiscoveryError("incomplete_evidence")
            if any(unit["selected"] != unit["completed"] for unit in normalized_units):
                raise ScopedDiscoveryError("incomplete_evidence")
            semantics = {
                "version": scope["version"],
                "method": "generic_synthetic_capture",
                "policy": "producer_declared_complete",
                "semantics": "capture_scope_v1",
            }
        records = tuple(
            batch.records[index] for index in cast(list[int], selected["record_indexes"])
        )
        if any(record.status == "rejected" for record in records):
            raise ScopedDiscoveryError("incomplete_evidence")
        selected_paths = selected["selected_paths" if pinned else "selected"]
        compatibility = canonical_json(
            {
                "family": capture.evidence_state,
                "semantics": semantics,
                "paths": selected_paths,
                "context": request.context.to_dict(),
                "selector": selection.selector,
            }
        )
        return SelectedCapture(capture, selection, scope, selected, records, compatibility)
    except ScopedDiscoveryError:
        raise
    except DiscoveryError as error:
        raise ScopedDiscoveryError(error.category) from None
    except CatalogError as error:
        raise ScopedDiscoveryError(
            "input_limit" if error.category == "input_limit" else "storage_corrupt"
        ) from None
    except (AttributeError, KeyError, TypeError, ValueError, UnicodeError, RecursionError):
        raise ScopedDiscoveryError("storage_corrupt") from None
