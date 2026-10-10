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

## P3a offline observation persistence

P1a is accepted and closed by the Orchestrator; the
[P3a contract](docs/phases/P3A_OBSERVATION_PERSISTENCE_CONTRACT.md) authorizes
only synthetic offline metadata history. The curated manifest remains the
identity authority. SQLite stores immutable accepted/candidate evidence,
resolution snapshots and safe rejection summaries; candidates have no CMT ID.
No real feed, price/stock data, promotion or commercial retention is authorized.

For a new disposable database in an existing private directory:

```sh
uv run --frozen cmt db init --db demo.sqlite3
uv run --frozen cmt persist --db demo.sqlite3 --input tests/fixtures/synthetic_persistence_valid.json --manifest tests/fixtures/synthetic_manifest.json
uv run --frozen cmt observations --db demo.sqlite3 --limit 100
uv run --frozen cmt persist --db demo.sqlite3 --input tests/fixtures/synthetic_persistence_valid.json --manifest tests/fixtures/synthetic_manifest.json
uv run --frozen cmt persist --db demo.sqlite3 --input tests/fixtures/synthetic_persistence_later.json --manifest tests/fixtures/synthetic_manifest.json
uv run --frozen cmt db verify --db demo.sqlite3
uv run --frozen cmt db backup --db demo.sqlite3 --destination demo-backup.sqlite3
uv run --frozen cmt db restore --db demo-backup.sqlite3 --destination demo-restored.sqlite3
```

The first batch commits seven observations and their curated parent identities.
Retrying the same producer UUID with equivalent normalized input/manifest context
returns `replay`, zero new rows and the original first-persistence timestamp.
The later capture adds another seven observations even with equal metadata.
Changed evidence/context under the old token fails without overwriting history.
Use a new token for each new capture and preserve it during retry; a lost token
cannot be deduplicated automatically. Capture is required explicitly at this new
write boundary and remains separate from release, provider update and first local
persistence. Existing `cmt catalog` semantics remain read-only and unchanged.

`observations` accepts at most one of `--batch-id UUID`, `--cmt-id UUID` or
`--candidate-reference PATH` (an exact INGESTION_V1 reference JSON object), with
limit 1..1000 and deterministic capture/batch/index order. Missing DB reads create
nothing. Successful stdout contains normalized metadata, including observed names
and contextual references; stderr logs only operation, run UUID, outcome, duration,
fixed category and safe counts. Errors report `counts=null, committed=null`.
Exit 0 means completed/empty/replay, 3 newly committed incomplete batch, 2 input
or replay/identity conflict, 1 local/storage failure. Backup/restore only accept
a new destination and verify schema, SQLite integrity and foreign keys.

Docker data commands run as UID/GID 10001 with private `/data`, a named volume,
read-only fixture mount and networking disabled. With Linux Docker Desktop:

```sh
docker compose build persistence
docker volume create cmt-p3a-local
docker compose run --rm persistence persist --db /data/history.sqlite3 --input /fixtures/synthetic_persistence_valid.json --manifest /fixtures/synthetic_manifest.json
docker compose run --rm persistence observations --db /data/history.sqlite3 --limit 100
```

These are distinct containers using the same data volume. A custom external
volume is selected with `CMT_PERSISTENCE_VOLUME`; existing volumes must already
have appropriate ownership. The smoke harness creates its own disposable volume,
checks actual mounted UID/mode and content, and cleans up only that volume:

```sh
uv run --frozen python scripts/observation_persistence_smoke.py --mode compose --fixtures tests/fixtures
```

See [ADR-0004](docs/adr/0004-offline-observation-persistence.md),
[persistible input](docs/data-contracts/PERSISTENCE_V1.md),
[storage/read contract](docs/data-contracts/STORAGE_V1.md),
[storage runbook](docs/runbooks/OBSERVATION_STORAGE.md) and
[P3a report](docs/phases/P3A_OBSERVATION_PERSISTENCE.md) for exact evidence and
Windows/permissions/recovery recipes. SQLite uses DELETE journal, FULL sync,
explicit transactions and a two-second SQL/lock budget. Trusted local directories
are required; OS/device stalls, hostile administrator path replacement, native Pi
power loss and unlimited history growth remain operational limits.

## Repository map

- [Architecture](docs/ARCHITECTURE.md), [standards](docs/CODING_STANDARDS.md), [tests](docs/TESTING_STRATEGY.md), and [quality gates](docs/QUALITY_GATES.md).
- [Operating model](docs/ENGINEERING_OPERATING_MODEL.md), [roadmap](docs/ROADMAP.md), [risks](docs/RISK_REGISTER.md), and [technical debt](docs/TECHNICAL_DEBT.md).
- [Logging contract](docs/data-contracts/LOGGING_V1.md), [threat model](docs/threat-model/THREAT_MODEL.md), and [P0 evidence report](docs/phases/P0_FOUNDATION.md).

P0 completion requires independent review and evidence for every applicable gate. A local run alone does not close the phase.
