# P8d — Remote Baseline Audit (Phase Lead)

**Date:** 2026-10-28. **Source:** read-only connected GitHub API for `KastaTM/card-market-tracker`. All results refer to observation time and are not a guarantee that remote has not changed since.

| Check | Observation | Status |
|---|---|---|
| Remote repository | `KastaTM/card-market-tracker`, default branch `main`; public | PASS |
| Current remote `main` | `9dda9fba0aa9646a67596657d4ae9a7088903808` | PASS |
| Commit tree | `dfd0414242cff364aad6082411ae88aef728783e` | PASS |
| Parents (ordered) | `228d5c8d0d91edf03ddb86a489c8232eeb7c08bc`, `d82aba73d9bc0eb455f8664e3ccddc0134ea9d9c` | PASS |
| PR #18 | merged/closed at the same merge commit | PASS |
| P8d remote branch search | zero results for `p8d` query at audit time | OBSERVED, not exhaustive branch/worktree proof |
| Remote file inventory | Existing `watchlist`, `watchlist_journal`, `watchlist_alerts`, `telegram_delivery`, 12 smoke harnesses | PASS (read-only) |
| Local repository/worktrees | No user-local checkout mounted; this container cannot resolve github.com to clone | BLOCKED, must be checked by Codex |
| Git branch/PR creation | No write attempted | NOT RUN |
| Implementation, tests, CI on P8d | No execution attempted | NOT RUN |
| QA, Reviewer | Not executed | NOT RUN |
| Telegram live destination validation/send | **Unauthorized** by P8d opening contract; no calls attempted | NOT RUN |
| AC-WT01..21 | Individual runtime acceptance not established | BLOCKED/NOT RUN |

**Historical evidence:** [PR #18](https://github.com/KastaTM/card-market-tracker/pull/18), [historical CI](https://github.com/KastaTM/card-market-tracker/actions/runs/40737659939). Historical P8c PASS is not P8d evidence.

**Safe next step:** Codex Engineering Lead must verify `git remote -v`, `git status`, branch/worktrees, `git ls-remote origin refs/heads/main`, `git fetch`, exact HEAD/tree/parents before creating `feat/p8d-watchlist-telegram-delivery`. Abort and communicate any mismatch; do not clean/overwrite/rebase unknown work or silently change baseline. Freeze ADR-0015 and both contracts before implementation. No real Telegram invocation without later specific operator/Orchestrator authorization.
