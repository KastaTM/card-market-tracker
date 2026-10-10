# Phase Completion Report — P3a Observation Persistence

Phase: P3a, contract v1, opened 2026-10-10 Europe/Madrid by the Orchestrator.
Proposed status at this committed snapshot: implementation complete; final
publication/review gates pending in the external delivery ledger. Only the
Orchestrator accepts/closes the phase. No merge authorized or performed.
Branch: `feat/p3a-observation-persistence`.
PR: [#6](https://github.com/KastaTM/card-market-tracker/pull/6).
Repository: `KastaTM/card-market-tracker`.

## Candidate and baseline

Authorized base `c6e66a2aba469d02f0ca63fde3b81ecc5eea41bc`, tree
`a9717922736a6220d3ff05293bec4cb222644269`. Initial clean checkout was
`feat/p1a-catalog-core` at `93a17711cb75f91816e41279fe76069055391e50`, same tree.
Local fetch verified remote main. Existing branches/user work were preserved;
P3a started from the authorized base. The attributed P1a closure/P3a opening is
recorded in [roadmap](../ROADMAP.md) and the later [P1a decision](P1A_CATALOG_CORE.md).
Historical PR5/main CI is baseline evidence, not a P3a gate.

Implementation independently reviewed/executed:
`4d8702ccfb4d3a93b6a1ae69ea5e164fe8602658`, tree
`ec8d37434409c57823fffe07ed3b815f6e4e6d8e`. Parent implementation:
`f43ce4b1c2e099cd4636c0e40f33c89c99fe1696`; the only intervening change renamed
one synthetic nested log-test key to remove a secret-scanner false positive.
Runtime/Docker/scripts/workflow/lock were equal. No suppressions/gate reductions.

Implementation PR CI [38088571440](https://github.com/KastaTM/card-market-tracker/actions/runs/38088571440)
passed all four jobs; their bodies were inspected. GitHub checked out temporary
merge `96fcef3698c1490a119b0793b7c39f6e463255b7`; fetched Git objects prove its
parents are authorized base then implementation head and its tree equals the
reviewed head. This is a PR test object, not an integration into main.

This report/ownership finalization creates a documentary successor. Its exact
head/tree/base, unchanged implementation proof, final independent reviews and
four-job CI bodies belong to the [external PR delivery ledger](https://github.com/KastaTM/card-market-tracker/pull/6).
Its own SHA is kept external to avoid circular commits. This snapshot's pending
final gates are superseded only by explicit exact-candidate evidence there.

## MODEL PROFILE USED and specialists

Root identifies as a GPT-6 based Codex agent; exact backend/reasoning is not
independently exposed. No client model change or separate ChatGPT execution is
claimed. The delegation tool offered and accepted the following explicit
`gpt-6.1-sol/high` requests. Accepted selection is observable; effective backend
execution is not introspectable. No Astra escalation occurred.

| Agent | Role / observed selection | Ownership / independence |
| --- | --- | --- |
| `/root` | Engineering Lead, exact backend/reasoning unverified | Git, CLI/logging, packaging/CI, shared docs/integration |
| `/root/storage_author` | ARQ + DB-OWNER + storage author, requested Sol/high | Combined ADR/contracts/schema/repository author |
| `/root/boundary_author` | BE/DATA, requested Sol/high | Input/application/models, fixtures/author tests |
| `/root/security_operations` | SEC + SRE, requested Sol/high | Supplementary design/runtime review; runbook/threats/risks/debt author |
| `/root/qa_final` | Independent QA, requested Sol/high | Separate clean detached worktree, source read-only, outside-source independent assertions |
| `/root/reviewer_final` | Independent REVIEWER, requested Sol/high | Different clean detached worktree, source read-only, independent review/probes |

[Ownership](P3A_OWNERSHIP.md) preceded delegation. Design/contracts/interfaces were
reviewed before dependent implementation. Earlier QA/REVIEWER attempts ended at a
client usage limit and supply no credited review. Final agents are distinct from
authors and each other; final documentary rechecks are recorded in the PR ledger.

## Objectives and implementation

Durable synthetic normalized catalog metadata and frozen resolution snapshots,
with the curated P1a manifest as identity authority. Accepted records retain
curated UUIDv4 targets and parent closure. Candidates retain exact contextual
reference/category/evidence without CMT ID or promotion. Invalid records retain
only indexed safe categorical summaries, never arbitrary payload/name/reference.

Version-1 wrapper requires producer UUIDv4 batch token and explicit capture.
Capture is UTC with fixed microseconds; wrapper/envelope/record disagreement fails.
Release date/provider update/capture/first local batch persistence remain distinct.
P1a capture stays optional. Composition retains normalized values omitted by
`BatchResult.to_dict()` and verifies resolution correspondence. Public repository
calls revalidate manually made dataclasses/manifests before file creation/retention.

One atomic transaction covers identity projections, batch, admitted observations
and rejection summary. Equivalent token/content/context returns `replay`, zero
new entities/observations and unchanged first persistence. Conflict fails without
overwrite. New token/later capture adds history despite unchanged values;
duplicates remain. Fingerprints cover versions, normalized evidence/order/nulls/
duplicates and conservative manifest identity/binding context, excluding canonical
localized names/audit reasons. Fingerprints check equivalence, never CMT identity.

Separate commands: `cmt persist`, `cmt observations`,
`cmt db init|verify|backup|restore`. Reads allow one batch/CMT-ID/exact candidate
reference filter, deterministic capture/token/index order, limit1..1000; missing
reads do not create a DB. Exit0 clean/empty/replay; 3 newly mixed/candidate/rejected;
2 invalid contract/replay/identity conflict; 1 local/storage failure. Error JSON
counts are null. `catalog` stays read-only; P0/P1a behavior/codes retain regression
coverage. README contains complete command examples.

## Architecture, ADRs and contracts

[ADR-0004](../adr/0004-offline-observation-persistence.md) adopts stdlib sqlite3,
consistent with ADR-0003. No new runtime dependency or lock change.
[PERSISTENCE_V1](../data-contracts/PERSISTENCE_V1.md) defines wrapper/public
validation/time/provenance/equivalence; [STORAGE_V1](../data-contracts/STORAGE_V1.md)
defines schema/reads/results/errors/transactions/recovery. Domain/resolver do not
import SQLite. The persistence application composes P1a normalization/resolution
and repository. Architecture, README, testing and gates reflect these boundaries.

## DATABASE CHANGES and migration

Initial schema1, application ID `0x434d5431`, four tables:
`storage_metadata`, `entities`, `batches`, `records`. Metadata/user version and
complete known SQL object inventory are checked before operating. Identity/unique/
snapshot checks, parent FKs and printing-context trigger enforce invariants.
Future/foreign/altered DB fails without reset. Empty initialization is atomic;
current version is no-op. Injected DDL failure rolls back tables/metadata/version.
No fictitious second migration, price/stock columns or user DB alteration.

Python3.13 explicit autocommit configuration and SQL
`BEGIN IMMEDIATE`/`COMMIT`/`ROLLBACK`; no executescript/upsert/replacement. FK enabled
and verified per connection; DELETE journal/FULL synchronization explicit.
One host/one writer, SQL/lock budget default2s/max5s with remaining busy timeout,
progress checks and backup deadline. Application budget cannot bound OS device
stalls. Reads/verification are read-only. Backup/restore use SQLite backup API,
verify schema/integrity/FKs and close/reopen before success. Destination must be
new/exclusive/owned. Existing files, hardlinks/reparse/linked ancestors, unsupported
paths and sidecar collisions fail. Failed copies remove only their reservation.

## Security, threat model, debt and observability

Synthetic-only write validation precedes rejection/retention. Documented/observed
fail. Synthetic is a trusted producer declaration, not proof of origin or rights.
Invented fixed-time fixtures have [provenance](../../tests/fixtures/PROVENANCE.md).
Bounded JSON/records/fields, independent revalidation, fixed/parameterized SQL,
disabled extensions, safe paths and restrictive creation address input/SQL/
poisoning/copy risks. Containers use UID/GID10001, /data0700, read-only fixtures,
network disabled; actual denied write to an unwritable path is tested.

[Threat model](../threat-model/THREAT_MODEL.md), risks R-03/04/05/06/10 and
[runbook](../runbooks/OBSERVATION_STORAGE.md) cover implemented controls,
lock/corruption/permissions/IO/recovery/growth. [Debt](../TECHNICAL_DEBT.md) retains
TD-001/002 and adds TD-003 trusted local directories (portable checks cannot defeat
hostile concurrent ancestor replacement) and TD-004 append-only capacity planning.

Logging v1 adds allowlisted `persistence.completed`, operation/result/category,
run_id/duration, processing and committed new-row counts. Replay differs from new
rows. Failure omits unconfirmed log counts; stdout counts null. Names, SQL, paths,
tokens, external references/raw exceptions cannot enter logs; legacy regressions
and hostile nested extras remain tested.

## Tests and environments

Exact implementation QA: 411 passed / one Windows symlink privilege skip;
97.54% own-runtime lines / 94.14% branches including persistence failure paths
(threshold85/80; no exclusions added). Windows junction/hardlink tests pass.
Frozen install/unchanged lock/Ruff format/check/strict mypy pass. Local runtime:
Python3.13.15 / SQLite3.53.1 / uv0.12.10. Linux CI also has 411 passed/1 skipped,
9.40s, same coverage; Linux runs symlinks and skips Windows junction test.

QA built sdist/wheel and installed outside source, empty PYTHONPATH, proven
site-packages import. P0 version/diagnose, five catalog smokes and distinct-process
persistence harness pass. Fourteen independently derived outside-source risk
assertion groups pass: UTC/provider clocks; equivalent offset/context/conflict;
provenance/forgery; raw rejected absence/UUID/FKs; duplicates/later history;
actual intermediate-write simulated IO rollback; child exit before/after commit;
copy/replay equivalence; unsafe destinations; missing/bounds/future schema;
finite150ms lock deadlines; safe CLI counters/redaction; sealed parent identity
collision/SQL-looking evidence; actual backup busy progress deadline/owned cleanup.
Socket creation was denied during installed runtime writes/replay. Script/evidence
live outside source under `.p3a-evidence/qa-outside`; path/hash/command in PR ledger.

REVIEWER independently installed/reviewed architecture/code/contracts/security/
SRE/docs/scope and ran 117 risk tests/one Windows privilege skip. Independent
probes pass forged-target rejection before DB creation, byte-preserving reads,
immutable old candidate after later manifest curation, copy/replay equivalence,
three sidecar collisions and expired-budget cleanup. Neither agent found blockers.
Final successor review is separate from these implementation conclusions.

Lead separately ran outside-source wheel, AMD64/ARM64 and Compose. Docker Desktop
client/daemon29.7.2; container Python3.13.16 / SQLite3.46.1, UID10001 /data0700.
CI observes QEMU10.2.3, binfmt/e29e7d7 (tonistiigi image digest
`sha256:400a4873b838d1b89194d982c45e5fb3cda4593fbfd7e08a02e76b03b21166f0`).
Local emulator implementation version is not exposed. Each disposable named-volume
harness verifies actual init/write/reopen/replay/later/mixed/empty/conflict,
synthetic-only refusal/bounds/integrity/backup/restore/existing-destination denial
across distinct non-root offline container invocations.

Reproducible CI recipes (Windows used equivalent installed-wheel/Docker harnesses):

```sh
uv sync --frozen --no-install-project
uv sync --frozen --no-build-isolation
uv run --frozen ruff format --check .
uv run --frozen ruff check .
uv run --frozen mypy src
uv run --frozen coverage run -m pytest
uv run --frozen coverage json -o coverage.json
uv run --frozen python scripts/check_coverage.py coverage.json
uv build --no-build-isolation
sh scripts/wheel_smoke.sh
uv export --frozen --all-groups --no-emit-project -o requirements-audit.txt
uv run --frozen pip-audit -r requirements-audit.txt
uv run --frozen python scripts/check_secret_scan.py
sh scripts/container_smoke.sh cmt-p3a-smoke:amd64 linux/amd64
sh scripts/container_smoke.sh cmt-p3a-smoke:arm64 linux/arm64
docker compose run --build --rm version
docker compose run --build --rm diagnose
docker compose build catalog persistence
python3 scripts/catalog_smoke.py --mode compose --fixtures tests/fixtures
python3 scripts/observation_persistence_smoke.py --mode compose --fixtures tests/fixtures
```

Evidence types are unit/contracts, SQLite integration, process interruption,
simulated IO/permission errors, P0/P1a regression and installed/container smoke.
No physical power cut/native Pi/licensed real source is claimed. Attached brief's
intentional Markdown hard-break spaces are preserved. Temporary DB/journals/
backups, independent worktrees and artifacts are ignored/untracked.

## Quality gates

Implementation PASS is tied to the SHA above. Documentary successor gates remain
FAIL until explicitly superseded by exact results in the external PR ledger.

| Mandatory gate | Result / evidence |
| --- | --- |
| Baseline / ownership / scope | PASS; Git objects/attribution/ownership/independent scope review |
| Frozen install / unchanged lock | PASS; both steps independently reproduced QA/REVIEWER and CI quality |
| Ruff format / lint / strict mypy | PASS; QA/CI, 36 formatted files/19 runtime files |
| Unit / contracts / SQLite / P0-P1a regression | PASS; QA and CI411 passed/one platform skip |
| Own-runtime coverage >=85/80 | PASS; QA/CI97.54% lines/94.14% branches |
| sdist / wheel / outside-source smoke | PASS; Lead/QA/CI, site-packages and P0/P1a/P3a assertions |
| Dependency audit / secret scan | PASS; independent QA/CI, no known vulnerabilities/candidates |
| ARQ / DB / SEC / SRE / docs | PASS; design checkpoint/specialist review/independent REVIEWER |
| AMD64 offline non-root durability | PASS; local and CI job114320124608, separate mounted-volume invocations |
| ARM64 QEMU offline non-root durability | PASS; local and CI job114320124615, actual contents and version/UID assertions |
| Compose offline non-root durability | PASS; local and CI job114320124542, legacy and persistence harnesses |
| Four implementation CI job bodies | PASS; run38088571440; quality114320124361 plus jobs above, equal PR-merge tree |
| Independent final documentary SHA QA/REVIEWER | FAIL pending clean exact-successor recheck/log review in PR ledger |
| Final successor four-job CI bodies | FAIL pending publication/run/log review in PR ledger |

## Acceptance criteria AC-O01–AC-O15

Tests below belong to reviewed implementation. Final readiness additionally
requires exact successor reviews/CI in the external ledger. Test files are
`tests/test_persistence_{input,input_forgery,storage,storage_backup,cli,logging}.py`;
packaged/container harnesses live in `scripts/`.

| AC | Result / concrete evidence |
| --- | --- |
| AC-O01 | PASS; baseline/tree/clean original checkout/preserved branches, ownership, attributed P1a closure/P3a opening in roadmap/report |
| AC-O02 | PASS; ADR-0004/PERSISTENCE_V1/STORAGE_V1; architecture review, domain/resolver independent of SQLite |
| AC-O03 | PASS; `test_identity_same_uuid_changed_relation_and_different_uuid_same_identity`, `test_database_enforces_required_snapshot_fields_and_foreign_keys`, QA UUID/parent probes |
| AC-O04 | PASS; `test_complete_metadata_survives_lossy_p1a_result`, `test_durable_normalized_snapshots_reopen_and_distinct_process`, wheel/Compose/AMD64/ARM64 actual-content assertions |
| AC-O05 | PASS; `test_replay_content_context_conflict_and_later_capture`, `test_order_capture_token_index_duplicates_and_target`, QA offset/context/first-time probes |
| AC-O06 | PASS; `test_safe_partial_candidate_rejected_and_empty_snapshots`, `test_distinct_batch_outcomes`, QA raw-rejection absence and immutable later-curation candidate probes |
| AC-O07 | PASS; `test_simulated_failure_after_real_intermediate_write_rolls_back_entire_batch`, `test_process_termination_before_or_after_commit_recovers_coherent_state`, QA child-exit/simulated IO assertions |
| AC-O08 | PASS; `test_initialization_ddl_version_metadata_rollback_and_current_noop`, `test_incompatible_owned_schema_is_rejected_without_reset`, `test_each_connection_fk_full_delete_and_read_only_mode` |
| AC-O09 | PASS; finite writer-lock/reader-contention/total-deadline/corrupt/missing/permission tests, actual non-root container denied write, QA150ms write/backup probes |
| AC-O10 | PASS; `test_backup_restore_reopen_exact_content_ids_candidates_replay`, committed snapshot/busy deadline/owned cleanup/hardlink/junction/sidecar tests, independent copy/replay probes |
| AC-O11 | PASS; outside-source wheel, local/CI Compose/AMD64/ARM64, UID10001/data0700, network disabled/read-only fixtures/distinct invocations |
| AC-O12 | PASS; persistence CLI/logging tests and P0/P1a logging regression, QA hostile error/null-count/redaction/replay metrics |
| AC-O13 | PASS; synthetic-before-rejection/provenance fixtures, SEC review, hostile SQL/forgery/resource/path checks, provenance/trust limitation |
| AC-O14 | FAIL for final delivery pending successor CI; implementation suite/coverage/quality/wheel/audit/scan/regression and four CI job bodies PASS |
| AC-O15 | FAIL for final delivery pending successor rechecks; independent implementation QA/REVIEWER PASS, report/contracts/runbook/risks/debt/roadmap delivered |

## Limitations, open issues and recommendation

No blocking implementation finding. Remaining final-delivery gates above are
FAIL until the PR ledger supplies exact-successor evidence. Only then propose
`READY_FOR_ORCHESTRATOR_REVIEW`; acceptance/closure/merge remain Orchestrator
choices. No merge, protection changes or new phase have been performed.

P2 remains BLOCKED for EUR access/semantics/retention; P6a/retail Discovery BLOCKED.
TCGdex remains provisional; synthetic does not certify coverage/rights. No live
feeds/HTTP, price/stock, scheduling, promotion, analytics, alerts or API/UI.
Generic validated sealed data does not introduce a retail adapter.

Producer must retain its token for retries. Conservative manifest equivalence
can require new tokens after unrelated binding changes. Trusted safe RecordError
summaries cannot reconstruct discarded invalid payload. FULL/process recovery
assume honest storage; QEMU/simulations do not certify physical Pi power loss.
Trusted directories (TD-003) and future capacity planning (TD-004) remain; audit is
point-in-time. Effective model backend/local QEMU version are unverified.
