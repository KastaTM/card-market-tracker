# Observation storage runbook

This runbook covers P3a's local synthetic catalog history. Use a disposable,
clearly identified data directory for drills. Never run a corruption, interruption,
permission or disk-full drill against an existing user database. The phase report
and PR ledger carry executed commands, environment and reviewed SHA; recipes in
this document are not gate results.

## Scope and operator responsibilities

Operate on one host with one writer at a time, using local storage and a directory
controlled by the operator. Keep input fixtures and the curated manifest separate
from writable data. Preserve the producer's UUIDv4 batch token across retries.
A different token denotes a different batch even when its observations are equal.
Keep explicit capture times; neither provider updates nor release dates establish
capture or first persistence. Local persistence time is scoped to the batch, not
the first appearance of a product.

Only authored synthetic records are allowed. A producer's `synthetic` declaration
does not prove origin or grant retention rights. Review fixtures and provenance.
Do not use SQLite availability to bypass blocked real market/retail sources or
their unresolved access, retention, deletion, analysis and display permissions.

Protect database and backup directories with host permissions. P3a has no remote
authentication or encryption layer. Host users able to modify a manifest or the
database remain trusted administrators; hashes and integrity checks do not
authenticate them. Use an operator-controlled directory without symlink/junction
ancestors or hostile concurrent path replacement. Review
[technical debt](../TECHNICAL_DEBT.md) before extending this deployment boundary.

## Commands and results

Use the installed `cmt` executable; from a development checkout prefix it with
`uv run --frozen`. The [input contract](../data-contracts/PERSISTENCE_V1.md) and
[storage contract](../data-contracts/STORAGE_V1.md) define accepted input/output.
`cmt catalog` remains a read-only P1a operation.

| Operation | Command |
| --- | --- |
| Initialize empty/current DB | `cmt db init --db PATH` |
| Commit synthetic batch | `cmt persist --db PATH --input INPUT --manifest MANIFEST` |
| Read bounded history | `cmt observations --db PATH --limit 100` |
| Read batch | `cmt observations --db PATH --batch-id UUID --limit 100` |
| Read accepted target | `cmt observations --db PATH --cmt-id UUID --limit 100` |
| Read candidate exact context | `cmt observations --db PATH --candidate-reference REFERENCE_JSON --limit 100` |
| Verify owned schema/integrity/FKs | `cmt db verify --db PATH` |
| Create consistent backup | `cmt db backup --db SOURCE --destination NEW_BACKUP` |
| Restore verified backup | `cmt db restore --db BACKUP --destination NEW_DB` |

Use at most one read filter and an integer limit from 1 to 1000. A bounded read
does not establish that no additional history exists. Results are ordered by
capture, batch UUID and input index; exact null candidate language is not a
wildcard. Reads of missing databases fail without creating a file.

| Exit | Meaning | Operator response |
| --- | --- | --- |
| 0 | Clean/empty operation or replay completed | Inspect JSON result; replay reports zero newly committed observations/entities. |
| 3 | New batch committed with candidates/rejections | Review safe counts and candidate evidence; no candidate promotion is available. |
| 2 | Input/capture/provenance/resolution/replay/identity conflict | Correct input or investigate stable token/manifest correspondence before retry. |
| 1 | Storage/schema/lock/IO/corruption/timeout/destination failure | Preserve data and resolve the categorized local failure before retry. |

On failure, counts and committed counts are unknown (`null`), not a successful
zero. JSON stderr includes stable event/category, run UUID, duration and permitted
counts; it omits input values, batch UUID, names, references, SQL, paths and raw
exceptions. Successful query stdout intentionally contains contracted normalized
metadata, including names and contextual references. Treat stdout as untrusted
data and protect any saved result with the same care as the database.

## Data directory and container preparation

Create a fresh private directory on a local filesystem. Its parent must already
exist. On Linux use owner-only directory access and the effective runtime owner;
on Windows check the directory ACL for the current user. Requested file mode 0600
does not replace Windows ACL administration. Do not use network shares or paths
controlled by another user. Database/backup destinations must be regular paths,
with no symlink/junction ancestors. Backup and restore require a destination that
does not already exist; an existing directory, link or alias is not a new target.

