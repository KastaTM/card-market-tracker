# P4c — Codex Engineering Brief (execution handoff)

**Status:** implementation work authorized by the 00 — ORCHESTRATOR; not accepted, not closed. 2026-10-19 (Europe/Madrid). Source: `P4C_DISCOVERY_RESULT_JOURNAL_CONTRACT.md`; the latter prevails in every conflict.

## MODEL PROFILE — reproduce in Codex

- ChatGPT Phase Lead: preferred **GPT-6.1 Sol / High** in Work if available; **GPT-5.6 Sol / High** in normal Chat when actually available. This chat has not changed/verified model UI configuration.
- Codex Engineering Lead: request **GPT-6.1 Sol / Medium** for coordination/routine work, **High** for storage, integrity and contention. Specialists ARQ/DB-OWNER, BE/DISCOVERY, SEC/SRE, QA and REVIEWER: **GPT-6.1 Sol / High** where available. QA and REVIEWER must be different nonauthors.
- Escalate Medium→High on a **reproduced** difficult bug, contract boundary, schema corruption or concurrency issue. Consider **GPT-6 Astra / High** only for a difficult reproducible blockade if selectable. Never claim a model/backend actually ran unless observed. If those exact models are absent, inspect the available Codex selector and use the closest *available* model, documenting the difference rather than inventing an accepted configuration.

## Verified preflight

GitHub connector read-only verification on 2026-10-19:
- Repository: `KastaTM/card-market-tracker` (public, default branch main).
- `refs/heads/main`: `de63457bd6de26874a30d2afd688dcd8901e01ff`.
- Tree `41c0f758c8a4bf09cc719a1ce16073245a5aadda`.
- Parents, ordered: `112916382ce02486ca38eb14487220dbb24196e7`, `8af647697dd67859b38fc007d493a54642a1d62f`.
- Branch `feat/p4c-discovery-result-journal` absent at search time.
- **WRITE BLOCKER:** GitHub connector `create_branch` returned HTTP 403 `Resource not accessible by integration` despite visible metadata reporting push permission. No branch, PR or repository commits resulted from this call. Local `git ls-remote` unavailable because sandbox DNS could not resolve github.com. Do not assert that host worktree/status/remotes were inspected; run the preflight anew on Codex host.
- Historical P1c coverage/test reports are not P4c evidence.

## Engineering Lead: required sequence

1. Inspect `AGENTS.md`, `context.md`, `docs/ROADMAP.md`, `docs/ARCHITECTURE.md`, the P1c/P4b phase records, ADRs 0001–0008, Discovery V1/V2/V3, Storage V1/V2, logging, testing, threat model and technical debt; `git status`, remote, all branches/worktrees, `git fetch`, `git rev-parse`, and latest main tree. Preserve unrelated edits/worktrees. If current main != authorized baseline, **stop on divergence and report it** rather than silently rebase.
2. Create `feat/p4c-discovery-result-journal` **from exact authorized SHA**, after preflight. Archive the supplied P4c contract verbatim (provided in this handoff) and write a dated roadmap note: P1c CLOSED by Orchestrator in chat, P4c OPEN, P2/P6a/retail discovery BLOCKED. Do not invent a GitHub closure comment.
3. Set ownership **before** concurrent work:
   - Lead: Git/ref control, integration, request-to-comparison app boundary, CLI and release evidence; final docs and CI integration.
   - ARQ/DB-OWNER (author): `journal_schema.py`, `journal_storage.py`, ADR-0009 and storage contract, schema/backup tests.
   - BE/DISCOVERY (author): `journal_application.py`, journal CLI, application/query tests and seventh smoke; do not edit schema owned by DB simultaneously.
   - SEC/SRE (read-only early, then review): paths, alias/hardlink/symlink, hostile SQLite, byte/time budgets, fault injection, backup/restart, redaction, ARM64.
   - QA: independent negative/edge probes, not an implementation author.
   - REVIEWER: final independent review on frozen exact SHA/tree, different from QA and all authors.
   Avoid shared-file concurrent writes and shared Git operations; use sequential integration.
4. Define typed interfaces and storage canonicalization in the two new contracts *before coding*. Sign off the exact event/result grammar and error categories. Keep comparator pure, no provider imports, no new source bytes, no changes to cmp3/evt3/old namespaces.
5. Implement storage and trusted admission, then tests, then CLI, recovery/backup, seventh smoke and CI integration. Authors may inspect the local handoff prototype but must not equate its isolated tests with project gates.
6. Execute local end-to-end suite, independent QA probes, full CI on **final exact candidate** and REVIEWER. Any code change after final review voids that SHA's attestations.
7. Open PR **without merge**. Publish a full external immutable ledger, read back comment and attach real logs/objects; use exact base/head/tree. Report only reproducible PASS, else FAIL/BLOCKED.

