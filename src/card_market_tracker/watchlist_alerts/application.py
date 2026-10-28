"""Original-only admission and one-operation private receipt for Watchlist previews."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

from ..catalog.manifest import parse_manifest
from ..catalog.validation import CatalogError
from ..persistence.errors import PersistenceError
from ..watchlist import storage as watchlist_storage
from ..watchlist import validation as watchlist_validation
from ..watchlist.errors import WatchlistError
from ..watchlist_journal import application as journal_application
from ..watchlist_journal import identity
from ..watchlist_journal import storage as journal_storage
from ..watchlist_journal.errors import JournalError
from . import policy, storage
from .errors import OutboxError
from .models import MAX_RECEIPT_BYTES

Budget = journal_storage.Budget
_AUTHORITY = object()


@dataclass(frozen=True)
class _Receipt:
    content_json: str
    _authority: object = field(default=None, init=False, repr=False, compare=False)
    _used: bool = field(default=False, init=False, repr=False, compare=False)


def _seal(content: str) -> str:
    return hashlib.sha256(content.encode("ascii")).hexdigest()


def _issue(content: dict[str, object], budget: Budget) -> _Receipt:
    """Private authoring boundary, called only after this operation's source admission."""
    budget.remaining()
    normalized = policy.validate_prepared(content, check=budget.remaining)
    # Container documents and rendered text have their own limits, not scalar1024.
    raw = json.dumps(
        normalized, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    )
    if len(raw) > MAX_RECEIPT_BYTES:
        raise OutboxError("input_limit")
    budget.remaining()
    receipt = _Receipt(raw)
    object.__setattr__(receipt, "_authority", (_AUTHORITY, id(receipt), _seal(raw), budget))
    return receipt


def _consume_receipt(receipt: object, budget: Budget) -> dict[str, object]:
    """Reject counterfeit/copy/mutation/budget renewal/reuse before writer open."""
    if type(receipt) is not _Receipt:
        raise OutboxError("unsupported_evidence")
    content = receipt.content_json
    authority = receipt._authority
    if (
        type(content) is not str
        or not content.isascii()
        or len(content) > MAX_RECEIPT_BYTES
        or type(authority) is not tuple
        or len(authority) != 4
        or authority[0] is not _AUTHORITY
        or authority[1] != id(receipt)
        or authority[2] != _seal(content)
        or authority[3] is not budget
        or receipt._used is not False
    ):
        raise OutboxError("unsupported_evidence")
    # Check the genuine issuing deadline after authority checks; never renew it.
    try:
        budget.remaining()
        object.__setattr__(receipt, "_used", True)
        value: object = json.loads(content)
        rebuilt = policy.validate_prepared(value, check=budget.remaining)
        if (
            json.dumps(
                rebuilt, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
            )
            != content
        ):
            raise OutboxError("unsupported_evidence")
        budget.remaining()
        return rebuilt
    except JournalError as error:
        raise OutboxError(error.category) from None
    except OutboxError as error:
        if error.category == "storage_timeout":
            raise
        raise OutboxError("unsupported_evidence") from None
    except (ValueError, TypeError, RecursionError):
        raise OutboxError("unsupported_evidence") from None


def _paths(outbox: Path, watchlist: Path, journal: Path, budget: Budget) -> None:
    for first, second in ((outbox, watchlist), (outbox, journal), (watchlist, journal)):
        budget.remaining()
        journal_application._distinct(first, second)
    storage._path(outbox)


def _manifest(value: object, budget: Budget) -> object:
    # Detach before executing callbacks; the caller's mutable dictionary is never
    # used again after freezing. Public limits/strict complete manifest parsing win.
    raw = policy.canonical(value)
    frozen: object = json.loads(raw)
    budget.remaining()
    parse_manifest(frozen)
    budget.remaining()
    return frozen


def _origin_entry(
    path: Path, manifest: object, watch_id: object, revision: object, budget: Budget
) -> dict[str, object]:
    """Read the exact P5a revision and check its residual deadline before parsing."""
    key = watchlist_validation.validate_watch_id(watch_id)
    selected = watchlist_validation.validate_revision(revision)
    response = watchlist_storage.get(path, key, revision=selected, timeout=budget.remaining())
    budget.remaining()
    entry = watchlist_validation.parse_entry(response["entry"])
    expected = watchlist_validation.identity_projection(manifest, entry["cmt_id"])
    if (
        policy.canonical(expected) != policy.canonical(entry["canonical_identity"])
        or watchlist_validation.digest(expected) != entry["identity_digest"]
        or entry["watch_id"] != key
        or entry["revision"] != selected
    ):
        raise OutboxError("identity_conflict")
    budget.remaining()
    return entry


