# Normalized catalog ingestion v1

Status: implemented P1a offline contract. Producer: isolated adapter after bounded external shape validation. Consumer: catalog resolver. This supersedes the catalog portion of preliminary [source ingestion v0](SOURCE_INGESTION_V0.md); market/retail requirements remain future requirements.

## Normalized values

`ExternalReference(namespace, kind, external_id, language, variant)` is an immutable contextual reference. Namespace/ID are nonempty tokens matching `[A-Za-z0-9][A-Za-z0-9_.:-]*`, maximum 128 characters. Kind is `set`, `card` or `sealed`; language is `es`, `en` or null; variant is `normal`, `holo`, `reverse` or `unknown`. Set/sealed references require unknown variant. Full equality includes every field; null never acts as a wildcard.

`Observation(kind, reference, name, set_reference, card_number, release_date, provider_updated_at, captured_at, provenance)` contains validated source evidence. Kind must equal reference kind. Name is required nonempty bounded text; it is never a match key, log field or CLI output field. A card requires a set reference of kind set and a textual card number (maximum 64 characters); card number is forbidden on other kinds. A sealed observation may have an explicit set reference but creates no entity. The adapter only emits set/card observations; synthetic generic sealed observations exercise the independent core.

Provenance is `synthetic`, `documented` or `observed`, required as an explicit keyword in normalized observations and declared explicitly by the offline adapter envelope. There is no inferred provenance default. It is a claim by the local input producer, not a license approval or live-provider health check. Synthetic fixtures are tagged in the fixture provenance ledger; no capture is inferred. Release date is an optional valid `YYYY-MM-DD`; provider-update and capture timestamps are distinct optional UTC ISO instants. Adapter source instants with explicit offsets normalize to UTC while preserving the instant. Missing/null dates remain null; no `first_seen_at` is created.

Source-specific mapping, fields and licensing are in [the adapter policy](../sources/TCGDEX_P1A_FIELDS.md). The external envelope and TCGdex shapes remain in the adapter, not canonical domain models. Availability flags cannot identify a finish. Explicit wrapper variant evidence supplies observed finish when available; absent evidence remains unknown.

## Errors, partial batches and candidates

Adapter output is an ordered tuple of `Observation | RecordError`. A record error has index and a fixed safe category; it never carries payload text. A malformed/incompatible envelope or input bound fails globally. A malformed individual record becomes a rejection and processing continues. The resolver emits indexed accepted/candidate/rejected rows in original order, including duplicates.

Resolver categories include `unknown_variant`, `unknown_language`, `missing_binding` and `identity_conflict`. Immutable set/number contradictions take precedence over ambiguity when explicit contextual mappings provide the facts. Exact bindings authorize acceptance only after facts and relationships agree. Names never create matches, unknown language never selects ES/EN, and candidates are never automatically promoted. An unresolved parent set is a candidate, not a broken canonical relation. Invalid source fields are rejected with `invalid_field`/`invalid_shape`; global manifest failures use the separate manifest categories.

## Bounds and security

`read_json(Path)` reads a regular file up to 1,048,576 bytes, maximum nesting 16, structural nodes 20,000 and any string/key 1,024 characters. Nesting is checked before recursive JSON decoding. Direct Python input receives the same structural validation. Nonfinite values, non-JSON objects, invalid UTF-8, unpaired Unicode surrogates and duplicate keys anywhere in JSON are rejected. File paths are read locally; no referenced URL is fetched. Files are never written by processing. Record limit is 1,000. Extra provider fields remain subject to these global complexity bounds, then are discarded.

Errors contain stable categories only and never echo file content, names, URLs, paths or arbitrary exception messages. Fixed global categories: `input_io`, `input_limit`, `invalid_json`, `duplicate_key`, `unsupported_version`, `invalid_shape`, `invalid_field`; manifest categories are documented separately. Explicit null and empty valid batch remain different from a parse failure. CLI exit codes, logging and stdout are documented by the CLI integration.

## Compatibility and evidence

Major version 1 is mandatory and integer booleans are not valid version numbers. The adapter tolerates compatible provider field additions, validates known allowed field types, and never exports ignored extras. Required-field removal or incompatible known-field types produce explicit rejections. Changes to context, enum, null or field semantics require a new major contract. Unit and adapter contract tests execute with synthetic inputs and no Internet.
