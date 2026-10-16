# Architecture

## P1b pinned repository ingestion and capture

Engineering acquires four exact pinned files once under a shared eight-request
budget. A bounded non-executing structural TypeScript parser extracts only the
approved fields with byte spans. Original source bodies stay transient. The
distribution contains a reviewed minimal package, field ledger and full MIT
notice; runtime and CI use it offline.

`pinned_repository` owns source grammar, namespace, reviewed digest anchor and
translation to generic observations. `persistence.capture` independently
revalidates package and manifest, freezes resolution and scopes, and writes
through SQLite v2. The domain and Discovery import no source model. Curated
UUIDs and exact contextual bindings remain the only identity authority.

See [ADR0006](adr/0006-pinned-capture-storage.md),
[bundle v1](data-contracts/PINNED_REPOSITORY_BUNDLE_V1.md),
[capture v1](data-contracts/CAPTURE_SCOPE_V1.md) and
[storage v2](data-contracts/STORAGE_V2.md). Reads support exact v1/v2 inventories;
migration is explicit, transactional and preceded by a verified exclusive
backup. History and v1 fingerprints remain unchanged, with legacy scope marked
unverified. New initialization uses v2. PERSISTENCE_V1 remains synthetic-only;
Discovery explicitly rejects selected observed or mixed batches.

The reviewed digest proves equivalence to the locally reviewed minimum package,
not independent producer authenticity, current availability, total catalog
coverage or physical product truth. Acquisition/capture/local insertion clocks
remain distinct. The historical sections below describe their original scope.

## P0.5b source qualification — documentation only

[Field/capture proposal](sources/P0_5B_FIELD_USE_CAPTURE_POLICY.md) names the future
boundary `External Source -> Validated Source Model -> Normalized Ingestion ->
CMT Domain`. Validated source model describes existing adapter responsibility;
no new runtime class, source collector, schema or dependency is added. Per-field
rights precede retention, and producer provenance is not rights/authenticity.
P1a curated identity, P3a frozen history/replay and P4a selected-window semantics
remain unchanged. Persistence/Discovery remain synthetic-only. Independent
capture context for empty/multiple producers is a later-contract proposal;
TD-005 is not resolved. Existing ADR-0003–0005 suffice; no new adopted ADR.

## P4a offline temporal discovery

```text
strict request -> one P3a consistent read transaction -> generic snapshots
  -> revalidation -> pure window/reference comparison -> typed result
  -> JSON stdout + allowlisted correlated execution logging
```

`discovery` depends on generic P1a evidence/validators, without SQLite, adapters,
CLI, current manifest or resolver execution. Public constructors are revalidated.
`persistence.sqlite_repository.read_snapshots` reads selected metadata/complete
rows/identity closure in one mode=ro/query_only snapshot. It consumes no query
stdout, creates no missing DB and changes no schema or business data.

[ADR-0005](adr/0005-offline-temporal-discovery.md) and
[DISCOVERY_V1](data-contracts/DISCOVERY_V1.md) define exact contexts, explicit
historical union, bootstrap, bounds, frozen states and deterministic hashes.
Empty capture scope is explicitly caller/producer-attested and labeled
`request_attested_empty`; schema1 cannot prove it. Nonempty batches require every
row to match. Reference novelty implies neither launch/global/product novelty
nor disappearance/source health/delivery. No event tables or migration exist.

## P3a observation persistence

```text
strict local persistence wrapper + read-only manifest
  -> existing P1a adapter/normalized evidence
  -> persistence.input + application validation/UTC capture/resolution binding
  -> immutable PersistenceBatch
  -> SQLite repository (independent validation again)
  -> atomic identity projection + batch + accepted/candidate/rejection snapshots
CLI persist / observations / db operations -> JSON stdout + allowlisted stderr
```

`persistence.application` composes P1a without importing SQLite; P1a domain and
resolver remain unchanged and independent of persistence/adapters. The repository
depends inward on validated values and uses standard-library SQLite. The curated
manifest remains the canonical identity/binding authority. DB entity projections
preserve UUIDs and required parents; snapshots never promote candidates or reassign
old decisions after manifest edits. Storage never consumes P1a stdout as the sole
evidence source because that serialization omits normalized timestamps/metadata.

[ADR-0004](adr/0004-offline-observation-persistence.md) and
[input](data-contracts/PERSISTENCE_V1.md)/[storage](data-contracts/STORAGE_V1.md)
define initial schema1, DELETE/FULL, explicit transaction lifecycle, validated
producer tokens/replay context, safe summaries, bounded read/lock/backup and new
restore destinations. Separate commands make writes explicit; `catalog` remains
read-only. Fixtures are exclusively synthetic. There is no network collector,
market/retail schema, scheduler, promotion workflow, analytic query or server.
The sections below describe their original phase implementations.

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
