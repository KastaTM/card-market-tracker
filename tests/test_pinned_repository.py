"""Offline real-package admission and explicitly synthetic parser adversaries."""

import copy
import hashlib
import json
import socket
from dataclasses import replace
from importlib.resources import files
from pathlib import Path
from typing import cast

import pytest

from card_market_tracker.catalog.manifest import parse_manifest
from card_market_tracker.catalog.resolver import reference_dict, resolve
from card_market_tracker.catalog.validation import read_json
from card_market_tracker.pinned_repository import (
    BundleError,
    VerifiedBundle,
    approved_bundle_document,
    bundle_document,
    capture_evidence,
    observations,
    validate_bundle,
)
from card_market_tracker.pinned_repository import bundle as bundle_module
from card_market_tracker.pinned_repository.bundle import APPROVED_BUNDLE_SHA256
from card_market_tracker.pinned_repository.extractor import (
    MAX_SOURCE_BYTES,
    SET_PATH,
    project_sources,
)

# Authored synthetic TS only; no excluded original source data retained here.
SYNTHETIC_SET = b"""import { Set } from '../../interfaces'
import serie from '../Sword & Shield'
const fake: Set = {id:'fake', name:{es:'Sintetico',en:'Synthetic'},
 releaseDate:'2020-01-02', serie:serie, ignored:{bool:true,other:false,n:null}}
export default fake
"""
SYNTHETIC_CARD = b"""import { Card } from '../../../interfaces'
import Set from '../Darkness Ablaze'
const card: Card = {name:{es:'Carta',en:'Card'},set:Set,
 ignored:[{attack:'EXCLUDED_SYNTHETIC_SENTINEL'},null,false,12]}
export default card
"""


def test_reviewed_bundle_exact_minimum_and_resolution() -> None:
    document = approved_bundle_document()
    assert document == read_json(Path("tests/fixtures/pinned_repository_bundle_v1.json"))
    bundle = validate_bundle(document)
    assert bundle_document(bundle) == document
    records = observations(bundle)
    assert [(r.kind, r.reference.language, r.name) for r in records] == [
        ("set", "es", "Oscuridad Incandescente"),
        ("set", "en", "Darkness Ablaze"),
        ("card", "es", "Furret"),
        ("card", "en", "Furret"),
    ]
    assert all(r.provenance == "observed" for r in records)
    assert all(r.reference.namespace == "tcgdex_repository" for r in records)
    assert all(r.reference.variant == "unknown" for r in records)
    assert records[0].release_date == "2020-08-14"
    for card in records[2:]:
        assert card.card_number == "136" and card.reference.external_id == "swsh3-136"
        assert card.set_reference is not None
        assert card.set_reference.external_id == "swsh3"
        assert card.set_reference.language == card.reference.language
        assert card.release_date is None and card.provider_updated_at is None
    result = resolve(records, parse_manifest({"version": 1, "entities": [], "bindings": []}))
    assert [r.category for r in result.records] == [
        "missing_binding",
        "missing_binding",
        "unknown_variant",
        "unknown_variant",
    ]


def test_capture_scope_exact_complete_fixed_times_and_copies() -> None:
    bundle = validate_bundle(approved_bundle_document())
    evidence = capture_evidence(bundle)
    assert evidence["acquired_at"] == evidence["captured_at"] == "2026-10-14T17:53:09.118954Z"
    assert evidence["evidence_status"] == "verified_local_pinned_bundle"
    assert evidence["bundle_sha256"] == APPROVED_BUNDLE_SHA256
    units = cast(list[dict[str, object]], evidence["units"])
    assert [(u["kind"], u["language"], u["source_count"]) for u in units] == [
        ("set", "es", 1),
        ("set", "en", 1),
        ("card", "es", 1),
        ("card", "en", 1),
    ]
    assert all(u["selected_paths"] == u["completed_paths"] for u in units)
    evidence["namespace"] = "forged"
    assert capture_evidence(bundle)["namespace"] == "tcgdex_repository"


