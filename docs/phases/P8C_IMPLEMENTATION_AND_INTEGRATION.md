# P8c Implementation and Integration - candidate record

> RW-01 (2026-10-28): Orchestrator REWORK_REQUIRED, accepted by Phase Lead.
> Prior readiness for360da646/tree3ce94d6e is suspended. Historical evidence below
> remains intact; corrected candidate evidence belongs to P8C_RW01_CORRECTIVE_IMPLEMENTATION.md
> and the new PR18 ledger. No merge or phase closure.

Date: 2026-10-27. Phase OPEN / IMPLEMENTATION AUTHORIZED. Design accepted by
Phase Lead only. No merge authorization; only Orchestrator accepts/closes.
This committed record describes implementation and the reproducible validation
plan. The PR evidence ledger supplies the final candidate SHA/tree, actual CI
results, independent attestations and final AC disposition. Pending evidence
below is not PASS. Historical PR17/main CI is not P8c evidence.

## Authority and verified baseline

Authorized worktree: C:/Projects/card-market-tracker-p8c.
Branch: feat/p8c-watchlist-signal-outbox.
Baseline/main: 228d5c8d0d91edf03ddb86a489c8232eeb7c08bc.
Tree: dde865b6d215efc4075918088d6deddfe7cdeb1f.
Ordered parents: 62ecd7ab792a93a6071b83277d870f1d95f61f9f,
f80bc8cdb877946f37d76b09212d68dd8da3e246.
Preflight inspected origin, local/live main, branches, all35 worktrees and clean
original/phase checkouts. Existing branches/worktrees were preserved. Original
checkout remains rework/p5b-rw03-publication-rollback at f80bc8cdb877946f37d76b09212d68dd8da3e246.
Git ownership exceptions are invocation-specific, never global or wildcard.

Frozen SHA256 values remain unchanged:

| Document | SHA256 |
| --- | --- |
| ADR-0014 | 79d2194800d3ae2e88b35669ff2cd6b8603d99210d25c6dccaa723292c6debd3 |
| API V1 | acc47dcb491841851544db11da96dd58b4bb23f174a09a966207e9fa24ceae31 |
| Storage V1 | 60aa73f5d12f3f6cc3df5c509f5a094fe71083e6808fd00c0fe740738b313ebf |
| Normative Orchestrator contract | e5af71ad901460abc5bdff1474c7230eaa781d70c2f67c46dd0ec43a70223e14 |

The archived normative contract is byte-identical to the validated handoff.
Handoff proposed design documents were not evidence of execution/adoption.
The subsequent Phase Lead design freeze acceptance authorizes this design.
Handoff ZIP SHA256: 0478ee545a470b16c2a4a3ce1b9483c467dc1aaacfde60cdbca908ef89ad703e.

## MODEL PROFILE USED and ownership

Requested Lead: gpt-6.1-sol/Medium, High for critical decisions. Root selection
and effective effort are not independently exposed; no selector change claimed.
Specialist spawn selector arguments gpt-6.1-sol/high are observable. Effective
backend/model execution cannot be independently verified. ChatGPT Phase Lead
profile is supplied by the user, not independently measured here.

See [ownership](P8C_OWNERSHIP.md). Actual separate sessions:
ARQ/BE and DB-OWNER authored disjoint product/test files; SEC/SRE read only.
Independent QA and a distinct REVIEWER authored only their respective probe
scripts. Neither authored product or author tests. Root owns shared integration,
CLI, logging, harness/CI, documentation, Git and evidence publication.
All author files were relinquished before sequential integration.
The reviewer deadline findings were corrected by their product owners.

## Implemented behavior

New watchlist_alerts package prepares exactly one explicit original P5b signal
for one local alias. It retains immutable semantic evidence, intent, deterministic
synthetic plaintext and digests. A private receipt is bound to content, instance,
issuing Budget and one consumption; caller DTOs/hashes confer no authority.
Every enqueue, including ancient replay, reads and validates the complete
manifest, exact P5a revision and deeply verified original P5b journal.
The sole earlier-owner extension is a minimal additive read-only P5b bundle
reader using one accepted full fold and one transaction. Prior writers,
schemas, evaluators, identities and transition logic remain unchanged.

CMTY application_id0x434d5459, schema1, exact frozen SQL: ten statements,
three tables, four indexes and six triggers. Intention/evidence commit together
under BEGIN IMMEDIATE. Writer checks the existing physical SQLite owner/version
before any writable open, then validates the complete schema in transaction.
Replay preserves bytes/cardinality/first timestamp. Two processes give one
recorded and one replayed result. Crash probes cover between inserts, after
commit and link-before-unlink publication.

