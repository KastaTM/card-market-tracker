# Pinned repository bundle v1

P1b source-only boundary. Namespace is fixed `tcgdex_repository`; repository is
`tcgdex/cards-database`, revision `4199850a6af49665db0080fa2bb9ef751750a406`.
Runtime is offline and uses the installed reviewed package. Source originals are
engineering-only transient input; they are never installed or persisted.

The strict reviewed document is [the minimum fixture](../../tests/fixtures/pinned_repository_bundle_v1.json).
Its complete key inventory is `version`, `repository`, `revision`, `namespace`,
`policy_version`, `extractor_version`, `acquired_at`, `captured_at`, `artifacts`,
`projection`, `projection_sha256`, `license_lines`, `license_declaration`,
`timestamp_convention`. Version is integer 1. Policy is
`tcgdex_two_artifacts_es_en_v1`; extractor is `pinned_ts_literals_v1`.
Any omitted/additional key or altered value fails equality with the reviewed lock.

Each artifact has exact `path`, `git_blob_sha1`, `sha256`, integer `bytes` and
UTC `acquired_at`. Four artifacts are ordered set, card, LICENSE, README. Git
SHA-1 hashes `blob <size>\0<bytes>`; content SHA-256 hashes bytes. The artifact
locks identify reviewed original bytes; runtime does not fetch or reconstruct
them. The whole-package canonical SHA-256 is embedded in reviewed Python code.

Each of four projections has exact keys `kind`, `language`, `external_id`,
`name`, `set_external_id`, `card_number`, `release_date`. Order is set ES, set EN,
card ES, card EN. Exact language literals are required. Set relation/number nulls
are exact; card release date is null. Card number comes from the textual filename
stem, never integer conversion. Card ID is `${set.id}-${stem}`. Names never match
identity. Release date is a calendar declaration, not a regional launch instant.
Provider update and all availability/finish evidence are excluded.

`license_lines` preserves the complete MIT notice lines; the byte-identical
`MIT_NOTICE.txt` also accompanies package and fixture. `license_declaration` is
one short database-license sentence. The README's other contents are excluded.
The notice grants no separate trademark/artwork/third-party rights.

`acquired_at` is aggregate engineering acquisition completion (latest of the four
artifacts); `captured_at` is the same declared engineering instant. Both are fixed
UTC `2026-10-14T17:53:09.118954Z`. Per-artifact acquisition remains separate.
Import/persistence time belongs to storage and never changes these values.

Canonical JSON uses UTF-8, sorted keys, `ensure_ascii=False`, comma/colon separators
without spaces. Projection hash covers only the ordered projection. The whole
package digest covers everything above. The exact document and digest are
review-controlled within the distribution. A caller recomputing hashes or
asserting `observed` does not gain authority.

Public API: `validate_bundle(document)->VerifiedBundle`,
`bundle_document(bundle)->dict`, `observations(bundle)->tuple[Observation,...]`,
`capture_evidence(bundle)->dict`, `approved_bundle_document()->dict`.
VerifiedBundle is frozen, carrying canonical JSON. Every consumer revalidates
against the code-controlled digest, including manually constructed Python values.
Returned dictionaries are independent copies. A host administrator can modify
installed code; host integrity is outside this local equality boundary.

All observations are `observed`, use the fixed namespace and exact ES/EN contexts,
and have unknown variant. Card set references use the same namespace/language and
unknown variant. No CMT UUID or curated binding is created. Storage must revalidate
the package independently; PERSISTENCE_V1 remains synthetic-only.

Capture evidence includes method `pinned_repository_bundle`, all four selected
and completed paths, artifact locks, policy/extractor, both fixed times, timestamp
convention, bundle/projection hashes, source count four, result
`complete_nonempty`, and evidence `verified_local_pinned_bundle`. Four disjoint
units each have namespace/kind/language/exact external-ID selector, selected and
completed artifact path, source count one and `complete_nonempty`. Linking is
explicit through card references; units do not mix languages/kinds. Resolution
acceptance/candidates/rejections are separate storage outcomes. Missing artifact,
translation, parser/digest failure or unauthorized selection fails before admission;
it cannot create a complete empty capture. Generic synthetic capture tests may
exercise empty/partial/rejected states under CAPTURE_SCOPE_V1; this package always
contains four source records. Complete selection proves neither catalog coverage
nor product absence. Legacy/producer-attested evidence stays distinct.

Bounds: package JSON 1 MiB, depth 16, nodes 20,000, scalar/key length 1,024,
same strict shared JSON validation, duplicate keys forbidden. License is represented
as lines to respect scalar bounds. TS input is at most 65,536 bytes per artifact,
10,000 tokens, nesting 16 and transient string 4,096. The restricted grammar accepts
the exact import/type/const/export wrapper, literal objects/arrays, integer/string/
boolean/null values and the explicitly declared relation identifier only. It rejects
duplicate properties, unsupported expressions, spread/computed keys, executable
statements, extra imports, unknown escapes and incomplete syntax. Comments and
optional semicolons carry no authority. The structural field spans are UTF-8
half-open offsets, including parent import and root relation. No upstream code or
import runs and no URL/path from payload is followed.

BundleError carries fixed safe categories: `invalid_shape`, `input_limit`,
`invalid_encoding`, `unsupported_syntax`, `invalid_import`, `duplicate_field`,
`invalid_selection`, `missing_field`, `missing_translation`, `invalid_relation`,
`invalid_field`, `duplicate_key`, `invalid_json`, `unapproved_bundle`,
`approved_package_io`. Errors never carry original values or paths.

See [field evidence and rights](../sources/P1B_FIELD_LEDGER.md) and the
[opening contract](../phases/P1B_PINNED_METADATA_INGESTION_CONTRACT.md). Local package
verification establishes reviewed-byte equivalence, not physical truth, independent
producer authentication, provider availability or deployed REST revision.
