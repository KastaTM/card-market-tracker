"""Independent capture admission, immutable evidence and consistent bounded reads."""

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from ..catalog.manifest import Manifest
from ..catalog.models import Entity
from ..catalog.resolver import resolve
from ..catalog.validation import MAX_DEPTH, MAX_NODES, MAX_STRING, CatalogError, uuid_value
from ..discovery.errors import DiscoveryError
from ..discovery.models import BatchSnapshot
from ..discovery.validation import validate_snapshot
from . import sqlite_repository as db
from .application import canonical_payload, validate_batch
from .errors import PersistenceError
from .input import (
    bounded_value,
    canonical_json,
    entity_dict,
    observation_dict,
    reference_value,
    utc_timestamp,
    validated_manifest,
)
from .models import PersistedRecord, PersistenceBatch, WriteResult

MAX_CAPTURE_BYTES = 1_000_000


def _capture_row(
    connection: sqlite3.Connection, budget: db._Budget, token: str
) -> sqlite3.Row | None:
    # SQL checks bytes before Python materializes attacker-modified envelope text.
    size = db._execute(
        connection,
        budget,
        "SELECT length(CAST(envelope AS BLOB)) FROM captures WHERE batch_id=?",
        (token,),
    ).fetchone()
    if size is None:
        return None
    if type(size[0]) is not int or not 2 <= size[0] <= MAX_CAPTURE_BYTES:
        raise PersistenceError("storage_corrupt")
    return cast(
        sqlite3.Row | None,
        db._execute(
            connection,
            budget,
            "SELECT * FROM captures WHERE batch_id=? "
            "AND length(CAST(envelope AS BLOB)) BETWEEN 2 AND ?",
            (token, MAX_CAPTURE_BYTES),
        ).fetchone(),
    )


def _decode_envelope(text: str, budget: db._Budget) -> object:
    # Lexical limits run before constructing the complete decoded object graph.
    depth = nodes = index = 0
    while index < len(text):
        if index % 1024 == 0:
            budget.remaining()
        char = text[index]
        if char in "[{":
            depth += 1
            nodes += 1
            if depth > MAX_DEPTH:
                raise PersistenceError("storage_corrupt")
            index += 1
        elif char in "]}":
            depth -= 1
            index += 1
        elif char == '"':
            start = index
            index += 1
            escaped = False
            while index < len(text):
                if index - start > MAX_STRING * 6 + 2:
                    raise PersistenceError("storage_corrupt")
                current = text[index]
                index += 1
                if escaped:
                    escaped = False
                elif current == "\\":
                    escaped = True
                elif current == '"':
                    break
            if len(json.loads(text[start:index])) > MAX_STRING:
                raise PersistenceError("storage_corrupt")
            nodes += 1
        elif char in " ,:\t\r\n":
            index += 1
        else:
            nodes += 1
            while index < len(text) and text[index] not in " ,:[]{}\t\r\n":
                index += 1
        if nodes > MAX_NODES:
            raise PersistenceError("storage_corrupt")
    return json.loads(text)


def _hash(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("ascii")).hexdigest()


def _manifest(manifest: Manifest) -> dict[str, object]:
    return {
        "version": 1,
        "entities": [
            entity_dict(entity) for entity in sorted(manifest.entities, key=lambda e: e.cmt_id)
        ],
        "bindings": sorted(
            [
                {
                    "reference": reference_value(binding.reference),
                    "cmt_id": binding.cmt_id,
                    "reason": "retained resolver context",
                }
                for binding in manifest.bindings
            ],
            key=canonical_json,
        ),
    }


def store_legacy(connection: sqlite3.Connection, budget: db._Budget, token: str) -> None:
    envelope = {"version": 1, "scope": None, "evidence_state": "legacy_unverified"}
    db._execute(
        connection,
        budget,
        "INSERT INTO captures VALUES (?,?,?,?,?)",
        (token, "legacy", "legacy_unverified", canonical_json(envelope), _hash(envelope)),
    )


