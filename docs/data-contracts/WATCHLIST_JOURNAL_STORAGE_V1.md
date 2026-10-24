# WATCHLIST_JOURNAL_STORAGE_V1 — independent bounded SQLite

**Status:** PROPOSED v1 implementation contract; gates tracked separately.
Owner `card-market-tracker.watchlist-journal`, SQLite application_id
`0x434D5451` (CMTQ), user_version `1`, no migration or rewrite of CMTW/P5a,
Discovery, captures, P8 outbox or Telegram delivery databases.

## Exact-owner schema plan (freeze inventory in code/contract before DB writes)

The concrete frozen inventory is the literal `STATEMENTS` tuple in
`src/card_market_tracker/watchlist_journal/schema.py`, frozen before storage
implementation as recorded in `docs/phases/P5B_DESIGN_FREEZE.md`. It defines
four STRICT tables, three explicit plus eight implicit indexes and eight triggers
(immutable metadata, sequence identity/no-delete, evaluation no-update/no-delete,
signal no-update/no-delete). The verifier compares all 23 SQLite-normalized
objects including exact SQL. Composite foreign keys bind same-sequence
predecessor/from/to/head references; head's FK is deferred. The table below
describes those implemented statements, whose full types/checks/nullability are
the versioned concrete inventory; no operator-created schema extension is allowed.

Use four `STRICT` tables, version/owner singleton metadata, immutability
triggers, foreign keys and exact known SQL/index inventory. Suggested conceptual
schema (column types/checks/nullability must be reviewed and frozen before
implementation, not silently inferred from this sketch):

| Table | Data and invariants |
| --- | --- |
| `wl_journal_metadata` | singleton=1, owner, schema version |
| `wl_journal_sequences` | PK sequence_id, unique watch_id/revision/policy/series, immutable entry_json/digest, head_eval_id, head observed_at/as_of; head may only advance to a new valid successor |
| `wl_journal_evaluations` | immutable eval_id PK, sequence FK, unique (sequence,current_sample_id), prior_eval_id nullable FK, canonical snapshot/preimage, recomputed result JSON, observed_at, as_of, originally persisted_at, monotonically assigned local ordinal per sequence |
| `wl_journal_signals` | immutable signal_id PK, sequence+rule+from/to eval FKs, canonical identity/body, unique (sequence,to_eval,rule); no sent state |

Reject unrecognized tables, indexes, triggers, altered owner/version,
missing/extra constraints, schema object SQL mismatches and malformed/rehashed
rows. Use CHECKs for critical shape/length, FK ON, owner singleton, exact
catalog-inventory comparison and application_id/user_version check. Preimage and
result cells <=65536 UTF-8 bytes, public input <=1MiB. Persisted `entry_json`
must be stable across all series of `(watch_id, revision)`; deep verifier checks
this cross-series constraint and all hashes/results, not just stored indexes.

## Atomic append and replay

One `BEGIN IMMEDIATE` transaction reopens selected sequence/head, checks exact
replay first, then checks strict chronology, nondecreasing as_of, unique
sample_id, previous equality, entry/config identity and predecessor CAS under
the same SQLite write lock. Insert one immutable evaluation, all independently
derived signals (zero or more), update head/ordinal, commit. Foreign keys are
enabled, and the transaction rolls back completely on injected failure,
conflict, lock timeout, disk exhaustion or SQLite error. Two processes with
identical normalized evaluation: exactly one commit, one replay. Two divergent
successors: at most one commit; other fails, no silent automatic adoption of
latest. No partial signal count or success output before COMMIT.

Older replay returns original eval ID/persisted_at/signals, does not move head.
Same sample_id but a different as_of/content/previous must fail rather than
create a new evaluation. Same observed_at with different current sample also
fails. Older backfill/reordering impossible without an explicit future contract.

## Deep verification

