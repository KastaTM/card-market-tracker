# PHASE COMPLETION REPORT — P0.5 Source Feasibility

**Proposed status:** evidence-gathering complete with an explicit `AC-F05 FAIL` and unresolved source-access decisions; candidate for Phase Lead review, **not** phase acceptance or closure. **Contract:** P0.5 Source Feasibility v1 in the 2026-10-07 Engineering Brief. **Date:** 2026-10-07, Europe/Madrid. **Repository:** `KastaTM/card-market-tracker`, branch `docs/p0-5-source-feasibility`, base `main` at `5175d5b09e8d412e11b2ddf4c24bff41df133843`. PR/head and hosted CI are tracked in the external delivery record after publication; a document cannot attest its own future commit/run. No merge is requested from the Engineering Lead.

## Baseline, ownership and method

The Engineering Brief relays the Orchestrator's 2026-10-07 P0 `ACCEPTED` and `PHASE CLOSED` decision. The Engineering Lead verified clean `main == origin/main` at the baseline, expected remote, [PR #2](https://github.com/KastaTM/card-market-tracker/pull/2) merge `5175d5b` and [main push CI 37649030624](https://github.com/KastaTM/card-market-tracker/actions/runs/37649030624). The later Orchestrator decision was recorded first in the [P0 history](P0_FOUNDATION.md) and [roadmap](../ROADMAP.md); it is not a decision made by this phase team. No pre-existing local edits were overwritten.

**Engineering Lead:** checkout, phase boundary, integration, matrix/selection, preliminary contract, risk/threat/roadmap, Git and gates. **Catalog specialist:** TCGdex, legacy Pokémon TCG API and Scrydex fiches, including bounded TCGdex probe. **Market specialist:** Cardmarket and eBay fiches. **Retail specialist:** GAME, Fnac and El Corte Inglés fiches. These specialists edited disjoint files. Independent QA and final REVIEWER evidence must be tied to the published candidate; they are not represented by the author's own review. **MODEL PROFILE USED:** this environment does not expose a reliable model/reasoning-level identifier for the current agents; the brief's model recommendations are not recorded as actual use.

The team read the repository instructions, context, P0 contract, operating model, architecture, roadmap, quality gates, testing strategy, risk register, debt, threat model, ADRs, data contracts and P0 report before work. It examined eight independent providers against official pages dated 2026-10-07. Each [fiche](../sources/SOURCE_MATRIX.md) separates provider documentation, bounded observation and inference; records access, cost/limits, rights, geography/language, singles/sealed, IDs/variants, price/stock/date semantics, pagination/freshness and uncertainty. Direct probes were capped at five per provider after conditions review. No account, plan, token, production adapter, database, scheduler or runtime dependency was added.

## Results, probes and selection

| Provider | Decision | Direct requests | Main evidence and limitation |
| --- | --- | ---: | --- |
| [TCGdex](../sources/TCGDEX.md) | `VERIFIED` only for bounded ES/EN singles/set catalog access; EUR aggregate `CONDITIONAL` | 5/5 | Four set/card GETs and one two-item paginated GET returned 200 on 2026-10-07 16:59–17:00 UTC; full endpoint, status, size and fields in fiche. No sealed retail SKU, completeness, sustained health or third-party price rights proved. |
| [Pokémon TCG API](../sources/POKEMON_TCG_API.md) | New integration `REJECTED` | 0/5 | Official retirement/new-signup closure; existing-key migration only conditional. |
| [Scrydex](../sources/SCRYDEX.md) | Singles/sealed catalog and sold-listing endpoints `CONDITIONAL`; EUR price primary `REJECTED` now | 0/5 | Sealed types and individual sold listings are documented, with an eBay/USD example; account/plan, coverage and license unresolved, EUR prices described as future. |
| [Cardmarket](../sources/CARDMARKET.md) | Recurring CMT feed `REJECTED` | 0/5 | New API applications closed and terms incompatible with planned recurring collection absent written agreement. |
| [eBay Browse](../sources/EBAY_BROWSE.md) | Active-listing discovery `CONDITIONAL`; sold/history not qualified | 0/5 | Production approval/license required; active asks only; ES marketplace documented, supply/storage unverified. |
| [GAME España](../sources/GAME_ES.md) | Retail `CONDITIONAL` | 0/5 | Manual sealed SKU, EUR and coming-soon evidence; monitoring/retention grant absent. |
| [Fnac España](../sources/FNAC_ES.md) | Retail `CONDITIONAL` | 0/5 | Manual sealed evidence; own and third-party offers differ; express commercial permission needed. |
| [El Corte Inglés](../sources/EL_CORTE_INGLES.md) | Retail `CONDITIONAL` | 0/5 | Manual sealed/assorted SKU evidence; applicable main-store terms unreadable, price/stock unverified. |

