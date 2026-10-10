# ENGINEERING BRIEF — P3a Observation Persistence

**Project:** Card Market Tracker (CMT)  
**Authority:** 00 — ORCHESTRATOR, contract opened 2026-10-10 (Europe/Madrid)  
**Phase Lead:** ChatGPT Phase Lead P3a. The Engineering Lead implements and produces evidence; only the Orchestrator accepts/closes.  
**Repo:** `https://github.com/KastaTM/card-market-tracker`  
**Local checkout:** `C:\Projects\card-market-tracker`  
**Authorized branch:** `feat/p3a-observation-persistence`  
**Authorized main baseline:** `c6e66a2aba469d02f0ca63fde3b81ecc5eea41bc`; tree per phase contract `a9717922736a6220d3ff05293bec4cb222644269`.

## MODEL PROFILE (mandatory)

- **Codex Engineering Lead:** contract recommends `GPT-6.1 Sol / Medium` *if selectable in the Codex client*. Escalate to **High** for transactional/schema design, migrations, security, recovery, integration or difficult debugging.
- **ARQ / DB-OWNER / SEC / SRE:** `GPT-6.1 Sol / High` for substantive architecture, persistence and operational reviews where selectable. ARQ + DB-OWNER may share an author, but record the combination.
- **BE / DATA:** `GPT-6.1 Sol / Medium` for bounded implementation; High when critical invariants/failures warrant.
- **QA and REVIEWER:** separate independent agents, each `GPT-6.1 Sol / High` if available, distinct from all authors and **from each other**. Read-only review on final SHA/tree.
- **Phase Lead (ChatGPT):** phase contract recommends `GPT-5.6 Sol / High` in normal chat and `GPT-6.1 Sol / High` where available; the currently running chat identifies as GPT-6 and its effective thinking setting is not verified. This prompt does not select a model on the user's behalf.
- **Escalation:** only consider the contract's `GPT-6 Astra / High` when actually available and after a reproducible persistent blocker, with reason and result recorded. If the named profiles are not available, use an actual selectable equivalent and record the deviation. Do not invent exact backend/reasoning provenance.

## Binding authorities and immediate instructions

1. Read **the full attached P3a phase contract**, `AGENTS.md`, repository `context.md`, `docs/ENGINEERING_OPERATING_MODEL.md`, `docs/ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/QUALITY_GATES.md`, `docs/TESTING_STRATEGY.md`, `docs/CODING_STANDARDS.md`, `docs/RISK_REGISTER.md`, `docs/TECHNICAL_DEBT.md`, `docs/threat-model/THREAT_MODEL.md`, `docs/data-contracts/{CATALOG_V1,INGESTION_V1,MANIFEST_V1,LOGGING_V1}.md`, `docs/adr/0003-catalog-identity.md`, `docs/phases/{P1A_CATALOG_CORE_CONTRACT,P1A_CATALOG_CORE}.md`, related P1a PR ledger and push-main CI evidence. The **repo and full phase contract** are the authority; this Brief is an execution plan, not permission to change scope.
2. **Before editing**, inspect `git remote -v`, `git status --porcelain=v1`, `git branch -vv`, `git fetch origin`, `git rev-parse origin/main`, `git rev-parse origin/main^{tree}`, `git cat-file -p origin/main`, worktrees, existing branches and any user changes. Remote main was verified through GitHub connector as `c6e66a2...` at handoff, but this does **not** verify Windows local checkout or future remote changes. Compare exact baseline/tree and report any unexpected advancement. Preserve unrelated work and make a clean isolated branch/worktree from verified base. If changed main materially alters dependency, escalate before integrating. Do not reset or overwrite users' files.
3. Archive the phase contract **unchanged in meaning** under `docs/phases/P3A_OBSERVATION_PERSISTENCE_CONTRACT.md` in the P3a branch. Record the Orchestrator's 2026-10-10 P1a closure and P3a opening in `docs/ROADMAP.md` and `docs/phases/P1A_CATALOG_CORE.md` as an attributed later decision with actual baseline/CI evidence. Do not rewrite the older pre-merge report as though it was originally written post-merge.
4. **No merge authorization.** You may inspect, branch, implement, test, review, document and open a PR within the contract. Stop at candidate delivery. Only the Orchestrator authorizes integration of a specific candidate. Do not open P2/P6a or change GitHub protections.