Verify is a local semantic fold; recompute separately reopens original sources.
Local validity does not authenticate a producer or prove original existence.
Backup/restore use source/copy/reopened-copy independent folds, one Budget,
fsync and exclusive link publication. Safe compensation removes only owned
links and preserves original failures/replacements/recovery evidence.

CLI provides init, enqueue, get, list, evidence-get, preview, verify, recompute,
backup and restore. Default2/max5-second cooperative budget covers parsing,
admission, storage, recovery and output. P5a get is unchanged and bracketed by
parent checks. Final output checks its deadline immediately before stdout, followed by one
completion log. Logging cannot retroactively alter an emitted response.
JSON/errors/counts are strict and redacted. P8c help/error/success routes do not
import Telegram transport or call sockets.

## Validation and reproducible commands

Native environment: Windows, managed CPython3.13.15. Frozen uv installs use
--no-cache; existing cache/ACL/owners/configuration were not repaired or changed.
Use the local .venv interpreter, or uv run --frozen in the prepared environment.

    uv --no-cache sync --frozen --no-install-project
    uv --no-cache sync --frozen --no-build-isolation
    uv run --frozen ruff format --check .
    uv run --frozen ruff check .
    uv run --frozen mypy src
    uv run --frozen coverage run -m pytest
    uv run --frozen coverage json -o coverage.json
    uv run --frozen python scripts/check_coverage.py coverage.json
    uv run --frozen python scripts/p8c_identity_oracle.py --check
    uv run --frozen python scripts/p8c_qa_probe.py --fixtures tests/fixtures --timeout 5
    uv run --frozen python scripts/p8c_reviewer_probe.py --fixtures tests/fixtures --timeout 5
    uv build --no-build-isolation
    sh scripts/wheel_smoke.sh
    uv --no-cache export --frozen --all-groups --no-emit-project -o requirements-audit.txt
    uv run --frozen pip-audit -r requirements-audit.txt
    uv run --frozen python scripts/check_secret_scan.py

Windows may use .venv/Scripts/python.exe -m COMMAND instead of uv run, with
.venv/Scripts on the process-local PATH for detect-secrets. Final unfiltered suite,
coverage, fresh builds and all four jobs must be bound to the exact reviewed
SHA/tree. No collection filters, new skips, threshold reductions or broad scanner
exceptions are authorized.

Development evidence:73 ARQ author tests,72 DB/recovery/process author tests,
28 CLI tests passed after the described fixes. Preliminary installed external
wheel ran all12 harnesses successfully; final wheel/remote gates remain separate.
Dependency audit found no known vulnerabilities. Secret scan found no unreviewed
candidates and used existing exact public-digest exceptions, unchanged.
Ruff/mypy passed during integration; final commands/results belong to the ledger.

Independent probes are complete standalone public source:

- [QA](../../scripts/p8c_qa_probe.py): own stdlib identities/results/renderer;
  five checkpoints/four signals,101 assertions and three fresh guarded CLI cases,
  original/replay/alias/revision/series/product isolation, forged receipts,
  coherent corruption, local-vs-origin distinction and recovery folds.
- [REVIEWER](../../scripts/p8c_reviewer_probe.py): own fixtures/renderer/identity,
  foreign hot-journal preservation, genuine owned recovery, receipt Budget,
  distinct recovery folds, publication disk-full, original absence and the
  first-stdout-byte deadline regression. Actual final attestation is a separate review.
- [Identity oracle](../../scripts/p8c_identity_oracle.py) and
  [literal vectors](../../tests/fixtures/p8c_identity_vectors_v1.json).

The probes are additive quality-job steps; they do not replace the full suite.

## Four CI jobs and twelve harnesses

Mandatory jobs: quality, container(linux/amd64), container(linux/arm64 via QEMU),
compose. Workflow shape and previous eleven harnesses remain intact; twelfth
watchlist_alert_outbox_smoke is added to wheel/container/Compose drivers.
All12 must pass in each required environment. New harness uses the full normal
five-checkpoint/four-signal scenario, separate CLI processes, replay,
preview/recompute and backup/restore. Runtime networking is disabled/guarded and
container private stores are owned by UID10001.

Local Docker build/info attempts failed even with punctual escalation because
the dockerDesktopLinuxEngine pipe was absent. No image/container was created.
This differs from the user's earlier recovered server29.7.2 diagnostic.
Local Compose/AMD64/ARM64 are BLOCKED until a functioning endpoint exists.
No local QEMU timing claim is made; three backup and restore timing controls
could not run locally. CI ARM64/QEMU remains mandatory and is not physical Pi
certification. No same-SHA CI rerun is permitted after failure without approval.

