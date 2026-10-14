"""Reviewed-package admission, never a claim of external producer authenticity."""

import hashlib
import json
from dataclasses import dataclass
from importlib.resources import files
from typing import cast

from ..catalog.ingestion import ExternalReference, Observation, ReferenceKind
from ..catalog.models import Language
from ..catalog.validation import MAX_BYTES, CatalogError, validate_structure
from .errors import BundleError
from .extractor import CARD_PATH, EXTRACTOR_VERSION, SET_PATH

POLICY_VERSION = "tcgdex_two_artifacts_es_en_v1"
NAMESPACE = "tcgdex_repository"
REPOSITORY = "tcgdex/cards-database"
REVISION = "4199850a6af49665db0080fa2bb9ef751750a406"
# Review-controlled anchor over the entire canonical minimum package, including
# immutable engineering times, policy, artifact locks, notice and projection.
APPROVED_BUNDLE_SHA256 = "3b43e1a78c117ef1ecb5cf200a4b2fc7e57af8fd29e3fcf29b06f4291ae58085"


@dataclass(frozen=True)
class VerifiedBundle:
    """Immutable value; construction alone grants no authority.

    Every consumer must use the public operations below, which revalidate even
    manually manufactured instances against the review-controlled digest.
    """

    document_json: str


def _canonical(document: object) -> str:
    try:
        validate_structure(document)
        return json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except CatalogError as error:
        raise BundleError(error.category) from None
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise BundleError("invalid_json") from None


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise BundleError("duplicate_key")
        result[key] = value
    return result


def _decode(raw: str) -> object:
    if type(raw) is not str:
        raise BundleError("invalid_shape")
    try:
        if len(raw.encode("utf-8")) > MAX_BYTES:
            raise BundleError("input_limit")
        # Preflight recursive JSON decoding; literal brackets in strings ignored.
        depth = 0
        quoted = escaped = False
        for char in raw:
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char in "[{":
                depth += 1
                if depth > 16:
                    raise BundleError("input_limit")
            elif char in "]}":
                depth -= 1
        result: object = json.loads(raw, object_pairs_hook=_pairs)
    except (UnicodeError, ValueError, RecursionError) as error:
        if isinstance(error, BundleError):
            raise
        raise BundleError("invalid_json") from None
    return result


def validate_bundle(document: object) -> VerifiedBundle:
    """Only the exact reviewed package is admissible, independently of caller claims."""
    canonical = _canonical(document)
    if len(canonical.encode("utf-8")) > MAX_BYTES:
        raise BundleError("input_limit")
    if hashlib.sha256(canonical.encode("utf-8")).hexdigest() != APPROVED_BUNDLE_SHA256:
        raise BundleError("unapproved_bundle")
    return VerifiedBundle(canonical)


def bundle_document(bundle: VerifiedBundle) -> dict[str, object]:
    if type(bundle) is not VerifiedBundle:
        raise BundleError("invalid_shape")
    document = _decode(bundle.document_json)
    validate_bundle(document)
    return cast(dict[str, object], document)


def approved_bundle_document() -> dict[str, object]:
    """Load the installed, review-controlled minimum package; never needs checkout files."""
    try:
        with files(__package__).joinpath("approved_bundle_v1.json").open("rb") as handle:
            data = handle.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise BundleError("input_limit")
        raw = data.decode("utf-8")
    except (OSError, UnicodeError):
        raise BundleError("approved_package_io") from None
    return bundle_document(validate_bundle(_decode(raw)))


def observations(bundle: VerifiedBundle) -> tuple[Observation, ...]:
    document = bundle_document(bundle)
    projection = cast(list[dict[str, object]], document["projection"])
    result: list[Observation] = []
    for record in projection:
        language = cast(Language, record["language"])
        kind: ReferenceKind = "set" if record["kind"] == "set" else "card"
        result.append(
            Observation(
                kind,
                ExternalReference(NAMESPACE, kind, cast(str, record["external_id"]), language),
                cast(str, record["name"]),
                set_reference=(
                    ExternalReference(
                        NAMESPACE, "set", cast(str, record["set_external_id"]), language
                    )
                    if kind == "card"
                    else None
                ),
                card_number=cast(str | None, record["card_number"]),
                release_date=cast(str | None, record["release_date"]),
                captured_at=cast(str, document["captured_at"]),
                provenance="observed",
            )
        )
    return tuple(result)


def capture_evidence(bundle: VerifiedBundle) -> dict[str, object]:
    """Canonical local verification context; importing never changes acquisition time."""
    document = bundle_document(bundle)
    units: list[dict[str, object]] = []
    for kind, path, selector in (("set", SET_PATH, "swsh3"), ("card", CARD_PATH, "swsh3-136")):
        for language in ("es", "en"):
            units.append(
                {
                    "namespace": NAMESPACE,
                    "kind": kind,
                    "language": language,
                    "selector": selector,
                    "selected_paths": [path],
                    "completed_paths": [path],
                    "source_count": 1,
                    "result": "complete_nonempty",
                }
            )
    return {
        "version": 1,
        "source": REPOSITORY,
        "method": "pinned_repository_bundle",
        "revision": REVISION,
        "namespace": NAMESPACE,
        "policy_version": POLICY_VERSION,
        "extractor_version": EXTRACTOR_VERSION,
        "acquired_at": document["acquired_at"],
        "captured_at": document["captured_at"],
        "timestamp_convention": "engineering_completed_utc",
        "artifacts": document["artifacts"],
        "selected_paths": [SET_PATH, CARD_PATH, "LICENSE", "README.md"],
        "completed_paths": [SET_PATH, CARD_PATH, "LICENSE", "README.md"],
        "units": units,
        "source_count": 4,
        "result": "complete_nonempty",
        "evidence_status": "verified_local_pinned_bundle",
        "bundle_sha256": APPROVED_BUNDLE_SHA256,
        "projection_sha256": document["projection_sha256"],
    }
