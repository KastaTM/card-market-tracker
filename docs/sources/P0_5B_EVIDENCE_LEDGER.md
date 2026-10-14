# P0.5b research and probe ledger

Run ID: `p05b-20261014-qualification`. Date: 2026-10-14 Europe/Madrid.
Lead coordinates the entire request budget. Documentation browsing is separate
from direct data requests. Browsing tool results may be cached/rendered; they
do not expose trustworthy origin HTTP status, bytes or duration. Such metrics
are `unknown`, never invented. No authenticated provider probes, account, token,
payment, accepted contract, or source connection in CI.

## Documentation research

| Record / UTC consultation | Route / question | Result category and evidence | Status / ms / bytes | Budget / retention |
| --- | --- | --- | --- | --- |
| D01 / 2026-10-14 11:01:37 | TCGdex access, MIT, object fields, paging | `documented`; official LICENSE, FAQ, card/set references, filtering page, reviewed by Lead + INTEGRATIONS | unknown / unknown / unknown | 0; links and summaries only |
| D02 / 2026-10-14, exact per-page UTC unknown | TCGdex artifact-to-REST transform | `documented` code; interfaces and cardUtil/setUtil/compiler/util; deployment correspondence `inferred`, not deployment attestation | unknown / unknown / unknown | 0; source links and minimal semantic summary |
| D03 / 2026-10-14, exact per-page UTC unknown | M1 eBay active EUR/ES rights | Official requirements/license/docs; see dated fiche | unknown / unknown / unknown | 0; no listing values |
| D04 / 2026-10-14, exact per-page UTC unknown | M2 Scrydex currency/history/rights | Official prices/history/best-practices/terms; see dated fiche | unknown / unknown / unknown | 0; no price values |
| D05 / 2026-10-14, exact per-page UTC unknown | R1 GAME legal/material delta | Official legal/conditions; no new product crawl; historical item evidence remains dated 2026-10-07 | unknown / unknown / unknown | 0; no new offer values |
| D06 / 2026-10-14, exact per-page UTC unknown | R2 Awin publisher/feed rights | Official feed guide/API/terms; concrete feed entitlement/coverage unknown | unknown / unknown / unknown | 0; no feed values |

Repository revision metadata via `git ls-remote` (not dataset enumeration):
TCGdex `refs/heads/master=4199850a6af49665db0080fa2bb9ef751750a406`.
This pins source reads; it does not identify the API deployment revision.

SEC supplementary document check2026-10-14 11:20:50UTC: linked Awin ES terms PDF
reported403 Forbidden in the browser; alternate official-document hosts were
inaccessible with unknown status. No denied-endpoint retry/evasion. Indexed terms
are provisional locators, not verified full applicable conditions. eBay call-limit
figures are also provisional indexed locators pending readable primary source.
These documentary requests consume no direct data budget and grant no permission.
SEC-01/SEC-02 wording findings were corrected before candidate commitment.

## Direct-request preflight — written before execution