def _bundle_batch(
    bundle: object, batch_id: object, manifest: object, *, multi_revision: bool = False
) -> tuple[PersistenceBatch, dict[str, object]]:
    from ..pinned_repository import (
        VerifiedBundle,
        bundle_document,
        capture_evidence,
        observations,
        validate_bundle,
    )

    if multi_revision:
        from ..pinned_repository.bundle_v2 import (
            VerifiedBundleV2,
            bundle_document_v2,
            capture_evidence_v2,
            observations_v2,
            validate_bundle_v2,
        )

        raw = (
            bundle_document_v2(bundle)
            if isinstance(bundle, VerifiedBundleV2)
            else bundle_document(bundle)
            if isinstance(bundle, VerifiedBundle)
            else bundle
        )
        verified_v2 = validate_bundle_v2(raw)
        document = bundle_document_v2(verified_v2)
        items = observations_v2(verified_v2)
        evidence = capture_evidence_v2(verified_v2)
    else:
        verified = validate_bundle(
            bundle_document(bundle) if isinstance(bundle, VerifiedBundle) else bundle
        )
        document = bundle_document(verified)
        items = observations(verified)
        evidence = capture_evidence(verified)
    token = uuid_value(batch_id)
    curated = validated_manifest(manifest)
    captured_at = utc_timestamp(document["captured_at"], required=True)
    assert captured_at is not None
    result = resolve(items, curated)
    evidence = dict(evidence)
    evidence["counts"] = {
        "input": len(items),
        "accepted": result.accepted,
        "candidates": result.candidates,
        "rejected": result.rejected,
    }
    units = cast(list[dict[str, object]], evidence["units"])
    counted_units = []
    for unit in units:
        indexes = [
            index
            for index, item in enumerate(items)
            if (item.reference.namespace, item.kind, item.reference.language)
            == (unit["namespace"], unit["kind"], unit["language"])
        ]
        counted_units.append(
            {
                **unit,
                "record_indexes": indexes,
                "accepted_count": sum(result.records[i].status == "accepted" for i in indexes),
                "candidate_count": sum(result.records[i].status == "candidate" for i in indexes),
                "rejected_count": sum(result.records[i].status == "rejected" for i in indexes),
            }
        )
    evidence["units"] = counted_units
    records = tuple(
        PersistedRecord(
            row.index,
            row.status,
            row.category,
            row.cmt_id,
            None if row.status == "rejected" else items[row.index],
        )
        for row in result.records
    )
    batch = PersistenceBatch(1, token, captured_at, curated, records, result.entities)
    envelope = {
        "version": document["version"],
        "bundle": document,
        "scope": evidence,
        "manifest": _manifest(curated),
    }
    bounded_value(envelope)
    return batch, envelope


def _synthetic_scope(batch: PersistenceBatch, value: object) -> dict[str, object]:
    bounded_value(value)
    if not isinstance(value, dict) or set(value) != {
        "version",
        "units",
        "outcome",
        "acquired_at",
        "captured_at",
    }:
        raise PersistenceError("invalid_shape")
    if type(value["version"]) is not int or value["version"] != 1:
        raise PersistenceError("invalid_version")
    capture = utc_timestamp(value["captured_at"], required=True)
    acquired = utc_timestamp(value["acquired_at"], required=True)
    if capture != batch.captured_at:
        raise PersistenceError("capture_conflict")
    units = value["units"]
    if not isinstance(units, list) or not 1 <= len(units) <= 32:
        raise PersistenceError("input_limit")
    seen: set[int] = set()
    contexts: set[tuple[object, ...]] = set()
    complete = True
    normalized: list[dict[str, object]] = []
    for unit in units:
        if not isinstance(unit, dict) or set(unit) != {
            "namespace",
            "kind",
            "language",
            "selector",
            "selected",
            "completed",
            "record_indexes",
        }:
            raise PersistenceError("invalid_shape")
        context = (unit["namespace"], unit["kind"], unit["language"])
        if (
            not isinstance(context[0], str)
            or not 1 <= len(context[0]) <= 128
            or context[1] not in ("set", "card", "sealed")
            or context[2] not in (None, "es", "en")
            or not isinstance(unit["selector"], str)
            or not 1 <= len(unit["selector"]) <= 256
        ):
            raise PersistenceError("invalid_field")
        key = (*context, unit["selector"])
        if key in contexts:
            raise PersistenceError("invalid_field")
        contexts.add(key)
        for field in ("selected", "completed"):
            paths = unit[field]
            if (
                not isinstance(paths, list)
                or len(paths) > 1000
                or any(not isinstance(path, str) or not 1 <= len(path) <= 256 for path in paths)
                or len(set(paths)) != len(paths)
            ):
                raise PersistenceError("invalid_field")
        if not unit["selected"] or not set(unit["completed"]) <= set(unit["selected"]):
            raise PersistenceError("invalid_field")
        complete = complete and set(unit["selected"]) == set(unit["completed"])
        indexes = unit["record_indexes"]
        if not isinstance(indexes, list) or len(indexes) > 1000:
            raise PersistenceError("input_limit")
        for index in indexes:
            if type(index) is not int or not 0 <= index < len(batch.records) or index in seen:
                raise PersistenceError("invalid_field")
            seen.add(index)
            observation = batch.records[index].observation
            if (
                observation is not None
                and (
                    observation.reference.namespace,
                    observation.kind,
                    observation.reference.language,
                )
                != context
            ):
                raise PersistenceError("capture_conflict")
        normalized.append(
            {
                **unit,
                "selected": sorted(unit["selected"]),
                "completed": sorted(unit["completed"]),
                "record_indexes": sorted(indexes),
            }
        )
    outcome = value["outcome"]
    if (
        outcome not in ("complete", "partial", "failed")
        or (outcome == "complete" and not complete)
        or (outcome == "failed" and batch.records)
    ):
        raise PersistenceError("invalid_field")
    if seen != set(range(len(batch.records))):
        raise PersistenceError("capture_conflict")
    return {
        "version": 1,
        "units": sorted(normalized, key=canonical_json),
        "outcome": outcome,
        "acquired_at": acquired,
        "captured_at": capture,
    }