def test_explicit_synthetic_curator_bindings_preserve_identity() -> None:
    records = observations(validate_bundle(approved_bundle_document()))
    curator_id = "f9743b79-20e3-4815-98d3-bb06f0c8195f"
    document = {
        "version": 1,
        "entities": [{"cmt_id": curator_id, "kind": "set"}],
        "bindings": [
            {
                "reference": reference_dict(record.reference),
                "cmt_id": curator_id,
                "reason": "Synthetic test curator explicit alias",
            }
            for record in records[:2]
        ],
    }
    before = copy.deepcopy(document)
    result = resolve(records, parse_manifest(document))
    assert result.accepted == 2 and result.candidates == 2 and result.rejected == 0
    assert [row.cmt_id for row in result.records] == [curator_id, curator_id, None, None]
    assert document == before


def test_offline_operations_have_no_socket_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket, "socket", forbidden)
    bundle = validate_bundle(approved_bundle_document())
    assert len(observations(bundle)) == 4
    assert capture_evidence(bundle)["source_count"] == 4
    assert len(project_sources(SYNTHETIC_SET, SYNTHETIC_CARD).projection) == 4


def test_packaged_resource_io_and_size_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(bundle_module, "files", lambda _: tmp_path)
    with pytest.raises(BundleError, match="approved_package_io"):
        approved_bundle_document()
    path = tmp_path / "approved_bundle_v1.json"
    path.write_bytes(b"x" * 1_048_577)
    with pytest.raises(BundleError, match="input_limit"):
        approved_bundle_document()
    path.write_bytes(b"\xff")
    with pytest.raises(BundleError, match="approved_package_io"):
        approved_bundle_document()


def test_mit_notice_and_projection_hash() -> None:
    document = approved_bundle_document()
    notice = files("card_market_tracker.pinned_repository").joinpath("MIT_NOTICE.txt").read_bytes()
    assert hashlib.sha256(notice).hexdigest() == (
        "12e7dd2d018848b9997d0226c4632f01da86ec4bf6ebe0c8b19953d5e5eeb6ff"
    )
    assert notice == Path("tests/fixtures/pinned_repository_MIT_NOTICE.txt").read_bytes()
    assert notice.decode().splitlines() == document["license_lines"]
    projection = json.dumps(
        document["projection"], ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    assert hashlib.sha256(projection).hexdigest() == document["projection_sha256"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("version", True),
        ("version", 2),
        ("repository", "attacker/repo"),
        ("revision", "0" * 40),
        ("namespace", "tcgdex"),
        ("policy_version", "unreviewed"),
        ("extractor_version", "unreviewed"),
        ("captured_at", "2027-01-01T00:00:00Z"),
        ("acquired_at", "2027-01-01T00:00:00Z"),
        ("artifacts", []),
        ("projection", []),
        ("projection_sha256", "0" * 64),
        ("license_lines", []),
        ("license_declaration", "No license"),
        ("provenance", "observed"),
    ],
)
def test_self_declared_metadata_has_no_authority(field: str, value: object) -> None:
    document = approved_bundle_document()
    document[field] = value
    with pytest.raises(BundleError, match="unapproved_bundle"):
        validate_bundle(document)


@pytest.mark.parametrize(
    "field,value",
    [
        ("name", "FORGED_SYNTHETIC"),
        ("language", "fr"),
        ("kind", "sealed"),
        ("external_id", "fake"),
        ("card_number", 136),
        ("release_date", "2020-08-15"),
        ("variant", "normal"),
        ("updated", "2020-01-01T00:00:00Z"),
    ],
)
def test_forged_projection_and_recomputed_hash_rejected(field: str, value: object) -> None:
    document = approved_bundle_document()
    records = cast(list[dict[str, object]], document["projection"])
    records[2][field] = value
    document["projection_sha256"] = hashlib.sha256(json.dumps(records).encode()).hexdigest()
    with pytest.raises(BundleError, match="unapproved_bundle"):
        validate_bundle(document)


