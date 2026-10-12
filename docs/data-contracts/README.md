# Data contract conventions

P3a adds [persistible synthetic input v1](PERSISTENCE_V1.md) and
[SQLite storage/read v1](STORAGE_V1.md), plus an additive allowlisted logging
extension. Required capture/synthetic-only retention apply at the new write
boundary; P1a's optional capture and read-only catalog contracts are unchanged.

P1a implements [catalog v1](CATALOG_V1.md), [ingestion v1](INGESTION_V1.md)
and [manifest v1](MANIFEST_V1.md), alongside the additive logging v1 extension.
Source ingestion v0 remains historical preliminary requirements for later
market/retail phases; it is not the P1a runtime contract.

Store contracts here as `NAME_VN.md`, where `N` is an integer major version. Describe producer, consumer, fields, types, semantics, errors, security/redaction, examples, and compatibility. A backward-compatible addition needs a documented optional field and tests. Removing or changing a required field, type, or meaning requires a new major version and a migration plan. Pin consumers to an explicit version.

The only implemented P0 data contract is [logging v1](LOGGING_V1.md). The future ingestion boundary is `External Source -> Validation -> Normalized Ingestion -> Domain`. Provider-specific contracts are deferred until source feasibility and adapter phases; no fictitious provider payloads are published.

Synthetic fixtures must be identified as synthetic. Future real fixtures must be minimal, sanitized, permitted to retain, and accompanied by source/provenance and date. See the [testing strategy](../TESTING_STRATEGY.md).
