# WATCHLIST_ALERT_OUTBOX_STORAGE_V1 — frozen engineering SQLite design

**Freeze:** 2026-10-26; Phase Lead review pending. **Implementation/tests:** NOT RUN.
Normative authority: [P8c opening contract](../phases/P8C_OFFLINE_WATCHLIST_SIGNAL_OUTBOX_CONTRACT.md).
See [ADR-0014](../adr/0014-offline-watchlist-signal-outbox.md) and
[API v1](WATCHLIST_ALERT_OUTBOX_V1.md). This document is the SQL and storage
implementation target; it is not phase acceptance or permission to write product
code in the documentation-only freeze step.

## 1. Independent ownership and physical configuration

Owner: card-market-tracker.watchlist-alert-outbox.
application_id: 0x434D5459 (CMTY). user_version: 1. schema_version: 1.
Static source audit at baseline228d5c8d found six existing allocations:
CMT1/0x434D5431/card-market-tracker; CMTA/0x434D5441/alert-outbox;
CMTD/0x434D5444/telegram-delivery; CMTJ/0x434D544A/discovery-journal;
CMTQ/0x434D5451/watchlist-journal; CMTW/0x434D5457/watchlist
(the latter five owner suffixes follow card-market-tracker.).
CMTY is distinct. No migration, prior-store DDL or source writes are permitted.

Use SQLite STRICT tables, DELETE journal mode, synchronous FULL for writable
connections, foreign_keys ON and verified, trusted_schema OFF, defensive mode.
Read connections use an existing URI mode=ro, query_only=ON, explicit BEGIN,
autocommit=True and finally rollback/close. Writable connections use mode=rw,
never implicit file creation. No extension loading, input SQL or dump execution.

## 2. Literal DDL authority

Each sql fence below is ONE ordered STATEMENTS entry, UTF-8 with LF, four spaces
for indentation, no trailing spaces/newline inside the entry and no trailing
semicolon. Statements 1..10 execute in order. Future schema.py must reproduce
these SQL strings exactly; source-language string formatting cannot change SQL.
These are documentary SQL statements, not executed database creation.

Statement 1:

```sql
CREATE TABLE watchlist_alert_metadata (
    singleton INTEGER PRIMARY KEY NOT NULL CHECK(singleton=1),
    owner TEXT NOT NULL CHECK(owner='card-market-tracker.watchlist-alert-outbox'),
    schema_version INTEGER NOT NULL CHECK(schema_version=1)
) STRICT
```

Statement 2:

```sql
CREATE TABLE watchlist_alerts (
    alert_id TEXT PRIMARY KEY NOT NULL CHECK(length(alert_id)=70 AND length(CAST(alert_id AS BLOB))=70 AND substr(alert_id,1,6)='walt1_' AND substr(alert_id,7) NOT GLOB '*[^0-9a-f]*'),
    destination_key TEXT NOT NULL CHECK(length(destination_key) BETWEEN 1 AND 64 AND length(CAST(destination_key AS BLOB))=length(destination_key) AND substr(destination_key,1,1) GLOB '[a-z]' AND destination_key NOT GLOB '*[^a-z0-9_-]*'),
    signal_id TEXT NOT NULL CHECK(length(signal_id)=70 AND length(CAST(signal_id AS BLOB))=70 AND substr(signal_id,1,6)='wsig1_' AND substr(signal_id,7) NOT GLOB '*[^0-9a-f]*'),
    policy_version TEXT NOT NULL CHECK(policy_version='watchlist_synthetic_alert_v1'),
    renderer_version INTEGER NOT NULL CHECK(renderer_version=1),
    channel TEXT NOT NULL CHECK(channel='offline_preview'),
    state TEXT NOT NULL CHECK(state='pending'),
    intent_json TEXT NOT NULL CHECK(length(CAST(intent_json AS BLOB)) BETWEEN 2 AND 65536),
    intent_sha256 TEXT NOT NULL CHECK(length(intent_sha256)=64 AND length(CAST(intent_sha256 AS BLOB))=64 AND intent_sha256 NOT GLOB '*[^0-9a-f]*'),
    message_text TEXT NOT NULL CHECK(length(CAST(message_text AS BLOB)) BETWEEN 1 AND 4096),
    message_sha256 TEXT NOT NULL CHECK(length(message_sha256)=64 AND length(CAST(message_sha256 AS BLOB))=64 AND message_sha256 NOT GLOB '*[^0-9a-f]*'),
    first_prepared_at TEXT NOT NULL CHECK(length(first_prepared_at)=27 AND length(CAST(first_prepared_at AS BLOB))=27),
    UNIQUE(destination_key,signal_id)
) STRICT
```