The [matrix](../sources/SOURCE_MATRIX.md) records all dimensions and the [selection](../sources/SOURCE_SELECTION.md) gives primary/alternative/gap by phase. TCGdex is the provisional P1a singles/set seed, subject to coverage, variants and field rights. Scrydex documents sealed products and sold listings, but no access, Spanish/EUR coverage or use rights were verified. No qualified primary EUR market-history feed exists for P2. No permitted retail probe or authorized P6a adapter exists. GAME is a first consent candidate, not an approved primary. TCGdex can surface new sets/cards for P4 but not sealed retail SKUs; Scrydex sealed catalog, eBay active listings or an approved affiliate feed are conditional leads with distinct semantics. P6a/P4 retail discovery and P2 pricing require Orchestrator decisions on source access, budget/permissions and possible roadmap effects. No unilateral scope change is made.

**Semantics:** singles and sealed are kept separate. A listing ask, completed sale, provider aggregate and MSRP are different facts. Scrydex's documented sold-listing example has USD/eBay provenance; it is neither a verified EUR sale feed nor an independent eBay market source. `EBAY_ES`, EUR or a Spanish page does not prove delivery, condition, language or representativeness. Release date and listing creation are not CMT first seen. Unknown products remain candidates for later review; source IDs/names never become canonical identity. The five TCGdex responses are evidence of access at one moment, not `HEALTHY` status or rights to historical prices. Only the sanitized response ledger remains; no payload was retained, so independent reviewers can assess method and plausibility but cannot reconstruct exact returned content without new requests. Public-page research is not counted as a direct retail/API probe. No cookies, secrets or personal data were retained.

## Architecture, contracts, security and operations

The [preliminary source-ingestion requirements](../data-contracts/SOURCE_INGESTION_V0.md) define future `External Source → Validation → Normalized Ingestion → Domain` fields, nulls, decimal/currency/price/stock semantics, provenance, partial responses and errors. They are proposed requirements, not implemented models or DB migrations. **DB changes: none.** Existing ADRs remain adopted; P0.5 adopts no new structural decision that warrants an ADR. The [risk register](../RISK_REGISTER.md) and [threat model](../threat-model/THREAT_MODEL.md) now address source dependency, licensing/retention, poisoning, variants, redirects/SSRF, excess responses, budgets, rate limits and secrets. They distinguish future required controls from current implementation. No new technical debt item was invented for excluded future features.

P0.5 records probe result categories and timestamps only. It does not implement Market Alerts or future System Alerts. A valid empty result, policy block, auth denial, rate limit, timeout, network error, oversized/incompatible response and successful response require separate future handling. One observed HTTP 200 cannot certify ongoing source health. ARM64 Foundation CI is QEMU emulation, not a physical Raspberry Pi test.

## Acceptance ledger

`PASS` means the documentary criterion has evidence in this candidate; it does not mean the phase is accepted. A missing required probe or exact-head hosted gate remains `FAIL` until supplied.

| Criterion | Status | Evidence or gap |
| --- | --- | --- |
| AC-F01 | PASS | Eight-provider [matrix](../sources/SOURCE_MATRIX.md), eight dated fiches with official links and required dimensions. |
| AC-F02 | PASS | Matrix and fiches explicitly separate singles/sealed, ES/EU, language and EUR with unknowns. |
| AC-F03 | PASS | Fiches distinguish documented, observed and inferred; conditional/documented-only is never operational verification. |
| AC-F04 | PASS | [Selection](../sources/SOURCE_SELECTION.md) names catalog route, market and retail gaps, alternatives and roadmap impact. |
| AC-F05 | **FAIL** | TCGdex catalog has five reproducible small GETs; no retailer/discovery route has an authorized direct probe. Three retailer fiches explain abstention and selection escalates alternatives to Orchestrator. |
| AC-F06 | PASS | [Cardmarket](../sources/CARDMARKET.md), [eBay](../sources/EBAY_BROWSE.md), [TCGdex](../sources/TCGDEX.md) and [Scrydex](../sources/SCRYDEX.md) condition/discard EUR market-history viability with price semantics. |
| AC-F07 | PASS | [Requirements](../data-contracts/SOURCE_INGESTION_V0.md) and [selection](../sources/SOURCE_SELECTION.md) preserve unknown candidates and own first seen. |
| AC-F08 | PASS | Each fiche records access/cost/limits/terms/retention; no token, full payload or personal record kept. |
| AC-F09 | PASS | [Preliminary contract](../data-contracts/SOURCE_INGESTION_V0.md), [risks](../RISK_REGISTER.md), [threat model](../threat-model/THREAT_MODEL.md); no future implementation. |
| AC-F10 | **FAIL** | Independent final review of the published candidate still required. |
| AC-F11 | **FAIL** | Exact-head PR CI and QA/reviewer linkage still required; Foundation baseline CI is not P0.5 candidate CI. |

