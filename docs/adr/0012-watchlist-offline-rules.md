# ADR-0012: Separate watchlist and pure synthetic rule evaluation

Date: 2026-10-23. Scope: P5a only. Authors: ARQ / BE / DB-OWNER / DOCS.

## Context

The first watchlist slice stores operator preferences for already curated
printing and sealed identities. It must preserve accepted catalog, capture,
Discovery, journal, outbox and delivery contracts. Configuration retries and
concurrent commands must not overwrite each other or manufacture observations.
An offline rule match provides an explanation, without creating an event or
authorizing delivery. The Raspberry Pi target favors bounded standard-library
operations and one independent local SQLite file.

## Decision

1. Reuse the complete MANIFEST_V1 parser at public add, update and evaluation
   boundaries. Only an existing printing or sealed CMT ID is admissible. Typed
   dataclasses, UUID syntax, names, source aliases and candidates confer no
   admission authority. Freeze canonical identity and required parent closure;
   exclude names, release dates, bindings and unrelated entities. Preserve exact
   null language, unknown variant and optional sealed set relationships.
2. Derive a watch key, not a product identity: `wlt1_` plus lowercase SHA-256 of
   UTF-8 `CMT_WATCHLIST_V1` followed by one NUL byte and the canonical CMT ID.
   Retain one entry per CMT ID, without retargeting or hard delete. Revalidate
   identity against the full current manifest on mutation and evaluation;
   incompatible canonical changes produce `identity_conflict`.
3. Store complete immutable configuration revisions and request replay records
   alongside a current-revision pointer in separate CMTW/schema1 SQLite storage.
   BEGIN IMMEDIATE commits history, pointer and request together. Add expects
   revision zero; subsequent changes require exact CAS. Canonical command
   equality binds action, target, precondition and complete effective config.
   An old replay reports the original operation without reverting newer state.
4. Use strict typed price/restock rules, EUR integer cents and an explicit
   bounded freshness window. At least one rule is configured even when disabled.
   Price and sample amounts are capped at 1,000,000,000 cents per field;
   booleans are not integers. max_age_seconds defaults to 86400, range 1..604800.
5. Keep a separate versioned synthetic sample contract. Samples and evaluation
   results are ephemeral; storage retains preferences, not observed prices.
   The pure evaluator accepts explicit revision, current/prior samples and
   as_of. It revalidates all inputs, identity/context and chronology before
   disabled SKIPPED. Freshness is inclusive and precedes stock decisions.
   Rules retain individual outcomes/reasons; OR gives MATCH precedence over
   INDETERMINATE and then NO_MATCH.
6. Expose explicit one-shot CLI operations, bounded keyset pages and a shared
   finite storage budget. Deep verification checks ownership, exact schema,
   immutable history, current pointers and replay correspondence. Backup uses
   a consistent SQLite snapshot. Restore reserves a new destination and fully
   validates it before exposure; previous stores are never migrated or written.
7. Product network budget is zero, including Telegram. No scheduler, source,
   market signal, historical observation or distributed transaction is added.
   Independent QA and a distinct REVIEWER must examine the final SHA/tree;
   documents and author tests alone cannot certify readiness.

The exact interfaces are [watchlist v1](../data-contracts/WATCHLIST_V1.md),
[storage v1](../data-contracts/WATCHLIST_STORAGE_V1.md) and
[synthetic evaluation v1](../data-contracts/WATCHLIST_SYNTHETIC_EVALUATION_V1.md).

## Alternatives

Mutating a prior database would couple recovery and break frozen ownership.
Deriving canonical CMT IDs, accepting names/URLs or inferring aliases would bypass
curation. Mutable configuration without history/CAS loses concurrent updates.
Token-only replay without command equality accepts conflicting requests; applying
an old replay to current state reverts legitimate changes. An expression DSL,
real sample acquisition, delivery and automatic scheduling exceed this phase.
Implicit clocks and coercive money parsing prevent reproducible decisions.

## Consequences

Configuration history grows without automatic retention. Whole-file verification
may time out as history grows; partial checking is never success. Private trusted
directories, host ACLs, capacity monitoring and recovery headroom remain operator
responsibilities. Hashes and synthetic labels test local equivalence and declared
shape; they authenticate neither a producer nor a privileged administrator.
Manifest validation and a later watchlist transaction are separate operations;
no atomic commit across files is claimed. Process interruption and ARM64 QEMU
evidence do not establish physical Raspberry Pi power-loss durability.
TD-001 through TD-005 remain OPEN with their existing owners and exits.

## Status

Adopted for P5a implementation, OPEN / IMPLEMENTATION AUTHORIZED. Acceptance,
integration and phase closure belong exclusively to the Orchestrator. This ADR
does not assert test, gate, publication or readiness results.

## Revisit conditions

An Orchestrator-authorized contract is required before real observations,
additional rules/currencies, event/outbox integration, transport, automatic
scheduling, multiuser or shared-directory deployment, retention/migration,
multiple independent writers or identity-granularity changes. Revisit operational
limits after measured capacity or native Pi recovery evidence.