Statement 3:

```sql
CREATE TABLE watchlist_alert_evidence (
    alert_id TEXT PRIMARY KEY NOT NULL CHECK(length(alert_id)=70 AND length(CAST(alert_id AS BLOB))=70 AND substr(alert_id,1,6)='walt1_' AND substr(alert_id,7) NOT GLOB '*[^0-9a-f]*'),
    evidence_json TEXT NOT NULL CHECK(length(CAST(evidence_json AS BLOB)) BETWEEN 2 AND 262144),
    evidence_sha256 TEXT NOT NULL CHECK(length(evidence_sha256)=64 AND length(CAST(evidence_sha256 AS BLOB))=64 AND evidence_sha256 NOT GLOB '*[^0-9a-f]*'),
    FOREIGN KEY(alert_id) REFERENCES watchlist_alerts(alert_id) ON DELETE RESTRICT
) STRICT
```

Statement 4:

```sql
CREATE INDEX watchlist_alerts_by_destination ON watchlist_alerts(destination_key,alert_id)
```

Statement 5:

```sql
CREATE TRIGGER watchlist_alert_metadata_no_update BEFORE UPDATE ON watchlist_alert_metadata BEGIN SELECT RAISE(ABORT,'immutable_metadata'); END
```

Statement 6:

```sql
CREATE TRIGGER watchlist_alert_metadata_no_delete BEFORE DELETE ON watchlist_alert_metadata BEGIN SELECT RAISE(ABORT,'immutable_metadata'); END
```

Statement 7:

```sql
CREATE TRIGGER watchlist_alerts_no_update BEFORE UPDATE ON watchlist_alerts BEGIN SELECT RAISE(ABORT,'immutable_alert'); END
```

Statement 8:

```sql
CREATE TRIGGER watchlist_alerts_no_delete BEFORE DELETE ON watchlist_alerts BEGIN SELECT RAISE(ABORT,'immutable_alert'); END
```

Statement 9:

```sql
CREATE TRIGGER watchlist_alert_evidence_no_update BEFORE UPDATE ON watchlist_alert_evidence BEGIN SELECT RAISE(ABORT,'immutable_evidence'); END
```

Statement 10:

```sql
CREATE TRIGGER watchlist_alert_evidence_no_delete BEFORE DELETE ON watchlist_alert_evidence BEGIN SELECT RAISE(ABORT,'immutable_evidence'); END
```

SQL length/GLOB/CAST constraints supplement, never replace, strict semantic,
calendar and canonical-JSON validation. Built-in SQL functions only; no Python
UDF or JSON extension is needed. All data SQL uses parameters.

## 3. Exact expected catalog

Compare (type,name,tbl_name,sql) from sqlite_master ORDER BY type,name. Expected
13 objects: three tables, four indexes, six triggers. The table/explicit
index/trigger SQL is expected byte-for-byte equal to the corresponding literal
statement1..10 above; implicit-index SQL is NULL. No whitespace collapsing,
semantic-equivalence tolerance or silent adaptation is allowed. A later
authorized SQLite normalization test must prove that stored SQL equals this
frozen inventory; any discrepancy requires design reconciliation before product
writes. In this freeze the count/names/SQL are STATIC expectations, not a claimed
executed normalization.

