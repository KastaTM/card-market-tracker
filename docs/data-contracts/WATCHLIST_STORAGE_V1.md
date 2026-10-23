# Watchlist storage v1

Independent P5a SQLite storage. application_id=0x434D5457 (CMTW), user_version1,
owner=`card-market-tracker.watchlist`; explicit
init only. No previous database, schema, canonical ID or capture is migrated or
written. See [watchlist](WATCHLIST_V1.md),
[ADR-0012](../adr/0012-watchlist-offline-rules.md) and
[recovery](../runbooks/WATCHLIST_RECOVERY.md). This contract establishes requirements,
not gate results or physical durability certification.

## Owned schema and invariants

Four STRICT tables retain ownership metadata, stable entries/current pointers,
immutable full revisions and immutable request records. Metadata/application_id/
user_version, exact tables/indexes/triggers, CHECK/UNIQUE constraints and foreign
keys distinguish this store from missing, foreign, future or modified databases.
Unknown schema objects are errors, not ignored extensions. Immutability triggers
forbid modification/deletion of revision and replay history. A privileged coherent
rewrite can evade local consistency checks; this file is not a signed audit log.

| Object | Stored content / purpose |
| --- | --- |
| watchlist_metadata | Exactly singleton1, owner and schema_version1 |
| watchlist_entries | watch_id, unique cmt_id, identity_json/digest, current_revision, priority_rank and enabled |
| watchlist_revisions | Composite (watch_id,revision), entry_json, action and unique request_token |
| watchlist_requests | request_token, command_json/digest, watch_id/revision; unique operation pair |
| watchlist_by_priority | Index on (priority_rank,watch_id) |

Six triggers are watchlist_identity_immutable, watchlist_entries_no_delete,
watchlist_revision_no_update, watchlist_revision_no_delete,
watchlist_request_no_update and watchlist_request_no_delete. Identity trigger
also requires the current pointer to advance by exactly1. Exact inventory
includes implicit indexes and normalized SQL, without extra objects. Deferred
foreign keys allow entry/current, revision and request circular links to be
created in the same transaction; committed consistency is mandatory.
Stored identity/entry/command JSON cells cap at65536 UTF-8 bytes, tighter than
the public1MiB input limit. Schema cells cap at32768, cursor input at2048.

One watch_id per CMT ID and canonical identity digest must agree with the
[watchlist projection](WATCHLIST_V1.md). Revision numbers start at1, are contiguous,
and are immutable. The current pointer identifies the latest committed revision.
Every revision and request agrees on target, complete configuration, canonical
identity and operation precondition. Replay digests are checked against complete
canonical content; a correct hash over malformed content is not valid history.
Every committed revision has corresponding request evidence and every request
references its original committed operation. No sample, observed price, previous
sample, evaluation result, event, destination or transport state is stored.

## Writes and replay

All mutations revalidate complete public values. One BEGIN IMMEDIATE transaction
checks replay, checks CAS, inserts immutable revision/request and moves current
pointer atomically. Add requires expected_revision0; updates require the exact
current revision. Conflict, interruption or failure rolls the operation back.
No caller-visible successful count precedes commit. Same request token with
equivalent normalized command returns original operation without adding history;
different content is replay_conflict. Old replay after a newer mutation does not
move current backwards. No hard delete, retarget or implicit schema repair exists.

SQLite foreign keys are enabled and checked; DELETE journaling/FULL sync follow
the existing local storage pattern. There is no cross-database transaction or
atomic manifest+watchlist commit. Host-controlled immutable manifest input is the
trust boundary between admission and the watchlist transaction.

## Reads, verification and resource limits

Reads use an existing read-only/query-only connection and a consistent snapshot;
missing paths are not created. Deep verification checks exact owned inventory,
quick/integrity and foreign-key results plus all identity, canonical JSON,
config, revision-contiguity, replay and current-pointer invariants. Corruption,
foreign/future schema, busy locks, IO faults and timeouts are categorized failures,
never empty/partial successful results. A timed-out verification cannot pass.

List keyset order is priority_rank high0/normal1/low2 then watch_id. History order
is ascending revision. Cursor validation binds query filters/context and ordering
position. Pages default100/max1000 and cap encoded output at1MiB. Separate pages
are separate snapshots, so concurrent changes can affect later pages. SQL data
uses parameters; input never supplies SQL fragments or extension/dump commands.
Validate scalar type/size before loading potentially hostile stored content.

One total cooperative budget covers lock waits, VM work, validation and copy:
default2 seconds, explicit finite positive maximum5 seconds. Busy/progress
callbacks and copy steps share the deadline rather than restarting it per
suboperation. A blocked
OS/device call that does not return remains outside a hard time guarantee.
Whole-history validation can reject larger files within this finite budget;
there is no unbounded fallback, automatic retention or quota.

## Paths, backup and restore

Use private trusted operator-controlled local directories. Reject unsafe local
path forms, directories/special files, symlinks, reparse/junction ancestors,
multiply linked files and unsafe sidecars. Preserve valid journals for SQLite
recovery; never delete a sidecar to force open. New init files and provisional
copies are exclusively reserved, and existing destination/sidecar collisions
are rejected. Request private
file permissions; Windows ACL enforcement remains the operator's responsibility.

Backup and restore both copy a consistent verified SQLite snapshot using the
backup API into an exclusively reserved random provisional file in the target's
trusted parent. They fully check/reopen the copy, fsync its inode, then publish
it at the new path using exclusive os.link and remove the provisional name.
The destination name is exposed only after validation. Existing destinations
are never replaced. A filesystem without hard-link support fails safely.
Failure cleanup removes only files reserved by that invocation after identity
checks; unrelated files/evidence stay untouched. Watchlist restore does not
restore or mutate capture/journal/outbox/delivery files. No atomic multi-file
backup, transport action or automatic resume is implied.

Portable pathname checks assume trusted ancestors and cannot defeat a hostile
administrator replacing directory components concurrently (TD-003). Backups
contain preferences/history/tokens and need host protection. Capacity and recovery
headroom (TD-004), native Pi power-loss qualification (TD-002), and all previous
TD-001..TD-005 owners/exits remain open. Integrity is local consistency, not
producer authenticity, source health, independent completeness or hardware proof.
