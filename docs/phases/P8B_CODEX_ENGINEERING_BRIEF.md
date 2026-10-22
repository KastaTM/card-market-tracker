# P8b — Codex Engineering Brief: Telegram Alert Delivery

**Project:** `KastaTM/card-market-tracker`  
**Authority:** 00 — ORCHESTRATOR; P8b Phase Lead directs the Engineering Lead.  
**Date:** 2026-10-21; **Status:** IMPLEMENTATION NOT STARTED / GITHUB WRITE BLOCKED.  
**Normative contract:** `P8B_TELEGRAM_ALERT_DELIVERY_CONTRACT.md` (verbatim user-supplied Orchestrator text).  
**Branch to create when authorized access works:** `feat/p8b-telegram-alert-delivery`. **Do not merge.**

## MODEL PROFILE

- **ChatGPT Phase Lead recommended:** GPT-6 / High (or the actual stronger phase-chat choice available). The contract requested GPT-6.1 Sol / High if available; availability of that selector in this environment was not established. The current phase lead is GPT-6; its effective reasoning level is not independently observable.
- **Codex Engineering Lead recommended:** contract requests GPT-6.1 Sol / Medium **only if actually available in Codex**; otherwise select the strongest currently available Codex model with Medium reasoning appropriate for coordination and incremental coding, and report the exact visible selector. Never claim access to GPT-6.1 Sol if not shown.
- **Codex escalation:** High for SQLite state machine, crash windows, fencing, restore quarantine, network failure classification and deadline enforcement; independent QA/REVIEWER High. If a critical dispute remains and the user actually has GPT-6 Astra/High, request escalation rather than inventing availability.
- **MODEL PROFILE USED** in every report must separate requested, visible/selected and unknown. **No Codex run or specialist invocation has occurred in this chat.**

## 1. Preflight — verified facts

At inspection, GitHub `main` SHA was `ac35d4df0f3a006ff60bb026de992c366e19cc09`, with tree `d604d3b8362c30af8b5dd516eddc0d8095fe7bf9`; this exactly matches the authorized P8a merge and tree. The GitHub connector displayed `push=true` but the actual `create_branch` request returned HTTP 403 `Resource not accessible by integration`. No branch, commit or PR was created from this chat. The local filesystem did not contain a checkout; direct `git ls-remote` failed DNS resolution. **Repeat preflight** in the Codex environment: remote URL, clean checkout/worktrees, `main` and tree, existing refs, and permission to push. If `main` has advanced, stop and escalate baseline divergence, not a silent rebase. Do not overwrite unrelated work.

Existing boundaries discovered by source inspection:

- `src/card_market_tracker/alerts/application.py`: `recompute(captures_db,journal_db,outbox_db,alert_id,comparison_id,timeout)` does original R0/R1 capture recomputation; its return proves one explicit association. Reuse it before prepare AND each send attempt.
- `src/card_market_tracker/alerts/storage.py`: `get`, `evidence_get`, `verify`, protected paths and SQLite operations; never mutate the outbox. Outbox schema owner CMTA, version 1, three tables, `offline_preview` and `pending` fixed.
- `src/card_market_tracker/alerts/cli.py`: strict nested CLI with redacted categories, logging and output. `src/card_market_tracker/cli.py` registers `alert-outbox`; add a sibling group, not arbitrary-text transmission.
- `docs/adr/0010-offline-alert-outbox.md` was the last ADR; propose ADR-0011. Existing CI `.github/workflows/ci.yml` has Quality, Compose, AMD64 and ARM64 QEMU jobs and eight offline smoke harnesses.
- Requirements: Python >=3.13,<3.14, no runtime dependencies (`pyproject.toml`), strict mypy, Ruff, pytest, frozen uv lock. Prefer stdlib, but make a falsifiable argument for network deadline guarantees before rejecting a necessary dependency.

## 2. Work order and ownership

