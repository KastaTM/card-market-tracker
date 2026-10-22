# ADR-0011 — Manual Telegram delivery with independent ledger

**Status:** adopted for P8b implementation; phase acceptance belongs to Orchestrator  
**Date:** 2026-10-21  
**Decision scope:** P8b only

## Context

P8a has an immutable, content-addressed offline outbox. Delivering its alert through Telegram introduces a remote side effect without a distributed transaction with local SQLite. The same discovery event may exist under more than one P8a logical destination and in multiple journal comparisons. Concurrent CLI processes, restarts, acceptance followed by local commit failure and stale backups can all produce duplicate notifications unless the delivery authority is separate, stable and conservative.

CMT targets ARM64/Raspberry Pi and local SQLite. An operator-owned private Telegram destination is the only authorized P8b transport. No scheduler, bot commands, groups or broadcast.

## Decision

1. Introduce independent owner/versioned SQLite ledger with immutable route registration, prepared deliveries, append-only attempt history and a global restored-state quarantine. Captures, journal and outbox remain read-only and unchanged.
2. Derive `tdl1` from canonical `{identity_version:1,alert_id:alt1,provider:'telegram'}` without chat/alias/token/message/clock; unique `(provider,event_id)` as a second, stronger guard against alternate P8a aliases producing duplicate Telegram deliveries. Each delivery freezes one route, comparison and semantic/message digests; mismatches are conflicts, never new sends.
3. Use explicit prepare and explicit one-shot send; both validate origin against original captures using existing recompute logic. `prepare` never contacts Telegram. Destination metadata validation (`getMe` and `getChat`) is explicit and must be backed by operator attestation of private-chat ownership.
4. Persist claim and attempt before the irreversible network call. Use durable SQLite write transaction, CAS on attempt owner and explicit finalization. Never hold an SQLite transaction across network access. Each invocation sends at most once.
5. `confirmed` means a valid Telegram `sendMessage` acceptance and a locally committed minimal receipt, **not** delivery/read. Ambiguous outcomes become `uncertain`, which forbids resend in P8b. Explicit 429 may retry later up to three total attempts, obeying `not_before`. In-flight does not silently expire; manual quiescence/fencing recovery can only move it to `uncertain`.
6. After any restore, globally quarantine **the whole ledger** from sending. The snapshot cannot prove whether an omitted row was sent subsequently; no bypass/unquarantine operation exists in P8b.
7. Official Telegram endpoint only, TLS verified, no inherited proxy/redirect/retries; bounded body + JSON validation; local env token, secret redaction, controlled deadline with failure treated as uncertain.
8. Use separate immutable claim and one-result-per-claim tables. Local verification reconstructs the mutable delivery state from complete history. Freeze ten evidence-binding fields and exact receipt/transport projection in the [engineering protocol](../phases/P8B_IMPLEMENTATION_PLAN.md) and [API](../data-contracts/TELEGRAM_DELIVERY_V1.md). A third valid 429 terminates as permanent_failure/retry_exhausted. Reject clock rollback; persisted UTC cooldown assumes a correctly maintained host clock across restarts.

## Alternatives considered

- Mutate P8a `pending` rows to sent: rejected, breaks accepted evidence schema/semantics.
- Store delivery inside capture/journal DB: rejected, couples failure and recovery domains.
- Deduplicate only per alias or `(bot_id,chat_id)`: rejected, route rotation and P8a alternate aliases could resend the same event.
- Optimistic resend after timeout or process crash: rejected; possibility of remote acceptance cannot be eliminated.
- Uncertain to confirmed without a durable verified receipt: rejected; fabricates evidence.
- Reset attempts/retry after restoring old snapshot: rejected; missing newer sends cannot be detected reliably.
- Exactly-once remote delivery guarantee: impossible with these APIs; rejected as a false promise.
- Scheduler, webhook, polling or global recipient discovery: outside P8b.

## Consequences

A false-negative notification (possible alert omission) is preferable to a potentially duplicate alert after uncertain outcomes. Operators must investigate ambiguity outside any automatic resend process. Retryable only covers clear 429 with a validated cooldown. A ledger bound to one trustworthy local authority is required; duplicating DBs across independent writers invalidates that assurance. Changed bot/chat or source evidence requires explicit future migration, not force. Strict transport deadline enforcement is an implementation gate: a per-socket read timeout alone is insufficient. ARM64 CI/QEMU cannot establish real power-loss durability.

## Revisit conditions

Revisit only through Orchestrator-authorized phase when: multi-channel/multi-recipient delivery becomes necessary; external idempotency/receipt lookup is supported; operator reconciliation and quarantine lifting are designed; DB replication/multi-writer deployment is requested; Pi physical power-loss measurements establish new guarantees; or the Telegram API security contract changes.
