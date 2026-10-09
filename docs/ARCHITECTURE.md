# Architecture

## P1a catalog core

```text
local external JSON -> bounded strict JSON -> TCGdex shape validation
  -> generic Observation / RecordError -> explicit manifest resolver
  -> provider-independent Entity / candidate / categorized rejection
CLI -> structured stdout + allowlisted JSON stderr
```

The implemented domain in `catalog.models` contains set, card, printing and
sealed entities with opaque UUIDv4 identities and explicit relationships.
`catalog.ingestion` describes source evidence without making provider references
domain IDs. `catalog.manifest` validates curated identities and contextual
bindings; `catalog.resolver` uses those bindings conservatively without name
matching or mutation. `catalog.adapters.tcgdex` owns provider shapes. No domain
module imports the adapter. Shared validation bounds local untrusted JSON.
CLI orchestrates these components without network, persistence or export files.
See [ADR-0003](adr/0003-catalog-identity.md) and versioned catalog, ingestion and
manifest contracts. The P0 section below remains its historical implementation
description; its version/diagnose/configuration behavior is preserved.

## P0 implementation

P0 is a single installable Python 3.13 application using `src/` layout. `card_market_tracker.cli` owns argument parsing and the one-shot `diagnose` command. `config` loads and validates two local settings. `logging_json` emits allowlisted JSON fields. There are no runtime third-party dependencies, network calls, database, scheduler, server, or published ports.

```text
CLI --> configuration
  |          |
  +--> JSON logging
  +--> local work-directory probe
```

Dependencies point inward: future source adapters must translate untrusted provider data before domain use; provider identifiers cannot become domain identity. The intended boundary is `External Source -> Validation -> Normalized Ingestion -> Domain`. This is an architectural constraint, not an implemented pipeline. Do not add empty module hierarchies to imply features exist. SQLite remains a future initial persistence preference; no business schema is selected in P0.

Configuration is loaded from defaults, an explicitly named env file, then the process environment. The diagnostic verifies the configured directory with a temporary file and removes it automatically. It does not test source health. Failures are categorized as configuration (`2`) or local execution (`1`). Logs contain run correlation and safe event fields. See [logging v1](data-contracts/LOGGING_V1.md).

The container is a one-shot process with non-root UID 10001. CI runs quality/security gates and builds smoke-tested AMD64 and emulated ARM64 images. These checks cannot establish long-running Raspberry Pi behavior. [ADR-0001](adr/0001-modular-application-boundary.md) and [ADR-0002](adr/0002-multiarch-validation.md) record the adopted choices.

Future capabilities are phased in the [roadmap](ROADMAP.md). P1a adopts catalog
identity in ADR-0003. Commercial observation schema, scheduler, healthcheck and
service API remain decisions for their owning phases.
