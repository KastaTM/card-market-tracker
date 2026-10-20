# P8a Offline Alert Outbox — implementation and evidence map

Phase: P8a. State: OPEN. Proposed engineering status is determined by the
exact-head Phase Completion Report published on the open phase PR; this source
document alone does not certify readiness. Only the Orchestrator accepts or
closes phases. No merge is authorized. Branch:
`feat/p8a-offline-alert-outbox`. Authorized base:
`b89fff319a94e5eb6e4b7bdad944e879bad371f6`, tree
`8f62a1d85b375ee839dcd95e09a578cb643c85b6`.

The final PR ledger records the actual PR URL, immutable head/tree, all four
complete CI job links/log results and separate QA/REVIEWER attestations. Keeping
those execution identities outside the source commit avoids a circular
SHA-only commit. Results below identify actual precommit integration checks;
final exact-head CI and independent checks must confirm the frozen candidate.

## Authority, preflight and model profile

The pasted user request authorizes implementation, agents, commits, push and an
open PR without merge. Attached draft documents are subordinate engineering
inputs. [The original contract](P8A_OFFLINE_ALERT_OUTBOX_CONTRACT.md) is archived
unchanged, SHA256
`1f93a903398d3cf8f22665f1509f633840fa49845e1314ebc3594099fef6e549`.
Its .gitattributes entry disables newline translation. The
[execution ledger](P8A_EXECUTION_STATUS.md) records clean initial checkout,
remote/main/worktrees, authentication, exact baseline and environment. No foreign
branch, detached evidence worktree or local main was changed.

User requested lead gpt-6.1-sol/Medium for ordinary work, High for architecture,
identity, SQLite, concurrency, security and review. Root is the system-provided
GPT-6-based Codex agent; no active root model-switch API or backend introspection
was available, and no switch is asserted. Actual specialist spawn requests
gpt-6.1-sol/High were accepted for storage author, application author, nonauthor
QA and separate nonauthor REVIEWER. Requested/accepted tool arguments do not
prove hidden backend routing. [Ownership](P8A_OWNERSHIP.md) names real agents and
disjoint files. QA and REVIEWER differ from each other and every author.

## Implemented objective and architecture

`alerts.application.enqueue` accepts three explicit distinct database paths,
one comparison ID and one local destination alias. It retains and freezes one
complete locally validated journal request/result, verifies original capture
snapshots through the existing reader, runs the unchanged v3 comparator, and
compares the full canonical result and ID. The same frozen result produces all
intentions. A private instance/content-bound receipt seals every consumed field;
constructor claims, flags, copied receipts and post-validation mutation grant
no authority. It is not a signature against privileged Python execution.

Pure policy derives alt1 from the exact canonical destination/event preimage.
Pure renderer produces deterministic bounded plaintext, labels synthetic and
candidates and qualifies novelty to the selected window. Source values are
retained in complete event evidence. Message/policy versions, captured clocks,
profile and evidence level are frozen. No names or URLs are fabricated.

The independent CMTA SQLite/schema1 has exactly metadata, immutable pending
alerts and per-comparison associations. One BEGIN IMMEDIATE transaction commits
all alert/evidence additions or rolls back. One evt3/destination across two cmp3
keeps one intention and both full evidence windows. Replay preserves stored
bytes and first timestamp. Conflicts do not overwrite anything. Baseline and
no_discoveries succeed with zero alerts/associations and a read-only outbox check.

The complete CLI implements init, enqueue, get, list, evidence-list, evidence-get,
preview, verify, recompute, backup and restore. Preview is read-only. Local verify
checks full schema, integrity, canonical semantic content and relationships;
explicit association recompute also checks journal and original captures.
New-target SQLite copies preserve evidence, messages, versions and initial clocks.
All queries/preparation have strict row, byte and shared time budgets. Paths reuse
the vetted trusted-directory/link/sidecar safeguards. No implicit initialization,
migration, retention, deletion, partial verification or silent repair exists.

[ADR0010](../adr/0010-offline-alert-outbox.md),
[public contract](../data-contracts/ALERT_OUTBOX_V1.md),
[storage contract](../data-contracts/ALERT_OUTBOX_STORAGE_V1.md),
[architecture](../ARCHITECTURE.md) and
[runbook](../runbooks/ALERT_OUTBOX_RECOVERY.md) formalize the changes.
Captures schema2, journal schema1, existing comparators/identities and source
registry/fixture bytes are unchanged. Acquisition budget is zero. Four real
R0-to-R1 comparisons produce zero alerts; all positives are explicitly synthetic.
Transport, recipients, credentials, scheduler, dispatcher, leases, retries,
acknowledgements and delivered/sent states remain outside P8a. P5/P8b are not open;
P2/P6a/retail Discovery remain BLOCKED.

## Security, observability and debt

The [threat model](../threat-model/THREAT_MODEL.md) covers coherent journal
tampering, forged authority, control text, hostile oversized SQLite cells,
relationship/digest corruption, aliasing, replay/conflicts, writer interruption,
backup ownership and evidence privacy. SQL type/byte guards precede materializing
TEXT, including schema metadata; pages never load whole histories. Local verify
does not authenticate coherent administrator rewrites. Enqueue checks source
snapshots before outbox commit and assumes contracted original immutability;
there is no three-database distributed transaction.

Logging adds only alert.outbox.completed, fixed alert_outbox operations, run ID,
duration, categories/results and bounded alert/association/event counts. Payloads,
destinations, references, messages, paths, SQL and raw exceptions are excluded.
Explicit stdout, databases and backups require private local access. No source
or recipient identifiers enter diagnostic logs.

