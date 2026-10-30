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

Active agent sessions (spawn results observed 2026-10-30):
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

A: preflight and documentation under verification.
B: proposed design only; Phase Lead design acceptance required.
C: blocked until B accepted. No writer/schema/definitive identity implementation.
Live: NOT AUTHORIZED. No getMe/getChat/sendMessage or token access.
