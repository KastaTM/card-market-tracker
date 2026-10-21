# P8b Telegram manual-delivery recovery runbook — DRAFT

**Not executable until P8b code exists and gates pass.** Commands below use the proposed CLI, not a claimed available release.

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
