> Historical design handoff: unavailable access/execution describes its creation
> environment. Current results belong to P8C_IMPLEMENTATION_AND_INTEGRATION.md
> and the PR evidence ledger; the template is not executed evidence.

# P8c — Acceptance evidence matrix / living template

**Status at design handoff (2026-10-25): ALL P8c implementation gates NOT RUN / BLOCKED for lack of Codex execution and remote-write permission.** This template is not a Phase Completion Report and may not be treated as successful testing. Fill with commit SHA, tree, code/test commands, artifact links, execution agent, result and date for each item. Do not turn a TODO or file presence into PASS.

| AC | Expected independent reproducible evidence | Status at handoff |
|---|---|---|
| AC-WA01 | Remote+local exact baseline SHA/tree/parents, worktree clean; verbatim archived contract/dated roadmap | BLOCKED — remote read PASS; local checkout and commit pending |
| AC-WA02 | End-to-end one-signal admission, exact P5a revision and full manifest rejection matrix | BLOCKED |
| AC-WA03 | One transaction/one deep P5b fold with exact pair; forged callers rejected; independent instrumentation | BLOCKED |
| AC-WA04 | Complete semantic projection, strict upper bounds, offline P5a recalculation and deterministic reconstruction | BLOCKED |
| AC-WA05 | Domain-separated `walt1_`, independent NUL/bytes/golden vectors and old ID isolation | BLOCKED — design-only three vector fixtures available |
| AC-WA06 | Alias/rule/episode/revision/series/product isolation with no fabricated signals | BLOCKED |
| AC-WA07 | Ancient replay after new appends and revisions, all immutable bytes/time, origin errors/conflicts no partial writes | BLOCKED |
| AC-WA08 | BEGIN IMMEDIATE atomic intent/evidence, process race, crash/reopen and rollback failure hooks | BLOCKED |
| AC-WA09 | Synthetic-labelled deterministic plaintext with Unicode/ESC/bidi/oversize; zero transport imports | BLOCKED |
| AC-WA10 | Complete local fold + coherently rehashed invalid row/trigger tests | BLOCKED |
| AC-WA11 | Read-only origin recompute, wrong/missing originals, byte-for-byte persistence nonmutation | BLOCKED |
| AC-WA12 | CLI exact JSON/error/status/bounds/cursors, shared 2s default and 5s max, no partial pages | BLOCKED |
| AC-WA13 | Source/copy/reopen independent verification; exclusive restore; fsync/link/unlink/multi-hardlink/sidecars | BLOCKED |
| AC-WA14 | Original stores byte-for-byte unchanged, zero product sockets, CMTA/CMTD still reject Watchlist signal | BLOCKED |
| AC-WA15 | Redacted structured correlation/time/counts, threat model update and secret/PII leak probes | BLOCKED |
| AC-WA16 | Eleven original harnesses + twelfth P8c passing wheel, Compose, linux/amd64, linux/arm64 QEMU | BLOCKED |
| AC-WA17 | Ruff/mypy strict/all unit/integration/contract/regression/coverage/security/deps/sdist/wheel/gates | BLOCKED |
| AC-WA18 | Non-author QA + distinct reviewer original probes/published source/results final SHA/tree; defects resolved | BLOCKED |
| AC-WA19 | ADR-0014, exact two contracts, architecture, logging, threat, recovery, testing, debt/roadmap synchronized | BLOCKED |
| AC-WA20 | PR candidate, four full CI job logs, complete completion report/readback, no merge/closure | BLOCKED |

### Mandatory evidence integrity

- Capture separate **requested / observed / unverifiable** model profiles for chat/Codex/specialists.
- Record baseline, branch, PR, `git rev-parse HEAD`, `HEAD^{tree}`, commit parents and file-change inventory.
- Keep failed CI runs and no same-SHA reruns without authorization. For all four final green CI jobs, record run/attempt/job URLs, complete raw sanitized logs, SHA hash, execution OS/platform and twelve harness statuses.
- Provide standalone self-contained reproducible QA and REVIEWER code with helpers/fixtures and their own independent reference oracles. These roles cannot be authors of product files.
- Document 5-checkpoint ARM64/QEMU recovery timing stage and at least 3 runs each where local environment exists; otherwise explain that local QEMU is unavailable and rely on mandatory CI as distinct evidence.
- State origin assumptions and lack of global multi-DB atomicity, authenticated producer, worldwide dedup, commercial offer/notification consent, Pi physical power-loss/hostile-admin resistance.
- **Only after all applicable gates PASS:** Phase Lead may report `READY_FOR_ORCHESTRATOR_REVIEW`. Only Orchestrator can accept/authorize merge/declare closure after required post-merge evidence.
