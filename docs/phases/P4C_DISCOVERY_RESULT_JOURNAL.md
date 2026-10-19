# P4c Phase Completion Report and evidence map

Phase: Discovery Result & Event Journal. Date:2026-10-19 Europe/Madrid.
Engineering candidate, not phase acceptance/closure. Final proposed readiness is
determined by the exact-candidate external PR ledger after reviews and CI.
This file records implementation scope and evidence recipes without a circular
commit containing its own SHA. No merge or next phase is authorized.

Branch: feat/p4c-discovery-result-journal. Repository: KastaTM/card-market-tracker.
Authorized base de63457bd6de26874a30d2afd688dcd8901e01ff; baseline tree
41c0f758c8a4bf09cc719a1ce16073245a5aadda; ordered parents
112916382ce02486ca38eb14487220dbb24196e7 and
8af647697dd67859b38fc007d493a54642a1d62f. Final head/tree/PR and four CI log URLs
belong in the external ledger and must be read back after publication.

## Execution and models

[Ownership](P4C_OWNERSHIP.md) documents preflight, actual host access, source ZIP
hash, requested versus observable models and exclusive files. Root authors
application/CLI/validation/harness/integration/docs. ARQ/DB-OWNER authors storage,
schema/errors, storage tests, ADR and storage contract. QA and REVIEWER are
distinct nonauthors and distinct from each other. Spawn accepted gpt-6.1-sol/high
for all three specialists; no authenticated backend introspection or root model
selector change is claimed. Root is system-identified Codex based on GPT-6.
No stronger model escalation was used. REVIEWER also performs SEC/SRE/docs audit.

The provided prototype was inspected, not copied as a finished implementation.
Its isolated18-test evidence is not a P4c gate. The contract/Engineering Brief
are archived literally; live ownership and this report supersede the brief's
historical environment limitations without altering its archived bytes.

## Implementation and decisions

Public record accepts only strict request+capture path+journal path and reuses
the unchanged P1c read boundary and pure v3 comparator. Content-bound private
application receipts freeze bounded canonical bytes; the writer independently
checks authority/content/grammar before any mutation. No result JSON or
self-declared verified flag authorizes admission. Separate capture snapshot and
journal commit do not constitute a distributed transaction.

Independent SQLite v1 has its own application_id, exact owner/version/inventory
and three logical tables. Captures remain schema2/five tables. Composite
occurrence identity preserves different-window evidence with the same evt3.
One transaction inserts a comparison plus all events; replay preserves bytes and
first insertion timestamp, while semantic collision is conflict without overwrite.
Canonical SHA256 covers journal_version/request/result, excluding local write
clock, paths, run IDs and durations. No historical hash preimages are changed.

Get retrieves one complete retained comparison. Keyset lists/occurrences return
bounded summaries with strict cursors and live multi-page semantics. Local
verify checks exact schema/integrity/FK/JSON/full grammar/digest/order/counts and
occurrence equality; source recompute rereads original captures and compares the
entire v3 output. Coherently rewritten valid local content is not authenticated
by local verification. Backup holds a verified source snapshot, uses SQLite's
backup API, validates and reopens a new destination. The two files need separate
backups followed by explicit recompute; there is no atomic joint backup.

[ADR0009](../adr/0009-discovery-result-event-journal.md),
[API](../data-contracts/DISCOVERY_JOURNAL_V1.md),
[storage](../data-contracts/DISCOVERY_JOURNAL_STORAGE_V1.md) and
[runbook](../runbooks/DISCOVERY_JOURNAL_RECOVERY.md) fix those decisions.
Project architecture, roadmap, testing/gates, threat model and debt are updated.

## Security, observability and limitations

SQL type/byte guards precede loading schema/scalar/payload values. Strict
duplicate/nonfinite/lexical parsing and complete nested grammar distinguish
bool from int. Original v3 guards remain unchanged. Result16MiB is checked during
encoding before copying through to_dict; pages are at most1MiB/1000rows with
default100. Shared record deadline defaults2s/max5s across all stages; SQLite
busy/progress and loops/encoding cooperate. OS/device stalls remain outside that
guarantee. Large full scans may fail by deadline; no partial verify is PASS.

