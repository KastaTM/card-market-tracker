# Phase Completion Report — P0.5b Real Source Qualification

Phase: P0.5b, opened by the Orchestrator 2026-10-13 Europe/Madrid.
Research/execution date: 2026-10-14. Proposed status at this committed publication
snapshot: investigation candidate, **final exact-SHA gates/reviews pending**.
Negative/conditional source results are valid research outcomes; no source or
consumer phase is approved by this report. Only the Orchestrator accepts/closes
or authorizes integration. **Merge not authorized or performed.**

Repository: `KastaTM/card-market-tracker`.
Branch: `docs/p05b-real-source-qualification`, target `main`.
PR/head/tree/final checks: external PR delivery ledger after publication,
avoiding a circular SHA-only commit. That ledger may supersede pending statuses
only with reproducible exact-candidate evidence. **DATABASE CHANGES: none.**

## Authority, baseline and preservation

The full [contract](P0_5B_REAL_SOURCE_QUALIFICATION_CONTRACT.md) was supplied by
the user in response to a location request; the [brief](P0_5B_CODEX_ENGINEERING_BRIEF.md)
was copied from the initial attachment. [Ownership](P0_5B_OWNERSHIP.md) records
archive provenance/hashes and disjoint read-only responsibilities. The initial
missing-contract marker was replaced; literal AC-Q01–Q12 are now available.
No requirement was inferred/invented in its absence.

Before edits: remote/status/branch/worktree inspection and fetch. Initial clean
P4a HEAD `c5ed228af831a2a6ed8a12c7072777d3908296a5`; local main `5175d5b` was
behind; old branches and P3a/P4a detached reviews preserved. Fetched main/base
`6385c952a9f2024c8b7bdb33d37fa21017029bd5`, tree
`8fa2abeb9f4e8991bab1b2895fc397f64bb39a19`, ordered parents
`734641a7ef920688677cdea6bc82f908a2856927` then
`c5ed228af831a2a6ed8a12c7072777d3908296a5`, matching the supplied baseline.
Initial HEAD-to-base diff empty. Authorized branch was absent and created from
that base; no reset, force or rebase. PR7 merge metadata independently checked.

