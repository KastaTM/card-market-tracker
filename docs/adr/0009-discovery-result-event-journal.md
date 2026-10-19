# ADR-0009: Separate Discovery result and event occurrence journal

Status: adopted for P4c implementation; phase acceptance belongs to Orchestrator.
Date: 2026-10-19.

## Context

Discovery v3 deterministically compares explicit verified capture windows, but
its stdout is not a durable queryable result record. The same evt3 can appear
in distinct cmp3 windows with different history evidence. Capture schema2 and
historical identities must remain stable, and source acquisition is zero.

## Decision

Use a separate SQLite application identity and schema v1 with exactly ownership,
comparisons and event_occurrences tables. Persist the normalized request, full
canonical semantic result, SHA256 content digest and first local insertion time.
Occurrence identity is (comparison_id,event_id), with unique deterministic ordinal
per comparison; event_id has a nonunique lookup index across comparisons.

The application admits only explicit request plus capture/journal paths. It
reuses the complete existing capture reader and pure comparator before issuing
a private content-bound receipt. Storage consumes and independently revalidates
the receipt/grammar/limits. This controls trusted in-process application use;
it is not a signature against compromised privileged code.

One BEGIN IMMEDIATE transaction atomically inserts comparison and all events.
Equal content replays preserve original content and first time; divergent content
for the same comparison fails and rolls back. Capture reading precedes journal
writing, with no distributed transaction. Existing capture immutability remains
the compatibility assumption. The comparator has no journal or IO dependency.

Use bounded read-only exact queries, keyset pages and local integrity verification.
Schema ownership and every returned scalar/payload receive byte guards before
materialization. Record shares one finite operation deadline across admission,
comparison and persistence. Verification does not report partial success.
Explicit backup/restore use SQLite backup into exclusively reserved new files,
validate copied content and reopen it. Path checks reuse the trusted-directory
policy; TD-003 host-administrator races are not solved.

Local verify establishes structural/semantic self-consistency, not source
authenticity. Explicit recompute against retained original captures additionally
compares comparison identity and the whole semantic result. Captures and journal
require separate backups; recovery never silently drops or repairs evidence.

## Alternatives

Adding journal tables to captures would expand the accepted schema2 inventory
and couple write/recovery lifecycles. Global event deduplication would discard
valid window-specific evidence. Accepting public result JSON would bypass
capture admission. Reconstructing results only at query time would lose the
first recorded evidence and require captures for every query. Those alternatives
are rejected for this scope.

## Consequences and revisit conditions

No change to cmp1/evt1/cmp2/evt2/cmp3/evt3 preimages, original comparators,
capture schema, source bytes or acquisition clocks. Zero-event results persist.
The journal result ceiling16MiB may reject an otherwise valid pure comparison;
pages are capped at1000 rows and1MiB. Budgets are SQLite/application work bounds,
not guarantees for stalled OS IO. Keyset pages have no shared snapshot across
requests. Physical power-loss durability and native Raspberry Pi testing are
not implied by process interruption or emulation evidence.

Revisit only through an authorized phase contract if migration, quotas/retention,
transport/delivery state, stronger host confinement or cross-database snapshot
coordination becomes required. None is implemented speculatively in P4c.
