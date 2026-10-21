# P8a — Codex Engineering Brief (execution specification)

## MODEL PROFILE

- **ChatGPT Phase Lead:** GPT-6 / High in the standard ChatGPT model menu. The original Orchestrator contract conditionally recommends GPT-6.1 Sol / High in Work, or GPT-5.6 Sol / High if offered. Do not claim those labels exist without checking the user's actual client.
- **Codex Engineering Lead:** request `gpt-6.1-sol` / Medium **only if this exact model is available in Codex**; escalate to High for trust, identity, SQLite concurrency, rollback and recovery. If absent, use the best actually offered GPT-6 engineering-capable Codex model with Medium/High as appropriate, record the exact selector result, and do not invent a backend switch.
- **QA and REVIEWER:** separate nonauthor agents, preferably `gpt-6.1-sol` / High if actually available. Author != QA != final reviewer. For difficult reproducible blocks, try High before any higher-tier selection.
- **Authority:** P8a is OPEN by Orchestrator chat. Phase Lead can report `READY_FOR_ORCHESTRATOR_REVIEW` only after evidence; cannot merge, accept or close. `main` must not be modified by this phase.

## 1. Engineering mission and immutable boundaries

Repo: `KastaTM/card-market-tracker`. Exact authorized base: `b89fff319a94e5eb6e4b7bdad944e879bad371f6`; tree: `8f62a1d85b375ee839dcd95e09a578cb643c85b6`; ordered parents `de63457bd6de26874a30d2afd688dcd8901e01ff` and `9fb53144dec521d0dde49c02d41022be831421c2`. Intended branch: `feat/p8a-offline-alert-outbox`. P4c PR #12 is merged. Inspect refs, local worktrees and uncommitted changes BEFORE touching any working copy. If remote main advanced, report delta to Phase Lead; do not silently rebase or overwrite others.

Goal: from ONE explicit journal comparison `cmp3` and THREE separately specified SQLite paths (captures, journal, outbox), plus ONE explicit local destination alias, create durable, deterministic, pending offline alert intentions. One alert per `(destination_key,evt3)` and one window-evidence association per `(alert_id,cmp3)`. Same evt3 across two cmp3 windows must keep one message/intent and two frozen associations. Never accept arbitrary result JSON/DTO as authority. Recompute comparison using original verified captures before outbox writes. Do not alter P4c identity, comparator, schema, profile registry, source materials or API behavior.

Out of scope: network delivery, Telegram/email/webhook, tokens/chat IDs, dispatcher, leases, retries, scheduler, sent/delivered state, new sources/acquisition, product/pricing/stock/watchlist/retail/launch/opportunities, API/frontend, promotion, deletion, automatic retention, global quotas. P2, P6a and retail Discovery remain BLOCKED. No P5/P8b opening. Preserve exact R0/R1 and existing synthetic corpus; no source purchases or external requests.

## 2. Preflight and integration reconnaissance

Read `context.md`, `AGENTS.md`, `docs/{ENGINEERING_OPERATING_MODEL,ARCHITECTURE,ROADMAP,QUALITY_GATES,TESTING_STRATEGY,TECHNICAL_DEBT}.md`, `docs/threat-model/THREAT_MODEL.md`, `docs/adr/0009-discovery-result-event-journal.md`, all three `DISCOVERY_{V3,JOURNAL_V1,JOURNAL_STORAGE_V1}.md` contracts, `docs/runbooks/DISCOVERY_JOURNAL_RECOVERY.md`, and P4c ownership/contract/engineering brief. Inspect:

- `src/card_market_tracker/discovery/journal_application.py`: `get`, `read_multi_revision_snapshots`, `parse_request`, `compare`, canonical pair and content checks; its receipt boundary is private and local, not a cryptographic signature.
- `discovery/journal_storage.py`, `journal_validation.py`, `journal_schema.py`, `journal_errors.py`, `journal_cli.py` for bounded SQLite, `_path`, `reject_same_file`, `Budget`, journal verification semantics and CLI mapping.
- `discovery/multi_comparison.py` for event intrinsic fields versus window evidence; `cli.py` for parser registration/dispatch; persistence path protections and existing seven harnesses; CI four-job matrix and container UID/network restrictions.

No local checkout or review workspace state is inferable from remote GitHub. Before coding, record actual remote, checkout, dirty files, worktree list, branch create result, Python/uv/Docker/GH capabilities and baseline delta. Never pretend unavailable tools ran.

## 3. Team assignment and ordered integration

