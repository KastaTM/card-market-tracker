# MODEL PROFILE — P8d / Codex Engineering Lead

**ChatGPT Phase Lead:** GPT-6 / High recomendado si está disponible; el modelo visible es GPT-6 y el esfuerzo real de este chat no es introspectable. El contrato original permite preferir GPT-6.1 Sol / High *solo si figura realmente en el selector*. Esta preparación no acredita la selección de ese modelo.

**Codex Engineering Lead:** solicitar GPT-6.1 Sol / Medium **solo si aparece realmente en su selector**; si no, elegir el modelo más capaz que realmente admita Codex para esta tarea y registrar nombre y esfuerzo observables. **High** para admisión desde originales, identidades, SQL/invariantes, consentimientos, concurrencia, efectos remotos ambiguos y revisiones independientes. Especialistas ARQ, DB-OWNER, SEC/SRE, QA y REVIEWER: High si existe. Escalar a GPT-6 Astra / High únicamente si está disponible y existe un bloqueo real justificado. No convertir perfiles solicitados en modelos efectivamente ejecutados sin prueba. **Cada especialista y el Engineering Lead deben registrar MODEL PROFILE USED.**

# P8d — Engineering Brief / Phase Lead → Codex Engineering Lead

**Phase:** P8d — Manual Watchlist Telegram Delivery  
**Contract authority:** `P8D_MANUAL_WATCHLIST_TELEGRAM_DELIVERY_CONTRACT.md` adjunto en este handoff; texto del Orchestrator 2026-10-28. Si hubiera discrepancia, prevalece ese contrato y las decisiones posteriores expresas del Orchestrator.  
**Status:** OPEN / IMPLEMENTATION AUTHORIZED (offline only); **LIVE EXECUTION NOT AUTHORIZED**.  
**Repository:** `KastaTM/card-market-tracker`.  
**Authorized baseline `main`:** `9dda9fba0aa9646a67596657d4ae9a7088903808`  
**Tree:** `dfd0414242cff364aad6082411ae88aef728783e`  
**Merge parents, ordered:** `228d5c8d0d91edf03ddb86a489c8232eeb7c08bc`, `d82aba73d9bc0eb455f8664e3ccddc0134ea9d9c`.  
**Suggested branch:** `feat/p8d-watchlist-telegram-delivery`.

## 0. Verified remote facts versus local unknowns

On 2026-10-28 the Phase Lead independently read GitHub through the connected GitHub integration. `main` matched the exact authorized SHA/tree/parents; PR #18 was closed and merged at that SHA. The search for `p8d` branches returned none at that moment. Existing package paths include `watchlist`, `watchlist_journal`, `watchlist_alerts` and `telegram_delivery`; there is no P8d module yet on this baseline. No remote writes, branch creation, Codex runs, worktree audits, code execution, CI, QA, delivery or transport calls were carried out by the Phase Lead. Current execution container cannot resolve github.com for `git ls-remote`; the GitHub connector can read remote resources but **cannot inspect the user's checkout/worktrees**. The observed repository is public and the connector indicates push permission, but that is not evidence of local checkout access or authorized merge.

**Codex must first run a clean local preflight** in its actual checkout:

```sh
git remote -v
git status --porcelain=v1
git branch -avv
git worktree list --porcelain
git rev-parse HEAD
git rev-parse HEAD^{tree}
git show --format='%P' -s HEAD
git ls-remote origin refs/heads/main
git fetch origin main
git show --format='%H %T %P' --no-patch origin/main
```

Do not overwrite, clean, reset, rebase or discard unknown local work. If `origin/main` is different from the authorized baseline, or existing branch/worktrees/dirty state overlap P8d, **stop and report**; do not silently adapt the baseline. Only after matching remote baseline and safe checkout, create the branch from `origin/main`. Coordinate Git/worktree ownership centrally.

## 1. Mission / exclusion boundary

