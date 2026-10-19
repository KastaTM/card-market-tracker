"""Generic profile-bound values for the explicit third comparison contract."""

import hashlib
from dataclasses import dataclass, field

from .models import DiscoveryContext
from .scoped_models import ScopedCapture, ScopedDiscoveryRequest, ScopedSelection, _receipt_content
from .validation import canonical_json

REVIEWED_PAIR_PROFILE = "tcgdex_swsh3_136_r0_r1_v1"
SYNTHETIC_PROFILE = "synthetic_multi_revision_v1"
PROFILES = frozenset({REVIEWED_PAIR_PROFILE, SYNTHETIC_PROFILE})
_PROFILE_AUTHORITY = object()


@dataclass(frozen=True)
class MultiRevisionRequest:
    version: int
    profile: str
    context: DiscoveryContext
    current: ScopedSelection
    history: tuple[ScopedSelection, ...]

    def scoped_request(self) -> ScopedDiscoveryRequest:
        return ScopedDiscoveryRequest(2, self.context, self.current, self.history)

    def to_dict(self) -> dict[str, object]:
        return {**self.scoped_request().to_dict(), "version": self.version, "profile": self.profile}


@dataclass(frozen=True)
class ProfiledCapture:
    capture: ScopedCapture
    profile: str
    extraction_json: str = "null"
    _authority: object = field(default=None, init=False, repr=False, compare=False)


def _content(value: ProfiledCapture) -> str:
    return hashlib.sha256(
        canonical_json(
            [_receipt_content(value.capture), value.profile, value.extraction_json]
        ).encode("ascii")
    ).hexdigest()


def _validated_profile_capture(
    capture: ScopedCapture, profile: str, extraction_proof: object = None
) -> ProfiledCapture:
    """Issued only after storage verifies the complete package's profile membership."""
    value = ProfiledCapture(capture, profile, canonical_json(extraction_proof))
    object.__setattr__(value, "_authority", (_PROFILE_AUTHORITY, _content(value)))
    return value


def _has_profile_authority(value: ProfiledCapture) -> bool:
    receipt = value._authority
    return (
        type(receipt) is tuple
        and len(receipt) == 2
        and receipt[0] is _PROFILE_AUTHORITY
        and receipt[1] == _content(value)
    )