Engineering Lead owns repo preflight, interface freeze, shared Git actions, final integration, gate orchestration, evidence, PR. Agree on interfaces and table names **before parallel edits**. Assign:

| Role | Exclusive write ownership | Duties |
| --- | --- | --- |
| ARQ/DB-OWNER | `src/card_market_tracker/alerts/schema.py`, `storage.py`, `errors.py`; DB-specific tests, ADR-0010 and storage contract | STRICT schema, owner, atomicity, paging, verification, backup/restore, concurrency |
| BE | `alerts/application.py`, `policy.py`, `render.py`, `cli.py`; `src/card_market_tracker/cli.py` integration; application/CLI tests and new smoke | Original-origin admission, immutable verified snapshot, message, fixed CLI and redacted logs |
| SEC/SRE | Independent risk analysis and runbook/security review; documentation changes only with allocated files | hostile input/path/alias, byte/time budgets, recovery and failure-first probes |
| QA | no author or official baseline test-file edits; independent probes in isolated ignored worktree/path | independently compute alt1, dual-window, mutation, hostile DB, recovery and read-only evidence |
| REVIEWER | read-only, separate from QA and all authors | frozen SHA/tree code/contract/security/docs review, four complete CI logs |
| Engineering Lead | branch, shared architecture/roadmap/gates/docs, harness integration, PR and published readback | conflict resolution, execution evidence, no unilateral scope expansion |

Parallelize read-only assessment or disjoint-file authorship; coordinate changes in `cli.py`, requirements/lock and CI exclusively. Do not launch redundant roles merely for agent count.

## 4. Versioned public API / CLI proposal (freeze prior to coding)

Use package `src/card_market_tracker/alerts/` separate from `discovery/` and `persistence/`, with pure `policy.py` + `render.py` and independent `application.py`, `schema.py`, `storage.py`, `errors.py`, `cli.py`. Group `cmt alert-outbox` has subcommands below; all require `--outbox-db PATH`, optional `--timeout SECONDS` default 2, upper bound 5 (finite, nonbool). Define typed Python service call analogues and make stdout canonical JSON, integer `version:1`, `operation`, `result`; failures fixed `error_category`, no raw traceback or partial results.

| Subcommand | Required parameters other than outbox DB | Extra parameters / output |
| --- | --- | --- |
| `init` | none | `schema_version:1`; exclusive new DB only |
| `enqueue` | `--captures-db`, `--journal-db`, `--comparison-id CMP3`, `--destination-key ALIAS` | counts `alerts_new`, `alerts_existing`, `associations_new`, `associations_existing`, `events`; result `inserted` or `replay` (document mix semantics) |
| `get` | `--alert-id ALT1` | intrinsic intent, frozen message, digest, first timestamp, `pending`, channel and versions; not entire evidence history |
| `list` | none | optional `--limit N`, `--cursor ALT1`, `--destination-key ALIAS`; bounded summaries, `next_cursor` |
| `evidence-list` | `--alert-id ALT1` | optional `--limit N`, `--cursor CMP3`; summaries keyed by comparison_id, no full event history |
| `evidence-get` | `--alert-id ALT1`, `--comparison-id CMP3` | one frozen full event and journal semantic digest; bounded explicit result |
| `preview` | `--alert-id ALT1` | frozen text and versions, no state mutation, network or consumption |
| `verify` | none | local inventory, integrity, complete semantic/row consistency, counts; timeout never partial PASS |
| `recompute` | `--captures-db`, `--journal-db`, `--alert-id ALT1`, `--comparison-id CMP3` | origin-recompute for ONE association; read-only |
| `backup` / `restore` | `--destination NEW_PATH` | independent SQLite snapshot and reopen verification; exclusive new target |

Do not add `--latest`, `--result-json`, `--send`, `--ack`, `--retry` or `--chat-id`. Existing `discovery-journal` CLI remains bit-for-bit compatible. Freeze exact JSON and category map in the versioned contract BEFORE implementation; adjust names only if an existing standard makes them incompatible, document reason and maintain contract coverage.

## 5. Admission: a single frozen verified comparison

`enqueue(captures_db,journal_db,outbox_db,comparison_id,destination_key,*,timeout=2.0)` must:

