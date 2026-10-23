# Watchlist recovery

P5a operates one independent watchlist SQLite file. Its
[storage contract](../data-contracts/WATCHLIST_STORAGE_V1.md) and
[watchlist contract](../data-contracts/WATCHLIST_V1.md) define local verification,
CAS and replay. Recovery never writes previous capture/journal/outbox/delivery
databases and never sends a notification. Product network budget is zero.

## Before recovery

Use a private operator-controlled directory with trusted ancestors and suitable
host ACLs. Stop other watchlist writers while investigating corruption or choosing
which recovered file will become the sole authoritative store. Keep the original
database and its journals as evidence. Do not edit rows, delete sidecars, run
arbitrary SQL dumps, change owner/schema markers or bypass constraints to make
verification pass. Copying a live main file alone is not a consistent backup.

Record the application version, categorized failure and chosen source/target
privately. Logs deliberately omit paths, preferences, tokens, samples and raw
exceptions. Do not paste local database/query output into a public issue. Check
disk capacity for original plus snapshot/provisional copy and recovery headroom;
automatic quotas/retention are not implemented.

## Verify and back up

Use explicit `cmt watchlist verify --watchlist-db <existing-db>`. Verify requires
an existing owned schema and checks full history/request/current consistency,
foreign keys, canonical identity and configuration. Failure or timeout is not
partial success. A locked database requires stopping competing work or retrying
within the documented finite budget, never an unlimited timeout. Missing files
are errors; only explicit init creates a new empty store.

Use `cmt watchlist backup` with the existing source and a new destination as
shown below. The command takes a consistent SQLite
snapshot, verifies/reopens the result and refuses existing destination/sidecars.
Protect the resulting file: it contains canonical targets, operator preferences,
request tokens and immutable revision history. Keep a privately recorded verified
backup and do not confuse an evaluation JSON result with a recoverable database.

```text
cmt watchlist verify --watchlist-db watchlist.sqlite
cmt watchlist backup --watchlist-db watchlist.sqlite --destination watchlist-backup.sqlite
cmt watchlist restore --watchlist-db watchlist-backup.sqlite --destination watchlist-restored.sqlite
cmt watchlist verify --watchlist-db watchlist-restored.sqlite
```

## Restore to a new path

1. Select a previously verified watchlist backup and a new destination in a
   trusted directory. Preserve the damaged/original store and valid sidecars.
2. Run explicit restore with the backup as --watchlist-db and a new --destination.
   It validates/reopens/fsyncs a provisional copy before exclusive publication.
   Existing targets are never overwritten. Categorized failure leaves no usable
   unverified destination; investigate before retrying.
3. Run verify on the restored path and inspect get/list/history outputs privately.
   Confirm the expected watch IDs, latest revision pointers, rules and history.
   A coherent snapshot can legitimately lack operations committed after its backup;
   local integrity cannot prove it is the newest store.
4. Choose that verified path explicitly for future watchlist commands. Preserve
   the prior evidence until the recovery decision is recorded. Never independently
   write both copies as if they shared a single CAS/replay authority.

An old token replay reports the original operation only when the restored history
contains that token. It does not synchronize omitted newer operations with another
file. Reconcile intended preferences through ordinary validated commands and
current expected revisions; there is no merge/force/history-rewrite operation.
Evaluation remains read-only against selected revisions and explicit synthetic
samples; restore neither schedules evaluation nor creates events.

## Limits and escalation

Do not substitute a foreign/future schema, extend deadlines above5 seconds or
disable deep verification. Record a capacity/verification-budget issue for
DB-OWNER/SRE if a valid growing history no longer fits. Unresponsive OS/device IO
may exceed cooperative deadlines. Link/inode guards rely on trusted ancestors;
Windows ACLs are operational controls (TD-003). Process-kill/fault-injection or
ARM64 QEMU results do not establish native Pi electrical durability (TD-002).
No hash authenticates an administrator controlling manifest, database and code.
TD-001..TD-005 remain OPEN. Only the Orchestrator can authorize new retention,
migration, shared-writer deployment or phase closure.
