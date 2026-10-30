"""Original-backed admission, single-use authority and one fenced manual send."""

from __future__ import annotations

import json
import os
import stat
from collections.abc import Callable
from contextvars import ContextVar
from dataclasses import dataclass, field
from functools import wraps
from itertools import combinations
from pathlib import Path
from typing import Protocol, cast

from ..catalog import validation as catalog_validation
from ..catalog.manifest import parse_manifest
from ..catalog.validation import CatalogError
from ..persistence import sqlite_repository as file_paths
from ..persistence.errors import PersistenceError
from ..watchlist import validation as watch_validation
from ..watchlist.errors import WatchlistError
from ..watchlist_alerts import application as source_application
from ..watchlist_alerts import storage as source_storage
from ..watchlist_alerts.errors import OutboxError
from ..watchlist_journal import application as journal_application
from ..watchlist_journal import storage as journal_storage
from ..watchlist_journal.errors import JournalError
from . import models, policy, storage
from .budget import Budget
from .errors import ERROR_CATEGORIES, DeliveryError

_AUTHORITY = object()
_invocation_budget: ContextVar[Budget | None] = ContextVar(
    "watchlist_delivery_budget", default=None
)
_SOURCE_ERRORS = (WatchlistError, JournalError, OutboxError, CatalogError, PersistenceError)


class Transport(Protocol):
    def check_configuration(self) -> None: ...
    def validate_destination(self, bot_id: int, chat_id: int, *, timeout: float) -> None: ...
    def validate_bot(self, bot_id: int, *, timeout: float) -> None: ...
    def send(self, bot_id: int, chat_id: int, message_text: str, *, timeout: float) -> object: ...


def _transport_factory() -> Transport:
    from .transport_adapter import new_transport

    return new_transport()


def _boundary[**P](function: Callable[P, dict[str, object]]) -> Callable[P, dict[str, object]]:
    @wraps(function)
    def guarded(*args: P.args, **kwargs: P.kwargs) -> dict[str, object]:
        try:
            return function(*args, **kwargs)
        except DeliveryError:
            raise
        except _SOURCE_ERRORS as error:
            raise DeliveryError(error.category) from None
        except Exception as error:
            category = getattr(error, "category", None)
            raise DeliveryError(
                category if type(category) is str and category in ERROR_CATEGORIES else "storage_io"
            ) from None

    return guarded


def _budget(timeout: float, maximum: float = 5.0) -> Budget:
    existing = _invocation_budget.get()
    if existing is not None:
        existing.remaining()
        return existing
    return Budget(timeout, maximum)