Implement exactly one manually chosen historical **synthetic** P8c Watchlist `walt1_` preview delivered *unchanged* to one explicitly registered, operator-attested, validated **private** Telegram route. A genuine P8c pending offline preview is not actual present-day consent. The operator must independently acknowledge this is a historical demonstration and bind that acknowledgement to alert, genuine signal, revision, full evidence/message digests and route digest. The string `SYNTHETIC — DEMONSTRATION ONLY` and historical-review framing must remain unchanged. No price/stock freshness, market value, commercial authenticity or human read status may be inferred.

Scope: private route registration/validation, original-backed admission, own SQLite STRICT ledger/identity, exact message binding, explicit per-send preflight, durable claim/fencing, one-attempt-per-invocation transport, durable receipt, conservative uncertainty handling, confirmed replay, verification/recompute/recovery/quarantined backup restore, safe bounded CLI and logs, thirteenth installed-process offline smoke, docs and independent gates. Out of scope: scheduler, polling, background sends, bulk/drain, arbitrary text, contacts/groups/channels, P8b or P8c writer/identity/schema/renderer changes, observed market values, new sources or products, automatic retention, web UI, migrated stores, global P5 closure or permission for subsequent phases. **Do not perform live Telegram calls now.** No token request or token paste to chat.

## 2. Read-first source inventory, with actual paths

Read `context.md`, `AGENTS.md`, `docs/ROADMAP.md`, `docs/ENGINEERING_OPERATING_MODEL.md`, `docs/ARCHITECTURE.md`, `docs/QUALITY_GATES.md`, `docs/CODING_STANDARDS.md`, `docs/TESTING_STRATEGY.md`, `docs/TECHNICAL_DEBT.md`, `docs/threat-model/THREAT_MODEL.md`, `docs/data-contracts/LOGGING_V1.md`, adopted ADR-0011 to ADR-0014, all relevant P5a/P5b/P8a/P8b/P8c contracts, runbooks and existing tests. Historical PR #18: `https://github.com/KastaTM/card-market-tracker/pull/18`; historical CI `https://github.com/KastaTM/card-market-tracker/actions/runs/40737659939`. These are **P8c historical evidence, not P8d PASS**. RW-01 corrective evidence must be preserved; do not reintroduce per-alias partitioning of the watch/revision invariant.

Actual code entry points observed on the authorized baseline:

- `src/card_market_tracker/watchlist_alerts/application.py`: `_manifest`, `_paths`, `_origin_entry`, `_admit`, `recompute`, `enqueue`. `_admit` reopens the original P5b verified signal bundle, both P5a snapshots and manifest/exact revision; `recompute` checks stored alert/evidence against independent originals. Preserve their semantics and avoid calling `enqueue` as a hidden write.
- `src/card_market_tracker/watchlist_alerts/storage.py`: `_get_pair` reads one consistent alert/evidence pair and checks the local store; `get`, `evidence_get`, `verify`, `backup`, `restore`. Reuse read-only behavior where safe. If necessary, add **one minimal P8c-owned read-only accessor** to expose the pair atomically while preserving all deep verification; no general refactor.
- `src/card_market_tracker/watchlist_alerts/policy.py`: `canonical`, `digest`, `validate_id`, `validate_evidence`, `validate_prepared`, renderer-derived `prepare`. It is not delivery consent. No changes to P8c policy/renderer.
- `src/card_market_tracker/telegram_delivery/transport.py`: `TelegramTransport`, `TransportResult`, `Receipt`, `check_configuration`, `_supervise`; already supervises HTTPS/DNS/connect/read via spawned worker. The narrow P8d port should reuse these types/transport **without changing** this module. `TelegramTransport.validate_destination`, `.validate_bot`, `.send` are the relevant operations.
- `src/card_market_tracker/telegram_delivery/application.py`: P8b `Transport` protocol, `_Budget`, `send`, `destination_validate`; study safety semantics, but **do not call P8b application `prepare` or `send`** (they admit `alt1:` / `evt3:` sources, not P8c `walt1_` / `wsig1_`).
- `src/card_market_tracker/telegram_delivery/storage.py`: `_claim_verified`, `_finish`, `recover`, `restore`; study conservative CAS/fencing/outcome/cleanup behavior, but do not reuse or mutate its ledger/schema.
- `src/card_market_tracker/watchlist_journal/storage.py`: `_verified_signal_bundle`, P5b full-fold and source verification; read-only only.
- `src/card_market_tracker/cli.py`: root has a special lazy parser for `watchlist-alert-outbox` to prevent Telegram imports and token access. Add P8d CLI lazily without regressing P8c's import guards or pulling Telegram into offline commands.
- `scripts/wheel_smoke.sh`, `scripts/container_smoke.sh`, `.github/workflows/ci.yml`: baseline has **12 smoke harnesses** and four CI jobs: `quality`, `compose`, `container (amd64)`, `container (arm64/QEMU)`.

