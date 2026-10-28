> Historical design handoff: unavailable access/execution describes its creation
> environment. Current results belong to P8C_IMPLEMENTATION_AND_INTEGRATION.md
> and the PR evidence ledger; the template is not executed evidence.

# P8c — Codex Engineering Brief

**Status:** DESIGN HANDOFF / NOT IMPLEMENTED / P8c OPEN. **Authority:** 00 — ORCHESTRATOR opening contract dated 2026-10-25. **Owner:** Codex Engineering Lead once invoked. This document is a proposed implementation brief, not an execution or acceptance claim.

## MODEL PROFILE (repeat in Codex)

- **ChatGPT Phase Lead:** requested GPT-6.1 Sol / High if selectable; fallback GPT-6 / High. This chat identifies as GPT-6; user-selected effort and effective backend are not introspectable. Do not record the requested model as observed.
- **Codex Engineering Lead:** requested GPT-6.1 Sol / Medium if actually present; High for source admission, SQLite, integrity, races, cooperative deadlines and ARM64. If unavailable use strongest actual compatible model and record selector name/effort.
- **ARQ/DB-OWNER/SEC/QA/REVIEWER:** request GPT-6.1 Sol / High if selectable; record concrete substitutions. Escalate difficult cross-phase or timing correctness to GPT-6 Astra / High only if selectable and a real blocker persists. No auto-escalation for routine tasks.
- **Model evidence:** separate requested profile, observed selector/tool arguments and unverifiable effective backend. No Codex call or independent agent review has occurred during production of this document.

## Audited remote baseline; mandatory local re-preflight

2026-10-25 GitHub read-only connector: `KastaTM/card-market-tracker`, `main=228d5c8d0d91edf03ddb86a489c8232eeb7c08bc`, tree `dde865b6d215efc4075918088d6deddfe7cdeb1f`, ordered parents `62ecd7ab792a93a6071b83277d870f1d95f61f9f` then `f80bc8cdb877946f37d76b09212d68dd8da3e246`. PR #17 merged; historical `push/main` CI 40186860176 success, attempt1. This evidence is not a P8c gate. Remote branch list showed no P8c branch. **Attempted GitHub connector branch creation returned HTTP403 `Resource not accessible by integration`; no remote writes were made.** Local `git clone/ls-remote` could not resolve github.com; no checkout/worktree is available in this execution environment.

Codex MUST verify: `git remote -v`, `git status --porcelain=v1`, `git rev-parse HEAD`, `git rev-parse HEAD^{tree}`, `git show --format='%P' -s HEAD`, `git ls-remote origin refs/heads/main`, `git branch -avv`, `git worktree list --porcelain`; inspect branch cleanliness and ownership. Stop on nonmatching remote `main`, unexpected checkout, overlapping worktrees, dirty edits or unknown existing P8c work; report divergence rather than silently rebase/merge. If baseline matches and authorized, create `feat/p8c-watchlist-signal-outbox` from verified baseline. Do not modify credentials or bypass the failed connector action.

## Goal / authorized boundaries

Select ONE original P5b `wsig1_` signal, verify its exact P5b journal predecessor/current and its original P5a watchlist revision and MANIFEST_V1, recompute P5a verdicts and P5b fresh per-rule transition, and durably prepare a content-bound offline preview `walt1_` in an independent SQLite file. Two aliases produce two alerts; price/restock produce two alerts; later episodes have new signal IDs. A replay must revalidate originals and preserve first bytes/time even after source appends or newer watchlist revisions. A complete local verify and explicit read-only origin recompute are separate operations.

**Out:** Telegram, delivery ledger, fake or actual transport, scheduler, polling, bulk enqueue, observed commercial samples, retail, new sources, P5a/P5b rule changes, migrations, old outbox reuse, automatic retention, web API/UI, automatic resolution of P5 global. Network calls by product: zero. P2/P6a/retail Discovery stay BLOCKED; TD-001–TD-005 stay OPEN.

## Read-first dependency inventory

Read `AGENTS.md`, `context.md`, docs/ARCHITECTURE.md, ROADMAP.md, QUALITY_GATES.md, TESTING_STRATEGY.md, TECHNICAL_DEBT.md, threat model and all adopted prior P5a/P5b/P8a/P8b ADRs/contracts. Code entry points identified remotely:

