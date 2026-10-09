# Explicit identity manifest v1

Status: implemented offline curated registry; no DB or automatic write path. See [ADR-0003](../adr/0003-catalog-identity.md), [catalog v1](CATALOG_V1.md), and [ingestion v1](INGESTION_V1.md).

## JSON shape

The top-level object has exactly required `version`, `entities`, `bindings` keys. Version must be integer 1, never bool. Both arrays may be empty. All manifest keys are strict: unknown keys are rejected rather than treated as implicit future decisions.

Entities have required `cmt_id`, `kind`, and optional `names`, `set_id`, `card_id`, `card_number`, `language`, `variant`, `release_date`, `sealed_type` under catalog v1 constraints. Names are an object containing only `es`/`en` keys with nonempty bounded text. Defaults are empty localizations, null optional relationships/dates/language and unknown finish. Required relationships, card number and sealed type still must be supplied for their entity kinds.

A binding has exactly required `reference`, `cmt_id`, `reason`. Reference has exactly required `namespace`, `kind`, `external_id`, `language`, `variant` keys, with the normalized contextual semantics from ingestion v1. Reason is nonempty text of at most 256 characters and records the curator's explicit equivalence decision; it is never emitted to stdout or logs. The target UUID must exist: set references bind sets, card references bind printings, sealed references bind sealed entities. Printing/sealed language and printing variant must equal the binding context, including null/unknown.

Multiple separately audited references may target one identity. A single exact contextual key may appear only once; duplicates fail even if their targets are equal. Within a card context `(namespace, external_id, language)`, all variant bindings must point to printings of the same base card. Observed ES/EN names do not establish set equivalence without bindings. Unknown context never becomes a wildcard.

## Validation and outcomes

The entire manifest is parsed and validated before processing observations. Duplicate UUIDs fail `duplicate_id`; duplicate `(set_id, card_number)` or `(card_id, language, variant)` fails `duplicate_identity`; missing/wrongly typed relation targets fail `broken_relation`; duplicate references, language/finish contradictions and variant-to-different-card assignments fail `contradictory_binding`. Syntax, types and enums use safe global input/shape/field/version categories. No partial valid manifest is used after a global failure.

Maximum entities: 1,000. Maximum bindings: 2,000. The shared byte/depth/node/string limits from ingestion v1 also apply. UUIDs must be canonical lowercase UUID v4 strings. Identity allocation happens once during curation and is preserved in Git; runtime processing never assigns IDs. A UUID's format alone is not evidence of independence from a provider; curated registry provenance and reviewed bindings establish that practice.

`parse_manifest(object) -> Manifest` yields frozen dataclasses and immutable tuples. `resolve(tuple[Observation | RecordError, ...], Manifest) -> BatchResult` performs conservative matching without modifying the manifest or promoting candidates. Result targets and parent closure are unique and sorted by UUID. Repeating the input preserves IDs and accepted entity counts; record counts deliberately preserve repeated observations.

`Entity` and `Manifest` are typed internal values, not untrusted-input parsers.
The public processing boundary requires a manifest produced by `parse_manifest`.
Constructing arbitrary dataclass instances directly does not confer validation;
the CLI always parses the entire manifest before resolution.

## Compatibility and sample

Major version 1 is explicit. Changes to identity/context/null semantics or relation constraints require a new contract. Renaming a localization or changing an external alias does not inherently change a CMT identity; a curator must update bindings explicitly with an audit reason. Existing decisions are never silently overwritten.

`tests/fixtures/synthetic_manifest.json` contains once-allocated IDs for two homonymous sets, cards numbered `001`, `TG01`, `SVP-001`, ES normal/holo/reverse and EN normal printings, an explicit alternative-namespace alias, and a sealed box related to a set. Every value is synthetic; it is neither a retained provider response nor real commercial SKU evidence. Executable tests cover relation failures, duplicate keys/identities/bindings, context conflicts, variant ambiguity, aliases, repeated runs and bounded hostile input.
