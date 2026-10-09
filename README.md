# Card Market Tracker

Card Market Tracker (CMT) is a personal market intelligence project for collectibles. The initial domain is Pokémon TCG in Spain and Europe, using EUR. This repository starts with the [project context](context.md) and the [P0 Foundation contract](P0_FOUNDATION_CONTRACT.md).

P0 supplies an installable Python package, validated local configuration, a one-shot CLI diagnostic, structured logs, and container/CI scaffolding. It does not collect market data or run a service.

## Quick start

Requires Python 3.13 and uv 0.12.10. From the repository root:

```sh
uv sync --frozen --no-install-project
uv sync --frozen --no-build-isolation
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

## P1a offline catalog demonstration

The [authorized contract](docs/phases/P1A_CATALOG_CORE_CONTRACT.md) defines this
catalog slice. After frozen installation, run:

```sh
uv run --frozen cmt catalog --input tests/fixtures/synthetic_tcgdex_valid.json --manifest tests/fixtures/synthetic_manifest.json
uv run --frozen cmt catalog --input tests/fixtures/synthetic_tcgdex_mixed.json --manifest tests/fixtures/synthetic_manifest.json
docker compose run --build --rm catalog
```

`cmt catalog --input PATH --manifest PATH` reads UTF-8 regular files, performs
strict JSON validation, translates the modeled TCGdex subset offline, and
resolves only explicitly authorized references. Stdout is one deterministic
JSON object with version, result, counts, entities and indexed records.
Records distinguish `accepted`, `candidate`, `rejected`; candidates retain their
minimal external reference and provenance for review, with no canonical ID.
Accepted entities include their required parents, are unique and sorted by CMT
ID. Names, images, prices and provider payloads are omitted from output.
JSON stderr contains one allowlisted `catalog.completed` event with UUID run_id,
duration, outcome and counts when parsing completed. No source health is claimed.

| Exit | Catalog meaning |
| --- | --- |
| 0 | All records accepted, or a valid empty batch (`result=empty`) |
| 3 | At least one candidate or rejected record, including an entirely rejected batch |
| 2 | Invalid arguments, unreadable input/manifest, malformed JSON, invalid manifest or incompatible envelope; global failure has `counts=null` |
| 1 | Unexpected local execution failure, sanitized and explicitly unsuccessful |

Per file: maximum 1 MiB, nesting depth 16, 20000 structural nodes, 1024 characters
per string. Maximum batch records 1000, manifest entities 1000 and bindings 2000.
Duplicate JSON keys, nonfinite numbers, incompatible versions, broken relations,
identity collisions and contradictory bindings fail explicitly. Unknown language
or variant stays unknown. Availability flags never select a printing. ES/EN set
equivalence and multiple provider aliases require explicit manifest bindings.
Sealed is a separate domain kind with synthetic coverage, never inferred from
TCGdex boosters. The manifest is read only; IDs are preassigned UUIDv4 values
and are never generated from a provider ID or name.

The fixtures are synthetic, not captured provider responses. The
[field policy](docs/sources/TCGDEX_P1A_FIELDS.md) separates official documentation
from synthetic behavior and real-data rights. This operation makes no network
requests and writes no database or export file. No live collector, synchronization,
market, retail, scheduler or temporal Discovery is delivered. Real-data retention
is not approved by this synthetic demonstration.

Build with `uv build --no-build-isolation`, then run `sh scripts/wheel_smoke.sh`
on Linux. That smoke installs outside the source tree and checks all five catalog
cases plus P0. `scripts/catalog_smoke.py --mode docker` and `--mode compose`
exercise the same cases; CI requires both AMD64 and QEMU ARM64, Compose,
quality, coverage and security. See [P1a report](docs/phases/P1A_CATALOG_CORE.md)
and the PR evidence ledger for exact SHA results.

## Repository map

- [Architecture](docs/ARCHITECTURE.md), [standards](docs/CODING_STANDARDS.md), [tests](docs/TESTING_STRATEGY.md), and [quality gates](docs/QUALITY_GATES.md).
- [Operating model](docs/ENGINEERING_OPERATING_MODEL.md), [roadmap](docs/ROADMAP.md), [risks](docs/RISK_REGISTER.md), and [technical debt](docs/TECHNICAL_DEBT.md).
- [Logging contract](docs/data-contracts/LOGGING_V1.md), [threat model](docs/threat-model/THREAT_MODEL.md), and [P0 evidence report](docs/phases/P0_FOUNDATION.md).

P0 completion requires independent review and evidence for every applicable gate. A local run alone does not close the phase.