@pytest.mark.parametrize("operation", [bundle_document, observations, capture_evidence])
def test_manually_constructed_verified_object_revalidated(operation: object) -> None:
    bundle = validate_bundle(approved_bundle_document())
    forged = replace(bundle, document_json=bundle.document_json.replace("Furret", "FORGED"))
    function = cast(object, operation)
    assert callable(function)
    with pytest.raises(BundleError, match="unapproved_bundle"):
        function(forged)


@pytest.mark.parametrize(
    "raw,category",
    [
        ('{"version":1,"version":1}', "duplicate_key"),
        ("{", "invalid_json"),
        ("[" * 17, "input_limit"),
        ('"' + "x" * 1_048_576 + '"', "input_limit"),
        ('"\\ud800"', "invalid_json"),
        ("NaN", "invalid_json"),
    ],
    ids=["duplicate", "malformed", "depth", "bytes", "surrogate", "nonfinite"],
)
def test_forged_serialized_objects_bounded(raw: str, category: str) -> None:
    with pytest.raises(BundleError, match=category):
        bundle_document(VerifiedBundle(raw))


def test_invalid_public_objects() -> None:
    with pytest.raises(BundleError, match="invalid_shape"):
        bundle_document(cast(VerifiedBundle, object()))
    with pytest.raises(BundleError, match="invalid_shape"):
        bundle_document(VerifiedBundle(cast(str, 3)))
    with pytest.raises(BundleError, match="invalid_shape"):
        validate_bundle({"value": object()})
    with pytest.raises(BundleError, match="input_limit"):
        validate_bundle({"value": "x" * 1025})
    with pytest.raises(BundleError, match="invalid_json"):
        validate_bundle({"value": 10**10000})


def test_parser_exact_structure_byte_offsets_and_leading_zero_number() -> None:
    extracted = project_sources(SYNTHETIC_SET, SYNTHETIC_CARD, card_path=SET_PATH[:-3] + "/001.ts")
    assert len(extracted.projection) == 4
    assert extracted.projection[2]["external_id"] == "fake-001"
    assert extracted.projection[2]["card_number"] == "001"
    assert "EXCLUDED_SYNTHETIC_SENTINEL" not in repr(extracted)
    fields = {(span.path, span.field): span for span in extracted.fields}
    span = fields[(SET_PATH, "name.en")]
    assert SYNTHETIC_SET[span.start : span.end] == b"'Synthetic'"
    span = fields[(SET_PATH[:-3] + "/001.ts", "$parent_import")]
    assert SYNTHETIC_CARD[span.start : span.end] == b"'../Darkness Ablaze'"


def test_parser_comments_semicolons_unicode_escapes_and_null_date() -> None:
    source_set = SYNTHETIC_SET.replace(b"import {", b"/*synthetic*/ import {")
    source_set = source_set.replace(b"'Synthetic'", b"'Synthe\\u0074ic\\\\\\\"\\'\\n\\r\\t\\b\\f'")
    # Escaped control characters in approved names are deliberately invalid.
    with pytest.raises(BundleError, match="invalid_field"):
        project_sources(source_set, SYNTHETIC_CARD)
    source_set = SYNTHETIC_SET.replace(b"'Synthetic'", b"'Synthe\\u0074ic'")
    source_set = source_set.replace(b"'2020-01-02'", b"null") + b"// synthetic comment"
    assert project_sources(source_set, SYNTHETIC_CARD).projection[0]["release_date"] is None
    source_set = source_set.replace(b"'../../interfaces'", b"'../../interfaces';")
    source_set = source_set.replace(b"'../Sword & Shield'", b"'../Sword & Shield';")
    source_set = source_set.replace(b"export default fake", b";export default fake;")
    assert project_sources(source_set, SYNTHETIC_CARD).projection[1]["name"] == "Synthetic"


