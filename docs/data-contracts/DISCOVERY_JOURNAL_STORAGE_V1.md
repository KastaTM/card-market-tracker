# Discovery journal SQLite storage v1

Authority: [P4c](../phases/P4C_DISCOVERY_RESULT_JOURNAL_CONTRACT.md) and
[ADR-0009](../adr/0009-discovery-result-event-journal.md). The independent journal
does not change capture schema2, its five tables, or Discovery identities.

## Identity and physical schema

`application_id=0x434D544A`, `user_version=1`, owner
`card-market-tracker.discovery-journal`, journal mode DELETE, synchronous FULL
for writes. Exact SQLite-normalized DDL, tables, explicit and implicit indexes
must equal `journal_schema.expected_inventory()`. Unknown objects, changed
constraints, versions, owner rows, or journal mode fail; nothing migrates.

Exactly three STRICT tables exist:

| Table | Columns and constraints |
| --- | --- |
| journal_metadata | singleton INTEGER PRIMARY KEY CHECK=1; exact owner TEXT; schema_version INTEGER CHECK=1; exactly one row |
| comparisons | comparison_id TEXT PRIMARY KEY NOT NULL, 69 characters; request_json TEXT, 2..1048576 bytes; result_json TEXT, 2..16777216 bytes; content_sha256 TEXT, 64 characters; first_recorded_at TEXT, 27 characters; all NOT NULL |
| event_occurrences | comparison_id TEXT FK comparisons ON DELETE RESTRICT; event_id TEXT, 69 characters; ordinal INTEGER 0..999; event_json TEXT, 2..16777216 bytes; all NOT NULL; PRIMARY KEY(comparison_id,event_id); UNIQUE(comparison_id,ordinal) |

`occurrence_by_event(event_id,comparison_id)` supports exact event lookup and
keyset pagination. SQLite owns three implicit UNIQUE/PK indexes. No triggers,
autoincrement, delivery state, deletion or retention API exist.

CHECK constraints complement validation; they do not establish trust. SQL reads
guard every returned TEXT with typeof and byte length before materializing it,
including schema SQL/names, metadata, identifiers, hashes and clocks. Inventory
reads stop after expected object count plus one. SQLite LENGTH and SQL limits,
VM progress and busy callbacks additionally bound hostile files. A read holds
one transaction so validation and payload selection share one snapshot.

## Canonical content and admission

The request is the normalized explicit v3 request. The full successful semantic
v3 result retains evidence, scopes, acquisition/extraction metadata and frozen
IDs exactly. Public recording accepts request plus capture/journal paths only;
the application verifies all captures using P1c, runs the unchanged comparator,
then issues its private content-bound receipt. `_record_verified` consumes that
receipt, revalidates semantic grammar and limits, and enforces canonical byte
ceilings before joining encoded content. A Python DTO, result JSON, declared
hash or verified flag grants no authority. The receipt is an in-process trust
boundary, not authentication against arbitrary privileged Python code.

Canonical JSON uses `ensure_ascii=True`, `sort_keys=True`,
`separators=(',', ':')`, `allow_nan=False`. SHA-256 lowercase hex covers the
ASCII bytes of canonical
`{"journal_version":1,"request":<request object>,"result":<result object>}`.
The digest is streamed. Insertion time, run IDs, duration and paths are excluded.
`first_recorded_at` is a valid UTC timestamp `YYYY-MM-DDTHH:MM:SS.ffffffZ`; it
records local first persistence and does not replace acquisition/event clocks.

One BEGIN IMMEDIATE/COMMIT transaction stores the comparison and all ordered
occurrences. Replay requires equal canonical request and entire semantic result,
preserves first insertion and writes no rows. Same comparison with different
content raises conflict with rollback. Same event ID in different comparisons
has separate occurrences and separate evidence. Zero events is valid. All
occurrence order, count, IDs and canonical event objects must equal the result.

The capture read finishes before journal writes. There is no cross-database
transaction. Existing capture immutability is relied upon; journal atomicity
covers its own comparison and occurrences only. Rollback disables expired
progress/busy handlers before cleanup. Process-recovery tests do not demonstrate
physical power-loss durability.

## Queries, bounds and verification

`get` retrieves one exact cmp3 ID, its normalized request, `comparison`, digest
and first timestamp. Missing DB/row is `storage_missing`, never empty success.
`list_comparisons` returns summaries with comparison_id, content_sha256,
first_recorded_at, result_bytes. `event_occurrences` returns comparison_id and
ordinal for one exact evt3 ID. Responses contain version1, operation, result,
items and next_cursor, with event_id for occurrence queries. Limits default100,
range1..1000 (bool forbidden); IDs/cursors are exact lowercase cmp3/evt3 SHA256
tokens. Rows sort by comparison_id; next_cursor is the final returned ID only
when more rows exist. A page uses one snapshot; successive pages do not share
an all-pages snapshot under concurrent insertion. Summaries never load results;
the complete canonical response has a 1MiB ceiling.

`verify` is read-only and requires exact identity/inventory, integrity_check,
foreign_key_check, finite strict JSON, normalized request/full result grammar,
canonical equality, digest, row identity and exact occurrence reconstruction.
It visits all comparisons within its budget; timeout is failure, never partial
PASS. Local verify detects inconsistencies but cannot authenticate a coherent
administrator rewrite. Application `recompute` separately verifies retained
request against the supplied original captures and compares full semantic output.
No verification path repairs, initializes, drops or migrates data.

Default operation budget2s, explicit maximum5s, finite nonbool numeric input.
Record starts at application entry and shares the deadline across all stages.
SQL busy/progress handlers and explicit loops check remaining time. These are
application/SQLite work budgets, not hard wall-clock latency promises for stalled
kernel/device calls. Existing v3 request1MiB/depth16/nodes20000/string1024,
33batches/33000records/1000events remain; full repeated result has its separate
16MiB ceiling. No global disk quota or automatic deletion is introduced.

## Paths and recovery

Only explicit init exclusively reserves a new local file, mode0600 where
supported. All existing files and existing sidecars at new destinations fail.
Other operations never create missing DBs. Existing persistence path policy is
reused: trusted local ancestor directories, no traversal, UNC/device/ADS,
reserved paths, symlink/junction/reparse points or hardlinks; regular file link
count must be1, including existing sidecars. Open checks compare file identity.
These checks assume trusted directories and do not defeat an administrator
racing file replacement (TD-003 remains open).

Backup and restore exclusively create new destinations using SQLite backup,
within the shared budget, and validate the source snapshot, copied content and
reopened destination. Source and destination aliases/existing links fail without
overwriting. Failure cleans only the exclusively reserved file with unchanged
identity. They preserve requests, results, occurrences, hashes and first clocks.
Journal and captures are backed up separately; after restoring both, recompute
using the matching capture database before claiming origin verification.

## Error map and compatibility

`JournalError` carries only its fixed category. Input/contract categories from
the existing scoped Discovery allowlist, invalid_profile and conflict exit2.
Local categories input_io, unsafe_destination, storage_missing, storage_schema,
storage_corrupt, storage_locked, storage_timeout, storage_io and
recompute_mismatch exit1. Unknown categories normalize to invalid_field.
SQLite extended error codes map by primary code; no raw message crosses the
boundary. JSON errors stored in a journal become storage_corrupt.

Legacy capture/Discovery APIs, stdout, exit codes and fingerprints remain
unchanged. The journal retains only existing minimal reviewed R0/R1 metadata;
MIT attribution and original acquisition times remain applicable. It acquires
no new source data and implements no delivery or global novelty semantics.
