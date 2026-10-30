"""Future AC-WT20 qualification: offline dossier and durable one-attempt accounting.

Live commands require a separately authored exact-selection authorization record.
This tool grants no permission and never declares the phase or live gate accepted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from uuid import uuid4

from card_market_tracker.persistence import sqlite_repository as paths
from card_market_tracker.watchlist import validation
from card_market_tracker.watchlist_delivery import application as app
from card_market_tracker.watchlist_delivery import storage
from card_market_tracker.watchlist_delivery.budget import Budget
from card_market_tracker.watchlist_delivery.errors import DeliveryError

ACK = "SYNTHETIC_HISTORICAL_DEMONSTRATION"
DECISION = "AUTHORIZE_ONE_HISTORICAL_SYNTHETIC_MESSAGE_FOR_THIS_EXACT_SELECTION"
SELECTION = (
    "delivery_id",
    "alert_id",
    "signal_id",
    "watch_id",
    "revision",
    "message_sha256",
    "evidence_sha256",
    "entry_sha256",
    "intent_sha256",
    "source_alert_sha256",
    "route_sha256",
    "consent_sha256",
    "binding_sha256",
)


class QualificationError(ValueError):
    """Fixed local failures carry no private values or raw exceptions."""


def _budget(timeout: float, maximum: float = 5.0) -> Budget:
    current = app._invocation_budget.get()
    if current is not None:
        current.remaining()
        return current
    return Budget(timeout, maximum)


def _json(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
    )


def _digest(value: object) -> str:
    return hashlib.sha256(_json(value).encode("ascii")).hexdigest()


def _safe(path: Path, *, directory: bool = False) -> Path:
    target = (
        paths._checked_path(path / "directory-check").parent
        if directory
        else paths._checked_path(path)
    )
    paths._unsafe_stat(target, file=not directory)
    return target


def _sync_directory(directory: Path) -> None:
    # Windows does not expose directory fsync through this API. Disclose it.
    if os.name != "nt":
        descriptor = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def _exclusive(path: Path, value: object) -> tuple[int, int]:
    target = paths._checked_path(path)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(target, flags, 0o600)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise QualificationError("unsafe_evidence")
        raw = (_json(value) + "\n").encode("ascii")
        with os.fdopen(descriptor, "wb", closefd=False) as output:
            output.write(raw)
            output.flush()
            os.fsync(descriptor)
        after = paths._unsafe_stat(target, file=True)
        if (after.st_dev, after.st_ino) != (before.st_dev, before.st_ino):
            raise QualificationError("unsafe_evidence")
        _sync_directory(target.parent)
        return before.st_dev, before.st_ino
    finally:
        os.close(descriptor)


def _read(path: Path) -> dict[str, Any]:
    target = _safe(path)
    before = target.stat()
    if before.st_size > 1_048_576:
        raise QualificationError("invalid_evidence")
    value = validation.read_json(target)
    after = _safe(path).stat()
    if (before.st_dev, before.st_ino, before.st_size) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
    ) or type(value) is not dict:
        raise QualificationError("invalid_evidence")
    return value


def _candidate(repository: Path, head: str, tree: str, budget: Budget) -> None:
    if any(re.fullmatch(r"[0-9a-f]{40}", value) is None for value in (head, tree)):
        raise QualificationError("candidate_mismatch")
    for arguments, expected in (
        (["rev-parse", "HEAD"], head),
        (["rev-parse", "HEAD^{tree}"], tree),
        (["status", "--porcelain", "--untracked-files=all"], ""),
    ):
        result = subprocess.run(
            ["git", "-C", str(repository), *arguments],
            capture_output=True,
            text=True,
            timeout=budget.remaining(),
            check=False,
        )
        if result.returncode or result.stdout.strip() != expected:
            raise QualificationError("candidate_mismatch")


def _ensure_installed() -> None:
    import card_market_tracker

    if not Path(card_market_tracker.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()):
        raise QualificationError("installed_wheel_required")


def _source_hashes(sources: dict[str, str], budget: Budget) -> dict[str, str]:
    result = {}
    for name, raw_path in sources.items():
        path = _safe(Path(raw_path))
        before = path.stat()
        digest = hashlib.sha256()
        with path.open("rb") as source:
            while chunk := source.read(65536):
                budget.remaining()
                digest.update(chunk)
        after = _safe(path).stat()
        if (before.st_dev, before.st_ino, before.st_size) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
        ):
            raise QualificationError("originals_changed")
        result[name] = digest.hexdigest()
    return result


def _selection(item: dict[str, Any]) -> dict[str, Any]:
    return {key: item[key] for key in SELECTION}


def _attestation(
    dossier: dict[str, Any],
    operation: str,
    counters: dict[str, int],
    *,
    result: str = "ok",
    category: str | None = None,
    receipt_verified: bool = False,
) -> dict[str, Any]:
    return {
        "version": 1,
        "operation": operation,
        "result": result,
        "qualification_sha256": _digest(dossier),
        "candidate_head": dossier["candidate_head"],
        "candidate_tree": dossier["candidate_tree"],
        "selection": dossier["selection"],
        "live_status": "LIVE_UNVERIFIED",
        "evidence_kind": "instrumented_method_reservations_require_independent_review",
        "request_counters": counters,
        "durable_receipt_verified": receipt_verified,
        "error_category": category,
        "directory_fsync_supported": os.name != "nt",
    }


def preflight(
    directory: Path,
    repository: Path,
    head: str,
    tree: str,
    ledger: Path,
    watchlist: Path,
    journal: Path,
    outbox: Path,
    manifest: Path,
    delivery_id: str,
    *,
    timeout: float = 2.0,
) -> dict[str, Any]:
    """Read-only product checks; exclusively reserve a new private evidence directory."""
    budget = _budget(timeout)
    _ensure_installed()
    _candidate(repository, head, tree, budget)
    sources = {
        "watchlist": str(_safe(watchlist)),
        "journal": str(_safe(journal)),
        "outbox": str(_safe(outbox)),
        "manifest": str(_safe(manifest)),
    }
    original_hashes = _source_hashes(sources, budget)
    context = app._invocation_budget.set(budget)
    try:
        app.recompute(
            ledger,
            watchlist,
            journal,
            outbox,
            validation.read_json(manifest),
            delivery_id,
            timeout=timeout,
        )
        item = storage.load_delivery(ledger, delivery_id, _budget=budget, _for_send=True)
        if item["state"] != "ready" or item["attempt_count"] != 0:
            raise QualificationError("qualification_requires_unused_ready_delivery")
        selected = _selection(item)
        if _source_hashes(sources, budget) != original_hashes:
            raise QualificationError("originals_changed")
    finally:
        app._invocation_budget.reset(context)
    ledger_path = _safe(ledger)
    ledger_info = ledger_path.stat()
    dossier = {
        "version": 1,
        "qualification_id": uuid4().hex,
        "candidate_head": head,
        "candidate_tree": tree,
        "repository": str(repository.resolve()),
        "ledger": str(ledger_path),
        "ledger_identity": [ledger_info.st_dev, ledger_info.st_ino],
        "alias": item["destination_key"],
        "sources": sources,
        "source_sha256": original_hashes,
        "selection": selected,
        "acknowledgement": ACK,
        "limits": {"metadata_request_upper_bound": 8, "send_attempt_upper_bound": 1},
    }
    target = paths._checked_path(directory)
    target.mkdir(mode=0o700, parents=False, exist_ok=False)
    _sync_directory(target.parent)
    _exclusive(target / "dossier.json", dossier)
    template = {
        "version": 1,
        "decision": "PENDING_NOT_AUTHORIZED",
        "authorization_reference": "REPLACE_WITH_EXPLICIT_OPERATOR_AND_ORCHESTRATOR_REFERENCE",
        "qualification_sha256": _digest(dossier),
        "candidate_head": head,
        "candidate_tree": tree,
        "selection": selected,
        "acknowledgement": ACK,
    }
    _exclusive(target / "authorization-template.json", template)
    budget.remaining()
    return _attestation(dossier, "preflight", _counters([]))


def _events(directory: Path) -> list[dict[str, Any]]:
    rows = []
    previous = "0" * 64
    for ordinal, path in enumerate(sorted(directory.glob("event-*.json")), 1):
        if ordinal > 1000:
            raise QualificationError("evidence_limit")
        if path.name != f"event-{ordinal:06d}.json":
            raise QualificationError("invalid_evidence")
        row = _read(path)
        if (
            set(row) != {"version", "ordinal", "previous_sha256", "kind", "payload"}
            or type(row["version"]) is not int
            or row["version"] != 1
            or type(row["ordinal"]) is not int
            or row["ordinal"] != ordinal
            or row["previous_sha256"] != previous
        ):
            raise QualificationError("invalid_evidence")
        rows.append(row)
        previous = _digest(row)
    return rows


def _append(directory: Path, kind: str, payload: dict[str, Any]) -> None:
    rows = _events(directory)
    ordinal = len(rows) + 1
    _exclusive(
        directory / f"event-{ordinal:06d}.json",
        {
            "version": 1,
            "ordinal": ordinal,
            "previous_sha256": _digest(rows[-1]) if rows else "0" * 64,
            "kind": kind,
            "payload": payload,
        },
    )


def _counters(events: list[dict[str, Any]]) -> dict[str, int]:
    counts = {
        "metadata_request_upper_bound": 0,
        "send_attempt_upper_bound": 0,
        "metadata_method_entry_reservations": 0,
        "send_method_entry_reservations": 0,
        "successful_metadata_expected_requests": 0,
        "send_method_completions": 0,
    }
    for row in events:
        kind, payload = row["kind"], row["payload"]
        if kind == "method-reserved":
            method = payload.get("method")
            if method not in {"validate_destination", "validate_bot", "send"} or set(payload) != {
                "method",
                "metadata",
                "send",
            }:
                raise QualificationError("invalid_evidence")
            meta, send = (
                (2, 0)
                if method == "validate_destination"
                else ((1, 0) if method == "validate_bot" else (0, 1))
            )
            if (
                type(payload["metadata"]) is not int
                or type(payload["send"]) is not int
                or (payload["metadata"], payload["send"]) != (meta, send)
            ):
                raise QualificationError("invalid_evidence")
            counts["metadata_request_upper_bound"] += meta
            counts["send_attempt_upper_bound"] += send
            counts["metadata_method_entry_reservations"] += int(meta > 0)
            counts["send_method_entry_reservations"] += send
        elif kind == "method-completed":
            method = payload.get("method")
            if method not in {"validate_destination", "validate_bot", "send"}:
                raise QualificationError("invalid_evidence")
            counts["successful_metadata_expected_requests"] += {
                "validate_destination": 2,
                "validate_bot": 1,
                "send": 0,
            }[method]
            counts["send_method_completions"] += int(method == "send")
        elif kind not in {"operation-started", "operation-ended", "receipt"}:
            raise QualificationError("invalid_evidence")
    if counts["metadata_request_upper_bound"] > 8 or counts["send_attempt_upper_bound"] > 1:
        raise QualificationError("qualification_budget_exhausted")
    return counts


@contextmanager
def _locked(directory: Path):
    target = _safe(directory, directory=True)
    marker = target / "active.json"
    identity = _exclusive(marker, {"version": 1, "worker": uuid4().hex})
    # Any unhandled failure/crash deliberately retains the marker and blocks reuse.
    yield target
    info = paths._unsafe_stat(marker, file=True)
    if (info.st_dev, info.st_ino) != identity:
        raise QualificationError("unsafe_evidence")
    marker.unlink()
    _sync_directory(target)


class AccountedTransport:
    def __init__(
        self,
        client: app.Transport,
        directory: Path,
        operation: str,
        faults: list[bool],
        budget: Budget,
    ) -> None:
        self.client, self.directory, self.operation = client, directory, operation
        self.faults = faults
        self.budget = budget

    def _record(self, kind: str, payload: dict[str, Any]) -> None:
        try:
            _append(self.directory, kind, payload)
        except Exception:
            self.faults.append(True)
            raise

    def check_configuration(self) -> None:
        self.client.check_configuration()

    def _reserve(self, method: str, metadata: int, send: int) -> None:
        if method == "send" and self.operation != "send":
            raise QualificationError("unexpected_provider_method")
        counts = _counters(_events(self.directory))
        if (
            counts["metadata_request_upper_bound"] + metadata > 8
            or counts["send_attempt_upper_bound"] + send > 1
        ):
            raise QualificationError("qualification_budget_exhausted")
        self._record(
            "method-reserved",
            {"method": method, "metadata": metadata, "send": send},
        )

    def validate_destination(self, bot_id: int, chat_id: int, *, timeout: float) -> None:
        self._reserve("validate_destination", 2, 0)
        self.client.validate_destination(
            bot_id, chat_id, timeout=min(timeout, self.budget.preclaim())
        )
        self._record("method-completed", {"method": "validate_destination"})

    def validate_bot(self, bot_id: int, *, timeout: float) -> None:
        self._reserve("validate_bot", 1, 0)
        self.client.validate_bot(bot_id, timeout=min(timeout, self.budget.preclaim()))
        self._record("method-completed", {"method": "validate_bot"})

    def send(self, bot_id: int, chat_id: int, message_text: str, *, timeout: float) -> object:
        self._reserve("send", 0, 1)
        result = self.client.send(
            bot_id, chat_id, message_text, timeout=min(timeout, self.budget.preclaim())
        )
        self._record("method-completed", {"method": "send"})
        return result


def _authorize(dossier: dict[str, Any], authorization: Path) -> None:
    value = _read(authorization)
    reference = value.get("authorization_reference")
    expected = {
        "version": 1,
        "decision": DECISION,
        "authorization_reference": reference,
        "qualification_sha256": _digest(dossier),
        "candidate_head": dossier["candidate_head"],
        "candidate_tree": dossier["candidate_tree"],
        "selection": dossier["selection"],
        "acknowledgement": ACK,
    }
    if (
        type(reference) is not str
        or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}", reference) is None
        or _json(value) != _json(expected)
    ):
        raise QualificationError("specific_operator_authorization_required")


def _recheck(dossier: dict[str, Any], budget: Budget) -> dict[str, Any]:
    _candidate(
        Path(dossier["repository"]), dossier["candidate_head"], dossier["candidate_tree"], budget
    )
    ledger = _safe(Path(dossier["ledger"]))
    info = ledger.stat()
    if [info.st_dev, info.st_ino] != dossier["ledger_identity"]:
        raise QualificationError("ledger_identity_changed")
    # app.send alone owns its nonrenewable aggregate origins scope. Avoid
    # duplicate source reads/recompute before it under a separate allowance.
    did = dossier["selection"]["delivery_id"]
    saved = storage.load_delivery(ledger, did, _budget=budget, _for_send=True)
    if _selection(saved) != dossier["selection"]:
        raise QualificationError("selection_changed")
    return saved


def remote(
    directory: Path, authorization: Path, operation: str, *, timeout: float = 15.0
) -> dict[str, Any]:
    """Inert unless exact matching external authorization exists. Never auto-retry."""
    if operation not in {"validate", "send"}:
        raise QualificationError("invalid_operation")
    budget = _budget(timeout, 30)
    _ensure_installed()
    with _locked(directory) as target:
        dossier = _read(target / "dossier.json")
        _authorize(dossier, authorization)
        previous = _counters(_events(target))
        # Block repeated send invocations before even constructing a client.
        if previous["send_attempt_upper_bound"]:
            raise QualificationError("qualification_budget_exhausted")
        context = app._invocation_budget.set(budget)
        original_factory = app._transport_factory
        category = None
        receipt_verified = False
        faults: list[bool] = []
        try:
            item = _recheck(dossier, budget)
            if operation == "send" and (item["state"] != "ready" or item["attempt_count"] != 0):
                raise QualificationError("qualification_requires_unused_ready_delivery")
            _append(
                target,
                "operation-started",
                {"operation": operation, "authorization_sha256": _digest(_read(authorization))},
            )
            app._transport_factory = lambda: AccountedTransport(
                original_factory(), target, operation, faults, budget
            )
            ledger = Path(dossier["ledger"])
            try:
                if operation == "validate":
                    response = app.destination_validate(ledger, dossier["alias"], timeout=timeout)
                else:
                    source = {key: Path(value) for key, value in dossier["sources"].items()}
                    response = app.send(
                        ledger,
                        dossier["selection"]["delivery_id"],
                        watchlist_db=source["watchlist"],
                        journal_db=source["journal"],
                        outbox_db=source["outbox"],
                        manifest=app._manifest_file(source["manifest"], budget),
                        timeout=timeout,
                    )
                category = response.get("error_category")
            except DeliveryError as error:
                category = error.category
            if faults:
                raise QualificationError("evidence_persistence_failed")
            saved = storage.load_delivery(
                ledger, dossier["selection"]["delivery_id"], _budget=budget, _for_send=True
            )
            if saved["state"] == "confirmed":
                if saved["attempt_count"] != 1:
                    raise QualificationError("invalid_qualification_receipt")
                receipt = saved["attempts"][0]["result"]
                _append(
                    target,
                    "receipt",
                    {
                        key: receipt[key]
                        for key in ("message_id", "accepted_at", "bot_id", "chat_id")
                    },
                )
                receipt_verified = True
            _append(
                target,
                "operation-ended",
                {
                    "operation": operation,
                    "error_category": category,
                    "originals_proof": "postflight_required",
                },
            )
            result = _attestation(
                dossier,
                operation,
                _counters(_events(target)),
                result="error" if category else "ok",
                category=category,
                receipt_verified=receipt_verified,
            )
            budget.remaining()
            return result
        finally:
            app._transport_factory = original_factory
            app._invocation_budget.reset(context)


_REPLAY_CHILD = r"""
import hashlib, importlib.abc, json, os, socket, sys


