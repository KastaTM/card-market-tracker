# TCGdex — P0.5b field qualification

Reviewed 2026-10-14 Europe/Madrid by Lead, INTEGRATIONS/DATA and SEC research.
Verdict: **CONDITIONAL** for localized live REST catalog metadata. Six bounded
reads establish sampled correspondence; they do not identify the deployed server
revision or license every enrichment. No production source is qualified by an
average of positive dimensions. The repository metadata route has a narrower
MIT permission basis, with coverage/transform qualification still bounded.

## Primary evidence and revisions

The [repository README, Licenses](https://github.com/tcgdex/cards-database#licenses)
licenses the database under [MIT](https://github.com/tcgdex/cards-database/blob/master/LICENSE).
Covered copies require the copyright and permission notice; the
[complete notice](TCGDEX_MIT_NOTICE.txt) accompanies this research. No fixed
retention period/deletion schedule is specified there for covered copies. The
grant applies to material the licensor can license; it grants no separate
Pokémon trademark, artwork or upstream market-data rights.

`git ls-remote` pinned repository master to
`4199850a6af49665db0080fa2bb9ef751750a406`. Direct text reads T01/T02 in the
[ledger](P0_5B_EVIDENCE_LEDGER.md) cover exactly these artifacts:

- [Set source](https://github.com/tcgdex/cards-database/blob/4199850a6af49665db0080fa2bb9ef751750a406/data/Sword%20%26%20Shield/Darkness%20Ablaze.ts).
- [Card source](https://github.com/tcgdex/cards-database/blob/4199850a6af49665db0080fa2bb9ef751750a406/data/Sword%20%26%20Shield/Darkness%20Ablaze/136.ts).
- [Pinned card compiler](https://github.com/tcgdex/cards-database/blob/4199850a6af49665db0080fa2bb9ef751750a406/server/compiler/utils/cardUtil.ts),
  `cardToCardSingle`/`getCards`, rendered as public code documentation.

[interfaces.d.ts](https://github.com/tcgdex/cards-database/blob/master/interfaces.d.ts),
[API declarations](https://github.com/tcgdex/cards-database/blob/master/meta/definitions/api.d.ts),
[setUtil.ts](https://github.com/tcgdex/cards-database/blob/master/server/compiler/utils/setUtil.ts)
and [util.ts](https://github.com/tcgdex/cards-database/blob/master/server/compiler/utils/util.ts)
were readable at mutable master. Their pinned pages did not render reliably.
Their findings are documented at consultation time, **not** asserted to be
immutable pinned-code evidence. Neither repository head nor sample equality
proves the API's deployed SHA. Public docs are also mutable.

## Field-to-artifact and ingestion matrix

Each use below means short catalog evidence for contextual matching/candidate
review, not market data or observed inventory. Rights basis is repository MIT
for identified source material, conditional for a general REST copy. Preserve
artifact/revision, route language, capture, transformation and notice. Evidence
classes remain separate: `documented` source/type/code claim; `observed` sampled
diagnostic; `inferred` deployment/general applicability; `unknown` coverage.

| Exact field | Source → localized response | Evidence / semantic limit | INGESTION_V1 destination / rights decision |
| --- | --- | --- | --- |
| Set `id` | `Set.id` in pinned set file → REST `id` | documented + observed equal ES/EN | `reference.external_id`; MIT source copy supported, general REST retention conditional |
| Set/card `name` | Source partial language map → localized string via `resolveText` | observed ES/EN equal for two files; missing translation policy below | Required bounded name; never identity. Short source metadata only, with notice; no branding grant |
| Card `id` | Compiler `${set.id}-${localId}`; no literal ID in sampled card file | documented pinned transform + observed formula equality | External reference only; derived from licensed code/source; no immutable-ID warranty |
| Card `localId` | Card filename stem → string | observed string matches stem; REST prose permits string or number | Text card number; current adapter deliberately rejects numeric values, preserving prefixes/zeros |
| Card `set.id` | `Card.set` reference → brief projection | documented relationship; observed parent equals sampled source set ID | Required contextual set reference; no name-based relation |
| Set `releaseDate` | Source scalar or localized map → string | sampled scalar equality; map fallback discussed below | Optional calendar `release_date`; regional applicability unknown unless explicit |
| `cardCount.official` | Source set count → REST official | observed equal ES/EN; int | Diagnostic count only; ignored by existing ingestion. Conditional retained research metric with source notice |
| `cardCount.total` | `Math.max(official, localized cards.length)` in inspected set compiler | documented derivation; int observed, not independent completeness proof | No v1 destination; source-derived diagnostic, general REST retention conditional |
| Card `updated` | Git file timestamp helper; fallback current time if cache misses | documented compiler delegation/helper, string observed; exact live derivation unknown | Optional `provider_updated_at` only after zoned-date validation; metadata claim excluding pricing, never capture/freshness proof |
| `variants.normal/holo/reverse/firstEdition/wPromo` | Object defaults or detailed-array projection → five booleans | documented pinned code; bool type observed. Source defaults can fill omitted values | Availability evidence, validated then discarded; no observed finish or printing allocation |
| `variants.jumbo/preRelease` | Optional source-interface properties | No projection in inspected REST branch; absent in both sampled responses | Excluded from confirmed REST scope pending evidence. Existing adapter support is unchanged |

The [Card reference](https://tcgdex.dev/reference/card), Common Properties and
Variants, distinguishes local number, metadata update and availability. The
[Set reference](https://tcgdex.dev/reference/set) and
[SetBrief](https://tcgdex.dev/reference/set-brief) describe full/brief shapes;
a brief is not enough to supply every optional full-set field.

Allowlist for further qualification: set `id,name,releaseDate,cardCount.official,
cardCount.total`; card `id,name,localId,set.id,updated` and the five flags above.
This is a research allowlist with conditional REST retention, not a permission
to persist all fields or a change to adapter/INGESTION_V1.
Default exclusions: images/logos/symbols/graphics, artwork, descriptions/effects,
prices, marketplace IDs, boosters and external extras. `variants_detailed` is
excluded and never establishes an observed printing. No raw real fixture saved.

## Missing fields, identity and coverage

[FAQ](https://tcgdex.dev/faq), Variants & Card Data / General API Questions,
documents community corrections, language support, free no-key access and
considerate caching without a published hard quota. A true variant flag is a
provider claim that a finish exists. It does not identify a captured specimen.
Source/compiler behavior is separate from independent real-world verification.

`Languages` is partial. The inspected compiler omits cards lacking the exact
requested-language name and sets lacking that language; `resolveText` can use a
matching language prefix. A missing translation is neither a deleted card nor
permission to label EN as ES. Names/IDs/local numbers required by the current
adapter must be bounded nonempty valid strings; invalid required evidence rejects
the record. Missing optional date/update/flags remains unknown. Unknown finish
or language stays a candidate under existing resolution rules.

Inspected set-date projection selects requested-language date, then the first
available map value. A returned date therefore need not be Spain's release date.
Metadata `updated` can use Git history or a compile-time fallback; its exact
provenance remains unknown in the deployed API. It never dates a price/sale.

Source correction/renaming/filename changes can change external identifiers.
No permanent-ID guarantee was found. CMT UUIDs remain curator-assigned with
explicit [MANIFEST_V1](../data-contracts/MANIFEST_V1.md) bindings; shared ES/EN
names or matching provider IDs do not automatically prove canonical equivalence.

## Enumeration and minimum repeatable scope

[Searching Sets](https://tcgdex.dev/rest/sets) documents enumeration, and
[Filtering, Sorting & Pagination](https://tcgdex.dev/rest/filtering-sorting-pagination)
documents optional page/items-per-page and sort controls; default order is
releaseDate, localId, id ascending. For a later bounded capture use explicit
ID ordering, page and at most10 items, with selector/capture interval recorded.
No documented atomic snapshot, cursor continuity, immutable ordering or tombstone
guarantee was established. Concurrent edits, translation gaps, filters and page
shifts prevent inferring removal or launch from absence/order. No P0.5b list
request or temporal comparison was made; historical P0.5's two-item list stays
historical evidence. Counts cannot prove complete enumeration.

The repeatable minimum demonstrated here is two pinned files + the corresponding
single known set/card in ES/EN: six GETs, no pagination or sustained polling.
Sampled source/name/date/count comparisons matched; card ID/number/parent formula
matched. Only type/presence of flags/update was checked, not actual finish or
timestamp validity. Raw bodies were discarded, so reviewers can reproduce the
protocol prospectively only under a new authorized request budget; the recorded
diagnostics cannot reconstruct them. Do not spend a seventh TCGdex request.

## Rights by action and decision dimensions

These decisions apply to this metadata scope only. Future CMT storage also needs
Orchestrator authorization; today's persistence/Discovery accept synthetic only.
Private display, raw redistribution and commercial exploitation are distinct
uses. MIT supports covered repository copies, with notice, but external API
enrichments require their own rights. No fixed deletion period was evidenced for
MIT-covered material; conditional REST retention remains unresolved.

| Action | Decision | Resolution / limit |
| --- | --- | --- |
| Consult transiently | YES | Public considerate bounded requests; proved for six point reads only |
| Save minimal real sample | CONDITIONAL | Exact field/source coverage and independent restrictions reviewed; attach complete notice/provenance. No sample retained here |
| Store in future CMT | CONDITIONAL | Future authorized contract; field rights, capture/coverage validation; current runtime rejects observed persistence |
| Publish fixture/documentation with real values | CONDITIONAL | Identified covered fields and notice; no excluded IP. This candidate publishes diagnostics only |
| Compare/derive/history | CONDITIONAL | Covered metadata lineage and future authorization; reference/catalog claims only |

| Dimension | Result |
| --- | --- |
| ACCESS | Documented public no-key; six successful point reads observed |
| RETENTION | Identified MIT source permission; general REST/deployed transform/upstream rights remain conditional |
| SEMANTICS | Narrow catalog mapping viable; availability, fallback timestamps/dates and external-ID changes limit interpretation |
| COVERAGE | One set/card per language observed; ES/EN corpus completeness and regional releases unknown |
| OPERATIONAL_LIMITS | Considerate caching documented; no SLA/snapshot guarantee or sustained-health evidence |

**CONDITIONAL** remains the route verdict. Resolution: pin/review the remaining
compiler/license lineage, establish live-to-source/field policy and coverage for
the exact future use, then obtain an Orchestrator contract. A positive narrow
repository grant does not unblock live REST ingestion, P2 or retail Discovery.
