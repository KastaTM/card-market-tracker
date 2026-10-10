# Engineering Completion Report — P3a Observation Persistence

Phase: P3a, contract v1, 2026-10-10 Europe/Madrid.
Proposed status: implementation candidate; mandatory exact-candidate evidence
pending. Only the Orchestrator accepts/closes. No merge is authorized or performed.
Repository: https://github.com/KastaTM/card-market-tracker.
Branch: `feat/p3a-observation-persistence`; base
`c6e66a2aba469d02f0ca63fde3b81ecc5eea41bc`, base tree
`a9717922736a6220d3ff05293bec4cb222644269`.
PR/head/tree and postpublication evidence belong to the external delivery ledger.

## Implementation and authority

The full contract and brief are archived, with explicit [ownership](P3A_OWNERSHIP.md).
The Orchestrator's P1a closure and P3a opening are attributed in roadmap/P1a report;
historical statements remain historical. P2 and P6a/retail Discovery remain blocked.
The observed root runtime identifies a GPT-6 based Codex agent; exact backend and
reasoning are unverified. Three author/supplementary-review delegations requested
`gpt-6.1-sol/high` and were accepted by the tool; actual backend is not introspectable.
QA and final REVIEWER must be separate independent agents on committed SHA.

## Architecture, database and contracts

[ADR-0004](../adr/0004-offline-observation-persistence.md),
[input v1](../data-contracts/PERSISTENCE_V1.md) and
[storage v1](../data-contracts/STORAGE_V1.md) precede dependent implementation.
Python3.13 stdlib SQLite preserves curated UUID parent projections and immutable
normalized/resolved accepted/candidate snapshots, with safe rejected summaries.
Initial schema1 only; DELETE/FULL, explicit atomic SQL transactions, foreign keys,
safe replay fingerprints, bounded reads/locks, verified new-destination backup/restore.
Domain/resolver stay independent; `catalog` remains read-only. New CLI:
`persist`, `observations`, `db init|verify|backup|restore`.

## Security, observability and operations

Synthetic-only writes, explicit capture/UTC, revalidation of manually constructed
values, parameterized SQL, bounded JSON and safe paths precede retention.
Allowlisted `persistence.completed` logs separate processing and committed counts;
errors use null counts and no raw messages/tokens/paths. Scope excludes real feeds,
price/stock, promotion, analytics and service operation. The
[runbook](../runbooks/OBSERVATION_STORAGE.md), threat model and risks describe
controls and limits; TD001/002 preserved, TD003 trusted directories and TD004 growth
record deliberate limits. Process drills, simulated IO and QEMU cannot certify
physical Pi power loss or authenticated source rights.

## Tests and gates — interim snapshot

Working-tree tests are provisional: 410 passed/1 Windows symlink-privilege skip,
97.54% lines/94.14% branches. Scoped Ruff/mypy and separate-process storage smoke
passed. Authors/supplementary SEC/SRE are distinct from final independent review.
These results are not presented as exact-reviewed-SHA gate PASS.

Mandatory frozen install/lock, Ruff format/check, strict mypy, pytest/coverage,
build/wheel, audit/secret scan, ARQ/DB/SEC/SRE/docs reviews, Compose, AMD64, ARM64,
four-job CI and independent QA/REVIEWER are **FAIL: final committed-candidate
execution/verification pending**. AC-O01–AC-O15 final matrix and exact evidence
will be filled after candidate checks/reviews. This interim report does not
recommend readiness.
