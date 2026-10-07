# P0 Foundation — interim evidence report

**Contract:** P0 Foundation v1. **Evidence date:** 2026-10-07, Europe/Madrid. **Proposed status:** Interim, blocked from acceptance. This ledger records local results reported by the Engineering Lead. Final evidence must be tied to the reviewed commit and CI runs. A gate lacking required evidence is marked FAIL, even when its command has not run. The Orchestrator alone accepts or closes P0.

| Identity | Current evidence |
| --- | --- |
| Repository | Local `C:\Projects\card-market-tracker`; confirmed remote `https://github.com/KastaTM/card-market-tracker.git`, empty with no branches before bootstrap |
| Branch | `chore/p0-foundation` (reported by Engineering Lead) |
| PR | None evidenced; publication blocked by automatic approval review |
| Commit | Initial `main` commit `30d4666e0e0e4d342c2d5246bc586dcc2c79e109`; no final reviewed implementation SHA yet |
| Pre-edit state | Local target had no Git repository or project files. The remote returned zero branches and `This repository is empty.` The initial SHA was nonexistent. Bootstrap commit `30d4666e0e0e4d342c2d5246bc586dcc2c79e109` contains only README, context, and contract. |

## Model profile used

The runtime identifies the Engineering Lead as based on GPT-6; exact variant and reasoning level are not exposed. ARQ, QA, and DOCS inherited the Lead's runtime profile, whose exact variant/reasoning is likewise not exposed. The independent REVIEWER was explicitly launched with GPT-6.1 Sol / High. No other model override or reasoning escalation was executed. The external Phase Lead's actual model/reasoning is not exposed here. The contract's recommendations are not evidence of use.

## Specialists and independence

Engineering Lead owned runtime, dependencies, Docker, CI, integration, and Git. ARQ performed read-only boundary and multiarch analysis. QA independently authored `tests/**` and reported 20/20 passing tests after logging hardening. DOCS authored README, AGENTS, `.env.example`, and `docs/**`. REVIEWER performed read-only review of `ec52aa70ef6593d98f96005fcb8d2dc3131f5b31` and raised three findings below. Re-review of the corrected SHA remains pending. An author cannot provide independent review of their own work.

## Objectives and implementation

The implemented P0 baseline contains a Python 3.13 package, frozen uv lock, validated local config, one-shot version/diagnose CLI, JSON logs, Dockerfile, Compose, tests, and CI workflow. Local evidence reports `uv sync --frozen` PASS on Windows with Python 3.13.15 and uv 0.12.10. A wheel and sdist built; a wheel installed in a clean temporary location outside the source tree and ran `--version` and `diagnose`. Commercial ingestion, product models, storage, scheduler, service, Telegram, and market analysis remain outside P0.

## Architecture, ADRs, and contracts

The documented decisions are [ADR-0001](../adr/0001-modular-application-boundary.md) and [ADR-0002](../adr/0002-multiarch-validation.md); the implemented interface is [logging v1](../data-contracts/LOGGING_V1.md). Independent architecture review remains unverified. **Database changes:** none in P0 implementation. The initial [threat model](../threat-model/THREAT_MODEL.md) and [debt register](../TECHNICAL_DEBT.md) are present.

## Observability

The CLI emits JSON stderr with UTC timestamps, allowlisted events, run_id, and error categories; diagnostic events include result/duration at the configured log level. Event names are allowlisted and invalid run IDs are replaced by generated UUIDs. QA's current 20-test suite covers JSON fields, redaction of nested/hostile extras, handler replacement, CLI exit codes, and local execution errors.

## Tests and quality gates

The local observations below preceded the candidate commit and independent review. Under [AGENTS.md](../../AGENTS.md), no mandatory gate is marked PASS until its result is tied to the reviewed commit. ARM64 was emulated through QEMU, not run on physical Pi hardware.

Local observations on Windows, Python 3.13.15, uv 0.12.10: `uv run --frozen ruff format --check .`, `ruff check .`, and `mypy src` passed; `coverage run -m pytest` passed 20 tests; `coverage json` plus `scripts/check_coverage.py` reported 94.56% lines and 81.25% branches. `uv build --no-build-isolation` produced wheel and sdist; the rebuilt wheel installed in a new temporary environment outside the tree and ran version and diagnosis with `PYTHONPATH` removed. `pip-audit` on a frozen all-groups export reported no known vulnerabilities after upgrading pytest to 9.1.1. AMD64 and QEMU ARM64 each built and ran version, valid diagnosis, invalid configuration (exit 2), and UID 10001. Both one-shot Compose commands passed. These results need confirmation against a fixed commit before gate promotion.

