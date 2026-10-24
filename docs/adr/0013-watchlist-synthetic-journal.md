# ADR-0013 — Independent synthetic watchlist evaluation journal

**Status:** PROPOSED (P5b implementation target; not Orchestrator acceptance).\
**Date:** 2026-10-23.\
**Scope:** P5b only; no live market event, destination or delivery authorization.

## Context

P5a stores immutable curated preference revisions but deliberately persists no
synthetic observations or evaluation results. Repeating explicit offline
simulations needs a durable, explainable journal, episode-level deduplication,
strict sequence chronology, per-rule transition semantics and integrity checks.
P5a's evaluator, watchlist store, P8 outboxes and Discovery stores already have
accepted, incompatible ownership and retention boundaries. SQLite is the MVP
storage target, including ARM64/Raspberry Pi. Correlated writes to distinct
SQLite databases have no guaranteed distributed atomicity.

## Decision

1. Own an independent SQLite `card-market-tracker.watchlist-journal`,
   `application_id=0x434D5451` (**CMTQ**), `user_version=1`, immutable evaluation
   and signal records and an atomic sequence head. No new table in P5a.
2. Require explicit complete MANIFEST_V1, exact watch_id/revision and typed
   synthetic current/optional previous/as_of. Reparse using P5a's public
   validation/application boundaries; never accept caller-provided verdicts,
   hashes, snapshot structs or an asserted `verified` flag as authority.
3. Freeze only P5a's complete normalized revision entry (including parent
   closure), current/previous normalized P5a sample shapes, normalized `as_of`,
   policy/contract versions and **recomputed** full P5a result. No unneeded
   manifest, aliases, names, arbitrary extras or personally identifying data.
   Retention of synthetic samples is **exclusive to this new journal**.
4. Define canonical bytes as UTF-8 of `json.dumps(value, sort_keys=True,
   ensure_ascii=True, separators=(',', ':'), allow_nan=False)`. Each identity is
   a lowercase hex SHA-256 of UTF-8 domain-separator ASCII bytes, then a single
   byte 0x00, then canonical JSON bytes. Versioned domains and preimage fields
   are frozen in the contracts. Sequence prefix `wjs1_`, evaluation `wje1_`,
   signal `wsig1_`. These are local deduplication/equality keys **not** source
   attestation or file authentication.
5. A sequence key commits `(watch_id, revision, policy_version, series_key)`.
   Its immutable entry snapshot commits target/variant/parent closure. A change
   in that snapshot for the same watch revision is a conflict; a different
   revision, policy or series starts an independent sequence.
6. Evaluation identity commits complete normalized entry, samples and as_of,
   sequence ID and policy version. An evaluation may be recorded once per current
   sample_id in the sequence. Replay of *exact* semantic content is stable,
   even after newer rows; changed content/as_of under the same sample_id fails.
7. The first sequence observation is a signal-free baseline, even if MATCH.
   On a subsequent append, emit a `WATCHLIST_RULE_ENTERED_MATCH` signal only for
   an individual rule whose immediate predecessor was NO_MATCH and whose new
   verdict is MATCH, with current and prior observed_at fresh against new
   as_of (inclusive P5a max_age). Neither OR aggregate nor MATCH persistence
   creates a new signal; unknown, skipped, indeterminate and stale history
   interrupt continuity. The signal ID binds sequence, rule, predecessor/new
   evaluation IDs, mode and semantic event kind.
8. Use `BEGIN IMMEDIATE` transaction for concurrency; check persisted head
   inside transaction, enforce strict `observed_at` increase and nondecreasing
   `as_of`, unique sample IDs, and supplied previous equal to the preceding
   stored current. Insert evaluation, exact zero-or-more signals and advance head
   atomically; rollback all on every conflict. Do not retry by silently choosing
   a different successor. Never do implicit latest or synthesize previous.
9. Verify local by checking exact schema inventory, version, FK/integrity,
   normalized identities, re-evaluation of **every** snapshot via P5a's pure
   evaluator, chronology, per-rule fold, exact signal set and current heads.
   Recompute separately against a *selected* record's original P5a revision
   and complete manifest; an unavailable/mismatched origin is a failure, not an
   empty or successful result. Neither operation writes data.
10. Explicit CLI with bounded parsing/pagination/deadlines, structured redacted
    completion logs, read-only verification and exclusive verified backup/restore
    follows existing path/inode/sidecar safety. No product network, daemon,
    sourcing, Telegram, outbox or exactly-once delivery claim.

## Alternatives considered

- **Add tables to P5a watchlist:** rejected; would relax its no-sample retention
  guarantee and change accepted schema/ownership.
- **Reuse Discovery journal or P8 outbox:** rejected; incompatible input trust
  authority, semantics and contract versioning.
- **Stateless evaluation only:** rejected; cannot reconstruct sequence, replay or
  explain sustained MATCH vs a later episode.
- **Implicit time-series latest detection:** rejected; invents ordering and risks
  spurious transition events from non-selected history.
- **External distributed service/queue:** rejected as unnecessary at MVP scale.

## Consequences

- Synthetic local operator evidence is durable and sensitive; restrict filesystem
  permissions, saved CLI output and backup access. The origin Watchlist cannot be
  atomically frozen with the journal transaction; immutability of a verified
  revision is an explicit operational assumption.
- Exact replay is deterministic but a privileged administrator can coherently
  rewrite local data. No cryptographic source authenticity, global exactly-once,
  network availability or unobserved intermediate-event guarantee exists.
- More storage/verification work and a new recovery flow are introduced; the
  existing P5a, Discovery, outbox and Telegram contracts remain unchanged.
- Disk-full, lock, crash or power-loss tests must prove rollback/recovery where
  simulation is feasible; ARM64/QEMU does not certify real Pi hardware.

## Revisit conditions

A phase explicitly authorizes commercial observations, external provenance,
real-time source monitoring, cross-store coupling, signature-based authenticity,
retention policy/migrations, scalable pagination or a verified delivery bridge.
Such changes require new ADR/contract versions and Orchestrator scope approval.
