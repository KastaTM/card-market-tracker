# Offline temporal discovery v1

Status: adopted for P4a implementation; acceptance and final evidence pending.
See [ADR-0005](../adr/0005-offline-temporal-discovery.md) and the compatible
[STORAGE_V1 snapshot read extension](STORAGE_V1.md). All captures are synthetic;
there is no source query, event persistence, promotion, delivery or CMT ID allocation.

## Request

Local JSON has exactly `version`, `current_batch_id`, `history_batch_ids`,
`context`. Version is integer 1, never bool. UUIDs are canonical lowercase UUIDv4
under the existing P1a validator. History is a list of at most 32 unique tokens,
excluding current, canonically sorted independently of input order. Context has
exactly `namespace`, `kind`, `language`: namespace follows the P1a reference-token
grammar and 128-character bound; kind is set/card/sealed; language is es/en/null.
Null is exact, not a wildcard. Variant is part of reference identity, not context.

The existing strict JSON limits apply to request and direct Python parsing:
1,048,576 bytes, depth 16, 20,000 nodes, each string/key at most 1,024 characters,
no duplicate keys, nonfinite numbers or malformed Unicode. No path/SQL/URL field
is accepted; the DB path comes from the CLI. Typed constructors confer no trust.

Every admitted row in every selected batch must match context exactly. A mixed
batch is an error. Each historical capture is strictly earlier than current in
canonical UTC; historical captures may tie. Missing batch is an error, not empty.
No historical batch means baseline after validating current evidence. Selected
rejected evidence is incomplete and fails even in a baseline request.

Submitting this request explicitly attests on behalf of the local producer that
every selected existing empty capture belongs to this exact context. Output
labels its scope `request_attested_empty`. The database independently verifies
existence/capture/zero counts and rows, but contains no durable empty scope and
does not authenticate the assertion. For nonempty batches `records_verified`
means every admitted stored reference matched context; it does not prove producer
health, completeness of a real source, rights, or cryptographic authenticity.
False caller attestation may create false relative novelty. No empty batch is
silently removed or relabeled as independently proven context.

## Generic snapshots and validation

`SnapshotRecord(index,status,category,cmt_id,observation)` and `BatchSnapshot`
are frozen generic values. Observation is the existing normalized P1a value,
not a provider JSON object. `BatchSnapshot` fields are `version`, `input_version`,
`resolver_version`, `batch_id`, `captured_at`, `first_persisted_at`, `fingerprint`,
`context_fingerprint`, `input_count`, `accepted_count`, `candidate_count`,
`rejected_count`, `result`, `records`. Records are immutable ordered tuples;
indexes are exactly 0..input_count-1. Versions are strict integer 1.

Capture and first persistence must be valid fixed-microsecond UTC timestamps;
every admitted record's capture equals batch capture. Hashes are 64 lowercase
hex characters and remain opaque P3a replay metadata, not proof of capture scope.
Counts are strict integers 0..1000, sum correctly, equal actual status partitions
and row count, and agree with result empty/ok/mixed. Accepted records have null
category, original valid CMT UUID and synthetic observation. Candidates have a
P1a candidate category, synthetic observation and no target. Rejected records
contain only index/status/allowlisted category and no observation or CMT ID.

Generic snapshot validation checks all these invariants independently of SQLite.
The public read boundary verifies stored accepted target/parent identity as well.
Maximum 33 selected batches / 33,000 rows / 1,000 events; bounds fail explicitly,
never return truncated success. Snapshot validation does not re-resolve a frozen
record against a later manifest or promote candidates.

## Comparison

Reference key is exactly namespace/kind/external_id/language/variant. Historical
seen references are the union of all accepted and candidate references in selected
prior batches, including accepted non-set kinds. A prior candidate later accepted
is already seen. Reappearance through an empty intermediate batch is already
seen if the original reference remains in the selected window.