## 3. Ownership / multi-agent plan (before parallelism)

Engineering Lead is **sole integrator** and owner of baseline/branch, shared CLI registration, logging, shared CI/smoke scripts, common docs, lockfiles, PR/publication, evidence and conflict resolution. Do not spawn every agent by default. Assign these disjoint edit targets with a written ownership file:

| Role | Exclusive authorship | Required evidence |
|---|---|---|
| ARQ/BE | New `watchlist_delivery/application.py`, `models.py`, `policy.py`, `errors.py` plus author tests for original admission/consent (ownership may be further split in separate worktrees). | Exact source/projection/receipt binding, oracle; no P8b writer calls. |
| DB-OWNER | New `watchlist_delivery/schema.py`, `storage.py` plus storage/concurrency/recovery author tests. | Exact DDL, transaction invariants, CAS, restore quarantine; independent RW-01 regression. |
| SEC/SRE | Read-only threat, privacy, outcome, deadline, token and recovery audit. Edit only an agreed isolated report/probe if authorized. | Failure matrix, no credential usage, transport safety and operational runbook suggestions. |
| QA | Separate nonauthor worktree/probe script(s), no product files. | Independent falsification tests/oracles on final SHA/tree. |
| REVIEWER | Different nonauthor from QA, read-only final review with distinct probes. | Final audit and reproducible probes/readback on exact final SHA/tree. |
| Engineering Lead | CLI, thirteenth smoke, shared docs/CI, commits/PR and integration tests. | Four CI logs, source-byte nonmutation, gate matrix and public sanitized evidence. |

Only parallelize read-only reviews and wholly disjoint author targets. Ensure `Author != QA != Final Reviewer`; code authored by the Lead is not QA independence. Shared storage/schema changes are DB-owned. One active writer per file, DB/lock state and Git integration. Do not claim a specialist ran unless its actual execution can be shown.

## 4. Mandatory documentation freeze before product writer

1. Archive the **complete unedited Orchestrator contract** in `docs/phases/P8D_MANUAL_WATCHLIST_TELEGRAM_DELIVERY_CONTRACT.md`. This handoff includes a separate copy. Do not silently shorten or correct its historical statements.
2. Add a dated top entry in `docs/ROADMAP.md`, and concise `AGENTS.md` map: P8c ACCEPTED/PHASE CLOSED by Orchestrator chat decision after PR #18; P8d OPEN with *only offline implementation authorized*. Preserve historical P8c RW-01 and previous dated status entries; do not invent a remote closure comment.
3. Freeze `docs/adr/0015-manual-watchlist-telegram-delivery.md` with Context, Decision, Alternatives, Consequences, Status, Revisit conditions, identity, separate authority, transport reuse and lack of distributed commit. Candidate **application_id 0x434D545A (`CMTZ`)** for the new owner `card-market-tracker.watchlist-telegram-delivery` / schema v1: prior documented allocations were CMT1/CMTA/CMTD/CMTJ/CMTQ/CMTW/CMTY; Codex **must re-audit all owners and SQL** before adoption. No existing DB migration.
4. Freeze **exact** `docs/data-contracts/WATCHLIST_TELEGRAM_DELIVERY_V1.md` (complete DTO schemas, identity, message/evidence/route/consent digests, consent command, UTC grammar, retry/clock-skew, CLI commands/flags/responses/errors/exits, time budget accounting, privacy) and `WATCHLIST_TELEGRAM_DELIVERY_STORAGE_V1.md` (literal STRICT DDL statements and inventory/triggers, indices, SQL cell guards, state transitions, quarantine, backup/restore, invariants and CAS).
5. Write executable failure-first runbook: offline setup, choosing exact `walt1_`, reviewing preview and digest, demonstration acknowledgement, registering private route without publishing IDs, fake tests, preflight, explicit separate live authorization, one-shot send, reopen/replay with token removed/network denied, failure/uncertain and worker-quiesced recovery, backups/restore quarantine, operator privacy.
6. Add cross-references to architecture, threat model, LOGGING_V1, quality/testing, technical-debt register (preserve TD-001–TD-005 OPEN). Separate intended design from evidence actually run. Freeze and review before schema.py or writer code.

