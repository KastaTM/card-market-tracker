# Data contract conventions

Store contracts here as `NAME_VN.md`, where `N` is an integer major version. Describe producer, consumer, fields, types, semantics, errors, security/redaction, examples, and compatibility. A backward-compatible addition needs a documented optional field and tests. Removing or changing a required field, type, or meaning requires a new major version and a migration plan. Pin consumers to an explicit version.

The only implemented P0 data contract is [logging v1](LOGGING_V1.md). The future ingestion boundary is `External Source -> Validation -> Normalized Ingestion -> Domain`. Provider-specific contracts are deferred until source feasibility and adapter phases; no fictitious provider payloads are published.

Synthetic fixtures must be identified as synthetic. Future real fixtures must be minimal, sanitized, permitted to retain, and accompanied by source/provenance and date. See the [testing strategy](../TESTING_STRATEGY.md).
