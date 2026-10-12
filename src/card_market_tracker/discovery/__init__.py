"""Offline temporal discovery over frozen synthetic observations."""

from .comparison import compare
from .errors import DiscoveryError
from .input import parse_request, read_request, validate_request
from .models import (
    BatchSnapshot,
    DiscoveryContext,
    DiscoveryRequest,
    DiscoveryResult,
    SnapshotRecord,
)
from .validation import validate_snapshot

__all__ = [
    "BatchSnapshot",
    "DiscoveryContext",
    "DiscoveryError",
    "DiscoveryRequest",
    "DiscoveryResult",
    "SnapshotRecord",
    "compare",
    "parse_request",
    "read_request",
    "validate_request",
    "validate_snapshot",
]
