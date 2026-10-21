# P8b engineering plan and protocol freeze

Date: 2026-10-21. Authority: the verbatim Orchestrator contract and supplied
Engineering Brief. Proposal documents are design inputs, not execution evidence.
Only the Orchestrator can accept, authorize merge, or close the phase.

## Preflight

Remote `https://github.com/KastaTM/card-market-tracker.git`; fetched main
`ac35d4df0f3a006ff60bb026de992c366e19cc09`, tree
`d604d3b8362c30af8b5dd516eddc0d8095fe7bf9`. GitHub independently returned
the same branch SHA/tree. All registered worktrees were clean; no local or remote
P8b branch collision. The original checkout was P8a head
`cf3c8f17128a5459d4d0f9228b2f1456e120817b` with the authorized identical tree.
Created `feat/p8b-telegram-alert-delivery` from the authorized main SHA.

Baseline run [39565851306](https://github.com/KastaTM/card-market-tracker/actions/runs/39565851306)
reports successful quality, compose, linux/amd64 and linux/arm64 jobs. This is
baseline evidence only. Local Docker daemon is unavailable. The sandbox command
launcher failed before shell start; reviewed escalated workspace commands work.
Existing authenticated local git/gh are available; no new credential is needed.

## MODEL PROFILE USED

Requested lead: GPT-6.1 Sol / Medium, High for critical durability/security work.
The lead runtime identifies itself as GPT-6-based Codex; no exact model selector
or reasoning control is exposed to the lead. Those exact settings are unknown.
The collaboration selector explicitly offers `gpt-6.1-sol`; DB, transport and
application author agents are selected as `gpt-6.1-sol` / `high` for these critical
paths. QA and REVIEWER will be distinct nonauthor agents selected with the same
observable profile. A planned review is not an executed review.

## Exclusive ownership

| Role / agent | Exclusive writes | Check |
| --- | --- | --- |
| ARQ / DB-OWNER `db_owner` | new delivery schema/storage; storage tests | QA and REVIEWER |
| INTEGRATIONS / SEC / SRE `transport_owner` | new transport; transport tests | QA and REVIEWER |
| BE `application_owner` | new package init/errors/application/CLI; application/CLI tests | QA and REVIEWER |
| Engineering Lead | shared CLI/logging registration, smoke/CI, all documentation, Git integration | QA and REVIEWER |
| QA, selected after freeze | external own probes/report, no candidate source edits | REVIEWER |
| REVIEWER, distinct from QA/authors | external final exact-SHA/tree audit/report | Orchestrator |

No competing DB authors. No changes to older outbox/capture/journal source,
schemas, identities or comparators. Shared files and Git changes remain serial.

## Frozen decisions before implementation

Adopt ADR-0011 for implementation, without asserting phase acceptance. CMTD
application ID `0x434D5444`, schema1, exact STRICT inventory, DELETE/FULL and FK.
Use five tables: metadata, immutable destinations, deliveries, append-only claims
and separate append-only one-result-per-claim evidence. A mutable delivery cache
must agree with reconstructed claim/result history during local verification.

Identity is `tdl1:` plus SHA256 of canonical ASCII JSON containing exactly
`identity_version=1`, `alert_id` and `provider=telegram`. Unique provider/alert
and provider/event constraints prevent alias rotation duplicates. Known vector:
`alt1:` + 64 zeroes yields
`tdl1:df549d47dc58e3404ca349cb0328939dd8c8f6cb619e592bd1302c743b4cb6bf`.

Private application receipt binds ten fields: alert_id, event_id, comparison_id,
alias, intent_sha256, message_sha256, event_sha256, journal_content_sha256,
alert_content_sha256 and evidence_content_sha256. The last two hash canonical
complete validated outbox alert and the projection
`{alert_id,comparison_id,event,journal_content_sha256,event_sha256}` respectively.
Route hash binds immutable alias/provider/bot/chat/private/ownership values and
excludes validation time. Preparation and each send repeat original recompute
and compare frozen snapshots; sources remain read-only and assumed immutable
between independent transactions.

Claim commits before sendMessage and no SQL transaction spans network IO. Finish
requires exact delivery, active attempt and in_flight state. Recovery requires
explicit quiescence and fences to uncertain. No in_flight expiry, resend from
uncertain or force. Valid 429 alone permits later explicit retry, UTC not_before,
max3 attempts; a third 429 ends permanent_failure/retry_exhausted. Reject local
clock rollback; correct host UTC remains an operator assumption across restarts.
Every restore durably quarantines the whole ledger, including absent deliveries;
no P8b command clears it.

Transport is stdlib HTTPSConnection to api.telegram.org:443, default TLS trust,
no proxy/redirect/retry/debug. POST methods limited to getMe/getChat/sendMessage.
Child reads token from CMT_TELEGRAM_BOT_TOKEN, never process args or output.
Supervised process enforces monotonic overall deadline including DNS/slow IO.
Metadata validation uses getMe/getChat; send checks getMe before claim and then
exactly one sendMessage with exact frozen text and disabled link previews.
Strict UTF8/JSON <=65536 bytes, depth16, duplicate/nonfinite/type rejection.
Positive bot/chat <=2^52-1; message ID <=2^63-1; date <=253402300799.
Success also checks sender is_bot/id, private recipient, exact text and date.
Receipt has exactly message_id, accepted_at (provider Unix date), bot_id, chat_id.
Only durable receipt commit means confirmed, not human receipt/read.
429 retry_after range1..86400; validated 4xx except408/409/425/429 may be
permanent; all ambiguous/5xx/malformed/timeout outcomes are uncertain.

## Ordered work and evidence

1. Import exact contract/brief; freeze ADR, API, storage and error/CLI protocol.
2. Implement exclusive modules and focused fake-transport/process tests.
3. Add ninth offline installed-process smoke across wheel/Compose/AMD64/ARM64;
   preserve all eight earlier harnesses, UID10001, no runtime network.
4. Frozen install, format/lint, strict mypy, complete pytest/85% lines/80% branches,
   build, outside-checkout wheel, dependency audit and secret scan.
5. Freeze candidate SHA/tree; distinct nonauthor QA and REVIEWER inspect that
   exact candidate, their own probes and all four complete CI job logs. Any
   substantive fix renews affected checks/reviews on the new candidate.
6. Prepare normal-pipeline synthetic alert and local live-gate instructions.
   No real send without specific operator authorization; no token requested in
   chat. T17 is BLOCKED / LIVE_UNVERIFIED until one authorized real attempt,
   durable receipt and separate-process replay are observed.
7. Open unmerged PR; publish and read back full AC-T01..T18 report, exact objects,
   jobs/logs/reviews/findings/limitations. Missing mandatory gates mean BLOCKED.
