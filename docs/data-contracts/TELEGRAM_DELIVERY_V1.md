# Telegram Delivery API / CLI Contract v1

**Source:** P8b Orchestrator contract. **Status:** frozen for implementation, not evidence of gate execution or Orchestrator acceptance. See [protocol/ownership](../phases/P8B_IMPLEMENTATION_PLAN.md).

## Identity / binding

Canonical: `json.dumps(v,ensure_ascii=True,sort_keys=True,separators=(',', ':'),allow_nan=False)` -> UTF-8 ASCII bytes. Lowercase SHA-256. Delivery key: `tdl1:` + SHA256 canonical `{ "identity_version":1, "alert_id":"alt1:<64 hex>", "provider":"telegram" }`. Unique per alert and provider, plus unique `(provider,event_id)` to prevent alternate-alias copies. No timestamp, bot, route, comparison, message or nonce in identity preimage. Attempt ID must be unique and never reused. Route `(alias, provider='telegram', bot_id, chat_id, private, operator_attested)` is immutable, numeric IDs locally private, and token is only in local process environment.

Prepare is called with exact `alt1`, `cmp3`, four distinct trusted DB paths, and route alias equal to P8a destination_key. It invokes original capture recomputation and validates alert/event/association and SHA256 of frozen original message before any write. It freezes one selected association plus digests. Later prepare with equivalent inputs yields `replay`; a difference yields `conflict` and does not overwrite. Prepare never contacts Telegram.

## States and allowed operations

`ready`, `in_flight`, `retryable`, `confirmed`, `permanent_failure`, `uncertain`; no automatic transition out of uncertain or confirmed. The attempt count increases and claim commits before HTTP. Only `ready` or eligible `retryable` (due time and attempt_count<3) can claim; the exact `attempt_id` owns the finalization. A replay of `confirmed` makes zero send calls, including after process reopen. Crash after claim never permits an automatic resend. Only validated 429 plus positive bounded `retry_after` permits a later attempt; each invocation at most one send. Permanently failed, uncertain or quarantined cannot send. Manual recovery with explicit quiescence may move a stale in_flight to uncertain only. No force.

## Telegram calls

Allowed official methods: `getMe`, `getChat`, `sendMessage`. `destination-validate` may call getMe/getChat; send additionally checks token identity. Only exact pinned private chat, with ownership attested by operator. Production request to fixed HTTPS API, strict TLS validation, no redirect/retries/environment proxy; send only `chat_id` numeric, `text` frozen P8a string, `link_preview_options={"is_disabled":true}`. No parse mode, entities, topic, content rewriting or arbitrary-text CLI.

- Token: local `CMT_TELEGRAM_BOT_TOKEN`, no token args, no DB/log/fixture/errors or shared script.
- Size limits: frozen message <=4096 bytes UTF-8; response <=65536 bytes; bounded depth and strict JSON types/keys (reject duplicate JSON keys and bool-as-int).
- Timeout: default 15s **overall**, maximum configurable 30s, testable on connect/read/write/DNS/slow response. A socket read timeout on its own does not satisfy this contract.
- Success: valid 200 and `ok is True`; `result.message_id` strictly positive int; `result.chat.id` strict integer exactly pinned; `result.chat.type` private; `result.text` equals frozen original; validate additional critical fields (e.g., sender and date) as contract implementation defines. Only durable receipt commit yields confirmed.
- Explicit 429 with strict positive `parameters.retry_after` -> retryable, persist UTC not_before and attempt. Explicit validated permanent 4xx -> permanent_failure. 5xx, lost connection, timeout, ambiguous/malformed success, local commit failure after possible acceptance -> uncertain.
- Receipt: minimum provider, method, message_id, accepted timestamp, delivered route ID represented privately and optionally provider projection digest; **no full body or names**. `confirmed` is provider acceptance, not human read.

## Exact CLI and response protocol

Group `cmt telegram-delivery`; every operation requires `--ledger-db PATH`.
No implicit initialization, latest selection, all-send or arbitrary-text input.

| Operation | Additional arguments |
| --- | --- |
| init, verify | none |
| destination-add | --alias ALIAS --bot-id INT --chat-id INT --operator-private-owned |
| destination-validate | --alias ALIAS |
| prepare | --captures-db PATH --journal-db PATH --outbox-db PATH --alert-id ALT1 --comparison-id CMP3 --alias ALIAS |
| send, recompute | --captures-db PATH --journal-db PATH --outbox-db PATH --delivery-id TDL1 |
| get | --delivery-id TDL1 |
| list | optional --state STATE --limit INT --cursor TDL1 |
| recover | --delivery-id TDL1 --worker-quiesced |
| backup, restore | --destination NEW_PATH |

