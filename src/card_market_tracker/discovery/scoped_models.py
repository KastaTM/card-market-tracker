"""Provider-independent v2 values; constructing a DTO grants no storage authority."""

import hashlib
from dataclasses import dataclass, field

from .models import BatchSnapshot, DiscoveryContext
from .validation import canonical_json, snapshot_dict

_STORAGE_AUTHORITY = object()


@dataclass(frozen=True)
class ScopedSelection:
    batch_id: str
    selector: str

    def to_dict(self) -> dict[str, object]:
        return {"batch_id": self.batch_id, "selector": self.selector}


@dataclass(frozen=True)
class ScopedDiscoveryRequest:
    version: int
    context: DiscoveryContext
    current: ScopedSelection
    history: tuple[ScopedSelection, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "context": self.context.to_dict(),
            "current": self.current.to_dict(),
            "history": [selection.to_dict() for selection in self.history],
        }


@dataclass(frozen=True)
class ScopedCapture:
    snapshot: BatchSnapshot
    mode: str
    evidence_state: str
    scope_json: str
    capture_fingerprint: str
    _storage_authority: object = field(default=None, init=False, repr=False, compare=False)


def _receipt_content(capture: ScopedCapture) -> str:
    return hashlib.sha256(
        canonical_json(
            {
                "snapshot": snapshot_dict(capture.snapshot),
                "first_persisted_at": capture.snapshot.first_persisted_at,
                "mode": capture.mode,
                "evidence_state": capture.evidence_state,
                "scope_json": capture.scope_json,
                "capture_fingerprint": capture.capture_fingerprint,
            }
        ).encode("ascii")
    ).hexdigest()


def _validated_storage_capture(
    snapshot: BatchSnapshot,
    mode: str,
    evidence_state: str,
    scope_json: str,
    capture_fingerprint: str,
) -> ScopedCapture:
    """Storage-only issuance after complete envelope reconstruction.

    This private capability is an application trust boundary, not cryptographic
    authentication against arbitrary Python code executing inside the process.
    """
    capture = ScopedCapture(snapshot, mode, evidence_state, scope_json, capture_fingerprint)
    object.__setattr__(
        capture, "_storage_authority", (_STORAGE_AUTHORITY, _receipt_content(capture))
    )
    return capture


def _has_storage_authority(capture: ScopedCapture) -> bool:
    receipt = capture._storage_authority
    return (
        type(receipt) is tuple
        and len(receipt) == 2
        and receipt[0] is _STORAGE_AUTHORITY
        and receipt[1] == _receipt_content(capture)
    )


@dataclass(frozen=True)
class ScopedDiscoveryResult:
    payload: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        # Fresh nested containers keep callers from modifying a result's identity.
        import json
        from typing import cast

        return cast(dict[str, object], json.loads(canonical_json(self.payload)))