def _admit(
    watchlist: Path, journal: Path, manifest: object, signal_id: object, budget: Budget
) -> dict[str, object]:
    bundle = journal_storage._verified_signal_bundle(journal, signal_id, _budget=budget)
    before = cast(dict[str, object], bundle["predecessor"])
    after = cast(dict[str, object], bundle["current"])
    snapshots = [cast(dict[str, object], point["snapshot"]) for point in (before, after)]
    saved = cast(dict[str, object], snapshots[0]["entry"])
    if policy.canonical(saved) != policy.canonical(snapshots[1]["entry"]):
        raise OutboxError("identity_conflict")
    # Revalidate the COMPLETE raw manifest/identity using the unchanged public
    # P5a exact-revision read; its return is deadline-checked before parsing.
    entry = _origin_entry(watchlist, manifest, saved["watch_id"], saved["revision"], budget)
    for point, snapshot in zip((before, after), snapshots, strict=True):
        budget.remaining()
        if policy.canonical(entry) != policy.canonical(snapshot["entry"]):
            raise OutboxError("identity_conflict")
        rebuilt, result = identity._normalized_snapshot(
            entry, snapshot["current"], snapshot["previous"], as_of=snapshot["as_of"]
        )
        if policy.canonical(rebuilt) != policy.canonical(snapshot) or policy.canonical(
            result
        ) != policy.canonical(point["evaluation_result"]):
            raise OutboxError("storage_corrupt")
        point["snapshot"], point["evaluation_result"] = rebuilt, result
        budget.remaining()
    return bundle


def enqueue(
    outbox_db: Path,
    watchlist_db: Path,
    journal_db: Path,
    manifest: object,
    signal_id: object,
    destination_key: object,
    *,
    timeout: float = 2.0,
    _budget: Budget | None = None,
) -> dict[str, object]:
    """Revalidate original sources on every attempt, including ancient exact replay."""
    try:
        budget = Budget(timeout) if _budget is None else _budget
        frozen = _manifest(manifest, budget)
        selected = policy.validate_id(signal_id, "wsig1_")
        alias = policy.destination(destination_key)
        _paths(outbox_db, watchlist_db, journal_db, budget)
        bundle = _admit(watchlist_db, journal_db, frozen, selected, budget)
        content = policy.prepare(bundle, alias, check=budget.remaining)
        receipt = _issue(content, budget)
        return storage._enqueue_verified(outbox_db, receipt, budget)
    except (JournalError, WatchlistError, CatalogError, PersistenceError) as error:
        raise OutboxError(error.category) from None


def recompute(
    outbox_db: Path,
    watchlist_db: Path,
    journal_db: Path,
    manifest: object,
    alert_id: object,
    *,
    timeout: float = 2.0,
    _budget: Budget | None = None,
) -> dict[str, object]:
    """Compare a healthy selected local pair against independently admitted originals."""
    try:
        budget = Budget(timeout) if _budget is None else _budget
        frozen = _manifest(manifest, budget)
        key = policy.validate_id(alert_id)
        _paths(outbox_db, watchlist_db, journal_db, budget)
        alert, evidence = storage._get_pair(outbox_db, key, budget)
        bundle = _admit(watchlist_db, journal_db, frozen, alert["signal_id"], budget)
        prepared = policy.prepare(bundle, alert["destination_key"], check=budget.remaining)
        if prepared["evidence_json"] != policy.canonical(evidence) or prepared[
            "intent_json"
        ] != policy.canonical(alert["intent"]):
            raise OutboxError("recompute_mismatch")
        for name in (
            "alert_id",
            "destination_key",
            "signal_id",
            "policy_version",
            "renderer_version",
            "channel",
            "state",
            "intent_sha256",
            "message_text",
            "message_sha256",
        ):
            if type(prepared[name]) is not type(alert[name]) or prepared[name] != alert[name]:
                raise OutboxError("recompute_mismatch")
        budget.remaining()
        return {
            "version": 1,
            "operation": "recompute",
            "result": "ok",
            "level": "origin-recompute",
            "alert_id": key,
        }
    except (JournalError, WatchlistError, CatalogError, PersistenceError) as error:
        raise OutboxError(error.category) from None
