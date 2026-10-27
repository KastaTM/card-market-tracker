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
