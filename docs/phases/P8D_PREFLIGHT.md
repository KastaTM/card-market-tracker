# P8d Gate A preflight

Date: 2026-10-30. Status: baseline and handoff checks complete; documentary commit/clean check recorded in the Design Freeze handoff.
Authority: Phase Lead CONTINUE GATE A authorization, including sibling worktree
and handoff paths. This resolves the original local-branch mismatch, not any
future remote-baseline divergence. No product code or live calls authorized here.

## Observed Git baseline

- origin: https://github.com/KastaTM/card-market-tracker.git
- git fetch origin: exit0; no output, completed successfully.
- git ls-remote origin refs/heads/main: 9dda9fba0aa9646a67596657d4ae9a7088903808.
- origin/main and new HEAD: 9dda9fba0aa9646a67596657d4ae9a7088903808.
- Tree: dfd0414242cff364aad6082411ae88aef728783e.
- Ordered parents: 228d5c8d0d91edf03ddb86a489c8232eeb7c08bc,
  d82aba73d9bc0eb455f8664e3ccddc0134ea9d9c.
- New worktree: C:/Projects/card-market-tracker-p8d.
- New local branch: feat/p8d-watchlist-telegram-delivery, explicitly from that SHA.
- Branch/path absent before creation; no matching worktree ownership found.
  git worktree add -b succeeded exclusively; initial porcelain clean.
- Original checkout retained rework/p5b-rw03-publication-rollback at
  f80bc8cdb877946f37d76b09212d68dd8da3e246, tree
  dde865b6d215efc4075918088d6deddfe7cdeb1f; porcelain remains empty.
- Historical worktrees/branches inventoried and preserved. Local main remains old;
  it was not advanced or used as baseline. No reset/clean/rebase/force push.
- PR18 merged at this baseline was verified through GitHub in the previous
  preflight; this run repeated fetch and exact live remote-main verification.
  Historical P8c CI is not P8d evidence.

The initial network sandbox blocked remote Git in the prior turn. This turn's
authorized fetch/ls-remote completed through sandbox escalation. No credential
extraction/configuration changes or network fallback writes were used.

## Handoff validation

Downloads supplied all three files; each SHA256 matched its ZIP entry before
copying. New C:/Projects/p8d-handoff copies and docs/phases archives match bytes.
Git newline-conversion warnings prompted explicit archive verification. Raw
blob comparison confirmed the initial commit already preserved all source bytes.
A follow-up adds three narrowly scoped -text attributes (the same pattern as
prior archived contracts) to preserve that property on future checkouts. The
archive itself needed no byte correction. Raw blob equality is checked too.
The complete Orchestrator contract is archived unedited; Brief and historical
audit are separately attributed, not treated as new user authorization.

| File | SHA256 |
| --- | --- |
| P8D_BASELINE_AUDIT.md | 6aa7e5d706a6492a8947d5bba614ff36c4a96c4460ce3392a018fc5f87e952c4 |
| P8D_CODEX_ENGINEERING_BRIEF.md | ed08f263239a8d1e628bd5af1f7efa8fe3329df2901fb5ea03dbc6dae6352cb6 |
| P8D_MANUAL_WATCHLIST_TELEGRAM_DELIVERY_CONTRACT.md | 9b5ec931250fd66f9660c9916153f4594ae021845c6dd9f643264f7df8e8d3e3 |

## Ownership and boundary

[Ownership](P8D_OWNERSHIP.md) assigns Lead/shared docs+Git, ARQ/API-only,
DB/storage-doc-only and SEC/isolated-review-only before parallel authorship.
QA and final REVIEWER are future nonauthors, distinct from each other.
No competing matching path/ref/worktree was observed; this is a point-in-time
inventory plus exclusive creation, not a global process lock.

AGENTS and ROADMAP add attributed P8c closure/P8d opening without deleting older
RW-01 history. P5 global/TD-001..005 stay OPEN; P2/P6a/retail stay BLOCKED.

## Reproducible evidence

[Machine-readable observations](../evidence/P8D_GATE_A/baseline.json).
Run from the P8d worktree (PowerShell quote revision braces):

    git remote -v
    git status --porcelain=v2 --branch
    git branch -avv
    git worktree list --porcelain
    git show -s --format='%H %T %P' 9dda9fba0aa9646a67596657d4ae9a7088903808
    git show -s --format='%H %T %P' origin/main
    git -C C:/Projects/card-market-tracker status --porcelain=v1
    git diff --exit-code 9dda9fba0aa9646a67596657d4ae9a7088903808 -- src tests scripts .github pyproject.toml uv.lock Dockerfile compose.yaml

Remote refresh was performed before creation; re-running fetch is an explicit
network operation and must be followed by a baseline check. Final documentary
commit and clean-tree validation are recorded in P8D_DESIGN_FREEZE.md, avoiding
a self-referential SHA in this report.

## Initial risks and pending decisions

Full original admission/deep folds share a bounded deadline; no guarantee they
fit maximum history on QEMU. Cross-database reads are not a distributed snapshot.
A coherent privileged rewrite or multiple live clones is outside authenticity/
dedup guarantees. Missing postclaim receipt is ambiguous, never retry authority.
RW-01 watch/revision entry agreement must be checked before every prepare/claim.
Restore quarantine is global, permanent, and precedes exposure.
Consent, exact DDL/inventory, mapping of transport outcomes and deadline reserve
are being specified for Phase Lead design review, not claimed implemented.

Gate B remains PENDING PHASE LEAD DESIGN REVIEW. No schema.py/writer/production
identity code, P8d runtime tests, CI or live requests have been executed.