The image prepares `/data` owned by UID/GID 10001 with mode 0700 during build;
runtime remains UID 10001. Mount an explicitly named new Docker-managed local
volume at `/data`; keep fixtures at `/fixtures` read-only and data commands on
`--network none`. Docker volumes [survive container removal](https://docs.docker.com/engine/storage/volumes/).
Keep the same volume name across distinct invocations. Verify mounted ownership
and effective UID before writing. An existing nonempty volume obscures image
ownership and is not repaired by rebuilding the image; prepare a new owned volume
or have the operator correct the selected directory's permissions. Do not run the
product as root, use mode 777 or make the repository writable to resolve a mount.

For Docker Desktop on Windows, use Linux containers and a Docker-managed named
volume for data; host bind-mount permission semantics differ from native Linux.
The fixture bind mount must resolve to the checkout's `tests/fixtures` directory.
Compose uses an external volume selected by `CMT_PERSISTENCE_VOLUME`; create that
explicit volume before running its persistence service. Record the name used in
the drill. Cleanup may remove only the disposable volume created for that drill,
after all invocations complete; never prune arbitrary volumes or use `down -v`
as a recovery procedure.

The automated disposable volume drill runs from the checkout on Windows or Linux:

```powershell
docker compose build persistence
uv run --frozen python scripts/observation_persistence_smoke.py --mode compose --fixtures tests/fixtures
docker build --tag cmt-p3a-smoke .
uv run --frozen python scripts/observation_persistence_smoke.py --mode docker --image cmt-p3a-smoke --platform linux/amd64 --fixtures tests/fixtures
```

Each harness run creates a unique `cmt-p3a-smoke-<UUID>` named volume, supplies its
name to Compose, checks actual mounted ownership/mode, and removes only that
disposable volume when complete. Record the command/runtime output. ARM64 uses
the separate Buildx/QEMU gate recipe in `scripts/container_smoke.sh`; the default
local build above is not ARM64 evidence. For a retained operator volume, create a
new explicit name with `docker volume create NAME`, set
`$env:CMT_PERSISTENCE_VOLUME = 'NAME'` in PowerShell (or `export` in a POSIX shell),
then run separate `docker compose run --rm -T persistence ...` invocations with
the chosen CLI commands. Its default command verifies `/data/history.sqlite3`
and intentionally fails if that file has not been initialized.

## Disposable Windows walkthrough

Run from the checkout with frozen dependencies installed. This creates only a new
temporary directory; each command is a separate process. Preserve the directory
until its contents/results have been checked.

```powershell
$cmtDrillDir = Join-Path $env:TEMP ("cmt-p3a-drill-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $cmtDrillDir | Out-Null
$cmtDrillDb = Join-Path $cmtDrillDir "observations.db"
$cmtDrillBackup = Join-Path $cmtDrillDir "backup.db"
$cmtDrillRestored = Join-Path $cmtDrillDir "restored.db"
uv run --frozen cmt db init --db $cmtDrillDb
uv run --frozen cmt persist --db $cmtDrillDb --input tests/fixtures/synthetic_persistence_valid.json --manifest tests/fixtures/synthetic_manifest.json
uv run --frozen cmt observations --db $cmtDrillDb --batch-id 824d9220-d225-4d09-9964-6d33142408a7 --limit 100
uv run --frozen cmt persist --db $cmtDrillDb --input tests/fixtures/synthetic_persistence_valid.json --manifest tests/fixtures/synthetic_manifest.json
uv run --frozen cmt persist --db $cmtDrillDb --input tests/fixtures/synthetic_persistence_later.json --manifest tests/fixtures/synthetic_manifest.json
uv run --frozen cmt observations --db $cmtDrillDb --limit 100
uv run --frozen cmt db backup --db $cmtDrillDb --destination $cmtDrillBackup
uv run --frozen cmt db restore --db $cmtDrillBackup --destination $cmtDrillRestored
uv run --frozen cmt db verify --db $cmtDrillRestored
uv run --frozen cmt observations --db $cmtDrillRestored --limit 100
uv run --frozen cmt persist --db $cmtDrillRestored --input tests/fixtures/synthetic_persistence_valid.json --manifest tests/fixtures/synthetic_manifest.json
```

Inspect exit codes immediately (`$LASTEXITCODE`); each command above should return
0. The first valid batch commits seven observations. Its retry reports `replay`
and zero new rows with unchanged first persistence. The later capture adds seven
observations; history reads show fourteen in capture order. Restore retains the
same IDs, timestamps and replay behavior. A second backup to the same destination
must fail safely; choose a fresh path for each new recovery copy. Candidate/mixed
and rejected fixtures use exit 3 on first commit, while replay uses 0. Invalid and
conflicting-token fixtures must fail without changing the database.

For packaged and container evidence use the repository's
`scripts/observation_persistence_smoke.py` harness in its installed, Docker or
Compose mode. It creates disposable paths/volumes and asserts JSON contents,
history and replay; record its command/result at the tested SHA. Container mode
must use separate invocations sharing the same named data volume. Never regard a
single successful container process as proof that mounted data survives restart.

## Recovery discipline

Storage uses SQLite rollback journal `DELETE` and `synchronous=FULL`, with explicit
batch transactions and foreign keys enabled on every connection. The default SQL
operation/lock budget is two seconds and has no unbounded retry. Device/OS calls
that fail to return are outside the deadline guarantee. SQLite backup uses bounded
page steps and a deadline callback; direct copies of an open main file are not a
consistent backup procedure. See the [SQLite backup API](https://www.sqlite.org/backup.html).

| Category | Immediate action |
| --- | --- |
| `storage_locked` | Find the other writer/long reader; let it finish or stop it normally. Retry unchanged token/input after contention ends. Do not delete journals to break a lock. |
| `storage_timeout` | Reduce concurrent work and check storage responsiveness/size. A failed copy is not a usable backup. Investigate before changing operational budgets. |
| `storage_schema` | Confirm installed contract/schema version and selected file. Preserve it; future/foreign/altered schemas are rejected rather than reset. |
| `storage_corrupt` | Stop writers, preserve DB and journal, and restore a verified backup into a new path. No automatic repair is provided. |
| `storage_io` | Check current user, ACL/mode, mount writability, free space and device errors. Disk-full/IO may roll back the batch; verify/retry with the original token. |
| `unsafe_destination` | Choose a new regular destination in an existing trusted directory; remove no unrelated files to make the command succeed. |
| `replay_conflict` | Compare producer token, capture, normalized input and relevant manifest context. Rejections compare only safe category/index; aliases/identity context may change replay. |
| `identity_conflict` | Review curated IDs and relationships against persisted projections. Do not overwrite an existing identity or suppress the conflict with an upsert. |

A `DB-journal` may remain after interruption. Preserve it beside its database;
SQLite may need a writable directory to recover it. A read-only verification can
fail while hot-journal recovery is needed. Resume only through a compatible
writable operation in the trusted directory, then verify. Do not copy an open DB
alone, manually delete journals, or relabel a database's journal mode to bypass
compatibility checks. WAL mode is outside this design.

After an interrupted attempt, reopen and verify the database, then retry the same
batch token and unchanged input/manifest. A replay must report no new rows; a token
conflict needs investigation of the producer's evidence/context, not a fresh token
chosen solely to suppress the error. Do not treat attempted processing counts as
confirmed writes when an operation fails.

For suspected corruption or incompatible schema, stop writers and preserve the
original database and any journal files for investigation. Do not reset the schema,
delete journals or use an untrusted SQL dump as a repair. Restore a verified backup
into a separate new destination, verify it, and compare the expected batch,
canonical IDs, candidates and replay behavior before selecting it for later use.
Keep the original untouched. A failed/incomplete backup is not a recovery source.

Physical power loss can expose filesystem/device behavior beyond process tests.
Keep backups on a separately protected location when qualifying a deployment.
Native Pi interruption and soak validation remain P9.5 work; QEMU does not certify
storage hardware. SQLite's [atomic commit documentation](https://www.sqlite.org/atomiccommit.html)
describes the filesystem and hardware assumptions underlying its guarantee.

## Capacity and evidence

History is append-only and P3a has no automatic retention, deletion or disk quota.
Before a batch or backup, check free space on the relevant host/volume; backup and
restore need space for another database plus SQLite's transient work. Track file
growth and reserve operator time for periodic verified backups. Stop ingestion if
space becomes constrained; do not introduce an automatic destructive cleanup.
Any real-data retention policy needs source-specific authorization in its owning
phase.

For an incident, record the installed version, candidate commit, Python/SQLite
versions, operation, exit code, safe error category and run ID. Keep paths and
evidence values in a restricted local note when needed; logs deliberately omit
them. `diagnose` tests configuration/work-directory access only. A storage integrity
result is scoped to database compatibility/content; neither result assesses source
health, overall Pi health or commercial completeness.
