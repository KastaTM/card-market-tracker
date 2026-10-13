# ENGINEERING BRIEF — P4a Offline Temporal Discovery

## MODEL PROFILE (mandatory — verify selectable options)

- **ChatGPT Phase Lead:** the Orchestrator's contract recommends **GPT-6.1 Sol / High in Work** if selectable, or **GPT-5.6 Sol / High in normal ChatGPT** if selectable. Selection is a client action, not established by the text of this brief; record the actual UI selection or its unavailability.
- **Codex Engineering Lead:** **GPT-6.1 Sol / Medium**, if selectable; escalate to **High** for snapshot consistency, temporal semantics, event identity, failure analysis, integration and final review.
- **ARQ + DB-OWNER, DATA/DISCOVERY, SEC/SRE:** **GPT-6.1 Sol / High** for critical design/risk reviews when available. Combined author roles may be justified; record ownership and selected models.
- **QA and REVIEWER:** **GPT-6.1 Sol / High**, two distinct agents, each separate from authors and from the other; use independent, isolated, read-only final-SHA worktrees.
- **Escalation:** consider **GPT-6 Astra / High** only for a persistent reproduced complex blocker, if available; record grounds and result. Do not claim a model/reasoning/backend that the actual client does not expose. If a recommendation is unavailable, select a real equivalent and report deviations; confirm with the Phase Lead when model choice requires a decision.

## Authority, scope and source of truth

You are the **Codex Engineering Lead** executing the contract **P4a — Offline Temporal Discovery: contrato y prompt de apertura**, issued by the CMT Orchestrator on **2026-10-12 (Europe/Madrid)**. The **ChatGPT Phase Lead** coordinates and receives your Engineering Completion Report. Only **00 — ORCHESTRATOR** may accept, merge-authorize a specific candidate or declare **PHASE CLOSED**. This brief does not supersede the complete phase contract; read that entire text before implementation and archive it in `docs/phases/P4A_OFFLINE_TEMPORAL_DISCOVERY_CONTRACT.md` preserving its meaning.

- Repo: `https://github.com/KastaTM/card-market-tracker`.
- Local checkout expected: `C:\Projects\card-market-tracker`.
- Authorized branch: `feat/p4a-offline-temporal-discovery`.
- Authorized baseline: `main = 734641a7ef920688677cdea6bc82f908a2856927`, tree `ae61fe57e6f874b138c98ecdaaa8cbd830406354`.
- Baseline parents, in order: `c6e66a2aba469d02f0ca63fde3b81ecc5eea41bc`, `e9c5f02e7f093dedff55b67f137c4446f22e8735`.
- P3a merged PR: `https://github.com/KastaTM/card-market-tracker/pull/6`; `push/main` workflow `https://github.com/KastaTM/card-market-tracker/actions/runs/38302824438` completed successfully at baseline. These are historical P3a results, not P4a quality evidence.
- ChatGPT Phase Lead independently verified the above *remote* baseline and absence of the proposed P4a branch by GitHub connector on 2026-10-12. **It has not verified the Windows checkout, uncommitted work, local Docker, model availability, or executable P4a gates.**
- No merge authorization. No new real feeds, schedulers, storage schema/migration, delivery, price/stock, source claims or network access.

## Mandatory repository inspection BEFORE edits

Read `AGENTS.md`, `context.md`, `docs/ENGINEERING_OPERATING_MODEL.md`, `docs/ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/QUALITY_GATES.md`, `docs/TESTING_STRATEGY.md`, `docs/CODING_STANDARDS.md`, `docs/RISK_REGISTER.md`, `docs/TECHNICAL_DEBT.md`, `docs/threat-model/THREAT_MODEL.md`, P1a/P3a contracts/reports/ownership/PR ledgers, `docs/adr/0003-catalog-identity.md`, `docs/adr/0004-offline-observation-persistence.md` and the versioned `INGESTION_V1`, `MANIFEST_V1`, `PERSISTENCE_V1`, `STORAGE_V1`, `LOGGING_V1` contracts. Inspect relevant runtime/tests/CI/harness code, not merely the documents.

Run and record remote/branch/worktree status and preservation checks: `git remote -v`, `git status --porcelain=v1`, `git branch -vv`, `git worktree list`, `git fetch origin`, `git rev-parse origin/main`, `git rev-parse origin/main^{tree}`, `git cat-file -p origin/main`, `git show --stat --oneline origin/main`. Ensure the parent ordering, tree, and baseline match. If `main` moved, compare changed files and impact, disclose it and elevate any changed dependencies; never silently rebase onto an unreviewed baseline. Preserve user changes and existing worktrees. Create an isolated branch/worktree only after the checks.

