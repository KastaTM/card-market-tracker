"""Application authority: only verified original captures can enter the journal."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from ..persistence.sqlite_repository import read_multi_revision_snapshots
from .journal_errors import JournalError
from .journal_storage import Budget, _record_verified, get, reject_same_file
from .journal_validation import canonical_bounded, decode_json, validate_pair
from .multi_comparison import compare
from .multi_input import parse_request, read_request

_AUTHORITY = object()


@dataclass(frozen=True)
class _Receipt:
    request_json: str
    result_json: str
    _authority: object = field(default=None, init=False, repr=False, compare=False)


def _seal(request_json: str, result_json: str) -> str:
    digest = hashlib.sha256()
    for value in (request_json, result_json):
        digest.update(str(len(value)).encode("ascii"))
        digest.update(b":")
        digest.update(value.encode("ascii"))
    return digest.hexdigest()


def _consume_receipt(
    receipt: object, budget: Budget | None = None
) -> tuple[dict[str, object], dict[str, object]]:
    """Constructor flags and copied receipts confer no application authority."""
    if type(receipt) is not _Receipt:
        raise JournalError("unsupported_evidence")
    if (
        type(receipt.request_json) is not str
        or type(receipt.result_json) is not str
        or len(receipt.request_json) > 1024 * 1024
        or len(receipt.result_json) > 16 * 1024 * 1024
    ):
        raise JournalError("input_limit")
    authority = receipt._authority
    if (
        type(authority) is not tuple
        or len(authority) != 2
        or authority[0] is not _AUTHORITY
        or authority[1] != _seal(receipt.request_json, receipt.result_json)
    ):
        raise JournalError("unsupported_evidence")
    check = budget.remaining if budget is not None else None
    return validate_pair(
        decode_json(receipt.request_json, maximum=1024 * 1024, check=check),
        decode_json(receipt.result_json, check=check),
        check=check,
    )


def record(
    captures_db: Path, journal_db: Path, request_path: Path, *, timeout: float = 2.0
) -> dict[str, object]:
    """Share one deadline across strict input, complete v3 verification and commit."""
    budget = Budget(timeout)
    reject_same_file(captures_db, journal_db)
    request = read_request(request_path)
    budget.remaining()
    captures = read_multi_revision_snapshots(captures_db, request, timeout=budget.remaining())
    budget.remaining()
    result = compare(request, captures)
    budget.remaining()
    # The comparator payload shares repeated evidence. Bound it BEFORE to_dict
    # could copy an oversized tree; the existing comparator API stays untouched.
    request_json = canonical_bounded(request.to_dict(), 1024 * 1024, check=budget.remaining)
    result_json = canonical_bounded(result.payload, check=budget.remaining)
    budget.remaining()
    receipt = _Receipt(request_json, result_json)
    object.__setattr__(receipt, "_authority", (_AUTHORITY, _seal(request_json, result_json)))
    return _record_verified(journal_db, receipt, budget)


def recompute(
    captures_db: Path, journal_db: Path, comparison_id: str, *, timeout: float = 2.0
) -> dict[str, object]:
    """Reconstruct one retained window against original immutable captures, read-only."""
    budget = Budget(timeout)
    reject_same_file(captures_db, journal_db)
    retained = get(journal_db, comparison_id, timeout=budget.remaining())
    budget.remaining()
    request = parse_request(retained["request"])
    captures = read_multi_revision_snapshots(captures_db, request, timeout=budget.remaining())
    budget.remaining()
    outcome = compare(request, captures)
    actual = canonical_bounded(outcome.payload, check=budget.remaining)
    expected = canonical_bounded(retained["comparison"], check=budget.remaining)
    budget.remaining()
    if outcome.payload.get("comparison_id") != comparison_id or actual != expected:
        raise JournalError("recompute_mismatch")
    return {
        "version": 1,
        "operation": "recompute",
        "result": "ok",
        "level": "origin-recompute",
        "comparison_id": comparison_id,
    }