1. **Engineering Lead (integration owner)**: inspect full repo, write fine-grained implementation plan and ownership matrix; repeat Codex model profile; freeze contract decisions and no-overlap file ownership. Coordinate checkpoints, integrate, run whole suite and prepare draft PR.
2. **ARQ + DB-OWNER (read-only design, then single DB author):** ADR-0011, delivery identity, route uniqueness, SQL schema and state machine, BEGIN IMMEDIATE claim/CAS/fencing, content verification, backup/restore quarantine. One designated DB author owns new `telegram_delivery/{schema,storage}.py`; do not have competing writers.
3. **SEC/SRE (review/advice or isolated network author):** Telegram read operations, production send transport, TLS/no proxy/no redirect/no retry, bounded response/time, token/error redaction, failure modes. Own `telegram_delivery/transport.py` if independent of DB author.
4. **BE (single application/CLI author):** `telegram_delivery/{application,cli,errors}.py`, top-level CLI registration and user workflows, using explicit DB and transport interfaces. Coordinate interface with DB/transport owners before parallel edits.
5. **QA and REVIEWER (two distinct non-authors):** each works from an immutable, final SHA and tree; QA runs its own adversarial scripts/oracles, REVIEWER performs independent security/architecture/behavior diff audit. Both identify SHA and tree and any revalidation after code changes.
6. **DOCS** only if useful and with exclusive ownership of contracts, ADR, runbook, roadmap, security changes. No large agent pool for its own sake.

Parallelize only independent file edits or read-only work. No simultaneous modifications of shared CLI/CI/docs without an integration owner. Author ≠ QA ≠ REVIEWER. No invented reports.

## 3. Frozen architecture decisions to implement

### Separation and immutable authority

Capture DB, journal DB, and P8a outbox remain owner/schema-verified **read-only**. New `telegram_delivery/` is application + transport + independent SQLite ledger. `prepare` and `send` must each call P8a `recompute()` for an explicit `alt1`/`cmp3`, then load and validate the P8a alert and association again against the frozen selection and confirm its bytes/digests before any claim. Any origins/path/evidence/message mismatch means zero network calls. Preserve exactly `message_text`; do not render, truncate, prefix or transform. There is no atomic cross-DB snapshot; validate immutable sources, bind digests and document the assumption.

### Identity and route

- Destination registry: immutable `(alias, provider='telegram', bot_id:positive_int, chat_id:positive_int, chat_type='private', operator_attested_owner=true)`. Alias obeys P8a grammar. `chat_id` and `bot_id` are private local ledger values; not stdout/logs.
- A route/bot/chat change for an existing alias is `conflict`; token rotation for the **same** `bot_id` is allowed. A new bot or chat is not an implicit new destination.
- **One delivery per (`alert_id`, `provider`) globally, not per alias or chat.** This deliberately enforces a stronger cross-route uniqueness rule: another alias/bot/chat cannot create a duplicate delivery. Explicit route fields are frozen on preparation.
- Proposed deterministic delivery ID `tdl1:` + SHA-256 of ASCII canonical JSON `{"identity_version":1,"alert_id":ALT1,"provider":"telegram"}` with `json.dumps(ensure_ascii=True,sort_keys=True,separators=(',', ':'),allow_nan=False)`. Confirm the exact preimage and a separately computed oracle vector before implementation. IDs cannot include clock, comparison, route, message or nonce.
- Freeze `alert_id`, one selected `comparison_id`, the immutable outbox content digests and a digest of the **validated bound route**. A second `prepare` is replay only if every bound input and route matches, otherwise conflict. Reject another P8a `alert_id` with the same underlying event but a different destination alias if it would bypass the intended one-route restriction; define and test a `(event_id,provider)` uniqueness guard where the same event must not be sent twice via alias changes. **Never accidentally make route change a new identity.**
- Outbox P8a may intentionally contain separate alt1 for the same evt3 under different logical destinations. Because this phase only supports one operator-private Telegram route, the ledger must prevent cross-alias duplicates by provider+event_id as well as provider+alert_id. Reserve both unique constraints; conflicting migration is out of scope.

### State machine and fencing

States `ready`, `in_flight`, `retryable`, `confirmed`, `permanent_failure`, `uncertain` (or documented exact synonyms). Record immutable route/alert binding, attempt counter and current attempt ID, timestamps, bounded error classification, `not_before`, sanitised immutable receipt, recovery/quarantine flag. Keep attempt history durable in a separate append-only table; no overwriting or deleting previous attempts. `attempt_id` must be unique and unpredictable or CAS sequence-bound; finish operation requires match on both `delivery_id` and `current_attempt_id` AND state=`in_flight` in a transaction. Distinct processes must not claim simultaneously; `BEGIN IMMEDIATE` and unique delivery/event indexes enforce it.