def _payload(batch: PersistenceBatch) -> dict[str, object]:
    return {
        "captured_at": batch.captured_at,
        "entities": [entity_dict(entity) for entity in batch.entities],
        "records": [
            {
                "index": row.index,
                "status": row.status,
                "category": row.category,
                "cmt_id": row.cmt_id,
                "observation": None
                if row.observation is None
                else observation_dict(row.observation),
            }
            for row in batch.records
        ],
    }


def _write(
    path: Path, batch: PersistenceBatch, envelope: dict[str, object], mode: str, timeout: float
) -> WriteResult:
    envelope = {**envelope, "snapshot": _payload(batch)}
    bounded_value(envelope)
    encoded = canonical_json(envelope)
    digest = _hash(envelope)
    with db._connection(path, writable=True, create=True, timeout=timeout) as (connection, budget):
        db._initialize(connection, budget)
        if db._execute(connection, budget, "PRAGMA user_version").fetchone()[0] != 2:
            raise PersistenceError("storage_schema")
        with db._transaction(connection, budget):
            previous = db._execute(
                connection, budget, "SELECT * FROM batches WHERE batch_id=?", (batch.batch_id,)
            ).fetchone()
            if previous is not None:
                capture = _capture_row(connection, budget, batch.batch_id)
                if capture is not None:
                    _check_capture(connection, budget, previous, capture)
                if (
                    capture is None
                    or capture["mode"] != mode
                    or capture["envelope"] != encoded
                    or capture["capture_fingerprint"] != digest
                ):
                    raise PersistenceError("replay_conflict")
                return db._result(previous, replay=True, observations=0, entities=0)
            inserted = db._project_entities(connection, budget, batch.entities)
            count = len(batch.records)
            accepted = sum(row.status == "accepted" for row in batch.records)
            candidates = sum(row.status == "candidate" for row in batch.records)
            rejected = count - accepted - candidates
            outcome = "empty" if count == 0 else "ok" if accepted == count else "mixed"
            first = datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
            db._execute(
                connection,
                budget,
                "INSERT INTO batches VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    batch.batch_id,
                    1,
                    1,
                    batch.captured_at,
                    first,
                    digest,
                    _hash(envelope["manifest"]),
                    count,
                    accepted,
                    candidates,
                    rejected,
                    outcome,
                ),
            )
            state = "verified_local_pinned_bundle" if mode == "pinned" else "producer_declared"
            db._execute(
                connection,
                budget,
                "INSERT INTO captures VALUES (?,?,?,?,?)",
                (batch.batch_id, mode, state, encoded, digest),
            )
            for row in batch.records:
                db._execute(
                    connection,
                    budget,
                    "INSERT INTO records ("
                    + db._RECORD_COLUMNS
                    + ") VALUES ("
                    + ",".join("?" for _ in range(19))
                    + ")",
                    db._record_values(batch.batch_id, row),
                )
            metadata = db._execute(
                connection, budget, "SELECT * FROM batches WHERE batch_id=?", (batch.batch_id,)
            ).fetchone()
            result = db._result(
                metadata, replay=False, observations=accepted + candidates, entities=inserted
            )
    return result


def persist_bundle(
    path: Path,
    bundle: object,
    batch_id: object,
    manifest: object,
    *,
    timeout: float = db.DEFAULT_TIMEOUT,
) -> WriteResult:
    try:
        batch, envelope = _bundle_batch(bundle, batch_id, manifest)
        return _write(path, batch, envelope, "pinned", timeout)
    except CatalogError as error:
        raise PersistenceError(error.category) from None