| type | name | tbl_name | SQL authority |
| --- | --- | --- | --- |
| index | sqlite_autoindex_watchlist_alert_evidence_1 | watchlist_alert_evidence | NULL |
| index | sqlite_autoindex_watchlist_alerts_1 | watchlist_alerts | NULL |
| index | sqlite_autoindex_watchlist_alerts_2 | watchlist_alerts | NULL |
| index | watchlist_alerts_by_destination | watchlist_alerts | statement4 |
| table | watchlist_alert_evidence | watchlist_alert_evidence | statement3 |
| table | watchlist_alert_metadata | watchlist_alert_metadata | statement1 |
| table | watchlist_alerts | watchlist_alerts | statement2 |
| trigger | watchlist_alert_evidence_no_delete | watchlist_alert_evidence | statement10 |
| trigger | watchlist_alert_evidence_no_update | watchlist_alert_evidence | statement9 |
| trigger | watchlist_alert_metadata_no_delete | watchlist_alert_metadata | statement6 |
| trigger | watchlist_alert_metadata_no_update | watchlist_alert_metadata | statement5 |
| trigger | watchlist_alerts_no_delete | watchlist_alerts | statement8 |
| trigger | watchlist_alerts_no_update | watchlist_alerts | statement7 |

The two alerts autoindexes implement PK and UNIQUE(destination_key,signal_id);
evidence PK creates the third implicit index. Metadata INTEGER PRIMARY KEY has
no autoindex. No AUTOINCREMENT/sqlite_sequence, views, sqlite_stat tables or
additional objects are allowed. Query at most14 guarded catalog rows; compare
the complete ordered inventory including SQL, not names/count alone.
Metadata must be exactly [(1,owner,1)]. Wrong app ID/user_version/mode/owner,
missing/modified/extra schema objects or altered constraints fail storage_schema.
sqlite_stat objects introduced externally are not silently accepted.

## 4. Private paths and guarded reads

Reuse accepted trusted-directory safety behavior without weakening existing
owners: reject UNC/device/ADS/traversal/reserved names, symlink/junction/reparse
ancestors, nonregular or multiple-link DB files and unsafe sidecars. Compare
dev/ino before/after opens. Enqueue/recompute reject every pairwise path/samefile
alias among Watchlist, journal and outbox; input manifest must be a bounded
regular local JSON file. Missing paths are not created. Existing valid sidecars
are preserved for SQLite recovery, never manually removed to force a read.

Before fetching an untrusted TEXT cell into Python use the internal-column
projection CASE WHEN typeof(c)='text' AND length(CAST(c AS BLOB)) BETWEEN
lower AND upper THEN c END. A resulting NULL is corruption for required fields.
INTEGER uses typeof(c)='integer' and runtime exact nonbool ranges. No SELECT *,
coercing CAST-to-TEXT or unchecked large fetchall. Bounds: inventory SQL/name
cells32768; owner128; IDs70; alias64; policy64; renderer integer1; channel32;
state16; intent65536; evidence262144; message4096; digests64; first time27.
Use smaller exact minima/field checks where defined. Runtime must recheck every
value even if SQL constraints/triggers were restored after a test mutation.

Freeze SQLITE_LIMIT_LENGTH=524288 and SQL_LENGTH=65536. The old P5b131072 row
limit must not reject P8c's valid256KiB evidence. These are SQLite ceilings;
per-field guards remain tighter. Byte/node/depth caps and deadline checks apply
before and during parse/canonicalization; type/size faults of stored cells are
storage_corrupt, not public-input failures. Preserve storage_timeout across
parser exception adapters.

first_prepared_at is a valid Gregorian UTC instant exactly
YYYY-MM-DDTHH:MM:SS.ffffffZ (27 ASCII bytes, fixed six microsecond digits).
Generate once at insertion from operational UTC. No cross-alert chronological
ordering is required, and this is never source as_of/observed_at. A privileged
rewrite to another valid operational time is not authenticated by local verify.

## 5. Transactions and replay

Init alone reserves an exclusive new target (requested private mode0600),
rejecting any existing target/sidecar. Under synchronous FULL and BEGIN IMMEDIATE,
execute all ten statements, singleton insert and PRAGMA application_id/user_version;
verify the empty complete store before COMMIT. Failure cleanup examines only
the reserved matching safe inode with no sidecar. No auto-init/repair/migration.

Enqueue repeats source admission even when its alert ID already exists. The
writer consumes the private complete-content-bound receipt once, with the exact
originating Budget object and positive remaining deadline, reconstructs all
derived fields and uses that same command Budget. Private instance/content/
Budget binding and single-use checks precede writer open; wrong identity/reuse
fails unsupported_evidence, an expired valid receipt fails storage_timeout.
A failed writer requires fresh original admission, never receipt reuse. Under BEGIN IMMEDIATE:
1. Check schema, integrity/FKs and selected existing alert/evidence together.
   A one-sided pair is storage_corrupt; never fill or repair it as replay.
   Check the destination/signal unique key cannot resolve to a different ID.
