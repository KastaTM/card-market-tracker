# Profiled multi-revision Discovery v3

Authority: [P1c contract](../phases/P1C_MULTI_REVISION_METADATA_CAPTURE_CONTRACT.md)
and [ADR-0008](../adr/0008-multi-revision-metadata-capture.md). The separate route
preserves [Discovery v1](DISCOVERY_V1.md) and [v2](DISCOVERY_V2.md), including their
guards, serialization and hash namespaces.

## Request and trusted profiles

Exactly version, profile, context, current and history are accepted. Version is
integer3, never bool. Context and selections follow the strict v2 grammar:
namespace token at most128, kind set/card/sealed, exact es/en/null language;
selection has canonical UUIDv4 batch_id and nonempty selector at most256.
History contains at most32 distinct batches, excludes current and canonicalizes
by batch ID. Request limits remain 1MiB/depth16/nodes20000/string1024, duplicate
keys and nonfinite/invalid JSON forbidden. No fallback between versions occurs.

Profile is exactly one of:

- `tcgdex_swsh3_136_r0_r1_v1`: pinned/verified_local_pinned_bundle captures whose
  complete retained packages belong to the exact reviewed R0/R1 code registry.
- `synthetic_multi_revision_v1`: synthetic/producer_declared captures only, for
  algorithm/adversarial demonstrations. This profile never authorizes real data.

Membership is verified from retained packages by storage; a request/profile
string, claimed digest or Python constructor grants no authority. Unknown
profiles, third packages, mixed families, schema1 and legacy scope fail.

## Read boundary and comparability

`read_multi_revision_snapshots(path,MultiRevisionRequest,timeout=2.0)` validates
the request and reads the complete explicit window in one mode=ro/query_only
connection and BEGIN/ROLLBACK. It shares the scoped window reader and retained
admission verifier. Schema/integrity/FKs, complete rows/envelopes, manifest,
resolver snapshots, all units/counters and identity parent closure validate
before selection. SQL byte guards precede envelope materialization; lexical
bounds precede JSON decoding. Per-batch1000, total33000 rows and 33 batches apply.
The shared operation budget defaults2 seconds and is at most5 seconds.

Storage issues content-bound `ProfiledCapture(ScopedCapture,profile,extraction_json)` receipts
inside that transaction after actual registry/family checks. The pure comparator
rechecks the profile receipt and underlying storage receipt, validates complete
snapshot/scope and selects exactly one matching unit per batch. Public
construction or replacement cannot confer those receipts. This is an application
trust boundary, not authentication against arbitrary in-process code.

R0 retains scope1; R1 has scope2. The profiled route permits both. Comparable
units require identical family, source/method, namespace, policy/extractor,
timestamp convention, evidence status, kind/language, exact selector and selected
path set. Pinned scope is reconstructed complete_nonempty. Synthetic outcome
must be complete with all path sets completed; partial/failed fail. Selected
rejects fail even for baseline. Contradictory references in any unit fail.
Unselected units remain validated and count toward global bounds.

Only the compatibility key omits per-capture revision, bundle/projection hashes,
artifacts and scope version for the reviewed pair. The original complete scopes
and fingerprints retain them. Replay equality remains stricter than comparison
compatibility. Every historical captured_at must be strictly before current;
history-history ties are allowed. R0 to R1 is valid, reverse order fails, and two
tokens of one package fail equal-time chronology. Four units are one acquisition.

## Algorithm and output

The pure `discovery.multi_comparison.compare(request,captures)` performs no IO,
provider import, current-manifest lookup or historical re-resolution. Reference
equality includes namespace/kind/external_id/language/variant. History is the
union of accepted and candidate references. Identical within-unit duplicates
collapse with original indexes; contradictory duplicates fail. Unseen current
accepted sets emit SET_REFERENCE_FIRST_OBSERVED; unseen candidates emit
CANDIDATE_REFERENCE_FIRST_OBSERVED. Accepted cards/sealed emit none. Existing
references with changed metadata/target, candidate-to-accepted or reappearance
within the selected union produce no novelty. At most1000 events are returned.