def persist_bundle_v2(
    path: Path,
    bundle: object,
    batch_id: object,
    manifest: object,
    *,
    timeout: float = db.DEFAULT_TIMEOUT,
) -> WriteResult:
    """Explicit exact-pair admission; R0 retains its original envelope and replay."""
    try:
        batch, envelope = _bundle_batch(bundle, batch_id, manifest, multi_revision=True)
        return _write(path, batch, envelope, "pinned", timeout)
    except CatalogError as error:
        raise PersistenceError(error.category) from None


def persist_capture(
    path: Path, batch: PersistenceBatch, scope: object, *, timeout: float = db.DEFAULT_TIMEOUT
) -> WriteResult:
    try:
        admitted = validate_batch(batch)
        envelope = {
            "version": 1,
            "scope": _synthetic_scope(admitted, scope),
            "manifest": _manifest(admitted.manifest),
            "synthetic_payload": canonical_payload(admitted),
        }
        return _write(path, admitted, envelope, "synthetic", timeout)
    except CatalogError as error:
        raise PersistenceError(error.category) from None


def _check_capture(
    connection: sqlite3.Connection, budget: db._Budget, metadata: sqlite3.Row, capture: sqlite3.Row
) -> dict[str, object]:
    try:
        envelope = cast(Any, _decode_envelope(capture["envelope"], budget))
        bounded_value(envelope)
        if (
            canonical_json(envelope) != capture["envelope"]
            or _hash(envelope) != capture["capture_fingerprint"]
        ):
            raise PersistenceError("storage_corrupt")
        if capture["mode"] == "legacy":
            if envelope != {"version": 1, "scope": None, "evidence_state": "legacy_unverified"}:
                raise PersistenceError("storage_corrupt")
            if db._execute(
                connection,
                budget,
                "SELECT 1 FROM records WHERE batch_id=? AND provenance='observed' LIMIT 1",
                (metadata["batch_id"],),
            ).fetchone():
                raise PersistenceError("storage_corrupt")
            rows = db._execute(
                connection, budget, db._SNAPSHOT_JOIN, (metadata["batch_id"],)
            ).fetchall()
            if len(rows) > 1000:
                raise PersistenceError("storage_corrupt")
            try:
                snapshot = BatchSnapshot(
                    version=1,
                    records=tuple(db._snapshot_record(row) for row in rows),
                    **{
                        field: metadata[field]
                        for field in (
                            "input_version",
                            "resolver_version",
                            "batch_id",
                            "captured_at",
                            "first_persisted_at",
                            "fingerprint",
                            "context_fingerprint",
                            "input_count",
                            "accepted_count",
                            "candidate_count",
                            "rejected_count",
                            "result",
                        )
                    },
                )
                validate_snapshot(snapshot)
                identities: dict[str, tuple[Entity, Entity | None]] = {}
                for row in rows:
                    budget.remaining()
                    db._snapshot_target(row, identities)
            except DiscoveryError:
                raise PersistenceError("storage_corrupt") from None
            return cast(dict[str, object], envelope)
        if capture["mode"] == "pinned":
            if type(envelope.get("version")) is not int or envelope["version"] not in (1, 2):
                raise PersistenceError("storage_corrupt")
            batch, prepared = _bundle_batch(
                envelope["bundle"],
                metadata["batch_id"],
                envelope["manifest"],
                multi_revision=envelope["version"] == 2,
            )
        else:
            from ..catalog.ingestion import RecordError
            from .application import build_batch
            from .capture_decode import decode_observation

            payload = envelope["synthetic_payload"]
            items = tuple(
                RecordError(row["index"], row["category"])
                if row["observation"] is None
                else decode_observation(row["observation"])
                for row in payload["records"]
            )
            batch = build_batch(
                metadata["batch_id"], payload["captured_at"], items, envelope["manifest"]
            )
            prepared = {
                "version": 1,
                "scope": _synthetic_scope(batch, envelope["scope"]),
                "manifest": _manifest(batch.manifest),
                "synthetic_payload": canonical_payload(batch),
            }
        expected = {**prepared, "snapshot": _payload(batch)}
        if (
            envelope != expected
            or metadata["fingerprint"] != _hash(expected)
            or metadata["context_fingerprint"] != _hash(expected["manifest"])
            or metadata["captured_at"] != batch.captured_at
        ):
            raise PersistenceError("storage_corrupt")
        rows = db._execute(
            connection,
            budget,
            "SELECT "
            + db._RECORD_COLUMNS
            + " FROM records WHERE batch_id=? ORDER BY record_index LIMIT 1001",
            (batch.batch_id,),
        ).fetchall()
        if tuple(tuple(row) for row in rows) != tuple(
            db._record_values(batch.batch_id, row) for row in batch.records
        ):
            raise PersistenceError("storage_corrupt")
        accepted = sum(row.status == "accepted" for row in batch.records)
        candidates = sum(row.status == "candidate" for row in batch.records)
        rejected = len(rows) - accepted - candidates
        outcome = "empty" if not rows else "ok" if accepted == len(rows) else "mixed"
        if (
            metadata["input_count"],
            metadata["accepted_count"],
            metadata["candidate_count"],
            metadata["rejected_count"],
            metadata["result"],
        ) != (len(rows), accepted, candidates, rejected, outcome):
            raise PersistenceError("storage_corrupt")
        if (
            utc_timestamp(metadata["first_persisted_at"], required=True)
            != metadata["first_persisted_at"]
        ):
            raise PersistenceError("storage_corrupt")
        for entity in batch.entities:
            stored = db._execute(
                connection,
                budget,
                "SELECT " + db._ENTITY_COLUMNS + " FROM entities WHERE cmt_id=?",
                (entity.cmt_id,),
            ).fetchone()
            if stored is None or tuple(stored) != db._entity_values(entity):
                raise PersistenceError("storage_corrupt")
        return cast(dict[str, object], envelope)
    except PersistenceError as error:
        if error.category in ("storage_timeout", "storage_locked", "storage_io"):
            raise
        raise PersistenceError("storage_corrupt") from None
    except (KeyError, TypeError, ValueError, CatalogError, RecursionError):
        raise PersistenceError("storage_corrupt") from None


