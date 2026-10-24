# P5b — Codex Engineering Brief / implementation handoff

Implementation-stage note (2026-10-24): this is the original design handoff;
its design-only status/blockers below describe 2026-10-23. Current work and
executed evidence are in [the engineering report](P5B_WATCHLIST_EVALUATION_JOURNAL.md).

**Phase:** P5b — Watchlist Evaluation Journal & Signal Deduplication\
**Authority:** 00 — ORCHESTRATOR; phase OPEN, not accepted/closed.\
**Baseline authorized:** main `ddd5fe3bbc7e40947bd838f71ee25e7046ff1b7e`, tree `f0eaf874e8671f75904ece1f618c283d7ff91536`.\
**Source:** [phase contract](P5B_WATCHLIST_EVALUATION_JOURNAL_CONTRACT.md).\
**Current deliverable status:** OFFLINE DESIGN HANDOFF ONLY — NOT IMPLEMENTED.

## MODEL PROFILE — requested and observable

- ChatGPT Phase Lead: opening asks GPT-6.1 Sol/High in Work or Astra/High in
  normal chat; this session is labelled GPT-6, actual reasoning selection not
  verifiable. Do not claim requested variant was served.
- Codex Engineering Lead: GPT-6.1 Sol/Medium **when actually available in Codex**;
  use High for immutable identities, transaction CAS, time ordering, corruption
  and recovery; QA/REVIEWER separate High. Check the actual Codex selector and
  document it in MODEL PROFILE USED. No Codex session was invoked here.
- Escalate to strongest available High reasoning for disagreement or difficult
  debugging; routine deterministic code Medium. Never invent a selector.

## Preflight (Codex must repeat; not inherited from this offline design)

1. Read `AGENTS.md`, context.md, docs/ARCHITECTURE.md, roadmap, gates, P5a
   contracts/ADR-0012 and P5a Python. Check git remote/main/tree/parents,
   branch list, worktrees and clean status **before changes**.
2. Read-only GitHub connector preflight on 2026-10-23 confirmed remote main at
   exact authorized SHA/tree and parents. Current execution container cannot
   resolve github.com for git clone; GitHub branch creation via connector
   returned 403 `Resource not accessible by integration`. No branch/PR/merge was
   created. A Codex session with working `git`+`gh` may perform authorized
   branch/PR actions after repeating preflight; never modify credentials or
   bypass 403; declare BLOCKED if unavailable.
3. Create `feat/p5b-watchlist-signal-journal` from exact main only after these
   checks, without moving main or disturbing other worktrees. Record divergent
   main if baseline changes; do not rebase/integrate silently.
4. Copy this bundle into repository with exact paths, then inspect/reconcile
   documents against authoritative repo and verify design freeze **before**
   implementation. Integrate roadmap new top entry; do not overwrite history.
   Markdown contracts in the bundle are **proposed, not yet merged**.

## Goal, boundaries and explicitly excluded work

Deliver durable independent **synthetic** P5a evaluation journal, per-rule
NO_MATCH -> MATCH transitions and replay-aware dedup, strict chronology,
recomputable record/sequence heads, CLI/pagination, backup/restore and offline
11th harness. Reuse existing full MANIFEST_V1 and P5a revision, sample and pure
evaluator **without altering their behavior**. Preserve current core/retail/
Discovery/alert/delivery databases and contracts byte-for-byte.

Out: external providers, commercial prices/stock, credentials, sources, URLs,
new discovery data, scheduled collection, implicit latest, network, daemon,
Telegram/P8 links, real market events, opportunities, migrations of accepted
stores, full P5 closure. P2/P6a/retail Discovery remain BLOCKED. TD-001..005 OPEN.

## Frozen identity and input decisions

See [WATCHLIST_JOURNAL_V1](../data-contracts/WATCHLIST_JOURNAL_V1.md),
[WATCHLIST_JOURNAL_STORAGE_V1](../data-contracts/WATCHLIST_JOURNAL_STORAGE_V1.md),
[WATCHLIST_SIGNAL_V1](../data-contracts/WATCHLIST_SIGNAL_V1.md),
[ADR-0013](../adr/0013-watchlist-synthetic-journal.md).

- Watch key/revision and frozen config/identity from validated P5a; full
  manifest reparsed each record/recompute; historical revision allowed,
  never a notification authorization. Limit retained evidence to normalized
  P5a entry + synthetic current/previous + as_of + derived full P5a result.
