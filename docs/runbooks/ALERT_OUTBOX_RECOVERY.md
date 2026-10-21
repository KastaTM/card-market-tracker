# Offline Alert Outbox recovery runbook

Authority: [P8a contract](../phases/P8A_OFFLINE_ALERT_OUTBOX_CONTRACT.md).
Commands describe the v1 implementation; executed evidence and limitations are
recorded in [the phase report](../phases/P8A_OFFLINE_ALERT_OUTBOX.md). No network
delivery is authorized. Use explicit IDs from bounded `list` and `evidence-list`
results; no latest-window lookup exists.

1. Keep capture DB, journal DB and alert-outbox DB in private trusted directories and back them up **separately**; ensure enough free disk space for all three snapshots. Preserve sidecars for SQLite recovery; do not delete them manually. Respect actual owner/schema identity when relocating files.
2. Take explicit destination-new backups via `cmt db backup --db captures.sqlite --destination captures.bak.sqlite`, `cmt discovery-journal backup --journal-db journal.sqlite --destination journal.bak.sqlite`, `cmt alert-outbox backup --outbox-db alerts.sqlite --destination alerts.bak.sqlite`. These are three independent consistent snapshots, **not** one distributed timepoint.
3. For restoration, choose fresh nonexisting paths and use corresponding explicit `restore` commands for each DB. Never overwrite an existing file; verify destination ownership, link safety, schema and permissions after copy.
4. Run `cmt discovery-journal verify --journal-db restored_journal.sqlite` and `cmt alert-outbox verify --outbox-db restored_alerts.sqlite`; these certify local self-consistency only. Run `cmt discovery-journal recompute --journal-db restored_journal.sqlite --captures-db restored_captures.sqlite --comparison-id CMP3` for retained comparison, then `cmt alert-outbox recompute --captures-db restored_captures.sqlite --journal-db restored_journal.sqlite --outbox-db restored_alerts.sqlite --alert-id ALT1 --comparison-id CMP3` for at least each association whose source authenticity is asserted. A failure is not `no_discoveries` and must not be silently repaired.
5. `preview` is read-only and offline. Its output is sensitive evidence, not a delivery receipt; `pending` is neither sent nor read. No dispatch process exists in P8a.
6. On corruption/missing database, locked file, deadline, path alias, disk-full or unexpected restart: stop writing, preserve original + sidecars and logs, take a protected forensic copy if feasible, inspect redacted error category, reopen/verify; restore from validated separate backups. Never drop rows/evidence or reset first timestamp to force success. Raise system/operational alert separately from market alerts in a later authorized implementation.
7. Process termination tests demonstrate transaction/reopen behavior only; they do not certify sudden physical power removal on Raspberry Pi. QEMU validates compatibility, not physical Pi reliability. Escalate untrusted-host path races, producer trust and capacity exhaustion to existing TD-003/TD-004 and corresponding owners.

Default operation budget is2s; explicitly choose `--timeout 5` at most when
needed for a copy or full verify. Timeout is failure and must not be described
as a partially verified database. Budgets cooperate with SQLite/application
work and cannot guarantee a deadline against blocked kernel/device calls.
Inspect capacity before copies: no global quota or automatic retention exists.
After a failed init/copy, a reserved destination with any remaining SQLite
sidecar is preserved together with its sidecars. Treat these as recovery evidence;
choose a fresh destination for another attempt and investigate without manually
deleting sidecars. Cleanup only removes its unchanged reserved main inode when
no sidecar remains after SQLite closes.

Safe preview of a selected retained alert:

```sh
cmt alert-outbox list --outbox-db alerts.sqlite --limit 100
cmt alert-outbox preview --outbox-db alerts.sqlite --alert-id ALT1
cmt alert-outbox evidence-list --outbox-db alerts.sqlite --alert-id ALT1 --limit 100
cmt alert-outbox evidence-get --outbox-db alerts.sqlite --alert-id ALT1 --comparison-id CMP3
```

ALT1 and CMP3 are placeholders for complete lowercase IDs, including prefixes.
Lists default to100, cap at1000 and1MiB; pass next_cursor to the following
`--cursor`. A page has its own snapshot, so concurrent inserts before a cursor
will not appear in later pages. Explicit evidence-get returns one full bounded
association. Protect stdout like the database. Existing destinations, aliases,
links and unsafe sidecars fail without overwrite. Preserve the original paths
and file identities while diagnosing failures; never remove SQLite sidecars.
