# Discovery journal API and CLI v1

Authority: [P4c contract](../phases/P4C_DISCOVERY_RESULT_JOURNAL_CONTRACT.md).
Implementation candidate; phase acceptance belongs to the Orchestrator.
Companion [storage contract](DISCOVERY_JOURNAL_STORAGE_V1.md) and
[ADR-0009](../adr/0009-discovery-result-event-journal.md).

## Admission and identity

`discovery.journal_application.record(captures_db, journal_db, request_path,
timeout=2.0)` accepts only paths to an existing capture DB, explicitly initialized
journal and strict DISCOVERY_V3 request file. It uses the unchanged
`read_multi_revision_snapshots` followed by the pure `multi_comparison.compare`.
No public result DTO, JSON, verified flag, digest or ID authorizes persistence.
The application issues a private receipt sealed over the frozen canonical
request/result bytes. Storage rechecks authority, content and full local grammar
before opening its write transaction. This is a local trusted-process boundary,
not a signature or defense against privileged in-process code.

The capture reader verifies the complete explicit window in one read-only
transaction. Journal commit follows in a separate transaction: there is no
distributed transaction. Capture evidence is immutable by its existing contract.
No source acquisition, current-manifest lookup or algorithm reimplementation occurs.

Store the complete normalized request and v3 result, including profile, context,
clocks, acquisition, extraction proof, scope, counts, references and frozen CMT IDs.
Preserve cmp3/evt3 and all historical identities. First persistence is a local UTC
microsecond timestamp, distinct from acquisition/capture/event clocks.

Canonical JSON is ASCII escaped, sorted-key, compact and finite:
`json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False)`.
Content SHA256 hashes the ASCII canonical object
`{"journal_version":1,"request":NORMALIZED_REQUEST,"result":FULL_V3_RESULT}`.
Insertion clock, run ID, duration and filesystem paths are excluded.

Same comparison and identical request/result is replay with no rewrite, preserving
the first persistence timestamp. Same comparison with differing content is conflict
with zero mutation, comparing content in addition to digest. Comparison plus all
ordered event occurrences commit atomically. Occurrence identity is the pair
`(comparison_id,event_id)`; the same evt3 in two windows retains both complete
evidences. This implies neither global novelty nor exactly-once delivery.
Baseline and no_discoveries are durable successful comparisons with zero events.

## Command grammar and results

All operations require `--journal-db PATH`. Each accepts `--timeout SECONDS`
(default 2, finite positive maximum 5). No operation auto-initializes.

| Operation | Additional arguments | Success |
| --- | --- | --- |
| init | none | new journal, schema_version 1 |
| record | --captures-db PATH --request PATH | inserted or replay, comparison_id, first_recorded_at, counts comparisons/occurrences |
| get | --comparison-id CMP3 | request, comparison (complete v3), content_sha256, first_recorded_at |
| list | optional --limit N --cursor CMP3 | summary items and next_cursor |
| event-occurrences | --event-id EVT3, optional --limit N --cursor CMP3 | one summary per matching comparison, ordinal, next_cursor |
| verify | none | level local, counts comparisons/occurrences |
| recompute | --captures-db PATH --comparison-id CMP3 | level origin-recompute, comparison_id |
| backup | --destination NEW_PATH | verified consistent independent journal and counts |
| restore | --destination NEW_PATH | verified restored journal and counts |

Responses have integer `version:1`, operation and result. Query/init/verify/copy/
recompute success has result ok. Errors have result error and fixed error_category;
no partial success or partial evidence is emitted. No `--result` exists.

List orders by comparison_id; event-occurrences filters exact evt3 and orders by
comparison_id. Cursor is the previous last canonical lowercase cmp3 ID. Strict
integer (nonbool) limit 1..1000 defaults to100. Pages contain summaries, never full
comparisons, and at most1MiB canonical output. One extra row detects next_cursor.
Static paging has no duplicates/omissions; under concurrent inserts, rows after
the cursor can appear, while earlier IDs are absent from subsequent pages. A
cursor does not freeze an all-pages snapshot. Get returns just one comparison.

## Verification, limits and errors

Local verify checks exact ownership/schema/inventory, integrity/FKs, bounded
strict JSON, canonical bytes, complete request/result grammar, timestamps, digest,
counts, ordinals and exact parent/occurrence equality. It cannot authenticate
coherently rewritten history. Recompute reads the retained request, verifies
original captures again, executes the existing comparator and compares the full
result and cmp3. Absent, changed or corrupt captures fail without repairing data.
Both are read-only and represent distinct evidence levels.

V3 guards remain: request1MiB, depth16, nodes20000, strings1024, history32,
33batches/33000records,1000records per batch,1000events. Expanded results repeat
evidence per event and do not inherit the request's aggregate20000-node limit.
Journal canonical result cap is16MiB; encoding stops before an oversized result
is copied through to_dict or written. Component grammar preserves original
bounds. SQLite TEXT types/byte lengths are checked in SQL before loading, even
if an attacker bypassed SQL CHECKs. Logs/pages never expand the whole history.
Record shares one monotonic budget across input, source verification, comparison
and storage; busy/progress/application loops are bounded. These are cooperative
deadlines, not guarantees against blocked OS/device calls. Whole-journal verify
and copies may fail as history grows; partial verification is never PASS.

Exit0 means success. Input/JSON/version/profile/scope/chronology/unsupported
evidence/conflict/input_limit/invalid_field categories exit2. Input IO, unsafe
destination, storage_missing/schema/corrupt/locked/timeout/io and recompute_mismatch
exit1. Upstream validated categories retain those mappings. Unanticipated CLI
execution failures use storage_io without exposing raw exceptions. Missing DB
never becomes empty success. No error is no_discoveries.

Structured logs emit discovery.journal.completed, component cli, a fixed
discovery_journal operation, run_id, duration_ms, result inserted/replay/ok/error,
error_category when applicable and bounded journal comparison/occurrence counts.
No payload, names, references, selectors, paths, SQL or raw exception text is
logged. Explicit stdout contains contracted evidence and requires local protection.

Existing discover/discover-scoped/discover-multi-revision output, exit codes and
effects are preserved. Capture schema2/five tables, original licensed minimum/MIT
notice, guards and source registry remain untouched. No alerts, scheduler, outbox,
new source, API/frontend, price/stock or retention behavior is introduced.
