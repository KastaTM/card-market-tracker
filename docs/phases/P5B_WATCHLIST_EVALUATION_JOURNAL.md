# P5b engineering candidate and evidence protocol

Phase OPEN. Implementation scope is complete; final execution results, immutable
HEAD/tree, PR/run URLs and the two independent reports belong to the external PR
evidence ledger. This versioned report is part of the candidate being checked;
it does not certify checks that have not run. Only all applicable green gates
permit READY_FOR_ORCHESTRATOR_REVIEW. Merge/acceptance/closure are not authorized.

## Baseline and implementation

Repository KastaTM/card-market-tracker; branch
`feat/p5b-watchlist-signal-journal`; exact base
`ddd5fe3bbc7e40947bd838f71ee25e7046ff1b7e`, tree
`f0eaf874e8671f75904ece1f618c283d7ff91536`, ordered parents
`d1038df1625a9727b44760866266b7124bb1d91a` then
`02ab89677afe11901ea5a2b1b8826604ce543c2f`. Local status was initially clean;
all branches/worktrees were inspected and preserved. Live main matched before
branch creation and during implementation. See [freeze](P5B_DESIGN_FREEZE.md)
for exact bundle/identity/SQL provenance. The opening contract is archived verbatim
with Git text conversion disabled. Roadmap's new top entry attributes P5a closure
and P5b opening to the supplied Orchestrator chat, preserving historical records.

New package `watchlist_journal` implements original full-manifest/exact-revision
admission, complete normalized synthetic snapshots, deterministic wjs1_/wje1_/
wsig1_ identities and per-rule fresh NO_MATCH-to-MATCH transitions. The first
record is signal-free even when MATCH. Exact ancient replay preserves the original
persisted_at and head. Explicit previous must equal the recorded predecessor;
observed_at advances strictly, as_of never regresses and sample IDs cannot be
reused for different content. Entry equality for the same watch/revision spans
all synthetic series. Unknown/stale/SKIPPED/INDETERMINATE break continuity.

CMTQ/schema1 owns four STRICT tables, eleven indexes and eight triggers. Under
BEGIN IMMEDIATE, storage revalidates the snapshot, recalculates P5a results,
checks replay/current head, derives exact signals and commits evaluation/signals/
head together. Deep read-only verification reconstructs all snapshots/results,
links/ordinals, exact signals and heads; result hashes are not verdict authority.
Explicit original-backed recompute separately reopens P5a and full manifest.
Verified exclusive backup/restore publishes a new inode only after full copy
verification/reopen/fsync. All prior packages, DB schemas, identities and the
lockfile are preserved; root CLI registration/logging are additive only.

The CLI is `cmt watchlist-journal init|record|get|list|signal-get|signal-list|
verify|recompute|backup|restore`, with explicit paths/IDs/revision/as_of. Inputs,
pages, JSON, output and operation budgets are bounded; errors are safe versioned
JSON. Structured logs contain allowlisted operation/category/outcome/duration/
counts, excluding snapshots/IDs/amounts/preferences/paths. Stdout/DB/backups hold
operator-sensitive synthetic data. No sockets, sources, commercial evidence,
implicit latest, scheduler, outbox bridge or Telegram action are introduced.

## MODEL PROFILE USED and actual specialists

The user requested GPT-6.1 Sol/Medium for the lead and High for critical design,
QA and REVIEWER, subject to actual availability. Root system context identifies
Codex based on GPT-6; exact root variant/selector/effective reasoning are not
exposed and are not invented. The observable collaboration tool accepted
`gpt-6.1-sol` with reasoning_effort `high` for all four specialists. These are
observable requested tool arguments, not independent certification of hidden
backend model/reasoning internals. No separate ChatGPT Phase Lead is impersonated.

| Agent | Role and disjoint ownership |
| --- | --- |
| /root | Engineering Lead, integration, journal CLI/root registration/logging, harness/CI, DOCS and final ledger |
| /root/arq_be | ARQ/BE author: errors/models/identity/transitions/application; domain/application tests |
| /root/db_owner | DB author: literal schema/storage; storage tests |
| /root/sec_sre | Read-only SEC/SRE, then independent non-author QA; own qa probe only |
| /root/reviewer | Distinct independent non-author REVIEWER; own reviewer probe only |

Neither QA nor REVIEWER authors product code; they are different agents. Shared
Git and docs changes remain with lead. Initial SEC review found a decoder error
class collision, fixed by DB-OWNER; a timeout caught by the reused decoder was
also corrected to preserve storage_timeout. These are fixed findings, not waivers.
Independent reports must attest the same final HEAD/tree after all fixes.

## Security, contracts, observability and recovery

[ADR0013](../adr/0013-watchlist-synthetic-journal.md) and the three new
[journal](../data-contracts/WATCHLIST_JOURNAL_V1.md),
[storage](../data-contracts/WATCHLIST_JOURNAL_STORAGE_V1.md) and
[signal](../data-contracts/WATCHLIST_SIGNAL_V1.md) contracts remain PROPOSED for
review/adoption; the frozen target is implemented without changing P5a contracts.
Architecture, testing/gates, logging, threat model, roadmap, AGENTS, technical
debt and the [recovery runbook](../runbooks/WATCHLIST_JOURNAL_RECOVERY.md) are synced.