## 5. Core protocol — normative checklist

**Admission:** Public `prepare` must require four distinct existing safe paths (P5a Watchlist DB, P5b journal, P8c outbox, P8d ledger), complete explicit MANIFEST_V1, exact selected `walt1_` and private destination alias. No latest, auto-init, bulk, caller-supplied DTO authority or permission inherited from P8c's preview or P8b T17. Revalidate owners/schema, genuine full P5b signal and P5a immutable revision through accepted P8c original route. Obtain selected P8c alert+evidence from one consistent verified read transaction, separately recompute against originals, and compare *exact* UTF-8 bytes, renderer/version, identity and all digests. Require pending/offline_preview/synthetic/watchlist_synthetic_alert_v1/WATCHLIST_RULE_ENTERED_MATCH. No rerender, silent fallback or altered text. Enforce 1..4096 UTF-8 bytes, preferably with same validations as P8c.

**Historical consent:** Define a concrete mandatory explicit confirmation flag/command showing chosen alert/signal, revision, message/evidence hashes and private route hash (no private IDs in normal output), with positive acknowledgement of `SYNTHETIC — DEMONSTRATION ONLY` and historical-not-current nature. The acknowledgement must bind to *content+route*, be stored immutably and rechecked before each unconfirmed send. Explicit preview and digest review precede acknowledge/prepare. Local operator/host trust is assumed; not a cryptographic human signature. Avoid a generic `--yes` whose meaning loses content/route binding.

**Sealed authority:** Bind an application-issued one-use private receipt to content, digest, exact Python instance, issuing budget, operation, source and route, and reject fake dataclasses, copied/modified receipts, a second call, or a fresh deadline. The storage writer must reconstruct SQL-side invariants under BEGIN IMMEDIATE; it cannot blindly trust a Python DTO. Reuse P8c pattern conceptually; no changing P8c authority.

**Identity:** `wtdl1_` followed by 64 lowercase hex digest of `b'CMT_WATCHLIST_TELEGRAM_DELIVERY_V1' + b'\x00' + canonical_ascii({'identity_version':1,'provider':'telegram','signal_id': genuine_wsig1})`. Canonical = JSON sorted keys/ASCII escapes/compact/no-NaN/strict types. UNIQUE(provider,signal_id). Alert aliases are NOT distinct sends: first accepted alert/alias/route/consent/evidence/text binds the signal forever in this ledger; identical replay preserves original; different alias/route/message/config conflicts. Different genuine episode/signal is a new delivery. Do not promise global exactly once across cloned ledgers.

**Independent identity oracle (format-level synthetic examples only; no source authenticity):**

```
canonical_A = {"identity_version":1,"provider":"telegram","signal_id":"wsig1_0000000000000000000000000000000000000000000000000000000000000000"}
preimage_A = ASCII("CMT_WATCHLIST_TELEGRAM_DELIVERY_V1") || byte(0x00) || ASCII(canonical_A)
sha256_A = b08e2920077a2f36ba634b32c0f1215e952063c55cfc99320ab55fbbdf9d36f5
id_A = wtdl1_b08e2920077a2f36ba634b32c0f1215e952063c55cfc99320ab55fbbdf9d36f5
canonical_B = {"identity_version":1,"provider":"telegram","signal_id":"wsig1_ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"}
sha256_B = 810e8528fcea94a8ee848b56cb50ae04ff35bbaef05de8f667bddda896cac9d8
```