- Canonical JSON sorted keys, ASCII escapes, compact separators, no NaN,
  UTF-8; lowercase SHA256 of ASCII domain + literal 0x00 + canonical JSON.
- Sequence `wjs1_`: watch_id, revision, policy_version, series_key;
  evaluation `wje1_`: seq, policy, complete entry, complete normalized
  samples, normalized as_of; signal `wsig1_`: sequence, rule, immediate
  previous/current eval, fixed semantic kind and synthetic mode. These are
  dedup identifiers, not origin authentication.
- Freeze exact bytes *before coding*. Existing synthetic P5a fixture vectors
  and expected hashes are in `tests/fixtures/p5b_identity_vectors_v1.json`,
  with runnable independent stdlib `scripts/p5b_identity_oracle.py` and
  `tests/test_p5b_identity_vectors_reference.py`. QA must independently
  calculate, not just call the productive digest helper.

## Sequence state machine

- First record is **baseline**, even MATCH or optional external previous: 0
  journal signals. New append requires strict increasing current.observed_at,
  nondecreasing as_of, unused sample_id, and explicitly supplied previous
  identical to last recorded current. No backfill, latest implicit, reorder.
- Exact historical replay is idempotent without moving head/persisted_at.
  Reused sample_id with changed content/as_of, changed identity/config for the
  same revision, equal-time different sample, or competing successor fails
  without partial writes. Different revision or series is new sequence.
- Per-rule transition `NO_MATCH -> MATCH` only when previous and new current
  observations both fresh against the **new** as_of. Other states, stale
  predecessor, disabled or first baseline break continuity; persistent MATCH
  never duplicates. Price and restock both may independently signal.
- Use pure transition function and transactionally derived signals, not
  caller-provided DTO; `BEGIN IMMEDIATE` head check, evaluation+signal+head
  commit together, competing writers at most one valid successor.

## Components and agreed ownership

Read [`P5B_OWNERSHIP.md`](P5B_OWNERSHIP.md). Engineering Lead owns integration,
branch, root CLI, smoke, CI and final evidence. ARQ/BE own admission,
validation and pure transition; DB-OWNER owns isolated schema/store; SEC/SRE
review threats and recovery. QA/REVIEWER are two genuinely different agents,
neither author; probes on frozen **final** SHA/tree (redo both if modified).
Concurrent editing same file or git state is forbidden.

Suggested isolated module `src/card_market_tracker/watchlist_journal/` with
`errors.py`, `models.py`, `identity.py`, `transitions.py`, `application.py`,
`schema.py`, `storage.py`, `cli.py`. Shared `src/card_market_tracker/cli.py`
registration only. Avoid generic ORM/framework or nonessential new package.
Use P5a's public validators/application/storage functions rather than changing
P5a itself. Reuse existing secure path/inode/sidecar and Budget patterns.

## CLI, integrity and fail-first behavior

Freeze the CLI named in the storage contract:
`cmt watchlist-journal init|record|get|list|signal-get|signal-list|verify|recompute|backup|restore`.
Explicit journal DB; record takes distinct Watchlist DB, full manifest,
watch ID, exact revision, current sample, optional previous and as_of.
Get/recompute select explicit eval ID. Separate read-only local verify vs
against-origin recompute. All responses versioned JSON, safe error categories,
operation timing/counters logs; no sensitive samples, amounts, preferences,
names, filenames, tokens or payload text in structured logs.

Max 1MiB input, depth16/nodes20000/string1024, tighter P5a field limits,
canonical <=64KiB; paginated list default100/max1000, max1MiB output and
cursor bounded/filter-bound; overall deadline default2s/max5s. No implicit
init and no full Watchlist scan. Each error/timeout is not `no results`.

New owner `card-market-tracker.watchlist-journal`, application_id
`0x434D5451`, schema1, four STRICT owner tables, exact inventory/triggers/FKs,
no migration. Verify all snapshots/result/links/heads and exact recomputed
signal fold, reject rehashed changes. Backup/restore only to new safe paths;
sidecar collision/reparse/symlink/hardlink/inode checks; no cleaning another
writer's evidence. No claim against privileged consistent rewrite, real
power-loss certification or original-provider authenticity.

## Tests and quality gates (all must have executed evidence)

- Admission: wrong/malformed manifest, missing/mismatched revision/target,
  disabled with malformed sample, caller-supplied result ignored/rejected.