1. Start a **single** `Budget(timeout)` immediately. Strictly validate CMP3 and ASCII destination (suggest `^[a-z][a-z0-9_-]{0,63}$`) before IO; check all three paths are distinct by file identity (and secure-path/sidecar rules); require journal and captures to exist and outbox initialized.
2. Obtain **one retained pair** via P4c `journal_storage.get(...timeout=budget.remaining())`: request, full comparison, `content_sha256`, comparison ID; local validation alone is not origin authority.
3. Parse retained strict request with existing `multi_input.parse_request`; call existing `read_multi_revision_snapshots(captures_db,request,timeout=budget.remaining())`, then pure `multi_comparison.compare(request,captures)`. Full canonical semantic result and comparison_id MUST equal the retained frozen pair; never verify one pair and consume a different one. Use existing `journal_validation.canonical_bounded` and `validate_pair`, preserving identity/size checks. On failure zero outbox writes.
4. Build pure versioned intentions from that **same** matched local result, including `event_id`, event `type`, complete `reference`, `status`, `category`, nullable frozen `cmt_id`, `current_batch_id`, `captured_at`, `first_observed_in_window_at`, `profile`, evidence level/mode; omit mutable/window-varying `history` and `comparison_id` from the intrinsic alert intent.
5. Render one deterministic plaintext message per intrinsic intent, then attach each full canonical event to a `(alt1,cmp3)` association along with P4c journal semantic digest; **do not** overwrite older-window evidence. Reject references to missing events/invalid profile/wrong version; baseline/no_discoveries => success with zero writes.
6. Under one BEGIN IMMEDIATE transaction store all new alerts + associations, or rollback all on conflict. Replay keeps frozen text, digest, versions, `first_prepared_at`, prior evidence unchanged. Return four disjoint counters; exact replay must leave the DB entirely unchanged.

A private content-bound receipt may control internal storage calls; any public DTO/JSON, digest/ID or boolean `verified` must be untrusted. If using a receipt, bind **all fields consumed** after actual origin recomputation. This is not a signature against privileged Python execution. The three DBs have no distributed transaction; documented snapshot and source immutability assumptions are required.

## 6. Identity and renderer (version 1)

Only admitted event types: `SET_REFERENCE_FIRST_OBSERVED`, `CANDIDATE_REFERENCE_FIRST_OBSERVED`; all must be exact members of the frozen validated Discovery v3 result. Policy ID `discovery_reference_alert_v1`, renderer version `1`, channel constant `offline_preview`, status constant `pending`.

Canonical JSON recipe: `json.dumps(value,ensure_ascii=True,sort_keys=True,separators=(',', ':'),allow_nan=False)` with finite scalars and lowercase SHA-256. Exact alert ID = `"alt1:" + sha256(canonical_ascii({"identity_version":1,"destination_key":alias,"event_id":evt3})).hexdigest()`. Validate token grammar (69 chars), all ordered identities, and collisions. DO NOT include cmp3, timestamps of preparation, message, renderer, history, database path or run ID in alt1 preimage. Add independent hand-calculated test vectors (QA must not import production identity helper). Same event+destination one alert; same event+different destination different alert; same event+two windows two evidence rows. Same identity with differing **intrinsic** intent/message or versions is explicit `conflict`, not overwrite. Future renderer migration is NOT automatically re-notification.

Renderer: deterministic, zero network/IO; UTF-8 byte length <=4096, not Python codepoints. Include evident window-relative phrasing (`first observed in selected comparison window`); clear accepted set versus unaccepted candidate; explicit synthetic label when `profile=synthetic_multi_revision_v1`; do not claim global novelty, sale, launch, stock, preorder, price or value. Plain text only, no HTML/Markdown parsing assumptions. Escape control characters, CR/LF, bidi controls and nonprintables deterministically (e.g. JSON-style `\\uXXXX`, not terminal execution); preserve original values in frozen association. Fail `input_limit` if safe rendering exceeds byte cap; never truncate to misrepresent source data. No names/links manufactured from absent evidence.

## 7. Independent SQLite v1 / storage contract

Proposed new owner `card-market-tracker.alert-outbox`, `application_id=0x434D5441` (ASCII CMTA; confirm unused), `PRAGMA user_version=1`, `journal_mode=DELETE`, `synchronous=FULL`, FK ON, SQLite STRICT. Use `schema.expected_inventory()` exact DDL and indexes with no auto-migration. Suggested 3 tables:

- `outbox_metadata(singleton PRIMARY KEY CHECK 1,owner,schema_version)` exactly one row.
- `alerts(alert_id PRIMARY KEY, destination_key, event_id, channel, policy_version, renderer_version, intent_json, message_text, intent_sha256, message_sha256, first_prepared_at, state CHECK='pending', UNIQUE(destination_key,event_id))`. Validate digest/version/message bytes on all reads before materializing; row may store optional explicitly bounded profile/type for summary indexing but never duplicate untrusted truth.
- `alert_evidence(alert_id FK alerts RESTRICT,comparison_id,event_json,journal_content_sha256,event_sha256, PRIMARY KEY(alert_id,comparison_id))`, optional index on comparison_id. Retain full original canonical event (`evidence.history` included) and journal digest. No delivery/scheduler tables.

