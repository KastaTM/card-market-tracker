"""Provider-independent validation of storage-issued profile membership."""

from dataclasses import dataclass

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


@dataclass(frozen=True)
class ProfileSelectedCapture(SelectedCapture):
    profile: str

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
        }


def validate_capture(
    value: object, request: MultiRevisionRequest, selection: ScopedSelection
) -> SelectedCapture:
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
        )
    except ScopedDiscoveryError:
        raise
    except (AttributeError, KeyError, TypeError, ValueError, UnicodeError, RecursionError):
        raise ScopedDiscoveryError("storage_corrupt") from None