For a current reference absent from history: accepted set emits
`SET_REFERENCE_FIRST_OBSERVED`; candidate of any existing kind emits
`CANDIDATE_REFERENCE_FIRST_OBSERVED` exactly once, including set candidates;
accepted card/sealed emits nothing. A changed name/date or binding alone is not
a new reference. Different external ID with the same CMT target remains new
reference evidence without any `product_new` assertion.

Identical duplicate same-reference records within a batch collapse and preserve
their indexes as evidence. A difference in complete normalized observation,
status/category/target for that same reference within one batch is contradictory
and fails the entire operation. Legitimate evolution between batches is allowed.
No implicit global seen set, historical scan or perpetually durable dedupe exists.

## Semantic output

Successful JSON has exactly `version`, `result`, `comparison_id`, `context`,
`current_batch_id`, `captured_at`, `history_batch_ids`, `window`, `counts`, `events`.
Result is baseline/no_discoveries/discoveries. History UUIDs are canonical sorted.
`window` has `scope: explicit_selected_history`, `current` and `history`. Each
batch evidence item has `batch_id`, `captured_at`, `scope_evidence` whose value
is records_verified/request_attested_empty. History items follow canonical IDs.

Counts contain `batches`, `observations`, `current_observations`,
`historical_observations`, `current_references`, `historical_references`, `events`.
Observation counts preserve repeated input; reference counts collapse duplicates;
historical references count the union, not a sum of per-batch unique counts.
Baseline has no events; valid explicit empty history is a comparison window.

Each event has `event_id`, `type`, exact `reference`, frozen `status`, `category`,
`cmt_id`, `current_batch_id`, `captured_at`, `first_observed_in_window_at`,
`evidence`. Evidence has `comparison_id`, all `current_record_indexes` in ascending
order, and canonical `history_batch_ids`. CMT ID is present only as the original
accepted target; candidates use null. First observation is the current capture
for an emitted reference absent from supplied history, never a release, global
first appearance, local insertion instant or notification. Events have stable
contextual-reference order, with explicit null ordering. Names are not output.

Semantic output excludes run ID, duration, execution clock and DB paths. An error
contains version 1, result error, safe fixed `error_category`, `counts:null`,
`events:[]`, and no apparent partial success.

## Canonical identities

Canonical JSON is ASCII-escaped, sorted-key, compact JSON with finite values.
`evt1:` plus lowercase SHA256 hashes `{identity_version:1,type,context,reference,
current_batch_id,captured_at}`. Reordering history does not change an existing
current finding's event ID; different context/current capture/type/reference/token
does. Event identity does not imply exactly-once or durable delivery deduplication.

`cmp1:` plus lowercase SHA256 hashes `{identity_version:1,request,snapshots}`.
Request includes its sorted history. Snapshots are sorted by batch ID and include
all snapshot fields above except `first_persisted_at`; ordered records include
index/status/category/cmt_id and full normalized observation or null. Different
window/context/pertinent content changes comparison identity. Backup/restore
and identical replay preserve semantic output. Opaque stored hashes participate
as metadata, alongside validated full records, without becoming authenticity
proof or exposing a lost manifest.

## CLI and errors

`cmt discover --db PATH --request REQUEST_JSON` emits JSON stdout and allowlisted
correlated stderr logging. Success baseline/no_discoveries/discoveries exits 0.
Malformed/missing request, limits, context/chronology/contradictory evidence,
missing batch and selected rejections exit 2. Storage/IO/schema/corruption/lock/
deadline/unsafe DB path failures exit 1. Existing command behavior is unchanged.
No error becomes no_discoveries. SQL/paths/raw exceptions/payloads/names/reference
or batch tokens are excluded from logs. Stdout retains only contracted evidence.

`discovery.completed` logs result/duration/run ID/safe category and bounded batch,
observation and event counts. Failed operations use null counts. Read-only does
not promise recovery of a hot rollback journal requiring writes; such failures
are categorized and do not initialize, repair or delete the database.
