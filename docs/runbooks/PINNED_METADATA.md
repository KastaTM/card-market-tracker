# Offline pinned metadata and explicit migration

Read the [P1b contract](../phases/P1B_PINNED_METADATA_INGESTION_CONTRACT.md),
[bundle](../data-contracts/PINNED_REPOSITORY_BUNDLE_V1.md),
[capture](../data-contracts/CAPTURE_SCOPE_V1.md) and
[storage](../data-contracts/STORAGE_V2.md). Use an operator-owned private
directory with space for DB, journal and backups. Installed import needs no network.

```sh
cmt bundle verify --input tests/fixtures/pinned_repository_bundle_v1.json
cmt db init --db /private/history.sqlite3
cmt bundle import --db /private/history.sqlite3 --input tests/fixtures/pinned_repository_bundle_v1.json --manifest tests/fixtures/synthetic_manifest.json --batch-id bd9cc4b8-eace-4567-8364-93cc4eccddc5
cmt captures --db /private/history.sqlite3 --batch-id bd9cc4b8-eace-4567-8364-93cc4eccddc5
cmt observations --db /private/history.sqlite3 --batch-id bd9cc4b8-eace-4567-8364-93cc4eccddc5
cmt db verify --db /private/history.sqlite3
cmt db backup --db /private/history.sqlite3 --destination /private/history.backup.sqlite3
cmt db restore --db /private/history.backup.sqlite3 --destination /private/history.restored.sqlite3
```

The supplied synthetic manifest has no repository bindings: four candidates
retain evidence without CMT IDs. Newly stored mixed/candidate import exits 3.
Curators can supply explicit consistent set bindings; the importer never creates
bindings. Card finish remains unknown. Same token/context replays with exit 0,
zero writes and original first-persistence time. Changed manifest/context with
the same token exits 2 (`replay_conflict`), preserving history. Stable token loss
loses retry deduplication. Offline reimport never redates acquisition/capture
or becomes a new live observation. Query stdout is explicit bounded metadata;
logs exclude names, paths and tokens.

Existing schema1 remains schema1 under init/read/verify. To migrate:

```sh
cmt db verify --db /private/legacy.sqlite3
cmt db migrate --db /private/legacy.sqlite3 --destination /private/legacy.v1.backup.sqlite3
cmt db verify --db /private/legacy.sqlite3
```

Migration verifies v1, holds an exclusive transaction, creates an exclusive
verified original backup, then atomically publishes v2. Backup and sidecar paths
must be absent; nothing is overwritten. Historical rows, UUIDs, timestamps and
fingerprints remain exact. Legacy scopes stay explicitly unverified, including
request-attested empty history. Read/verify never upgrades; future/altered schemas fail.

On lock/timeout/IO failure preserve DB and journal, check permissions/free space,
then retry explicitly. Do not delete a hot journal or reset corruption. Rollback
restores verified v1 backup into a new path rather than deleting v2 history.
Backup/restore support v2 and verify capture relationships. Exit 1 is local IO
or storage failure; exit 2 is invalid data/policy/context. Neither is valid empty.

Discovery and PERSISTENCE_V1 stay synthetic-only. Observed/mixed Discovery
selections fail. Context proves reviewed local validation, not total catalog
coverage, product absence, current availability or independent producer truth.
Pi power-loss behavior remains unqualified. Engineering acquisition is separate:
four fixed paths only, eight-request shared budget, no shipped fetcher or scheduler.