Exclusive init/copy destinations and inherited path/link/hardlink/sidecar checks
protect ordinary local use. Trusted directories and operator-controlled Windows
ACLs remain required (TD-003). No global capacity quota/retention exists (TD-004).
TD-001 through TD-005 stay OPEN with existing owners/exits. No excluded commercial
feature is invented as debt. Process kill/rollback/QEMU do not certify physical
Pi power loss or long-running health. No new source acquisition occurred; existing
licensed minimum/MIT notice and exact R0/R1 registry are preserved.

CLI is the separate discovery-journal group with nine operations. Logs contain
allowlisted operation/run ID/result/category/duration and bounded counts only.
Contracted stdout contains evidence and needs local protection. Existing
discover/discover-scoped/discover-multi-revision output/codes/effects stay intact.

## Executed development evidence and final gate recipes

Development runs are provisional until repeated/bound to final immutable objects.
Author application/storage tests passed, including four real unit comparisons,
synthetic positives, same-event two-window preservation, replay/conflict, forged
and mutated receipts, nested invalid grammar, bounds, hostile SQL cells,1005-row
paging, injected faults, real concurrent processes and process kill before commit.
Build and installed external journal harness passed in development. Frozen sync,
strict mypy and targeted Ruff ran successfully. The full final suite and coverage,
security checks, all seven external smokes and CI are ledger requirements below.

Host is Windows/Python3.13; Docker daemon unavailable locally. Container evidence
must come from actual exact-candidate Linux CI, not this limitation or old CI.
One skip inherited from the baseline remains; no new skip or relaxed threshold
is authorized. Every unexecuted mandatory gate is FAIL/BLOCKED with its reason.

| Gate | Reproducible command/evidence |
| --- | --- |
| Frozen install and lock | uv sync --frozen --no-install-project; uv sync --frozen --no-build-isolation; git diff --exit-code -- uv.lock |
| Formatting/lint/types | uv run --frozen ruff format --check .; uv run --frozen ruff check .; uv run --frozen mypy src |
| Suite/coverage | uv run --frozen coverage run -m pytest; coverage json; scripts/check_coverage.py; lines>=85%,branches>=80% |
| Packaging/external runtime | uv build --no-build-isolation; scripts/wheel_smoke.sh or Windows equivalent with external installed interpreter, all seven harnesses |
| Security | uv export --frozen --all-groups --no-emit-project; pip-audit; scripts/check_secret_scan.py |
| Linux containers | Four exact-candidate CI jobs: quality, compose, container AMD64, container ARM64/QEMU; full logs |
| Independent evidence | Nonauthor QA probes + separate REVIEWER on exact head/tree; renewed after changes |
| Publication | Push branch/open PR without merge; publish and read back external ledger |

## AC ledger

Status is pending exact-candidate confirmation in the external PR report; recipes
below are not assertions that a gate passed. Missing final evidence means FAIL.

| AC | Implementation/test evidence to bind in final ledger |
| --- | --- |
| J01 | preflight/archived contract/ownership/roadmap and exact baseline objects |
| J02 | journal schema/init/path tests; unchanged capture code/schema and raw source bytes |
| J03 | public application record path; forged/mutated receipt tests and QA admission probes |
| J04 | full v3 retained equality and independent canonical SHA; unchanged historical comparators |
| J05 | replay/reopen first timestamp, bytes and synthetic collision zero mutation |
| J06 | real admitted synthetic two-window shared evt3, distinct full evidence, paginated occurrences |
| J07 | injected rollback, simultaneous independent writers, killed application writer/reopen |
| J08 | four approved real no_discoveries cases, synthetic positives and baseline |
| J09 | get/keyset pages/strict cursors1005-row regression/read-only and missing DB failures |
| J10 | full local grammar/digest/relationships and coherently altered valid content requiring recompute |
| J11 | consistent backup/restore/reopen/recompute, unsafe destination and alias tests |
| J12 | SQL guards, byte/time/page bounds, strict errors/log redaction and adversarial QA |
| J13 | zero acquisition, unchanged registry/admission/v1/v2/v3/full regression suite |
| J14 | seventh harness added to wheel/Compose/AMD64/ARM64, preserving all six |
| J15 | ADR/contracts/architecture/runbook/threat/debt/roadmap checked against implementation |
| J16 | exact final four-job CI logs plus distinct nonauthor QA and REVIEWER attestations |

Recommendation: submit for Orchestrator review only when the external ledger
demonstrates every mandatory gate PASS on the final candidate. Otherwise report
REWORK_REQUIRED/BLOCKED and the concrete outstanding action. No merge/closure.
