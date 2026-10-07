# Card Market Tracker

Card Market Tracker (CMT) is a personal market intelligence project for collectibles. The initial domain is Pokémon TCG in Spain and Europe, using EUR. This repository starts with the [project context](context.md) and the [P0 Foundation contract](P0_FOUNDATION_CONTRACT.md).

P0 supplies an installable Python package, validated local configuration, a one-shot CLI diagnostic, structured logs, and container/CI scaffolding. It does not collect market data or run a service.

## Quick start

Requires Python 3.13 and uv 0.12.10. From the repository root:

```sh
uv sync --frozen
uv run --frozen cmt --version
uv run --frozen cmt diagnose
```

The diagnostic validates configuration and checks that the local work directory accepts a temporary file. It makes no network request. Success prints `diagnose: ok (configuration, local work directory)` on stdout; at the default `INFO` level, a JSON event goes to stderr. Exit codes are `0` for success, `2` for invalid configuration or arguments, and `1` for local execution failure.

Configuration precedence is **process environment > explicitly selected env file > defaults**. An env file is read only with `cmt diagnose --env-file PATH`. There is no automatic `.env` lookup.

| Variable | Default | Validation |
| --- | --- | --- |
| `CMT_LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, or `ERROR` (case insensitive) |
| `CMT_WORK_DIR` | Current working directory | Existing directory; the diagnostic checks write access |

See [.env.example](.env.example) for sanitized settings. Env files accept `KEY=value`, blank lines, comments, and simple matching quotes. Unknown keys and malformed lines fail validation. Errors and JSON logs omit configured values.

## Container

With a running Docker daemon:

```sh
docker compose run --rm version
docker compose run --rm diagnose
```

Both commands exit after completion. The image runs as UID/GID 10001, publishes no ports, and defaults `CMT_WORK_DIR` to `/tmp`. See the [local runbook](docs/runbooks/LOCAL_DEVELOPMENT.md) for development commands and multiarch smoke tests.

## Repository map

- [Architecture](docs/ARCHITECTURE.md), [standards](docs/CODING_STANDARDS.md), [tests](docs/TESTING_STRATEGY.md), and [quality gates](docs/QUALITY_GATES.md).
- [Operating model](docs/ENGINEERING_OPERATING_MODEL.md), [roadmap](docs/ROADMAP.md), [risks](docs/RISK_REGISTER.md), and [technical debt](docs/TECHNICAL_DEBT.md).
- [Logging contract](docs/data-contracts/LOGGING_V1.md), [threat model](docs/threat-model/THREAT_MODEL.md), and [P0 evidence report](docs/phases/P0_FOUNDATION.md).

P0 completion requires independent review and evidence for every applicable gate. A local run alone does not close the phase.
