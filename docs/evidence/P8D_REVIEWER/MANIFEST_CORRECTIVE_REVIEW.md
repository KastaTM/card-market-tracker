# P8d independent REVIEWER - manifest correction readback

Date: 2026-10-30. Actor: `/root/p8d_final_reviewer`.
Status: PROVISIONAL working-tree review; exact final candidate verification pending.

The Lead's new `application._manifest_read` was independently inspected. It
checks the accepted physical path/ancestors, requires a regular single-link
inode, opens with O_NOFOLLOW/O_BINARY where supported, limits descriptor reads
to1MiB+1 and compares before/opened/readback/after device/inode/link count/size/
mtime. It then applies the unchanged strict duplicate/nonfinite/UTF8 parser and
canonical structural limits under the shared Budget. The deferred path remains
unread on confirmed replay. Prior P5a/P8c validators were not changed for this
correction. This implements the accepted physical boundary without a frozen
DDL/API/identity/consent/outcome change.

Independent command:

```powershell
& .venv/Scripts/python.exe -B scripts/p8d_reviewer_probe.py
```

Observed result: **18 PASS, exit0**, Python3.13.15 / SQLite3.53.1. The previously
failing `manifest_multiple_hardlinks_refused` now passes. All other independent
checks continue to pass, including fresh-process token/socket/Telegram-import
denied confirmed replay and source-byte nonmutation. Sanitized output is retained
in MANIFEST_CORRECTIVE_PROBE_RESULT.json. The original17PASS/1FAIL result remains
unchanged in MANIFEST_GAP_PROBE_RESULT.json. Own script Ruff check remains clean.

There are no outstanding findings from this provisional review. HEAD/tree still
identify the accepted design checkpoint50fcb55a/d8d3eac while runtime code is
uncommitted, so these results are not a final candidate attestation. Await Lead's
exact committed HEAD/tree and renewed execution. No live Telegram call, token
access, product edit, candidate acceptance or phase closure was performed by this
reviewer. AC-WT20 remains BLOCKED - LIVE_UNVERIFIED.