2. For a complete existing pair, validate it semantically. Compare exact alias,
   signal, policy, renderer, channel/state, canonical intent/evidence, their
   hashes, rendered bytes and message hash. Equal means replay with no INSERT,
   UPDATE or DELETE. Preserve the old valid first_prepared_at; do not compare it
   to a newly generated clock. A differing valid frozen pair is replay_conflict;
   malformed stored content is storage_corrupt.
3. Otherwise insert the complete alert and its one evidence row, using the
   column order above. Independently reload/validate that pair and check
   deadline and FKs before one COMMIT. No INSERT OR IGNORE/REPLACE/upsert.
4. Return recorded/replayed only after successful commit/transaction completion.

Two independent identical writers serialize to one recorded and one replayed.
No retry changes evidence, aliases or source selection. Precommit exceptions
roll back completely; rollback disables the expired progress handler and sets
busy wait zero before attempting rollback. Close in finally. Process death before
commit leaves no committed half-pair; SQLite recovery evidence stays intact.
A durable commit can precede a response timeout/crash: exact retry re-admits
originals and resolves this as replay. Do not claim every error means no writes.

## 6. Local reads and complete semantic verification

get/evidence-get/preview operate in one ro snapshot, check owned schema and
integrity/FKs, and reconstruct the selected alert+evidence jointly. They validate
no missing half-pair and return no unverified stored renderer text.
list validates owned schema/integrity and every returned summary's selected pair
within one ro snapshot; output omits bundles and messages. It is not a claim
that all off-page semantic records were checked. Global FK checking remains.
A page failure/timeout returns no partial successful response.

verify and each recovery fold examine the entire store:
1. Exact owned schema/configuration/singleton, integrity_check(1)='ok',
   foreign_key_check empty; stream every alert in alert_id order.
2. Require exactly one evidence per alert and no orphan/extra evidence. Decode
   strict canonical JSON and exact API keysets. Recompute both full P5a snapshots,
   including each snapshot.previous and full results; compare canonical bytes.
3. Recompute P5b sequence/evaluation/signal identities. Require same complete
   immutable entry/product/revision/series, consecutive ordinals, exact successor
   predecessor link, distinct samples, strict observed_at increase,
   nondecreasing as_of and successor.previous equal to predecessor.current.
   predecessor predecessor link is null iff its ordinal is1; otherwise it is
   a valid wje1_ distinct from the retained pair IDs. Retained earlier ancestry
   is not fabricated or claimed to be fully present in a two-evaluation bundle.
4. Reuse unchanged P5b transition semantics: enabled, synthetic, both current
   samples fresh at new as_of, chosen rule predecessor NO_MATCH/current MATCH,
   and exact chosen signal among derived signals. Aggregate OR grants no
   authority. Recompute each P5a result once within a normalized private fold
   where possible, with no cross-fold/cache reuse.
5. Rebuild intent, walt1_ from alias/signal, deterministic render(intent,evidence)
   and all canonical/text hashes. Compare every persisted column/version/state
   and operational timestamp grammar. For repeated watch/revision enforce
   identical complete entry across retained bundles. Check destination/signal
   uniqueness and exact total alert/evidence counts before success.

Local verify does not prove original existence, omitted earlier ancestry,
producer authenticity or privileged-host truth. Recompute independently repeats
source admission against the complete manifest/P5a/P5b originals and compares
the entire selected projection, intent, IDs, versions and message/hashes.
It validates/preserves first_prepared_at without inventing a source proof for
that operational clock. It writes nothing and cannot treat local verify as
origin authority.

## 7. Deadline and bounded operations

One monotonic command deadline default2/max5, finite positive nonbool numeric.
Start before parsing/path/input work. New stages/helper share the same Budget;
unchanged P5a readers get only residual timeout and outer checks. No fresh full
budget per source or recovery stage. Busy/progress handlers, bounded loops,
canonicalization and backup progress observe it. Public success is fully encoded,
byte/deadline checked before first stdout byte. No success page is streamed.

