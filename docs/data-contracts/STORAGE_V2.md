# Offline SQLite storage v2

Status: P1b implementation candidate; supplements historical STORAGE_V1 without
rewriting its accepted evidence. Standard-library sqlite3, no ORM/dependencies.

Ownership keeps application_id 0x434d5431 and owner card-market-tracker.
user_version and singleton storage_metadata.schema_version are 2. Exact schema
inventory/SQL, foreign keys and DELETE journal mode are required. Unknown/future
versions fail. Reads accept exact v1/v2 without migration; initialize(existing v1)
returns schema_version 1 unchanged, while new initialization creates v2 atomically.

Entities and batches retain v1 columns/constraints and historical identity
relationships, UUIDs, timestamps, result snapshots and original fingerprints.
Records retain v1 shape and indexes, except provenance permits synthetic or
observed. That SQL enum is not authorization: independent application admission
allows observed only from the exact reviewed pinned bundle.

New STRICT table captures has batch_id primary key/FK to batches, mode
legacy/synthetic/pinned, evidence_state, bounded canonical envelope TEXT and
64-character SHA256 capture_fingerprint. Modes map exactly to legacy_unverified,
producer_declared, verified_local_pinned_bundle respectively. Envelope has at
most 1,000,000 encoded characters and application generic JSON bounds. Readers
check SQL UTF-8 byte length before materializing envelopes, bounded to 1,000,000
bytes, then apply lexical depth/node/string limits before complete JSON decoding.
These guards remain effective when a corrupting writer bypasses SQL CHECKs. Every v2
batch must have one capture. SQL triggers reject UPDATE/DELETE of capture rows.
API writes append frozen batch/record/entity evidence and do not overwrite it.
New real/scoped synthetic batch fingerprint covers its canonical envelope;
context_fingerprint covers its retained resolver context. Legacy hashes retain
v1 rules and are never recalculated from inferred scope or a new manifest.

Migration is explicit `migrate(path, destination)` and only accepts exact v1.
It acquires BEGIN EXCLUSIVE, performs schema/integrity/FK preflight, reserves the
backup destination with O_EXCL and existing path/link/sidecar checks, copies the
stable original main file in bounded chunks, flushes/fsyncs, then opens/verifies
that v1 backup. Under the held exclusive lock and required DELETE journal mode,
main bytes cannot change. This avoids deadlocking SQLite backup against the same
source transaction. General backup/restore retain the SQLite backup API.

Only after backup verification does transactional DDL rebuild the records CHECK,
recreate its exact indexes/trigger, add capture tables/triggers, backfill every
old batch with legacy_unverified/scope null, and publish both version markers.
All rows copy with INSERT SELECT unchanged. Final integrity/schema/capture checks
precede SQL COMMIT. Any error, timeout or interruption rolls back to complete v1;
verified original backup survives. A failed unverified owned backup is cleaned.
Existing backup destinations are never overwritten. A concurrent reader/writer
may cause bounded storage_locked; migration is not automatic conflict recovery.
Process termination recovery uses SQLite's rollback journal, never manual journal
deletion. Tests do not claim native Pi power-loss durability or honest hardware.

Verify checks exact inventories, SQLite integrity/FKs and one capture per batch.
For new captures it reparses the reviewed bundle or synthetic scope, revalidates
retained manifest, reconstructs resolution and compares scope/snapshot/digests,
counts/times and stored entity parent closure. Legacy batches receive complete
snapshot/identity consistency checks but no claim of recoverable original
manifest or independent scope. Alterations fail storage_corrupt/storage_schema;
they are not accepted as empty. Ordinary source queries also validate v2 capture
evidence and return no partial corrupted rows. Finite operation budgets cover
whole integrity work, not just selected output; large histories can time out.

Backup and restore require verified compatible v1/v2 sources and newly reserved
destinations, copy consistently using SQLite backup API, verify and reopen before
success. V2 evidence and replay hashes survive restoration. Failed partial owned
copies are removed; unrelated paths are untouched.

P4a read_snapshots remains synthetic-only. Selected pinned admission or any
observed/mixed row causes synthetic_only before comparison; rows are never
silently filtered. Selected v2 synthetic/legacy capture envelopes are independently
validated in the same read snapshot before comparison, using only retained
resolver context. Valid scope and rows cannot be combined across writer commits. Real temporal Discovery needs a separate future contract.
