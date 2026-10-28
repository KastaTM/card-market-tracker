# P8c RW-01 Corrective Implementation - candidate record

2026-10-28. P8c OPEN / REWORK_REQUIRED. Orchestrator rework accepted by Phase
Lead; prior READY recommendation suspended. No merge, closure or new phase.
This document records corrective implementation before final publication. The
PR18 RW-01 ledger must bind the corrected SHA/tree, final independent reviews,
new four-job CI and complete public logs/readback before any readiness proposal.

## Defective candidate and reproducible cause

Original HEAD360da646892e46545ca70e8838bc3a2a89e460a3,
tree3ce94d6e214de74889475753807122b526085b98;
base228d5c8d0d91edf03ddb86a489c8232eeb7c08bc.
Pre-edit clean state, all36worktrees/localbranches and live origin/main verified;
main published remains baseline. Historical local main5175d5b09e8d412e11b2ddf4c24bff41df133843
matches the previous recorded preflight; it was not moved or mistaken for origin.
Frozen four design/normative hashes remain unchanged.

Two independently legitimate P5a/P5b source pairs have the same watch_id/revision1
but target_price_minor900/1000. All source creation and admission used public APIs.
Both produce distinct valid wsig1_/walt1_. The old writer returned two recorded,
then complete verify and backup both failed storage_corrupt.
Reproduced before product edits on CPython3.13.15/SQLite3.53.1;
all four original source files unchanged, zero sockets.
Lead probe exit1 is the expected failure, not a passing gate.
Original code SHA2562d849cdbeae6b19395eb9c00520755a07748d0d1c3ddbb0373d1d1aa5c149725
and raw output are retained immutably in ignored RW-01/pre-fix evidence.
The public probe has only formatting/import cleanup; original executable remains
available unchanged in the evidence bundle for before/after replay.

    python scripts/p8c_rw01_invariant_probe.py --fixtures tests/fixtures --timeout 5

Root cause: writer checked only owned schema/physical integrity/selected alert,
while complete verify enforced full canonical entry equality across alerts
sharing(watch_id,revision). Per-pair-valid source authority did not guarantee
the global retained-store invariant. No fabricated DTO, SQL/source mutation or
private writer was used to produce this primary finding.

## Correction and conflict precedence

Only product file changed: src/card_market_tracker/watchlist_alerts/storage.py.
A shared semantic fold reconstructs every retained pair and checks all original
verifier invariants/counts. Writer executes it once under the same BEGIN IMMEDIATE
and Budget, retaining only that transaction's canonical entry map/selected pair.

1. Any preexisting retained corruption/contradiction fails storage_corrupt.
2. A valid selected same alert ID with different frozen content retains
   replay_conflict. Identical ancient replay retains original bytes/time.
3. Only a new distinct ID whose complete entry differs for the same historical
   key fails identity_conflict/exit2 before INSERT/COMMIT.
4. Equal complete entries may coexist for independent aliases/signals/series;
   distinct revisions/watch IDs/products remain independent.

No comparison trusts raw stored JSON/hashes; existing pairs undergo original
semantic reconstruction before contributing to the canonical map.
No cache crosses operations/snapshots; each recovery fold independently invokes
the same complete verifier. Shareddefault2/max5s deadlines, rollback, receipt,
SQLiteDDL/application_id, identities and all earlier owners remain unchanged.
O(history) admission verification may legitimately timeout at capacity; no retry,
new deadline, unchecked insert or verifier weakening hides that cost.

## Actual ownership and review roles

[Ownership](P8C_OWNERSHIP.md) preserves prior records and names new RW-01 sessions.
DB-OWNER authored only storage.py/new test_watchlist_alert_rw01.py.
New ARQ/BE and SEC/SRE performed read-only semantic/transactional fix reviews;
no blocking static findings and no runtime PASS claimed by those roles.
Lead owns root probe, twelfth harness/CI, shared docs/Git/evidence.
New nonauthor QA and distinct REVIEWER authored only their own standalone probes;
preliminary working-tree runs are not final-candidate attestations.

Requested Lead:gpt-6.1-sol/Medium,High for critical decisions; actual root
selector/effort not independently exposed.
All new specialist spawn arguments gpt-6.1-sol/high are observable; backend
unverified. No model introspection or old-review reuse claimed.

## Regression coverage and failure-first history

35 new author regressions cover all12 requested requirements, plus full config/
canonical-identity differences and classification/one-fresh-fold precision.
Primary cases create sources via public add/update/record and enqueue only.
Pre-fix matrix12FAILs retained; final scoped128PASS in25.17seconds is author
development evidence, not a substitute for final full suite/CI.

Cases include target/priority/freshness/restock differences; same/different alias/
series; real conflicting processes; equal independent semantic copies; revision/
product independence; ancient replay after source growth; exact retained bytes,
first_prepared_at, full alert/evidence/list/counts and original source bytes;
verify/backup after every rejection; IO/timeout at both INSERTs and COMMIT.
Controlled negative OUTBOX-only corruption fixtures test storage_corrupt
precedence. They are not source authority or the primary public reproduction.
Original P5a/P5b databases are never modified after setup.