`verify` is read-only and examines the **whole** history within one 2s default
(5s maximum) cooperative operation budget. It validates sqlite quick/integrity
check and FKs; owner/application_id/version, exact tables/indexes/triggers; all
JSON cells with strict P5a parsers; canonical preimage/IDs; every P5a evaluation
result recalculated; unique sample and ordered link chain; continuity and
per-rule signal fold; exact stored signals including no surplus/missing rows;
sequence head/current ordinal. A timeout is a failure, **never** a partial PASS.

`recompute` selects an explicit evaluation ID, uses a distinct and explicit
original Watchlist DB and full manifest, reloads exact revision, compares
entry/identity/config and reruns P5a using retained samples. Missing original
revisions or changed identity cause failure. Local verify can pass even if P5a
origin is unavailable; recompute then fails. Neither proves commercial source
authenticity or resists a coherent privileged rewrite of all authorities.

## CLI contract and resource limits

`cmt watchlist-journal {init,record,get,list,signal-get,signal-list,verify,
recompute,backup,restore}`; each operation takes `--journal-db`. Record and
recompute additionally take `--watchlist-db` and `--manifest`. Record requires
`--watch-id`, exact `--revision`, `--sample`, optional `--previous`, explicit
`--as-of`. Recompute/get use `--evaluation-id`; signal-get uses `--signal-id`.
Lists allow sequence/watch/revision/rule filters as relevant; page limit default
100, maximum1000, serialized output <=1MiB; opaque keyset cursors bind filter
and sort and are bounded to2048 bytes. No implicit init/list-all-watchlists.

Evaluation list order is ascending evaluation_id; signal list order is ascending
signal_id. Both accept --sequence-id, --watch-id and --revision; signal-list
additionally accepts --rule price|restock. Cursors bind operation, order and all
filters. Each page is its own read snapshot. A byte-limited page retains an
opaque continuation cursor instead of truncating evidence. get returns
`{version,operation,result:ok,evaluation}`; evaluation contains evaluation_id,
sequence_id, predecessor_evaluation_id, ordinal, persisted_at, snapshot,
evaluation_result and signal_ids. signal-get returns the exact signal body under
`signal`, including signal_id. Lists use evaluations/signals and next_cursor.
verify/backup/restore return counts of sequences/evaluations/signals. init returns
schema_version1. recompute returns evaluation_id and the freshly derived
evaluation_result. Record response is specified in WATCHLIST_JOURNAL_V1.
All success outputs include version1 and operation. Error output includes
version1, operation, result:error and fixed error_category; invalid input/context/
conflict exits2 and local path/storage/IO/deadline failure exits1. Success exits0,
including replay and rule outcomes. Shared P5a/catalog/path/storage error categories
are reused without raw values. A failure after commit can be resolved by repeating
the exact record request and receiving deterministic replay.

Total time budget includes parsing, lock wait, SQL, copying, verification and
result formatting; finite >0..5s, default 2s. Public JSON parsing: max1MiB,
depth16, nodes20000, string1024, no duplicate keys/NaN; narrower P5a field
limits win. Local canonical record <=64KiB. Redacted JSON logs only operation,
category, outcome, duration and counts. Stdout/DB/backups hold sensitive local
price/preferences data and need operator access controls. No sockets opened by
product commands or offline harness.

## Recovery and threat boundary

Use existing P5a trusted-directory and inode/sidecar protections; SQLite
DELETE journaling + FULL sync or documented equivalent. Backup: consistent
verified snapshot to a newly reserved exclusive path; restore: validate
provisional copy **before** atomically exposing a new destination, and refuse
existing destination/sidecars. Never delete another process's journal/sidecars,
clobber CMTW, or imply cross-DB recovery. Recovery is as of backup time;
post-backup evaluations are not restored. Simulated process interruption and
reopen smoke are required; real Pi/power-loss assertions remain out of scope.

Testing: unit/contract/fixtures for bad formats, duplicates, conflicts,
missing/mutated row/signal/head, expiration, two-process race, rollback,
read-only recompute, path collisions, disk/lock errors and nonmutation checks;
undécimo installed-wheel process smoke; existing ten unchanged; CI Quality,
Compose, AMD64, ARM64/QEMU all PASS before readiness.
