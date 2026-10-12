# Agent map

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

Do not assert a gate passes without a reproducible result tied to the reviewed commit. Record scope proposals for the Orchestrator instead of adding commercial features to P0.