| Gate | Status | Evidence / blocker |
| --- | --- | --- |
| Formatting | FAIL | Local command passed; reviewed SHA and revalidation pending. |
| Ruff | FAIL | Local command passed; reviewed SHA and revalidation pending. |
| mypy | FAIL | Local command passed; reviewed SHA and revalidation pending. |
| Unit/integration tests | FAIL | QA reported 20/20 passing locally; reviewed SHA and revalidation pending. |
| Logging contract tests | FAIL | QA's six logging tests passed locally; reviewed SHA and revalidation pending. |
| Coverage >=85% lines, >=80% branches | FAIL | Local result: 94.56% lines, 81.25% branches; reviewed SHA and revalidation pending. |
| Build and outside-tree install | FAIL | Local wheel/sdist and clean temporary install passed; reviewed SHA pending. |
| Docker AMD64 build/smoke | FAIL | Docker Desktop 29.7.2 x86_64: all five checks passed locally; reviewed SHA pending. |
| Docker ARM64 build/smoke | FAIL | All five checks passed under QEMU locally; reviewed SHA pending. |
| Compose version/diagnose | FAIL | Both one-shot commands passed on 2026-10-07; reviewed SHA pending. |
| Secret scan | FAIL | Final Git-tracked file scan and finding disposition not yet evidenced. |
| Dependency audit | FAIL | Frozen all-groups `pip-audit` reported no vulnerabilities locally after pytest 9.1.1 update; reviewed SHA pending. |
| Architecture review | FAIL | Separate reviewer and reviewed SHA not yet recorded. |
| Security review | FAIL | Separate review and final secret scan not yet recorded. |
| Documentation review | FAIL | Current docs need final consistency review. |
| Independent QA/reviewer | FAIL | Prior QA run exists; current revision QA and separate final reviewer evidence outstanding. |
| CI on PR and main | FAIL | No cited passing PR/main runs; publishing context/contract was rejected by automatic approval review. |

Commercial provider contract tests, DB recovery, Telegram, scheduler, and continuous operation on physical Pi are **not applicable to P0**. This does not excuse unrun mandatory P0 gates.

## Acceptance criteria

| Criterion | Status | Evidence / blocker |
| --- | --- | --- |
| AC-01 identity and traceability | FAIL | Initial SHA and branch reported; canonical remote, pre-edit record, and final reviewed SHA missing. |
| AC-02 reproducible installation | FAIL | `uv sync --frozen` passed locally, but clean-checkout/lock-unchanged evidence at reviewed SHA is missing. |
| AC-03 executable package | FAIL | Local wheel/sdist and outside-tree install passed; reviewed SHA pending. |
| AC-04 configuration | FAIL | Eight config acceptance tests passed locally; reviewed SHA pending. |
| AC-05 logging | FAIL | Six adversarial logging tests passed locally; reviewed SHA pending. |
| AC-06 architecture | FAIL | Architecture documented; independent review outstanding. |
| AC-07 automated quality | FAIL | Format/Ruff/mypy, 20 tests, and separate coverage thresholds passed locally; reviewed SHA pending. |
| AC-08 container | FAIL | AMD64 and QEMU ARM64 local build/smoke passed, including invalid config exit 2 and UID 10001; reviewed SHA pending. |
| AC-09 Compose | FAIL | Both documented one-shot commands passed locally, no published ports; reviewed SHA pending. |
| AC-10 CI | FAIL | No PR and main CI runs tied to proposed SHA. |
| AC-11 security | FAIL | Threat model and dependency audit exist; final secret scan and independent security review absent. |
| AC-12 documentation | FAIL | Substantive docs exist; final consistency review not yet evidenced. |
| AC-13 independent review | FAIL | Current-revision QA and independent final reviewer evidence outstanding. |
| AC-14 reproducible report | FAIL | Final SHA, command transcripts, CI URLs, and review evidence incomplete. |

## Independent review and rework

REVIEWER (separate from Engineering Lead, QA, and DOCS) reviewed commit `ec52aa70ef6593d98f96005fcb8d2dc3131f5b31` read-only. The review found three P2 issues:

| ID | Finding | Correction in progress | Revalidation needed |
| --- | --- | --- | --- |
| RW-01 | CI did not run Compose, allowing a broken Compose file to pass. | Add a failing CI Compose job for both documented commands. | New-SHA workflow review and actual PR/main CI runs. |
| RW-02 | Isolated package builds could resolve Hatchling/build dependencies outside `uv.lock`. | Install locked build dependencies first; build/install with `--no-build-isolation` locally and in Docker; pin build backend and editable helper. | Clean checkout frozen install, wheel and multiarch rebuild, audit, reviewer re-check. |
| RW-03 | Container smoke treated any nonzero invalid-config exit as success. | Require exit 2 and safe JSON failure event/category. | Run the exact smoke script on AMD64 and emulated ARM64; reviewer re-check. |

The reviewer found no additional blocking Foundation scope, runtime security, or documentation defects at that SHA. These corrections are not accepted until the new candidate SHA is reviewed and affected checks are repeated.

## Known limitations, open issues, and recommendation

Current blockers: the automatic approval review rejected publishing the source context/contract to GitHub, so PR/main CI evidence is unavailable; the final tracked-file secret scan, re-review of RW-01–RW-03, and exact reviewed SHA remain outstanding. P0 diagnostic proves only local configuration and work-directory access. Emulated ARM64 does not prove physical Pi operations. **Recommendation:** do not submit for Orchestrator acceptance while mandatory gates remain FAIL. The Engineering Lead should append exact commands/results and commit, resolve or clearly report the publication blocker, and seek re-review before proposing readiness.
