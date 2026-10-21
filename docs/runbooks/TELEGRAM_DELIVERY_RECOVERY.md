# P8b Telegram manual-delivery recovery runbook

Implementation v1. Execute live qualification only after exact-candidate offline
gates/reviews and authorization of the specific private destination and alert.
Code existing is not proof of a live gate.

## Concrete local qualification sequence (PowerShell)

Pin the reviewed PR head/tree and install its wheel in an isolated environment.
The preparation script does not read a token or contact Telegram. It uses normal
synthetic capture -> journal -> P8a outbox APIs, selects one of two synthetic
alerts and creates an empty ledger. It refuses an existing directory. If
engineering already prepared it, reuse selection.json; do not generate another
alert for qualification. The fixed alias is operator-private.

```powershell
uv build --no-build-isolation
uv venv --python 3.13 .p8b-evidence/wheel
uv pip install --python .p8b-evidence/wheel/Scripts/python.exe --no-deps dist/card_market_tracker-0.1.0-py3-none-any.whl
.p8b-evidence/wheel/Scripts/python.exe scripts/prepare_telegram_live_gate.py --directory .p8b-evidence/live --fixtures tests/fixtures
$p8bLocal = (Resolve-Path .p8b-evidence/live).Path
$p8bSelection = Get-Content "$p8bLocal/selection.json" -Raw | ConvertFrom-Json
$p8bCli = (Resolve-Path .p8b-evidence/wheel/Scripts/cmt.exe).Path
$p8bPython = (Resolve-Path .p8b-evidence/wheel/Scripts/python.exe).Path
```

Obtain your bot ID and private chat ID locally through your authorized setup.
Set local CMT_GATE_BOT_ID/CMT_GATE_CHAT_ID accordingly. Never send those values or
the token to this chat. Inject CMT_TELEGRAM_BOT_TOKEN from local secret storage
into this process only; never CLI args/files/copied shell history/transcripts.
Confirm that this is your private chat and you authorize this exact selected
alert/message digest before continuing.

Metadata validation performs at most2 requests; send at most1 getMe plus1
sendMessage. The total metadata bound3 is below8. The wrapper records safe
invocation counts and durable receipt/history, reserves evidence before network
and refuses another qualification send on a used delivery. A failed or ambiguous
send does not authorize another attempt. Stop and escalate in that case.

```powershell
& $p8bCli telegram-delivery destination-add --ledger-db "$p8bLocal/ledger.sqlite3" --alias operator-private --bot-id $env:CMT_GATE_BOT_ID --chat-id $env:CMT_GATE_CHAT_ID --operator-private-owned
& $p8bPython scripts/telegram_live_gate.py --directory $p8bLocal --operation validate --operator-authorized
& $p8bCli telegram-delivery prepare --ledger-db "$p8bLocal/ledger.sqlite3" --captures-db "$p8bLocal/multi.sqlite3" --journal-db "$p8bLocal/journal.sqlite3" --outbox-db "$p8bLocal/outbox.sqlite3" --alert-id $p8bSelection.alert_id --comparison-id $p8bSelection.comparison_id --alias operator-private --timeout 5
& $p8bPython scripts/telegram_live_gate.py --directory $p8bLocal --operation send --operator-authorized
```

Run each next command only if the previous exit code was0. After send reports
confirmed, remove the token and start the separate replay process. Its wrapper
forbids transport calls and requires replay with zero invocations. Preserve
live-validate.json, live-send.json and live-replay.json privately. Publish only
their reviewed redacted projection together with exact SHA/tree. Human
observation, if supplied, is separate evidence from API acceptance.

```powershell
Remove-Item Env:CMT_TELEGRAM_BOT_TOKEN
& $p8bPython scripts/telegram_live_gate.py --directory $p8bLocal --operation replay --operator-authorized
```

The kickoff supplies no specific recipient authorization or production token.
T17 remains BLOCKED / LIVE_UNVERIFIED until this sequence actually succeeds.