Trusted local directories/Windows ACLs and immutable original P5a revisions are
operational assumptions. No distributed commit or privileged rewrite/source
authentication is claimed. Cooperative deadlines cannot preempt a blocked device
syscall. Append-only growth can exceed the finite whole-history budget; there is
no automatic quota/retention. Recovery ends at the backup point and does not
coordinate earlier DBs or change Telegram quarantine. TD-001..TD-005 remain OPEN
with existing owners/exits. Process restart and ARM64/QEMU do not certify native
Pi hardware or electrical power-loss durability. No new runtime dependency exists.

The secret scanner retains every detector and tracked file. One exact public
synthetic projection digest in the supplied fixture is reviewed via the existing
detector/path/value mechanism, with independent recomputation and regression
checks for modified path/value/detector. See SECURITY_SCANNING runbook.

## Reproducible final gates

After a clean source commit, capture `git rev-parse HEAD` and `HEAD^{tree}`.
Run the following on that exact candidate; scripts reject mismatched identities:

```text
uv run --frozen python scripts/p5b_validate.py --expected-head HEAD_SHA --expected-tree TREE_SHA
uv run --frozen python scripts/p5b_qa_probe.py --expected-head HEAD_SHA --expected-tree TREE_SHA
uv run --frozen python scripts/p5b_reviewer_probe.py --expected-head HEAD_SHA --expected-tree TREE_SHA
```

The local validator retains full commands/stdout/stderr/exit codes in ignored
`.p5b-evidence/HEAD_SHA/local/`, plus summary.json; no evidence DB/log enters source.
It executes frozen dependency/project install, Ruff format/check, strict mypy,
complete coverage pytest, JSON coverage85/80 thresholds, wheel+sdist build,
outside-source installed-wheel version/diagnose and all eleven offline harnesses,
dependency audit and full tracked-file secret scan. QA/reviewer retain independent
JSON probe reports with checks and identity. Full test logs distinguish author,
independent and eight supplied design tests; no historical P5a run counts as P5b.

The eleventh harness demonstrates five checkpoints/two episodes/four signals,
ancient replay, MATCH persistence, pagination, local verify/origin recompute,
exclusive backup/restore and nonmutation across installed child processes with
socket audit denial. Existing ten harnesses remain unchanged. CI retains exactly
four jobs: Quality, Compose, linux/amd64 and linux/arm64 QEMU, with the eleventh
harness wired to each path. Local Docker daemon absence is not a container pass;
read full final-candidate CI logs and record URLs/conclusions in the PR ledger.

## Individual acceptance evidence map

The entries identify executable evidence, not inferred PASS. Final ledger must
state each AC's actual status bound to the final candidate and cite relevant runs.

| AC | Required evidence and implementation/tests |
| --- | --- |
| S01 | Preflight Git/base/tree/parents, verbatim opening contract, design freeze and new roadmap entry |
| S02 | application original manifest/revision admission; application/CLI negative tests and independent original-origin probes |
| S03 | strict normalized <=64KiB synthetic snapshot; domain/public-boundary tests, no prior package/DB mutation |
| S04 | supplied literal byte fixture; stdlib design oracle, productive vector tests and two independent SHA oracles |
| S05 | sequence/watch/revision/series identity and cross-series immutable-entry tests; revision/series isolation probes |
| S06 | initial MATCH/external-previous signal-free baseline domain/storage/independent cases |
| S07 | per-rule simultaneous transitions, OR noninterference and two episodes; independent full-rule/fold oracle and smoke |
| S08 | UNKNOWN, missing money, stale new-as_of, inclusive boundary, disabled/SKIPPED/INDETERMINATE continuity tests |
| S09 | explicit previous equality, strict observed_at, nondecreasing as_of, sample uniqueness; adversarial domain/storage probes |
| S10 | ancient replay preserves bytes/head/time/signals; divergent content/as_of/previous conflicts and rollback |
| S11 | same-process and real process identical/divergent writers, injected four-stage rollback, process exit and reopen |
| S12 | exact SQL/owner/FK, rehashed result/signal/head/link/ordinal/extra/missing corruption probes; deep complete fold |
| S13 | original-backed read-only recompute and local verify success with origin absent/changed; application and independent probes |
| S14 | parsers/limits/filter-bound cursors/shared deadline, safe logs and audit-hook/monkeypatched zero sockets |
| S15 | verified exclusive backup/restore/restart, inode/sidecar/link/copy faults; unchanged original stores |
| S16 | final full regression/coverage/build/audit/scan, eleven installed harnesses and all four complete CI logs |
| S17 | two actual distinct non-author reports and committed own scripts on final HEAD/tree; repeat after fixes |
| S18 | synced ADR/contracts/architecture/threat/logging/runbook/debt, exact provenance, individual AC map and external final report |

## Delivery and limitations

Publish only a coherent candidate PR, with full final report and independent probe
reports in its evidence comment. Read back the complete published body and record
the exact HEAD/tree, base, commit list, local command summaries and four CI jobs.
If the connector denies creation, use only existing normal local Git/gh authority;
do not change/extract credentials or bypass permissions. No force push or merge.
Any unexecuted/failed mandatory gate produces BLOCKED/rework, never readiness.
P2/P6a/retail Discovery stay BLOCKED and P5 overall stays open.
