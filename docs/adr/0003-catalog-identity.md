# ADR-0003: Explicit catalog identities and printing granularity

Status: adopted for the P1a candidate; phase acceptance belongs to the Orchestrator.
Date: 2026-10-09.
Owners: ARQ / BE / DATA author; independent QA and REVIEWER review the final candidate.

## Context

The same external identifier can occur in multiple language contexts, and the same name can describe unrelated objects. TCGdex variant availability describes possible versions of a card, without identifying an observed printing. CMT needs reproducible offline identities before any persistence phase. Set enumeration does not establish a sellable sealed product.

## Decision

Use four provider-independent entity kinds, each identified by a canonical lowercase UUID v4 allocated once by a curator and persisted in the explicit manifest. Processing never generates, hashes or derives canonical identities from external data. UUID format constrains serialization; the manifest and curated bindings establish the provenance of identity assignment.

- A `set` is an expansion identity with optional ES/EN name localizations. Observing the Spanish and English names can reference one set through two explicit bindings. A translated name alone never establishes equivalence.
- A `card` is a base design within a set, with its exact textual card number. Its logical uniqueness is `(set_id, card_number)` in this first slice. It carries neither language nor finish. Changes in numbering or design require curated identities; name similarity cannot resolve them.
- A `printing` is the commercial identity beneath a card, distinguished by `(card_id, language, variant)`. ES and EN, and normal, holo and reverse are separate printings. Unknown language or finish may be represented in a curated entity but does not authorize automatically accepting an ambiguous observation. Condition, seller, stock, price and grading are outside this identity.
- A `sealed` entity is independent of card/printing, with an optional set relationship, explicit language/null and a minimal product type. Its identity is assigned independently; no provider booster metadata, inferred contents or generated SKU creates it.

The external reference key is exactly `(namespace, kind, external_id, language, variant)`. Every component participates in equality, including null language and unknown variant. Set and sealed references must use unknown variant. Card references bind to printing entities; their base card and set are reached through validated relationships. Multiple references may bind to one identity only through separately recorded curator decisions. Binding reasons are bounded audit material and are never log fields. A contextual external card `(namespace, external_id, language)` cannot bind different variants to different base cards.

Manifest validation rejects duplicate CMT IDs, duplicate base-card/printing identity tuples, duplicate contextual reference keys even when their targets agree, broken or wrongly typed relationships, incompatible target kinds, and language/variant contradictions. Names are never unique keys. The complete manifest is validated before batch processing.

Resolution checks immutable number and set facts against explicit contextual bindings before classifying an unknown finish as a candidate. Thus an ambiguous poisoned record still produces an identity conflict. Unknown finish/language and missing mappings remain explicit candidates; processing never adds entities or bindings. Known context changes without a binding also remain candidates. Explicitly mapped records with contradictory immutable facts are rejected. Repeated observations contribute repeated accepted record counts but result entities are unique. The result includes required card/set parents and sorts entities by UUID; record order follows the input.

The implemented boundaries are `external JSON -> bounded shape validation -> normalized source observations -> validated manifest and resolver -> provider-independent entities`. Domain models import no adapter, source shape, transport, configuration or logging module. Source references and provenance belong to the ingestion boundary, not canonical entities.

Release dates are dates; provider update and capture timestamps are separate optional UTC instants. Missing dates remain null. No first-seen timestamp, temporal delta, database or durable candidate queue is implemented.

## Alternatives considered

Provider IDs, names, URLs, SKUs and hashes of provider IDs would couple identity to a source or merge homonyms. Runtime UUID allocation would break reproducibility. Name matching and availability-to-finish inference would merge identities without evidence. One entity for all language/finish combinations would lose the distinction needed by later observations. A database, ORM, abstract adapter hierarchy or runtime dependency is unnecessary for the bounded offline operation.

## Consequences

The curated manifest is small, explicit and auditable. Missing mappings require later human review; candidate references contain no canonical ID. There is no claim of complete provider coverage, operational source health or commercial catalog completeness. Optional fields and localizations can grow compatibly within the contracts; changes to identity granularity or contextual equivalence require a new contract/ADR. UUIDs and relationships can be persisted later without adopting any schema now.

## Revisit conditions

Revisit base-card uniqueness when authorized evidence demonstrates multiple distinct designs sharing a set/number or language-dependent numbering. Revisit language/product distinctions when actual regional sealed data is licensed. Persistence, concurrent curators, migrations and candidate lifecycle belong to P3a/P4 under their own contracts. Physical Pi validation remains an operational follow-up; P1a ARM64 evidence is explicitly emulated.