TD-001 through TD-005 remain OPEN. Cooperative deadlines cannot bound blocked
kernel/device IO. Trusted-ancestor races, Windows ACLs, append-only capacity,
producer authentication, legacy scope and native Pi durability remain documented
limits. Process kill and ARM64/QEMU do not qualify electrical power-loss behavior.

The executed dependency audit found certifi2026.7.22 affected by
[GHSA-6q48-6c7w-9gw2](https://github.com/advisories/GHSA-6q48-6c7w-9gw2).
Only its lock entry was upgraded to2026.10.19; frozen reinstall and repeated
audit found no known vulnerabilities. No runtime dependency was added. The
tracked-file secret scan passed with63 existing exact public digest matches and
no unreviewed candidates. No threshold, regression test or skip was weakened.

## Reproducible checks and environments

Windows preflight observed uv0.12.10, Python3.13.15, SQLite3.53.1, Docker29.7.2.
Linux containers report Python3.13.16/SQLite3.46.1; product runs UID/GID10001 with
private0700 data and read-only fixture mounts, networking disabled at runtime.
Build/audit dependencies use network only during setup, never source acquisition.

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
sh scripts/container_smoke.sh cmt-p8a-amd64 linux/amd64
sh scripts/container_smoke.sh cmt-p8a-arm64 linux/arm64
```

Compose CI runs version/diagnose, builds the existing offline services and runs
all eight harnesses with --mode compose. The eighth is
`scripts/alert_outbox_smoke.py`; the previous seven are unchanged. Wheel runs
install a fresh package outside checkout, clear PYTHONPATH and invoke all eight
between separate processes. The local Windows equivalent is preserved under
ignored .p8a-evidence/lead/run_wheel.py and all three container drivers under
run_containers.py. Local complete logs live in .p8a-evidence/lead; full public CI
logs and immutable job URLs are linked from the final PR report.

Initial complete integration:1244passed/1historicalWindowsSkip, lines92.87% and
branches85.66%, above unchanged85%/80% thresholds. This preceded the remaining
author boundary tests; final exact-head suite/counts/coverage are recorded in
the PR ledger. Final author subsets: storage55passed; application/policy/CLI
106passed; logging21passed. Root integrated the final numeric-cell guard and
two storage regressions after independent QA reproduced the issue. Initial
installed wheel and all eight local Compose/AMD64/ARM64 harnesses passed;
the corrected final package is rebuilt and rechecked. Nonauthor QA separately
ran41independent probes before the numeric fix, then both numeric regressions
passed after correction. Its final attestation must bind actual frozen SHA/tree.
These are execution records, not a claim that pending CI/review gates passed.

A full integration rerun while three container suites were active found the
short150ms lock probe exhausted its shared budget during origin verification,
correctly returning storage_timeout before lock acquisition. The public lock
probe now supplies1s while retaining its existing under2s elapsed bound and
exact storage_locked expectation; explicit early-deadline tests remain. This
distinguishes source-verification timeout from an actual SQLite busy timeout.

## Acceptance and final gate evidence map

| AC | Reproducible evidence |
| --- | --- |
| A01 | Preflight ledger, original contract hash, actual ownership, roadmap chat attribution, exact Git objects |
| A02 | application tests for public admission, missing source and forged/modified/copied receipts; original capture reader/comparator unchanged |
| A03 | Frozen-pair mutation test, coherent journal rewrite rejection, whole semantic comparison and zero-write failures |
| A04 | Independent canonical SHA test vector, policy tests, second-destination tests and QA oracle |
| A05 | Application/storage tests and eighth harness: same evt3 across two cmp3, one alert/two full associations per destination |
| A06 | Replay byte/clock checks, intrinsic/association conflicts and rollback after prior inserts |
| A07 | Policy/renderer tests for deterministic labels, strict source grammar, Unicode/control/bidi escaping and4096UTF8 ceiling |
| A08 | Exact CMTA inventory and source byte/schema assertions; Git diff preserves prior comparator/storage/source files |
| A09 | Storage real subprocess writers, actual process termination mid-transaction, rollback and reopen/retry; independent QA repeats |
| A10 | Keyset/filter/cursor/limits tests, concurrent page insertion, preview read-only bytes and pending-only state |
| A11 | Local verify corruption probes plus original-backed association recompute; coherent local rewrite differs from origin proof |
| A12 | SQLite consistent backup/restore, timestamp/replay preservation, aliases/links/sidecars/existing-target/cleanup probes |
| A13 | Four real R0-to-R1 zero-alert cases in tests/eighth harness and QA; exclusively synthetic positives |
| A14 | Strict budgets/errors/log allowlists, hostile SQLite bounds, eight-harness wheel/Compose/AMD64/ARM64 recipes |
| A15 | ADR0010, both v1 contracts, architecture, roadmap, runbook, threats, logging, gates/testing and open debt |
| A16 | Mandatory final exact-head CI4jobs + complete logs; independent QA and distinct REVIEWER SHA/tree attestations in PR ledger |

Every mandatory gate must be PASS with reproducible frozen-candidate evidence.
Missing evidence means FAIL/BLOCKED and prevents readiness, including a missing
CI job or independent review. No claim of physical Pi testing is made. The final
Phase Completion Report names open findings, their resolution, residual limits
and recommendation; it may propose READY_FOR_ORCHESTRATOR_REVIEW only after
all required evidence has been retrieved and read back from GitHub. It cannot
declare acceptance, closure or perform merge.
