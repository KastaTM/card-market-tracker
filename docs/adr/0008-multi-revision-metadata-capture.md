# ADR-0008: Exact-pair metadata admission and profiled Discovery v3

## Status

Adopted for the P1c implementation candidate, 2026-10-18. Owners: Engineering
Lead, ARQ / DB-OWNER and BE / DISCOVERY. Independent candidate reviews and
Orchestrator phase acceptance are separate gates. Only the Orchestrator closes
P1c. Authority: [P1c contract](../phases/P1C_MULTI_REVISION_METADATA_CAPTURE_CONTRACT.md).

## Context

R0 and R1 are two authorized revisions of the same TCGdex repository, acquired
at different original capture instants. Their four authorized blobs and minimum
projections are equal. P1b accepts exactly R0; P4b compares acquisition-sensitive
scope semantics. Broadening those accepted interfaces or removing revision,
artifact locks and clocks from fingerprints would weaken historical evidence.

The requirement is to retain both captures in the existing five-table SQLite
schema2 and compare their four units under one explicitly reviewed policy. The
expected real result is `no_discoveries`, zero events. Positive novelty evidence
continues to use synthetic producer declarations.

## Decision

Add [bundle v2](../data-contracts/PINNED_REPOSITORY_BUNDLE_V2.md), an explicit
entrypoint with a code-controlled registry of exactly the complete R0 and R1
package digests. A whole-package anchor binds revision, allowlist policy,
extractor, projection, license and immutable acquisition times. Inputs cannot
provide registry authority. Existing bundle v1 code and R0 resource are unchanged.

`persist_bundle_v2` reconstructs observations and frozen resolution before
opening storage. R0 uses its exact original envelope/scope version1, preserving
replay with `persist_bundle`; R1 uses envelope/scope version2. Existing pinned
mode and `verified_local_pinned_bundle` evidence state preserve schema2 inventory
and constraints. Verify, query, replay and backup/restore dispatch by retained
envelope version into the same strict admission/reconstruction path. Historical
scope, manifest, rows and fingerprints are never rewritten.

Add [DISCOVERY_V3](../data-contracts/DISCOVERY_V3.md). Storage verifies every
selected complete batch in one read-only/query-only connection and explicit
transaction, then issues a content-bound profile receipt. The reviewed profile
`tcgdex_swsh3_136_r0_r1_v1` requires actual registry membership. The separate
`synthetic_multi_revision_v1` profile requires synthetic/producer_declared
evidence. A request only selects a profile; it cannot establish membership.

The pure comparator imports no provider or SQLite. Profile authorization permits
per-capture revision, digest and clock differences within the exact pair while
retaining matching repository, family, policy, namespace, kind, language,
selector and selected paths. Complete acquisition evidence remains in output
and comparison/event identities. Profile compatibility is distinct from replay
equality. Original capture time alone orders history.

V1 remains synthetic-only. V2 retains R0-only pinned admission and explicitly
rejects R1 even on baseline. Versioned `cmp3:` / `evt3:` payloads include profile
and capture evidence; cmp1/evt1/cmp2/evt2 inputs and outputs remain unchanged.

## Alternatives

Accepting any MIT commit, trusting a payload registry, producer provenance or a
constructed Python value cannot prove review of an exact acquisition. Deleting
revision/time/artifacts from existing hashes conflates comparability and replay.
Wrapping R0 in a new envelope breaks historical replay. Independent scope/row
queries can combine different committed states. A new table, migration, event
store or generic upstream collector adds capability outside this phase.

## Consequences

Runtime, tests and CI import only packaged minimum data and run offline. Bounds,
2-second default / 5-second maximum storage budgets, atomic writes and existing
backup requirements remain. Whole-database verification may exhaust those
budgets as history grows. Private receipts express an application trust boundary,
not authentication against arbitrary code running inside the process.

The real pair demonstrates comparison across two repository revisions with
unchanged selected content. It establishes no new product, metadata change,
release, commercial transition, source health or global absence. Engineering
timestamps are local producer declarations supported by the acquisition ledger,
not provider-authenticated timestamps. No native Pi or power-loss certification
is implied by ARM64/QEMU. TD-001 through TD-005 remain open.

## Revisit conditions

A third package/revision, different corpus or policy, authenticated producers,
larger windows, continuous acquisition, schema/event persistence or retail
behavior requires a new Orchestrator decision and explicit contract. No input
parameter extends this registry or these profiles.

The v3 storage profile receipt additionally binds a reviewed extraction_proof:
version1/extractor/eight exact UTF8 field spans (path, field, start, end,
exact_literal transformation). Same approved blobs give identical R0/R1 proof.
`extraction_evidence_v2` independently revalidates the exact package before issuing
this code-controlled descriptor. V3 outputs/hashes include it; synthetic proof
is explicitly null. Neither historical envelopes/source package hashes nor v1/v2
outputs/fingerprints change. See Discovery v3 for strict generic proof bounds.
