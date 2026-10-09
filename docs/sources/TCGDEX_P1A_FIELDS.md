# TCGdex P1a: minimum offline field policy

Review date: 2026-10-09 (Europe/Madrid). Roles: INTEGRATIONS author and SEC read review.
This policy covers the offline adapter in `catalog/adapters/tcgdex.py`; no network
collector is implemented. New live TCGdex API requests in P1a: **0 of 5**.

## Sources and evidentiary status

Official sources read on the review date:

- [Card reference](https://tcgdex.dev/reference/card) and
  [REST card example](https://tcgdex.dev/rest/card): API metadata shape.
- [Set reference](https://tcgdex.dev/reference/set) and
  [REST set example](https://tcgdex.dev/rest/set): localized set shape.
- [Database interfaces](https://github.com/tcgdex/cards-database/blob/master/interfaces.d.ts):
  corresponding database field declarations; this is the source repository shape,
  which uses language maps in places where the localized REST shape uses strings.
- [Database license](https://github.com/tcgdex/cards-database/blob/master/LICENSE):
  MIT; copyright (c) 2021 TCGdex. Reuse of covered material requires preservation
  of the copyright and permission notice. The repository license does not establish
  ownership or permission for every third party item delivered by an API.
- [FAQ](https://tcgdex.dev/faq): coverage and matching caveats, languages and variant flags.
- [Assets](https://tcgdex.dev/assets) and
  [market integration](https://tcgdex.dev/markets-prices): separate asset and market fields.

**Documented:** the field shapes and database license above. **Synthetic:** every
versioned P1a fixture, reference, name, date, and variant choice. **Observed in P1a:**
no real API records. The P0.5 sanitized ledger is historical evidence, not a JSON
fixture; no response has been reconstructed from it. Tests demonstrate the modeled
shape and implementation behavior, not real ES/EN coverage or provider completeness.

## Field allowlist and mapping

These are the only provider fields read. Required means required by this minimum
adapter contract, which is deliberately smaller than a complete API response.

| Input | Ingestion destination / meaning | Validation and unknown policy | Database correspondence / retention decision |
| --- | --- | --- | --- |
| set/card `id` | `reference.external_id`, namespace `tcgdex`, explicit kind and wrapper language | Required nonempty token, at most 128 characters; never CMT identity | Database `Set.id`; card IDs supplied by REST record. Synthetic only retained here; real IDs need dated metadata provenance and license notice. |
| set/card `name` | Metadata `name` | Required bounded nonempty string; no name matching | Database localized `Set.name`/`Card.name`; do not infer rights to trademarks from MIT. Synthetic short labels only in fixtures. |
| card `localId` | Text `card_number` | Required string, at most 64 characters; preserve leading zeros/prefixes | REST `localId`; model deliberately rejects numeric form because conversion can lose numbering semantics. Synthetic text retained. |
| card `set.id` | `set_reference`, same namespace and language, variant unknown | Required nested object and token ID; manifest resolves relation | REST `set` and database `Card.set`/`Set.id`. Synthetic only retained. Nested names/assets/counts are ignored. |
| set `releaseDate` | Optional `release_date` | Missing/null remains unknown; supplied value must be an actual `YYYY-MM-DD` date | Database `Set.releaseDate` plus REST localized string. Synthetic dates retained. Never capture/first-seen date. |
| card `updated` | Optional `provider_updated_at` | Missing/null remains unknown; supplied value must be an ISO timestamp with timezone; normalize to UTC Z | REST documented provider metadata timestamp. Excludes pricing freshness. Synthetic timestamps retained. Never capture/first-seen date. |
| card `variants.normal`, `.holo`, `.reverse`, `.firstEdition`, `.wPromo`, `.jumbo`, `.preRelease` | Validated availability evidence only; not exported | Missing object/flag remains unknown; supplied object flags must be booleans. Null flags and incompatible object types rejected | REST bool flags and database `variants` declarations. No inference of a single observed printing; wrapper variant is separate curated input. No real flags retained. |

Envelope `version`, `provenance`, `records`, optional actual `captured_at`, record `kind`, `language`, and optional
`variant` are **CMT offline wrapper fields**, not provider API fields. Language may
be `es`, `en`, or null and is supplied explicitly by the caller's documented
context, never inferred from a name. `variant` may identify a synthetic/curated
observation separately; omission/null is unknown. Provider flags alone, even one
true flag, do not create that observation. Provenance must be explicitly declared;
the adapter cannot attest that an arbitrary caller's assertion is truthful.

All other fields are ignored after bounded structural validation, including
`image`, `logo`, `symbol`, `pricing`, `description`, attacks/effects, `boosters`,
marketplace IDs, and `variants_detailed`. They are neither fetched nor copied to
normalized ingestion, stdout results, logs, fixtures, or export. Test-only sentinel
values prove removal. Booster metadata never creates a sealed SKU. No rights to
images, brands, long text, or third party prices are inferred from the database MIT
license. No current source approval for real-data persistence or redistribution is
claimed by this implementation.

## Compatibility and security

Envelope major version 1 is mandatory. Unknown wrapper keys are rejected to catch
mistakes; extra provider keys are tolerated and discarded. Missing required fields,
wrong types, required nulls, or invalid dates reject that record with a stable
category; no raw values or provider exception messages appear in errors. Mixed
batches retain errors alongside valid records rather than hide rejected records.
The current database interfaces also permit an array of detailed variants while
the REST references show the boolean object: this adapter pins the minimum boolean
object form. An array in `variants` is an explicit incompatible record, not a silent
interpretation. A separate `variants_detailed` extra is ignored.

The shared JSON reader rejects duplicate keys and malformed/nonfinite JSON before
translation. In-memory objects are also structurally bounded. Limits are inherited
from the ingestion contract: at most 1,000 records, depth 16, 20,000 nodes, 1 MiB
UTF-8 file input, and scalar text at most 1,024 characters (names 256, IDs 128, card numbers 64). The adapter imports only the standard
library and inward ingestion/validation modules. It has no network calls, URL
fetches, logging, persistence, arbitrary file output, or dynamic execution.

## Storage, attribution and pending real use

P1a stores authored synthetic fixtures under project version control. It performs
transient local processing and emits allowlisted normalized values; it neither
caches provider responses nor creates a historical database. Documentation links
TCGdex as the modeled source shape, not as the origin of invented fixture values.

Before any future real retained sample, SEC must confirm each retained API field's
correspondence to licensed material, retain the applicable complete MIT copyright
and permission notice with copied material, document source/capture and scope, and
confirm any independent restrictions. Images/marks/prices/text remain excluded.
The unresolved rights and coverage of real commercial data are explicit limits;
P2, sealed retail and Discovery dependencies remain blocked as recorded in P0.5.
