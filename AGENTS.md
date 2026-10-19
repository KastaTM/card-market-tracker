# Agent map

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
