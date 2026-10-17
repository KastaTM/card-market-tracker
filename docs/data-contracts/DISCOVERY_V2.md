# Scoped capture Discovery v2

P4b adds a separate offline, read-only route. [ADR-0007](../adr/0007-scoped-capture-discovery.md)
and the [binding contract](../phases/P4B_SCOPED_CAPTURE_DISCOVERY_CONTRACT.md)
define its authority. V1 serialization, synthetic-only guard and hashes are unchanged.

## Strict request and unit selection

Exactly `version`, `context`, `current`, `history`; version is integer 2, never
bool. Context has exactly `namespace`, `kind`, `language`: P1a token <=128,
set/card/sealed and es/en/null exact. Each selection has exactly canonical UUIDv4
`batch_id` and nonempty `selector` <=256 characters. History has <=32 distinct
batches excluding current; canonical batch-ID ordering preserves duplicate errors.
No indexes, path/URL/SQL fields or extra references are accepted. Scope metadata
paths are never opened. Strict JSON/Python bounds: 1 MiB, depth16, nodes20000,
strings/keys1024, no duplicate keys/nonfinite values/malformed Unicode.

Exactly one persisted unit must match namespace/kind/language/selector. Missing
or ambiguous selection is an error. Validate the entire batch/envelope/partition
before selecting its original record indexes. Other validated units contribute
to global validated counts but no selected references or events. Rejected rows
inside the selected unit mean incomplete evidence, even on baseline.

## Storage and evidence

`read_scoped_snapshots(path, request, timeout=2.0)` returns generic `ScopedCapture`
DTOs, sorted by batch ID. One explicit BEGIN on one mode=ro/query_only connection
covers schema2, integrity/FKs, metadata, full capture envelopes and rows, retained
resolver reconstruction and accepted identity closure. SQL byte-size checks precede
envelope materialization, lexical complexity checks precede full JSON decoding.
Complete validation has a 33-batch / 33000-row bound, per-batch1000-row bound and
shared maximum5-second operation budget. Errors never yield truncated success.

The reader issues a private content-bound receipt only after validation. Ordinary
constructors and `dataclasses.replace` grant no stored provenance. The pure public
comparison boundary validates this receipt and revalidates request, actual
provenance, snapshots and scope; the receipt is not independent authentication
against code/administrators already inside the process. No current manifest or
resolver is consulted by comparison.

Schema1 or legacy_unverified fail explicitly; no scope inference or migration.
Families are pinned/verified_local_pinned_bundle (only reviewed P1b admission) and
synthetic/producer_declared. Documented and mixed windows fail. Source/namespace,
selector, exact selected path set, family and method/policy/semantics must agree.
Generic synthetic semantics are method `generic_synthetic_capture`, policy
`producer_declared_complete`, semantics `capture_scope_v1`. These are generic local
declaration labels, not a real repository/method. Reordered paths are equivalent.

Synthetic requires global outcome complete and every selected/completed path set
equal; pinned requires complete_nonempty over selected paths and reconstructed
counts. Rejections are not emptiness; missing artifact/language is not absence.
A complete synthetic zero-row unit retains its persisted producer declaration.
Every history capture is strictly before current by original normalized UTC time;
history-history ties are valid. No history is baseline after full validation.

## Algorithm and output

Full reference equality is namespace/kind/external_id/language/variant. History
is the union of accepted and candidate references across selected units. A prior
candidate later accepted, metadata/target changes or reappearance inside that
window are already seen. A new alias at the same curated target remains a new
reference, without asserting another real product. Current unseen accepted sets
emit SET_REFERENCE_FIRST_OBSERVED; unseen candidates of any kind emit
CANDIDATE_REFERENCE_FIRST_OBSERVED. Accepted cards/sealed emit none.
Identical duplicate observations/status/category/target collapse preserving
original indexes; contradictory duplicates inside a selected unit fail globally.
Across-capture evolution is permitted. There are at most1000 events.

Success JSON has exactly `version`, `result`, `comparison_id`, `context`,
`current`, `history`, `window`, `counts`, `events`. Result is
baseline/no_discoveries/discoveries; window is
`{scope:explicit_selected_capture_units}`. Each current/history item has exactly
`batch_id`, `selector`, `captured_at`, `mode`, `evidence_state`, `scope` (complete
selected unit with original indexes), `scope_semantics` (family, semantics, paths,
context, selector). History follows canonical batch-ID order.

Counts are exactly `validated_batches`, `validated_records`,
`current_selected_records`, `historical_selected_records`,
`current_selected_references`, `historical_selected_references`, `events`.
Validated records cover complete batches; selected records retain duplicates,
reference counts collapse them and historical references count the window union.
Events contain evt2 identity, type/reference/status/category/frozen CMT
target, current batch/capture, first_observed_in_window_at and evidence of the
comparison/window/unit with original record indexes. Names, full bundle and
manifest are excluded. First observation is only relative to selected history.

## Canonical identities

ASCII-escaped sorted-key compact JSON, finite values, SHA256 lowercase hex;
identity_version2. Capture identity is exactly `{snapshot,mode,evidence_state,
scope,capture_fingerprint,selection}`. Snapshot is full v1 frozen serialization
excluding first_persisted_at; scope includes all normalized units; selection is
`{batch_id,selector}`. The private receipt binds insertion time for API validation
only, never semantic identity. cmp2 hashes `{identity_version:2,request,captures}`,
with canonical request and capture identities sorted by batch ID. evt2 hashes
`{identity_version:2,type,context,reference,current,record,record_indexes}`:
current is current capture identity, record is full representative frozen record
with index normalized to0, and record_indexes preserves all original indexes.
History is excluded from evt2. Event evidence has comparison_id,
current_record_indexes and current/history unit evidence. Payload additions
require contract compatibility review.
New prefixes cmp2:/evt2: prevent collision with v1 namespaces. Scope/content
alterations change identity or fail validation. Reordered history, replay and
backup/restore preserve equivalent output. Execution clock/run ID/duration/DB
path/insertion time never participate. Hashes prove equivalence, not authenticity
or exactly-once delivery. V1 payloads remain unchanged.

## CLI, logging and failures

`cmt discover-scoped --db PATH --request REQUEST_JSON` accepts only v2. Success
exits0; malformed request/scope/chronology/incomplete or unsupported evidence
exits2; storage/schema/corruption/lock/deadline/IO exits1. Error JSON has version2,
result error, fixed safe error_category, counts null, events empty; no fallback or
partial output. A distinct allowlisted logging operation includes run ID,
duration/result/category and bounded validated-batch/row/event counts only.
No names/references/selectors/paths/tokens/SQL/payloads/raw exceptions enter logs.

No DB creation, schema/data mutation, journal deletion, repair, cache, migration,
source acquisition, promotion, CMT allocation, event store or delivery occurs.
Trusted local directories remain required. One approved real capture cannot
establish a real temporal transition; positive demonstrations remain synthetic.