Allowed transitions:

| From | Action | To | Policy |
| --- | --- | --- | --- |
| absent | prepare after verified recompute | ready | No send/network |
| ready | explicit send CAS claim | in_flight | Persist intent/attempt before any HTTP |
| retryable | explicit later send; `now>=not_before`, count<3 | in_flight | No waiting or loop |
| in_flight | validated 200 + exact recipient/text + durable receipt | confirmed | Local commit must succeed |
| in_flight | validated, unambiguous permanent provider rejection | permanent_failure | No resend |
| in_flight | validated 429 with positive bounded `retry_after` | retryable | Persist `not_before`; one invocation finishes |
| in_flight | timeout, crash, 5xx, malformed/ambiguous success, lost commit, network uncertain | uncertain | NO auto retry |
| in_flight | explicit recovery with worker quiescence + fencing | uncertain | Never reset to ready |
| confirmed | any repeat send | confirmed | Return `replay`, no HTTP |
| uncertain/permanent_failure | send or force | unchanged | Error/no send; no force in P8b |

There is **no exactly-once guarantee**. A remote acceptance with failed local commit can leave uncertain and possible missed future alerts. In-flight does not expire into ready; `recover` is a deliberate manual no-send operation requiring documented quiescence, not a silent lease-steal. An old worker must not finalize a different attempt; finalization must compare the exact attempt owner. Limit to **one sendMessage attempt per CLI invocation**, at most three attempts over the delivery lifetime (valid 429 only). Even if preparation is invoked repeatedly, do not reset attempt count.

### Restored database quarantine

A restored backup may omit confirmed deliveries that happened after the snapshot. `restore` **always** applies a persistent global `send_quarantined=1` marker before making the restored database usable, even when it contains no attempts; it is checked transactionally in every send claim and cannot be bypassed in P8b. Separate trusted initialization is only for a genuinely new ledger; never use `init` over an existing restored database. `verify`, `get`, `list`, `recompute`, `backup` remain allowed in quarantine. No `unquarantine` or `--force` subcommand. Preserve sidecars/unknown files after failures, use owner/path protections and exclusive new destinations.

## 4. Telegram transport contract

Authoritative reference checked on 2026-10-21: https://core.telegram.org/bots/api (Bot API 10.3 page, 2026-08-24 release). `getMe`, `getChat`, and `sendMessage` on the fixed official endpoint. SendMessage returns a `Message` after API acceptance; this does **not** prove human delivery/read. Telegram's 1–4096 characters does **not** relax CMT's independent 4096 **UTF-8 bytes** ceiling. ResponseParameters supplies `retry_after` as seconds for rate limiting.

- Only `https://api.telegram.org/bot<TOKEN>/<METHOD>` constructed internally; no endpoint override, path injection or user-supplied URL. TLS verify true. Only `POST` for send and official API reads; reject redirects, disable inherited proxies, implicit retry and urllib/HTTP client debug logging.
- Payload `chat_id` (validated integer), `text` **exact frozen P8a string**, `link_preview_options={"is_disabled":true}`. No `parse_mode`, entities, chat topics, extras or arbitrary text CLI. Avoid `disable_web_page_preview` if unsupported by current spec; test exact JSON form body.
- Token local `CMT_TELEGRAM_BOT_TOKEN` **only** (never command args, DB or output); verify via `getMe.id==bot_id` before sending; `getChat` on explicit `destination-validate` must match `chat.id` and type `private`. A successful `getChat` alone cannot prove user ownership; require explicit operator attestation before route can become eligible. Recheck token bot identity on send so rotation to another bot is rejected.
- Default **15s overall** (user-set max 30s) with bounded connect/write/read budgets. A per-read socket timeout alone is not an overall deadline; design an explicit monotonic overall bound and test DNS stalls, slow drips and uncooperative read. If using a supervised child process for a hard bound, claim first, kill child on deadline and mark `uncertain` to avoid duplicate; never run two concurrent send workers for one claim. Any unbounded DNS behavior is a failed AC-T11, not a documentation-only waiver.
- Read at most 65536 body bytes plus one sentinel; strict UTF-8/JSON parser: no duplicate keys, bool-as-int, non-finite numbers, missing mandatory fields, invalid nesting or excessive depth. Validate only the necessary provider projection. On 200 require JSON `ok is True`, positive integral `result.message_id`, exact integral `result.chat.id`, `result.chat.type == 'private'`, exact `result.text == frozen_message` and a coherent sender identity when present/required by chosen contract. Decide minimum other receipt fields (e.g. date) explicitly before code and test missing/mismatched combinations. Store only `(message_id, accepted_at, bot_id, chat_id, response_digest?)` necessary to prove acceptance without full provider JSON/persona.
- 429 with a valid positive finite/bounded integer `retry_after` can yield retryable with persisted UTC `not_before` and at most three total attempts. 5xx, parse errors, unreadable HTTP response or transport exceptions after intent claim yield uncertain. 4xx requires strictly parsed evidence of rejection before permanent_failure. Never surface full URLs (contain token), response bodies, raw exceptions, bot/chat/user names in logs/CLI.
- Failure-first test cases include redirect, reflected token in `description`, malicious JSON, TLS exception with token, 64KiB+ response, response trickle, truncation, wrong recipient, 200 malformed, confirmation local commit failure, network uncertainty, clock skew, duplicate requests and lost CAS.

