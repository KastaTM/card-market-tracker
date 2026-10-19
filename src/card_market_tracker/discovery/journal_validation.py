"""Bounded local v3 grammar checks; source authentication belongs to recompute."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from io import StringIO
from typing import cast

from ..catalog.manifest import parse_reference
from ..catalog.validation import (
    CatalogError,
    _constant,
    _pairs,
    _preflight,
    array_value,
    object_value,
    string_value,
    token_value,
    uuid_value,
)
from .journal_errors import JournalError
from .multi_input import parse_request
from .multi_models import SYNTHETIC_PROFILE
from .scoped_errors import ScopedDiscoveryError
from .validation import CANDIDATE_CATEGORIES, bounded_value, canonical_json, canonical_timestamp

MAX_RESULT_BYTES = 16 * 1024 * 1024


def canonical_bounded(
    value: object, maximum: int = MAX_RESULT_BYTES, *, check: Callable[[], object] | None = None
) -> str:
    """Stop serialization before allocating more than the contracted ASCII cap."""
    parts = StringIO()
    size = 0
    try:
        for index, part in enumerate(
            json.JSONEncoder(
                ensure_ascii=True, sort_keys=True, separators=(",", ":"), allow_nan=False
            ).iterencode(value)
        ):
            if check is not None and index % 256 == 0:
                check()
            size += len(part)
            if size > maximum:
                raise JournalError("input_limit")
            parts.write(part)
    except (ValueError, TypeError, RecursionError, UnicodeError) as error:
        if isinstance(error, JournalError):
            raise
        raise JournalError("storage_corrupt") from None
    return parts.getvalue()


def decode_json(
    raw: str, *, maximum: int = MAX_RESULT_BYTES, check: Callable[[], object] | None = None
) -> object:
    """Lexical bounds precede parsing; reject duplicate keys and nonfinite numbers."""
    try:
        if type(raw) is not str or len(raw) > maximum or len(raw.encode("utf-8")) > maximum:
            raise JournalError("input_limit")
        _preflight(raw)
        value: object = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)
        pending = [iter([value])]
        visited = 0
        while pending:
            visited += 1
            if check is not None and visited % 256 == 0:
                check()
            try:
                node = next(pending[-1])
            except StopIteration:
                pending.pop()
                continue
            if isinstance(node, dict):
                for key in node:
                    string_value(key)
                pending.append(iter(node.values()))
            elif isinstance(node, list):
                pending.append(iter(node))
            elif isinstance(node, str):
                if len(node) > 1024 or any(0xD800 <= ord(char) <= 0xDFFF for char in node):
                    raise JournalError("storage_corrupt")
        # The full result repeats bounded evidence per event. The request's
        # 20,000-node limit applies to its components, not this expanded result.
        canonical_bounded(value, maximum, check=check)
        return value
    except (CatalogError, ValueError, RecursionError, UnicodeError) as error:
        if isinstance(error, JournalError):
            raise
        raise JournalError("storage_corrupt") from None


def _require(condition: bool) -> None:
    if not condition:
        raise JournalError("storage_corrupt")


def _same(first: object, second: object) -> bool:
    # Python container equality equates True with1 and must not validate evidence.
    return canonical_json(first) == canonical_json(second)


def _object(value: object, keys: set[str]) -> dict[str, object]:
    result = object_value(value)
    _require(set(result) == keys)
    return result


def _int(value: object, maximum: int = 33000) -> int:
    _require(type(value) is int and 0 <= value <= maximum)
    return cast(int, value)


def _hex(value: object, length: int = 64, prefix: str = "") -> str:
    _require(
        type(value) is str
        and re.fullmatch(prefix + "[0-9a-f]{" + str(length) + "}", value) is not None
    )
    return cast(str, value)


def _paths(value: object) -> list[str]:
    paths = [string_value(item, 256) for item in array_value(value)]
    _require(bool(paths) and paths == sorted(set(paths)))
    return paths


def _indexes(value: object) -> list[int]:
    indexes = [_int(item, 999) for item in array_value(value)]
    _require(indexes == sorted(set(indexes)))
    return indexes


def _proof(value: object, synthetic: bool) -> None:
    if synthetic:
        _require(value is None)
        return
    proof = _object(value, {"version", "extractor", "fields"})
    _require(type(proof["version"]) is int and proof["version"] == 1)
    token_value(proof["extractor"])
    fields = array_value(proof["fields"], 32)
    _require(bool(fields))
    seen: set[tuple[str, str]] = set()
    for item in fields:
        field = _object(item, {"path", "field", "start", "end", "transformation"})
        key = (string_value(field["path"], 256), string_value(field["field"], 128))
        _require(key not in seen)
        seen.add(key)
        start, end = _int(field["start"], 65536), _int(field["end"], 65536)
        _require(start < end and field["transformation"] == "exact_literal")


def _evidence(
    value: object, selection: dict[str, object], context: dict[str, object], profile: str
) -> dict[str, object]:
    evidence = _object(
        value,
        {
            "batch_id",
            "selector",
            "captured_at",
            "mode",
            "evidence_state",
            "scope",
            "scope_semantics",
            "profile",
            "acquisition",
            "extraction_proof",
        },
    )
    bounded_value(evidence)
    _require(all(evidence[key] == item for key, item in selection.items()))
    canonical_timestamp(evidence["captured_at"])
    synthetic = profile == SYNTHETIC_PROFILE
    family = "producer_declared" if synthetic else "verified_local_pinned_bundle"
    _require(
        evidence["profile"] == profile
        and evidence["mode"] == ("synthetic" if synthetic else "pinned")
        and evidence["evidence_state"] == family
    )
    unit = _object(
        evidence["scope"],
        {
            "namespace",
            "kind",
            "language",
            "selector",
            "record_indexes",
        }
        | (
            {"selected", "completed"}
            if synthetic
            else {
                "selected_paths",
                "completed_paths",
                "source_count",
                "result",
                "accepted_count",
                "candidate_count",
                "rejected_count",
            }
        ),
    )
    _require(all(unit[key] == item for key, item in context.items()))
    _require(unit["selector"] == selection["selector"])
    indexes = _indexes(unit["record_indexes"])
    selected_key, completed_key = (
        ("selected", "completed") if synthetic else ("selected_paths", "completed_paths")
    )
    paths = _paths(unit[selected_key])
    _require(_paths(unit[completed_key]) == paths)
    acquisition_keys = {"version", "acquired_at", "captured_at"}
    if synthetic:
        acquisition_keys |= {"outcome"}
    else:
        acquisition_keys |= {
            "source",
            "method",
            "revision",
            "namespace",
            "policy_version",
            "extractor_version",
            "timestamp_convention",
            "artifacts",
            "selected_paths",
            "completed_paths",
            "evidence_status",
            "bundle_sha256",
            "projection_sha256",
        }
    acquisition = _object(evidence["acquisition"], acquisition_keys)
    _require(
        type(acquisition["version"]) is int
        and acquisition["version"] in ((1,) if synthetic else (1, 2))
    )
    canonical_timestamp(acquisition["acquired_at"])
    _require(canonical_timestamp(acquisition["captured_at"]) == evidence["captured_at"])
    if synthetic:
        _require(acquisition["outcome"] == "complete")
        semantics: dict[str, object] = {
            "version": 1,
            "method": "generic_synthetic_capture",
            "policy": "producer_declared_complete",
            "semantics": "capture_scope_v1",
        }
    else:
        _require(bool(indexes) and _int(unit["source_count"], 1000) == len(indexes))
        _require(unit["result"] == "complete_nonempty" and _int(unit["rejected_count"], 1000) == 0)
        _require(
            _int(unit["accepted_count"], 1000) + _int(unit["candidate_count"], 1000) == len(indexes)
        )
        for key in (
            "source",
            "method",
            "namespace",
            "policy_version",
            "extractor_version",
            "timestamp_convention",
        ):
            string_value(acquisition[key], 256)
        _hex(acquisition["revision"], 40)
        for key in ("bundle_sha256", "projection_sha256"):
            _hex(acquisition[key])
        _require(
            acquisition["evidence_status"] == family
            and acquisition["namespace"] == context["namespace"]
        )
        all_paths = _paths(acquisition["selected_paths"])
        _require(
            _paths(acquisition["completed_paths"]) == all_paths and set(paths) <= set(all_paths)
        )
        artifacts = array_value(acquisition["artifacts"], 32)
        artifact_paths = []
        for item in artifacts:
            artifact = _object(item, {"path", "bytes", "sha256", "git_blob_sha1", "acquired_at"})
            artifact_paths.append(string_value(artifact["path"], 256))
            _int(artifact["bytes"], 65536)
            _hex(artifact["sha256"])
            _hex(artifact["git_blob_sha1"], 40)
            canonical_timestamp(artifact["acquired_at"])
        _require(
            len(set(artifact_paths)) == len(artifact_paths) and sorted(artifact_paths) == all_paths
        )
        semantics = {
            key: acquisition[key]
            for key in (
                "source",
                "method",
                "namespace",
                "policy_version",
                "extractor_version",
                "timestamp_convention",
                "evidence_status",
            )
        }
    _require(
        _same(
            evidence["scope_semantics"],
            {
                "family": family,
                "semantics": semantics,
                "paths": paths,
                "context": context,
                "selector": selection["selector"],
            },
        )
    )
    _proof(evidence["extraction_proof"], synthetic)
    return evidence


def validate_pair(
    request: object, result: object, *, check: Callable[[], object] | None = None
) -> tuple[dict[str, object], dict[str, object]]:
    """Strict local consistency, deliberately distinct from original-capture proof."""
    try:
        canonical_bounded(request, 1024 * 1024, check=check)
        canonical_bounded(result, check=check)
        normalized = parse_request(request).to_dict()
        _require(_same(normalized, request))
        payload = _object(
            result,
            {
                "version",
                "result",
                "comparison_id",
                "profile",
                "context",
                "current",
                "history",
                "window",
                "counts",
                "events",
            },
        )
        _require(type(payload["version"]) is int and payload["version"] == 3)
        comparison_id = _hex(payload["comparison_id"], prefix="cmp3:")
        profile = cast(str, normalized["profile"])
        context = object_value(normalized["context"])
        _require(payload["profile"] == profile and payload["context"] == context)
        current = _evidence(
            payload["current"], object_value(normalized["current"]), context, profile
        )
        history = array_value(payload["history"], 32)
        selections = array_value(normalized["history"], 32)
        _require(len(history) == len(selections))
        for item, selection in zip(history, selections, strict=True):
            if check is not None:
                check()
            historical = _evidence(item, object_value(selection), context, profile)
            _require(cast(str, historical["captured_at"]) < cast(str, current["captured_at"]))
            _require(_same(historical["scope_semantics"], current["scope_semantics"]))
        _require(payload["window"] == {"scope": "explicit_selected_capture_units"})
        counts = _object(
            payload["counts"],
            {
                "validated_batches",
                "validated_records",
                "current_selected_records",
                "historical_selected_records",
                "current_selected_references",
                "historical_selected_references",
                "events",
            },
        )
        for value in counts.values():
            _int(value)
        current_indexes = _indexes(object_value(current["scope"])["record_indexes"])
        historical_count = sum(
            len(_indexes(object_value(object_value(item)["scope"])["record_indexes"]))
            for item in history
        )
        _require(counts["validated_batches"] == 1 + len(history))
        _require(
            counts["current_selected_records"] == len(current_indexes)
            and counts["historical_selected_records"] == historical_count
        )
        _require(_int(counts["validated_records"]) >= len(current_indexes) + historical_count)
        _require(_int(counts["current_selected_references"], 1000) <= len(current_indexes))
        _require(_int(counts["historical_selected_references"], 32000) <= historical_count)
        events = array_value(payload["events"], 1000)
        _require(
            counts["events"] == len(events)
            and len(events) <= _int(counts["current_selected_references"])
        )
        _require(
            payload["result"]
            == ("baseline" if not history else "discoveries" if events else "no_discoveries")
        )
        _require(bool(history) or not events)
        event_ids: set[str] = set()
        reference_keys: list[tuple[str, str, str, str, str]] = []
        event_indexes: set[int] = set()
        for item in events:
            if check is not None:
                check()
            event = _object(
                item,
                {
                    "event_id",
                    "type",
                    "reference",
                    "status",
                    "category",
                    "cmt_id",
                    "current_batch_id",
                    "captured_at",
                    "first_observed_in_window_at",
                    "evidence",
                },
            )
            event_id = _hex(event["event_id"], prefix="evt3:")
            _require(event_id not in event_ids)
            event_ids.add(event_id)
            reference = parse_reference(event["reference"])
            _require(
                (reference.namespace, reference.kind, reference.language)
                == (context["namespace"], context["kind"], context["language"])
            )
            reference_keys.append(
                (
                    reference.namespace,
                    reference.kind,
                    reference.external_id,
                    reference.language or "",
                    reference.variant,
                )
            )
            if event["status"] == "candidate":
                _require(
                    event["type"] == "CANDIDATE_REFERENCE_FIRST_OBSERVED"
                    and event["cmt_id"] is None
                    and type(event["category"]) is str
                    and event["category"] in CANDIDATE_CATEGORIES
                )
            else:
                _require(
                    event["status"] == "accepted"
                    and reference.kind == "set"
                    and event["type"] == "SET_REFERENCE_FIRST_OBSERVED"
                    and event["category"] is None
                )
                uuid_value(event["cmt_id"])
            _require(
                event["current_batch_id"] == current["batch_id"]
                and event["captured_at"] == current["captured_at"]
                and event["first_observed_in_window_at"] == current["captured_at"]
            )
            evidence = _object(
                event["evidence"], {"comparison_id", "current_record_indexes", "current", "history"}
            )
            _require(
                evidence["comparison_id"] == comparison_id
                and _same(evidence["current"], current)
                and _same(evidence["history"], history)
            )
            indexes = _indexes(evidence["current_record_indexes"])
            _require(
                bool(indexes)
                and set(indexes) <= set(current_indexes)
                and not event_indexes.intersection(indexes)
            )
            event_indexes.update(indexes)
        _require(reference_keys == sorted(set(reference_keys)))
        return normalized, payload
    except (
        CatalogError,
        ScopedDiscoveryError,
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        RecursionError,
        UnicodeError,
    ) as error:
        if isinstance(error, JournalError):
            raise
        raise JournalError(
            "input_limit" if getattr(error, "category", "") == "input_limit" else "storage_corrupt"
        ) from None