These are derived by a separate stdlib script, not P8d production imports, and still need an independent QA oracle plus a byte-literal preimage in committed tests.

**Global invariants / RW-01:** Full immutable P5a watch entry/configuration for identical watch_id/revision across all retained P8d deliveries must be consistent even across different signal IDs, aliases, routes, products/series. The **prepare/claim transactions** must check the same global invariants as `verify` before commit. Genuine independent P5a/P5b/P8c origin bundles that disagree on full entry for same watch/revision must conflict on *second prepare* without storing a corrupt ledger. Semantically equivalent copies must pass. No alias-partitioned check or relying only on verify-after-the-fact.

**State machine:** ready → in_flight → (confirmed | retryable | permanent_failure | uncertain). A genuine explicit 429 with strictly valid 1..86400 `retry_after` may produce `retryable` and bounded UTC `not_before`; manual later invocation only, 3 lifetime claims maximum; third 429 exhausts attempts. 408/409/425, 5xx, lost response, timeout, TLS/transport unknown, malformed success, and post-possible-send local storage failure produce `uncertain` or blocked `in_flight`. Invalid/no-receipt 200 is never auto-retryable. Other valid permanent 4xx may produce `permanent_failure` according to frozen mapping. No implicit restart recovery, force or uncertain requeue.

**Claim/send fencing:** Revalidate ledger/route/consent/bot/originals and budget *before* claim. Under `BEGIN IMMEDIATE` recheck state/binding/full invariants/cooldown/counter, create unique unpredictable attempt owner/id and contiguous ordinal, commit in_flight **before** HTTP. No DB transaction over HTTP; exactly one `sendMessage` at most per invocation. Terminal/uncertain blocked; two competing processes cannot claim same delivery. Complete result using owner+attempt+current-state CAS; stale finish/recovery may not overwrite newer receipts or terminal state. Recovery only explicit `worker_quiesced=true`, in_flight → uncertain; no resend. Confirmed replay validates local ledger/binding/receipt without token/network/original paths; **global quarantine blocks send even on confirmed replay**.

**Transport:** import/reuse only `telegram_delivery.transport.TelegramTransport` and its types through a narrow P8d port; no changes to P8b HTTP or ledger. Fixed official HTTPS, TLS checked, no redirect/proxy/retries, accepted getMe/getChat/sendMessage only. Exact text, link previews off, no parse_mode/topic/entities. Token only `CMT_TELEGRAM_BOT_TOKEN` in local environment; no token args, DB, file, fixture, IPC to parent, log, response or chat. Never publish private bot/chat identifiers or raw receipts. Bounded strict response parser ≤64KiB, no duplicate keys/NaN/bool-as-int; require expected bot/private chat, message_id, provider timestamp and exact mirrored message. Provider success is not human read confirmation.

**Budgets:** local commands default 2s/max5s whole invocation (including parse/output); destination validation/send default 15s/max30s **one global budget**, including local origin read, bot validation, remote supervised HTTP, receipt persistence and formatting; original checks during send have a **single combined max5s** and must not allocate 5s per helper. Reserve time for SQLite finalization and treat a local response error after possible HTTP as ambiguous. Freeze UTC microsecond-Z timestamp grammar, skew refusal and monotonic deadline behavior. SQLite/filesystem/stdout deadlines are cooperative, not hard real-time if kernel syscall blocks.

