# Agent map

- [P8c contract](docs/phases/P8C_OFFLINE_WATCHLIST_SIGNAL_OUTBOX_CONTRACT.md),
  [brief](docs/phases/P8C_CODEX_ENGINEERING_BRIEF.md),
  [ownership](docs/phases/P8C_OWNERSHIP.md),
  [ADR](docs/adr/0014-offline-watchlist-signal-outbox.md): independent CMTY/schema1
  offline preview outbox; original complete manifest, exact P5a revision and
  single-transaction deeply verified P5b signal bundle. Immutable per-alias/signal
  intentions/replay; local verify differs from original recompute. Exclusive
  three-fold recovery. Only additive read-only P5b helper; prior writers/schemas/
  identities unchanged. P8c OPEN; no product network/transport or merge authority.

- [P5b contract](docs/phases/P5B_WATCHLIST_EVALUATION_JOURNAL_CONTRACT.md),
  [brief](docs/phases/P5B_CODEX_ENGINEERING_BRIEF.md),
  [ownership](docs/phases/P5B_OWNERSHIP.md),
  [freeze](docs/phases/P5B_DESIGN_FREEZE.md),
  [ADR](docs/adr/0013-watchlist-synthetic-journal.md): independent synthetic
  journal CMTQ/schema1; exact original P5a revision/manifest admission,
  immutable snapshots, ancient replay, explicit previous/head CAS and per-rule
  fresh NO_MATCH-to-MATCH signals. Deep local fold verification differs from
  origin recompute. No product network or outbox/delivery bridge; preserve P5a
  and all prior schemas/identities. P5b closed by the supplied P8c opening
  contract's Orchestrator chat decision; historical evidence remains unchanged.

- [P5a brief/ownership](docs/phases/P5A_CODEX_ENGINEERING_BRIEF.md),
  [ADR](docs/adr/0012-watchlist-offline-rules.md),
  [watchlist](docs/data-contracts/WATCHLIST_V1.md),
  [storage](docs/data-contracts/WATCHLIST_STORAGE_V1.md),
  [synthetic evaluation](docs/data-contracts/WATCHLIST_SYNTHETIC_EVALUATION_V1.md):
  separate offline watchlist, complete manifest identity checks, immutable
  revisions/CAS/replay, pure explicit-time synthetic evaluation, no persisted
  samples/results or product network. Preserve prior DBs/schemas/identities.
  P5a closed by the supplied P5b opening contract's Orchestrator chat decision;
  historical evidence remains in its report. TD-001..005 remain OPEN.

- [P8b contract](docs/phases/P8B_TELEGRAM_ALERT_DELIVERY_CONTRACT.md),
  [engineering brief](docs/phases/P8B_CODEX_ENGINEERING_BRIEF.md),
  [ownership/protocol](docs/phases/P8B_IMPLEMENTATION_PLAN.md): manual one-shot
  private Telegram delivery, separate ledger, original-capture recompute,
  claim before send, uncertain never resends, all restored ledgers quarantined.
  No prior DB/schema/identity mutations or merge authorization.

- [P8a contract](docs/phases/P8A_OFFLINE_ALERT_OUTBOX_CONTRACT.md),
  [ownership](docs/phases/P8A_OWNERSHIP.md),
  [evidence](docs/phases/P8A_OFFLINE_ALERT_OUTBOX.md): separate offline outbox v1,
  original-capture verified journal comparisons, destination/event deduplication,
  full evidence per comparison; no transport, source, comparator or prior DB changes.

- [P4c contract](docs/phases/P4C_DISCOVERY_RESULT_JOURNAL_CONTRACT.md),
  [ownership](docs/phases/P4C_OWNERSHIP.md), [evidence](docs/phases/P4C_DISCOVERY_RESULT_JOURNAL.md):
  separate journal v1, verified v3 request/captures only, comparison/event
  occurrences, no capture-schema/comparator/source or delivery changes.

- [P1c contract](docs/phases/P1C_MULTI_REVISION_METADATA_CAPTURE_CONTRACT.md), [ownership](docs/phases/P1C_OWNERSHIP.md), [evidence](docs/phases/P1C_MULTI_REVISION_METADATA_CAPTURE.md): exact R0/R1 registry, separate Discovery v3; preserve R0/v1/v2 and schema2.

- [P4b contract](docs/phases/P4B_SCOPED_CAPTURE_DISCOVERY_CONTRACT.md) and
  [ownership](docs/phases/P4B_OWNERSHIP.md),
  [evidence map](docs/phases/P4B_SCOPED_CAPTURE_DISCOVERY.md): explicit SQLite v2 capture units,
  separate read-only Discovery v2, no new source/schema or v1 guard changes.

- [P1b contract](docs/phases/P1B_PINNED_METADATA_INGESTION_CONTRACT.md),
  [ownership](docs/phases/P1B_OWNERSHIP.md) and
  [P1b report](docs/phases/P1B_PINNED_METADATA_INGESTION.md): pinned minimum
  metadata, separate real admission and explicit schema1→2 migration; no real Discovery.

Read [context.md](context.md) and [P0_FOUNDATION_CONTRACT.md](P0_FOUNDATION_CONTRACT.md) before changing P0. Keep P0 limited to Foundation capabilities. The Orchestrator alone accepts or closes phases.

- [Operating model](docs/ENGINEERING_OPERATING_MODEL.md): ownership, review, and phase decisions.
- [Architecture](docs/ARCHITECTURE.md) and [ADRs](docs/adr/): boundaries and adopted decisions.
- [Coding](docs/CODING_STANDARDS.md), [testing](docs/TESTING_STRATEGY.md), [quality gates](docs/QUALITY_GATES.md): implementation and evidence.
- [Data contracts](docs/data-contracts/) and [threat model](docs/threat-model/THREAT_MODEL.md): interface and security rules.
- [P0 report](docs/phases/P0_FOUNDATION.md): evidence status and review record.
- [P1a contract](docs/phases/P1A_CATALOG_CORE_CONTRACT.md) and
  [P1a report](docs/phases/P1A_CATALOG_CORE.md): offline catalog scope and evidence.
- [P3a contract](docs/phases/P3A_OBSERVATION_PERSISTENCE_CONTRACT.md),
  [ownership](docs/phases/P3A_OWNERSHIP.md) and
  [P3a report](docs/phases/P3A_OBSERVATION_PERSISTENCE.md): synthetic-only SQLite scope and evidence.
- [P4a contract](docs/phases/P4A_OFFLINE_TEMPORAL_DISCOVERY_CONTRACT.md),
  [ownership](docs/phases/P4A_OWNERSHIP.md) and
  [P4a report](docs/phases/P4A_OFFLINE_TEMPORAL_DISCOVERY.md): bounded synthetic offline comparison and evidence.

Do not assert a gate passes without a reproducible result tied to the reviewed commit. Record scope proposals for the Orchestrator instead of adding commercial features to P0.
