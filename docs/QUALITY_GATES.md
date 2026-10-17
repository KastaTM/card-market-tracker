# Quality gates

## P4b mandatory evidence

[P4b](phases/P4B_SCOPED_CAPTURE_DISCOVERY_CONTRACT.md) adds AC-S01–S15 with all
earlier gates preserved. Require frozen installs/unchanged lock, Ruff format/lint,
strict mypy, full suite including independent negative/concurrency tests, coverage
>=85% lines/>=80% branches of own runtime, sdist/wheel/outside-checkout install,
dependency audit/secret scan and ARQ/DB/SEC/SRE/docs reviews. The new scoped capture
process harness runs alongside all old smokes in installed wheel, Compose,
linux/amd64 and linux/arm64-QEMU, offline with readonly fixtures and UID10001.
Keep exactly four CI jobs: quality, compose and the two container architectures.
Independent QA and REVIEWER are distinct nonauthors, inspecting the exact final
SHA/tree and complete four job logs. External PR ledger records immutable objects,
commands/logs/results/limitations without circular SHA-only commits. Unexecuted
mandatory gates are FAIL; historical P1b results cannot certify P4b. No merge or
phase closure follows from engineering readiness.

## P1b mandatory evidence

[P1b](phases/P1B_PINNED_METADATA_INGESTION_CONTRACT.md) adds AC-I01–I16,
preserving all earlier gates and four CI jobs. Require bounded deterministic
non-executable extraction, independent artifact/projection/MIT contrast and
eight-request ledger; separate real admission and preserved synthetic guards;
SQLite migration/rollback/history/replay/scopes/integrity/recovery tests. Add
`scripts/pinned_repository_smoke.py` to outside-tree wheel, Compose, AMD64 and
QEMU ARM64, with separate processes, no data network, readonly fixtures and UID10001.
Frozen lock, Ruff/mypy, full suite, coverage85/80, build/install, audit/scan and
independent QA/REVIEWER exact candidate checks remain mandatory. Unexecuted gates
are FAIL. External PR evidence binds SHA/tree/base/job bodies/reviews without
circular identity-only commits. Only Orchestrator accepts/integrates/closes.

## P0.5b mandatory evidence

[P0.5b](phases/P0_5B_REAL_SOURCE_QUALIFICATION_CONTRACT.md) is documentary source
qualification, preserving all four CI jobs and the existing recipes below.
AC-Q01–Q12 require field/rights/semantics traceability, preflight/serial shared
request-budget compliance and correctly bounded negative/conditional conclusions.
No live calls in CI. Final frozen install/lock, Ruff/mypy, all existing tests,
coverage85/80, build/outside-source wheel, audit/scan, Compose/AMD64/QEMU ARM64
and complete CI bodies require exact-candidate evidence. Separate QA/REVIEWER
inspect detached exact-SHA worktrees, public documentation and retained diagnostics
without repeating probes. Unexecuted mandatory gates are FAIL. External PR ledger
binds final head/base/tree/reviews/logs, avoiding circular SHA-only commits.

## P4a mandatory gates

[P4a](phases/P4A_OFFLINE_TEMPORAL_DISCOVERY_CONTRACT.md) adds AC-D01–D15,
preserving all earlier recipes/smokes. Require frozen install/unchanged lock,
Ruff format/check, strict mypy, unit/contract/real SQLite concurrency/negative/
CLI regression, coverage>=85% lines/>=80% branches of all own runtime,
sdist/wheel/outside-source installation, audit/secret scan and ARQ/DB/SEC/SRE/docs
review. Distinct QA and REVIEWER inspect detached exact final-SHA worktrees.

`scripts/discovery_smoke.py` joins catalog/persistence harnesses in wheel,
Compose, AMD64 and ARM64 QEMU. It seeds through P3a then compares in separate
invocations, asserting events, full logical content/schema/version nonmutation
and backup/restore equality. Containers remain UID10001, network disabled and
fixtures read-only. CI retains four jobs: quality/Compose/two architecture jobs.
Final identities/job bodies/reviews belong in the external PR ledger. Unexecuted
mandatory gates are FAIL; historical results cannot certify P4a. Only Orchestrator
authorizes integration. QEMU cannot qualify physical Pi durability.

## P3a mandatory gates

