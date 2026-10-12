# ADR-0005: Offline temporal reference discovery and attested empty scope

Status: adopted for P4a implementation after Engineering Lead design checkpoint;
phase acceptance belongs exclusively to the Orchestrator.
Date: 2026-10-12. Owners: ARQ / DB-OWNER and DATA / DISCOVERY authors.

## Context

P1a contextual references and P3a frozen observations permit a local comparison
without a source, current manifest, identity allocation, or durable event store.
P4a compares one explicitly selected current batch against at most 32 explicitly
selected earlier batches in one exact namespace/kind/language context. Absence
from this supplied window establishes relative reference novelty only.

The immutable STORAGE_V1 `batches` table records capture, processing counts and
replay hashes, but no capture-scope namespace/kind/language. Empty batches have
no records from which to verify scope. `context_fingerprint` hashes the complete
resolver-relevant manifest, which can contain several languages, kinds and
namespaces. It is not a capture-scope declaration. Existing bounded `query`
returns the same empty result for a missing batch and an existing empty batch.

The original P4a contract permits an empty capture with context declared by its
producer, preserves the four-field request, and forbids schema changes. The
Engineering Brief requires an honest distinction between caller attestation and
stored proof. The design checkpoint reproduced the limitation on Python 3.13.15 /
SQLite 3.53.1: accepted ES, accepted EN and empty batches under one manifest had
the same context hash. This is information absent from the hash input, not a
SHA256 collision. The ignored evidence directory contains a reproducible probe;
author and independent tests supply candidate-specific evidence.

## Decision

### Exact window and context

The versioned request has exactly `version`, `current_batch_id`,
`history_batch_ids`, and `context`. History UUIDs are unique, distinct from the
current token, and canonically sorted. Every historical capture is strictly
earlier than current capture; historical captures may tie. No clock, implicit
latest batch, global scan, or baseline inferred from a missing batch is used.

All admitted rows in each batch must exactly match declared namespace, kind and
language, including null. Mixed contexts fail rather than being filtered. Full
reference equality additionally includes external ID and variant. Historical
seen references are the union of accepted and candidate rows; accepted non-set
references count as seen even though they do not emit events. Any rejected row
makes the comparison incomplete and fails the operation.

Submitting a request attests, on behalf of the local capture producer, that every
selected existing empty batch was produced for the exact request context.
Nonempty scope evidence is `records_verified`; empty scope evidence is
`request_attested_empty`. These labels appear for each selected batch in output.
The DB proves empty batch existence, capture and zero counts/rows. It cannot
prove the empty capture's context, authenticate the caller as producer, prove
capture completeness beyond the stored evidence, or establish source health.
The request does not create a persisted declaration. A wrong caller assertion
can cause false window-relative novelty. Results are conditional on that assertion.
This limited interpretation is compatible with the original producer-declaration
wording; no field, schema, or acceptance gate is silently removed. Requiring
independently verified durable empty scope would require an Orchestrator decision
and a later persistence contract, rather than relabeling a request as stored proof.

### Snapshot boundary

`persistence.sqlite_repository.read_snapshots` takes an explicit tuple of 1..33
unique canonical UUIDv4s and returns generic immutable batch/record snapshots.
One checked `mode=ro`, `query_only` connection and explicit `BEGIN` encompasses
ownership/schema checks, SQLite integrity and FK checks, every batch's metadata,
complete ordered rows, and accepted identity-parent checks. It rolls back the read
transaction and closes on every path. Writer `BEGIN IMMEDIATE` is not reused.

Each selected batch has at most 1,000 records and a LIMIT 1001 sentinel detects
overrun without truncated success. Total selected observations cannot exceed
33,000. Generic DTO validation checks versions, IDs, exact UTC timestamps, hash
grammar, record shape/status/provenance, indexes, counts and batch result. The
reader also verifies accepted targets and identity parent closure, target kind,
language/variant, and card number against the persisted projections. Historical
bindings and resolver context are not retained in full and cannot be reconstructed
from hashes; no current manifest is consulted or used to re-resolve history.

