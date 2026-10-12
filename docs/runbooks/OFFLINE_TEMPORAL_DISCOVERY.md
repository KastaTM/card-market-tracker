# Offline temporal Discovery runbook

This runbook covers P4a's synthetic, local read-only comparison. Recipes and
described controls are not executed gate results. The
[phase report](../phases/P4A_OFFLINE_TEMPORAL_DISCOVERY.md) and PR ledger must
record reproducible commands, environment and reviewed commit before a gate
passes. Use only fresh disposable databases and specifically named test volumes
for failure drills; never tamper with a user database.

## Select an explicit evidence window

Run `cmt discover --db PATH --request REQUEST_JSON` using the installed wheel;
prefix with `uv run --frozen` in a development checkout. Discovery reads existing
P3a batches. It creates no database, schema, event, cursor or output file. Protect
saved stdout with the same host access policy as the database.

The request has exactly `version`, `current_batch_id`, `history_batch_ids` and
`context`. Use integer version 1 and canonical lowercase UUIDv4 batch IDs.
Context has exactly `namespace`, `kind`, `language`; null language is an exact
value. Every selected nonempty batch must match that context in every record;
mixed batches fail rather than being filtered. Variant remains part of each
full reference key. Select at most 32 distinct historical IDs, excluding the
current ID; every historical capture must be strictly earlier than current.
Historical captures may tie. The order of supplied history IDs is irrelevant.

Select batches intentionally: no history means explicit `baseline` with no
events. A valid historical window may contain existing empty batches. Novelty
means absent from the union of accepted and candidate references in that exact
selected window; changing the window can change the conclusion. A repeated
reference, candidate later accepted, or reference reappearing after an
intermediate empty capture is already seen if it remains in the supplied union.
A new reference to an already known CMT ID is not a new canonical product.
Names, release dates and provider update times do not establish reference identity.

## Empty context is an operator assertion

STORAGE_V1 retains empty-batch existence, counts and capture, but no empty capture
namespace/kind/language. Its `context_fingerprint` identifies the resolver/manifest
context; it does not prove capture scope. For every selected empty batch, the
request's exact context is an explicit caller/producer attestation. The result
labels this evidence `request_attested_empty`. Nonempty batches use
`records_verified` after validating all their records against the context.
Neither label authenticates the producer or administrator.

Confirm the original synthetic producer's intended scope before selecting an
empty batch. If its scope is unknown or disputed, stop that comparison and
preserve the evidence; do not relabel it to obtain a desired result. A mistaken
empty-scope attestation can generate false novelty. The database cannot detect
that mistake, and a matching manifest hash is not a substitute. Independently
persisted scope would require an Orchestrator-authorized later storage contract;
P4a adds no schema fields or extra request fields. See TD-005 in the
[debt register](../TECHNICAL_DEBT.md).

## Bounds and failures

The request reader permits at most 1,048,576 bytes, depth 16, 20,000 structural
nodes and 1,024 characters per string/key. Duplicate keys, nonfinite values,
invalid UTF-8, unknown fields and forged direct Python DTOs must fail explicitly.
Selected batches permit at most 1,000 records each, 33,000 total; output permits
at most 1,000 events. These are hard budgets: a truncated comparison is never
successful. Keep the finite global SQLite deadline; no unbounded retries.

| Exit | Meaning | Operator response |
| --- | --- | --- |
| 0 | `baseline`, `no_discoveries` or `discoveries` | Read the exact window and scope evidence before interpreting events. |
| 2 | Invalid request/context/chronology or incomplete/contradictory evidence | Correct the request or investigate producer evidence; do not omit a failed batch silently. |
| 1 | Local storage, ownership/schema, corruption, lock, IO or timeout failure | Preserve the database and journal; resolve the safe category before retrying the unchanged request. |

A referenced missing batch, nonzero rejection count, incompatible provenance,
count/index inconsistency or contradictory rows fails the entire operation with
no partial events. Candidates with zero rejections remain valid. Existing empty,
missing, failed, rejected and baseline are different states. Errors have unknown
counts, not zero successful discoveries. Identical repeated rows in one batch
collapse; incompatible same-reference rows cannot be resolved by choosing one.

The reader must use one SQLite `mode=ro`/`query_only` connection and one explicit
consistent read transaction for metadata and rows of every selected batch.
Ownership/schema, integrity, foreign keys and business evidence validation have
separate purposes: an integrity result does not authenticate scope, producer,
completeness or source health. The default two-second budget bounds ordinary
SQL/lock work; an unresponsive OS or device call is outside that guarantee.

