# ADR-0015 - Independent manual Watchlist Telegram delivery

Date: 2026-10-30. Status: PROPOSED - Phase Lead design review required.
Scope: P8d design only; no writer/schema/definitive identity implementation.
Authority: [Orchestrator contract](../phases/P8D_MANUAL_WATCHLIST_TELEGRAM_DELIVERY_CONTRACT.md),
[Brief](../phases/P8D_CODEX_ENGINEERING_BRIEF.md) and subsequent Phase Lead Gate A
authorization in chat. Design acceptance is separate from implementation,
candidate acceptance, merge and phase closure.

## Context

P5a retains immutable Watchlist revisions; P5b records synthetic evaluations and
per-rule fresh NO_MATCH-to-MATCH wsig1_ signals. P8c renders immutable walt1_
offline previews with complete original-backed evidence. These are historical
simulations and provide no present-day Telegram consent. P8b owns a separate
Discovery delivery authority and accepted HTTPS transport. Reusing its
application admission would incorrectly mix alt1:/evt3: and walt1_/wsig1_.

Manual remote acceptance and SQLite receipt persistence have no distributed
commit. A crash, ambiguous HTTP result, concurrent sender or stale restored
ledger can duplicate an alert if treated as ordinary retry. RW-01 also showed
that a verifier-only global Watchlist invariant is insufficient.

## Decision

1. Propose a new watchlist_delivery boundary and independent owner
   card-market-tracker.watchlist-telegram-delivery, schema/user_version1,
   application_id 0x434D545A (CMTZ). The baseline source allocation audit found
   CMT1, CMTA, CMTD, CMTJ, CMTQ, CMTW and CMTY; CMTZ is unallocated. This is
   repository-local collision evidence, not a global SQLite registry claim.
   Record the reproducible audit and exact literal DDL in
   [storage v1](../data-contracts/WATCHLIST_TELEGRAM_DELIVERY_STORAGE_V1.md).
   No prior SQLite schema/owner/identity/writer is modified or migrated.

2. Admit only one explicit pending/offline_preview/synthetic P8c alert, exact
   manifest and four distinct safe existing DB paths. Use the existing P8c
   consistent pair reader, complete local verification, original-backed
   recompute through P5a exact revision/P5b genuine signal, and before/after
   pair equality. Reconstruct the full entry and evidence, not caller hashes.
   No P8c accessor change is presently needed. Source read snapshots are
   separate; immutable originals and trusted local directories remain explicit
   assumptions. Do not rerender, truncate or reinterpret current preferences.

3. Offline review exposes redacted content commitments. The operator privately
   inspects the exact P8c message and acknowledges the historical synthetic
   demonstration explicitly with the exact alert/signal/revision/message/
   evidence/route binding described in [API v1](../data-contracts/WATCHLIST_TELEGRAM_DELIVERY_V1.md).
   Preview alias and historical enabled preferences do not grant consent.
   The private route matches that alias, is operator-attested and immutable;
   a repeated validated_at changes no route identity. Local consent is not a
   cryptographic signature or proof against a malicious host administrator.

4. Follow the Orchestrator wtdl1_ formula exactly: SHA256 of ASCII
   CMT_WATCHLIST_TELEGRAM_DELIVERY_V1, one NUL, and canonical strict
   {identity_version:1,provider:"telegram",signal_id:wsig1_}. Deduplicate on
   UNIQUE(provider,signal_id), independent of alias. Immutable first alert,
   route, consent, full entry/evidence and exact message bind the row.
   Identical prepare replays; any changed binding conflicts without overwrite.
   Keep independent literal-preimage format oracles separate from production
   authenticity. Definitive implementation waits for design acceptance.

5. A one-use private application receipt binds exact instance, canonical
   content, issuer, operation, all source/route commitments and the issuing
   Budget. Copies, mutations, fake DTOs, a second consumption or a renewed
   deadline confer no authority. This guards ordinary application boundaries,
   not arbitrary privileged Python. The writer additionally reconstructs the
   same complete semantic and global invariants as verify under BEGIN IMMEDIATE.
   Full entries for a retained (watch_id,revision) must agree across every
   signal, alias, route, product/series and preparation. Equivalent source
   copies remain admissible. An incompatible second genuine bundle rolls back.

6. States are ready, in_flight, retryable, confirmed, permanent_failure and
   uncertain. Before claim, check healthy/nonquarantined ledger, exact original
   bindings/consent/route, bot, state, clock/cooldown and lifetime count. Commit
   immutable unpredictable attempt ownership plus in_flight before one
   sendMessage, release SQLite, then finalize using attempt/owner/state CAS.
   No SQLite transaction spans HTTP. Competing processes cannot share a claim.
   All late result/recovery operations are fenced. Each claim retains the exact
   route validation timestamp used at admission; a later revalidation cannot
   invalidate old history. This operational snapshot changes no identity.

