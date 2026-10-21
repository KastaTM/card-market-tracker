# ADR-0010: Offline alert identity and window evidence outbox

Status: adopted for P8a implementation; phase acceptance belongs to Orchestrator.
Date: 2026-10-20.

## Context

Discovery journal v1 preserves complete verified v3 comparisons. The same event
can appear in distinct selected windows with different evidence. Preparing one
message per comparison would duplicate future notification intent; deduplicating
away windows would lose evidence. Capture and journal schemas/identities are
accepted and must remain unchanged. Source acquisition budget is zero; delivery
is outside P8a.

## Decision

Use a separate SQLite outbox v1, application CMTA and exact owner/inventory, with
three STRICT tables: metadata, alerts and alert_evidence. Alert identity alt1 is
SHA-256 of canonical finite ASCII JSON with identity_version1, destination_key
and event_id. Destination is a bounded local ASCII alias. Comparison, window
history, paths, preparation clocks and renderer versions do not enter identity.

Freeze a validated intrinsic intent and deterministic plain-text message per
alert. Include policy discovery_reference_alert_v1, integer renderer version1,
offline_preview channel and pending state. Preserve original reference values in
complete event evidence while escaping unsafe controls in presentation. Label
synthetic evidence, distinguish candidates and describe novelty relative to the
selected window. Do not infer commercial availability or global novelty.

Preserve complete window-specific events and the journal semantic digest in
associations keyed (alert_id,comparison_id). Same event/destination across two
windows gives one alert and two independently retrievable associations; changing
destination gives a separate alert. Existing identity with different intrinsic
content or association content is conflict. A single BEGIN IMMEDIATE transaction
inserts the entire requested comparison, including new evidence for old alerts.
Replay preserves message, evidence, pending state and first local preparation
time. Baseline/no_discoveries performs a read-only validation with zero rows.

Public admission requires three explicit distinct DBs and one explicit cmp3 and
destination. Reuse journal validation and unchanged original-capture reader/pure
comparator. Freeze and compare the whole retained result before issuing a private
content-bound receipt. Storage revalidates every consumed row. This controls the
application boundary and does not authenticate privileged in-process code.
Capture/journal reads precede outbox commit; there is no distributed atomicity.
Immutable origin evidence remains the assumption.

Bound every SQLite cell before materialization and every prepared operation before
retention. One deadline covers origin verification through commit. Local verify
checks complete structural/semantic consistency; origin recompute independently
checks the journal/captures. Queries and preview are read-only, with strict keyset
pages; timeout never becomes partial PASS. Backup/restore use SQLite snapshots,
new exclusively reserved safe files, validation and reopen. The three databases
need separate recovery followed by origin recompute.

## Alternatives

Adding outbox tables to captures or journal would change their accepted schema
and recovery lifecycle. Including comparison_id in alert identity would duplicate
intent across windows. Keeping one evidence row per event would discard distinct
window proof. Public result JSON admission would bypass original-capture checks.
Early transport/leases/acknowledgements would open P8b without authorization.
These alternatives are rejected within P8a scope.

## Consequences and revisit conditions

No source/comparator/capture/journal schema or identity changes. No network
transport, dispatcher, retries, recipient credentials, scheduling or delivered
state exists. Pending conveys preparation only. Future renderer/policy changes
cannot authorize a fresh send automatically and require a migration contract.
Storage limits may reject otherwise valid large Discovery results. Keyset pages
are separate snapshots. Cooperative deadlines do not bound stalled device IO.
Local verify cannot authenticate a coherent privileged rewrite; recompute cannot
defend an administrator controlling all originals. TD-001 through TD-005 remain
open. Process interruption/QEMU do not prove physical Pi power-loss durability.

Revisit through an authorized phase contract when transport, stronger producer
or host authentication, quotas/retention, migrations, physical durability or
cross-database snapshot coordination is needed. P8b is not opened here.
