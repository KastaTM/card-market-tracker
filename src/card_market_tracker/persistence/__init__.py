"""Synthetic observation persistence boundary; constructors alone are unvalidated."""

from .application import (
    build_batch,
    canonical_payload,
    context_fingerprint,
    fingerprint,
    validate_batch,
)
from .errors import PersistenceError
from .input import parse_persistence, read_persistence
from .models import PersistedRecord, PersistenceBatch, WriteResult

__all__ = [
    "PersistedRecord",
    "PersistenceBatch",
    "PersistenceError",
    "WriteResult",
    "build_batch",
    "canonical_payload",
    "context_fingerprint",
    "fingerprint",
    "parse_persistence",
    "read_persistence",
    "validate_batch",
]