Use exact CHECK/lexical/type guards plus stricter Python validators. All TEXT returned from potentially modified SQLite must have SQL `typeof` + byte-length guards before loading; inventory reads bounded at expected count+1; strict finite duplicate-aware JSON decode and canonical comparison; verify `alert_evidence.event_id/intent` correspond semantically to parent. Entire prepared operation canonical content <=16MiB, no splitting or partial success. Outbox read-only operations must open `mode=ro/query_only`. Original captures and journal are NEVER migrated or modified.

Path safety: reuse vetted persistence `_checked_path`, `_check_sidecars`, exclusive `_reserve`, `_unsafe_stat`, no symlinks/UNC/device names/hardlinks/cross-DB aliases, trusted ancestors, existing new-destination rejection, distinguish missing DB from zero rows. New-file failure cleanup only exclusively owned inode; never manually delete sidecars. Own `Budget` or reuse P4c budget with shared remaining; SQLite progress handler/busy timeout, cleanup after interruption. Document hostile administrator race outside scope (TD-003).

Queries: default page 100, limit 1..1000 nonbool, max canonical output 1MiB; strictly ascending lowercase alt1 or cmp3 keyset, `next_cursor` last returned if more; no whole-table fetchall; pagination pages are individual snapshots, not a multi-page global snapshot. Evidence-get is one explicit full association bounded by journal-compatible limits. Default operation 2s, explicitly <=5s; shared origin-check + prepare + commit budget cannot reset; cooperative deadline cannot bound blocked kernel IO. Local verify whole DB or FAIL timeout, no partial PASS. Backup and restore independently reserve a new target, SQLite backup to consistent snapshot, validate/reopen schema/semantic content and clocks. Capture/journal/outbox backups remain separate.

Error codes: exit 2 for strict input, grammar, unsupported evidence/profile, limit or conflict; exit 1 for input IO, paths/unsafe destination, storage missing/locked/corrupt/schema/timeout/IO, recompute mismatch and execution. Fixed output category; no raw exception strings. Structured logging includes only operation, run ID, duration, fixed category/result and bounded counts; never routes, SQL, payload, alias, reference or rendered message. Preview and explicit stdout require filesystem/terminal protection.

## 8. Testing and QA — fail-first mandatory matrix

Unit/contract: independent alt1 canonical preimage, distinct destination identity, same evt3 in two cmp3 windows; case of an accepted set and candidate; synthetic labelling; baseline/no_discoveries zero rows; renderer Unicode/CR-LF/bidi/control/plain-text/4096 UTF-8 bytes; intrinsics omit comparison-specific history; wrong full event/schema/policy versions; shared-intent collision => atomic conflict; exact replay no byte changes.

Admission: forged result DTO/JSON, ID, digest, `verified` flag, copied/mutated private receipt, source DB absent/change, journal coherent rewrite versus original captures, mismatch on full semantic result, profile errors; assert absolutely zero writes. Snapshot mutation after read/validation and strict no TOCTOU within consumed verified object. All real R0→R1 four profile comparisons must create ZERO alerts. Positive examples synthetic only.

Storage/security: exact schema/application owner/DDL/indexes, FK/orphans, duplicate evidence, malformed/oversized SQLite TEXT before materialization, noncanonical JSON, bool/int, invalid ID/version/digest, alias across all three SQLite files, sidecars/links, permissions and trusted dirs, busy writers/deadline/interrupt, clean rollback after first alert insertion, two real concurrent writers, process kill during transaction/reopen, backup restore then replay/evidence compare, operation without init, no transport attempts and preview read-only. Distinguish process crash recovery from physical power loss.

Paging: empty vs missing; 100/1000 summaries, 1MiB ceiling, keyset before/after concurrent insert, explicit full evidence retrieval, cap SQL row sizes before fetch. Verify and origin recompute are read-only; local verify can pass after coherent rewrite but origin recompute MUST fail. Deadline expiry yields FAIL, never partial PASS.

Add eighth `scripts/alert_outbox_smoke.py`: separate processes for captures/journal/outbox init, explicit P4c record, enqueue+preview, replay, 2-window 1-event association check, evidence-list/get, local verify, origin recompute, backups and restores; no runtime data network. Preserve all seven existing harnesses.

