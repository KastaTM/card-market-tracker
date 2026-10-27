# ADR-0014 — Independent offline Watchlist synthetic alert outbox

**Status:** Accepted — P8c Engineering Design Freeze
**Engineering design freeze:** 2026-10-26; accepted by the Phase Lead for design only.
This acceptance applies exclusively to the engineering design. It does not
accept an implementation candidate, authorize merge or declare phase closure;
those decisions remain exclusively with the Orchestrator.
**Implementation:** NOT STARTED. **P8c:** OPEN / IMPLEMENTATION AUTHORIZED.
This freezes an engineering implementation target, not Orchestrator acceptance,
merge authorization, an executed gate or phase closure.

## Authority and reviewed baseline

The normative authority is the unchanged
[P8c Orchestrator opening contract](../phases/P8C_OFFLINE_WATCHLIST_SIGNAL_OUTBOX_CONTRACT.md).
It takes precedence over this ADR and the API/storage design contracts. The
handoff's proposed ADR and contracts are reconciled by this freeze; their former
presence did not prove adoption or execution.

Worktree: C:\Projects\card-market-tracker-p8c.
Branch: feat/p8c-watchlist-signal-outbox.
HEAD: 228d5c8d0d91edf03ddb86a489c8232eeb7c08bc.
Tree: dde865b6d215efc4075918088d6deddfe7cdeb1f.
Ordered parents: 62ecd7ab792a93a6071b83277d870f1d95f61f9f,
then f80bc8cdb877946f37d76b09212d68dd8da3e246.
The Lead verified the clean local checkout before edits. The Phase Lead's latest
remote-main verification is attributed to the Phase Lead; it was not repeated
in this documentation-only step. PR17 and historical main CI are not P8c gates.

## Context and boundary

P5a owns immutable Watchlist revisions and a pure explicit-time synthetic
evaluator. P5b owns independently verified journals and rule-specific wsig1_
signals. P8a accepts Discovery evt3: events and derives alt1: alerts. P8b accepts
that contracted route and owns tdl1: delivery history and restore quarantine.
These are different evidence authorities.

P8c prepares exactly one explicitly selected Watchlist signal for one local
alias as an immutable, explainable offline preview. It adds no acquisition,
transport, credential, delivery state, scheduler, bulk operation, web API,
migration, rerender or retention policy. Product sockets and Telegram calls are
zero. Earlier store schemas, identities, evaluators, writers and recovery remain
unchanged. A historical revision authorizes simulation only, not current
notification consent. P5 global and TD-001..TD-005 remain OPEN; P2/P6a/retail
Discovery remain BLOCKED.

## Decisions

1. Introduce an independent package watchlist_alerts and owner
   card-market-tracker.watchlist-alert-outbox, application_id 0x434D5459 (CMTY),
   user_version/schema_version 1. Static audit of every current owner found
   CMT1=0x434D5431, CMTA=0x434D5441, CMTD=0x434D5444, CMTJ=0x434D544A,
   CMTQ=0x434D5451 and CMTW=0x434D5457. CMTY is unoccupied at the reviewed tree.
   No SQLite database, including an in-memory database, was created for this
   freeze. Exact DDL and the expected 13-object inventory are defined in
   [storage v1](../data-contracts/WATCHLIST_ALERT_OUTBOX_STORAGE_V1.md);
   SQLite execution/normalization remains a later implementation test.
2. Source admission revalidates the complete raw MANIFEST_V1 and exact original
   P5a entry on every enqueue/recompute, including ancient replay. One additive
   P5b private reader holds a single ro/query_only transaction, performs the
   accepted full journal verifier once, and reads the selected signal and exact
   from/to evaluations in that snapshot. The API contract fixes its signature,
   projection and error boundary. It neither accepts public DTO authority nor
   changes any existing P5b API, write, fold, transition or recovery behavior.
3. Both frozen snapshots must agree on the exact P5a watch/revision/entry and
   sequence. The application compares the full historical entry, reparses the
   complete manifest, recalculates both P5a results and derives the exact P5b
   fresh per-rule NO_MATCH-to-MATCH signal. The aggregate OR is not authority.
   No signal is regenerated for a baseline or absent signal. Different source
   read transactions are not a global three-file snapshot.
4. Freeze policy watchlist_synthetic_alert_v1, renderer integer1, channel
   offline_preview and state pending. The alias is ASCII
   ^[a-z][a-z0-9_-]{0,63}$. Freeze the four-key evidence bundle, fifteen-key intent,
   full P5b versions/IDs/links/results, canonical JSON and DTOs in
   [API v1](../data-contracts/WATCHLIST_ALERT_OUTBOX_V1.md).
   Omit source paths, global heads/counts, persisted_at, run IDs, current
   preferences and file-wide digests from semantic evidence.