## Goal and architecture

Implement a reproducible **offline, read-only temporal comparator** of one synthetic persisted P3a current batch against **up to 32 explicitly selected prior batches**, all in a single **exact context** (`namespace`, `kind`, `language`, including null as an exact value). The operation reports whether accepted **set references** and **candidate references** are first observed **within that explicitly supplied historical window**. A reference newly seen under another external ID but resolving to an old CMT UUID remains a new *reference*, never a new canonical product. Never claim launch, preorder, new commercially sellable sealed product, global first observation, restock or source health.

Target flow:

```
strict bounded local request JSON
    -> P3a consistent owned SQLite snapshot API (new compatible *read* only)
    -> validated generic batch snapshots
    -> pure provider/SQLite/CLI-independent comparator
    -> versioned typed Discovery result / canonical event IDs
    -> `cmt discover --db PATH --request REQUEST_JSON` JSON stdout
       + allowlisted correlated JSON stderr
```

No schema migration, no Discovery event/outbox/cursor/checkpoint table, no persistence of output, no implicit latest-batch lookup, no retention or destructive cleanup. Keep old P0/P1a/P3a API/CLI behavior unchanged.

## Early design checkpoint — empty-batch context proof (do not gloss over)

The current P3a `batches` table contains batch ID, capture, counts and `context_fingerprint`, but **no explicit `namespace/kind/language` capture-scope columns**; the hash is derived from manifest/resolver identity context, not an unambiguous scope declaration. An empty batch has zero `records` from which to verify capture context. `persistence.sqlite_repository.query` returns a maximum of 1,000 rows and lacks authoritative empty-vs-missing batch metadata.

**Required:** before implementation, ARQ/DB-OWNER must propose and test how the permitted four-field request context and P3a metadata support *honest* empty-batch attestation while avoiding false novelty. Do not claim DB proof of empty-batch context if the schema cannot supply it. Clearly distinguish an explicit producer/caller attestation from a cryptographically or persistently verifiable stored fact. If AC-D03/08/09 cannot be met without a new durable schema field, stop that dependent portion and escalate a concrete, minimal alternative to the Orchestrator; continue independent work. Do not invent extra request fields, change schema1, or silently drop empty historical batches.

## Workstream sequencing and ownership

1. **Engineering Lead** — record baseline and ownership in `docs/phases/P4A_OWNERSHIP.md`; archive full contract; coordinate design decisions; own Git/worktrees, public CLI/logging, integration, CI/workflows/Docker/Compose/scripts, shared docs and final report/PR. Delegate only explicit tasks.
2. **ARQ + DB-OWNER (combined author allowed)** — one ADR with Context/Decision/Alternatives/Consequences/Status/Revisit conditions on temporal window, snapshot read boundary, event/comparison identities; contracts `DISCOVERY_V1` and compatible `STORAGE_V1` read extension. Own additive storage read API and SQLite-integrity tests. Check the empty-context risk before coding dependent behavior.
3. **DATA/DISCOVERY + BE** — own generic versioned request/snapshot/event models, pure comparison and deterministic output; unique files under `src/card_market_tracker/discovery/`; own synthetic fixtures/contract/unit/edge cases. Do not modify SQLite/CLI files or re-resolve frozen history.
4. **SEC + SRE** — independent design and runtime read-only inspection of input limits, mode=ro/query_only, timeout, rejected/contradictory evidence, no mutating DB, log redaction, UID10001, offline containers; own threat/risk/runbook/debt docs only by coordinated handoff.
5. **Engineering Lead** — integrate only after shared DTO and error contract frozen; CLI, logging allowlists, wheel/Compose/AMD64/ARM64 smokes, CI, docs. Preserve all earlier smoke cases, no unrelated refactor.
6. **QA** — independent agent in a separate detached read-only worktree at exact final candidate SHA; devise tests beyond author tests; execute risk scenarios. No authorship of production code.
7. **REVIEWER** — distinct agent in a different detached read-only worktree at same SHA; inspect scope, identity, contracts, Git objects, quality evidence and CI job logs, with independent probes. No self-approval.

Keep an explicit file/role ownership ledger before concurrency. Parallelize independent read-only investigation or disjoint edits only. Shared Git, workflow, CLI, lock, logging and common docs changes are serial. Agent model selection requested/accepted/effective visibility and any combination are recorded; no invented multiagent execution.

## Exact comparison contract