Run locked/frozen install, `ruff format --check`, `ruff check`, strict `mypy`, full `pytest` with no regression/skips added, coverage >=85% lines AND >=80% branches (including newly added runtime), sdist/wheel and wheel-installed tests outside checkout, dependency audit, secret scan; eight harnesses on outside-checkout wheel, Compose and linux/amd64 and linux/arm64/QEMU; four complete CI jobs required. Runtime nonroot UID 10001, private data, fixtures read-only, network disabled. QEMU not physical Raspberry Pi qualification. QA creates independent oracle/probes; final REVIEWER inspects exact immutable SHA/tree plus all four complete CI logs. Any post-review code change invalidates relevant signoffs.

## 9. Documentation deliverables and PR

- Archive **the complete authoritative Orchestrator contract** unchanged at `docs/phases/P8A_OFFLINE_ALERT_OUTBOX_CONTRACT.md`.
- `docs/phases/P8A_CODEX_ENGINEERING_BRIEF.md` (this brief); `docs/phases/P8A_OWNERSHIP.md` with actual agents/model accepted, worktrees and time.
- ADR-0010: context, decision, alternatives, consequences, status, revisit: alt1, frozen intrinsic/outbox, per-window evidence, separate SQLite, offline-only.
- `docs/data-contracts/ALERT_OUTBOX_V1.md` + `ALERT_OUTBOX_STORAGE_V1.md` exact keys/CLI/status/identities/SQL/errors/pagination/byte and timeout bounds.
- `docs/ARCHITECTURE.md`, `ROADMAP.md` prepend P4c closed/P8a open explicitly attributed to Orchestrator **chat**, no fabricated public close comment; threat model, runbook recovery, testing strategy, quality gates, technical debt implications. Existing TD-001–TD-005 remain OPEN.
- `scripts/alert_outbox_smoke.py` and CI wiring to all four environments, without disabling prior jobs or enlarging authorized source corpus.
- PR remains **OPEN, NOT MERGED**. Phase report binds base/head/tree, coverage, commands, test counts, actual CI run/4 complete log bodies, independent QA and REVIEWER attestations, published readback, precise AC-A01…A16 matrix, constraints and issues. No `ACCEPTED`, `PHASE CLOSED`, or opening P8b.

## 10. Execution checkpoints / acceptance traceability

| Checkpoint | AC | Gate |
| --- | --- | --- |
| preflight+contract+ownership | A01 | exact base/tree and no unexpected changes |
| origin-admission+same content | A02–A03 | forged/changed-source negative tests, zero outbox writes |
| policy/destination/event+associations | A04–A06 | QA independent alt1 vector, 2 windows and replays/conflicts |
| versioned safe renderer | A07 | UTF-8/control text and truth-claims tests |
| owner, schema, atomic writes | A08–A09 | integrity, concurrent processes, rollback/kill/reopen |
| bounded query and preview | A10 | nonmutation, keyset/paging and output limits |
| local and origin verification | A11 | coherent mutation / independent recompute probes |
| paths/recovery | A12 | aliases, backup/restore and replay |
| source policy | A13 | four real no-events, synthetic-only positives, zero network |
| observability, 8 harnesses | A14 | bounded logs/error cases, all environments |
| ADR and records | A15 | traceable doc audit, TD-001…005 open |
| exact frozen review and CI | A16 | four full CI PASS logs + QA and REVIEWER independent |

A criterion without evidence is FAIL/BLOCKED. Keep implementation work moving autonomously inside the authorized scope and raise only material cross-phase decisions to Orchestrator. **No merge.** Completion output, only when everything is independently demonstrated: `READY_FOR_ORCHESTRATOR_REVIEW`.

## 11. Current access handoff (do not mistake for product status)

On 2026-10-20 this ChatGPT session verified through the connected GitHub read API that remote `main` exactly equals the authorized commit and tree, with the expected ordered parents; `feat/p8a-offline-alert-outbox` was not found. GitHub `create_branch` returned HTTP 403 `Resource not accessible by integration`. The current environment has no checked-out repo or Codex agent-spawn capability and network DNS to GitHub is not available to local shell. **No branch, PR, implementation, test execution, independent QA or CI run has been completed by this session.** Codex, from the developer environment with `gh` permissions, must redo the preflight, create the branch and archive these handoff files; no 403 workaround may write `main` or impersonate QA. This is an operational access blocker for this session, not evidence that P8a product acceptance failed.
