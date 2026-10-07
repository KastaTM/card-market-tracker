# Engineering operating model

The ChatGPT Orchestrator defines phase contracts, evaluates reports, and alone may declare `PHASE CLOSED`. A Phase Lead translates the contract into implementation work and may propose `READY_FOR_ORCHESTRATOR_REVIEW` only after applicable gates have evidence. The Orchestrator returns `ACCEPTED`, `REWORK_REQUIRED`, or `BLOCKED`; rework items receive IDs such as `RW-01`.

The Codex Engineering Lead inspects repository and Git state, plans, assigns disjoint ownership, integrates, runs gates, and records evidence. Specialist roles are used only when useful. Prefer separate author, QA, and final reviewer; an author's self-review is not independent. Parallel edits require explicit file ownership. Git, lockfile, and other shared-state changes are coordinated sequentially.

Each phase starts with objective, scope, exclusions, dependencies, acceptance criteria, tests, observability, security, mandatory gates, deliverables, and a model profile based on models actually available. A phase may not expand its own scope. Record proposed changes and their impact for Orchestrator decision. Use a short branch and a PR as the review boundary; preserve existing work and avoid force-push.

Definition of Ready requires a complete phase contract. Definition of Done requires working implementation, reproducible automated evidence, documented decisions, security and architecture review, independent review, and Orchestrator acceptance. Unrun work is unverified, never PASS. Record exact branch, commit, CI run URL, environment, and whether ARM64 used native hardware or emulation.

The [P0 phase report](phases/P0_FOUNDATION.md) is the evidence ledger. An interim report may describe blockers, but must not claim readiness while mandatory evidence is missing.