def _response(
    operation: str, budget: Budget, *, result: str = "ok", **fields: object
) -> dict[str, object]:
    response: dict[str, object] = {"version": 1, "operation": operation, "result": result, **fields}
    raw = json.dumps(
        response, ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    if len(raw) + 1 > models.MAX_INPUT_BYTES:
        raise DeliveryError("input_limit")
    budget.remaining()
    return response


def _descriptor(path: Path) -> tuple[object, ...]:
    target = journal_storage._path(path)
    before = target.lstat()
    with target.open("rb") as stream:
        header = stream.read(100)
    after = target.lstat()
    if (before.st_dev, before.st_ino, before.st_nlink) != (after.st_dev, after.st_ino, 1):
        raise DeliveryError("unsafe_destination")
    return str(target).casefold(), after.st_dev, after.st_ino, header[:100]


@dataclass(frozen=True)
class _Receipt:
    content_json: str
    _authority: object = field(default=None, init=False, repr=False, compare=False)
    _used: bool = field(default=False, init=False, repr=False, compare=False)


def _issue(
    content: dict[str, object],
    budget: Budget,
    ledger_db: Path,
    sources: tuple[Path, Path, Path],
    manifest: object,
) -> _Receipt:
    budget.remaining()
    rebuilt = policy.validate_prepared(content, check=budget.remaining)
    raw = policy._json(rebuilt)
    if len(raw) > models.MAX_RECEIPT_BYTES:
        raise DeliveryError("input_limit")
    descriptor = _descriptor(ledger_db)
    originals = tuple((path, _descriptor(path)) for path in sources)
    manifest_sha256 = policy.digest(policy.canonical(manifest, check=budget.remaining))
    receipt = _Receipt(raw)
    seal = (
        _AUTHORITY,
        id(receipt),
        policy.digest(raw),
        budget,
        budget.global_deadline,
        budget.origin_seal,
        rebuilt["operation"],
        ledger_db,
        descriptor,
        originals,
        manifest_sha256,
    )
    object.__setattr__(receipt, "_authority", seal)
    return receipt


def _consume_receipt(
    receipt: object, budget: Budget, operation: str, ledger_db: Path
) -> dict[str, object]:
    """Reject counterfeit/copy/mutation/renewal/reuse before any writable open."""
    if type(receipt) is not _Receipt:
        raise DeliveryError("unsupported_evidence")
    raw, seal = receipt.content_json, receipt._authority
    if (
        type(raw) is not str
        or not raw.isascii()
        or len(raw) > models.MAX_RECEIPT_BYTES
        or type(seal) is not tuple
        or len(seal) != 11
        or seal[0] is not _AUTHORITY
        or seal[1] != id(receipt)
        or seal[2] != policy.digest(raw)
        or seal[3] is not budget
        or seal[4] != budget.global_deadline
        or seal[5] != budget.origin_seal
        or seal[6] != operation
        or receipt._used is not False
    ):
        raise DeliveryError("unsupported_evidence")
    budget.remaining()
    if operation == "claim" and budget.origin_seal[2] is not True:
        raise DeliveryError("unsupported_evidence")
    # A structurally genuine matching authority is consumed once even when
    # subsequent source/path validation refuses this writer attempt.
    object.__setattr__(receipt, "_used", True)
    try:
        if _descriptor(ledger_db) != seal[8]:
            raise DeliveryError("unsupported_evidence")
        for path, expected in seal[9]:
            budget.remaining()
            if _descriptor(path) != expected:
                raise DeliveryError("unsupported_evidence")
    except (OSError, JournalError, PersistenceError):
        raise DeliveryError("unsupported_evidence") from None
    try:
        value: object = json.loads(raw)
        rebuilt = policy.validate_prepared(value, check=budget.remaining)
        if policy._json(rebuilt) != raw or rebuilt["operation"] != operation:
            raise DeliveryError("unsupported_evidence")
        return rebuilt
    except DeliveryError as error:
        if error.category == "storage_timeout":
            raise
        raise DeliveryError("unsupported_evidence") from None
    except (ValueError, TypeError, RecursionError):
        raise DeliveryError("unsupported_evidence") from None


def _paths(ledger: Path, watchlist: Path, journal: Path, outbox: Path, budget: Budget) -> None:
    for first, second in combinations((ledger, watchlist, journal, outbox), 2):
        budget.remaining()
        journal_application._distinct(first, second)
    journal_storage._path(ledger)


@dataclass(frozen=True)
class _ManifestFile:
    path: Path
    budget: Budget


def _manifest_file(path: Path, budget: Budget) -> object:
    """CLI-only deferred input; materialized inside the origins allowance."""
    return _ManifestFile(path, budget)


def _manifest_read(value: _ManifestFile, budget: Budget) -> object:
    """Bound a CLI JSON snapshot to checked ancestors and one regular inode."""
    budget.remaining()
    try:
        target = file_paths._checked_path(value.path)
        before = file_paths._unsafe_stat(target, file=True)
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
        descriptor = os.open(target, flags)
        with os.fdopen(descriptor, "rb") as stream:
            opened = os.fstat(stream.fileno())
            if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
                raise DeliveryError("unsafe_destination")
            if opened.st_size > models.MAX_INPUT_BYTES:
                raise DeliveryError("input_limit")
            budget.remaining()
            raw = stream.read(models.MAX_INPUT_BYTES + 1)
            readback = os.fstat(stream.fileno())
        file_paths._checked_path(target)
        after = file_paths._unsafe_stat(target, file=True)
    except OSError:
        raise DeliveryError("input_io") from None
    identities = {
        (item.st_dev, item.st_ino, item.st_nlink, item.st_size, item.st_mtime_ns)
        for item in (before, opened, readback, after)
    }
    if len(identities) != 1:
        raise DeliveryError("unsafe_destination")
    if len(raw) > models.MAX_INPUT_BYTES:
        raise DeliveryError("input_limit")
    budget.remaining()
    try:
        text = raw.decode("utf-8", "strict")
        catalog_validation._preflight(text)
        result: object = json.loads(
            text,
            object_pairs_hook=catalog_validation._pairs,
            parse_constant=catalog_validation._constant,
        )
    except CatalogError:
        raise
    except (UnicodeError, ValueError, RecursionError):
        raise DeliveryError("invalid_json") from None
    # Preserve the complete accepted parser's scalar/depth/node/canonical caps.
    watch_validation.canonical(result)
    budget.remaining()
    return result


def _admit(
    ledger_db: Path,
    watchlist_db: Path,
    journal_db: Path,
    outbox_db: Path,
    manifest: object,
    alert_id: object,
    alias: object,
    budget: Budget,
    *,
    operation: str = "prepare",
) -> tuple[dict[str, object], object]:
    selected = policy.validate_id(alert_id, "walt1_")
    selected_alias = policy.destination(alias)
    if type(manifest) is _ManifestFile:
        if manifest.budget is not budget:
            raise DeliveryError("unsupported_evidence")
        for original in (ledger_db, watchlist_db, journal_db, outbox_db):
            journal_application._distinct(manifest.path, original)
        budget.remaining()
        manifest = _manifest_read(manifest, budget)
        budget.remaining()
    # Detach the complete manifest before source callbacks can mutate caller input.
    frozen: object = json.loads(policy.canonical(manifest, check=budget.remaining))
    parse_manifest(frozen)
    budget.remaining()
    _paths(ledger_db, watchlist_db, journal_db, outbox_db, budget)
    sources = (watchlist_db, journal_db, outbox_db)
    descriptors = tuple(_descriptor(path) for path in sources)
    saved_route = storage.load_destination(ledger_db, selected_alias, _budget=budget)
    frozen_route = policy.route(
        {
            "route_version": 1,
            "operator_attested": True,
            **{
                key: saved_route[key]
                for key in models.ROUTE_FIELDS - {"route_version", "operator_attested"}
            },
        }
    )
    source_storage.verify(outbox_db, _budget=budget)
    before = source_storage._get_pair(outbox_db, selected, budget)
    source_application.recompute(
        outbox_db, watchlist_db, journal_db, frozen, selected, _budget=budget
    )
    after = source_storage._get_pair(outbox_db, selected, budget)
    if policy._json(before) != policy._json(after):
        raise DeliveryError("recompute_mismatch")
    if descriptors != tuple(_descriptor(path) for path in sources):
        raise DeliveryError("recompute_mismatch")
    alert, evidence = before
    if alert["destination_key"] != selected_alias:
        raise DeliveryError("invalid_destination")
    prepared = policy.prepare(
        alert, evidence, frozen_route, operation=operation, check=budget.remaining
    )
    return prepared, frozen


@_boundary
def initialize(ledger_db: Path, *, timeout: float = 2.0) -> dict[str, object]:
    return storage.initialize(ledger_db, _budget=_budget(timeout))


@_boundary
def destination_add(
    ledger_db: Path,
    alias: object,
    bot_id: object,
    chat_id: object,
    *,
    operator_private_owned: object = False,
    timeout: float = 2.0,
) -> dict[str, object]:
    return storage.destination_add(
        ledger_db,
        cast(str, alias),
        cast(int, bot_id),
        cast(int, chat_id),
        operator_private_owned=cast(bool, operator_private_owned),
        _budget=_budget(timeout),
    )


@_boundary
def destination_validate(
    ledger_db: Path, alias: object, *, timeout: float = 15.0
) -> dict[str, object]:
    budget = _budget(timeout, 30.0)
    with budget.reserved():
        saved = storage.load_destination(ledger_db, cast(str, alias), _budget=budget)
        client = _transport_factory()
        client.check_configuration()
        client.validate_destination(
            cast(int, saved["bot_id"]), cast(int, saved["chat_id"]), timeout=budget.preclaim()
        )
    return storage._destination_validated(
        ledger_db,
        cast(str, alias),
        _budget=budget,
        expected_route_sha256=cast(str, saved["route_sha256"]),
    )


@_boundary
def review(
    ledger_db: Path,
    watchlist_db: Path,
    journal_db: Path,
    outbox_db: Path,
    manifest: object,
    alert_id: object,
    alias: object,
    *,
    timeout: float = 2.0,
) -> dict[str, object]:
    budget = _budget(timeout)
    content, _ = _admit(
        ledger_db, watchlist_db, journal_db, outbox_db, manifest, alert_id, alias, budget
    )
    binding = cast(dict[str, object], content["binding"])
    return _response(
        "review",
        budget,
        review={
            **binding,
            "binding_sha256": content["binding_sha256"],
            "acknowledgement": models.ACKNOWLEDGEMENT,
            "historical_demonstration": True,
        },
    )


@_boundary
def prepare(
    ledger_db: Path,
    watchlist_db: Path,
    journal_db: Path,
    outbox_db: Path,
    manifest: object,
    alert_id: object,
    alias: object,
    *,
    acknowledgement: object,
    expected_signal_id: object,
    expected_revision: object,
    expected_message_sha256: object,
    expected_evidence_sha256: object,
    expected_route_sha256: object,
    expected_binding_sha256: object,
    timeout: float = 2.0,
) -> dict[str, object]:
    budget = _budget(timeout)
    content, frozen = _admit(
        ledger_db, watchlist_db, journal_db, outbox_db, manifest, alert_id, alias, budget
    )
    binding = cast(dict[str, object], content["binding"])
    expected = {
        "signal_id": expected_signal_id,
        "revision": expected_revision,
        "message_sha256": expected_message_sha256,
        "evidence_sha256": expected_evidence_sha256,
        "route_sha256": expected_route_sha256,
    }
    if (
        type(acknowledgement) is not str
        or acknowledgement != models.ACKNOWLEDGEMENT
        or type(expected_binding_sha256) is not str
        or expected_binding_sha256 != content["binding_sha256"]
        or any(
            type(value) is not type(binding[key]) or value != binding[key]
            for key, value in expected.items()
        )
    ):
        raise DeliveryError("consent_mismatch")
    receipt = _issue(content, budget, ledger_db, (watchlist_db, journal_db, outbox_db), frozen)
    return storage._prepare_verified(ledger_db, receipt, budget)


@_boundary
def recompute(
    ledger_db: Path,
    watchlist_db: Path,
    journal_db: Path,
    outbox_db: Path,
    manifest: object,
    delivery_id: object,
    *,
    timeout: float = 2.0,
) -> dict[str, object]:
    budget = _budget(timeout)
    saved = storage.load_delivery(ledger_db, cast(str, delivery_id), _budget=budget)
    content, _ = _admit(
        ledger_db,
        watchlist_db,
        journal_db,
        outbox_db,
        manifest,
        saved["alert_id"],
        saved["destination_key"],
        budget,
    )
    _compare(saved, content)
    return _response(
        "recompute",
        budget,
        level="origin-recompute",
        delivery_id=delivery_id,
        binding_sha256=content["binding_sha256"],
    )


def _compare(saved: dict[str, object], content: dict[str, object]) -> None:
    for key in models.PREPARED_FIELDS - {"operation", "authority_version"}:
        if (
            key not in saved
            or type(saved[key]) is not type(content[key])
            or policy._json(saved[key]) != policy._json(content[key])
        ):
            raise DeliveryError("recompute_mismatch")


def _preflight(saved: dict[str, object], budget: Budget) -> None:
    if saved["send_quarantined"]:
        raise DeliveryError("send_quarantined")
    if saved["state"] not in ("ready", "retryable"):
        raise DeliveryError("delivery_blocked")
    if not saved["validated_at"]:
        raise DeliveryError("not_validated")
    now = policy.now()
    if any(
        type(saved.get(key)) is str and now < cast(str, saved[key])
        for key in ("operational_high_water", "registered_at", "validated_at", "updated_at")
    ):
        raise DeliveryError("clock_skew")
    if saved["not_before"] is not None and now < cast(str, saved["not_before"]):
        raise DeliveryError("retry_not_due")
    if cast(int, saved["attempt_count"]) >= 3:
        raise DeliveryError("attempt_limit")
    budget.preclaim()


def _postclaim(client: Transport, saved: dict[str, object], budget: Budget) -> dict[str, object]:
    try:
        from .transport_adapter import normalize_result

        result = client.send(
            cast(int, saved["bot_id"]),
            cast(int, saved["chat_id"]),
            cast(str, saved["message_text"]),
            timeout=budget.preclaim(),
        )
        return normalize_result(result, cast(int, saved["bot_id"]), cast(int, saved["chat_id"]))
    except Exception as error:
        category = getattr(error, "category", None)
        accepted = {
            "token_configuration",
            "bot_mismatch",
            "destination_mismatch",
            "transport_timeout",
            "transport_failure",
            "provider_invalid",
            "deadline_exceeded",
        }
        return {
            "state": "uncertain",
            "error_category": category
            if type(category) is str and category in accepted
            else "network_uncertain",
            "retry_after": None,
            "receipt": None,
        }


@_boundary
def send(
    ledger_db: Path,
    delivery_id: object,
    *,
    watchlist_db: Path | None = None,
    journal_db: Path | None = None,
    outbox_db: Path | None = None,
    manifest: object = None,
    timeout: float = 15.0,
) -> dict[str, object]:
    budget = _budget(timeout, 30.0)
    with budget.reserved():
        saved = storage.load_delivery(
            ledger_db, cast(str, delivery_id), _budget=budget, _for_send=True
        )
        if saved["state"] == "confirmed":
            return _response(
                "send", budget, result="replay", delivery=storage._safe_delivery(saved)
            )
        _preflight(saved, budget)
        if any(path is None for path in (watchlist_db, journal_db, outbox_db)) or manifest is None:
            raise DeliveryError("invalid_field")
        origins = (cast(Path, watchlist_db), cast(Path, journal_db), cast(Path, outbox_db))
        with budget.origins():
            content, frozen = _admit(
                ledger_db,
                *origins,
                manifest,
                saved["alert_id"],
                saved["destination_key"],
                budget,
                operation="claim",
            )
            _compare(saved, content)
        client = _transport_factory()
        client.check_configuration()
        client.validate_bot(cast(int, saved["bot_id"]), timeout=budget.preclaim())
        receipt = _issue(content, budget, ledger_db, origins, frozen)
        claimed = storage._claim_verified(ledger_db, cast(str, delivery_id), receipt, budget)
    if claimed.get("result") == "replay":
        return _response(
            "send",
            budget,
            result="replay",
            delivery=storage._safe_delivery(cast(dict[str, object], claimed["delivery"])),
        )
    claimed_item = cast(dict[str, object], claimed["delivery"])
    outcome = _postclaim(client, claimed_item, budget)
    if outcome["state"] == "retryable":
        outcome["error_category"] = "rate_limited"
    handle = claimed["_handle"]
    try:
        finished = storage._finish(ledger_db, cast(str, delivery_id), handle, outcome, budget)
    except Exception:
        # A failed commit may have committed, so never fabricate a delivery state.
        try:
            storage._finish(
                ledger_db,
                cast(str, delivery_id),
                handle,
                {
                    "state": "uncertain",
                    "error_category": "local_commit_failed",
                    "retry_after": None,
                    "receipt": None,
                },
                budget,
            )
        except Exception:
            pass
        raise DeliveryError("local_commit_failed") from None
    if finished["state"] == "confirmed":
        return _response("send", budget, delivery=finished)
    category = cast(str, finished["last_error_category"])
    return _response("send", budget, result="error", error_category=category, delivery=finished)


@_boundary
def get(ledger_db: Path, delivery_id: object, *, timeout: float = 2.0) -> dict[str, object]:
    return storage.get(ledger_db, cast(str, delivery_id), _budget=_budget(timeout))


@_boundary
def list_deliveries(
    ledger_db: Path,
    *,
    state: object = None,
    limit: object = 100,
    cursor: object = None,
    timeout: float = 2.0,
) -> dict[str, object]:
    return storage.list_deliveries(
        ledger_db,
        state=cast(str | None, state),
        limit=cast(int, limit),
        cursor=cast(str | None, cursor),
        _budget=_budget(timeout),
    )


@_boundary
def verify(ledger_db: Path, *, timeout: float = 2.0) -> dict[str, object]:
    return storage.verify(ledger_db, _budget=_budget(timeout))


@_boundary
def recover(
    ledger_db: Path, delivery_id: object, *, worker_quiesced: object = False, timeout: float = 2.0
) -> dict[str, object]:
    return storage.recover(
        ledger_db,
        cast(str, delivery_id),
        worker_quiesced=cast(bool, worker_quiesced),
        _budget=_budget(timeout),
    )


@_boundary
def backup(ledger_db: Path, destination: Path, *, timeout: float = 2.0) -> dict[str, object]:
    return storage.backup(ledger_db, destination, _budget=_budget(timeout))


@_boundary
def restore(ledger_db: Path, destination: Path, *, timeout: float = 2.0) -> dict[str, object]:
    return storage.restore(ledger_db, destination, _budget=_budget(timeout))
