# Quality gates

## P8d proposed gates (2026-10-30)

[Design handoff](phases/P8D_DESIGN_FREEZE.md) separates Gate A preflight from
Gate B Phase Lead design acceptance. Product schema/identity/writer work waits
for B PASS. Current documentation/probes certify no implementation gates.

The later candidate must preserve frozen installs, Ruff format/check, strict
mypy, complete pytest, line>=85%/branch>=80% coverage, sdist/wheel, installation
outside checkout, dependency audit and secret scan. Four final jobs (Quality,
Compose, AMD64 and ARM64/QEMU) and all thirteen applicable harnesses must pass
on the exact candidate; preserve failures and full logs. No same-SHA failed-job
reruns just to obtain green, reduced fixtures, suppressed tests or enlarged
contract timeouts. Measure >=3 backup/restore controls on full fixture in local
QEMU when available and state unavailability honestly; CI ARM64 is mandatory.

Independent QA and a distinct final REVIEWER must be nonauthors with their own
published runnable probes/results tied to final HEAD/tree. Draft publication/
readback follows implementation. AC-WT20 additionally needs specific one-alert/
private-route live authorization, <=8 metadata and <=1 sendMessage attempt total,
durable receipt/reopen and separate-process replay with zero token/network.
Until then BLOCKED - LIVE_UNVERIFIED; no readiness, merge or phase closure.

## P8c mandatory gates

[AC-WA01..20](phases/P8C_OFFLINE_WATCHLIST_SIGNAL_OUTBOX_CONTRACT.md) require
exact-candidate evidence. Preserve frozen installs, Ruff format/check, strict
mypy, complete pytest, separate line>=85%/branch>=80% coverage, sdist/wheel,
outside-source installation, audit and secret scan; no weakened thresholds,
broad exceptions or collection filters.

All twelve harnesses run in wheel/Compose/AMD64/ARM64-QEMU, product offline with
read-only fixtures and UID10001/private data as applicable. Preserve four jobs
and full final-SHA/tree logs; retain failures, no same-SHA failed-job reruns
without authority. Corrective commits get fresh CI and renewed affected reviews.
Distinct nonauthor QA/REVIEWER provide public probes/helpers/oracles. Unrun gates
are explicit; engineering cannot merge or close P8c.

## P5b mandatory gates

AC-S01..S18 in the opening contract require exact baseline/archived contract,
original revision admission, isolated bounded synthetic retention, independent
identity vectors, strict sequence/replay/transitions, atomic concurrent append,
deep full-fold verification, original-backed recompute, bounded safe CLI/recovery
and documentation. Keep frozen lock/install, Ruff format/check, strict mypy,
complete pytest, line coverage >=85% and branch coverage >=80%, sdist/wheel,
outside-source installed wheel, dependency audit and secret scan unchanged.

The eleventh watchlist-journal harness runs alongside all ten previous harnesses
with product networking denied. Exactly four CI jobs remain Quality, Compose,
AMD64 and ARM64/QEMU. Inspect complete logs tied to the final commit/tree.
Distinct non-author QA and REVIEWER must attest that same candidate with their
own published probes; fixes require renewed probes. Unrun checks remain blocked,
and only all-green applicable evidence permits READY_FOR_ORCHESTRATOR_REVIEW.
Engineering does not merge, accept or close P5b; no live Telegram gate applies.

## P5a mandatory gates

AC-W01..W18 require exact baseline/provenance, canonical target identity,
strict rules, atomic revisions/CAS/replay, synthetic-only ephemeral evaluation,
exact money/time semantics, explanations, bounded CLI, deep recovery, compatibility,
zero product network and complete documentation. Preserve frozen install,
Ruff format/check, strict mypy, full pytest, line coverage >=85% and branch
coverage >=80% (or any stricter project threshold), sdist/wheel, external installed
wheel, dependency audit and secret scan gates. No P5a live/product-network gate
exists; historical P8b T17 evidence is neither rerun authority nor a P5a prerequisite.

The tenth `scripts/watchlist_smoke.py` joins all nine previous installed-process
harnesses in wheel, Compose and linux/amd64 plus ARM64/QEMU validation. Preserve
all four existing CI jobs, offline product invocations, read-only fixtures,
UID10001 and private persistent data. Inspect complete logs on the final candidate;
QEMU does not qualify native Pi hardware or physical power-loss recovery.

Author != independent QA != distinct final REVIEWER. Both nonauthors derive
their own probes/review and attest the same final SHA/tree. Substantive changes
renew checks and attestations. Each AC and gate needs a reproducible result tied
to the reviewed candidate, with FAIL/BLOCKED/unexecuted stated accurately.
Requirements here certify no PASS. The Engineering Lead cannot merge, accept or
close the phase; only a fully evidenced candidate may be recommended for review.

