# ADR-0007: Read-only Discovery over explicit persisted capture units

Status: adopted for P4b implementation; independent exact-candidate reviews and
Orchestrator acceptance remain separate gates.
Date: 2026-10-16. Owners: Engineering Lead, ARQ / DB-OWNER, BE / DISCOVERY.

## Context

P1b schema2 stores durable unit scope and frozen resolution. P4a cannot consume
observed batches and its empty scope is caller-attested. The approved real bundle
contains four ES/EN set/card projections from one capture instant. Importing it
under another token provides no second temporal observation.

## Decision

Add DISCOVERY_V2 and a separate `discover-scoped` command. A strict request selects
exactly one unit per explicitly named batch. The SQLite reader validates the
complete window, including other units, in one existing read-only/query-only
connection and explicit deferred transaction. It reuses P1b envelope byte guards,
lexical guards and retained bundle/manifest reconstruction, then checks complete
records, provenance and accepted identity parent closure. No schema or writer
policy changes are needed. Schema1 and legacy scope are unsupported by v2.

Storage returns generic frozen DTOs. A private, content-bound in-process receipt
marks values issued after storage validation; public dataclass construction or
replacement cannot confer that provenance. This is a conventional module trust
boundary, not authentication against arbitrary code executing within the process.
The pure comparator still revalidates request, full snapshot shape and scope.
It imports no provider, SQLite, current manifest or source transport, performs no
I/O and never changes provenance to pass the v1 synthetic guard.

Comparable units require exact context, selector, selected path set and compatible
evidence family/method/policy/semantics. Generic synthetic scopes use the explicit
CAPTURE_SCOPE_V1 producer declaration, without inventing a repository or real
acquisition method. Pinned units retain the one approved bundle policy; no other
observed policy is admitted. Original normalized capture time alone orders the
window. Global partial/failed and selected rejects fail, including on baseline.

Use the full reference key and union accepted plus candidate history. Collapse
identical within-unit duplicates while retaining original indexes; contradictions
fail. Only accepted sets and candidates can emit first-observed-in-window events.
Frozen targets, exact nulls and textual numbers remain evidence. Baseline has
no events. Versioned cmp2/evt2 identities include scope and evidence/content;
execution time, insertion time and paths to the DB remain nonsemantic.

DISCOVERY_V1, its synthetic-only validation and cmp1/evt1 payloads stay intact.
PERSISTENCE_V1, P1b admission, migration, replay and backup/restore stay intact.

## Alternatives considered

Widening v1's provenance guard would silently change a contracted interface.
Repeated `query_capture` calls can mix committed snapshots. Filtering before
full validation can turn corrupt or partial evidence into false completeness.
Manifest hashes cannot reconstruct capture scope. Reimport tokens cannot replace
capture chronology. A new schema/event store or second real package exceeds scope.
Trusting a constructor or a caller-provided digest would bypass reviewed admission.

## Consequences

New reads retain the 2-second default / 5-second maximum shared budget and safe
lock/deadline errors. Whole-DB integrity work may exceed the budget as history
grows; unresponsive OS/device work remains outside deadline guarantees. Reader
rollback/close must work after interruption; hot-journal recovery is never forced.

The real demonstration is four validated unit baselines with no events and an
equal-time chronology rejection. Positive transitions and empty scopes are
synthetic producer declarations, not independently authenticated observations.
No real provider change, launch, stock, global novelty, exactly-once delivery or
physical Pi durability is established. TD-001–TD-005 remain open.

## Revisit conditions

A second compatible real acquisition, another evidence policy, authenticated
independent producers, larger windows, continuous collection, event delivery or
physical Pi qualification requires a later Orchestrator-authorized contract.