`--timeout` is finite positive: local operations default2/max5 seconds;
send/destination-validate default15/max30 seconds. Limit defaults100, range1..1000;
cursor is exclusive tdl1 key. Pages are independent validated snapshots, <=1MiB.
Boolean integers and malformed tokens/aliases are invalid. All four existing
DB paths must be distinct safe files. Only destination-validate and send can
contact Telegram. Quarantined and confirmed replay paths make zero network calls.

Every stdout response is one canonical ASCII JSON object with required keys
`version:1`, `operation:<fixed operation>`, `result:<ok|inserted|replay|error>`.
Errors include only a fixed `error_category`; send also exposes its safe local
state/delivery/attempt identifiers when known. Successful delivery operations may
include delivery_id, state, attempt_count, current_attempt_id, not_before and
immutable nonpersonal evidence hashes. get returns a redacted delivery; list
returns redacted items and next_cursor (null at end). verify adds level=local,
counts and send_quarantined; recompute uses level=origin-recompute. No bot/chat
IDs, route payload, message text, token, authenticated URL, provider body/persona,
paths, SQL or arbitrary exception strings leave the product in ordinary stdout.
Internal Python storage accessors and the private local DB contain required route
IDs; these are never serialized by the CLI.

Exit0 means operation verified/committed or replay. Exit1 means local IO/deadline,
transport ambiguity/retryable or failed confirmation; exit2 means invalid input,
conflict, blocked policy or permanent rejection. An error exit does not imply
the remote side effect did not occur. Inspect durable local state before taking
any action. CLI catches unexpected failures into fixed categories.

Categories comprise inherited bounded source/SQLite validation categories plus
invalid_destination, not_validated, send_quarantined, delivery_blocked,
retry_not_due, attempt_limit, stale_attempt, token_configuration, bot_mismatch,
destination_mismatch, transport_timeout, transport_failure, provider_rejection,
provider_rate_limit, provider_invalid, confirmation_failed, provider_rejected,
rate_limited, retry_exhausted, network_uncertain, malformed_response,
deadline_exceeded, recovered, local_commit_failed and clock_skew. Unknown
categories map to invalid_field; never echo an exception message.

One structured completion log uses event telegram.delivery.completed, fixed
operation prefix telegram_delivery_, local delivery/attempt tokens, state,
result/category, run ID and duration. All dynamic identifiers are grammar-checked;
unknown fields are omitted by the formatter.

## Frozen transport projection

Production uses supervised stdlib HTTPSConnection POST to api.telegram.org:443,
with default TLS context and no proxy, redirect, retry or debug. Each child reads
the environment token itself; it is absent from arguments and IPC results.
Application calls validate_bot (getMe) before claim; send itself performs only
one sendMessage after durable claim. destination-validate calls getMe/getChat.
The caller shares its remaining overall monotonic budget across these calls;
supervisor termination bounds stalled DNS, connect/write/read and response drip.
SQLite keeps cooperative bounds; stalled device/kernel IO is not a hard realtime
guarantee. A killed/crashed claimant remains blocked until uncertain recovery.

JSON is strict UTF8, <=65536 bytes, depth<=16; duplicate keys, NaN/Infinity,
invalid critical field types and bool-as-int fail. A valid Message requires
positive message_id<=2^63-1, date1..253402300799, sender.id equal to pinned bot
and is_bot=true, recipient.id equal to pinned chat and type=private, exact text.
Bot/chat IDs are positive integers<=2^52-1. Receipt stores exactly message_id,
accepted_at (provider Unix date), bot_id and chat_id privately.
Valid rejection requires ok=false, error_code equal to HTTP status, bounded
nonempty description and no success result. 429 additionally requires integer
retry_after1..86400. 4xx408/409/425 remain ambiguous; other validated permanent
4xx reject without retry. Any 5xx/redirect/malformed/truncated/timeout failure is
uncertain. At attempt3 a valid429 ends permanent_failure/retry_exhausted.

Metadata calls budget <=8 for one live qualification; **at most one** authorized real sendMessage attempt. CI transport always fake and credential-free. Never infer Telegram acceptance from a fake. Absence of live gate is `BLOCKED / LIVE_UNVERIFIED`.

## Independent identity test vector (non-production)

Input `alert_id=alt1:` plus 64 `0` characters, `provider=telegram`, `identity_version=1`. Exact ASCII preimage:

```json
{"alert_id":"alt1:0000000000000000000000000000000000000000000000000000000000000000","identity_version":1,"provider":"telegram"}
```

Expected ID: `tdl1:df549d47dc58e3404ca349cb0328939dd8c8f6cb619e592bd1302c743b4cb6bf`. QA must independently recompute without importing the production identity helper.