- `watchlist_journal/storage.py`: `_connect`, `_transaction`, `_verify`, `_load_evaluation`, `_signals_for`, `signal_get`; `application.py: _origin_entry` validates manifest + exact revision. `_verify` folds all sequences in one transaction and per-row P5a results **once per fold**; don't regress P5b RW-03.
- `watchlist_journal/identity.py`: `validate_snapshot`, `_evaluation_id`, `signal_body`, `signal_id`; `transitions.py: _derive_normalized_signals` reuses already verified fold points only **within** one transaction.
- `watchlist/storage.py:get`, `watchlist/validation.py:identity_projection, parse_entry, canonical, digest`, `watchlist/evaluation.py:evaluate` must stay read-only and behaviorally unchanged.
- `alerts/application.py`, `alerts/storage.py`, `alerts/render.py` illustrate private content-bound receipt, strict cell checks, deterministic escaping, keys, budgets; reuse patterns rather than importing Discovery authority or modifying CMTA.
- `watchlist_journal/storage.py:_rollback_publication` fixes P5b RW-03 exclusive publication cleanup; copy the safety **behavior**, not a weaker implementation.
- `scripts/wheel_smoke.sh`, `scripts/container_smoke.sh`, `.github/workflows/ci.yml`: eleven existing harnesses, four CI jobs. Preserve exact existing gates.

## Mandatory design freeze BEFORE schema or ID/product writes

1. Archive **this entire Orchestrator contract verbatim** at `docs/phases/P8C_OFFLINE_WATCHLIST_SIGNAL_OUTBOX_CONTRACT.md` (the bundle includes an exact copy). Add dated top roadmap status and concise AGENTS map without rewriting historical statuses or claiming remote closure comment publication.
2. Review proposed ADR-0014 and both proposed `WATCHLIST_ALERT_OUTBOX_*_V1` documents in this bundle; resolve any open fields within authorized scope; freeze the definitive exact DTO field sets, normalized JSON, SQL inventory, expected identity vector bytes, CLI responses/errors and budgets. Reject undocumented schemas and semantics. Source-of-truth becomes committed repo, not this local handoff.
3. Verify selected SQLite `application_id` is unused versus ALL currently adopted owners (candidate: `0x434D5459`, ASCII `CMTY`); owner `card-market-tracker.watchlist-alert-outbox`, schema1. Freeze before any DB file creation. Do not use CMTA, CMTD, CMTW, CMTQ.
4. Confirm the independent stdlib identity oracle (three fixture cases using P5b golden signal IDs), verify NUL is literal `0x00`, canonical sorted ASCII compact JSON; commit vectors, full hex preimages and oracle, and independent QA reference tests. Test-only golden signal IDs are identity vectors, not producer authorization for enqueue.

## Author implementation order and ownership

**Engineering Lead** integrates, provides one shared repo owner for root CLI/logging, harness/CI, merged docs and PR; freezes interfaces before task dispatch. **ARQ/BE (author)** owns `src/card_market_tracker/watchlist_alerts/{errors,models,policy,render,application}.py` and corresponding author domain/application tests. **DB-OWNER (other author)** owns `{schema,storage}.py` and storage tests. Only one owner modifies each path. **P5b additive source reader:** allocate to ARQ/BE with explicit single-file ownership coordination; add one private read-only `_verified_signal_bundle(path,signal_id, _budget)` in original `watchlist_journal/storage.py`, or narrow equivalent, that executes `_verify` exactly once while holding one `mode=ro/query_only` journal transaction, loads the exact signal and its `from/to` evaluations in the same transaction using the same Budget, validates link/transition against already revalidated data. Do not call separate full verifying public `signal_get/get/get` or read on different snapshots. Keep all existing P5b public entry points and behavior intact. **SEC/SRE** read-only threat/recovery/time review. **QA** and a distinct **REVIEWER** each author separate, publicly recoverable final-SHA probes; neither authored implementation.

Suggested stage gates:

- A: freeze ADR/data contracts/DDL/CLI and independent oracle; design review no product code.
- B: source reader + pure policy/renderer; author tests; zero sockets.
- C: new SQLite writer/readers/verify/recovery; concurrency/fault tests.
- D: CLI/logging, 12th installed-process harness and CI integration; documentation.
- E: independent QA then distinct REVIEWER on exact candidate SHA/tree, full gates and remote PR+CI logs. A code fix after review requires renewed affected reviews/gates.

## Semantic route and trust boundary

`read complete manifest -> independently verify journal original (single read transaction/fold) -> select wsig1_ and exact predecessor/current -> re-read exact P5a historical revision for both snapshots -> recompute P5a results, sequence links and rule-specific NO_MATCH -> MATCH -> build strict content-bound semantic projection -> render deterministic plaintext -> private one-operation receipt -> BEGIN IMMEDIATE new CMTY SQLite: atomic alert+evidence INSERT or strict replay/conflict`. Separate read transactions are unavoidable; report original immutable-revisions/trusted-folder assumption; never claim global snapshot/producer authentication.

