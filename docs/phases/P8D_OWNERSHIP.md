# P8d ownership and execution boundaries

Status: Gate A / design preparation. Date: 2026-10-30.
Authority: archived P8d contract and Phase Lead CONTINUE GATE A decision in chat.
Worktree: C:/Projects/card-market-tracker-p8d.
Branch: feat/p8d-watchlist-telegram-delivery.
Base: 9dda9fba0aa9646a67596657d4ae9a7088903808.
All historical worktrees and the original rework checkout are outside edit scope.

## Current exclusive authorship

| Actor | Exclusive edit targets in this worktree | Boundary |
| --- | --- | --- |
| Engineering Lead / root | AGENTS.md; shared docs; ADR-0015; P8D_OWNERSHIP, PREFLIGHT, DESIGN_FREEZE and evidence; new runbook; Git integration | Sole integrator. No product code at Gates A/B. |
| ARQ/BE design specialist | docs/data-contracts/WATCHLIST_TELEGRAM_DELIVERY_V1.md only | API/admission/consent/identity proposal. Read all other files; no product code/Git mutation. |
| DB-OWNER design specialist | docs/data-contracts/WATCHLIST_TELEGRAM_DELIVERY_STORAGE_V1.md only | Literal proposed DDL/inventory, invariant/CAS/recovery design. No schema.py/writer/database files. |
| SEC/SRE design specialist | docs/phases/P8D_SECURITY_DESIGN_REVIEW.md only | Read-only source audit; isolated report. No real transport, credentials or product edits. |
| Future independent QA | Not activated; separate future probe files/worktree to be assigned | Must not author product/API/storage. Not a current QA PASS. |
| Future final REVIEWER | Not activated; distinct future probe files/worktree to be assigned | Must differ from authors and QA. Not a current final review. |

Design agent sessions (spawn results observed 2026-10-30):
- /root/p8d_arq_design: API document sole author.
- /root/p8d_db_design: storage document sole author.
- /root/p8d_sec_design: security report sole author.
Each spawned with fork_turns=none, model=gpt-6.1-sol, reasoning_effort=high.
They have only the explicitly assigned document as write scope. Effective backend
and reasoning are not independently observable. No QA/final REVIEWER is active.
No overlapping file edits. Lead integration of specialist-owned files waits until
that specialist hands them back. Specialists may not spawn further agents or
change branches, index, refs, lockfiles, existing databases or historical evidence.
Only Lead may commit. No network/Telegram product execution in this stage.

## Model profile used

Lead requested by user: GPT-6.1 Sol/Medium for coordination, High for critical
design; root variant/effort are not exposed by selection arguments here and no
root model change is claimed. Effective backend/effort are not independently
verifiable. Specialist requested profile: GPT-6.1 Sol/High, available as an
explicit collaboration tool selection. Record requested arguments and actual
spawn results; availability is not proof of effective backend.

## Future implementation ownership (not yet active)

ARQ/BE: new watchlist_delivery application/models/policy/errors and own author
tests. DB: new schema/storage and own storage/recovery/concurrency tests.
Lead: lazy CLI/logging integration, transport adapter integration, harness/CI,
shared docs and commits. One minimal read-only P8c accessor, if necessary, needs
explicit Lead file assignment. Prior P8b transport/writers and P8c policy,
renderer, identities, schema/writers remain unchanged. Independent QA and final
REVIEWER cannot be these authors.

## Gates

A: PASS at Gate A checkpoint1f3f9cabd9381e8f2833d89dcaf20961cffadac7;
baseline/handoff/clean-state evidence in P8D_PREFLIGHT and P8D_DESIGN_FREEZE.
B: proposed design only; Phase Lead design acceptance required.
C: blocked until B accepted. No writer/schema/definitive identity implementation.
Live: NOT AUTHORIZED. No getMe/getChat/sendMessage or token access.

All specialist design files returned to Lead after review. DB/SEC chronology
revision was explicitly reassigned to those same isolated documents and returned.
No active specialist owns product files; QA/final REVIEWER remain unactivated.

## Gate C activation - 2026-10-30

The [Phase Lead decision](P8D_DESIGN_ACCEPTANCE.md) supersedes the historical
Gate A/B-only restrictions above. Frozen design50fcb55a remains unchanged.

| New actor/session | Exclusive current edit targets | Constraints |
| --- | --- | --- |
| /root/p8d_be_impl | src/card_market_tracker/watchlist_delivery/application.py, policy.py, models.py, errors.py, budget.py; tests/test_watchlist_delivery_application.py, tests/test_watchlist_delivery_policy.py | Product BE author. Coordinate private writer/policy interfaces with DB before implementation. No Git/shared docs edits. |
| /root/p8d_db_impl | src/card_market_tracker/watchlist_delivery/schema.py, storage.py; tests/test_watchlist_delivery_storage.py, tests/test_watchlist_delivery_recovery.py, tests/test_watchlist_delivery_concurrency.py | DB author; exact literal accepted DDL, bounded materialization/full folds/CAS/recovery. No Git/shared docs edits. |
| /root/p8d_qa_independent | scripts/p8d_qa_probe.py and docs/evidence/P8D_QA/ only | Nonauthor QA; no product or author-test edits. Independent probes/oracles. Initial read-only analysis then exact-final-candidate validation. |
| /root/p8d_final_reviewer (reserved, distinct agent) | scripts/p8d_reviewer_probe.py and docs/evidence/P8D_REVIEWER/ only | Nonauthor final REVIEWER; distinct from authors and QA. Spawn after product integration. |
| Engineering Lead /root | __init__.py, CLI and narrow transport adapter; root CLI/logging; thirteenth smoke/wheel/container/CI; integration/CLI tests; shared docs/Git/evidence | Sole integrator; no concurrent edits to delegated files without explicit handback. |

All paths are relative to the authorized P8d worktree. All specialists must
use fake transport only and must not read actual credentials or call Telegram.
No extra subagents, branch/index/ref mutations or prior-schema/product edits.
BE and DB may exchange messages/read each other's files; authorship stays exclusive.
QA/final REVIEWER may not fix product files. A finding goes to Lead/author.
Requested specialist profile remains gpt-6.1-sol/high; effective backend unverified.

## Narrow qualification tooling assignment - offline authoring only

/root/p8d_be_impl returned its product files to Lead. It is reassigned exclusively
scripts/watchlist_telegram_qualification.py and
tests/test_watchlist_delivery_qualification.py to prepare the later AC-WT20
dossier/cumulative-cap wrapper. Fake-only tests; no real authorization, token
read or provider invocation by the agent. Lead retains product files and CLI/
harness/CI; no overlapping edits. Frozen core contracts are unchanged.

Qualification tooling reassignment ended when the BE agent returned a usage-limit error before tests. Lead takes back both assigned wrapper/test paths, preserves the authored draft, completes validation and records this interruption. No product/frozen changes are inferred from an uncompleted agent turn.
