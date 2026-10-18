"""Explicit multi-revision admission of exactly two review-controlled packages."""

import hashlib
from dataclasses import dataclass
from importlib.resources import files
from typing import cast

from ..catalog.ingestion import ExternalReference, Observation, ReferenceKind
from ..catalog.models import Language
from ..catalog.validation import MAX_BYTES
from . import bundle as v1
from .errors import BundleError
from .extractor import CARD_PATH, SET_PATH

PROFILE = "tcgdex_swsh3_136_r0_r1_v1"
R1_REVISION = "af57972e8f784c2507ab9e573c99bf02ae2e5e42"
APPROVED_BUNDLE_V2_SHA256 = "e3b6ec38358a8fc089e65a365fe2f5566459df441e67c3e8ad51b3b5352b50c0"


@dataclass(frozen=True)
class RegistryEntry:
    """A whole-package digest binds all fields, including policy and acquisition."""

    member: str
    version: int
    revision: str
    sha256: str


APPROVED_PACKAGES = (
    RegistryEntry("r0", 1, v1.REVISION, v1.APPROVED_BUNDLE_SHA256),
    RegistryEntry("r1", 2, R1_REVISION, APPROVED_BUNDLE_V2_SHA256),
)


@dataclass(frozen=True)
class VerifiedBundleV2:
    """A value, never authority; every consumer independently revalidates it."""

    document_json: str


def validate_bundle_v2(document: object) -> VerifiedBundleV2:
    canonical = v1._canonical(document)
    if len(canonical.encode("utf-8")) > MAX_BYTES:
        raise BundleError("input_limit")
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    entry = next((entry for entry in APPROVED_PACKAGES if entry.sha256 == digest), None)
    if entry is None:
        raise BundleError("unapproved_bundle")
    if entry.member == "r0":
        v1.validate_bundle(document)
    return VerifiedBundleV2(canonical)


def bundle_document_v2(bundle: VerifiedBundleV2) -> dict[str, object]:
    if type(bundle) is not VerifiedBundleV2:
        raise BundleError("invalid_shape")
    document = v1._decode(bundle.document_json)
    validate_bundle_v2(document)
    return cast(dict[str, object], document)


def approved_bundle_document_v2(member: str = "r1") -> dict[str, object]:
    if member == "r0":
        return v1.approved_bundle_document()
    if member != "r1":
        raise BundleError("unapproved_bundle")
    try:
        with files(__package__).joinpath("approved_bundle_v2.json").open("rb") as handle:
            raw = handle.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise BundleError("input_limit")
        document = v1._decode(raw.decode("utf-8"))
    except (OSError, UnicodeError):
        raise BundleError("approved_package_io") from None
    return bundle_document_v2(validate_bundle_v2(document))


def observations_v2(bundle: VerifiedBundleV2) -> tuple[Observation, ...]:
    document = bundle_document_v2(bundle)
    if document["version"] == 1:
        return v1.observations(v1.validate_bundle(document))
    result: list[Observation] = []
    for record in cast(list[dict[str, object]], document["projection"]):
        language = cast(Language, record["language"])
        kind = cast(ReferenceKind, record["kind"])
        result.append(
            Observation(
                kind,
                ExternalReference(v1.NAMESPACE, kind, cast(str, record["external_id"]), language),
                cast(str, record["name"]),
                set_reference=(
                    ExternalReference(
                        v1.NAMESPACE, "set", cast(str, record["set_external_id"]), language
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


def capture_evidence_v2(bundle: VerifiedBundleV2) -> dict[str, object]:
    document = bundle_document_v2(bundle)
    if document["version"] == 1:
        return v1.capture_evidence(v1.validate_bundle(document))
    units = [
        {
            "namespace": v1.NAMESPACE,
            "kind": kind,
            "language": language,
            "selector": selector,
            "selected_paths": [path],
            "completed_paths": [path],
            "source_count": 1,
            "result": "complete_nonempty",
        }
        for kind, path, selector in (("set", SET_PATH, "swsh3"), ("card", CARD_PATH, "swsh3-136"))
        for language in ("es", "en")
    ]
    return {
        "version": 2,
        "source": document["repository"],
        "method": "pinned_repository_bundle",
        "revision": document["revision"],
        "namespace": document["namespace"],
        "policy_version": document["policy_version"],
        "extractor_version": document["extractor_version"],
        "acquired_at": document["acquired_at"],
        "captured_at": document["captured_at"],
        "timestamp_convention": document["timestamp_convention"],
        "artifacts": document["artifacts"],
        "selected_paths": [SET_PATH, CARD_PATH, "LICENSE", "README.md"],
        "completed_paths": [SET_PATH, CARD_PATH, "LICENSE", "README.md"],
        "units": units,
        "source_count": 4,
        "result": "complete_nonempty",
        "evidence_status": "verified_local_pinned_bundle",
        "bundle_sha256": APPROVED_BUNDLE_V2_SHA256,
        "projection_sha256": document["projection_sha256"],
    }
