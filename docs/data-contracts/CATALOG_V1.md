# Catalog domain v1

Status: implemented in the P1a candidate. Producer: validated curated manifest and resolver. Consumer: local CLI result; future consumers require their own phase authorization. Boundary and rationale: [ADR-0003](../adr/0003-catalog-identity.md).

## Entities and nulls

All entities have required `cmt_id` (canonical lowercase UUID v4) and `kind` (`set`, `card`, `printing`, `sealed`). Internal IDs are allocated once by a curator, persisted and reused; no provider identifier, name, hash, SKU or URL defines them. Optional names are ES/EN localizations, represented by immutable `Localization(language, name)` values; absent localization means unknown. Names are bounded nonempty text, not matching keys.

| Field | Meaning and constraints |
| --- | --- |
| `set_id` | Required for card; optional for sealed; forbidden for set/printing. Target must exist and be a set. |
| `card_id` | Required for printing only; target must exist and be a card. |
| `card_number` | Required for card only; nonempty string, maximum 64 characters. `001`, `TG01`, `SVP-001` remain distinct strings. |
| `language` | `es`, `en` or null; printing/sealed only. Null is unknown and is never English. |
| `variant` | `normal`, `holo`, `reverse`, `unknown`; only printing can hold a known variant. Unknown is not normal or a false availability flag. |
| `release_date` | Optional exact ISO calendar date `YYYY-MM-DD`; no fabricated default. |
| `sealed_type` | Required for sealed: `booster_pack`, `box`, `bundle`, `collection`, `unknown`; forbidden for other kinds. |

Base cards are logically unique by `(set_id, card_number)` and printings by `(card_id, language, variant)`. These constraints reject duplicate curated identities rather than silently merging them. Sealed entities are independently assigned and never inferred from booster metadata. Price, images, condition, seller, stock, source update/capture dates and grading are absent from canonical identity.

## Result serialization v1

`BatchResult.to_dict()` produces `{version:1, counts, entities, records}`. Counts are `input`, `accepted`, `candidates`, `rejected`, `entities`. The first four count records; their partition satisfies `input = accepted + candidates + rejected`. Entity count includes unique accepted targets and their required parent closure, so it is not an accepted-record count.

Entities are sorted by UUID and serialize the canonical fields above except localized names, which are intentionally not exported by this minimal CLI. Each source record produces one result in its original order: `index`, `status` (`accepted`, `candidate`, `rejected`), `category` or null, `cmt_id` or null, bounded external `reference` or null, and `provenance` or null. References and provenance are allowed output evidence; arbitrary names, raw input/extras and binding reasons are omitted. Rejected records contain neither external values nor payloads. Accepted results have a CMT ID; candidates have no CMT ID and retain their exact contextual source reference for later review. Input timestamps remain semantically distinct ingestion fields and are not exported as canonical entity fields.

Processing is deterministic and read-only: no manifest mutation, identity generation, DB or network. Identical input and manifest produce equal results. Repeated records retain their counts while entities remain unique. Errors carry only fixed categories; CLI adds separately documented global outcome and exit handling.

## Compatibility

Contract major version is 1, including result serialization. Identity, relation, enum or null-semantics changes are breaking and require a new version. Manifest unknown keys are rejected to prevent accidental contract drift. Compatible provider extras are allowed only at the adapter boundary and discarded after validation. Domain code contains no TCGdex shape or transport dependency.

Executable evidence: `catalog/models.py`, `catalog/manifest.py`, `catalog/resolver.py`, and `tests/test_catalog_core.py` cover stable IDs, homonyms, explicit aliases, localization, three finishes, unknowns, sealed separation, textual numbers, relations, contradictions, duplicate records and deterministic serialization.
