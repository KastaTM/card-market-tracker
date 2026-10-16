# ADR-0006: Reviewed pinned capture admission and explicit SQLite v2

Status: design checkpoint for implementation; independent final review pending.
Date: 2026-10-14. Owners: ARQ / DB-OWNER and INTEGRATIONS / DATA.
Phase acceptance belongs only to the Orchestrator.

The new real path independently reparses the immutable bundle against a reviewed,
packaged policy lock before resolution or writing. Observed provenance alone
confers no authority. PERSISTENCE_V1 retains its synthetic-only guard. UUIDs and
bindings remain curated; card variant unknown remains a candidate.

Schema2 preserves entities and batch columns and widens record provenance to
synthetic/observed. One immutable capture envelope per batch stores canonical,
bounded scope/evidence, manifest context, source bundle and its equivalence hash.
Legacy batches retain original rows, capture times and fingerprints, and receive
legacy_unverified context with no fabricated scope. The old unscoped synthetic
API likewise makes no completeness claim. New explicit synthetic capture scope
supports exact empty, partial and rejected tests without inventing real empties.

Read operations recognize exact v1 or v2 inventories and never migrate. New
initialization creates v2; opening v1 for initialization leaves v1. Migration
requires BEGIN EXCLUSIVE, schema/integrity preflight, an exclusively reserved
backup, stable DELETE-journal byte copy with fsync and reopened verification,
then transactional record-table/version rebuild and legacy capture backfill.
Any exception rolls back all DDL and version publication. Backup and destination
are never overwritten. A held exclusive transaction is the required exception
to ordinary SQLite backup API usage: it makes the source main file stable and
avoids deadlocking sqlite3.backup against its own transaction. General backup
and restore continue to use SQLite backup API and verify/reopen the destination.

Capture reads obtain metadata, evidence and complete ordered rows in one bounded
read transaction. Verification reconstructs authorized new capture admission and
compares frozen rows/context, not current bindings. P4a explicitly rejects any
selected observed/mixed batch, without filtering records. Scope evidences exact
local validation, not catalog completeness or independent producer authenticity.

Alternatives rejected: automatic migrations, provenance string authorization,
source-shaped domain models, new ORM/dependencies, recomputing v1 fingerprints,
or synthetic empty scope inferred from manifest bindings. Revisit broader real
sources, independent signatures, catalog coverage and real temporal discovery
only under later Orchestrator contracts. No native Pi durability claim is made.
