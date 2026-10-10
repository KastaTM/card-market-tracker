# ADR-0004: Atomic offline SQLite observation snapshots

Status: adopted for implementation after Lead design review; gates pending.
Phase acceptance belongs exclusively to the Orchestrator.
Date: 2026-10-10. Owner: one combined ARQ / DB-OWNER / storage author.

## Context

ADR-0003 makes the curated manifest the identity authority. P1a results omit
normalized names and timestamps and cannot alone reconstruct an observation.
P3a must retain synthetic metadata and immutable resolution snapshots, survive
process restarts, and distinguish retries from later captures. It must not
implement market data, Discovery, promotion, or a live collector.

## Decision

Use Python 3.13 standard-library `sqlite3`, without an ORM, migration framework,
pool or alternate backend abstraction. Application composition validates and
resolves input; the public repository independently revalidates its immutable
batch with the same boundary helper before opening a write connection. The
manifest remains read-only. Persist only accepted target parent closure as
identity projections; never allocate CMT IDs or overwrite identity relations.

Use four small tables: singleton ownership/version metadata, immutable entity
identity projections, committed batch metadata, and indexed record snapshots.
Accepted/candidate records contain complete contracted normalized metadata and
resolution; rejected records contain only index/status/fixed category. See
[persistence input](../data-contracts/PERSISTENCE_V1.md) and
[storage](../data-contracts/STORAGE_V1.md) for exact boundaries and invariants.
Initial schema version 1 is the only production schema. Empty SQLite initializes
atomically; current schema is a no-op; foreign, future and malformed structure
fail without reset. Validate owned schema SQL definitions, object inventory,
version metadata and application ID, including indexes and triggers.

Every connection explicitly uses `autocommit=True`, foreign keys on and checked,
and no extension loading. Writers use `BEGIN IMMEDIATE`, individual parameterized
statements and explicit SQL `COMMIT`/`ROLLBACK`. Do not use `executescript`, Python
connection context-manager commits, or `Connection.commit()` to establish
transaction semantics. Initial DDL and ownership/version publication share one
transaction. Batch projection checks/inserts, metadata and all record snapshots
share another transaction. Returned new-row counts exist only after commit.

Choose rollback journal `DELETE` and `synchronous=FULL` for single-host local
storage. New DB setup selects DELETE; existing owned DB must already use DELETE
and is checked before mutation. FULL is set per writable connection. Readers
open `mode=ro`, use `query_only` and never create/initialize files. No WAL files,
checkpoint policy or recurring background process are needed. A rollback journal
may exist during writes and recovery; operators must preserve it with the DB.

Default lock and operation budget is two seconds, never above five seconds.
Remaining monotonic budget controls each SQL busy timeout; a progress handler
interrupts long VM work. SQLite backup copies in bounded page steps with a
deadline-aware progress callback and short bounded retry sleep. These deadlines
bound SQL work and ordinary lock waits, not an unresponsive operating system or
physical device. One connection per operation, explicitly closed in all paths.

A producer-supplied UUIDv4 batch token is stable across retry; per-attempt run ID
is independent and not stored as identity. SHA256 of canonical normalized input,
ordered resolution snapshots and resolver-relevant manifest context is only an
equivalence check. Equivalent retry returns replay and zero new rows. Changed
content/context conflicts atomically. A different token inserts another capture,
even when evidence values match; loss of the token loses retry deduplication.

Read by batch, accepted CMT target or exact contextual candidate reference, with
fixed ascending `(captured_at, batch_id, index)` order and limit 1..1000. Integrity
verification checks both SQLite integrity and foreign keys. Backup and restore
both use the SQLite backup API from a verified compatible source into a newly
reserved exclusive destination, verify it, close/reopen and report success only
after completion. Existing files, links, directories and linked ancestors fail.
Pre-existing destination journal/WAL/SHM sidecars fail before reservation.
Failed copies remove only the destination created by this operation; they cannot
overwrite any existing file. Trusted local directory ownership is required;
cross-process hostile ancestor replacement is outside portable path checks.

## Alternatives

WAL can improve reader/writer overlap but adds sidecar/checkpoint operations
without a current consumer. An ORM or migration framework adds dependencies
without making this initial schema safer. Provider-derived IDs, name matching,
upserts, global content dedupe and storing P1a stdout lose required identity or
history. Copying an open main DB directly is not a consistent backup strategy.

## Consequences

Stored identity fields are immutable; localized canonical names are not stored.
Observation names, release date, provider update, explicit UTC capture and first
local batch persistence remain distinct. Candidates never have a CMT ID.
Canonical manifest names and audit reasons are excluded from replay context
because the resolver does not consume them. All other validated identity
projections and binding keys/targets participate conservatively; unrelated
binding edits can therefore require a new batch token. Full manifest context is
hashed in memory and is not retained as arbitrary curator text.

Process interruption tests demonstrate atomic recovery, not physical Pi
power-loss durability. FULL depends on honest storage/fsync behavior. History is
append-only with no destructive cleanup, commercial retention policy or source
health claim. Synthetic provenance is a local producer claim, not proof of rights.

## Sources and effective runtime

Consulted official [Python 3.13 sqlite3 documentation](https://docs.python.org/3.13/library/sqlite3.html),
[SQLite online backup documentation](https://www.sqlite.org/backup.html), and
[SQLite WAL documentation](https://www.sqlite.org/wal.html) on 2026-10-10.
The official Python page currently identifies its documentation as 3.13.16;
the local executable is Python 3.13.15 with SQLite 3.53.1. A local probe of
explicit BEGIN/DDL/SQL ROLLBACK leaves no table. Container runtime versions must
be recorded separately. Backup supports a consistent snapshot while the source
is accessed, and deadline control must account for busy retries.

## Revisit

Revisit when an authorized phase needs concurrent writers, licensed non-synthetic
retention, new observation contracts, a second schema, large-history operational
budgets or native Pi recovery evidence. No such capability is implied now.
