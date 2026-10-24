# P5b synthetic Watchlist journal recovery

This new journal is independent of P5a watchlist, Discovery, outbox and
Telegram delivery. **No auto-init/repair or send operation.**

1. Stop local writers; preserve the original DB and any SQLite journal/sidecars,
   permissions and timestamps. Never remove sidecars just to force an open.
2. Run `cmt watchlist-journal verify --journal-db <path>` read-only, with an
   appropriate bounded timeout. A timeout/IO error is a failure, not a clean DB.
3. For original-configuration assurance use explicit
   `cmt watchlist-journal recompute --journal-db <journal> --watchlist-db <p5a>
   --manifest <manifest> --evaluation-id <wje1...>`. This does not authenticate
   a synthetic sample's original human declaration.
4. Produce backup to **new** local path using `backup --journal-db <journal>
   --destination <new_path>`; test `restore --journal-db <backup_path>
   --destination <new_restore_target>` in a separate fresh trusted directory.
   Both commands use journal-db as source and destination as a new output path.
5. Verify restored DB *before* using it, then recompute against original P5a as
   appropriate. Never substitute it silently for the active database.
6. Recovered history ends at the backup point; newer evaluations are not
   recovered. No delivery ledger quarantine changes and no exactly-once claim.
7. Treat any malformed row, owner/version mismatch, broken FK, missing or extra
   signal, changed head, unexplained corrupted preimage, symlink/hardlink or
   unsafe sidecar as an incident. Preserve evidence; escalate instead of fixing
   rows manually. A privileged coherent rewrite can evade this local verifier.

Log only sanitized operation/outcome/category/duration/counts. Stored samples
and saved stdout are sensitive local operator data; handle backups accordingly.
The implementation evidence ledger records executed recovery checks separately;
the procedure alone certifies no test result or physical durability. A successful
commit may precede an output/timeout failure; repeat the exact record request to
resolve uncertainty by deterministic replay without inventing a new observation.