## AC evidence map - before final candidate review

All rows currently BLOCKED for final acceptance pending exact committed
candidate, final four-job evidence and independent attestations. This map names
reproducible checks rather than equating file existence/test count with PASS.

| AC | Status at integration record | Evidence/command to bind in final ledger |
| --- | --- | --- |
| AC-WA01 | BLOCKED | baseline/preflight and frozen hashes above; dated ROADMAP and archived contract |
| AC-WA02 | BLOCKED | test_watchlist_alert_application/source; QA original-manifest/revision matrix |
| AC-WA03 | BLOCKED | source tests and QA one-held-connection/one-fold, receipt adversarial checks |
| AC-WA04 | BLOCKED | domain/storage tests, QA independent complete snapshot/result reconstruction |
| AC-WA05 | BLOCKED | identity oracle --check, three literal independent QA vectors |
| AC-WA06 | BLOCKED | domain/application tests, QA aliases/rules/episodes/revision/series/product cases |
| AC-WA07 | BLOCKED | application/storage tests, QA ancient replay + invalid original byte preservation |
| AC-WA08 | BLOCKED | test_watchlist_alert_concurrency and storage rollback checks; real child processes |
| AC-WA09 | BLOCKED | domain exact-message golden/escaping tests; own QA/REVIEWER plaintext oracles |
| AC-WA10 | BLOCKED | storage corruption tests; QA coherently rehashed result rejection |
| AC-WA11 | BLOCKED | source/application tests; QA local-valid/original-mismatch and missing originals |
| AC-WA12 | BLOCKED | CLI/storage pagination/bounds/deadline tests; REVIEWER late-logging regression |
| AC-WA13 | BLOCKED | recovery tests and independent QA/REVIEWER three-fold/publication probes |
| AC-WA14 | BLOCKED | guarded fresh CLI, prior-source byte assertions, foreign hot-journal regression |
| AC-WA15 | BLOCKED | CLI logging allowlist/privacy tests; secret scan and updated threat model |
| AC-WA16 | BLOCKED | all12 harnesses in external wheel/Compose/AMD64/ARM64 final job logs |
| AC-WA17 | BLOCKED | full quality job: format/lint/mypy/tests/85%line+80%branch/build/audit/scan |
| AC-WA18 | BLOCKED | distinct QA+REVIEWER final exact-SHA/tree reruns and public source/results |
| AC-WA19 | BLOCKED | unchanged freezes; architecture/logging/threat/runbook/testing/roadmap/ownership |
| AC-WA20 | BLOCKED | final PR report/readback, four full logs and preserved failures; no merge |

## Preserved failures and residual limits

- Historical connected GitHub branch creation HTTP403 preceded this local work;
  no remote write was claimed for that attempt. Local authenticated git/gh is
  independently available; actual publication result must be recorded.
- An initial developer-only harness attempt failed its installed-package prefix
  guard; the guard was retained and an external wheel installation then passed.
- Initial combined/full Windows test runs hit excessive automatic pytest IDs
  in PYTEST_CURRENT_TEST; payloads retained, explicit short IDs fixed setup.
  Earlier full run:2145PASS,1skip,2setup errors; not a passing gate.
- Initial secret scan invocation lacked .venv/Scripts in PATH. Correct local
  environment produced PASS without changing scanner or allowlist.
- DB author reproduced foreign hot-journal recovery before owner rejection
  (FAIL); header precheck fixes it and preserves genuine owned crash recovery.
- Reviewer reproduced logging exhaustion followed by incorrect stdout ok
  (FAIL); final parent check immediately before stdout yields storage_timeout on
  pre-output expiration, then one completion log follows the response. Root
  retained the initial failure, interim fix and final affected-suite results.
- Reviewer identified post-P5a-get check after normalization rather than
  immediately after return. Author's2failure-first cases caught this; new
  private P8c reader now checks immediately, preserving earlier APIs.

These failures stay historical failures, not overwritten by later successful
attempts. Raw local logs stay in ignored .p8c-evidence; sanitized public records
and complete final CI logs must be linked by the PR evidence ledger.

Trusted immutable origins/directories are assumed. No global multi-DB atomic
snapshot, authenticated producer, global dedup, delivery consent, hostile-admin
resistance or tested physical power-loss guarantee is claimed. OS stalls/stdout
cannot be hard-preempted; a postcommit error may leave a complete valid result.
Preview-only restores do not affect Telegram quarantines. No new scope/debt
concession is introduced; P5 global and TD-001..005 remain OPEN.