Blocking kernel/IO/stdout calls and a bounded indivisible parser/evaluator call
cannot be forcibly preempted; check immediately afterward. Larger histories or
slower hosts can fail storage_timeout; no partial verify/ok, increased defaults,
global cache or smaller ARM64 acceptance fixture is allowed.

## 8. Exclusive recovery: three folds before publication

Backup and restore share this exact sequence and one Budget:
1. Validate a new destination and trusted parent; open existing source ro with
   BEGIN. Full fresh semantic fold1 verifies that held source snapshot.
2. Exclusively reserve .cmt-watchlist-alert-outbox-<uuid4hex>.tmp in that parent,
   recording dev/ino. Open writable and recheck reserved inode, FULL sync.
3. SQLite backup from the still-held source snapshot in pages32 with a progress
   callback and bounded sleep0.01. Busy handlers observe remaining time; never
   rerun copy with another budget/evidence.
4. In its own copied-connection transaction, perform full fresh fold2. Close
   copy/source connections. Never authorize fold2 using fold1's verdicts.
5. Independently reopen the provisional mode=ro, BEGIN, and perform full fresh
   fold3, checking counts equal fold2. This is the reopened future-destination
   inode, NOT an already exposed final path. Close that connection.
6. Revalidate reserved inode/sidecars; fsync the verified provisional file;
   check remaining deadline. Validate destination still absent and publish
   exclusively with os.link(provisional,destination); unlink provisional.
7. Return counts only after publication completes. Never overwrite any existing
   destination or alter origins/prior stores. A copied outbox is still preview.

No independent verification is replaced by cached normalized content from another
fold. Corruption inserted between folds must be detected before publication.
After source snapshot validation, later appends do not change that held snapshot.

If provisional unlink raises AFTER link, preserve that original error. Examine
BOTH names with lstat: each must match reserved dev/ino, be regular/nonreparse,
have exactly st_nlink=2, and have no -journal/-wal/-shm sidecar. Only then attempt
to unlink the newly created destination link. Suppress compensation errors so
they do not replace the primary error; never retry publication.
Finally remove the provisional only when regular/single-link/nonreparse, owned
dev/ino matches and no sidecar remains. Never remove replacements, a foreign
hardlink or sidecar. No broad path-based/recursive cleanup.

Crash after link/before unlink may leave two names/nlink2, rejected by normal
guards and requiring preserved evidence/manual inspection. Crash after unlink or
response failure may leave a complete valid destination. A successful publication
may precede response-time timeout; explicit verify is the next diagnostic, not
force overwrite or deletion. Persistent filesystem refusal can leave owned
artifacts. Do not promise physical cleanup, hard realtime, parent-directory power
loss durability or native Pi qualification.

## 9. Required failure-first implementation evidence

Not executed in this freeze. Tests must cover: strict owner/configuration/catalog,
every immutable trigger, hostile SQL types/oversize cells before decode, rehashed
invalid results/links/identity/text, missing halves and full counts; real
two-process recorded/replayed race; injected failure between each insertion and
commit; lock/ENOSPC and process termination/reopen; exact stable ancient replay;
local verify versus original-backed recompute; source byte nonmutation.

Recovery probes cover every fold's deadline/corruption, independent connection/
recomputation counts, callback interruption, fsync/link/pre-unlink/post-link unlink
failure, hardlink extras, inode replacements, reparse points, foreign sidecars,
source preservation, no prevalidation exposure and subsequent valid recovery.
Keep original errors and failed evidence. Run unchanged five-checkpoint/four-signal
fixture under installed wheel/Compose/AMD64/ARM64-QEMU, explicit timeout5 allowed.
At least3 backup and3 restore timing controls plus per-stage measurements when
local QEMU is available; otherwise state unavailable and retain mandatory CI.
QEMU is not physical-Pi power-loss evidence.

Traceability: SQL/guards WA04,08,10,12,19; transactions/replay WA06,07,08;
verification/origins WA02,03,04,10,11; paths/recovery/deadline WA08,12,13,14;
fault tests/harnesses WA13,16,17,18. Complete WA01..20 mapping is in API v1.