## Objective / strict scope

Implement a minimal **offline SQLite** storage layer for accepted and candidate **normalized catalog metadata observations** with immutable resolution/evidence snapshots, curated CMT UUID relationships, atomic batch writes, stable-token idempotent replay, bounded read/reopen, schema initialization/version checks, integrity check and consistent backup/restore. Only synthetic fixtures can be written. Make this demonstrable via an installed `cmt` command, Docker Compose and linux/amd64 + linux/arm64 QEMU images, including **data surviving distinct container invocations** as UID 10001 with networking off.

**Not allowed:** live HTTP, TCGdex GETs, price/stock/retail/market schema, real data retention, scraping, scheduler, collection daemon, discovery/novelty detection, candidate promotion/review queue, public API/UI, Telegram, P3b analytics, PostgreSQL, remote sync, automatic destructive cleanup or rewriting real user DBs. P2 remains BLOCKED for EUR feed semantics/access/retention; P6a and retail Discovery remain BLOCKED. P1a's `cmt catalog` stays read-only and behavior-compatible.

## Code-specific baseline findings to respect

- Current `catalog.adapters.tcgdex.translate_batch()` translates a versioned P1a synthetic envelope to ordered `Observation | RecordError` and allows optional top-level `captured_at`. Its per-record adapter uses that envelope time; invalid records can become safe `RecordError`.
- `catalog.resolver.resolve()` maps those observations to `BatchResult(records, entities)`; accepted targets and their parent closure come from a validated **manifest**, not provider IDs or names. Candidates have a contextual `ExternalReference` but no CMT ID; rejections have fixed safe error categories.
- **`BatchResult.to_dict()` loses the normalized observation's `name`, `release_date` as observed, `provider_updated_at`, `captured_at`, `set_reference` and `card_number`.** Do not persist this output as the only input. The application composition must bind each validated normalized item to its corresponding indexed resolution, detecting mismatch rather than silently zipping disparate lengths/indices. The persistence boundary must independently validate arbitrary programmatically constructed dataclasses.
- P1a treats capture timestamp as optional; P3a must require explicit capture at its **new persistible boundary** without modifying P1a backwards. Preserve release date, provider update, capture and first-local-persistence time as separate semantics.
- `src/card_market_tracker/cli.py` currently implements `--version`, `diagnose`, and read-only `catalog`; `logging_json.py` uses a strict event/category/field allowlist. Add, don't break; the five P1a smokes plus P0 regressions remain mandatory. Python 3.13, stdlib-only runtime is current, `compose.yaml` holds one-shot commands, Docker `USER 10001:10001`, CI has four jobs (quality/compose/amd64/arm64).

## Delegation, ownership and checkpoints

**Engineering Lead owns:** verified Git/worktrees; task decomposition; shared `cli.py`, `logging_json.py`, `compose.yaml`, Docker/CI scripts, lockfile; integration sequencing and evidence ledger. Assign non-overlapping file ownership **before** parallel edits. Keep review and test authors independent.

**Checkpoint A — design before schema/code:**
- **ARQ + DB-OWNER** (possibly one author) inspect P1a identity, contracts and ADR-0003; design ADR-0004 (or next actual free number) with Context/Decision/Alternatives/Consequences/Status/Revisit. Decide minimal SQLite schema, source-of-truth/invariant mapping, `sqlite3` connection lifecycle under Python 3.13, journal/synchronous, FK enforcement on **every** connection, transaction/DDL atomicity, writer lock budget <=5s, read bounds, conflict categories, integrity check, backup and restore. Single host/one writer, no DB abstraction without consumer. Determine DB metadata/version and incompatible/future/foreign DB handling with no reset.
- Define documented **versioned persistible input and storage/read contracts** refining `INGESTION_V1` (do not change P1a semantics). Decide exact persisted metadata, nulls, UTC normalization, maximum sizes, meaningful manifest context for replay, safe fingerprint canonicalization (order, duplicates, version, field nulls), schema indexes, candidate references, error/result taxonomy, stdout JSON and CLI exit codes. A fingerprint is only a replay equivalence check, **never** a product ID. Decide first-persisted timestamp semantics and avoid global `first_seen_at`.
- No implementation until those decisions are reviewed for contradictions with the phase contract. Don't fabricate a second production schema solely to satisfy migration testing.

