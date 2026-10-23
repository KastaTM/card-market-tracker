"""Original-manifest and exact P5a-revision admission for journal operations."""

from __future__ import annotations

import os
from pathlib import Path
from typing import cast

from ..watchlist import storage as watchlist_storage
from ..watchlist.errors import WatchlistError
from ..watchlist.validation import (
    digest,
    identity_projection,
    parse_entry,
    validate_revision,
    validate_watch_id,
)
from . import storage
from .errors import JournalError
from .identity import canonical, normalized_snapshot, validate_snapshot


def _distinct(journal: Path, origin: Path) -> None:
    try:
        if journal.resolve() == origin.resolve() or (
            journal.exists() and origin.exists() and os.path.samefile(journal, origin)
        ):
            raise JournalError("unsafe_destination")
    except ValueError:
        raise JournalError("unsafe_destination") from None
    except (OSError, RuntimeError):
        raise JournalError("storage_io") from None


def _origin_entry(
    path: Path, manifest: object, watch_id: object, revision: object, budget: storage.Budget
) -> dict[str, object]:
    try:
        key = validate_watch_id(watch_id)
        selected = validate_revision(revision)
        response = watchlist_storage.get(path, key, revision=selected, timeout=budget.remaining())
        entry = parse_entry(response["entry"])
        expected = identity_projection(manifest, entry["cmt_id"])
        if (
            canonical(expected) != canonical(entry["canonical_identity"])
            or digest(expected) != entry["identity_digest"]
        ):
            raise JournalError("identity_conflict")
        if entry["watch_id"] != key or entry["revision"] != selected:
            raise JournalError("identity_conflict")
        budget.remaining()
        return entry
    except WatchlistError as error:
        raise JournalError(error.category) from None


def record(
    journal_path: Path,
    watchlist_path: Path,
    manifest: object,
    watch_id: object,
    current: object,
    previous: object = None,
    *,
    revision: object,
    as_of: object,
    timeout: float = 2.0,
) -> dict[str, object]:
    """Admit original evidence on every call, including ancient exact replay."""
    budget = storage.Budget(timeout)
    _distinct(journal_path, watchlist_path)
    entry = _origin_entry(watchlist_path, manifest, watch_id, revision, budget)
    snapshot = normalized_snapshot(entry, current, previous, as_of=as_of)
    budget.remaining()
    return storage._record_validated(journal_path, snapshot, _budget=budget)


def recompute(
    journal_path: Path,
    watchlist_path: Path,
    manifest: object,
    evaluation_id: object,
    *,
    timeout: float = 2.0,
) -> dict[str, object]:
    """Read-only original-source re-admission, separate from local verification."""
    budget = storage.Budget(timeout)
    _distinct(journal_path, watchlist_path)
    response = storage.get(journal_path, evaluation_id, _budget=budget)
    evaluation = cast(dict[str, object], response["evaluation"])
    snapshot, local_result = validate_snapshot(evaluation["snapshot"])
    saved_entry = cast(dict[str, object], snapshot["entry"])
    entry = _origin_entry(
        watchlist_path, manifest, saved_entry["watch_id"], saved_entry["revision"], budget
    )
    if canonical(entry) != canonical(saved_entry):
        raise JournalError("identity_conflict")
    rebuilt = normalized_snapshot(
        entry, snapshot["current"], snapshot["previous"], as_of=snapshot["as_of"]
    )
    _, result = validate_snapshot(rebuilt)
    if (
        canonical(rebuilt) != canonical(snapshot)
        or canonical(result) != canonical(local_result)
        or canonical(result) != canonical(evaluation["evaluation_result"])
    ):
        raise JournalError("storage_corrupt")
    budget.remaining()
    return {
        "version": 1,
        "operation": "recompute",
        "result": "ok",
        "evaluation_id": evaluation_id,
        "evaluation_result": result,
    }
