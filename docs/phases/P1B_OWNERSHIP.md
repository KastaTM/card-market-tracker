# P1b ownership and preflight

Authority: archived P1b contract and brief supplied by the user, 2026-10-14.
Only Orchestrator accepts/closes/integrates. No merge authorized.

Lead /root owns Git, acquisition requests and shared request ledger, CLI,
logging, harnesses, workflow/Compose, shared documentation and final evidence.
INTEGRATIONS/DATA source_author owns src/card_market_tracker/pinned_repository/,
tests/test_pinned_repository*.py, docs/data-contracts/PINNED_REPOSITORY_BUNDLE_V1.md,
docs/sources/P1B_FIELD_LEDGER.md, minimal bundle/license fixtures. No network requests.
ARQ/DB-OWNER storage_author owns persistence/schema.py, sqlite_repository.py,
new persistence/capture*.py, tests/test_capture*.py, tests/test_migration*.py,
docs/adr/0006-pinned-capture-storage.md, CAPTURE_SCOPE_V1 and STORAGE_V2 contracts.
No concurrent edits to these paths. Shared interfaces agreed before integration.
SEC/SRE analysis initially combined with Lead; later read-only specialist review.
QA qa_final and REVIEWER reviewer_final are distinct new read-only agents, neither
an author nor each other. Each reviews detached final exact-SHA/tree worktree.

Specialists requested gpt-6.1-sol/high, an exposed tool option; actual accepted
invocations and findings recorded later. Root runtime identifies GPT-6-based Codex;
precise serving variant and client reasoning selection unobservable, no switch claimed.

Preflight: clean initial docs/p05b-real-source-qualification at 302e8d3f3155c14091d26841b8a230791109f220.
Remote https://github.com/KastaTM/card-market-tracker.git. Fetch verified baseline
acca10e406dac8809edc289c3077a6ec8785a622, tree 26011d0375f3716a7fffb31956665eb97567a0df,
ordered parents 6385c952a9f2024c8b7bdb33d37fa21017029bd5 then 302e8d3f3155c14091d26841b8a230791109f220.
Initial HEAD has same tree. Local main 5175d5b is behind 16 commits; preserved.
Authorized P1b branch absent locally/remotely and created from exact baseline.
Existing P3a/P4a/P0.5b detached worktrees preserved. No reset/rebase/force.
Sandbox process setup fails; automatically reviewed elevated shell works.
Contract and brief copied byte-for-byte from supplied Downloads paths.

Plan: fixed offline source grammar and policy -> generic observations -> independent
real admission -> explicit transactional schema2 migration with verified backup ->
CLI/consistent reads/replay/restore -> offline process harness -> gates and reviews.
Historical contracts/reports remain snapshots. No automatic manifest bindings.

Preliminary independent findings (not final-SHA gates): QA caught uncategorized
serialization of a huge Python integer; source author fixed and QA rechecked.
REVIEWER caught quoted-token grammar spoofing and missing v2 capture revalidation
in Discovery snapshot reads; owners add regressions and reviewer rechecks before
freeze. Reviewer also requested predecode byte/depth guards, first-error integrity
checks and a scope+rows concurrent snapshot test. Lead adds installed CLI socket
audit denial throughout the process harness. Final decisions/results belong in
external exact-candidate PR ledger; no source requests issued by specialists.
