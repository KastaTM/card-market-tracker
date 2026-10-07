# Quality gates

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