5. Preserve the Orchestrator's identity exactly:
   walt1_ + SHA256(ASCII("CMT_WATCHLIST_ALERT_V1") + one 0x00 byte +
   canonical({identity_version:1,destination_key:alias,signal_id:wsig1_})).
   No renderer, text, prepared time or filename enters that identity. Canonical
   JSON uses sorted keys, ensure_ascii=True, compact separators and no NaN,
   with strict normalized field types. Vectors are not runtime admission proof.
6. The renderer is pure render(intent,evidence), not render(intent) alone.
   Evidence supplies the exact timestamps, selected-rule reasons and nullable
   monetary components absent from intent. It validates their correspondence,
   uses the exact line template/escaping in API v1, and rejects oversize rather
   than truncating. No caller-selected labels, names, URLs or PII are rendered.
7. Only a private instance-bound, complete-content-bound, issuing-Budget-bound
   single-use receipt produced after source admission reaches the P8c writer.
   A different Budget or repeated consumption fails before writer open; a valid
   expired issued deadline remains storage_timeout. The receipt stays transient. Writer validation independently
   reconstructs semantics, intent, identity, message and digests. Ordinary
   caller JSON, a copied receipt, hashes or verified=True confer no authority.
   This is an application boundary, not authentication against privileged code.
8. BEGIN IMMEDIATE serializes complete alert+evidence insertion. Equal immutable
   contents replay without UPDATE, DELETE or new first_prepared_at. Conflicting
   content rolls back. One alert/evidence per alias/signal; no global dedup across
   copies. The first successful insert's UTC clock is operational, never source
   chronology. Local verification reconstructs every retained semantic relation;
   origin recompute separately reopens sources. No trust cache crosses operations,
   snapshots, copies or independent recovery folds.
9. One cooperative default2/max5-second deadline covers parsing, source reads,
   validation, SQLite, recovery and response serialization. New P8c stages and
   the P5b helper share the same Budget object. Unmodified P5a get receives only
   remaining time and is bracketed by outer checks; it receives no new full
   timeout and no new _budget argument. SQL progress/busy handling observes the
   remaining deadline. Kernel/filesystem stalls are outside hard preemption.
10. Recovery verifies a source read snapshot, the copied provisional, and an
    independently reopened provisional, using three fresh folds before fsync
    and exclusive publication. No valid target pathname is exposed earlier.
    Post-link unlink failure uses P5b's safe owned-link compensation, retaining
    the original error and foreign/recovery evidence. Crash windows and
    postcommit/output errors are described honestly; cleanup is not unconditional.
11. Root CLI integration will load Telegram registration/dispatch lazily only
    for its prior routes/help when needed. No telegram_delivery module or
    transport is imported during the P8c route, including invalid arguments and
    help. Preserve existing command grammar/help/results and earlier tests;
    do not edit Telegram product files or broaden admission. This is the
    permitted minimal CLI integration, not a general CLI refactor.
12. Freeze exact error categories and exits, input/retained/envelope limits,
    filter-bound cursor, completion logging and failure tests in API/storage v1.
    No unknown source error is flattened into successful no-match or zero counts.
    Logs exclude aliases, IDs, evidence, money, paths, tokens and raw exceptions.
13. Preserve all gates and all eleven previous harnesses; add the twelfth across
    installed wheel, Compose, AMD64 and ARM64/QEMU. Require separate non-author
    QA and final REVIEWER on the exact candidate SHA/tree, full public rerunnable
    probes and four complete CI logs. No execution or acceptance is implied here.

## Eight readiness points resolved

| Point | Frozen resolution | AC |
| --- | --- | --- |
| Exact DDL | Literal SQL, column order, constraints, indexes, six triggers, 13-object static inventory; no DB creation now | WA04,08,10,13,19 |
| P5b bundle | Private one-transaction/one-full-fold reader; exact four-key semantic projection | WA02,03,04,07 |
| Renderer inputs | render(intent,evidence), exact required lines, monetary unknowns and UTF-8 hash | WA04,09,10 |
| Telegram eager import | Minimal deferred root registration/dispatch and fresh-process import-denial probes | WA09,14,17 |
| Shared deadline | Outer deadline, shared Budget, residual-only unchanged P5a calls, output check | WA02,03,12,13 |
| Recovery order | Source/copy/reopened provisional verified before fsync/exclusive publication | WA08,13 |
| Errors/DTO | Closed source-compatible enum, exact responses, cursor and exit mapping | WA07,11,12,15 |
| Writing oracle | Future --check/stdout-only default; fixture generation explicit; supplied script not executed now | WA05,17,18 |