Integrity checks establish SQLite structure/CHECK/FK invariants, not scope,
business counter consistency, producer truth, rights, or health. Business
validation is separate. Whole-file integrity traversal shares the finite global
operation budget; the selected-row bound is not a promise that integrity work
is independent of total DB size. SQL and ordinary lock waits plus Python
validation checkpoints share a 2-second default, maximum 5-second budget.
Unresponsive OS/device calls remain outside this bound.

Rollback-journal readers can delay a writer's commit until their snapshot ends;
the bounded operation and closing limit that effect. Hot-journal recovery may
require writes and a read-only operation can fail safely. No journal deletion,
repair, initialization, business mutation, or schema migration occurs.

### Events and duplicate evidence

An accepted set reference absent from the history union emits
`SET_REFERENCE_FIRST_OBSERVED`; any absent candidate reference emits
`CANDIDATE_REFERENCE_FIRST_OBSERVED`, including a set candidate exactly once.
Accepted non-set references do not emit. A new external reference bound to an
existing CMT ID remains a new reference, never evidence of a new canonical product.

Identical same-reference records within one batch collapse for comparison and
retain their input indexes as event evidence. Different status, category, target
or normalized observations for one same-batch reference fail. Legitimate
differences across separate captures remain frozen. A prior candidate becoming
accepted, reappearance through an empty intervening capture, or name/date change
does not create novelty while the reference remains in the supplied history.
No history means explicit `baseline` with no events. Existing attested empty
history is an explicit window and may establish relative first observations.

### Canonical identities

Canonical JSON uses ASCII escaping, sorted object keys, compact separators,
finite values and validated fixed-microsecond UTC instants. SHA256 identifiers
have independently versioned payloads and `evt1:` / `cmp1:` prefixes. They are
not CMT UUIDs, authentication signatures, delivery keys or durable deduplication.

Event identity hashes `{identity_version:1,type,context,reference,
current_batch_id,captured_at}`. History permutation, replay, duration, run ID,
DB path and backup/restore do not change it. A different current token, capture,
context, reference or event type does. History affects whether an event exists,
but is not part of the identity of the same current finding.

Comparison identity hashes `{identity_version:1,request,snapshots}`. The request
is canonical, and snapshots are sorted by batch ID. Every snapshot includes
contract/input/resolver versions, batch ID, capture, replay hashes, counts,
processing result and full ordered frozen records. `first_persisted_at` is
excluded: local retention time is not observation evidence. A different selected
window, context, current token or relevant snapshot content changes comparison
identity. Both opaque replay hashes and validated read contents participate;
their inclusion does not make the original manifest recoverable or authentic.

`first_observed_in_window_at` equals the current capture for an emitted event,
since its reference is absent from every supplied prior capture. It does not
mean global first observation, local insertion, announcement, release or delivery.
Semantic output excludes runtime correlation/duration and uses stable reference
ordering with explicit null ordering.

## Alternatives

Treating `query` stdout as complete proof loses batch existence and metadata.
Independent read connections can combine metadata and rows from different
committed states. Hash equality cannot reveal omitted capture scope. Deriving
scope from manifest bindings confuses resolver authority with capture intent.
Silently dropping empty history changes the selected window and bootstrap
semantics. A new request attestation field or schema2 exceeds P4a authority.
Persisted event/outbox state and exactly-once claims belong to a later contract.

## Consequences

The operation remains offline, synthetic, read-only and provider independent.
Existing P0/P1a/P3a operations and schema1 remain compatible. Typed constructors
are revalidated at public boundaries. Errors return no partial events and never
represent missing, rejected, corrupt or timed-out evidence as zero discoveries.
Caller trust for empty capture scope is an explicit residual risk and debt.
QEMU and local SQLite tests do not certify native Pi or power-loss durability.

## Revisit conditions

Revisit with an authorized requirement for durable capture-scope declarations,
authenticated producers, licensed live feeds, larger history budgets, concurrent
writers, durable events/delivery, migrations, or physical Pi recovery. Elevate
any interpretation requiring stored empty-scope proof to the Orchestrator before
changing schema or accepting weaker evidence under a stronger claim.