**Storage/recovery:** separate STRICT own ledger with metadata/global `send_quarantined`, destinations, deliveries, claims, immutable attempt results/receipts, constraints/FK/triggers/exact inventory/indexes; SQL-side typeof/byte-length guard before materializing untrusted large values. Verify owner/application_id/user_version/integrity/FK, strict canonical JSON, complete immutable bindings/IDs/global watch-revision identity, attempt ordinal/state/owner/CAS/receipts/not_before, global quarantine. Local verify is not source authenticity; origin-backed read-only recompute must fail for absent/mutated originals. Backup consistently, restore to **new exclusive path** with **durable global quarantine before exposure**, affecting even delivery records created after the backup. Reopen and verify, protect inode/links/reparse/sidecars/foreign hot journals; fsync and safe link/unlink compensation; never remove foreign evidence. Restore does NOT provide a command to clear quarantine.

**CLI/observability:** `cmt watchlist-telegram-delivery` lazy registration with init, destination-add/validate, prepare, send, get/list, verify/recompute, recover, backup/restore. Exact closed error/exit/JSON schema. No `send-all`, `force`, `resend-uncertain`, `unquarantine`, arbitrary text, unknown paths or auto-init. Explicit IDs and source paths; keyset default 100/max1000/≤1MiB, filters bound to versioned cursor; input bound 1MiB/depth16/20k nodes. One completion structured log per invocation, redacted to fixed safe operation/result/category/status/duration/local validated IDs/counters. No message/evidence/route/PII/secret/SQL/raw exception log. Offline commands must have no token reads, Telegram imports or sockets. Printed ordinary CLI JSON must also be privacy-safe.

## 6. Ordered implementation and review gates

**Gate A — baseline:** local preflight, branch from authorized SHA, record ownership and no overwrites. Archive contract; update AGENTS/ROADMAP. **No code** until A PASS.

**Gate B — design freeze:** ADR-0015, API and storage v1, selected `CMTZ` collision audit, SQL inventory/identity vectors, command/consent semantics, time/error/state/outcome table, runbook. ARQ/DB/SEC review; Phase Lead accepts **design only**. **No writer** until B PASS. No need to ask routine choices; escalate genuine scope contradictions.

**Gate C — implementation:** new P8d module; source-backed admission and consent; DB ledger; narrow P8b transport; lazy CLI; no real requests. Start with tests and fault injection. Preserve P8b/P8c contracts unmodified except minimal P8c read-only accessor if justified.

**Gate D — author regressions / offline harness:** test positive original P5a→P5b→P8c→P8d and all failure-first paths below. Run full checks locally; no filters, gates suppressed or timeouts raised to make green. Add `scripts/watchlist_telegram_delivery_smoke.py` as the **13th** harness in wheel, Compose, AMD64 and ARM64/QEMU. It must build five checkpoints/four genuine synthetic signals, choose one, prepare, fake-send, receipt, persistent confirmed replay in another process with no token/sockets, independent recompute/recovery/quarantine, and source byte nonmutation. Earlier twelve harnesses continue unchanged.

**Gate E — QA and final reviewer:** distinct nonauthor QA then independent final REVIEWER on **exact final HEAD/tree**, with own runnable probes, independent oracle and publicly available sanitized code/helpers/results. Corrective commits invalidate affected prior attestations. Static review is not a live test.

**Gate F — CI/publishing:** Draft PR only; four jobs final candidate PASS (Quality, Compose, AMD64, ARM64/QEMU), 13 harnesses per applicable environment, UID10001/private files/network none, frozen uv, Ruff format/check, strict mypy, complete pytest, ≥85% lines and ≥80% branches, sdist/wheel + external installation, pip-audit and secret scan. Inspect all final job logs, preserve failed attempts and don't rerun a failed job of same SHA just to green it. ARM64 QEMU is not a physical Raspberry Pi or proof of physical power-loss durability. Publish and read back sanitized PR/evidence; don't invent remote publication.