class Denied(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith("card_market_tracker.telegram_delivery"):
            raise RuntimeError("forbidden_replay_import")


sys.meta_path.insert(0, Denied())


def blocked(*args, **kwargs):
    raise RuntimeError("forbidden_replay_network")


socket.socket = socket.create_connection = socket.getaddrinfo = blocked
old_get = os.environ.get
old_item = type(os.environ).__getitem__


def guarded_get(key, *args):
    if key == "CMT_TELEGRAM_BOT_TOKEN":
        raise RuntimeError("forbidden_replay_token")
    return old_get(key, *args)


def guarded_item(self, key):
    if key == "CMT_TELEGRAM_BOT_TOKEN":
        raise RuntimeError("forbidden_replay_token")
    return old_item(self, key)


os.environ.get = guarded_get
type(os.environ).__getitem__ = guarded_item
from pathlib import Path
from card_market_tracker.watchlist_delivery import application, storage

p = Path(sys.argv[1])
did = sys.argv[2]
response = application.send(p, did, timeout=float(sys.argv[3]))
item = storage.load_delivery(p, did, timeout=float(sys.argv[3]))
assert response["result"] == "replay" and item["state"] == "confirmed"
assert item["attempt_count"] == 1 and not item["send_quarantined"]
receipt = item["attempts"][0]["result"]
assert receipt["state"] == "confirmed" and receipt["error_category"] is None
projection = {key: receipt[key] for key in ("message_id", "accepted_at", "bot_id", "chat_id")}
assert (
    hashlib.sha256(
        json.dumps(
            projection, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
        ).encode("ascii")
    ).hexdigest()
    == sys.argv[4]
)
print(
    json.dumps({"result": "replay", "attempt_count": 1, "binding_sha256": item["binding_sha256"]})
)
"""


def replay(directory: Path, *, timeout: float = 2.0) -> dict[str, Any]:
    budget = _budget(timeout)
    with _locked(directory) as target:
        dossier = _read(target / "dossier.json")
        _candidate(
            Path(dossier["repository"]),
            dossier["candidate_head"],
            dossier["candidate_tree"],
            budget,
        )
        ledger_info = _safe(Path(dossier["ledger"])).stat()
        if [ledger_info.st_dev, ledger_info.st_ino] != dossier["ledger_identity"]:
            raise QualificationError("ledger_identity_changed")
        before = _counters(_events(target))
        if before["send_attempt_upper_bound"] != 1 or not any(
            row["kind"] == "receipt" for row in _events(target)
        ):
            raise QualificationError("confirmed_qualification_required")
        receipt_events = [row for row in _events(target) if row["kind"] == "receipt"]
        receipt_sha256 = _digest(receipt_events[-1]["payload"])
        environment = {
            key: os.environ[key]
            for key in os.environ
            if key not in {"CMT_TELEGRAM_BOT_TOKEN", "PYTHONPATH"}
        }
        response = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                "-c",
                _REPLAY_CHILD,
                dossier["ledger"],
                dossier["selection"]["delivery_id"],
                str(budget.remaining()),
                receipt_sha256,
            ],
            env=environment,
            capture_output=True,
            text=True,
            timeout=budget.remaining(),
            check=False,
        )
        if response.returncode:
            raise QualificationError("isolated_replay_failed")
        output = json.loads(response.stdout)
        if (
            output
            != {
                "result": "replay",
                "attempt_count": 1,
                "binding_sha256": dossier["selection"]["binding_sha256"],
            }
            or _counters(_events(target)) != before
        ):
            raise QualificationError("isolated_replay_failed")
        _append(
            target,
            "operation-ended",
            {"operation": "replay", "zero_provider_calls": True, "separate_process": True},
        )
        budget.remaining()
        return _attestation(dossier, "replay", before, receipt_verified=True)


def postflight(directory: Path, *, timeout: float = 2.0) -> dict[str, Any]:
    """Separate offline original-byte proof, never a new send allowance."""
    budget = _budget(timeout)
    with _locked(directory) as target:
        dossier = _read(target / "dossier.json")
        _candidate(
            Path(dossier["repository"]),
            dossier["candidate_head"],
            dossier["candidate_tree"],
            budget,
        )
        if _source_hashes(dossier["sources"], budget) != dossier["source_sha256"]:
            raise QualificationError("originals_changed")
        counts = _counters(_events(target))
        _append(
            target,
            "operation-ended",
            {
                "operation": "postflight",
                "originals_unchanged": True,
            },
        )
        budget.remaining()
        return {**_attestation(dossier, "postflight", counts), "originals_unchanged": True}


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise QualificationError("invalid_arguments")


def main(argv: list[str] | None = None) -> int:
    started = time.monotonic()
    parser = _Parser(description=__doc__, allow_abbrev=False)
    parser.add_argument(
        "--operation",
        choices=("preflight", "validate", "send", "replay", "postflight"),
        required=True,
    )
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--candidate-repository", type=Path)
    parser.add_argument("--candidate-head")
    parser.add_argument("--candidate-tree")
    parser.add_argument("--ledger-db", type=Path)
    parser.add_argument("--watchlist-db", type=Path)
    parser.add_argument("--journal-db", type=Path)
    parser.add_argument("--outbox-db", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--delivery-id")
    parser.add_argument("--timeout", type=float)
    try:
        args = parser.parse_args(argv)
    except QualificationError:
        print(
            _json(
                {
                    "version": 1,
                    "operation": "arguments",
                    "result": "error",
                    "error_category": "invalid_arguments",
                    "live_status": "LIVE_UNVERIFIED",
                }
            )
        )
        return 1
    context = None
    try:
        maximum = 30.0 if args.operation in {"validate", "send"} else 5.0
        default = 15.0 if maximum == 30.0 else 2.0
        selected_timeout = default if args.timeout is None else args.timeout
        budget = Budget(selected_timeout, maximum, started=started)
        budget.remaining()
        context = app._invocation_budget.set(budget)
        if args.operation == "preflight":
            required = (
                args.candidate_repository,
                args.candidate_head,
                args.candidate_tree,
                args.ledger_db,
                args.watchlist_db,
                args.journal_db,
                args.outbox_db,
                args.manifest,
                args.delivery_id,
            )
            if any(value is None for value in required):
                raise QualificationError("explicit_selection_required")
            result = preflight(args.directory, *required, timeout=selected_timeout)
        elif args.operation == "replay":
            result = replay(args.directory, timeout=selected_timeout)
        elif args.operation == "postflight":
            result = postflight(args.directory, timeout=selected_timeout)
        else:
            if args.authorization is None:
                raise QualificationError("specific_operator_authorization_required")
            result = remote(
                args.directory,
                args.authorization,
                args.operation,
                timeout=selected_timeout,
            )
        output = _json(result)
        budget.remaining()
        print(output)
        return 0 if result["result"] == "ok" else 1
    except Exception as error:
        category = str(error) if type(error) is QualificationError else "qualification_failed"
        print(
            _json(
                {
                    "version": 1,
                    "operation": args.operation,
                    "result": "error",
                    "error_category": category,
                    "live_status": "LIVE_UNVERIFIED",
                }
            )
        )
        return 1
    finally:
        if context is not None:
            app._invocation_budget.reset(context)


if __name__ == "__main__":
    raise SystemExit(main())