## Gates and reproducibility

The documentary change does not alter runtime, lockfile, Docker or CI. Before commit, Windows Python 3.13.15 / uv 0.12.10 completed frozen sync, Ruff format/check, mypy, 20 pytest tests, coverage 94.56% lines / 81.25% branches, build, dependency audit with no known vulnerabilities, and secret scan with no candidates; all commands returned exit 0. These are useful precommit checks, **not** exact-commit gate evidence. The independent QA inspected 16 Markdown files with no broken local links, found a documentation-only diff and confirmed AC-F05 remains failed. The exact-head PR workflow must repeat the Foundation gates and show four successful jobs; no P0 run or precommit result is substituted.

| Gate on published candidate | Status in this prepublication report | Required exact-head evidence |
| --- | --- | --- |
| Frozen sync and lock consistency | **FAIL — candidate SHA pending** | `uv sync --frozen --no-install-project`, then `uv sync --frozen --no-build-isolation`; unchanged lockfile in PR. |
| Formatting, lint and typing | **FAIL — candidate SHA pending** | `ruff format --check .`, `ruff check .`, `mypy src` in quality job. |
| Tests and coverage | **FAIL — candidate SHA pending** | pytest and coverage script >=85% lines / >=80% branches, with counts in quality log. |
| Package build and install smoke | **FAIL — candidate SHA pending** | Locked non-isolated build and outside-tree wheel smoke in quality job. |
| Dependency and secret security | **FAIL — candidate SHA pending** | `pip-audit`, secret scan and threat-model review; no unreviewed relevant finding. |
| Compose | **FAIL — candidate SHA pending** | `version` and `diagnose` smoke in Compose job. |
| AMD64 and ARM64 containers | **FAIL — candidate SHA pending** | Build and version/valid-invalid diagnose/non-root checks in both matrix jobs; ARM64 is QEMU emulation. |
| Independent QA and REVIEWER | **FAIL — exact candidate review pending** | Separate read-only review tied to candidate SHA and documented correction/recheck. |
| PR CI and scope | **FAIL — PR head pending** | PR URL, exact head SHA, successful four jobs and diff limited to intended documentation. |

Live provider tests are intentionally **not applicable to CI** because they would consume third-party access and lack stable rights or fixtures; this does not waive AC-F05's missing retail/discovery probe. No native physical-Pi test applies to this documentation-only candidate; the later operational phase owns native validation. The external delivery record will link the published SHA, CI run, logs and independent review without another commit merely to cite its own hash.

## Independent review record before publication

Separate QA confirmed documentary scope, 16 Markdown files with zero broken local links, no credential-like material, and the AC-F05 blocker. It did not repeat TCGdex requests because the five-request budget was exhausted; the sanitized response ledger permits methodological review, not independent reconstruction of exact payloads. The independent REVIEWER found a material omission in the original Scrydex fiche: its official [sealed](https://scrydex.com/docs/pokemon/sealed) and [sold-listings](https://scrydex.com/docs/pokemon/listings) references. The catalog author corrected the fiche; the Engineering Lead corrected matrix, selection, roadmap and report. The reviewer also found retired Cardmarket documentation links; the market author moved them to the official `apiv2.cardmarket.com` documentation host. A precision finding about individual EUR sales versus aggregates was corrected in the matrix. Final read-only recheck and published SHA linkage remain prerequisites; this paragraph is a correction history, not final approval.

## Limitations, open decisions and recommendation

The five TCGdex observations cannot establish completeness, availability or terms for downstream price history. Cardmarket's published restriction, eBay's production/license dependency, Scrydex's non-EUR prices, and the retailers' absent monitoring rights leave market and retail capabilities unresolved. The specific request to the Orchestrator is whether to obtain retailer/feed authorization, assess an affiliate feed under a separate scoped source review, and choose a rights-compatible EUR market source or change the dependent roadmap. P0.5 can be reviewed as a negative feasibility finding, but AC-F05 remains failed and no phase is closed by this report. Final QA, independent review and exact-head CI will be attached externally to the PR/Phase Lead handoff.
