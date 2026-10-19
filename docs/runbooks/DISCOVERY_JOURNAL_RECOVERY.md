# Discovery journal operation and recovery

Use private, operator-controlled local directories and protect stdout, captures,
journal and backups. POSIX new files request0600; containers run UID/GID10001 with
data mode0700, networking disabled and fixtures read-only. Windows ACLs remain
the operator's responsibility. Do not use shared/untrusted directories (TD-003).

The [journal API](../data-contracts/DISCOVERY_JOURNAL_V1.md),
[storage contract](../data-contracts/DISCOVERY_JOURNAL_STORAGE_V1.md) and
[ADR0009](../adr/0009-discovery-result-event-journal.md) bind this workflow.
Captures remain the separate schema2 five-table SQLite file. Journal init creates
an independent v1 file with its own owner/application_id and three tables.
Neither path may alias the other. Links, unsafe ancestors, hardlinks, existing
new destinations and sidecar collisions are rejected without overwriting them.

```text
cmt discovery-journal init --journal-db JOURNAL
cmt discovery-journal record --journal-db JOURNAL --captures-db CAPTURES --request V3_REQUEST
cmt discovery-journal get --journal-db JOURNAL --comparison-id CMP3
cmt discovery-journal list --journal-db JOURNAL --limit 100
cmt discovery-journal event-occurrences --journal-db JOURNAL --event-id EVT3 --limit 100
cmt discovery-journal verify --journal-db JOURNAL
cmt discovery-journal recompute --journal-db JOURNAL --captures-db CAPTURES --comparison-id CMP3
cmt discovery-journal backup --journal-db JOURNAL --destination NEW_BACKUP --timeout 5
cmt discovery-journal restore --journal-db NEW_BACKUP --destination NEW_RESTORE --timeout 5
```

Use explicit requests from the [multi-revision workflow](MULTI_REVISION_METADATA.md);
no latest capture/history selection exists. Record does not initialize. Reusing
identical semantic input returns replay and preserves first_recorded_at. Do not
change clocks or source data to force an insertion. The same evt3 may appear in
several comparison windows; inspect its paginated occurrences and each parent's
full evidence. Baseline/no_discoveries are valid zero-event results. Errors are
failures, never evidence of absence or source health.

After a process interruption, preserve SQLite sidecars for normal engine recovery;
never manually delete rollback journals. Reopen and run local verify. If it fails,
preserve the files and logs for diagnosis and restore a separately verified backup
to a new safe destination. No automatic repair, migration or destructive cleanup
is provided. Lock/deadline errors are bounded; explicit retry must retain the
same intended request rather than dropping history or checks.

Backup/restore use SQLite's consistent backup API, validate the source snapshot,
then validate and reopen the destination before success. Existing destinations
are never overwritten. Failed owned partial copies are removed; unrelated files
are preserved. There is no atomic joint backup of journal and captures: back up
captures separately using [observation storage](OBSERVATION_STORAGE.md), verify
each file, then recompute explicit journal comparisons against restored captures.
Missing captures or mismatch is a failed origin check even when local verify
passes. Do not erase/rewrite the journal to hide a mismatch.

Local verify confirms bounded schema/JSON/digest/relational consistency only.
Recompute additionally rereads the original immutable capture evidence. Neither
authenticates an administrator who controls both files or establishes external
source truth. Retained real v3 evidence derives from the existing licensed minimum
package; preserve its packaged MIT notice and existing attribution. No additional
upstream source bodies are acquired or stored.

Operations default2s with explicit maximum5s across cooperative work; OS/device
stalls are outside the guarantee. Large append-only journals can exhaust time or
disk; monitor capacity and reserve recovery space (TD-004). Do not interpret
partial scans as PASS. Per-result16MiB and summary-page1MiB caps may reject a pure
v3 result that is otherwise valid; no partial row is stored. Keyset pagination is
live across pages, not a frozen snapshot. No quotas or retention are implemented.

The seventh `scripts/discovery_journal_smoke.py` runs with the other six harnesses
against an externally installed wheel, Compose, AMD64 and ARM64/QEMU. It uses
separate offline processes for source seeding, record/replay/read/verify/recompute
and restore. Process-kill tests and emulation do not certify physical Pi power loss.