Success keys are version3, result, comparison_id, profile, context, current,
history, window, counts, events. Result is baseline with no history, otherwise
discoveries or no_discoveries. Window is
`{scope:explicit_selected_capture_units}`. Counts have the unchanged seven v2
fields: validated_batches, validated_records, current_selected_records,
historical_selected_records, current_selected_references,
historical_selected_references, events. Full validated rows and selected rows
remain distinct counts.

Current/history evidence contains batch_id, selector, captured_at, mode,
evidence_state, selected unit scope with original indexes, normalized
scope_semantics, profile, bounded acquisition and extraction_proof. Acquisition retains available
version/source/method/revision/namespace/policy_version/extractor_version,
acquired_at/captured_at/timestamp_convention, artifact locks, complete path sets,
evidence_status, bundle/projection hashes, and synthetic outcome. It contains no
full package, manifest, names or raw upstream bodies. History is canonically
ordered. Both real revisions/digests/times remain visible even with zero events.

Real extraction_proof has exactly version1, extractor and fields. The reviewed
registry supplies exactly eight UTF8 zero-based half-open span records, each
with exact path/field/start/end/transformation. Both approved packages use the
same reviewed spans because their blobs and extractor are identical. The generic
validator requires exact keys, nonempty <=32 fields, unique(path,field), path<=256,
field<=128, integer(nonbool) 0<=start<end<=65536 and transformation exact_literal.
Existing JSON byte/lexical limits apply before decoding. The synthetic profile
requires extraction_proof null. The content-bound profile receipt covers the
canonical proof, so a copied receipt cannot authorize changed spans. Registry
proof is an adjunct to v3 evidence; source bundles, envelopes and replay remain
unchanged. Complete proof participates in cmp3 and evt3 current-capture identity.

Events retain the v2 event fields with evt3 IDs: type/reference/status/category,
frozen cmt_id, current_batch_id/captured_at/first_observed_in_window_at and
evidence with comparison_id, original indexes and current/history evidence.
First observation means relative to the explicit window, never global novelty,
physical product introduction, launch, price, stock or source health.

## Canonical identities

Use ASCII-escaped sorted-key compact finite JSON and lowercase SHA256. Complete
capture identity is `{snapshot,mode,evidence_state,scope,capture_fingerprint,
selection,profile,extraction_proof}`: all frozen ordered rows and complete normalized scopes
participate, excluding first_persisted_at. The insertion time is bound by private
receipts only, never semantic identity.

`cmp3:` hashes `{identity_version:3,request,captures}` with full version3/profile
request and captures sorted by batch ID. `evt3:` hashes
`{identity_version:3,type,profile,context,reference,current,record,record_indexes}`.
Current is its complete capture identity; record is the full representative
frozen record with index normalized0; indexes retain originals. History affects
event existence and comparison identity but is excluded from event identity.
Revision, acquisition clocks, artifacts/digests, scope and replay fingerprints
remain identity evidence. History permutation, replay and backup/restore retain
equivalence. Execution/run ID, duration, DB path and insertion time are excluded.
These hashes provide equivalence, not signatures or exactly-once delivery.

## CLI, failures and limits

`cmt discover-multi-revision --db PATH --request REQUEST_JSON` accepts only v3.
Success exits0. Invalid request/profile/unit/scope/chronology/incomplete or
unsupported evidence exits2; storage/schema/corruption/lock/deadline/IO or local
execution exits1. Error JSON is version3, result error, fixed error_category,
counts null and events empty. It never reports partial success or treats an
error as zero discoveries.

Structured logs use discovery.multi.completed / discover_multi_revision with
run correlation, result/category, duration and bounded counts. No names,
references, selectors, tokens, URLs, paths, payloads, SQL or raw exceptions enter
logs. Stdout is explicit contracted evidence and needs local protection.

Comparison does not initialize/create/migrate/repair a DB, write business data,
delete journals, acquire upstream content, allocate identities or persist events.
Whole-database integrity work shares the finite deadline; stalled OS/device calls
remain outside that guarantee. The real unchanged pair must return
no_discoveries and zero events for all four units; positive events remain synthetic.