**Checkpoint B — write path, transactional failures:**
- **BE / DATA authors** own distinct P3a persistence modules and author tests/fixtures after design. Implement explicitly validated synthetic-only input with externally supplied **UUIDv4 `batch_id`** stable across retries and independently generated per-attempt `run_id`. Require explicit `captured_at` UTC instant (wrapper allowed), reject disagreement with P1a envelope capture. No inferred timestamp from execution clock, provider update or release date. `documented`/`observed` must fail before any retention. Reject contradictory identity/relationships, including incoming CMT ID already stored differently. Preserve all accepted/candidate evidence snapshots, including exact candidate reference and category **without** a CMT ID/promotion. Invalid records: only safe indexed categorical/aggregate rejection summary, never raw payload/name/reference or exception text.
- One transaction per batch must encompass verified curated entity parent closure, batch metadata, accepted/candidate observations and rejection summary. Inject actual failures after intermediate writes and assert rollback. Never `INSERT OR REPLACE` or silently reassign targets. Read-only manifest remains identity authority; DB records projections, not a new curator.
- Replayed `batch_id` plus **equivalent normalized content and relevant manifest/resolver context** returns explicit `replay` with **zero new rows** and unchanged first persistence. Same token with changed content/context fails atomically; a new batch with later `captured_at` adds a historical observation even if field values are identical. Explain limitation when producer loses/replaces stable batch token. Keep error paths unable to print in-memory attempted counts as committed storage counts.

**Checkpoint C — operations and packaging:**
- Engineering Lead / **SRE** implement or coordinate minimal, separately named write/query/verify/backup/restore CLI commands; preserve P0/P1a commands. Specify and test JSON stdout, fixed errors and exit codes: recommended 0 clean/empty/replay, 3 partially accepted records/candidates/rejections, 2 globally invalid input or conflicting replay (document choice), 1 storage/IO/lock/corruption. Do not alter P0/P1a codes. Queries by batch/CMT ID/contextual candidate reference have allowlisted sort/filters, deterministic order, strict max limit; DB absent must **not** be created by reads.
- `sqlite3` backup API (or equivalent officially supported consistent backup) with timeout/contended writer behavior, `integrity_check` and `foreign_key_check`, destination-new only, reject symlinks/same inode/existing file/dangerous destination, and do not advertise incomplete backup as valid. Restore to a separate new destination and verify reopen, content, IDs, candidates and replay. Create operational runbook covering lock, incompatible schema, corrupt DB, permission errors, disk full, restart/power loss, WAL sidecars if selected, backup restore and storage growth; never mutate actual user DB during drills.
- Add explicit writable data mount owned for UID/GID 10001; fixture mounts must be read-only and container data commands run `--network none`, no ports/root/chmod777. Windows bind/volume setup documented. Prove same DB across two **separate** `docker run`/Compose invocations; a process-only test is insufficient. Extend logging V1 with allowlisted P3a events/result/error categories, `run_id`, durations, accepted/candidate/rejected/processed vs **committed new row counts**, and replay status. No raw text, SQL, paths, tokens, external references, exception text or names on stderr.