- JSON request **exact fields only:** `version`, `current_batch_id`, `history_batch_ids`, `context`. Reuse P1a bounded JSON reader: 1,048,576-byte max; depth 16; nodes 20,000; any string/key 1,024 chars; forbid duplicate keys anywhere; strict `version: 1` integer not bool; UUID validation via existing validators.
- `history_batch_ids`: max 32 unique UUIDs; canonical sort independent of input ordering; current UUID distinct. No inferred history or wall clock.
- Each batch at most 1,000 stored records; total across selected batches at most 33,000; output at most 1,000 events. Limits are hard fail-closed budgets. No success when truncated.
- Context equality exact for *all admitted* records in each referenced batch: `namespace`, `kind`, `language` (`null` exact), variant included in reference equality but not a context wildcard. Mixed-context batch must fail rather than filter. All historical `captured_at` strictly earlier than current UTC normalized capture. Historical captures may tie with one another.
- Any referenced missing batch, `rejected_count > 0`, inconsistent metadata/rows/status/provenance, corrupt/foreign/future schema, incompatible record, timeout/lock/IO, contradictory same-reference snapshots, forged Python DTOs or out-of-bound input: **explicit categorized failure, no partial events**. Candidates with zero rejects are valid.
- No valid history => explicit **baseline**, zero events. Existing empty historical capture is distinct from missing/failed/rejected. Do not infer source health or treat a failed source as zero observations.
- Historical *seen set* is union of accepted + candidate references across **all selected** historical batches; it includes accepted non-set kinds to suppress false candidate novelty. Historical state remains frozen: candidate→accepted later is not first-observed. A reference lost in an intermediate empty batch is still seen if in the supplied union. A reference outside a different window can later count new **relative to that different window**.
- Key = validated `(namespace,kind,external_id,language,variant)`; never name, release date, SKU, payload hash, record index or CMT ID. Changes of name/release/provider updated dates do not produce new-reference events. Duplicate identical rows within the *same* batch collapse; incompatible same-reference rows within the same batch reject entire operation. Legitimate evolution across different batches is not contradiction.
- Current accepted **set** ref absent from historical union => exactly one `SET_REFERENCE_FIRST_OBSERVED` event; any new **candidate** ref => exactly one `CANDIDATE_REFERENCE_FIRST_OBSERVED` even when candidate kind=set. Other newly accepted kinds do not emit P4a events.
- Events retain original current batch/capture, exact contextual reference, frozen status, nullable CMT ID only if accepted observation carried it, evidence window, deterministic window-relative first observation. Never claim `product_new=true`, automatic promotion, delivery, or guaranteed exactly-once.
- Document deterministic canonical JSON (sorted keys and canonical UTC), event identity version/hash and comparison identity/hash. Event IDs must be stable across history-ID permutation/replay/backup restore; change when context or current capture differs. Comparison ID captures canonical historic window and pertinent snapshot contents/fingerprints; decide and test when change of window causes a new comparison ID. Exclude runtime run_id, duration, wall-clock and DB paths from semantic output. Event order stable by reference key.

## Snapshot reader contract

Add a **small public P3a read-only API**, without introducing speculative multi-backend abstraction. One SQLite `mode=ro`, `query_only` connection and **one explicit consistent read transaction** for metadata plus rows across *all* selected batches. Existing `query` is not sufficient. Validate ownership `application_id=0x434d5431`, `user_version=1`, schema inventory, provenance and known status/kind/category, required timestamps and UTC, batch counts/row counts, contiguity/index integrity as applicable, per-row shape and cross-row consistency. Keep parameterized SQL, a single global finite budget and safe path guards/closing/rollback on all paths; distinguish missing from existing empty batch. `integrity_check`/`foreign_key_check` assure database invariants, **not** business scope/producer health; add business validation separately. Discovery's pure comparator must receive validated generic values without importing `sqlite3`, table names or TCGdex. Do not create a missing DB on read.

## CLI, observability and operational behavior

Add `cmt discover --db PATH --request REQUEST_JSON`; stdout emits a contract-versioned JSON result for baseline/no_discoveries/discoveries or error. Stderr emits an allowlisted `discovery.completed` logging event with run_id, result, duration_ms, error_category and bounded batch/observation/event counts, without leaking batch IDs, external references, names, paths, SQL, payload or raw exceptions. Successful exit `0`; invalid input/context/chronology/incomplete evidence `2`; storage/IO/lock/timeout/corruption `1`. Preserve all preexisting CLI codes. No new dependencies absent compelling need; if one is needed assess ARM64 and ADR impact before proposing.

Container smoke: seed a real SQLite database with existing installed P3a commands inside offline non-root container, exit that process, invoke Discovery **in a different process**, verify explicit event semantics and compare pre/post DB logical content/inventory/version, including backup/restore result equality. Root UID is 10001; no networking; fixtures read-only; distinguish QEMU from native physical Raspberry Pi. Avoid assuming SQLite can always recover a hot journal through a read-only handle.