Projection MUST retain full signal body+ID and two normalized evaluation snapshots, with exact evaluation IDs, ordinals, predecessor link and recalculated results. Strip journal persisted_at, global head, paths, run IDs, full DB digests, new current revision and wall clock; historical P5a revision remains exact and simulation-only. All untrusted source DTOs revalidated, even replay. Public receipt creation and private consumption must bind ALL content/versions; ordinary dict objects/hashes/`verified=True` cannot grant write authority.

`identity = walt1_ + sha256(b'CMT_WATCHLIST_ALERT_V1\x00' + canonical({identity_version:1,destination_key:<alias>,signal_id:<wsig1_>})).hexdigest()`. Dest alias grammar `^[a-z][a-z0-9_-]{0,63}$`. Other accepted IDs are NOT widened. Intent <=64KiB, evidence bundle <=256KiB, message <=4096 UTF-8 bytes, JSON <=1MiB/depth16/nodes20000/strings1024 (or stricter original). Canonical bytes use the exact P5a/P5b serializer. No forward declaration of real availability.

Require deep `verify` to reject semantically invalid rehashed rows or restored triggers, and separate `recompute` that independently reopens original journals/revisions and compares intent, evidence, IDs, rendering and original frozen content WITHOUT writing. No cross-operation caches or reuse of previously verified folds. List only bounded summaries, cursor bound to filters/version and result <=1MiB; no partial result=ok on timeout or corruption. Shared default2s/max5s cooperative deadline across stages; test QEMU five-checkpoint scenario without relaxing it.

## Security, recovery, observability

Immutable STRICT exact SQLite object inventory, owner/application_id/version, bounded cell reads before decode, FK/integrity and full semantic verification, prohibited UPDATE/DELETE, atomic BEGIN IMMEDIATE, stable duplicate replay and explicit conflict rollback. Concurrent separate CLI processes: one insert, one replay. Failures lock, ENOSPC, fsync, link/unlink, restart/crash, sidecars and race conditions fail closed. `backup`/`restore`: source, copy and destination independent full folds within one budget; exclusive destination, validated reopened copy, inode/hardlink/reparse/sidecar safeguards, safe owned-only compensation after unlink failure. Never alter original P5a/P5b, CMTA or CMTD bytes; no Telegram environment import or sockets.

Renderer exactly begins `SYNTHETIC — DEMONSTRATION ONLY`, includes explicit NOT REAL OFFER/COMMERCIAL ALERT, shows CMT ID/watch ID/historical revision/rule/signal, sample/as_of times and rule reasons. Money is exact EUR cents; effective acquisition price only if valid unit+shipping both present. Do not print names/URLs/PII, infer current preferences or stock. Escape controls, backslashes and bidi per P8a, reject oversize rather than truncate. SHA message over exact UTF-8 bytes.

Add allowlisted `watchlist.alert_outbox.completed` event and fixed `watchlist_alert_outbox_` operation family. Include UUID run_id/duration/result/safe error-category/counts. Exclude destination aliases, manifest, sample/price payload, message, secrets, host paths or exception strings. Separate Market vs Operational Alerts; P8c emits no messages.

## Validation and evidence delivery

AC-WA01..20 must each be PASS/FAIL/BLOCKED with direct evidence. Run frozen uv, Ruff format/check, mypy strict, full pytest unit/integration/contract/regression, separated >=85% line >=80% branch coverage, sdist/wheel outside-tree, dependency audit, secret scan, Docker Compose+linux/amd64+linux/arm64(QEMU); zero filters/weakening. All **twelve** harnesses must run in installed wheel, Compose, AMD64, ARM64. Twelfth harness must use one MANIFEST, P5a revisions, five P5b checkpoints/four signals, real separate processes for append/enqueue/replay/preview/recompute/backup/restore, offline `--network none`/UID10001 as applicable. Include three controlled 5s ARM64/QEMU backup+restore measurements and per-stage timings when feasible; not a physical Pi claim.

Preserve prior failed CI runs, don't rerun failed jobs of same SHA without authorization. Publish full sanitized runnable QA/REVIEWER sources/helpers/instructions/results bound to final HEAD/tree and all four full CI logs. Readback every remote link. No branch/PR/commit/CI/probe evidence may be claimed from this offline package.

**Handoff required:** Phase Completion Report with branch/PR/commit/base/HEAD/tree, models requested/actual, specialist ownership, ADRs/contracts/DB/threat/observability/debt, AC-WA01..20 individually, four final job IDs/logs and twelve harnesses, caveats/failures, documentation/evidence readback and recommendation. Only report `READY_FOR_ORCHESTRATOR_REVIEW` after all applicable gates PASS. **Do not merge, accept or close P8c.**
