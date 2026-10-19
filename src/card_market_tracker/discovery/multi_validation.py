"""Provider-independent validation of storage-issued profile membership."""

import json
from dataclasses import dataclass

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
from .multi_models import (
    REVIEWED_PAIR_PROFILE,
    SYNTHETIC_PROFILE,
    MultiRevisionRequest,
    ProfiledCapture,
    _has_profile_authority,
)
from .scoped_errors import ScopedDiscoveryError
from .scoped_models import ScopedSelection
from .scoped_validation import SelectedCapture, _validate_capture
from .validation import bounded_value, canonical_json


@dataclass(frozen=True)
class ProfileSelectedCapture(SelectedCapture):
    profile: str
    extraction_json: str

    def evidence(self) -> dict[str, object]:
        keys = (
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
            "evidence_status",
            "bundle_sha256",
            "projection_sha256",
            "outcome",
        )
        return {
            **super().evidence(),
            "profile": self.profile,
            "acquisition": {key: self.scope[key] for key in keys if key in self.scope},
            "extraction_proof": json.loads(self.extraction_json),
        }


def _extraction_proof(value: ProfiledCapture) -> str:
    raw = value.extraction_json
    if type(raw) is not str or len(raw.encode("utf-8")) > MAX_BYTES:
        raise CatalogError("input_limit")
    _preflight(raw)
    proof = json.loads(raw, object_pairs_hook=_pairs)
    bounded_value(proof)
    if value.profile == SYNTHETIC_PROFILE:
        if proof is not None:
            raise CatalogError("invalid_shape")
        return canonical_json(None)
    document = object_value(proof)
    if set(document) != {"version", "extractor", "fields"}:
        raise CatalogError("invalid_shape")
    if type(document["version"]) is not int or document["version"] != 1:
        raise CatalogError("unsupported_version")
    token_value(document["extractor"])
    fields = array_value(document["fields"], 32)
    if not fields:
        raise CatalogError("invalid_shape")
    seen = set()
    for item in fields:
        field = object_value(item)
        if set(field) != {"path", "field", "start", "end", "transformation"}:
            raise CatalogError("invalid_shape")
        key = (string_value(field["path"], 256), string_value(field["field"], 128))
        if key in seen:
            raise CatalogError("invalid_field")
        seen.add(key)
        start, end = field["start"], field["end"]
        if (
            type(start) is not int
            or type(end) is not int
            or not 0 <= start < end <= 65536
            or field["transformation"] != "exact_literal"
        ):
            raise CatalogError("invalid_field")
    return canonical_json(proof)


def validate_capture(
    value: object, request: MultiRevisionRequest, selection: ScopedSelection
) -> ProfileSelectedCapture:
    try:
        if type(value) is not ProfiledCapture or not _has_profile_authority(value):
            raise ScopedDiscoveryError("unsupported_evidence")
        if value.profile != request.profile:
            raise ScopedDiscoveryError("scope_mismatch")
        expected = {
            REVIEWED_PAIR_PROFILE: ("pinned", "verified_local_pinned_bundle"),
            SYNTHETIC_PROFILE: ("synthetic", "producer_declared"),
        }[request.profile]
        if (value.capture.mode, value.capture.evidence_state) != expected:
            raise ScopedDiscoveryError("unsupported_evidence")
        selected = _validate_capture(
            value.capture, request.scoped_request(), selection, multi_revision=True
        )
        return ProfileSelectedCapture(
            selected.capture,
            selected.selection,
            selected.scope,
            selected.unit,
            selected.records,
            selected.compatibility,
            request.profile,
            _extraction_proof(value),
        )
    except ScopedDiscoveryError:
        raise
    except CatalogError as error:
        raise ScopedDiscoveryError(
            "input_limit" if error.category == "input_limit" else "storage_corrupt"
        ) from None
    except (AttributeError, KeyError, TypeError, ValueError, UnicodeError, RecursionError):
        raise ScopedDiscoveryError("storage_corrupt") from None
