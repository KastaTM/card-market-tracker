# Exact-pair pinned repository bundle v2

Authority: [P1c contract](../phases/P1C_MULTI_REVISION_METADATA_CAPTURE_CONTRACT.md)
and [ADR-0008](../adr/0008-multi-revision-metadata-capture.md). This explicit
entrypoint extends admission without changing [bundle v1](PINNED_REPOSITORY_BUNDLE_V1.md).

## Registry and package identity

`pinned_repository.bundle_v2.APPROVED_PACKAGES` is an immutable tuple in reviewed
code. It contains exactly these whole-package canonical SHA256 anchors:

| Member | Document version | Repository revision | Canonical package SHA256 |
| --- | --- | --- | --- |
| r0 | 1 | `4199850a6af49665db0080fa2bb9ef751750a406` | `3b43e1a78c117ef1ecb5cf200a4b2fc7e57af8fd29e3fcf29b06f4291ae58085` |
| r1 | 2 | `af57972e8f784c2507ab9e573c99bf02ae2e5e42` | `e3b6ec38358a8fc089e65a365fe2f5566459df441e67c3e8ad51b3b5352b50c0` |

Canonicalization is the unchanged v1 package canonicalization: UTF-8 JSON,
unescaped Unicode, sorted keys and compact separators after strict structural
validation. The digest binds every package field; a caller-recomputed hash or
registry supplied in input provides no authority. R0 also passes the unchanged
v1 validator. Any extra/omitted field, altered clock, third revision or package
fails `unapproved_bundle` before DB opening.

R1 retains repository, revision, namespace, policy/extractor, acquired_at,
captured_at, four artifact locks, projection/projection_sha256, complete MIT
license_lines, license_declaration and timestamp_convention. Artifact locks have
path, Git blob SHA1, content SHA256, byte size and original acquired_at. Four
projections contain only kind, language, external_id, name, set_external_id,
card_number and release_date. Their exact field values are anchored by the
complete package digest. R1 projection SHA256 equals R0:
`53100248a987378fb3ca2273b7ec219747b876b515f57087faf6becdd0caa479`.

Authorized paths remain the set TS file, card136 TS file, LICENSE and README
listed in P1c. Full TS/README originals are temporary acquisition material;
runtime packages retain only the minimum projection, locks and permitted notice.
Extraction spans and independent contrast/disposition are documented in the
phase field/acquisition ledger. No upstream source executes at admission.

## Python API and bounds

`validate_bundle_v2(document)` returns `VerifiedBundleV2(document_json)`.
`bundle_document_v2`, `observations_v2` and `capture_evidence_v2` independently
revalidate that value. A forged constructor, subclass or replaced document
cannot grant admission. `approved_bundle_document_v2(member="r1")` reads the
installed resource; `member="r0"` returns the original v1 resource unchanged.
Other members fail. No path, URL or registry input is accepted by these APIs.

Package limits remain 1MiB, depth16, nodes20000, scalar/key length1024, strict
UTF-8/JSON and no duplicate keys. Direct-object validation and decoding preserve
the existing bounds. Parser limits and non-executing extraction grammar remain
the P1b contract. Safe `BundleError` categories remain v1 categories; no source
text or arbitrary exceptions are returned.

## Persistence and reconstruction

`persistence.capture.persist_bundle_v2(path,bundle,batch_id,manifest,timeout=2.0)`
accepts raw documents, revalidated v2 values and revalidated original v1 values.
It resolves against the explicit curated manifest and freezes all four records,
units, counters and resolver context. Namespace remains `tcgdex_repository`;
variants remain unknown, UUIDs/bindings stay curated, cards remain candidates.
There is no identity allocation or promotion.

R0 retains its exact envelope/scope version1 and replay identity, including when
imported through v2. R1 uses envelope/scope version2 with the same field layout,
mode pinned and evidence_state verified_local_pinned_bundle. Scope includes
original acquisition/capture, revision, artifacts, bundle/projection hashes,
policy/extractor, selected/completed paths and four disjoint ES/EN set/card
units with original indexes and resolution counts. SQLite remains schema2 with
the same five tables and constraints; no migration is introduced.

`_check_capture` dispatches by exact retained envelope version and reconstructs
the complete package, manifest, parent closure, resolution, scope, snapshot,
counts and hashes. Query, source query, verify and backup/restore reuse this
boundary. Replay requires identical package/evidence/context/snapshot under the
same token and performs no writes. Any difference conflicts atomically.
Insertion time remains separate and reimport never redates capture. R0 capture
is `2026-10-14T17:53:09.118954Z`; R1 capture is
`2026-10-18T12:18:50.379756Z`. These are engineering declarations, not external
timestamp authentication.

`persist_bundle`/bundle v1 still reject R1. PERSISTENCE_V1 remains synthetic-only.
Discovery v2 rejects R1 even without history. The new profile applies only in
the explicit [Discovery v3](DISCOVERY_V3.md) route.

## CLI and meaning

`cmt bundle-v2 verify --input PACKAGE_JSON` returns a version2 admission summary.
`cmt bundle-v2 import --input PACKAGE_JSON --manifest MANIFEST_JSON --db PATH
--batch-id UUID` returns a version2 persistence summary. Verification, replay or
all-accepted import exits0; a stored mixed result exits3. Expected candidates
can produce mixed without a failed transaction. Invalid input/admission exits2;
local IO/storage execution exits1. Error summaries have version2, result error,
fixed error_category, counts null and committed null. Logs identify bundle_v2_verify/import
with correlation, duration and counts, without payloads, names, paths or tokens.

Verified local pinned bundle means equivalence to the two reviewed minimum
packages. It does not authenticate the provider, extend MIT to images/trademarks,
prove full catalog coverage or establish current source availability.

The v3 storage profile receipt additionally binds a reviewed extraction_proof:
version1/extractor/eight exact UTF8 field spans (path, field, start, end,
exact_literal transformation). Same approved blobs give identical R0/R1 proof.
`extraction_evidence_v2` independently revalidates the exact package before issuing
this code-controlled descriptor. V3 outputs/hashes include it; synthetic proof
is explicitly null. Neither historical envelopes/source package hashes nor v1/v2
outputs/fingerprints change. See Discovery v3 for strict generic proof bounds.
