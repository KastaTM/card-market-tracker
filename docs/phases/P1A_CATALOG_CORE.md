# Engineering Completion Report — P1a Catalog Core

Phase: P1a, contract v1, evidence date 2026-10-09 Europe/Madrid.
Proposed status: engineering candidate for independent Orchestrator review;
publication of this report requires its own exact-head reviews and CI ledger.
Only the Orchestrator accepts or closes a phase. No merge has been performed.
Repository: https://github.com/KastaTM/card-market-tracker.
Branch: `feat/p1a-catalog-core`. PR: [#5](https://github.com/KastaTM/card-market-tracker/pull/5)
into `main`. DB changes: **NONE**.

## Authority, baseline and Git

The authorized contract was found in Downloads as `P1A_CATALOG_CORE_PROMPT.md`
(the requested filename with `(1)` was absent). Its P1a identity, baseline,
authority and scope match the Engineering Brief. The archived
[contract](P1A_CATALOG_CORE_CONTRACT.md) was copied byte for byte; source and
copy SHA-256 before Git normalization:
`03F50A67F8BF95410193961D9FA88D567BF757159D31B4F2A2264953ACF8CB42`.
The brief and repository sources of truth were read before implementation.

Initial checkout: clean `docs/p0-5-integration-record`, HEAD
`253a5354d8645fa8c72cbd7038e213832ab8ce18`. Local `main` was
`5175d5b09e8d412e11b2ddf4c24bff41df133843`; no branch or existing work was reset.
After `git fetch origin`, remote `main` matched the authorized baseline:

| Object | Verified value |
| --- | --- |
| Base | `af573f04586024e7666a8999526e0aaab238c0dc` |
| Base tree | `878cba9cfadfea47beaf0b6727469c3926dc25c9` |
| Ordered base parents | `1dc890c7410e3d9c718654e9f64380f9e5026042`, `253a5354d8645fa8c72cbd7038e213832ab8ce18` |
| Baseline PR / push CI | [PR #4](https://github.com/KastaTM/card-market-tracker/pull/4) / [37956251863](https://github.com/KastaTM/card-market-tracker/actions/runs/37956251863), four jobs successful |
| Reviewed implementation commit | `d434390373fa738a8fda7d2e787702e331caaea2` |
| Implementation tree | `222390154495f243e907344d029e187d367b9120` |
| Implementation parent | Exact authorized base above |

The branch was created from verified `origin/main`. P0.5's later acceptance and
closure are recorded in its report and roadmap **as the Orchestrator decision**;
historical pending labels remain historical evidence. The final report commit,
head/tree/base, checks and review confirmations are recorded in the PR's external
delivery ledger, avoiding a commit created solely to quote its own SHA. Every
substantive correction requires reviews and checks on the resulting SHA.

## Models and specialists

| Role | Recommended profile | Actually observable usage |
| --- | --- | --- |
| Engineering Lead | GPT-6.1 Sol / Medium, High for identity/security/debugging | Runtime identifies a GPT-6 based agent; exact backend variant/reasoning is not exposed and remains unverified. No unsupported claim of a root model switch. |
| ARQ / BE / DATA (`core_author`) | GPT-6.1 Sol / High | Explicit `gpt-6.1-sol`, `high` delegation accepted by orchestration; backend cannot be independently introspected. |
| INTEGRATIONS / SEC (`integration_author`) | GPT-6.1 Sol / High | Same explicitly accepted delegation; backend independently unverified. |
| QA (`qa`) | GPT-6.1 Sol / High | Separate explicitly accepted delegation; backend independently unverified. |
| REVIEWER (`reviewer`) | GPT-6.1 Sol / High | Separate explicitly accepted delegation; backend independently unverified. |
| ChatGPT Phase Lead | Brief recommends GPT-5.6 Sol / High, alternative GPT-6.1 Sol / High | Not observed by local Codex. |

No Astra escalation was used. Lead owns Git, shared integration, CLI/logging,
scripts/CI and completion documentation. ARQ/BE/DATA authored only catalog core,
identity ADR/contracts, manifest fixture and core tests. INTEGRATIONS authored
only the adapter namespace, adapter tests/fixtures and source field policy.
Parallel ownership was disjoint; a formatting-only overlap in the adapter was
identified and coordinated before committing. QA and REVIEWER author no source
or tests, are different agents from authors and each other, and review read-only.
SEC's author/read review is supplementary and is not represented as independent
QA or final approval. No SRE/DB-OWNER delegation was needed.

## Objective, implementation and decisions

The installed `cmt catalog --input PATH --manifest PATH` now validates bounded
local JSON, translates modeled TCGdex set/card metadata, resolves explicit
contextual correspondences, and emits deterministic accepted entities,
candidates and categorized rejections without network, secrets or database.
Repeated records preserve record counts and stable IDs while entity output is
unique and includes required parent closure.

[ADR-0003](../adr/0003-catalog-identity.md) separates set, base card, printing and
sealed identities. Canonical UUIDv4 values are assigned once during curation;
provider IDs/names/URLs/SKUs/hashes never generate them. Card numbers remain text.
ES/EN set aliases require explicit equivalence, while language and normal/holo/
reverse distinguish printing IDs. Availability flags cannot prove an observed
finish. Unknown language/variant remains a candidate without canonical ID.
Homonyms do not merge. A contradictory number, relation or binding fails instead
of silently merging or hiding the problem behind variant ambiguity.

The implemented inward boundary is external JSON -> bounded shape validation ->
generic ingestion evidence -> validated manifest/resolver -> provider-independent
entities. Domain modules import no adapter or TCGdex shape. Standard library only;
no new runtime/development dependency and no lockfile change.
Versioned [catalog](../data-contracts/CATALOG_V1.md),
[ingestion](../data-contracts/INGESTION_V1.md) and
[manifest](../data-contracts/MANIFEST_V1.md) contracts define relationships,
unknown/nulls, provenance, outcomes, bounds and incompatible changes.
Provenance is explicitly required, not synthesized by default. Release date,
provider update and capture retain distinct semantics; no first-seen is fabricated.

Sealed is an independent minimal entity and generic synthetic observation tested
in the core; the TCGdex adapter processes only sets/cards. No sealed commercial
SKU is inferred from boosters. No commercial catalog completeness, collector,
sync/pagination, scheduler, DB/ORM/history, market EUR, retail, stock/preorders,
temporal Discovery, alert delivery or web UI is delivered.

## Security, provenance, observability and debt

All fixtures are synthetic, labeled and documented in
[provenance](../../tests/fixtures/PROVENANCE.md). Official TCGdex docs and database
interfaces/license were reviewed for the minimum fields in
[the field policy](../sources/TCGDEX_P1A_FIELDS.md). No new live API GET: **0/5**.
Official documentation is not an observed response, synthetic tests do not prove
coverage or source health, and MIT does not authorize third-party images, marks,
prices or arbitrary API material. No real-data retention approval is claimed.

The [threat model](../threat-model/THREAT_MODEL.md) describes implemented byte,
depth, node, string and count bounds, duplicate-key/nonfinite/encoding rejection,
identity controls and the local curator trust boundary. Per file: 1 MiB, depth16,
20000 nodes, string1024; records1000, entities1000, bindings2000. Manifest input
is entirely validated before use. No input URL is fetched; there is no output
file option or DB mutation. Compose/catalog image smoke disables network and
uses read-only fixture mounts; effective container UID is10001.

[Logging v1](../data-contracts/LOGGING_V1.md) has a compatible additive extension:
one `catalog.completed` event with UUID run_id, duration, fixed outcome and bounded
counts, and allowlisted error category when applicable. Paths, raw input, names,
secrets and exception messages never enter stderr. Stdout results omit names,
images, prices and raw extras; minimal contextual candidate references are
intentional untrusted output evidence. Global failure has `counts=null` rather
than misleading empty success. Codes0/3/2/1 distinguish clean-or-empty, incomplete
batch, global invalid input, and unexpected local failure. P0 remains regression
tested. No duplicate handlers are added.

No new significant technical debt was identified. Existing TD-001 local-only
diagnosis and TD-002 emulated ARM64/native Pi gap remain. Absence of DB and
Discovery is contractual scope, not invented debt. Source-rights/coverage risks
and physical Pi behavior remain explicit limits in the risk register.

## Tests and reproducible gates

Implementation SHA `d434390373fa738a8fda7d2e787702e331caaea2` local Windows
Python3.13.15/uv0.12.10: **218 tests passed**, comprising101 core,81 adapter,
10 CLI,6 additive log and20 Foundation regression tests. Own runtime coverage
**99.04% lines / 97.59% branches**; no runtime exclusions added.
Ruff0.13.3 and strict mypy1.20.2 passed. Docker Desktop29.7.2 uses
Python3.13.16 pinned image; ARM64 is QEMU emulation, not physical Pi.
The sandbox helper initially could not create processes; reviewed execution
outside that sandbox worked. That environment error is not a repository failure.

| Gate | Result on implementation SHA | Command / evidence |
| --- | --- | --- |
| Frozen installation / unchanged lock | PASS | `uv sync --frozen --no-install-project`; `uv sync --frozen --no-build-isolation`; `git diff --exit-code -- uv.lock` |
| Format, Ruff, mypy | PASS | `uv run --frozen ruff format --check .`; `uv run --frozen ruff check .`; `uv run --frozen mypy src` |
| Unit/integration/contracts/regressions | PASS | `uv run --frozen coverage run -m pytest`:218 passed |
| Coverage | PASS | `coverage json -o coverage.json`; `python scripts/check_coverage.py coverage.json`:99.04/97.59 above85/80 |
| Wheel build | PASS | `uv build --no-build-isolation`, wheel and sdist |
| Installed wheel outside tree | PASS | Temporary venv, `uv pip install --python ... --no-deps dist/*.whl`; installed version/diagnose and five `catalog_smoke.py --mode installed` cases |
| Secret scan | PASS | `uv run --frozen python scripts/check_secret_scan.py`: no candidates across tracked new files |
| Dependency audit | PASS | Frozen all-groups export then `uv run --frozen pip-audit -r requirements-audit.txt`: no known vulnerabilities |
| AMD64 build/run | PASS | `docker buildx build --platform linux/amd64 --load`; `catalog_smoke.py --mode docker`; version/diagnose/invalid-config exit2 JSON + uid10001 |
| ARM64 build/run | PASS | Same commands with `linux/arm64`, QEMU emulated, including five catalog cases |
| Compose | PASS | Rebuild version/diagnose/catalog services; `catalog_smoke.py --mode compose`: five cases |
| Architecture/data/security/docs review | PASS | REVIEWER exact implementation SHA read-only; no remaining runtime/contract/security blocker |
| Independent QA / REVIEWER implementation | PASS | Two distinct read-only agents checked exact implementation SHA; QA clean checkout218 tests +19 independent risk assertions, wheel, scans; REVIEWER Git blobs, contracts/architecture/security |
| Four-job PR CI on implementation | PASS | [Run37961483065](https://github.com/KastaTM/card-market-tracker/actions/runs/37961483065), exact `headSha=d434390373fa738a8fda7d2e787702e331caaea2`, completed success; all four job steps/logs inspected |
| Final report commit review/CI | FAIL pending publication | This report's committed SHA, independent rechecks and four-job CI must be supplied in PR delivery ledger; implementation evidence alone does not certify the new revision |

On Linux CI, scripts `wheel_smoke.sh` and `container_smoke.sh` run the same
catalog harness. Windows uses equivalent explicit commands. The five modeled
cases assert accepted/candidate/rejected counts and codes0/3/0/2/3, required event
shape and stable replay; tests additionally cover wholly rejected batches and
malformed JSON. No tests process live source data or depend on provider access.
Main push CI after merge is a later authorized integration step and does not
exist for this unmerged PR. Mandatory unexecuted candidate gates remain FAIL.

## AC-C01–AC-C12 matrix

PASS here means evidence for the implementation candidate, not acceptance.
The final published report SHA/checks/reviews must additionally pass in the
external PR ledger before the Phase Lead can recommend Orchestrator review.

| AC | Result | Evidence |
| --- | --- | --- |
| AC-C01 | PASS | Verified baseline objects/PR4/CI, preserved clean prior branch, P0.5 attribution and branch/PR5 |
| AC-C02 | PASS | ADR-0003, typed models, stable UUIDs, ES/EN/variants/sealed core tests |
| AC-C03 | PASS | Three v1 contracts, inward boundaries, typed generic source evidence |
| AC-C04 | PASS | Manifest strict parsing, identity/relationship/context conflict tests, deterministic replay and unique parent closure |
| AC-C05 | PASS | Offline minimum adapter,81 synthetic contract tests, extras discarded/incompatibilities explicit |
| AC-C06 | PASS | Unknown/unmapped candidate records preserve context without name matching or promotion |
| AC-C07 | PASS | ES/EN aliases/printing IDs, three finishes/unknowns, text numbering, sealed generic core sample |
| AC-C08 | PASS | Dated field rights policy and fixture provenance; synthetic-only retention, no real rights claim |
| AC-C09 | PASS | Installed wheel and container/Compose five-case smokes; explicit global/mixed/empty codes and no network/DB |
| AC-C10 | PASS | Additive logging contract + tests: UUID/duration/outcome/bounded counts/categories and secret-safe errors |
| AC-C11 | PASS for implementation | Local checks and exact four-job CI37961483065 pass on reviewed implementation SHA; final report revision requires its own checks |
| AC-C12 | PASS for implementation; final report pending | Independent QA and REVIEWER passed exact implementation SHA; this report's final committed re-review is required before delivery |

## Findings and independent review

The first integration run caught incompatible synthetic set dates; fixture was
aligned with the explicitly curated manifest rather than relaxing conflict checks.
Strict mypy caught unnecessary casts; authors corrected them. Adapter tests found
Windows fixture BOMs, removed before commit. Timestamp conversion year-boundary
overflow was made a categorized error with regression tests. QA's risk plan
requested poison/unknown/duplicate/bool-version/bounds/privacy cases.
REVIEWER and ARQ independently identified implicit synthetic provenance; the
author made it mandatory and tests explicit. Remaining documentary precision
items (P0 human stdout scope, adopted identity decision, metadata-only risk
mitigation, trusted Manifest construction) were corrected before implementation
commit. REVIEWER inspected exact implementation SHA/tree and Git blobs with clean
status and no blockers. QA executed independently in a clean temporary checkout
at `C:\Users\Rodrigo\AppData\Local\Temp\cmt-p1a-qa-dc15d5d3224644e9af96611ef2ce381a`,
with clean Git and unchanged lock before/after. All218 tests, quality, coverage,
outside-tree wheel, secrets/dependency audit and19 extra risk assertions passed.
These exercised deterministic replay, unique identities, number/set poisoning,
unknown language/variant, arbitrary-name/price/image removal, socket denial,
no file mutation, duplicate/nonfinite/depth/byte input and error redaction.
The four-job implementation CI independently reproduces the same local results.
The later exact report SHA, QA result, reviewer confirmation and CI log results
must be recorded in the PR ledger; agent findings are not formal GitHub approval.

## Limits, open dependencies and recommendation

Real source coverage, field retention and commercial dataset completeness remain
unverified; all processing evidence is synthetic. Detailed variant arrays are an
explicit incompatible shape in this minimum adapter. Base card uniqueness by
set/number is deliberately limited and has an ADR revisit trigger for actual
design/numbering evidence. Manual manifests are small curated local assets, not
signed authorizations or concurrent-edit/persistence machinery. No native Pi,
24/7 operation, history/recovery, collector or durable candidates are claimed.
P3a is unopened. P2 and P6a/retail Discovery remain blocked by source rights,
access and semantics. No scope proposal expands this contract.

Submit PR5 only with the completed final exact-SHA evidence ledger for Phase
Lead/Orchestrator review. This document does not accept the phase or authorize
merge. If any mandatory gate fails, correct it and revalidate the resulting SHA;
do not declare readiness while evidence is incomplete.