## 5. Proposed CLI (adjust only to match repository style)

`cmt telegram-delivery <operation> --ledger-db PATH ...` with strict parser, fixed error categories and JSON stdout. No network except `destination-validate` (explicit metadata reads) and `send` (explicit metadata validation + one sendMessage). No init implicitly.

| Operation | Required arguments | Behavior |
| --- | --- | --- |
| `init` | `--ledger-db` | New trusted DB and schema v1 only |
| `destination-add` | `--ledger-db --alias --bot-id --chat-id --operator-private-owned` | Pins route/ownership attestation offline, no network |
| `destination-validate` | `--ledger-db --alias` | Explicit `getMe`/`getChat`; records validated identities; no send |
| `prepare` | `--ledger-db --captures-db --journal-db --outbox-db --alert-id --comparison-id --alias` | Origin recompute, freeze, insert/replay/conflict; no network |
| `send` | `--ledger-db --captures-db --journal-db --outbox-db --delivery-id` | Verify, CAS claim, at most one Telegram send |
| `get` | `--ledger-db --delivery-id` | One validated record/last safe attempt |
| `list` | `--ledger-db [--state] [--limit 1..1000] [--cursor]` | Strict bounded keyset pagination |
| `verify` | `--ledger-db` | Owner/schema/relations/content digests/state transitions and quarantine |
| `recompute` | `--ledger-db --captures-db --journal-db --outbox-db --delivery-id` | Explicit original-capture proof; read-only |
| `recover` | `--ledger-db --delivery-id --worker-quiesced` | Change stale in_flight to uncertain only; never allow retry |
| `backup` | `--ledger-db --destination NEW_PATH` | Consistent SQLite snapshot, exclusive new output |
| `restore` | `--ledger-db BACKUP_PATH --destination NEW_PATH` | Exclusive restore + permanent dispatch quarantine |

CLI outputs must never expose token, URL, chat_id, bot_id, message text or full error body; raw P8a preview stays a separately intentional local operator function. Fixed error category and exit code (0 success/replay, 1 local/transient IO, 2 invalid/conflict/blocked policy) with machine readable result; specify and test all codes.

## 6. Proposed SQLite layout and security

New distinct application_id (e.g. `0x434D5444`, CMTD), `user_version=1`, unique owner string `card-market-tracker.telegram-delivery`, `STRICT` tables, exact DDL/index inventory verified on reads, `foreign_keys=ON`, durable `synchronous=FULL`, journaling compatible with existing restore strategy, NO implicit migrations. Proposed tables: `delivery_metadata(singleton, owner, schema_version, send_quarantined)`; `destinations(alias PRIMARY KEY, provider, bot_id, chat_id, private_type, attested, validated_at)`; `deliveries(delivery_id PRIMARY KEY, alert_id UNIQUE, event_id, provider, alias FK, comparison_id, frozen_message_sha256, frozen_evidence_sha256, frozen_route_sha256, state, attempt_count, active_attempt_id, not_before, created_at, changed_at, UNIQUE(provider,event_id))`; `delivery_attempts(attempt_id PRIMARY KEY, delivery_id FK, ordinal, claimed_at, result_state, error_category, receipt_message_id, receipt_accepted_at, UNIQUE(delivery_id,ordinal))`. Include immutable message text only if needed for auditing; prefer hash and retrieve exact message from P8a after recompute; never store token. Add necessary CHECKs/foreign key constraints and strict bounded decoded cell validation.