**Gate G — REAL, SEPARATE AUTHORIZATION AC-WT20:** do **NOT** execute this gate before offline code, QA and candidate PR. Prepare sanitized preflight specifying exact candidate HEAD/tree, signal/alert/delivery, message/evidence/route digest and one private route; request explicit consent from operator for precisely one historical synthetic message with distinct route. No token or bot/chat IDs in chat/PR. Global qualification budget ≤8 `getMe`/`getChat` calls and ≤1 **real** `sendMessage` attempt, even if failed/uncertain; measured and never reset by process restart. No automatic retry or second real send from product's 429 feature. Demand durable accepted receipt, one claim, reopen confirmed and separate-process replay without token/sockets, 0 extra calls; original sources intact and ledger not restored/quarantined. QA/REVIEWER inspect sanitized evidence read-only, no new network. If authorization withheld: `BLOCKED — LIVE_UNVERIFIED`; no claim that fake/CI/P8b T17 substitutes for real gate. If live succeeds and code later changes, renew affected reviews/gates; no repeat send without new specific authority.

## 7. Mandatory failure-first test matrix

- Admission: genuine P5a/P5b/P8c from complete MANIFEST_V1; fake DTO/receipt, copy/second use, mutation, late Budget reuse, invalid/missing originals, poisoned owners, extra sources, wrong mode/kind/policy/renderer/state, preview/alias mistaken for consent, route re-attested after change, global read consistency, no source mutations.
- Identity: independent literal NUL/preimage oracle; same wsig1 across aliases/routes; same signal/different evidence/config; two valid signal episodes; race of writers with incompatible full watch/revision settings and RW-01 genuine independent sources; verify and backup remain healthy after rejected second prepare.
- Concurrency: two actual sender processes, persistent in_flight before fake HTTP, one send, stochastic attempt ownership and ordinal; kill before/after claim, in/during HTTP, between HTTP acceptance and receipt write, after receipt, stale finalizers/CAS, recover quiesced only.
- Telegram fake contract: strict valid bot/chat/text/accepted_at/message_id; 429 valid/invalid retry_after and cooldown/max3, permanent 4xx, 408/409/425, 5xx, timeout, lost bytes, truncated/duplicate JSON, malformed success, wrong sender/chat/text; TLS/response drip/DNS, refusal and injected persistence errors; no misclassification of uncertainty as retryable.
- Storage/ops: SQL rehashed tampering, overlength storage values, altered owner/user_version/application_id/inventory/FK/triggers, hot journal before writable open, ENOSPC, lock, timeouts at each stage, restore old backup/global quarantine with post-backup unknown records, hardlink/reparse/symlink/sidecar/inode/existing destination, safe unlink compensation, no foreign deletion.
- Interface/privacy: structured stdout/errors/exits and only one completion log, sentinel credentials/IDs/evidence/SQL absent, bounded keysets/filters/cursors/paging; offline package/CLI `help`/invalid args import deny of Telegram and socket, token absent; global and local origins deadlines without refresh; 13th offline smoke plus all twelve regressions.

## 8. Required evidence and handoff

Submit a **Phase Completion Report** for P8d with: proposed status; branch/PR/base/HEAD/tree/commits; MODEL PROFILE USED (requested/observable/unverifiable); role ownership; implementation/diff; ADR/contracts/DB/threat/debt/logging/runbooks; each AC-WT01 through AC-WT21 **PASS/FAIL/BLOCKED** with its own reproducible evidence; all tests/coverage; four final CI jobs and full logs, thirteen harnesses, QA and separate REVIEWER SHA/tree; remote publication/readback; offline versus actual Telegram distinction; precise live-gate data or `BLOCKED — LIVE_UNVERIFIED`; limitations/issues and Orchestrator recommendation. No merge, acceptance or `PHASE CLOSED` by Engineering Lead/Phase Lead. Only after **every** gate including AC-WT20 is satisfied may Phase Lead declare `READY_FOR_ORCHESTRATOR_REVIEW` for the Orchestrator.

**Immediate first response required from Codex:** (1) local Git/branch/worktree/baseline audit with exact observed evidence, (2) read-first dependency summary, (3) disjoint ownership plan and agents/models actually selectable, (4) draft ADR/storage/API freeze choices including CMTZ collision audit and specific historical acknowledgement, (5) execution plan and first independent negative tests. Do not substitute an assertion of completion for executable evidence.