These are integrated Lead decisions. Specialist advice is separately attributed
below; advice alone is not a document edit, gate PASS or implementation review.

## Specialist inputs, models and ownership

Requested Lead profile: GPT-6.1 Sol/Medium, High for architecture/SQLite/security.
The root session's selected variant and effective effort/backend are not
independently exposed; no root model switch is claimed.

Three real read-only design sessions were spawned using the tool selector
gpt-6.1-sol and reasoning_effort=high:
- /root/p8c_freeze_arq: admission, evidence/intent, renderer and errors.
- /root/p8c_freeze_db: exclusive owner/DDL, transactions, verification, recovery.
- /root/p8c_freeze_sec: privacy, import isolation, deadlines and failure modes.

The selector arguments and sessions are observable; effective backend/reasoning
is not independently verified. These sessions are design specialists, not final
implementation QA or REVIEWER. All shared-document edits belong to /root.

Cross-review separately required explicit issuing-Budget/one-use receipt
binding (ARQ) and correction of an ambiguous receipt-persistence sentence (SEC).
Lead incorporated both; DB found no blocking design defect. SQL catalog equality
is explicitly byte-exact, with runtime normalization still unexecuted.

Their review inputs separately identified: ARQ's missing renderer evidence and
source-taxonomy compatibility; DB's available CMTY ID, literal SQL and prepublish
reopen order; SEC's eager Telegram import, internal-envelope bounds and crash
windows. The integrated decisions above resolve those points without changing
scope. ARQ and the Lead each checked the three supplied identity preimage/digest
pairs using read-only .NET SHA256 operations; all three matched including the
actual NUL byte and full hex preimage. The supplied writing oracle was not run.
This is vector consistency evidence, not original admission or a product gate. Future ownership stays disjoint: ARQ owns new semantic/application files
and the reserved additive P5b reader; DB owns new schema/storage; Lead owns
CLI/logging/harness/CI/docs/Git. QA and REVIEWER must be distinct non-authors and
different from each other. No product authorship has started in this step.

## Alternatives and consequences

Rejected: fabricating evt3:/alt1:/tdl1:; widening P8a/P8b authority; caller DTO
admission; separate journal transactions per field; identity based on rendering,
paths or time; a global verification cache; postpublication first verification;
and increasing time budgets or shrinking ARM64 fixtures to obtain green gates.

Immutable-origin/trusted-directory assumptions remain. Whole-history verification
can legitimately time out as data grows. No hostile-admin authentication, global
three-DB atomicity, worldwide dedup, delivery/exactly-once, physical power-loss
qualification or unconditional cleanup is promised. Capacity, ACLs and native Pi
durability retain existing debt owners/exits. No new debt is invented for excluded
features.

## Revisit conditions

Reconsider ADR-0014 when objective evidence establishes any of the following:

- An adopted P5a/P5b contract or identity changes in a way that affects exact
  revision admission, snapshot/result grammar, evaluator semantics, sequence or
  signal derivation, canonical bytes or compatibility of this consumer.
- A future requirement introduces real delivery, a transport channel or current
  notification authorization beyond this offline synthetic preview.
- Reproducible SQLite or ARM64 incompatibilities prevent the frozen DDL, literal
  catalog equality, consistency, recovery or unchanged resource/deadline gates
  from being satisfied on a required supported environment.
- A demonstrated security or integrity defect invalidates trusted-directory,
  immutable-origin, receipt/admission, verification or transport-isolation
  assumptions relied upon by this design.
- Normative persistence or recovery requirements change, including ownership,
  schema/version compatibility, immutable retention/replay, verification,
  exclusive publication or safe failure/cleanup obligations.

Record the triggering evidence, affected decisions/contracts and ACs, and a
bounded revision proposal before changing the design. Escalate to the
Orchestrator whenever resolution would expand phase scope or alter previously
accepted cross-phase boundaries. These triggers neither authorize implementation
of excluded features nor permit unilateral changes to existing stores or
identities. They reconsider this ADR, not the phase's acceptance or closure.

## Evidence plan and authority to proceed

The API contract maps each WA01..WA20 to tests and published evidence; the storage
contract defines fault/recovery obligations. Preserve failures and prohibit
same-SHA failed-job retries without authorization. Corrective commits later receive
normal fresh CI and renewed affected reviews.

This step prepares exactly four design documents, no product code, databases,
migrations, commits, PR or final-review agents. Phase Lead review of this freeze
precedes any newly authorized implementation step. Only the Orchestrator accepts,
authorizes integration and closes P8c. Archive/roadmap/AGENTS and other documentary
updates outside these four paths remain for a later authorized step.