7. Confirmed requires strict validated provider acceptance and durable receipt.
   A timeout, malformed success, possible acceptance followed by local failure
   or lost response is uncertain, or remains blocked in_flight if persistence
   fails. Neither state authorizes resend. Only an explicit valid429 permits
   retryable with bounded not_before and a later manual invocation, maximum3
   lifetime claims. Third429 ends permanent_failure/retry_exhausted.
   Recovery requires worker quiescence and only yields uncertain.

8. Reuse only P8b TelegramTransport and its result/receipt types through a
   narrow lazy port. Preserve official HTTPS/TLS, fixed getMe/getChat/
   sendMessage, bounded strict response parsing, exact bot/private-chat/text
   validation, no inherited proxies/redirects/debug/retries, no parse_mode/
   entities/topics and disabled link previews. Never call P8b prepare/send.
   Offline commands, all help/errors and confirmed replay import no Telegram
   and read no token. Check global quarantine BEFORE any confirmed replay and
   return verified local replay without requiring originals. Ordinary JSON/logs
   expose no private destination IDs, text, token or raw receipts.

9. One monotonic budget starts before CLI parsing and covers serialization.
   Local default2/max5 seconds; destination validation/send default15/max30
   seconds including metadata/origins/final persistence. All origin work in
   send shares one aggregate ceiling of5 seconds and the parent deadline.
   Reserve finalization time without refreshing either deadline. Persisted UTC
   microsecond-Z event timestamps and a conservative high-water rule prevent rollback
   from bypassing cooldown. Exact rules/outcomes belong to API/storage.
   Supervised P8b worker bounds DNS/connect/write/read; SQLite/filesystem/stdout
   are cooperative and blocked kernel syscalls are outside hard preemption.

10. Deep local verify reconstructs schema/inventory, JSON, complete bindings,
    global entry agreement, history/claims/results, clock/cooldown and receipts.
    Origin recompute separately validates unchanged P5a/P5b/P8c originals.
    Neither opaque commitments nor local verify authenticate the originals.
    Backup verifies independent source/copy/reopened snapshots. Restore to a NEW
    exclusive destination establishes durable global quarantine in staging
    BEFORE exposure and rechecks it after reopen. Quarantine covers unknown
    post-backup deliveries and new preparations; no clear/force/unquarantine
    command exists. Preserve safe inode/sidecar/reparse/link/owner handling,
    fsync and owned-link compensation; preserve foreign evidence on refusal.

11. Freeze bounded lazy CLI/DTOs/errors/logging and operator
    [runbook](../runbooks/WATCHLIST_TELEGRAM_DELIVERY.md) in this design package.
    Implementation later adds a thirteenth offline installed-process harness
    without changing the twelve accepted ones. Full gates, independent nonauthor
    QA and distinct final REVIEWER apply to the exact final candidate. This
    design review is neither of those runtime acceptance reviews.

## Alternatives

Reusing the P8b ledger/admission or fabricating Discovery events would mix
authorities. Mutating P8c pending rows would break its accepted contract.
Deduplication by alert/alias/route would permit the same signal to send twice.
Retry after uncertainty, clock rollback or restore would fabricate no-send
knowledge. Unquarantine, operator force, scheduling and bulk APIs exceed P8d.
A generic delivery framework or broad source refactor is unnecessary.

## Consequences

Conservative ambiguity handling can omit a notification. Correct operation
requires one trustworthy ledger, immutable source revisions, operator-controlled
directories/ACLs, maintained UTC and sufficient recovery headroom. Independent
clones are not coordinated; no global exactly-once guarantee is possible.
Whole-history folds can legitimately exhaust the contract deadline, especially
on QEMU. No partial verification or timeout enlargement is accepted as success.
Process crashes and ARM64/QEMU cannot certify physical Raspberry Pi power loss.
TD-001..TD-005 remain OPEN; no excluded feature is invented as new debt.

## Status and review boundary

Proposed design target only. ARQ/BE, DB-OWNER and SEC/SRE inputs and actual
design probes are recorded in [Design Freeze handoff](../phases/P8D_DESIGN_FREEZE.md).
Phase Lead must accept this design before product schema/identity/writer work.
AC-WT20 remains BLOCKED - LIVE_UNVERIFIED: no current live authorization,
metadata calls, real credentials, qualification sends or inherited P8b-T17
permission. Only Orchestrator may accept/merge/close the phase.

## Revisit conditions

Only an Orchestrator-authorized contract can introduce new sources, channels,
multiple recipients/live authorities, reconciliation or quarantine lifting,
shared-directory/multiuser deployment, automatic sending/retention, identity
changes or stronger physical durability guarantees. Any material change to the
frozen DDL, canonical schemas, consent, outcomes or deadlines requires a revised
design decision and affected independent reviews.