@pytest.mark.parametrize(
    "old,new,category",
    [
        (b"id:'fake'", b"id:'fake',id:'evil'", "duplicate_field"),
        (b"es:'Sintetico',", b"fr:'Sintetico',", "missing_translation"),
        (b"name:{es:'Sintetico',en:'Synthetic'}", b"name:null", "missing_translation"),
        (b"releaseDate:'2020-01-02',", b"", "missing_field"),
        (b"'2020-01-02'", b"'2020-02-30'", "invalid_field"),
        (b"'../../interfaces'", b"'../../evil'", "invalid_import"),
        (b"'../Sword & Shield'", b"'../evil'", "invalid_import"),
        (b"id:'fake'", b"id:process.env.NAME", "unsupported_syntax"),
        (b"id:'fake'", b"id:evil()", "unsupported_syntax"),
        (b"id:'fake'", b"...evil", "unsupported_syntax"),
        (b"id:'fake'", b"[evil]:'fake'", "unsupported_syntax"),
        (b"const fake", b"let fake", "unsupported_syntax"),
        (b"export default fake", b"export default evil", "unsupported_syntax"),
        (b"ignored:", b"'ignored':", "success"),
        (b"id:'fake'", b"id:12", "invalid_field"),
        (b"id:'fake'", b"id:'fake\\x41'", "unsupported_syntax"),
        (b"id:'fake'", b"id:'fake\\uXX12'", "unsupported_syntax"),
        (b"id:'fake'", b"id:'fake\\ud800'", "invalid_encoding"),
        (b"id:'fake'", b"id:'fake\n'", "unsupported_syntax"),
        (b"id:'fake'", b"id:'" + b"a" * 4097 + b"'", "input_limit"),
        (b"n:null", b"n:12345678901", "input_limit"),
        (b"ignored:{bool:true,other:false,n:null}", b"ignored:[]", "success"),
        (b"ignored:{bool:true,other:false,n:null}", b"ignored:{}", "success"),
    ],
)
def test_synthetic_parser_adversarial(old: bytes, new: bytes, category: str) -> None:
    modified = SYNTHETIC_SET.replace(old, new)
    assert modified != SYNTHETIC_SET
    if category == "success":
        assert len(project_sources(modified, SYNTHETIC_CARD).projection) == 4
    else:
        with pytest.raises(BundleError, match=category):
            project_sources(modified, SYNTHETIC_CARD)


@pytest.mark.parametrize("suffix", [b"evil()", b"import Evil from 'evil'", b"/*", b"'"])
def test_parser_trailing_executable_or_incomplete_source_rejected(suffix: bytes) -> None:
    with pytest.raises(BundleError, match="unsupported_syntax"):
        project_sources(SYNTHETIC_SET + suffix, SYNTHETIC_CARD)


@pytest.mark.parametrize(
    "source,category",
    [
        (b"\xff", "invalid_encoding"),
        (b"x" * (MAX_SOURCE_BYTES + 1), "input_limit"),
        (b"", "unsupported_syntax"),
        (SYNTHETIC_SET + b"'\\", "unsupported_syntax"),
        (SYNTHETIC_SET + b"'", "unsupported_syntax"),
        (SYNTHETIC_SET.replace(b"n:null", b"n:" + b"[" * 17 + b"]" * 17), "input_limit"),
        (SYNTHETIC_SET.replace(b"n:null", b"n:[" + b"0," * 6000 + b"]"), "input_limit"),
    ],
    ids=["utf8", "bytes", "empty", "escape_eof", "quote_eof", "depth", "tokens"],
)
def test_parser_encoding_work_limits_and_incomplete_input(source: bytes, category: str) -> None:
    with pytest.raises(BundleError, match=category):
        project_sources(source, SYNTHETIC_CARD)


def test_parser_import_relation_and_path_rejections() -> None:
    for path in ("evil.ts", SET_PATH[:-3] + "/../001.ts", SET_PATH[:-3] + "/001.js"):
        with pytest.raises(BundleError, match="invalid_selection"):
            project_sources(SYNTHETIC_SET, SYNTHETIC_CARD, card_path=path)
    for source in (
        SYNTHETIC_CARD.replace(b"set:Set,", b"set:null,"),
        SYNTHETIC_CARD.replace(b"set:Set,", b""),
    ):
        with pytest.raises(BundleError, match="invalid_relation"):
            project_sources(SYNTHETIC_SET, source)
    with pytest.raises(BundleError, match="invalid_import"):
        project_sources(SYNTHETIC_SET, SYNTHETIC_CARD.replace(b"../Darkness Ablaze", b"../evil"))
    with pytest.raises(BundleError, match="invalid_shape"):
        project_sources(cast(bytes, "wrong"), SYNTHETIC_CARD)
    with pytest.raises(BundleError, match="invalid_shape"):
        project_sources(
            SYNTHETIC_SET.split(b"= {")[0] + b"= []; export default fake", SYNTHETIC_CARD
        )