Backup snapshot must be consistent; restore must set quarantine within a durable transaction before exposing the DB. No sidecar deletion on exceptional paths. Reuse vetted path/file checks from P8a (taking care not to treat owner-specific DBs as each other). Reject one inode used as two source/ledger paths. Advisory locks alone are insufficient; SQLite CAS/uniqueness must establish the single-claim guarantee.

## 7. Quality gates and evidence

- Unit/contract tests with **fake transport**, no real network: message bytes, strict request/response projection, getMe/getChat, reflected secrets/redaction, timeouts, mixed 4xx/429/5xx, 200 malformed, no implicit calls from import/init/preview/prepare/smokes.
- SQL/process tests: concurrent claims across two independent Python processes, owner fencing, stale finisher, crash before HTTP / mid HTTP / after remote acceptance before local receipt commit, restart replay, existing confirmed 0 sends, 429 not-before/max3, rollback and lock contention, corrupted SQLite cells, disk-full simulated IO, unknown owner/schema, dirty sidecars.
- Backup/restore: snapshot taken before a confirmed send -> restore quarantines **every** attempted delivery including rows absent from snapshot; no bypass even with a copied/stale backup, forever in P8b.
- Origin checks: modify captures/journal/outbox and ensure local verify vs full source recompute distinction, zero send on mismatch, matched contents frozen before commit. Synthetic sequence follows captures -> journal -> outbox -> ledger; never send arbitrary CLI input.
- Ninth `scripts/telegram_delivery_smoke.py`: wheel-installed in isolated environment, nonroot UID 10001, **separate processes**, persistent SQLite, 0 network and fake transport; preserve all eight previous harnesses. Wire into CI Quality/Compose/linux-amd64/linux-arm64. No production token in CI.
- Frozen `uv sync`, Ruff format/check, mypy strict, all pytest, 85%+ lines and 80%+ branches or stricter existing thresholds, wheel/sdist from outside source tree, dependency audit, secret scan, Docker and full four CI jobs. Cite real job IDs and logs, not previous-phase percentages.
- Two independent author-distinct QA/REVIEWER final reports for exact HEAD/tree. If a later edit changes code, revalidate reviews/gates as appropriate.
- Live gate T17: after offline candidate clean/reviewed, operator identifies and authorizes their private Telegram chat. One synthetically generated P8a alert, one **explicit** `send` invocation, <=8 `getMe`/`getChat` metadata calls, **one** sendMessage attempt; validate/send receipt durable, replay after process restart and 0 additional send calls. Never request token in chat, log it, publish it or create secret fixture. Without authorized destination/token, mark T17 BLOCKED / LIVE_UNVERIFIED.

## 8. Deliverables, findings and handoff rule

Copy the exact contract to `docs/phases/P8B_TELEGRAM_ALERT_DELIVERY_CONTRACT.md`; update ROADMAP to attribute P8a closed and P8b opened **to the Orchestrator chat decision**. Publish final ADR-0011, `TELEGRAM_DELIVERY_V1.md`, `TELEGRAM_DELIVERY_STORAGE_V1.md`, threat model, runbook, actual tests/harness, CLI docs, ownership matrix and reproducible evidence. Keep TD-001..TD-005 OPEN and P2/P6a/retail Discovery BLOCKED; record only actual new significant debt with exit criteria. The initial drafts in this handoff are proposals, not accepted repo documents.

Do not claim full AC pass until each of AC-T01..T18 is tied to observed evidence. PR may be opened without merge when a candidate exists; final phase status can only be READY_FOR_ORCHESTRATOR_REVIEW if the required gates, including T17, actually pass. Otherwise declare BLOCKED with unmet gates and exact recovery instructions. The **Orchestrator alone** may authorize the exact-head merge and after-push acceptance/closure.
