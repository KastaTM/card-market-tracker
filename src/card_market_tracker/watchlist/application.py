"""Manifest-revalidated application operations over independent watchlist storage."""

from __future__ import annotations

from pathlib import Path

from . import evaluation, storage
from .errors import WatchlistError
from .validation import (
    digest,
    identity_projection,
    parse_config,
    parse_entry,
    token,
    validate_cmt_id,
    validate_revision,
    validate_watch_id,
)


def add(
    path: Path,
    manifest: object,
    cmt_id: object,
    config: object,
    *,
    request_token: object,
    timeout: float = 2.0,
) -> dict[str, object]:
    budget = storage.Budget(timeout)
    identity_projection(manifest, cmt_id)
    effective = parse_config(config)
    request = token(request_token)
    return storage.write(
        path,
        action="add",
        manifest=manifest,
        cmt_id=validate_cmt_id(cmt_id),
        config=effective,
        expected_revision=0,
        request_token=request,
        timeout=budget.remaining(),
    )


def _entry(path: Path, key: object, revision: object, budget: storage.Budget) -> dict[str, object]:
    watch = validate_watch_id(key)
    selected = None if revision is None else validate_revision(revision)
    response = storage.get(path, watch, revision=selected, timeout=budget.remaining())
    return parse_entry(response["entry"])


def _identity(manifest: object, entry: dict[str, object]) -> None:
    expected = identity_projection(manifest, entry["cmt_id"])
    if expected != entry["canonical_identity"] or digest(expected) != entry["identity_digest"]:
        raise WatchlistError("identity_conflict")


def update(
    path: Path,
    manifest: object,
    watch_id: object,
    config: object,
    *,
    expected_revision: object,
    request_token: object,
    action: str = "update",
    timeout: float = 2.0,
) -> dict[str, object]:
    budget = storage.Budget(timeout)
    if action not in ("update", "enable", "disable"):
        raise WatchlistError("invalid_field")
    request = token(request_token)
    validate_revision(expected_revision)
    previous = _entry(path, watch_id, None, budget)
    _identity(manifest, previous)
    if action == "update":
        effective: dict[str, object] | None = parse_config(config)
    elif config is not None:
        raise WatchlistError("invalid_shape")
    else:
        effective = None
    return storage.write(
        path,
        action=action,
        manifest=manifest,
        cmt_id=validate_cmt_id(previous["cmt_id"]),
        config=effective,
        expected_revision=validate_revision(expected_revision),
        request_token=request,
        timeout=budget.remaining(),
    )


def evaluate(
    path: Path,
    manifest: object,
    watch_id: object,
    current: object,
    previous: object = None,
    *,
    revision: object,
    as_of: object,
    timeout: float = 2.0,
) -> dict[str, object]:
    budget = storage.Budget(timeout)
    entry = _entry(path, watch_id, revision, budget)
    _identity(manifest, entry)
    result = evaluation.evaluate(entry, current, previous, as_of=as_of)
    budget.remaining()
    return result