def test_mutated_artifact_lock_rejected() -> None:
    for field in ("path", "git_blob_sha1", "sha256", "bytes", "acquired_at"):
        document = copy.deepcopy(approved_bundle_document())
        artifacts = cast(list[dict[str, object]], document["artifacts"])
        artifacts[0][field] = "forged"
        with pytest.raises(BundleError, match="unapproved_bundle"):
            validate_bundle(document)


@pytest.mark.parametrize(
    "old,new",
    [
        (b"import {", b"'import' {"),
        (b"import {", b"import '{'"),
        (b" } from", b" '}' from"),
        (b" } from", b" } 'from'"),
        (b"\nimport ", b"\n'import' "),
        (b"const ", b"'const' "),
        (b"fake: Set", b"fake ':' Set"),
        (b"card: Card", b"card ':' Card"),
        (b": Set =", b": 'Set' ="),
        (b": Card =", b": 'Card' ="),
        (b" = {", b" '=' {"),
        (b" = {", b" = '{'"),
        (b"name:", b"name':'"),
        (b", name:", b" ',' name:"),
        (b",en:", b" ',' en:"),
        (b"'Card'}", b"'Card' '}'"),
        (b"'Synthetic'}", b"'Synthetic' '}'"),
        (b"ignored:[", b"ignored:'['"),
        (b"false,12]", b"false,12 ']'"),
        (b"\nexport default", b"\n'export' default"),
        (b"export default", b"export 'default'"),
        (b"default fake", b"default 'fake'"),
        (b"default card", b"default 'card'"),
        (b"{ Set }", b"{ 'Set' }"),
        (b"{ Card }", b"{ 'Card' }"),
        (b"import serie from", b"import 'serie' from"),
        (b"import Set from", b"import 'Set' from"),
    ],
)
def test_quoted_grammar_tokens_never_satisfy_syntax(old: bytes, new: bytes) -> None:
    # Each attack quotes a keyword, identifier or delimiter in its grammar role.
    # Some roles occur in only one fixture; use that fixture explicitly.
    source = SYNTHETIC_SET if old in SYNTHETIC_SET else SYNTHETIC_CARD
    source_kind = "set" if source == SYNTHETIC_SET else "card"
    assert old in source
    modified = source.replace(old, new, 1)
    with pytest.raises(BundleError, match="unsupported_syntax"):
        project_sources(
            modified if source_kind == "set" else SYNTHETIC_SET,
            modified if source_kind == "card" else SYNTHETIC_CARD,
        )


@pytest.mark.parametrize("location", ["interface", "parent", "object", "export"])
def test_quoted_optional_semicolon_never_satisfies_syntax(location: str) -> None:
    fragments = {
        "interface": (b"'../../interfaces'", b"'../../interfaces' ';'"),
        "parent": (b"'../Sword & Shield'", b"'../Sword & Shield' ';'"),
        "object": (b"\nexport default", b" ';'\nexport default"),
        "export": (b"export default fake", b"export default fake ';'"),
    }
    old, new = fragments[location]
    with pytest.raises(BundleError, match="unsupported_syntax"):
        project_sources(SYNTHETIC_SET.replace(old, new), SYNTHETIC_CARD)


def test_strings_matching_grammar_tokens_remain_literal_values() -> None:
    for value in (b"'{'", b"'['", b"'}'", b"']'", b"';'", b"'import'", b"'true'", b"'null'"):
        source = SYNTHETIC_CARD.replace(b"'EXCLUDED_SYNTHETIC_SENTINEL'", value)
        assert len(project_sources(SYNTHETIC_SET, source).projection) == 4