def verify_captures(connection: sqlite3.Connection, budget: db._Budget) -> None:
    missing = db._execute(
        connection,
        budget,
        "SELECT 1 FROM batches b LEFT JOIN captures c ON c.batch_id=b.batch_id "
        "WHERE c.batch_id IS NULL LIMIT 1",
    ).fetchone()
    if missing:
        raise PersistenceError("storage_corrupt")
    cursor = db._execute(connection, budget, "SELECT * FROM batches ORDER BY batch_id")
    for metadata in cursor:
        budget.remaining()
        capture = _capture_row(connection, budget, metadata["batch_id"])
        if capture is None:
            raise PersistenceError("storage_corrupt")
        _check_capture(connection, budget, metadata, capture)


def query_capture(
    path: Path, batch_id: object, *, timeout: float = db.DEFAULT_TIMEOUT
) -> dict[str, object]:
    try:
        token = uuid_value(batch_id)
    except CatalogError as error:
        raise PersistenceError(error.category) from None
    with db._connection(path, writable=False, timeout=timeout) as (connection, budget):
        db._execute(connection, budget, "BEGIN")
        db._require_schema(connection, budget)
        db._check_integrity(connection, budget)
        version = db._execute(connection, budget, "PRAGMA user_version").fetchone()[0]
        metadata = db._execute(
            connection, budget, "SELECT * FROM batches WHERE batch_id=?", (token,)
        ).fetchone()
        if metadata is None:
            raise PersistenceError("invalid_field")
        envelope: dict[str, object] = {
            "version": 1,
            "scope": None,
            "evidence_state": "legacy_unverified",
        }
        state = "legacy_unverified"
        if version == 2:
            capture = _capture_row(connection, budget, token)
            if capture is None:
                raise PersistenceError("storage_corrupt")
            envelope = _check_capture(connection, budget, metadata, capture)
            state = capture["evidence_state"]
        rows = db._execute(
            connection,
            budget,
            "SELECT * FROM records WHERE batch_id=? ORDER BY record_index LIMIT 1001",
            (token,),
        ).fetchall()
        if len(rows) > 1000 or len(rows) != metadata["input_count"]:
            raise PersistenceError("storage_corrupt")
        records = [
            {
                "index": row["record_index"],
                "status": row["status"],
                "category": row["category"],
                "cmt_id": row["cmt_id"],
                "observation": db._observation(row),
            }
            for row in rows
        ]
        budget.remaining()
    return {
        "version": 1,
        "result": "ok",
        "schema_version": version,
        "evidence_state": state,
        "capture": envelope,
        "batch": dict(metadata),
        "records": records,
    }
