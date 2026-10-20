# P8a execution ledger

Date: 2026-10-20 (Europe/Madrid). Phase OPEN. This file records preflight;
the phase report P8A_OFFLINE_ALERT_OUTBOX.md and exact-head PR ledger contain
final candidate, gate and review evidence. Historical results are not P8a gates.

## Local preflight actually executed

- Origin fetch/push: https://github.com/KastaTM/card-market-tracker.git.
- Initial checkout feat/p4c-discovery-result-journal at
  9fb53144dec521d0dde49c02d41022be831421c2; git status --short empty.
- Existing detached evidence worktrees and all previous branches preserved.
- Local main remains 5175d5b09e8d412e11b2ddf4c24bff41df133843. Remote-tracking
  and live git ls-remote main agree at authorized baseline
  b89fff319a94e5eb6e4b7bdad944e879bad371f6, tree
  8f62a1d85b375ee839dcd95e09a578cb643c85b6. No remote-main delta.
- gh auth status: KastaTM active, HTTPS, repo/workflow authorization. Repository
  API reports push permission. Previous connector403 did not block local access.
- git switch -c feat/p8a-offline-alert-outbox from the exact baseline succeeded.
  No main write, force push or cleanup of foreign worktrees.
- Supplied ZIP documents archived only into absent docs targets. Unmodified
  contract SHA256 equals supplied standalone file:
  1f93a903398d3cf8f22665f1509f633840fa49845e1314ebc3594099fef6e549.
- Sandbox startup failed before execution with helper_unknown_error/setup refresh
  errors; approved elevated commands worked. This is execution infrastructure.
- uv0.12.10 frozen two-stage installation succeeded without lock changes.
  Python3.13.15 and SQLite3.53.1 observed on Windows AMD64.
- Docker initially had no Linux daemon. Docker Desktop started hidden;
  server29.7.2 and buildx AMD64/ARM64 support subsequently observed.

## Authority and team

The pasted user request instructs implementation, tests, commits, push and PR
without merge. Attached briefs/drafts are engineering inputs subordinate to
the unchanged Orchestrator contract and adopted repository architecture.
P8A_OWNERSHIP.md records actual disjoint authors, nonauthor QA and the required
separate final reviewer. Source acquisition budget is zero. P4c closure/P8a
opening is attributed to Orchestrator chat, not a GitHub closure publication.
TD-001 through TD-005 remain OPEN. Phase readiness requires all mandatory gates
on the final candidate, not this preflight record.