Access review: the official [FAQ](https://tcgdex.dev/faq) permits public no-key
API use with considerate caching; the [README](https://github.com/tcgdex/cards-database)
licenses the database under [MIT](https://github.com/tcgdex/cards-database/blob/master/LICENSE).
Source files are read from that repository at the pinned commit. The copied
MIT notice accompanies this research in [the notice file](TCGDEX_MIT_NOTICE.txt).
This justifies bounded transient source/metadata inspection. It grants no blanket
third-party price/image/mark rights. All raw bodies and excluded values are
discarded; retain only structure, counts, types and source/REST equality booleans.
No real fixture is published and nothing enters the application or database.

Each request below is a separate serial GET: <=15s total request/read budget,
<=262144 response bytes, no credentials/cookies, redirects disabled, no retries,
no payload URL follow, stop provider on 401/403/429/overrun. The response is never
executed. TypeScript is inspected as text, not imported. API JSON is parsed only
in transient memory. Quota reserves 6/6 TCGdex, 6/12 phase; any attempted data
request consumes its slot, including failures. Other providers reserve zero.

| ID | Exact endpoint / question | Diagnostic allowlist / interpretation |
| --- | --- | --- |
| T01 | `https://raw.githubusercontent.com/tcgdex/cards-database/4199850a6af49665db0080fa2bb9ef751750a406/data/Sword%20%26%20Shield/Darkness%20Ablaze.ts` — source set ES/EN names and facts? | Presence/types of `id,name.en,name.es,releaseDate,cardCount.official`; compare privately to subsequent REST. Missing text match is unknown, not absent data. |
| T02 | `https://raw.githubusercontent.com/tcgdex/cards-database/4199850a6af49665db0080fa2bb9ef751750a406/data/Sword%20%26%20Shield/Darkness%20Ablaze/136.ts` — source card ES/EN names and variants? | Presence/types of `name.en,name.es,variants`; filename `136` only supplies reference context. Exclude effects, art and upstream prices. |
| T03 | `https://api.tcgdex.net/v2/en/sets/swsh3` — localized set shape/mapping? | `id,name,releaseDate,cardCount.total,cardCount.official`, cards count only; source match booleans. Not set completeness, historical release verification or deployed revision proof. |
| T04 | `https://api.tcgdex.net/v2/es/sets/swsh3` — same question, ES? | Same diagnostic fields; differing translation does not create another canonical identity. |
| T05 | `https://api.tcgdex.net/v2/en/cards/swsh3-136` — card number/parent/flags/update shape? | `id,name,localId,set.id,updated`; types/presence of normal/holo/reverse/firstEdition/wPromo/jumbo/preRelease flags, source name match booleans. No printing observation. |
| T06 | `https://api.tcgdex.net/v2/es/cards/swsh3-136` — same question, ES? | Same; source localization correspondence only for this record, not Spanish coverage. |

No list pagination probe is budgeted: documentation establishes supported selectors,
not stable snapshots/completeness. Six source/detail reads cannot qualify full
enumeration or temporal novelty. No second capture or source delta is claimed.

## Execution outcomes

All six attempts executed serially, without redirects/retries. Each returned 200
and category `successful_response`. These are point observations, not health/SLA
or blanket licensing evidence. Consumed **6/12 phase, 6/6 TCGdex**. No further
TCGdex data request is allowed in this phase. M1/M2/R1/R2 each consumed zero.

| ID | Start UTC 2026-10-14 | HTTP / bytes / duration ms | Diagnostic result |
| --- | --- | --- | --- |
| T01 | 11:05:57.689065 | 200 / 536 / 426 | Source set id/name/date/official-count present; both localized names present. |
| T02 | 11:05:58.115510 | 200 / 2028 / 318 | Source card name/variants present; both localized names present; no literal card ID. |
| T03 | 11:05:58.433723 | 200 / 21922 / 144 | EN id/name/date/official exactly match pinned source; total/official are ints, 201 card briefs. |
| T04 | 11:05:58.578090 | 200 / 21966 / 175 | ES same checks match; 201 card briefs. This count is not proof of complete translation. |
| T05 | 11:05:58.752910 | 200 / 2157 / 126 | EN name matches source; ID formula/localId/parent match; updated string; five bool flags, jumbo/preRelease absent. |
| T06 | 11:05:58.878993 | 200 / 2942 / 136 | ES same checks match; same flag types. Different byte sizes do not prove market changes. |

Response payloads/source bodies were not written or printed. A one-off ignored
stdlib diagnostic invocation read text without execution, rejected redirects,
bounded chunk reads and duplicate JSON keys, and emitted only these diagnostics.
It is not a shipped helper/collector. Local diagnostic JSON and invocation are
in ignored `.p4a-evidence/p05b/`; published table permits method review but cannot
reconstruct exact payloads. No comparison of excluded prices/marketplace fields,
no observed finish, no temporal novelty, no paginated list, no new real fixture.
Source/API equality is limited to sampled scalar checks, not deployed-SHA proof.

Failure categories distinguish policy block/access denial, timeout, rate limit,
invalid/oversized payload, absent data, partial response and successful response.
Unreachable never means empty. No failure case was exercised against a provider.
