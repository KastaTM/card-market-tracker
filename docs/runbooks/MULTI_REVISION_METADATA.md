# Offline multi-revision metadata workflow

Use installed package resources and trusted local directories. R0 is preserved
at its original capture; R1 is the separately reviewed package acquired under
the P1c bounded source budget. Runtime commands below perform no acquisition.
Do not edit package clocks, revisions or projection to obtain a discovery.

The binding contracts are [bundle v2](../data-contracts/PINNED_REPOSITORY_BUNDLE_V2.md),
[Discovery v3](../data-contracts/DISCOVERY_V3.md) and
[ADR-0008](../adr/0008-multi-revision-metadata-capture.md).

## Admit and inspect

Obtain the minimum R0/R1 JSON files from the installed distribution or the
reviewed resources. Use explicit canonical UUIDv4 batch tokens and a reviewed
local manifest. Empty bindings keep all four projections as candidates; coherent
curated set bindings accept sets while cards remain unknown_variant candidates.

```text
cmt bundle-v2 verify --input R0_JSON
cmt bundle-v2 verify --input R1_JSON
cmt bundle-v2 import --db DB_PATH --input R0_JSON --manifest MANIFEST_JSON --batch-id R0_UUID
cmt bundle-v2 import --db DB_PATH --input R1_JSON --manifest MANIFEST_JSON --batch-id R1_UUID
cmt captures --db DB_PATH --batch-id R0_UUID
cmt captures --db DB_PATH --batch-id R1_UUID
cmt db verify --db DB_PATH
```

Import appends atomically to schema2. Import to an existing schema1 DB requires
the previously accepted explicit backup/migration workflow first; these commands
do not introduce a migration. The schema remains five tables. A successful mixed
import exits3 when candidates are retained; this is expected for the real card
units. Verification/replay or all-accepted success exits0. Admission/input errors
exit2, local/storage errors exit1. Check the JSON result and committed counts.

Reusing the same token and exact retained context/evidence returns replay with
zero new writes. R0 replay is compatible across bundle and bundle-v2. Another
revision/package/manifest under that token conflicts. New insertion time never
changes the original capture timestamp. Source queries, capture queries,
verify and backup/restore reconstruct the retained authorized variant.

## Compare one exact unit

Create a local request replacing both illustrative tokens with imported tokens:

```json
{
  "version": 3,
  "profile": "tcgdex_swsh3_136_r0_r1_v1",
  "context": {"namespace": "tcgdex_repository", "kind": "set", "language": "es"},
  "current": {"batch_id": "bd9cc4b8-eace-4567-8364-93cc4eccddc5", "selector": "swsh3"},
  "history": [{"batch_id": "5f423499-65a0-48bb-81af-13c3497c0093", "selector": "swsh3"}]
}
```

```text
cmt discover-multi-revision --db DB_PATH --request REQUEST_JSON
```

Current must be R1 and history R0. Repeat for set es/en with selector swsh3 and
card es/en with selector swsh3-136. Every real comparison returns version3,
no_discoveries and zero events: the authorized projections are unchanged.
Current/history acquisition evidence shows distinct revision, package digest
and original times. This does not establish changed metadata, a new product or
a commercial transition.

Empty history requests produce baseline after complete validation. Inverted
R1-to-R0 history and reimported equal-time packages fail chronology. Discovery v2
retains its R0 policy and rejects R1 even for baseline; v1 remains synthetic-only.
The synthetic_multi_revision_v1 profile is separate and permits only explicitly
synthetic/producer_declared fixtures. Never relabel modified real data synthetic
to claim another approved observed capture.

Success exits0. Invalid profile/selection/chronology/incomplete or unsupported
evidence exits2; storage/schema/corruption/lock/deadline/IO exits1. Version3 errors
have counts null and events empty. An error is not no_discoveries. Preserve
journals and diagnose failures using verified backups; comparison performs no
repair, migration, creation or writes.

## Operational checks

Read budget defaults2 seconds, Python maximum5. One explicit read-only
transaction validates the complete window, including unselected units. At most
32 historical/33 total batches, 1000 rows per batch, 33000 rows and 1000 events
apply. Whole-database integrity work shares that budget. Readers may delay a
rollback-journal writer's commit; stalled OS/device calls are outside deadline
guarantees. No retry should silently broaden selection or skip verification.

Protect stdout, DB and backups: stdout contains contracted tokens, references,
paths and capture locks. Structured stderr logs expose only safe operations,
categories, counts and correlation. Engineering timestamps are ledger-supported
local declarations, not authenticated provider clocks. Local reviewed-package
equivalence does not establish source availability, total coverage or product
truth. No events are stored or delivered.

Build/install the wheel outside the checkout and run the sixth multi-revision
smoke harness with that installed environment's Python:

```text
python scripts/multi_revision_metadata_smoke.py --mode installed --fixtures ABS_FIXTURES_PATH
python scripts/multi_revision_metadata_smoke.py --mode compose --fixtures ABS_FIXTURES_PATH
python scripts/multi_revision_metadata_smoke.py --mode docker --image IMAGE --platform linux/amd64 --fixtures ABS_FIXTURES_PATH
python scripts/multi_revision_metadata_smoke.py --mode docker --image IMAGE --platform linux/arm64 --fixtures ABS_FIXTURES_PATH
```

Keep the five existing harnesses. The new harness exercises separate import/read/compare/replay/
backup-copy/reopen processes, the four real zero-event units, synthetic positives,
old-version guards, recovery equivalence and no-network runtime. Verified
backup/restore operations may explicitly use the existing public Python API's
5-second budget in isolated harness processes. CLI and ordinary reads retain
their 2-second defaults; no verification or earlier harness is skipped.

Compose and linux/amd64 plus linux/arm64 container modes require fixtures
read-only, network disabled, UID/GID10001 and private disposable data volumes.
Remove only harness-owned volumes. ARM64/QEMU is emulation and does not certify
physical Raspberry Pi or electrical power-loss durability. Record actual
candidate SHA/tree, commands and results; these instructions alone establish no
gate PASS.
