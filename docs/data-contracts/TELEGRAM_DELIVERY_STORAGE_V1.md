# Telegram Delivery Storage Contract v1

**Status:** frozen for P8b implementation, not gate evidence. Independent of outbox v1 (CMTA), capture schema2 and discovery journal v1. Exact executable DDL/inventory is [schema.py](../../src/card_market_tracker/telegram_delivery/schema.py), with decisions frozen in [the engineering plan](../phases/P8B_IMPLEMENTATION_PLAN.md).

## Ownership

Dedicated owner `card-market-tracker.telegram-delivery`, distinct SQLite `PRAGMA application_id` (candidate `0x434D5444`), `user_version=1`, `STRICT` tables, `journal_mode=DELETE` unless an ADR amendment justifies otherwise, `synchronous=FULL`, FK enabled. Validate exact table+index inventory and owner metadata for each operation, as in `alerts/storage.py`; default path/sidecar hardening reused, no implicit init or file clobbering. For every untrusted SQLite TEXT, perform SQL-side `typeof` and byte-length guards before Python materialization, then strict semantic validation and digest recomputation. Read in bounded pages, not fetchall.

## Frozen tables and constraints

`delivery_metadata(singleton CHECK 1,owner,schema_version,send_quarantined)`; flag persists across restarts, is set on restore, and has **no P8b clearing command**.

`destinations(alias PRIMARY KEY,provider CHECK telegram,bot_id INTEGER,chat_id INTEGER,chat_type CHECK private,operator_attested CHECK 0/1,validated_at)`; immutable route after registration, except allowed idempotent validation timestamp update with equivalent identities. No credentials.

`deliveries(delivery_id PRIMARY KEY,alert_id UNIQUE,event_id,provider,alias REFERENCES destinations,comparison_id,journal_digest,event_digest,message_digest,route_digest,state,attempt_count,current_attempt_id,not_before,created_at,updated_at,UNIQUE(provider,event_id))`; enforce bounded tokens, state CHECK, valid not_before use, monotonic attempt count, immutable evidence digests and route binding.

`delivery_attempts(attempt_id PRIMARY KEY,delivery_id REFERENCES deliveries,ordinal,claimed_at,UNIQUE(delivery_id,ordinal))` records immutable claims.

`delivery_attempt_results(attempt_id PRIMARY KEY REFERENCES delivery_attempts,state,completed_at,error_category,retry_after,not_before,message_id,accepted_at,bot_id,chat_id)` records at most one immutable result per claim. No update or deletion API exists for either history table. Local verify reconstructs state/count/active owner/cooldown and requires exact agreement with delivery caches, contiguous ordinals and valid receipt/state combinations. A pending claim has no result and corresponds to in_flight only. Terminal states cannot have later claims; only a valid rate-limit result can precede a retry.

Deliveries additionally freeze `alert_content_sha256` (canonical entire validated
outbox alert dict) and `evidence_content_sha256` (canonical
`{alert_id,comparison_id,event,journal_content_sha256,event_sha256}`). The exact
column names use `intent_sha256`, `message_sha256`, `event_sha256`,
`journal_content_sha256`, `route_sha256`, `current_attempt_id`, `updated_at`.
Destination ownership column is `operator_attested_owner`, explicitly1; no
implicit attestation. Route hash excludes validated_at and binds immutable route.
All TEXT/INTEGER projections are SQL guarded before Python materialization.
SHA256 suffixes are64 lowercase hex; aliases retain P8a grammar; ordinals1..3;
all timestamps have strict UTC microsecond format; unknown inventory/owner/version
is refused without migration. DEFAULT local timeout2/max5 is shared by each SQL
operation. Reads verify complete history under the same bounded snapshot.

An implementation can refine column naming but cannot omit the invariant that **an unknown delivery after backup is blocked by global quarantine**. No unsafe restore-to-existing-db overwrite, no force. Owner/schema/version mismatch -> category error, no write/send.

## Atomic protocol

`prepare`: recompute original outside ledger transaction, recheck immutable content snapshot, `BEGIN IMMEDIATE`, compare dedup indexes and frozen route/evidence, insert once or replay; rollback entirety on conflict.

`claim`: verify local frozen data + preflight remote bot identity before claim; `BEGIN IMMEDIATE` atomically check `send_quarantined=0`, route validated/attested, deliverable state and attempt count/not_before, insert durable attempt and CAS state->in_flight/owner; **COMMIT** before sendMessage. No transaction held over HTTP.

`finish`: `BEGIN IMMEDIATE`, CAS where delivery_id, `current_attempt_id`, `state=in_flight` and expected version match. Persist strict receipt and `confirmed` together or terminal classification. If commit cannot be confirmed, do not re-send; after restart in_flight remains blocked pending manual uncertain recovery. Old attempt can't overwrite newer attempt's finalization.

`recover`: only explicit operator-certified worker quiescence, in_flight -> uncertain; never reopen to ready.

`backup`: SQLite online backup consistent snapshot, exclusive new safe target, validate/reopen. `restore`: validate source, exclusive new target, mark `send_quarantined=1` durably **before** returning/restored use. A backup before a later send cannot know that send took place, even for missing rows; hence global quarantine even for apparently empty source. Verify and read operations may continue.

## Failure-first tests

Owner/DDL/index tamper, FK orphan, oversized cells, malformed JSON, duplicate provider/event identity, invalid state/transitions/attempt sequence, two processes claim one delivery, lost CAS owner, interrupted process around claim/HTTP/finish, disk full and busy writer simulation, restored stale backup with missing delivered row, quarantined empty backup, renamed file / inode swap / sidecar left over, non-root restart, read-only origin changes, and zero sends in all invalid/replay paths.

Process-kill and QEMU tests do not prove real power loss. A single trusted ledger authority is assumed; clones and independently active restores are outside the guarantee.