## Operator prerequisites

1. Use a clean, reviewed exact-SHA P8b wheel installation and trusted filesystem/directories with one active ledger. Verify captures, journal and outbox independently; check ledger verification. Back up all databases consistently before experiments, but **do not assume that restoring an old ledger re-enables safe sending**.
2. Keep the bot token in a process-local secret environment variable, `CMT_TELEGRAM_BOT_TOKEN`; do not store it in scripts, shell history, CLI arguments or commits. Avoid `set -x`. Do not disclose or paste it into ChatGPT/Codex. Ensure stderr/logs redaction, restricted filesystem access and host process access.
3. Create a private chat with the intended bot manually via Telegram UI. The operator must obtain their own positive numeric chat ID **locally using an authorized path**, assert explicitly that this is their chat, and pin its route. No auto-discovery of contacts, groups, topics, updates, or scanning.
4. The CLI `destination-validate` must run `getMe` and `getChat` and confirm the configured numeric bot/chat identities and type `private`; the API response alone cannot prove human ownership. Route changes conflict, not silently rotate.
5. Generate exactly one synthetic alert through the existing **normal** capture -> journal -> P8a outbox path; `prepare` it using explicit `alt1` and selected `cmp3` and verify/recompute before any send. Never compose arbitrary text through the send command.

## Live qualification — only with operator authorization

- Stop if the operator has not authorized the **specific** synthetic alert and **specific** private destination. Authorization must be explicit; do not ask for or share a token in chat.
- Maximum **eight** metadata calls (`getMe`/`getChat`) and **one** `sendMessage` attempt; no automatic retry, no other Telegram methods. Count all actual requests.
- Record exact reviewed code SHA/tree, sanitized prepared route/alert references and message digest (not actual destination IDs or body), fake-free transport invocation count, minimal accepted receipt from `sendMessage`, subsequent `confirmed` after process exit/reopen and `replay` with **zero** subsequent requests. Human arrival observation is separate evidence, not acceptance semantics.
- If token/destination/host are unavailable, report `AC-T17 BLOCKED / LIVE_UNVERIFIED`, not PASS. Do not replace it with mock transport evidence.

## Handling a failed send

- **ready:** no claim has occurred. Recompute originals and inspect route; a new explicit send may proceed if all gates and authorization are satisfied.
- **in_flight:** assume acceptance might have occurred even if the process is dead. Never retry automatically or on timeout expiry. Establish that the worker is quiescent, then run an explicitly authorized `recover` to mark **uncertain** (no resend). If worker quiescence is not established, leave in_flight and stop.
- **uncertain:** no resend or force option. Record available independent evidence and escalate a future reconciliation strategy to Orchestrator. A local fabricated receipt is forbidden.
- **retryable:** only a validated 429 with positive `retry_after` can lead here; later explicit send is allowed only after persisted `not_before`, max three total sends. No sleep loop.
- **permanent_failure:** no automatic retry; inspect metadata/configuration and escalate planned remediation rather than changing route under same delivery.
- **confirmed:** repeat send returns replay; no Telegram call, after process restart too. Provider acceptance does **not** mean read.
- **restore:** **all** restored ledgers are quarantined globally from send. An old snapshot may omit later confirmed deliveries; even completely absent rows must not be sent. P8b does not implement unquarantine/force. Keep original ledger forensic evidence and seek an Orchestrator-approved reconciliation phase if operation must resume.

## Failure evidence and secrets

Collect local delivery ID, attempt ID, state transition, structured category, redacted duration, SHA/tree, bounded count of calls and source-evidence verification results. Never publish the token, authenticated URL, full Telegram response/body, bot/chat IDs, personal names, message text, shell history or raw exceptions. Separate market alert content from system/operational incidents; P8b does not send operational errors through Telegram.

Simulated disk full/rollback/reopen/process termination can support automated gates, not physical power-loss guarantees. Disable sending on unverified/corrupt ledger, mismatched identity or revoked/rotated bot to a different bot ID.