## Hard architectural boundary

Public record API accepts **only** `(request v3 file/object parsed through multi_input, capture SQLite path, journal SQLite path, timeout)`; derive result with the unchanged `read_multi_revision_snapshots` and `multi_comparison.compare` on fully verified snapshots. No public `result`, no trusted `ScopedDiscoveryResult` constructor, no declared hash or `verified` flag. An internal writer receipt is issued only after full admission and binds canonical request, semantic result and digest by content. Writer validates receipt and limits before any mutation. Application receipt is an in-process boundary, not cryptographic authentication of privileged code.

One read-only capture connection/transaction yields a coherent snapshot before journal writes. There is **no distributed transaction** across DBs. Verified snapshots are immutable by existing contract; journal atomicity covers comparison and all occurrences in a single `BEGIN IMMEDIATE`/commit transaction. Capture DB retains schema2 and its five tables; journal has exactly three owner/business tables plus declared indexes, separate application ID and `user_version=1`.

## Suggested file map / API (subject to repo inspection)

- `src/card_market_tracker/discovery/journal_schema.py`: schema SQL, separate app id, exact metadata and sqlite_master inventory validation.
- `src/card_market_tracker/discovery/journal_storage.py`: storage read/write/verify/backup/restore, private receipt consumption; immutable row schemas; monotonic operation budget, path checks and SQL pre-materialization guards.
- `src/card_market_tracker/discovery/journal_application.py`: `record(captures_db, journal_db, request_path, *, timeout=2.0)`, `recompute(...)`; reuse upstream verified read/compare. Keep application as only exported admission entrypoint.
- `src/card_market_tracker/discovery/journal_errors.py`: fixed categories and 1/2 exit mapping, no raw exceptions or path/SQL in log.
- `src/card_market_tracker/cli.py`: **additive** `discovery-journal` group; no changes to legacy CLI output/exit.
- `tests/test_discovery_journal_*.py`: storage/admission/CLI/adversarial/QA tests with synthetic and reviewed R0/R1 fixtures.
- `scripts/discovery_journal_smoke.py`: seven-harness suite extension, separated processes and replay/restore.
- docs: this contract, brief, ownership, ADR-0009, `DISCOVERY_JOURNAL_V1`, `DISCOVERY_JOURNAL_STORAGE_V1`, runbook, architecture, threat model, gates, testing, technical debt and roadmap.

## Data model and invariants

1. `journal_metadata`: unique singleton, exact owner string, schema=1. SQLite `application_id` distinct from captures `0x434D5431`, `user_version=1`.
2. `comparisons`: PK `comparison_id` (`cmp3:` plus 64 lowercase SHA hex), canonical normalized request, full canonical result, SHA-256 over canonical semantic tuple `{journal_version:1,request:<object>,result:<object>}`, first recorded UTC micro timestamp (not identity). Result payload maximum 16 MiB. Canonical JSON uses `ensure_ascii=True`, `sort_keys=True`, `separators=(',',':')`, `allow_nan=False`; no b32/base64 ambiguity.
3. `event_occurrences`: `PRIMARY KEY(comparison_id,event_id)`, `ON DELETE RESTRICT` FK (no destructive API), deterministic `ordinal` UNIQUE per comparison, optional exact canonical event JSON; no `UNIQUE(event_id)` across comparisons. The result's events array equals stored occurrences in order and content exactly. Event count 0 is valid for `baseline`/`no_discoveries`.
4. Same comparison same canonical content: replay and preserve first_recorded_at/content; same comparison different canonical content: explicit conflict with zero mutation (compare content, not just SHA). Same event in distinct comparisons: two occurrences with evidence, never collapse.
5. Local verify: exact schema/id, pragma integrity+FK checks, JSON strict/finite/bounded, canonical equivalence/digest, cross-row identity, event order/count/equality. NOT origin authentication. Recompute: re-read original capture DB with retained request and compare both cmp ID and **entire** semantic result. Altered/absent capture source = failure, never repair/drop.
6. `record` starts one 2 s default/<=5 s budget at request entry. Pass remaining to existing snapshot reader and enforce again before SQL; do not reset between stages. SQLite busy/progress limits and explicit bounded loops. Don’t claim hard latency under blocked kernel IO.
7. `get` is exactly one cmp; `list` sorted stable by cmp id, cursor based on last cmp ID; `event-occurrences` filtered exact event ID sorted by cmp id, cursor from last cmp ID. Default 100, max1000, response summaries <=1MiB; keyset pagination is **not** an all-pages snapshot amid concurrent inserts.
8. `init` only explicitly and exclusive create in trusted local directory, `record/get/list/verify` do NOT initialize. Backup/restore use SQLite backup API and validate source/destination ownership and content. Reject samefile/hardlink/symlink/captures-as-journal and vice versa without altering foreign files.
9. Errors map fixed input/version/profile/unsupported evidence/limits to exit2; path/ownership/schema/lock/deadline/IO/corruption/recompute mismatch to exit1, comparison collision to exit2 unless contract explicitly chooses storage class. No operation converts missing DB or corrupt source into empty success.
10. Logs per journal invocation: operation, run_id, duration_ms, outcome `inserted|replay|ok|error`, bounded event/comparison counters, error_category. NEVER log names, references, selectors, payloads, URLs, filesystem paths, SQL, raw exception text. Stdout is contracted evidence.

