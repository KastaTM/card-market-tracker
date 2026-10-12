# Offline SQLite storage and read contract v1

Status: adopted for implementation; gates pending. Implementation is standard-library
SQLite, single host/one writer/local filesystem, synthetic-only. No curator,
promotion, market schema, analytics or destructive cleanup capability exists.

## Schema and invariants

Ownership uses application ID `0x434d5431` (CMT1), `user_version=1` and singleton
`storage_metadata` with owner `card-market-tracker` and schema version 1.
The complete known schema object inventory/SQL definitions must match before
operations. Additional tables/views/triggers/indexes, altered constraints,
missing objects, mismatched ownership/version and future schema fail
`storage_schema` without initialization/reset. Empty means no user schema and
zero application/user versions. Initialization DDL+metadata+version publication
is a single transaction. Current version initialization is a no-op.

| Table | Stored fields and purpose |
| --- | --- |
| storage_metadata | Singleton owner and version marker |
| entities | CMT UUID, kind, set/card parent UUID, textual number, language/null, variant, sealed type; immutable projected identity only |
| batches | Stable UUID token, input/resolver version, normalized capture, first local persistence instant, input/context SHA256, safe processing counts/result |
| records | Batch FK plus input index PK, status/category/target FK, normalized evidence columns for accepted/candidate or all null evidence for rejection |

Canonical localization names and release-date metadata are not entity identity
columns. Release dates observed belong to record snapshots and resolver-relevant
manifest metadata participates in the context hash. Identity equality includes
kind and every relationship/discriminator including exact nulls and sealed type.
An existing UUID with another projection fails `identity_conflict`; another UUID
claiming existing card `(set_id,card_number)` or printing
`(card_id,COALESCE(language,''),variant)` also fails. No upsert/reassignment exists.
Parent closure is inserted parent-first. Foreign keys enforce existing parent,
batch and target; fixed insert triggers enforce set/card parent kinds and
observation target-kind compatibility. SQL CHECKs enforce enum/null/shape/length,
synthetic provenance and accepted/candidate/rejected evidence combinations.

Records contain source kind, exact reference namespace/kind/ID/language/variant,
name, optional set-reference components, textual card number, release date,
provider update, capture and synthetic provenance. Set-reference absence is an
all-null tuple. Rejections carry no reference/name/target/provenance/timestamps.
Accepted category is null; candidate category is allowlisted and target null;
rejected category is allowlisted. Record indexes are 0..999 and batches max1000.
Capture must be required UTC; datetime/date correctness and token grammar are
validated by Python, with basic storage bounds/checks as defense in depth.

Indexes support `(captured_at,batch_id,index)`, target+ordering and candidate exact
reference+ordering, in addition to PKs and identity uniqueness. Candidate language
null is exact equality (`IS` parameter semantics), never a wildcard.

## Public operations

Functions in `persistence.sqlite_repository`:

- `initialize(path: Path) -> dict[str, object]`: create/initialize empty or validate current.
- `persist(path: Path, batch: PersistenceBatch) -> WriteResult`: independently revalidate then atomic insert/replay.
- `query(path: Path, *, batch_id: str|None=None, cmt_id: str|None=None, candidate_reference: ExternalReference|None=None, limit: int=100) -> dict[str, object]`.
- `verify(path: Path) -> dict[str, object]`: owned schema, integrity and FK checks.
- `backup(source: Path, destination: Path) -> dict[str, object]`.
- `restore(source: Path, destination: Path) -> dict[str, object]`: verified SQLite backup operation into separate new DB.

At most one query filter is allowed; no filter returns bounded history. Limit
must be strict integer 1..1000, never bool. UUID/reference filters receive the
normal boundary validators. Result order is ascending
`(captured_at,batch_id,index)`; rejected summaries have batch capture as effective
sort capture. Query result `{version:1,result:ok|empty,records:[...]}` contains
batch_id/index/status/category/cmt_id, complete observation/null and the batch's
first_persisted_at. Batch filter includes safe rejected rows; target and candidate
filters include only matching admitted snapshots. Read does not claim completeness
beyond its limit and never changes identity, versions or record state.
Verification returns `{version:1,result:ok,schema_version:1}` after both
`PRAGMA integrity_check` and `PRAGMA foreign_key_check` succeed. It is database
integrity only, not source or whole-host health. Operation results omit paths.

Use new, closed connections per operation with explicit foreign keys checked.
Read/verify/backup source open URI `mode=ro` with query_only; missing file fails
storage IO and creates nothing. Write opens read-write only for an existing
regular safe file and read-write-create only for a new checked path. Values are
SQL parameters; query fragments are fixed. No source SQL/dump/extensions execute.
Writers verify ownership/schema/journal before mutations. `DELETE` journal and
`FULL` synchronous are explicit. Each SQL statement receives remaining lock
budget and VM interruption; SQL BEGIN/COMMIT/ROLLBACK define transactions.

## Deadlines, paths and recovery

Default lock/operation budget is 2 seconds (maximum supported 5 seconds), without
unbounded retry. Public operations accept an optional `timeout` keyword in the
strict range greater than zero and at most five seconds; the CLI uses the default.
Lock contention is `storage_locked`; exhausted operation budget
is `storage_timeout`. An unresponsive OS/device call is outside this bound.
Other categories: `storage_schema`, `storage_io`, `storage_corrupt`,
`unsafe_destination`, `replay_conflict`, `identity_conflict`. Storage errors carry
only fixed categories, no original exception text or SQL. Corruption/IO never
becomes an empty read. Simulated IO/full failures are labeled simulated evidence.

DB/backup/restore paths must be normal local files: reject links/reparse points,
linked ancestors, directories and special files. Existing write DB must have
one hardlink. Backup/restore destination must not exist (including broken links),
its parent must already exist, and it cannot equal or alias the source. Reserve
only after rejecting any existing destination `-journal`, `-wal` or `-shm`.
Existing writable DB journals must also be regular, unlinked files; a valid hot
rollback journal is preserved for SQLite recovery, never removed manually. Reserve
with exclusive creation and restrictive requested mode 0600 (host ACL semantics
apply on Windows), check identity before opening SQLite, and do not overwrite.
Trusted directories and OS permissions remain the local security boundary;
portable checks cannot prevent a privileged hostile ancestor replacement race.

Backup verifies source schema/integrity/FKs, uses `Connection.backup` in bounded
page chunks with deadline progress callback and <=50ms busy retry sleep, then
verifies destination schema/integrity/FKs, closes and reopens. Failed copy does
not yield success and removes only its own newly reserved file/sidecars after
identity checks. Restore uses the same safety and consistency checks into a
new destination; it never overwrites the source or any user DB. Successful result
is `{version:1,result:ok,schema_version:1}`. Tests prove observations/IDs/candidates,
first persistence and stable replay survive both backup and restore.

Rollback journal may be present during an interrupted transaction. Do not remove
it manually; SQLite recovery must run in a writable trusted directory. Read-only
open may fail if journal recovery requires writes. No automatic corrupt repair,
reset, database deletion or retention cleanup exists. Tests use temporary DBs;
process rollback/restart and QEMU evidence do not certify physical Pi power loss.

## Evolution

Only initial schema version 1 exists. No fabricated migration is shipped.
A future contract must define tested migrations before another version opens;
current software rejects it conservatively. Historical snapshots remain frozen
when a later manifest changes; candidate promotion requires another phase.