The [P3a contract](phases/P3A_OBSERVATION_PERSISTENCE_CONTRACT.md) adds AC-O01–O15
without reducing the existing recipes. Require frozen lock/install, Ruff format
and lint, strict mypy, all unit/contract/SQLite/integration/regression tests,
coverage >=85% lines/>=80% branches across all own runtime (including storage
failures), sdist/wheel build and outside-source installed smokes, audit/secret
scan, ARQ/DB/SEC/SRE/documentation review and distinct isolated exact-SHA QA and
REVIEWER. Compose and linux/amd64 + linux/arm64 QEMU execute both catalog and
persistence harnesses, proving durable DB content across separate containers.
CI retains exactly four jobs: quality, compose and two platform matrix jobs.

Report every mandatory gate PASS/FAIL with command, environment, reviewed SHA/tree
and result. Unexecuted means FAIL with reason. Working-tree results are not exact
candidate evidence until object identity is established. The PR's external ledger
records postpublication checks/reviews, avoiding self-referential hash commits.
No merge or phase acceptance follows from a green engineering gate; only the
Orchestrator decides. Main-push evidence belongs to a later authorized integration.

## P1a mandatory gates

The [P1a contract](phases/P1A_CATALOG_CORE_CONTRACT.md) adds AC-C01–AC-C12.
Maintain all frozen installation, Ruff, strict mypy, pytest, coverage >=85% lines
and >=80% branches, wheel, secret and dependency audit gates below.
Wheel, Compose, AMD64 and QEMU ARM64 must additionally run the five catalog
smokes in `scripts/catalog_smoke.py`, including valid/mixed/empty/invalid/candidate
input and deterministic replay. Independent QA and REVIEWER review the exact
final SHA. CI has four jobs: quality, compose and two container matrix jobs.
Every applicable result must refer to the final candidate or its identical tree;
the PR ledger records published SHA/checks without a circular SHA-only commit.
Unexecuted mandatory gates are FAIL with reason. Main push evidence after merge
requires a later Orchestrator integration decision; no merge is authorized in P1a
engineering delivery. Synthetic compatibility does not certify live coverage.

For P0, an applicable mandatory gate is PASS only with a reproducible result tied to the reviewed commit. The [phase report](phases/P0_FOUNDATION.md) records mandatory gates as PASS or FAIL. A blocked or unexecuted gate is FAIL with its reason stated. A command in this table is an evidence recipe, not a claim that it ran.

| Gate | Evidence required |
| --- | --- |
| AC-01 identity | Repository, initial state, branch, reviewed commit, and pre-edit changes |
| AC-02 reproducibility | Clean checkout plus `uv sync --frozen --no-install-project` then `uv sync --frozen --no-build-isolation`; lockfile unchanged |
| AC-03 package | `uv build --no-build-isolation`, `sh scripts/wheel_smoke.sh` on Linux or equivalent outside-tree Windows install, version and diagnose |
| AC-04 configuration | Tests for defaults, explicit file, environment precedence, invalid and redacted values |
| AC-05 logging | JSON contract, UTC, run_id, redaction, and handler tests |
| AC-06 architecture | Independent boundary review, no commercial dependency or premature infrastructure |
| AC-07 code quality | `ruff format --check .`, `ruff check .`, `mypy src`, pytest and coverage >=85% lines, >=80% branches of own runtime code |
| AC-08 containers | AMD64 and ARM64 build and smoke: version, valid/invalid diagnose, effective UID non-root |
| AC-09 Compose | `docker compose run --rm version` and `docker compose run --rm diagnose` |
| AC-10 CI | Passing PR and main runs for the proposed commit; failures fail the workflow |
| AC-11 security | Threat model review, secret scan, dependency audit, relevant findings resolved or exception reviewed |
| AC-12 documentation | Substantive documents checked against code and roadmap |
| AC-13 review | Separate QA and reviewer evidence, reviewed commit, blocking findings resolved and rechecked |
| AC-14 report | Each criterion mapped to command, file, test, review, or CI URL |

Mandatory P0 gates also include unit/integration tests, the logging contract test, formatting, Ruff, mypy, coverage, build/install, both container architectures, Compose, secret and dependency scanning, architecture/security/documentation review, and CI. Run `uv run --frozen coverage run -m pytest`, `uv run --frozen coverage json -o coverage.json`, then `uv run --frozen python scripts/check_coverage.py coverage.json` for the coverage threshold. CI includes these commands plus audit and container jobs.

Commercial provider contracts, DB recovery, Telegram delivery, scheduling, and continuous operation on physical Raspberry Pi hardware are **not applicable to P0** because their components do not exist. An unrun mandatory P0 gate is **FAIL with reason: not executed**, never “not applicable.” If any mandatory gate lacks evidence, the phase cannot be recommended for acceptance.