## Tests and mandatory quality gates

Implement each `AC-D01`–`AC-D15` in the original contract as a traceability matrix to concrete test/command/reviewer evidence, with **PASS/FAIL** only. Negative cases: missing/malformed/duplicate-key/version request, forged DTOs, missing DB/batch, foreign/future/corrupt DB, counts tampering, rejection count, corrupt provenance, historic timestamp equality/reversal, wrong context, >32 histories and >33k rows budgets, >1k event budget, contradictory duplicates, lock/deadline/IO, stdout/stderr leak tests, nonmutation. Positive cases: accepted new set, new candidate including set candidate, known canonical CMT ID/new external ref, candidate→accepted, repeats, intermediate empty and reappearance, accepted other kinds, name/date-only changes, null/exact-language/variant differences, baseline/explicit empty, input history-order invariance, replay, independent backup/restore, container persistence across processes. Use deterministic versioned synthetic fixtures only; no Internet in runtime tests.

Re-run P0/P1a/P3a regression plus new functionality on **installed wheel outside checkout**, Compose, linux/amd64, linux/arm64 QEMU. Existing smoke cases must remain. Use the repo's gate commands (adapt script names for P4a without removing old assertions):

```sh
uv sync --frozen --no-install-project
uv sync --frozen --no-build-isolation
uv run --frozen ruff format --check .
uv run --frozen ruff check .
uv run --frozen mypy src
uv run --frozen coverage run -m pytest
uv run --frozen coverage json -o coverage.json
uv run --frozen python scripts/check_coverage.py coverage.json
uv build --no-build-isolation
sh scripts/wheel_smoke.sh
uv export --frozen --all-groups --no-emit-project -o requirements-audit.txt
uv run --frozen pip-audit -r requirements-audit.txt
uv run --frozen python scripts/check_secret_scan.py
sh scripts/container_smoke.sh cmt-p4a-smoke:amd64 linux/amd64
sh scripts/container_smoke.sh cmt-p4a-smoke:arm64 linux/arm64
docker compose run --build --rm version
docker compose run --build --rm diagnose
```

Also run **both prior catalog and observation-persistence smoke scripts** plus the new P4a harness for wheel/Compose/containers. Coverage all own runtime must be **>=85% lines and >=80% branches**; preserve CI four jobs (quality, compose, amd64, arm64), require final exact candidate CI job bodies PASS. Do not label an unexecuted mandatory gate N/A or PASS. Record Python/SQLite/QEMU actual versions and CI/local differences. Use unique disposable DBs; never touch a user DB.

## Documentation and handoff

Update: `docs/phases/P4A_OFFLINE_TEMPORAL_DISCOVERY_CONTRACT.md` (contract), `docs/phases/P4A_CODEX_ENGINEERING_BRIEF.md`, `docs/phases/P4A_OWNERSHIP.md`, `docs/phases/P4A_OFFLINE_TEMPORAL_DISCOVERY.md` (report), `docs/ROADMAP.md` (attributed Orchestrator P3a closure/P4a opening), late note in P3a report without rewriting history, `docs/ARCHITECTURE.md`, `docs/QUALITY_GATES.md`, `docs/TESTING_STRATEGY.md`, relevant ADR, data contracts, runbook, threat model, risk and debt register, fixture provenance and README. Keep AGENTS brief. Preserve TD-001–TD-004 absent actual exit evidence. No new schema/migration in DATABASE CHANGES; if necessary, escalate instead.

Produce one pull request from authorized branch **without merging**. The report must contain: Phase, Proposed Status, Branch/PR/head/base/tree, MODEL PROFILE USED with requested/accepted/backend visibility, specialists and ownership, objectives, code, ADR/contract/DB changes, threat/debt/observability, tests and command/environment/sha evidence, individual AC-D01..D15 PASS/FAIL, quality gates, blockers/limitations, recommendation. Link immutable CI job bodies and independent reviews at exact final candidate SHA in a PR ledger; avoid a circular SHA claim in committed report. Check head/tree/base/checks/mergeability and any intervening ref changes. No final status `READY_FOR_ORCHESTRATOR_REVIEW` while gates remain failed or unverified. Return **READY_FOR_ORCHESTRATOR_REVIEW** only for a demonstrably complete candidate; otherwise clearly report current progress and blockers, never `PHASE CLOSED`.

## First response requested from Codex Engineering Lead

Report verified Git remote/local status and baseline; actual selectable model profile; full contract/document inspection; ownership and design-risk decisions (including empty-batch scope); an ordered implementation/test plan; then autonomously execute authorized work. Ask the Orchestrator only about a genuine cross-phase/scope change or a material blocker, not routine Git/PR actions. **Do not merge.**