Contract attributes P4a ACCEPTED/PHASE CLOSED and P0.5b opening to the Orchestrator.
[Roadmap](../ROADMAP.md) and [P4a historical note](P4A_OFFLINE_TEMPORAL_DISCOVERY.md)
record that decision, not Codex acceptance. [PR7 integration](https://github.com/KastaTM/card-market-tracker/pull/7#issuecomment-6155836622)
and [main CI38471731980](https://github.com/KastaTM/card-market-tracker/actions/runs/38471731980)
remain historical evidence, never new P0.5b tests. No closure comment invented.

Mandatory context/governance, phase reports/contracts, source matrix/fiches,
architecture/ADRs, data contracts, testing/gates/CI, risks/debt/threats were read.
Sandbox shell setup failed before commands; automatically reviewed elevated
execution worked. This environment issue is not provider failure.

## MODEL PROFILE USED and specialists

| Role / agent | Requested / accepted configuration | Observable scope and limit |
| --- | --- | --- |
| Engineering Lead `/root`, also PO/integrating author | GPT-6.1 Sol/Medium, High for rights/integration requested by brief; exact root selection unverified | Runtime identifies GPT-6-based Codex; precise serving variant/reasoning/client selector not exposed. No claimed switch |
| INTEGRATIONS/DATA `integrations_data` | Explicit `gpt-6.1-sol/high` accepted | Read-only TCGdex artifact/type/compiler/semantic research; no direct requests/edits |
| SEC `security_rights` | Explicit `gpt-6.1-sol/high` accepted | Read-only rights/market/retail/field-use research and supplementary review; not independent final QA |
| ARQ/DB-OWNER `architecture` | Explicit `gpt-6.1-sol/high` accepted | Read-only boundary/timestamp/TD-005 proposal and documentary corrections |
| QA `qa_final` | GPT-6.1 Sol/High planned | Distinct final detached exact-SHA execution/source verification, no authorship; accepted invocation/results external |
| REVIEWER `reviewer_final` | GPT-6.1 Sol/High planned | Separate final detached exact-SHA independent review, no authorship; accepted invocation/results external |
| ChatGPT Phase Lead | Contract recommends Sol/High Work or5.6Sol/High normal | Separate client selection/execution unobserved |

Accepted tool configuration does not independently identify serving backend.
No Astra escalation or root model switch. Lead alone owns all edits/Git/gates;
research agents were concurrent read-only, direct requests serial Lead-only.
Author, QA and REVIEWER are different agents; agent results are not formal GitHub
approval. Source research specialists are not substituted for independent reviews.

## Objectives, source decisions and primary evidence

Exactly five providers/routes assessed: TCGdex priority; M1/M2 market; R1/R2
retail/feed. Awin is the sole new provider. Second routes resolve different gaps:
Scrydex daily/history/local-storage semantics versus active eBay; Awin permitted
feed infrastructure versus direct GAME HTML. No full rerun of eight historical
providers and no out-of-scope new vendor. All earlier P0.5 evidence preserved.

| Route | Result | Concrete evidence / limits |
| --- | --- | --- |
| [TCGdex](../sources/TCGDEX_P0_5B_QUALIFICATION.md) | CONDITIONAL live REST metadata | Pinned two source files, code/type/localization/license correspondence,6 successful serial reads. Sampled source names/id/date/official and generated card reference match ES/EN; deployed revision/full coverage/general REST rights unresolved |
| [eBay Browse](../sources/EBAY_BROWSE_P0_5B_QUALIFICATION.md) | CONDITIONAL active ES/EUR listings | Full license/production requirements; active asks/bids, not sold history. Intermediate/deletion/display/derived-use restrictions; quota only provisional indexed locator and current method paging gap;0 probes |
| [Scrydex](../sources/SCRYDEX_P0_5B_QUALIFICATION.md) | REJECTED_FOR_PROPOSED_USE EUR/Spain reference | Current USD/JPY/futureEUR; local historical-chart storage guidance positive, durable/upstream/publication rights unresolved. Daily aggregates versus sold dates separate;0 probes |
| [GAME](../sources/GAME_ES_P0_5B_QUALIFICATION.md) | CONDITIONAL automated retail route | Current legal conditions resolve no access/history grant. Historical sealed/assorted/coming-soon observations stay dated, no new product crawl;0 probes |
| [Awin](../sources/AWIN_PRODUCT_FEEDS.md) | CONDITIONAL feed route | Publisher/feed permission required; detailed legacy/enhanced schema and partial200 semantics. Concrete Pokémon ES/EU feed/private eligibility/history rights unknown; full relevant terms403, index only provisional locator;0 probes |

Each fiche separates exact fields/upstream, intended use, documented/observed/
inferred/unknown, five actions and ACCESS/RETENTION/SEMANTICS/COVERAGE/LIMITS.
[Matrix](../sources/SOURCE_MATRIX.md) and [selection](../sources/SOURCE_SELECTION.md)
retain gaps rather than averaging permission. No source is declared fully qualified.
No repeated upstream API aggregate is counted as an independent market.

## Probes, retention and observability

[Ledger/preflight](../sources/P0_5B_EVIDENCE_LEDGER.md), run
`p05b-20261014-qualification`: six Lead-only GETs2026-10-14 11:05:57–59UTC,
**6/12 total,6/6 TCGdex**, each200,126–426ms,536–21966bytes. Two pinned official
text artifacts and four set/card ES/EN details, no list/second temporal capture.
Remaining providers0. Public docs/tool Git metadata are not direct data probes.
HTTP200 proves only each response, not source health, SLA or license.

Written preflight preceded requests: permitted transient public access, paths,
field diagnostics, serial count/time/byte limits, no auth/cookies, redirects,
retry or payload-link follow. Raw bodies were never saved/printed; retain only
UTC/endpoints/status/bytes/duration/types/presence/counts/scalar equality booleans.
No real sample/fixture or observed DB record. Complete MIT notice retained with
identified repository research. Ephemeral ignored stdlib invocation is not a
shipped helper, collector or reusable API. Offline boundary verification of that
invocation can be supplied by QA without any provider requests.

Browser research timing/HTTP/bytes unavailable is explicitly unknown; tool-clock
checkpoints are session times, not invented page response metrics. Full inaccessible
terms/method documents stay gaps; indexed text never certifies a complete license.
Failure/partial/empty/denial/timeout/rate-limit categories stay distinct. No new
product/stock/delta/source health or real observed printing was claimed.

## Architecture, contracts, security and debt

[Proposal](../sources/P0_5B_FIELD_USE_CAPTURE_POLICY.md): source → adapter-owned
validated source model → normalized ingestion → curated CMT domain. No runtime
model/schema/dependency introduced. Source IDs remain references; counts ignored
by INGESTION_V1, flags availability-only, jumbo/preRelease excluded from confirmed
REST scope, detailed variants never create printing observations. Missing required
data rejects; optional dates remain unknown. P1a policy preserves its historical
supported synthetic shape. Existing ADR0003–5 suffice; no new adopted ADR.

`captured_at/provider_updated_at/first_seen_at/release_date/price_observed_at/sold_at`
are explicitly separated. Multi-page capture needs disclosed interval/completeness,
not an atomic snapshot assumption. TD-005 durable empty/multi-producer context is
a later-contract proposal, never a schema1 repair or producer-authentication claim.
Runtime, identity, replay/history, comparator, lock/dependencies, current v1 data
contracts and synthetic-only controls are unchanged. SOURCE_INGESTION_V0's status
is clarified as preliminary, acknowledging implemented v1 catalog.

Threat/risk/architecture/debt and [research runbook](../runbooks/SOURCE_QUALIFICATION.md)
distinguish future policy machinery from current controls. Raw content/credentials/
private headers/personal data/art/third-party prices excluded; no contacts/costs/
accounts/contracts accepted. **TD-001–TD-005 remain open**, no artificial new debt.
QEMU/API success does not close native-Pi/health/capture gaps. Unknown retention
blocks copying; no provenance relabeling. **DATABASE CHANGES: none.**

## Final mandatory gates and exact acceptance criteria

At this prepublication snapshot the final committed identity/reviews/CI do not
yet exist. Every mandatory final gate is **FAIL pending exact-candidate evidence**,
not N/A or historical PASS. External delivery ledger supplies actual commands,
environment, SHA/tree, reviewers, full CI job bodies and limitations for all rows.

| Gate | Snapshot result / recipe |
| --- | --- |
| Baseline/scope/document/license/link review | FAIL pending independent exact candidate; supporting documents above |
| Frozen install/lock | FAIL pending final `uv sync --frozen --no-install-project`, then `--no-build-isolation`; lock diff empty |
| Ruff/strict mypy | FAIL pending final `ruff format --check .`, `ruff check .`, `mypy src` |
| Unit/integration/contract/regression/coverage | FAIL pending final `coverage run -m pytest`, JSON and check_coverage;>=85%lines/>=80%branches |
| sdist/wheel/outside-source smokes | FAIL pending final build + existing Foundation/catalog/persistence/Discovery smokes |
| Dependency audit/secret scan | FAIL pending final frozen export/pip-audit/check_secret_scan |
| Compose/AMD64/ARM64 QEMU | FAIL pending final four-job CI and full body inspection; emulation only |
| Separate final QA/REVIEWER | FAIL pending final detached exact-SHA results |

| Literal contract AC | Snapshot result | Concrete document/primary evidence / required verification |
| --- | --- | --- |
| AC-Q01 | FAIL pending exact review | Baseline/ownership/archive/roadmap/P4a note; Git object/status/worktree diff and contract authority |
| AC-Q02 | FAIL pending exact review | TCGdex field fiche, pinned source/transform/docs/MIT notice, T01–06 diagnostic mapping; independent field/source review |
| AC-Q03 | FAIL pending exact review | M1/M2 fiches: current license/requirements/prices/history/cache/terms;2 routes, currency/aggregate/sale/upstream distinctions |
| AC-Q04 | FAIL pending exact review | GAME/Awin fiches: legal/feed schema/access conditions;2 routes, seller/stock/preorder/ES/retention gaps |
| AC-Q05 | FAIL pending exact review | Written preflight + diagnostic ledger6/12,6/6; abstentions reasoned; CI diff unchanged/no live calls |
| AC-Q06 | FAIL pending exact review | D01–D06/T01–T06, artifact revisions/dates/types/rights notice; no raw bodies, indexed/full-read uncertainty explicit |
| AC-Q07 | FAIL pending exact review | Matrix with five dimensions/action decisions; no qualified route/false entitlement, blocks preserved |
| AC-Q08 | FAIL pending exact review | Selection priorities and conditional future P1b field/capture scope; no phase opened, no permission invented |
| AC-Q09 | FAIL pending exact review | Policy/timestamps/TD-005 proposal, architecture/v0 status; `git diff BASE HEAD -- src tests uv.lock pyproject.toml` empty |
| AC-Q10 | FAIL pending exact review | Threat/risk/runbook/notice/payload-discard/security/TD preservation; final scan and independent SEC/REVIEWER review |
| AC-Q11 | FAIL pending final executions/CI | Unchanged existing recipes/four jobs, frozen quality/tests85/80/build/install/audit/scan/containers; no shipped helper/tests |
| AC-Q12 | FAIL pending final reviews | Distinct QA/REVIEWER detached final identity, coherent archives/docs/external exact-head ledger |

No AC requires a compatible source. Final external PASS may certify this bounded
research even when every future use is blocked/conditional. Author self-evaluation
does not substitute independent review, and no main-push P0.5b gate is invented
for an unmerged PR.

## Limits, open actions and recommendation

Maintain P2/P6a/retail blocked and TCGdex provisional. Prioritize exact artifact/
transform/field-right correspondence for narrow ES/EN catalog. If qualified under
a later decision, propose **P1b Licensed Metadata Ingestion & Capture Scope**
for the stated whitelist and versioned observed-source/empty/multi-producer capture
contracts, without implementing or opening it here. Next, consider Awin eligibility/
one concrete ES/EU feed/full advertiser rights through a human decision; eBay/GAME
need their specific permission/access actions. Scrydex EUR awaits actual European
coverage; no USD/JPY conversion, plan purchase or alternate scope substitution.

Full remaining compiler/deployment correspondence, corpus coverage, ID permanence,
independent capture completeness and some full terms remain unknown. These are
source-use conditions, not failed implementation hidden as N/A. No seventh
TCGdex request or new vendor is authorized. Current runtime remains intact.

Submit the PR without merge. Propose readiness only when its exact final ledger
contains all mandatory gates and distinct independent reviews. The Orchestrator
alone decides acceptance/closure/integration; no unilateral source unblock.