**Checkpoint D — tests / security / exact SHA:**
- Author deterministic fixture cases: valid, mixed, candidates, all rejected, empty, globally invalid, missing/contradictory capture, offsets, synthetic/documented/observed, duplicate record, replay equivalence/conflict, changed manifest context, later capture, malicious SQL-looking fields, hostile paths/oversize data, parent/identity collision, unsupported DB schema. Update `tests/fixtures/PROVENANCE.md`. No actual provider data, secrets or commercial payloads.
- SQLite file integration: reopen from second process, read ordering/bounds, PRAGMA foreign_keys each connection, injected mid-transaction error, terminate process before commit vs after commit, schema initialization rollback/no-op/future/foreign DB, finite lock timeout, corruption, permissions, simulated disk-full/IO **labeled simulated**, `backup`/`restore` equivalence and replay. No destructive tests on an existing DB. Test security/redaction, SQL parameterization and parser limits.
- Preserve wheel-outside-source and five P1a smokes, plus version/diagnose/config. Build `scripts/observation_persistence_smoke.py` or equally small harness: validate actual JSON content and stable-row replay across process and container restart, with fixture read-only + writable mounted DB. Integrate in `scripts/wheel_smoke.sh`, `scripts/container_smoke.sh`, Compose and `.github/workflows/ci.yml` **four jobs**. Use linux/amd64 and linux/arm64 QEMU and note that this is not physical Pi or power-loss certification.
- **SEC** performs input/SQL/replay/storage permissions/path/backup/data-rights and logs review; **SRE** reviews resource deadlines/durability/recovery/docker nonroot. Neither may claim production source access. Update threat model and R-03/04/05/06/10, record any deliberate important limitation as technical debt with ID/owner/impact/exit/horizon; preserve TD-001/002 unless evidenced exit.
- Independent **QA** (read-only) derives and actually executes risk/AC-driven tests against final exact SHA in isolated checkout; separate independent **REVIEWER** inspects final code blobs, architecture/ADR/contracts/rights/CI, Git/diff, security and evidence, also on exact SHA. All blocking findings corrected, then repeat exact-head review/checks.

## Mandatory quality gates — never infer PASS from P1a

Record **PASS/FAIL**, command, host/runtime, exact candidate SHA/tree and evidence for: frozen uv sync & unchanged lock; Ruff format/check; strict mypy; pytest unit/integration/contracts/regressions; full own-runtime coverage **>=85% lines and >=80% branches** without masking critical persistence code; sdist/wheel build and installed smoke outside checkout; dependency audit and secret scan; architecture/DB/security/SRE/docs reviews; offline Compose nonroot persistent-data test; linux/amd64 and linux/arm64 QEMU smoke; all **four GitHub CI jobs** for proposed PR head. Existing baseline 218 tests and 99.04/97.59 coverage belong to P1a, not P3a. An unrun mandatory gate is **FAIL**, not N/A.

Example baseline commands (adapt only to repo recipes):

```bash
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
```

## Required evidence and delivery

- Write `docs/phases/P3A_OBSERVATION_PERSISTENCE.md` with Phase, proposed status, branch/PR/head/base/tree, **MODEL PROFILE USED** (selected vs verified), specialists and independent authorship/reviews, objective, implementation, architecture/ADRs/contracts, **DATABASE CHANGES**, initialization/migration details, security/threat-model and technical-debt deltas, observability, unit/integration/contract/regression outputs, complete PASS/FAIL gates, AC-O01–AC-O15 individually mapped to exact evidence, limitations, open issues and recommendation.
- Update ADR(s), `docs/data-contracts/`, architecture, roadmap, testing/quality docs, README, runbook, fixture provenance and risks. Do not claim real Pi durability, provider rights, commercial history, or source health.
- Open a reviewable PR **without merging it**, with a compact external PR evidence ledger of checks and reviews for published head. Include exact current base/head/tree and clickable CI URLs; do not create self-referential commits just to include the PR's own SHA. Rerun reviews/tests after any substantive code change.
- Return a **Phase Completion Report** to the Phase Lead/Orchestrator with AC-O01–O15 evidence and pending failures. Only if every gate passes, conclude `READY_FOR_ORCHESTRATOR_REVIEW`. **Never** `PHASE CLOSED` and **never** self-authorize a merge.

## Handoff communication cadence

First response in Codex: (a) exact observed Git state vs authorized baseline and non-destructive plan; (b) file ownership matrix; (c) design decisions requiring ARQ/DB-OWNER, risk register and work breakdown; (d) available model selections and observable evidence. Then execute authorized independent work without pausing for routine approvals. Provide useful milestone reports at design freeze, implementation, QA, final candidate. If any local permissions/tooling block an action, report the exact command/error and continue other authorized work; do not claim a remote connector failure proves local Git cannot work.
