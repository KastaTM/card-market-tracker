# P5b rework RW-01 / RW-02 / RW-03

The Orchestrator requested integration rework after the ARM64/QEMU backup
timeout in push/main run
[40084565396](https://github.com/KastaTM/card-market-tracker/actions/runs/40084565396).
The integrated baseline is `62ecd7ab792a93a6071b83277d870f1d95f61f9f`, tree
`618f6f1b511a58fa8e35e6892fad951b8e7f788d`. This report records diagnosis and
a conditioned correction proposal. It does not accept or close P5b or P5.

## RW-01: isolated measurement

The original four complete CI logs and their SHA-256 digests were preserved.
The integrated tree was inspected in a detached worktree without product edits.
An isolated diagnostic script wrapped connections, SQLite backup progress,
verification, reservation, fsync and publication in memory. Each backup retained
the actual shared five-second budget. Only disposable synthetic databases were
used; no product networking or live data was involved.

The five checkpoints from the original priced sample fixture produced one
sequence, five evaluations and four signals. The database was 94,208 bytes,
23 pages of 4,096 bytes. Native measurements used Windows/AMD64,
Python 3.13.15 and SQLite 3.53.1; the local Docker daemon was unavailable.

Three uninstrumented backups took 275.717–280.158 ms; three instrumented
backups took 280.766–287.591 ms. Stage medians in milliseconds:

| Stage | Median |
| --- | ---: |
| Destination validation | 0.972 |
| Source open | 1.253 |
| Source deep verification | 89.873 |
| Provisional reservation | 0.366 |
| Writable copy open | 1.358 |
| SQLite backup | 2.225 |
| Copy deep verification | 90.238 |
| Copy reopen | 2.106 |
| Reopened deep verification | 90.246 |
| fsync | 0.298 |
| Exclusive publication, including provisional unlink | 1.558 |

Nested spans overlap; these are wall times, not additive exclusive CPU costs.
Full monotonic start/end timings, environment and results are retained in the
local ignored evidence directory `.p5b-evidence/rw-2026-10-24/`.

Six induced deadline expirations covered destination validation, source fold,
SQLite backup progress, copy fold, reopened fold and fsync. Each used the real
five-second deadline with a deliberate 5 ms injection margin. Each returned
`storage_timeout`, preserved source bytes, passed fresh source verification,
and left no destination, reserved temporary or SQLite sidecar. Successful
copies and subsequent restores also passed fresh verification.

These native measurements do not reproduce the original ARM64 timeout. The
three deep folds dominate measured native cost, but the original log has no
stage timings. Neither QEMU nor a particular fold is established as its root
cause. Cooperative deadlines cannot preempt a blocked filesystem syscall.

## RW-02: one authorized retry

After RW-01 completed and the remote run was confirmed at attempt 1, the
following command was invoked once and returned exit code 0:

```text
gh run rerun 40084565396 --repo KastaTM/card-market-tracker --job 120844721694
```

Attempt 2 uses the same push/main merge and accepted tree. Its ARM64 job is
`120875898003`. The three successful original jobs remain preserved separately
with their original IDs and complete logs. The final attempt result and its
complete log will be attached to the rework handoff. A passing retry alone
cannot establish absence of a defect; another retry is not authorized.

## RW-03: demonstrated distinct publication defect

Independent DB analysis reproduced a different failure on the integrated tree:
if `provisional.unlink()` raises after the exclusive `os.link()`, backup returns
`storage_io` but leaves both names with link count two. Normal verification
rejects that destination as `unsafe_destination`; existing cleanup also refuses
the two-link inode. The source remains unchanged. This defect does not depend
on QEMU, history size or deadline expiration and does not explain the original
`storage_timeout`.

The two post-link regression cases (backup and restore) failed on the integrated
implementation before correction. The correction compensates only the newly
created destination link, after checking both names against the reserved inode,
regular-file type, exact two-link state, absence of reparse points and absence
of recovery sidecars. Existing cleanup can then remove the owned provisional.
The operation reports its original error; it does not retry backup or unlink.

All three deep verifications, exclusive creation, the shared maximum of five
seconds, prior storage owners, schemas, identities, fixtures and CI checks remain
unchanged. Foreign replacements and recovery evidence are preserved. Persistent
filesystem deletion failure or evidence of interference can still require manual
inspection; physical cleanup is not guaranteed when the filesystem refuses it.

Reproduce the focused regression and deadline/safety cases:

```text
uv run --frozen pytest tests/test_watchlist_journal_storage.py -q
```

The corrected storage suite passed 60 cases locally, including post-link failure
for backup/restore, each verification-stage deadline, a substituted destination,
and recovery sidecars at either name. Full gates and distinct non-author QA and
REVIEWER evidence must bind the final candidate SHA/tree in the new PR handoff.
This branch is a proposal only; it must not be merged without new acceptance.

## Model profile and ownership

The requested Engineering Lead profile is GPT-6.1 Sol/Medium with High for this
SQLite/integrity diagnosis. The session identifies Codex as based on GPT-6;
exact selectable variant and effective reasoning are not independently exposed.
No claim is made that the requested variant or reasoning was selected.

Engineering Lead `/root` owns the correction, author tests and integration.
`/root/rw01_db_analysis` supplied read-only DB analysis and its isolated probe.
`/root/rw03_qa` and `/root/rw03_reviewer` are distinct non-author agents with
separate probes and reports. Their actual final results, limitations and
candidate identities are recorded in the rework handoff.
