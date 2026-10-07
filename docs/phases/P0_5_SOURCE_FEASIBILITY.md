# PHASE COMPLETION REPORT — P0.5 Source Feasibility

**Proposed status:** RW-01 supports `AC-F05 PASS` solely for exploratory ES set-discovery access, with retail and market-access decisions still open. New revision review/CI are prerequisites for delivery. **Contract:** P0.5 Source Feasibility v1 and the 2026-10-07 Phase Lead rework RW-01–RW-03. **Date:** 2026-10-07, Europe/Madrid. **Repository:** `KastaTM/card-market-tracker`, branch `docs/p0-5-source-feasibility`, [PR #3](https://github.com/KastaTM/card-market-tracker/pull/3), base `main` at `5175d5b09e8d412e11b2ddf4c24bff41df133843`. Prior reviewed candidate: `d6e7429c0cc5d2c443b0ce934791629b895681c3`. This new revision's final SHA, review and four-job CI are supplied in the PR delivery addendum after publication; no earlier run certifies its new head. No merge or phase acceptance/closure is performed by this report.

## Baseline, ownership and method

The Engineering Brief relays the Orchestrator's 2026-10-07 P0 `ACCEPTED` and `PHASE CLOSED` decision. The Engineering Lead verified clean `main == origin/main` at the baseline, expected remote, [PR #2](https://github.com/KastaTM/card-market-tracker/pull/2) merge `5175d5b` and [main push CI 37649030624](https://github.com/KastaTM/card-market-tracker/actions/runs/37649030624). The later Orchestrator decision was recorded first in the [P0 history](P0_FOUNDATION.md) and [roadmap](../ROADMAP.md); it is not a decision made by this phase team. No pre-existing local edits were overwritten.

**Original-phase ownership:** Engineering Lead handled checkout, integration and Git; catalog, market and retail specialists edited disjoint source fiches. Their model/reasoning identifiers were not reliably exposed and the brief's recommendations are not evidence of actual use. Independent QA and final REVIEWER evidence must be tied to the published candidate; the author's own review is not independent.

**Rework ownership:** Engineering Lead alone edits TCGdex fiche, matrix, selection, roadmap and this report and owns Git. Separate read-only `qa_rework` and `reviewer_rework` evaluate the criterion and final candidate; both were explicitly invoked using available **GPT-6.1 Sol / High**, which is known from their invocation. The root model/reasoning and the original phase agents' profiles remain unverified. No Astra escalation was used. Author, QA and final reviewer are different agents.

The team read the repository instructions, context, P0 contract, operating model, architecture, roadmap, quality gates, testing strategy, risk register, debt, threat model, ADRs, data contracts and P0 report before work. It examined eight independent providers against official pages dated 2026-10-07. Each [fiche](../sources/SOURCE_MATRIX.md) separates provider documentation, bounded observation and inference; records access, cost/limits, rights, geography/language, singles/sealed, IDs/variants, price/stock/date semantics, pagination/freshness and uncertainty. Direct probes were capped at five per provider after conditions review. No account, plan, token, production adapter, database, scheduler or runtime dependency was added.

## Results, probes and selection

| Provider | Decision | Direct requests | Main evidence and limitation |
| --- | --- | ---: | --- |
| [TCGdex](../sources/TCGDEX.md) | `VERIFIED` only for bounded catalog-detail and ES set-enumeration access; future discovery loop and EUR aggregate `CONDITIONAL` | 5/5 total | Four set/card GETs and one two-item paginated GET on 2026-10-07 16:59–17:00 UTC. Existing nonempty ES list and fields support exploratory candidates; no delta, candidate novelty, retail SKU, completeness, sustained health or third-party price rights proved. No sixth request. |
| [Pokémon TCG API](../sources/POKEMON_TCG_API.md) | New integration `REJECTED` | 0/5 | Official retirement/new-signup closure; existing-key migration only conditional. |
| [Scrydex](../sources/SCRYDEX.md) | Singles/sealed catalog and sold-listing endpoints `CONDITIONAL`; EUR price primary `REJECTED` now | 0/5 | Sealed types and individual sold listings are documented, with an eBay/USD example; account/plan, coverage and license unresolved, EUR prices described as future. |
| [Cardmarket](../sources/CARDMARKET.md) | Recurring CMT feed `REJECTED` | 0/5 | New API applications closed and terms incompatible with planned recurring collection absent written agreement. |
| [eBay Browse](../sources/EBAY_BROWSE.md) | Active-listing discovery `CONDITIONAL`; sold/history not qualified | 0/5 | Production approval/license required; active asks only; ES marketplace documented, supply/storage unverified. |
| [GAME España](../sources/GAME_ES.md) | Retail `CONDITIONAL` | 0/5 | Manual sealed SKU, EUR and coming-soon evidence; monitoring/retention grant absent. |
| [Fnac España](../sources/FNAC_ES.md) | Retail `CONDITIONAL` | 0/5 | Manual sealed evidence; own and third-party offers differ; express commercial permission needed. |
| [El Corte Inglés](../sources/EL_CORTE_INGLES.md) | Retail `CONDITIONAL` | 0/5 | Manual sealed/assorted SKU evidence; applicable main-store terms unreadable, price/stock unverified. |

The [matrix](../sources/SOURCE_MATRIX.md) records all dimensions and the [selection](../sources/SOURCE_SELECTION.md) gives primary/alternative/gap by phase. TCGdex is the provisional P1a singles/set seed, subject to coverage, variants and field rights. Scrydex documents sealed products and sold listings, but no access, Spanish/EUR coverage or use rights were verified. No qualified primary EUR market-history feed exists for P2. No permitted retail probe or authorized P6a adapter exists. GAME is a first consent candidate, not an approved primary. TCGdex's ES set-list access supports future candidate enumeration for P4; no actual novelty or card-discovery route was tested. Scrydex sealed catalog, eBay active listings or an approved affiliate feed are conditional leads with distinct semantics. P6a/P4 retail discovery and P2 pricing require Orchestrator decisions on access, budget/permissions and roadmap effects. No unilateral scope change is made.

### Rework outcomes

**RW-01:** [the TCGdex fiche](../sources/TCGDEX.md) assesses two routes using five existing results: known-ID catalog details and the ES set list without predetermined IDs. The latter returned two elements and minimum field structure (`id,name,cardCount` in the first) and official documentation describes SetBrief enumeration. This supports a small exploratory discovery route beyond the HTTP result; same provider is allowed by the criterion. Comparing future external references against own observations, creating unknown local candidates and assigning own first seen are **inferred and unexecuted**. No actual set novelty, second snapshot or delta was observed, and no IDs/payload were retained. Coverage, sort/ASC order, pagination, changes between executions, field retention and ID stability remain to validate. It does not prove discovery of cards, SKUs retail, sealed vendible, stock or preorders.

Independent QA initially recommended FAIL because no baseline/delta was recorded. After checking the exact criterion, QA explicitly withdrew that extra requirement: AC-F05 requires probes of routes, not an implemented temporal detector or two providers, and samples are optional. REVIEWER independently agreed with PASS limited to enumerative feasibility. Their agreement does not turn the future comparison into a tested behavior or acceptance of P0.5.

**RW-02:** not executed because RW-01 is sufficient for the narrow route criterion. A documentation-only refresh read [Scrydex authentication](https://scrydex.com/docs/getting-started/authentication), [terms](https://scrydex.com/terms) and [sealed reference](https://scrydex.com/docs/pokemon/sealed); normal plan/team/key requirements coexist with documented reduced unauthenticated access, while resource use, dataset extraction, commercial exploitation and reuse restrictions remain relevant. That text is not an observed entitlement. No account, consent transaction, key, team, subscription or GET to Scrydex API was made; its total stays 0/5 and classification stays `CONDITIONAL`. No unauthenticated access or persistence rights are claimed verified.

**RW-03:** the next section distinguishes the prior exact SHA's completed review/CI from this revision's publication prerequisites. The final PR addendum will provide this revision's SHA and run after checks complete, without committing claims about its own future CI.

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
| AC-F05 | PASS (exploratory set route only) | RW-01: catalog-detail and ES set-list routes within the same five GETs. List nonempty + observed fields + official enumeration semantics support feasibility; temporal comparison and new candidates are inferred/not executed. Independent QA/REVIEWER agree on exact scope. Retail remains unresolved. |
| AC-F06 | PASS | [Cardmarket](../sources/CARDMARKET.md), [eBay](../sources/EBAY_BROWSE.md), [TCGdex](../sources/TCGDEX.md) and [Scrydex](../sources/SCRYDEX.md) condition/discard EUR market-history viability with price semantics. |
| AC-F07 | PASS | [Requirements](../data-contracts/SOURCE_INGESTION_V0.md) and [selection](../sources/SOURCE_SELECTION.md) preserve unknown candidates and own first seen. |
| AC-F08 | PASS | Each fiche records access/cost/limits/terms/retention; no token, full payload or personal record kept. |
| AC-F09 | PASS | [Preliminary contract](../data-contracts/SOURCE_INGESTION_V0.md), [risks](../RISK_REGISTER.md), [threat model](../threat-model/THREAT_MODEL.md); no future implementation. |
| AC-F10 | **FAIL for this unpublished revision** | Prior `d6e7429…` passed exact-SHA independent review; RW-01 criterion analysis agreed independently. Final review of this revision's own committed SHA is still required and will be recorded in PR addendum. |
| AC-F11 | **FAIL for this unpublished revision** | Prior `d6e7429…` passed four-job PR CI 37685412628. This revision requires its own exact-head CI and review linkage in PR addendum; prior evidence is not substituted. |

## Completed prior-candidate evidence — d6e7429c0cc5d2c443b0ce934791629b895681c3

Tree `20477a9b96e1096821060d625018841f36d10179`, parent `5175d5b09e8d412e11b2ddf4c24bff41df133843`. Separate QA and REVIEWER inspected that exact SHA, 16 documentation files, local links and corrected primary-source conclusions with no remaining documentary blocker. Their review satisfied AC-F10 for that SHA, not automatically this revision. The prior report recorded AC-F05 FAIL; RW-01 in this rework narrows the interpretation after independent re-evaluation.

The [pull_request run 37685412628](https://github.com/KastaTM/card-market-tracker/actions/runs/37685412628) reports `headSha=d6e7429c0cc5d2c443b0ce934791629b895681c3`, completed/success. Quality [job 113011847587](https://github.com/KastaTM/card-market-tracker/actions/runs/37685412628/job/113011847587) passed frozen sync, Ruff format/check, mypy, 20 tests, coverage 94.56% lines/81.25% branches, build/wheel install, audit without known vulnerabilities and secret scan without candidates. Compose [job 113011848129](https://github.com/KastaTM/card-market-tracker/actions/runs/37685412628/job/113011848129) passed both commands; [AMD64 113011847927](https://github.com/KastaTM/card-market-tracker/actions/runs/37685412628/job/113011847927) and [QEMU ARM64 113011847967](https://github.com/KastaTM/card-market-tracker/actions/runs/37685412628/job/113011847967) passed build/version/valid-invalid diagnose/non-root checks with UID 10001. These gates and AC-F11 were **PASS for d6e7429 only**, as also recorded in the PR's postpublication evidence.

## Gates and reproducibility — new rework revision

The rework changes only conclusions and evidence in documentation. Prior Windows Python 3.13.15 / uv 0.12.10 precommit checks were exit 0, but the new revision's gates below require its own committed SHA. The final PR addendum supplies results/versions/logs after publication and replaces these prepublication prerequisites for that exact SHA only. No P0 run, prior-head run or precommit result certifies the new candidate.

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

Live provider tests are intentionally **not applicable to CI** because they would consume third-party access and lack stable rights or fixtures. This does not prove permission or capability for retail. No native physical-Pi test applies to this documentation-only candidate; the later operational phase owns native validation. The external delivery record will link the published SHA, CI run, logs and independent review without another commit merely to cite its own hash.

## Original review correction history and rework review

Separate original QA confirmed documentary scope, 16 Markdown files with zero broken local links, no credential-like material, and the then-reported AC-F05 blocker. It did not repeat TCGdex requests because the five-request budget was exhausted; the sanitized response ledger permits methodological review, not independent reconstruction of exact payloads. The original REVIEWER found omitted Scrydex [sealed](https://scrydex.com/docs/pokemon/sealed) and [sold-listings](https://scrydex.com/docs/pokemon/listings) references. The catalog author corrected the fiche; the Engineering Lead corrected matrix, selection, roadmap and report. Retired Cardmarket documentation URLs and individual-EUR-sale wording were corrected too. Final original QA/reviewer checks on `d6e7429…` found no documentary blocker and its CI passed, as recorded above. Rework QA/REVIEWER agreed independently on the narrower RW-01 reading after examining exact contract text; they must recheck the new committed content, and any correction receives its own recheck before delivery.

## Limitations, open decisions and recommendation

The five TCGdex observations establish small catalog and set-enumeration access only; they cannot establish completeness, temporal discovery, availability or terms for downstream price history. Cardmarket restrictions, eBay access/license, Scrydex non-EUR prices and retailer monitoring rights leave market and retail capabilities unresolved. AC-F05 is narrowly satisfied by set-discovery feasibility; it does not remove those gaps. The Orchestrator must decide retailer/feed authorization or dependent P6a/retail-P4 timing, and a rights-compatible EUR market route or P2 scope. Submit this rework candidate after its own independent QA/REVIEWER and four-job CI are evidenced in the PR. Phase acceptance remains the Orchestrator's decision.
