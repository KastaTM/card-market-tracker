# P5b rework RW-01 / RW-02 / RW-03

The Orchestrator requested integration rework after the ARM64/QEMU backup
timeout in push/main run
[40084565396](https://github.com/KastaTM/card-market-tracker/actions/runs/40084565396).
The integrated baseline is `62ecd7ab792a93a6071b83277d870f1d95f61f9f`, tree
`618f6f1b511a58fa8e35e6892fad951b8e7f788d`. This report records diagnosis and
a conditioned correction proposal for repeated budget exhaustion and a distinct
publication fault. It does not accept or close P5b or P5.

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

These native measurements alone do not reproduce the original ARM64 timeout.
The original log has no stage timings. After RW-02 failed again, Docker Desktop
was started and the integrated product was built with the unchanged pinned
Dockerfile for an isolated ARM64/QEMU experiment, with runtime networking denied.

The same five checkpoints reproduced `storage_timeout` in three of three
integrated backups (5,027–5,112 ms including cooperative failure/cleanup).
Instrumented runs completed the source and copy folds in approximately 1.69 s
and 1.66–1.72 s, then expired during the reopened fold. SQLite copy itself took
only 4–6 ms. Source bytes and subsequent deep verification remained valid;
neither destination nor provisional was exposed or left behind. Runtime:
Linux/aarch64, Python 3.13.16, SQLite 3.46.1, matching the pinned CI image.

Independent profiling explains a concrete source of excess work: each
`validate_snapshot()` executed the identical pure P5a evaluator twice. A
five-checkpoint backup executed 210 evaluator calls across its three independent
folds. The correction reuses the result already calculated during that call's
normalization and canonical size check. It retains all 105 snapshot validations
and all three deep folds, reducing evaluator calls to 105. Public normalization
and validation shapes, rejection checks and deterministic identities are
unchanged. There is no cache between calls or verification stages.

Paired ARM64 measurements on the same image and fixtures passed three of three
corrected backups in 3,992–4,037 ms; all three independent folds completed, with
valid source and destination verification and no residuals. This demonstrates
the cause and correction of the locally reproduced budget exhaustion. The
original CI failure's exact stage was not logged, and arbitrary larger histories
or slower hosts can still legitimately exhaust the bounded operation budget.
QEMU slowness alone is not presented as root cause. Cooperative deadlines cannot
preempt a blocked filesystem syscall. Raw stage measurements and paired profiles
are retained under `arm64-integrated/`, `arm64-candidate/` and `db-owner/` in the
ignored evidence directory.

## RW-02: one authorized retry

After RW-01 completed and the remote run was confirmed at attempt 1, the
following command was invoked once and returned exit code 0:

```text
gh run rerun 40084565396 --repo KastaTM/card-market-tracker --job 120844721694
```

Attempt 2 uses the same push/main merge and accepted tree. Its ARM64 job
`120875898003` failed at the journal backup with `storage_timeout`, 5,176 ms;
the preceding ten harnesses passed. No further retry was attempted. The three
successful original jobs remain preserved separately with their original IDs
and complete logs. GitHub's attempt-2 listing creates inherited entries with
new IDs and their original execution timestamps; these are not new executions.
The first PR #17 candidate also failed its ARM64 backup at 5,159 ms; that run
and its complete failed log are preserved. The next candidate must receive
fresh CI after the correction, rather than rerunning either failed execution.

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
The operation reports its original error; it does not retry copy or publication.
The existing finally cleanup still attempts removal of its owned provisional
after compensation makes the single-link state safe.

Together with the normalization-result reuse above, all three deep verifications,
exclusive creation, the shared maximum of five seconds, prior storage owners,
schemas, identities, fixtures and CI checks remain unchanged. Foreign replacements
and recovery evidence are preserved. Persistent
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
Domain regressions compare exact recomputation results against the pure evaluator
and frozen vectors, enforce one evaluation per snapshot validation and prove
that later mutable evidence is recomputed independently. The combined domain
and storage subset passed 106 cases after both corrections.
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
