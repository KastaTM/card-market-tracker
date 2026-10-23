# P5a watchlist core and offline rule evaluation

Engineering candidate for Orchestrator review; only the Orchestrator accepts,
integrates or closes phases. The completion ledger in the open P5a PR records
the final immutable SHA/tree, executed gates, independent reports and readiness
decision. This document fixes scope and reproducible evidence locations; it
does not turn a test recipe or historical P8b result into a passing P5a gate.

## Baseline and authority

Repository KastaTM/card-market-tracker; authorized main
`d1038df1625a9727b44760866266b7124bb1d91a`, tree
`2bb06b79a04fefdc945f754e3611d5862192f5dc`. Both parents were checked locally,
and `git ls-remote origin refs/heads/main` matched before changes. The worktree
was clean; existing branches/worktrees/evidence were preserved. Branch
`feat/p5a-offline-watchlist` starts at the authorized baseline. The first
documentary commit records the attributed P8b closure/P5a opening in ROADMAP,
as authorized by the user-supplied phase contract. No merge is authorized.

The offline handoff's prototype and 33 isolated tests are reference material.
They certify neither this implementation nor project coverage. The previous
P8b main run is historical integration evidence only. P2/P6a/retail Discovery
remain BLOCKED; TD-001 through TD-005 remain OPEN. P5a does not close all P5.

## MODEL PROFILE USED and actual ownership

Requested lead: GPT-6.1 Sol / Medium, High for difficult decisions. Observable
lead identity from session instructions: GPT-6; its effective reasoning setting
is not observable. Specialist calls request `gpt-6.1-sol` and `high`; those
selectors do not independently attest a backend serving identity or effective
reasoning setting. No profile is inferred from output quality.

- Engineering Lead: CLI/logging integration, author CLI tests, synthetic
  fixtures, tenth harness, CI wiring, integration, Git and evidence publishing.
- BE/ARQ author: validation/models/errors, pure evaluation and application;
  domain and application author tests.
- DB-OWNER author: schema/storage and storage author tests.
- DOCS/ARQ/SEC author: ADR/contracts, architecture, threat model, recovery,
  testing/gates/debt updates and consistency review.
- QA and final REVIEWER: distinct nonauthors, separate from each other and
  from DOCS; final PR ledger includes their own probes on the same frozen
  SHA/tree and any renewed review after substantive changes.

Disjoint ownership preceded parallel edits. The Engineering Lead alone changes
shared Git state. Author validation is not independent QA. See the
[engineering brief](P5A_CODEX_ENGINEERING_BRIEF.md).

## Implementation and boundaries

The new `watchlist` package accepts only existing canonical printing/sealed
targets after full MANIFEST_V1 parsing. Its versioned stable watch key commits
the exact CMT ID. Frozen identity contains the target and necessary card/set
closure, preserves null/unknown and excludes names/dates/aliases/unrelated
entities. Incompatible identity changes fail without retargeting.

Configuration stores operator preferences only: priority, enabled, positive
optional EUR-cent target, restock flag and bounded max age. Every new command
creates immutable history, current pointer and request evidence atomically.
CAS prevents lost updates; replay returns the original revision without moving
the current pointer backwards. There is no hard delete.

The separate CMTW/schema1 SQLite store owns exactly four STRICT tables plus
contracted indexes/triggers. Deep verification checks canonical history,
identity/digests, contiguous revisions, request bijection and current pointers.
Backup/restore use a verified consistent snapshot and exclusive destination;
restore exposes validated preferences, never transport receipts.

The pure evaluator revalidates typed JSON values and uses explicit frozen
revision, synthetic samples and as_of. Application validation checks the full
manifest commitment before calling it. Freshness is inclusive, required stale
evidence is indeterminate before stock decisions, and missing stock is never
inferred as out of stock. Price uses exact unit plus known shipping; restock
requires a valid same-context transition. Per-rule reasons survive OR aggregation.
Disabled SKIPPED follows malformed/context/time validation. Samples/results are
ephemeral, never persisted, and MATCH has no event or notification meaning.

CLI is one-shot and opt-in, with bounded versioned JSON, keyset pages, fixed
error categories and redacted structured completion events. Default total
budget is2 seconds, maximum5. The tenth installed-process harness joins all
nine earlier smokes in wheel, Compose and both architecture jobs. Runtime calls
to the Internet are zero, including Telegram. Earlier capture/comparator/
journal/outbox/delivery modules, schemas and IDs are unchanged; only minimal
root CLI and logging registration are additive.

## Decisions, security and recovery