New independent QA:17 preliminary cases PASS at default2 and explicit5;
same new probe fails against an isolated original360da646 package.
New REVIEWER:28 preliminary own checks PASS at default2/explicit5, including
genuine same-ID/different-ancestry replay_conflict and spawned conflicting race.
Their exact corrected SHA/tree reruns and clean attestations remain mandatory.

Twelfth installed/Compose/AMD64/ARM64 harness extends the full original five
checkpoints/four signals with a second genuine incompatible pair. It asserts
exit2/identity_conflict, unchanged outbox/source bytes/alert/evidence/counts,
and successful subsequent verify/backup/restore. The eleven earlier harnesses
are unchanged. Quality adds the three RW-01 probes beside prior probes.

## Mandatory final gates

Frozen installs use uv --no-cache without ACL/cache repair. Lock/dependencies
unchanged. All these gates need the corrected committed candidate:

    uv run --frozen ruff format --check .
    uv run --frozen ruff check .
    uv run --frozen mypy src
    uv run --frozen coverage run -m pytest
    uv run --frozen coverage json -o coverage.json
    uv run --frozen python scripts/check_coverage.py coverage.json
    uv run --frozen python scripts/p8c_rw01_invariant_probe.py --fixtures tests/fixtures --timeout 5
    uv run --frozen python scripts/p8c_rw01_qa_probe.py --fixtures tests/fixtures --timeout 5
    uv run --frozen python scripts/p8c_rw01_reviewer_probe.py --fixtures tests/fixtures --timeout 5
    uv build --no-build-isolation
    sh scripts/wheel_smoke.sh
    uv export --frozen --all-groups --no-emit-project -o requirements-audit.txt
    uv run --frozen pip-audit -r requirements-audit.txt
    uv run --frozen python scripts/check_secret_scan.py

Preserve new four jobs:quality,Compose,AMD64,ARM64/QEMU, all12harnesses.
Old run40586563511 and evidence commit82570887057a1421ca24d2d8ceea09eb2db7e706
are historical defective-candidate evidence, never RW-01 gates.
No same-SHA failed-job reruns. Any corrective commit needs applicable renewal.
Independent probes/helper source, full raw sanitized logs, commands and readback
must be publicly retrievable from PR18, not private paths/hashes alone.

## AC-WA01..20 renewal map

All rows below are BLOCKED for FINAL RW-01 acceptance until the new candidate,
gates, independent attestations and publication are bound by the PR ledger.

| AC | Current final-candidate state | Renewal evidence |
| --- | --- | --- |
| AC-WA01 | BLOCKED | renewed local/remote baseline/preflight, original/current SHA/tree, frozen bytes |
| AC-WA02 | BLOCKED | full source admission regression + legitimate independent RW-01 sources |
| AC-WA03 | BLOCKED | original receipt/one P5b fold tests + one fresh transaction-local writer fold |
| AC-WA04 | BLOCKED | complete evidence reconstruction + full-entry config/identity comparison |
| AC-WA05 | BLOCKED | unchanged identity vectors + new independently verified distinct/same IDs |
| AC-WA06 | BLOCKED | alias/series/equal-copy/revision/product positive controls |
| AC-WA07 | BLOCKED | incompatible historical entry rejects without bytes/time/evidence mutation; ancient replay preserved |
| AC-WA08 | BLOCKED | real conflicting process race, atomicity, INSERT/COMMIT timeout+IO rollback |
| AC-WA09 | BLOCKED | full renderer/offline regressions unchanged |
| AC-WA10 | BLOCKED | shared full verifier, preexisting contradiction storage_corrupt precedence |
| AC-WA11 | BLOCKED | exact original recompute/source bytes regressions |
| AC-WA12 | BLOCKED | unchanged default2/max5 Budget, CLI/errors/page limits and conflict exit2 |
| AC-WA13 | BLOCKED | verify/backup/restore remain healthy after reject; independent recovery folds preserved |
| AC-WA14 | BLOCKED | zero sockets, unchanged prior schemas/writers/source bytes/transport boundaries |
| AC-WA15 | BLOCKED | logging/privacy/security gates and documented identity_conflict |
| AC-WA16 | BLOCKED | all12 harnesses/new twelfth regression in wheel/Compose/AMD64/ARM64 |
| AC-WA17 | BLOCKED | full unfiltered suite/85line80branch/format/lint/mypy/build/audit/scan |
| AC-WA18 | BLOCKED | NEW QA + distinct REVIEWER on exact corrected clean SHA/tree |
| AC-WA19 | BLOCKED | RW-01 docs/ownership/runbook/roadmap and preserved frozen contracts |
| AC-WA20 | BLOCKED | updated PR18, four full new CI logs, complete report and public readback |

## Residual limits

Already contradictory stores are corruption, not repaired/migrated/pruned by
enqueue. Preserve evidence and restore only a separately verified good backup
to a new path. No weakened verifier or automatic source reconciliation.
Local Docker info again failed with absent dockerDesktopLinuxEngine pipe,
even with punctual escalation; no images/containers or localQEMU timing claimed.
Remote mandatory jobs remain required, no physicalPi certification.
Trusted directories/immutable revisions, no distributed global snapshot/authenticated
producer/global copy dedup, cooperative OS limits and postcommit response ambiguity
remain as frozen. P5global/TD-001..005 OPEN. No merge/PHASECLOSED/new phase.