## P8b mandatory gates

AC-T01..T18 require original-backed one-shot delivery, private-route validation,
durable claim/receipt/fencing, ambiguous no-resend, valid429 cooldown/max3 and
globally quarantined restore. Preserve frozen install/Ruff/mypy/full pytest/
85% line/80% branch/build/audit/secret gates. Ninth harness
`scripts/telegram_delivery_smoke.py` joins all eight earlier installed-process
smokes in wheel, Compose and linux/amd64 + ARM64 QEMU. Runtime remains offline,
fixtures read-only, product UID10001/data private. Exactly four CI jobs remain;
inspect complete final-candidate logs.

Distinct nonauthor QA/REVIEWER attest exact SHA/tree with own probes/audit.
Substantive edits renew checks/reviews. Real T17 is mandatory for readiness: one
specifically authorized synthetic alert, durable receipt, separate-process replay,
<=8 metadata requests and exactly1 send attempt. Missing destination authorization
or credentials means BLOCKED / LIVE_UNVERIFIED; complete offline work and name
the dependency. Engineering cannot authorize merge or phase closure.

## P8a mandatory gates

[AC-A01 through AC-A16](phases/P8A_OFFLINE_ALERT_OUTBOX_CONTRACT.md) add
original-capture admission, shared-event/window evidence, safe renderer,
pending-only independent storage, strict read/byte/deadline guards, concurrency,
real process termination/reopen and recovery. Keep all frozen install, Ruff,
strict mypy, complete pytest, line coverage >=85% and branch coverage >=80%,
sdist/wheel, dependency audit and secret scan gates unchanged.

`scripts/alert_outbox_smoke.py` is the eighth harness. All eight run in an
installed wheel outside checkout, Compose and Linux AMD64/ARM64 images; ARM64
uses QEMU. Runtime networking is disabled, fixtures are mounted read-only,
container product UID is10001 and persistent data is private. CI retains four
jobs: quality, compose and two architecture matrix jobs. All four complete logs
must be inspected against the final candidate/tree. Local daemon absence is
reported as unexecuted, never inferred PASS from a historical phase.

Nonauthor QA and a different nonauthor REVIEWER must attest the final SHA/tree.
Follow-up edits renew affected checks and reviews. Record exact reproducible
commands/results in [the report](phases/P8A_OFFLINE_ALERT_OUTBOX.md) and PR ledger.
No gate is certified by this requirements section. Missing mandatory evidence
fails readiness. Merge and phase acceptance remain separate Orchestrator actions.

## P4c mandatory evidence

[AC-J01 to J16](phases/P4C_DISCOVERY_RESULT_JOURNAL_CONTRACT.md) preserve frozen
install/lock, Ruff format/lint, strict mypy, full pytest with runtime coverage
>=85% lines/>=80% branches, build/external wheel, audit and secret scan. The
seventh discovery_journal_smoke.py runs alongside all six existing harnesses in
outside-checkout wheel, Compose, AMD64 and ARM64/QEMU: separate offline processes,
readonly fixtures, UID10001/private data and verified recovery. Keep four CI jobs.

Require independent nonauthor QA and REVIEWER, distinct from each other, on the
exact frozen SHA/tree; risks include dual-window/same-event evidence, forged
admission, hostile SQL/JSON, bounds, rollback, process interruption and concurrent
writers. Full four-job logs and postpublication review evidence belong in the PR
ledger, read back after publishing. Unexecuted evidence is FAIL/BLOCKED; historical
P1c or prototype success cannot certify P4c. Local Docker unavailability does not
constitute a container pass; exact-candidate CI must execute those gates. No merge
or phase closure follows from engineering readiness.

## P1c mandatory evidence

[AC-M01?M16](phases/P1C_MULTI_REVISION_METADATA_CAPTURE_CONTRACT.md) preserve all
earlier gates: frozen install, Ruff format/check, strict mypy, full pytest and
runtime coverage >=85% lines/>=80% branches, audit/secret scan, sdist/wheel and
outside-checkout installation. The sixth harness `multi_revision_metadata_smoke.py`
joins the existing five in wheel, Compose, AMD64 and QEMU ARM64 with separate
processes, no runtime network, readonly fixtures and UID10001/private data.
Retain exactly four CI jobs. QA and REVIEWER must be distinct nonauthors,
contrast R1 before freeze and inspect final immutable SHA/tree and full four-job
logs. Record commands/results in phase report and external PR ledger; unrun
mandatory evidence is FAIL/BLOCKED. Do not substitute historical CI or QEMU for
new candidate execution or native Raspberry Pi tests.

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