- [ADR-0012](../adr/0012-watchlist-offline-rules.md)
- [Watchlist v1](../data-contracts/WATCHLIST_V1.md)
- [Storage v1](../data-contracts/WATCHLIST_STORAGE_V1.md)
- [Synthetic evaluation v1](../data-contracts/WATCHLIST_SYNTHETIC_EVALUATION_V1.md)
- [Recovery runbook](../runbooks/WATCHLIST_RECOVERY.md)
- [Threat model](../threat-model/THREAT_MODEL.md) and
  [logging contract](../data-contracts/LOGGING_V1.md)

No new runtime dependency, source feed, provider price, transport, event bridge,
web UI or scheduler is introduced. Synthetic provenance is a caller declaration,
not authentication or permission to reuse real data. Local consistency cannot
authenticate a coherent privileged rewrite. Trusted directories/Windows ACLs,
capacity, device stalls and physical Pi power-loss validation remain limitations.
There is no distributed atomicity, clone synchronization or global history
retention policy; existing debt owners/exits are preserved.

## Acceptance evidence map

Each row names a distinct observable assertion; executed PASS/FAIL/BLOCKED
results, commands/logs and exact candidate identities belong in the PR ledger.

| AC | Required observable evidence |
| --- | --- |
| W01 | Baseline commit/tree/parents and ls-remote; first documentary commit and attributed ROADMAP entry |
| W02 | Domain/application tests rejecting missing UUIDs, sets/cards/candidates and forged manifests; full parser relation/binding validation |
| W03 | Stable wlt1_ preimage, distinct printing variants/languages and sealed null-parent closure; harmless rename vs incompatible canonical change |
| W04 | Config defaults, at least one rule, exact bool/integer and money/age/enum bounds; disable retains rules |
| W05 | Two concurrent CAS writers yield one winner; atomic history/request/current and injected intermediate-write rollback/reopen |
| W06 | Canonical replay, token-content conflict, stale revision and old replay after newer update retain current bytes/history |
| W07 | Synthetic sample parser rejects real provenance, EUR mismatch, unknown fields, duplicate/hostile JSON and bool/float/zero unit; no sample/result tables |
| W08 | Exact threshold and +/-1 cent, known free shipping vs null, bounded exact sum and missing amount outcomes |
| W09 | Complete stock matrix, missing/UNKNOWN prior and series/ID mismatch; only OUT_OF_STOCK to AVAILABLE matches restock |
| W10 | Inclusive freshness edge, stale current/prior semantics, future and duplicate/reversed chronology rejection, normalized UTC offsets and explicit as_of |
| W11 | Per-rule reason retention, OR with uncertainty, disabled SKIPPED after invalid-input rejection |
| W12 | Byte/hash equality of watchlist and accepted temporary source databases after evaluation; fixed revision outputs repeat despite later config |
| W13 | All12 CLI routes, versioned sanitized errors/logs, priority/filter-bound cursor and history paging plus byte/count/input/deadline limits |
| W14 | Exact schema/index/trigger/owner and deep history/request/current tampering checks; rollback/reopen, exclusive copies, IO and sidecar failures |
| W15 | Full prior regression suite, unchanged accepted storage modules/contracts, denied sockets in import/CLI/evaluation/harness and accepted DB hash probes |
| W16 | Frozen install, Ruff/mypy/full suite/85line80branch/build/audit/secret; all10 installed harnesses; four final-candidate CI job bodies |
| W17 | Distinct QA/REVIEWER reports with their own probes and same final SHA/tree; findings reproduced/fixed/rechecked |
| W18 | ADR, three contracts, runbook, threat/logging/debt/architecture/test/gate updates and published/read-back Phase Completion Report |

Author evidence lives in `tests/test_watchlist_domain.py`,
`tests/test_watchlist_application.py`, `tests/test_watchlist_storage.py`,
`tests/test_watchlist_cli.py` and `scripts/watchlist_smoke.py`. Synthetic fixture
provenance is documented in `tests/fixtures/PROVENANCE.md`.

## Reproducible gates and report protocol

Use [quality gate commands](../QUALITY_GATES.md). Frozen install, Ruff format/check,
strict mypy, full coverage suite, threshold script, sdist/wheel, audit and tracked
secret scan all apply. Install the built wheel in an isolated environment outside
the checkout and run all ten harnesses. CI retains quality, compose and two
container matrix jobs (linux/amd64 and linux/arm64 with QEMU). Inspect complete
logs for the final PR SHA; local Docker absence cannot pass a container gate.
No live product gate applies to P5a. QEMU certifies neither native Pi operation
nor real electrical interruption recovery.

The external PR ledger avoids a self-referential commit hash: it records exact
base/head/tree, commits, gate results/log URLs, coverage deltas, independent
reports and unresolved limits after freezing the source. Read that published
report back. Missing mandatory evidence means FAIL/BLOCKED, never readiness.
No merge, phase acceptance or closure follows from an engineering recommendation.