## Test matrix and failure-first probes

- Admission: forged result/receipt, mutated DTO after issue, missing capture DB, mismatched profile, bool-as-int, extra fields, duplicate JSON keys, NaN/infinite, overly deep/string/oversized input, R0/R1 source locks.
- Replay/conflict: same cmp replay after reopen first time unchanged; injected semantic conflict (private seam) does not mutate; two explicit windows with same evt3 preserve different evidence; base/no_discoveries valid.
- Atomicity: force SQLite failure after comparison row, after first occurrence, during subsequent occurrences; rollback leaves no comparison/events. Concurrent independent processes with same cmp produce one insert + replay or bounded deadline; no duplicates.
- Verification: divergent event vs parent, missing ordinal, duplicate/extra row, wrong FK, truncated JSON, excess size, wrong digest, coherent tampering, owner/schema changed, journal replaced with captures DB, malformed cursor, query paging with 1000+ fixtures without omissions.
- Recovery: process termination between inserts and commit, restart, SQLite backup/restore after actual writes, verify/recompute restored DB, original captures still immutable/byte-stable.
- Bounds: 1MiB request / depth16 / nodes20k / string1024; max33 batches/33k records/1000 events; journal16MiB result,1MiB page, 100-1000 limit, 2s default/5s max, SQL guards BEFORE hostile large TEXT loading.
- CLI/regressions: old `discover`, `discover-scoped`, `discover-multi-revision` byte-for-byte stdout and code unchanged; exceptions mapped; no implicit selection/transport; separate processes.
- Real: four R0→R1 comparisons each `no_discoveries` with zero events; only synthetic profile can demonstrate positive events.

## Required quality gates (all PASS, no inherited credit)

`uv sync --frozen --no-install-project`, `uv sync --frozen --no-build-isolation`, `uv run ruff format --check .`, `uv run ruff check .`, `uv run mypy --strict ...` per existing repo recipe, full pytest+coverage at least **85% lines / 80% branches**, `uv build --no-build-isolation`, installed external wheel suite, audit and secret scan, Compose, `linux/amd64`, QEMU `linux/arm64`. CI stays at **four jobs**; preserve all six smokes and add journal as seventh. No new skips, no relaxed thresholds, no new external fetch, no CI dependency on secrets. Document source health and remaining TD-001 to TD-005 explicitly BLOCKED/OPEN.

## Evidence handoff to Phase Lead / Orchestrator

Phase Completion Report: Phase; Proposed Status; branch/PR/commit; base/head/tree; actual model configurations; all specialists and ownership; objectives; implementation; architectural changes; ADR; contracts; DB changes; threat-model changes; technical debt; observability; tests with commands; 4 complete CI logs/results; all AC-J01 through AC-J16 individually PASS/FAIL/BLOCKED with evidence; limitations and open issues. Finish `READY_FOR_ORCHESTRATOR_REVIEW` **only once all mandatory evidence passes**. Otherwise report actual BLOCKED or in-progress state. **Never merge, close or open another phase.**

## Blocker record from this handoff

This execution environment does not expose Codex subprocess/subagent sessions and the available GitHub connector returned write-403 on branch creation. Host `git`, full local repo, Docker, QEMU and CI cannot be executed or certified here. The included design/prototype is **not** a reviewed/validated implementation candidate. Codex must integrate/test/attest it or implement its own code on the authoritative repository. Do not mark any unexecuted gate PASS.
