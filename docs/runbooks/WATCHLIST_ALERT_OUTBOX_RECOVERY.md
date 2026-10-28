# P8c offline Watchlist alert outbox recovery

CMTY/schema1 is independent of Watchlist/journal/CMTA/CMTD. Pending is a synthetic
preview, never send authority. Protect DB/backups/stdout as private operator data.

1. Quiesce writers; preserve DB and sidecars/permissions/timestamps. Never remove
   sidecars or repair rows/schema to force open.
2. Run cmt watchlist-alert-outbox verify --outbox-db PATH --timeout 5.
   Failure/timeout is not partial verification success.
3. Recompute selected origin correspondence with cmt watchlist-alert-outbox
   recompute --outbox-db PATH --watchlist-db ORIGINAL_WATCHLIST --journal-db
   ORIGINAL_JOURNAL --manifest MANIFEST --alert-id WALT1 --timeout 5.
   Local verify can succeed while missing originals make recompute fail.
4. Backup only to a NEW trusted destination: cmt watchlist-alert-outbox backup
   --outbox-db PATH --destination NEW_BACKUP --timeout 5. Source, copied provisional
   and reopened provisional are independently verified before fsync/publication.
5. Restore only to another NEW destination: cmt watchlist-alert-outbox restore
   --outbox-db BACKUP --destination NEW_RESTORE --timeout 5. Verify then recompute.
   Never overwrite an active store or silently substitute a restored copy.
6. Preserve original errors and unsafe residue. Post-link unlink compensation
   checks both controlled regular/nonreparse inode names, exactly nlink2 and no
   sidecars; foreign replacements/extra links/sidecars remain for inspection.
   Do not force cleanup by altering permissions or deleting names.
7. A response failure may follow a complete insertion/publication. Explicit verify
   or exact original-backed enqueue retry resolves uncertainty; do not invent
   another signal or alias.

Backups preserve first time/pending state and end at their snapshot. No global
multi-DB recovery/copy dedup, Telegram bridge or quarantine lifting is implied.
Process tests and QEMU do not qualify physical Pi electrical durability.


RW-01: writer admission checks the complete retained semantic state within its
write transaction. A new incompatible complete entry for an existing
(watch_id, revision) fails identity_conflict/exit2, even for another alias/series.
The previously healthy store remains byte-identical and verifiable/backupable.
A preexisting contradiction is storage_corrupt, including on replay; no repair,
row deletion, migration or automatic preference rewrite is attempted. Preserve
the store/originals and use only a separately verified known-good backup at a NEW
restore path. Never weaken verify to make an already contradictory store pass.
The full write-time fold shares the original2s/max5s Budget; a large history can
legitimately time out with rollback before COMMIT rather than accept unchecked data.