## Local recovery and permissions

Use operator-controlled private local directories, owner-only Linux access and
appropriate Windows ACLs. P4a inherits the trusted-directory assumption and path
checks from P3a; they do not defeat a hostile administrator replacing an ancestor
concurrently. No SQL, URL, dump or extension supplied by the request is executed.
Discovery has no network source, remote authentication, encryption or delivery.

For `storage_locked`, allow the competing process to finish; retry only after
contention ends. For `storage_timeout` or `storage_io`, check device responsiveness,
permissions and capacity before retrying. For `storage_schema` or
`storage_corrupt`, stop writers, preserve the original and recover a verified
backup into a new destination through the
[storage runbook](OBSERVATION_STORAGE.md). Never initialize/reset a failed read,
delete a journal, import an untrusted dump or weaken permissions to bypass it.

A hot rollback journal can require writable recovery, so read-only Discovery can
fail even when recovery remains possible. It does not acquire write authority
to repair the file. Preserve the DB and journal, perform a compatible authorized
P3a recovery operation in the trusted directory, verify, then retry. Backups use
P3a's consistent backup API; copying an open main file alone is unsafe.

## Wheel and container evidence

The reproducibility drill must seed synthetic batches with installed P3a commands,
exit those processes, then invoke installed Discovery in another process. Verify
the full logical database contents, schema inventory and version before/after
comparison; a successful CLI invocation alone is not nonmutation evidence.
Replay and comparison against independently backed-up/restored databases must
produce equal semantic results and stable event IDs. Test the installed wheel
outside the checkout/PYTHONPATH.

Containers run as UID/GID 10001 with a private `/data` directory, networking
disabled and fixtures mounted read-only. Use a unique explicitly named disposable
local Docker volume and check the actual mounted UID/GID/mode; image ownership
alone does not establish existing volume permissions. Keep its name across
separate seed/compare/verify invocations. Do not run the product as root, chmod
777, mount the whole project writable, prune arbitrary volumes or use `down -v`
for recovery. Cleanup may remove only the disposable volume created for the drill.

Compose, linux/amd64 and linux/arm64 QEMU must retain Foundation, catalog and
persistence smokes while adding Discovery. Record Python/SQLite/QEMU versions and
the exact reviewed SHA. QEMU, process termination and simulated IO failures do
not establish native Raspberry Pi behavior or physical power-loss durability.
TD-001 through TD-004 remain open.

Run the checkout harness from the repository, selecting the installed wheel's
absolute executable path for installed mode. Its product subprocesses run outside
the checkout with PYTHONPATH removed. Example recipes (not results):

```powershell
uv run --frozen python scripts/discovery_smoke.py --mode installed --executable C:/PATH/TO/WHEEL-VENV/Scripts/cmt.exe --fixtures tests/fixtures
docker compose build discovery
uv run --frozen python scripts/discovery_smoke.py --mode compose --fixtures tests/fixtures
uv run --frozen python scripts/discovery_smoke.py --mode docker --image cmt-p4a-smoke:amd64 --platform linux/amd64 --fixtures tests/fixtures
```

Build the selected architecture image first through the mandatory gate recipe;
the Docker harness does not build or establish its provenance. ARM64 must select
its separate linux/arm64 image/platform and record QEMU evidence. The harness
creates only a unique `cmt-p4a-smoke-<UUID>` volume and removes that selected volume
after its invocations. A failed cleanup needs investigation of that name only.

## Interpret output and record incidents

Stdout contains only contracted minimal evidence: exact references, frozen
status/nullable CMT ID, explicit batch/capture/window and deterministic IDs; names,
raw payloads and ignored provider extras do not belong in Discovery results.
Treat references and all retained output as untrusted metadata. Events express
window-relative first observation, never launch, preorder, restock, withdrawal,
global first appearance, licensed real retention, source health or exactly-once
delivery. Reexecuting returns the same semantic events and sends nothing.

Correlated `discovery.completed` stderr must contain only fixed allowlisted result,
category, run ID, duration and bounded counts. It omits batch IDs, references,
names, paths, SQL, payloads and raw exception messages. Record the installed
version, reviewed commit, Python/SQLite versions, safe category, exit code and run
ID for an incident. Keep any needed paths/input evidence in restricted operator
notes. `diagnose` still measures configuration/work-directory access only.