- Identity: golden canonical byte preimages/digests independently computed;
  change of any semantic field changes evaluation ID, different presentation
  of equivalent timestamps normalizes to same.
- Rules: first MATCH no signal; NO_MATCH->MATCH, MATCH->MATCH, second episode,
  two rules simultaneous, OR does not hide rule, UNKNOWN, INDETERMINATE,
  SKIPPED, stale/no continuity, inclusive max-age boundary.
- History: revision/series isolation; sample_id collision and re-eval as_of
  conflict; previous mismatch, chronology/as_of violations; replay old no
  head/clock changes, two same-process concurrent writers and incompatible
  successors, injected fail before/between eval/signal/head rollback.
- Tamper: invalid DB owner/schema/trigger/index/FK, missing/extra/tampered
  signals, overwritten evaluation result (even rehashed), wrong head,
  duplicate/hole, P5a origin changed/absent; local verification/recompute
  distinguished. Whole-history timeout no partial PASS.
- Recovery/limits: exclusive verified restore, backup evidence, unsafe
  symlinks/sidecars, locks, disk/IO, restart, parsers, pagination/cursor,
  redacted logs, zero network sockets and nonmutation of all prior DBs.
- 11th installed-wheel multi-process offline harness
  `scripts/watchlist_journal_smoke.py`: init, first NO_MATCH baseline, next
  MATCH two independent signals, replay unchanged, MATCH persistence, second
  episode, verify/recompute, backup/restore, process restart. Retain ten
  historical harnesses.
- CI four jobs: Quality, Compose, linux/amd64, linux/arm64 QEMU. Ruff
  format/check, strict mypy, full pytest, coverage >= current stricter gates
  (at least 85% lines/80% branches), wheel/sdist frozen install, dependency
  audit, secret scan, Docker startup/smoke. No live test or Telegram.

## Acceptance matrix — evidence MUST be bound to final head/tree

| AC | Verification demand |
| --- | --- |
| S01 | Baseline exact, full contract versioned, roadmap P5a closed/P5b open |
| S02 | Original manifest/revision admission, independently recomputed P5a |
| S03 | Bounded immutable synthetic-only journal retention; P5a unchanged |
| S04 | Versioned wjs1/wje1/wsig1 + literal independent SHA vectors |
| S05 | Sequence isolation by revision/series/policy/product |
| S06 | Initial MATCH still signal-free baseline |
| S07 | Per-rule two-episode/double-rule cases, OR noninterference |
| S08 | Unknown, stale, disabled, indeterminate continuity reset |
| S09 | Strict time/as_of/previous/sample ID, no latest inference |
| S10 | Ancient replay unchanged, divergent replay conflicts and rollback |
| S11 | Atomic evaluation/signals/head, concurrency head guard |
| S12 | Deep integrity/result/fold/heads recomputed, tamper detected |
| S13 | Original-source recompute failure/success independent of local verify |
| S14 | CLI parsers/pages/budget/log safety, zero product network |
| S15 | Reopen/recovery/verified exclusive backup restore and other DB safety |
| S16 | Full regression + 11th harness + all four CI jobs green |
| S17 | Independent QA & REVIEWER full reports and scripts on final SHA/tree |
| S18 | ADR/contracts/threat/runbook/debt/observability/docs/evidence |

### Required docs sync (implementation stage)

Incorporate this contract into repo, add NEW top roadmap entry attributing P5a
closure/P5b opening to supplied Orchestrator chat (do not fabricate remote
closure comment); update architecture, testing, gates, logging, threat model,
runbooks, technical debt and AGENTS map. ADR significant decisions documented
with context/decision/alternatives/consequences/status/revisit. Preserve P5a/P2
contracts. Avoid committing confidential samples, commercial data, tokens.

## Handoff and status

Phase Completion Report must include branch/PR/commits/head/tree, actually used
model profiles and agents, individual AC evidence, 4 CI jobs, full test outputs,
coverage, two independent reports from final commit, known limitations, bugs and
recommendation. End `READY_FOR_ORCHESTRATOR_REVIEW` **only** after all applicable
gates PASS; never `PHASE CLOSED`. Merge requires separate Orchestrator authority.

**Blocking facts at this handoff:** No local checkout/network to clone, no
Codex tool/session, and GitHub connector returned 403 when creating a branch.
Thus remote files/PR, product implementation, test suite, final gate evidence,
QA/REVIEWER reports and acceptance are **not completed**. This brief/ADR and
contracts are design artifacts pending integration, not a final candidate.
