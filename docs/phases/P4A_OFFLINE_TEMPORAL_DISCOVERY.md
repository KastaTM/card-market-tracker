# Phase Completion Report — P4a Offline Temporal Discovery

## Later Orchestrator decision — 2026-10-13

The [P0.5b opening contract](P0_5B_REAL_SOURCE_QUALIFICATION_CONTRACT.md), supplied
by the user, records P4a **ACCEPTED / PHASE CLOSED** by the Orchestrator after
actual integration and exact-main CI. [PR7](https://github.com/KastaTM/card-market-tracker/pull/7)
merged as `6385c952a9f2024c8b7bdb33d37fa21017029bd5`, tree
`8fa2abeb9f4e8991bab1b2895fc397f64bb39a19`, ordered parents
`734641a7ef920688677cdea6bc82f908a2856927` then
`c5ed228af831a2a6ed8a12c7072777d3908296a5`. Local fetch/objects/PR metadata
were verified at P0.5b start. Historical [integration ledger](https://github.com/KastaTM/card-market-tracker/pull/7#issuecomment-6155836622)
and [push CI38471731980](https://github.com/KastaTM/card-market-tracker/actions/runs/38471731980)
support that contract's baseline. They are not newly executed P0.5b gates.
This note attributes the decision to the Orchestrator, invents no closure comment
and preserves the original prepublication snapshot below. P0.5b is now open for
source qualification; P2/P6a/retail remain blocked, synthetic-only unchanged.

## Original prepublication snapshot

Phase: P4a, contract issued by the Orchestrator on 2026-10-12 Europe/Madrid.
Proposed status at this publication snapshot: implementation complete; final
exact-candidate QA/REVIEWER and hosted CI evidence pending in the external ledger.
This report does not accept/close the phase or authorize integration. No merge.
Branch: `feat/p4a-offline-temporal-discovery`. Repository: `KastaTM/card-market-tracker`.
PR/head/tree/checks: to be recorded after publication in the branch's external
PR delivery ledger, avoiding a commit that claims its own circular SHA. Final
readiness requires that ledger's exact candidate results, not provisional tests.

## Baseline, preservation and authority

Authorized base and fetched `origin/main`:
`734641a7ef920688677cdea6bc82f908a2856927`; tree
`ae61fe57e6f874b138c98ecdaaa8cbd830406354`; ordered parents
`c6e66a2aba469d02f0ca63fde3b81ecc5eea41bc` then
`e9c5f02e7f093dedff55b67f137c4446f22e8735`. Git remote fetch/push is
`https://github.com/KastaTM/card-market-tracker.git`. Local status/branch/worktrees,
fetch, rev-parse/cat-file/show and direct remote refs were verified before edits.
Initial clean checkout was P3a at the second parent, same tree. Its branch, local
main and detached `.p3a-evidence/qa` and `reviewer` remain preserved. P4a branch
was absent remotely and created from the exact authorized baseline; no reset.

Full Downloads contract/brief were read and archived byte for byte with SHA256
values in [ownership](P4A_OWNERSHIP.md). AGENTS/context, operating model, roadmap,
architecture/ADRs, coding/testing/gates, risks/debt/threats, versioned contracts,
P1a/P3a reports/ownership/PR ledgers and runtime/tests/CI/harnesses were inspected.
The user requests Engineering Lead execution; the attached contract's Phase Lead
role text is interpreted as delegated authority/scope, not a change of this role.

[Roadmap](../ROADMAP.md) and the later P3a report note attribute P3a closure and
P4a opening to the Orchestrator. Historical [integration ledger](https://github.com/KastaTM/card-market-tracker/pull/6#issuecomment-6131957615)
and [main-push CI38302824438](https://github.com/KastaTM/card-market-tracker/actions/runs/38302824438)
are baseline evidence only. The contract reports a403 publishing closure, while
the decision was issued in chat; no published closure comment is invented.
P2/P6a/retail stay blocked, TCGdex stays provisional, and P4a does not implement
the full P4 or authorize retained real observations/source queries.

## MODEL PROFILE USED and specialists

The user requested GPT-6.1 Sol/Medium for Lead, High for architecture/integrity/
review. Root identifies as GPT-6 based Codex; exact backend/reasoning and client
selection are not independently exposed. No root model switch or separate
ChatGPT Phase Lead invocation is asserted. Delegation offers and accepted explicit
`gpt-6.1-sol/high` requests below; accepted configuration does not independently
verify the serving backend. No Astra escalation or Max/Ultra request was used.

| Agent | Role and accepted configuration | Responsibility/independence |
| --- | --- | --- |
| `/root` | Engineering Lead; exact variant/reasoning unverified | Git, CLI/logging, smokes/workflow/Compose/shared docs/integration |
| `/root/arq_checkpoint` | ARQ + DB-OWNER, Sol/High | Read-only initial design checkpoint, then explicit ADR/contracts/reader/tests authorship |
| `/root/discovery_author` | DATA/DISCOVERY + BE, Sol/High | Generic Discovery models/input/validation/comparator and disjoint tests/fixtures |
| `/root/security_operations` | SEC + SRE, Sol/High | Read-only runtime/design probes; runbook/threat/risk/debt docs only |
| `/root/qa_final` | Independent QA, Sol/High | Separate final-SHA detached source worktree; independent outside-source probes; no production authorship |
| `/root/reviewer_final` | Independent REVIEWER, Sol/High | Different detached final-SHA worktree; independent code/Git/contracts/CI review; no authorship |

Ownership preceded parallel edits; shared DTO/errors/output/identities were frozen
before dependent integration. Lead alone changes Git/refs and shared inputs.
Author roles are combined explicitly. QA and REVIEWER are separate from all authors
and each other; their accepted delegations exist, but final evidence is pending
at this committed snapshot. Agent reviews are not formal GitHub approvals.

## Objective and implementation

`cmt discover --db PATH --request REQUEST_JSON` compares one synthetic current
batch against at most32 explicit earlier batches in a single exact namespace/
kind/language context. Variant remains part of the full reference key. History
order is canonical, timestamps fixed UTC and strictly earlier than current;
historical ties are allowed. No runtime clock, latest-batch lookup or global scan.

`discovery` uses only generic P1a observations/references/validation and revalidates
Python DTO constructors. The pure comparator imports no SQLite/persistence/provider
adapter, reads no current manifest and never re-resolves frozen history.
Historical union includes accepted and candidate references, including accepted
non-set kinds. Candidate->accepted/reappearance/metadata changes do not create
novelty while the reference remains in the selected window. Same-batch identical
duplicates collapse with all indexes retained; incompatible duplicates fail.

New accepted set reference produces `SET_REFERENCE_FIRST_OBSERVED`; new candidate
of any existing kind produces one `CANDIDATE_REFERENCE_FIRST_OBSERVED`, including
set candidates. Candidates have no target and are not promoted. A new external
alias pointing to an old CMT UUID remains new reference evidence, never product
novelty. Events preserve original frozen state, current capture/token, contextual
reference and explicit evidence window. `first_observed_in_window_at` is bounded
to supplied captures, not release/global first appearance/local persistence.

No history gives explicit baseline/no events after validating current. Existing
empty history establishes a comparison window. Missing/rejected/corrupt/contradictory/
incompatible/failed evidence fails globally without partial events. No disappearance,
launch, stock, preorder, source health, notification or exactly-once claim exists.

## Early ARQ/DB-OWNER decision and architecture

The checkpoint reproduced ES/EN/empty batches sharing the same manifest context
fingerprint. STORAGE_V1 stores no empty namespace/kind/language declaration; the
hash identifies resolver context, not capture scope. Existing query stdout cannot
distinguish empty from missing. A reproducible author probe is retained in ignored
`.p4a-evidence/arq_checkpoint.py`; tests also reproduce this information loss.

[ADR-0005](../adr/0005-offline-temporal-discovery.md) adopts the compatible local
producer/caller assertion contemplated by the brief: submitting request context
explicitly attests every selected empty capture belongs to it. Output labels
`request_attested_empty`; the DB proves existence/capture/zero counts and rows
only. Nonempty `records_verified` requires every stored reference to match.
Neither authenticates the producer. A wrong empty assertion can cause false
relative novelty. Independently stored scope would need Orchestrator authorization
of a later persistence contract; it is not implemented or falsely inferred here.

The additive public `read_snapshots` opens one checked mode=ro/query_only connection
and BEGIN read transaction before ownership/schema/integrity/metadata/rows/target
closure checks. All selected evidence shares that transaction, with cleanup rollback/
close on success/failure. It never reuses writer BEGIN IMMEDIATE. Real concurrent
writer testing establishes commit waits until the consistent reader releases.
LIMIT1001 detects per-batch overrun; no truncated success. The global finite
budget covers SQL/locks and Python validation checkpoints, default2s/max5s.
Whole-file integrity can exceed practical budgets on growing DBs; OS/device stalls
remain outside that deadline guarantee. Business counts/indexes/status/provenance/
canonical UTC/target kind/language/variant/card number are checked separately.

[DISCOVERY_V1](../data-contracts/DISCOVERY_V1.md), compatible STORAGE_V1 and
LOGGING_V1 extensions document exact request/snapshot/output/errors/limits.
ASCII canonical sorted-key compact JSON drives `evt1:` and `cmp1:` SHA256 IDs.
Event identity includes version/type/context/reference/current token/capture;
comparison additionally binds sorted selected history and validated frozen content,
excluding first persistence/run ID/duration/path. Window changes alter comparison
identity; history permutation/replay/backup restore preserve results.

## DATABASE CHANGES, security, observability and debt

**NONE** to schema/migration/business data in Discovery. STORAGE_V1 SQL/schema1,
P1a identity, old APIs/codes, dependency inputs and lock remain unchanged. The new
reader performs no initialize/migrate/repair/write. No event/cursor/checkpoint/outbox
tables or destructive retention exist. Missing DB creates nothing; read-only
hot-journal recovery may fail when authorized writing would be required.

Strict request JSON uses existing 1MiB/depth16/nodes20000/string1024 limits,
duplicate-key rejection and canonical UUID validators. Max32 histories/33000
records/1000 events are fail-closed budgets. Per-record generic validation permits
the complete bounded history without wrongly imposing one request node cap on it.
Standard library only; product tests are offline with synthetic local fixtures.
Trusted directory/host ACLs, synthetic claims and administrative honesty remain
explicit trust boundaries, not authenticated facts or real-source rights.

Compatible logs add `discovery.completed`, safe result/category/run_id/duration,
batch_count0..33/discovery_observation_count0..33000/event_count0..1000. Prior
count limits remain unchanged. Error stdout counts are null/events empty; failure
log counts are omitted. Baseline/no_discoveries/error remain distinct. No payload,
arbitrary names/reference/token/path/SQL/raw exception enters stderr. Minimal
stdout evidence intentionally includes exact references/batches. Codes0/2/1
mean success/invalid request or evidence/local storage failure; old commands retain
their codes. Missing request is2 and missing DB1.

Threat/risk/runbook docs describe controls and residuals. TD-001–TD-004 remain open;
TD-005 records the persisted empty-scope proof gap with owner/exit/horizon. No source,
Pi, licensing or operational debt is closed by synthetic evidence. Fixture
provenance records invented UUIDs/fixed capture times/aliases/candidates/requests.

## Tests, environments and provisional execution

Lead integrated working-tree suite: **600 passed /1 Windows symlink-privilege skip**,
31.05s. Coverage **97.78% lines /94.41% branches**, all own runtime, no exclusions.
Ruff format/check and strict mypy pass. These are preliminary execution results;
the committed candidate must have reproducible independent/final hosted evidence.

DATA author138 tests; ARQ storage plus existing storage/backup82 pass/1 skip.
SEC independently ran23 CLI/log tests plus seven disposable-DB security assertions.
Author/SEC executions are supplementary, not QA/REVIEWER. SEC found and rechecked
two corrected Python-boundary issues (candidate-category allowlist and huge-int
serialization); author test setup/UUID assumptions were corrected without reducing
limits/gates. Independent final QA/REVIEWER findings will be recorded externally.
Precommit REVIEWER additionally identified impossible `missing_binding` states
under resolver_v1's unknown-variant/language precedence. The author added inverse
category validation plus generic and actual SQLite tampering regression cases,
without re-resolving history. Targeted core/storage120 tests passed; final full
candidate execution must include this correction and added tests.

Lead preliminary installed-wheel test proved site-packages import, empty PYTHONPATH,
outside-source processes, version/diagnose, five catalog cases, durable persistence
and Discovery. AMD64 and Compose preliminary smokes pass; ARM64 QEMU and final
candidate reruns are recorded externally when complete. Discovery harness checks
new alias to old UUID/targetless candidate/baseline/no_discoveries/attested empty/
incomplete/context/replay/missing DB/nonmutation/backup restore through separate
processes. Full logical DB content/schema/version remain equal before/after.
Containers check actual UID/GID10001 and /data0700, read-only fixtures/no network,
using unique disposable volumes with targeted cleanup; all prior smoke cases remain.

Local project Python3.13.15/SQLite3.53.1/uv0.12.10/gh2.100.0/Docker29.7.2.
Default system Python3.12.10 is not used for project gates. Containers observed
Python3.13.16/SQLite3.46.1; local QEMU version is not independently exposed and
must be distinguished from hosted QEMU metadata. Sandbox shell startup failed
before execution; automatically reviewed elevated execution worked. Docker Linux
daemon was initially stopped and started for tests. None is a source-health claim.
Audit found no known vulnerabilities; unchanged frozen dependency inputs were used.

Reproducible recipes are the P4a brief/QUALITY_GATES, unchanged frozen quality/
coverage/build/audit/scan commands and extended wheel/container shell scripts.
Windows uses explicit outside-source installed-wheel and Docker harness equivalents.
Hosted CI keeps exactly quality/Compose/AMD64/ARM64 jobs. Final run URLs/full log
hashes/metadata and PR temporary merge tree proof belong in the external ledger.

## Exact-candidate mandatory gates and AC-D01–D15

At this committed publication snapshot, the candidate SHA/reviews/CI do not yet
exist as final evidence. Every final gate below is therefore FAIL pending that
specific evidence, not N/A and not borrowed PASS. External exact-candidate ledger
may supersede these rows only with actual executions and independent review.

| Gate | Status / required evidence |
| --- | --- |
| Frozen install/lock, Ruff/mypy | FAIL pending exact candidate; preliminary commands passed |
| Unit/contract/SQLite/CLI/P0-P1a-P3a regression/coverage | FAIL pending exact candidate; preliminary600p/1s,97.78/94.41 |
| Build/outside-source wheel and legacy/new smokes | FAIL pending exact candidate package evidence |
| Audit/secret scan | FAIL pending exact candidate tracked-file scan/audit |
| ARQ/DB/SEC/SRE/docs | FAIL pending final exact-candidate independent review |
| Compose/AMD64/ARM64 QEMU | FAIL pending final exact-candidate runs/job bodies |
| Four final CI job bodies | FAIL pending published exact-SHA run and complete-body inspection |
| Distinct final QA/REVIEWER | FAIL pending detached exact-SHA execution/probes/review |

| AC | Status | Concrete traceability for final evidence |
| --- | --- | --- |
| AC-D01 | FAIL pending final scope review | Baseline Git objects above, attributed ROADMAP/P3a note, archives/ownership and preserved branches/worktrees |
| AC-D02 | FAIL pending final review | ADR0005/DISCOVERY/STORAGE/logging, `test_comparator_import_has_no_sqlite_provider_or_persistence_dependency` |
| AC-D03 | FAIL pending final execution | Empty/missing, complete frozen read, query_only/BEGIN and real writer-commit interleave tests in test_discovery_storage.py |
| AC-D04 | FAIL pending final execution | `test_new_reference_known_cmt_and_candidate_set_each_emit_once`, installed/container alias assertions |
| AC-D05 | FAIL pending final execution | Same test, accepted-other-kinds tests, targetless set candidate harness assertions |
| AC-D06 | FAIL pending final execution | Seen-union/candidate-to-accepted, metadata/window, reappearance and selected-window core tests |
| AC-D07 | FAIL pending final execution | Metadata changes, identical duplicates/index evidence and same-batch contradictions tests |
| AC-D08 | FAIL pending final execution | Exact context/null/variant/UUID/chronology tests and explicit empty attestation output |
| AC-D09 | FAIL pending final execution | Baseline/explicit-empty/rejected tests, missing/corrupt refusal and harness distinct outcomes |
| AC-D10 | FAIL pending final execution | Deterministic exact hashes/history permutation/window sensitivity plus independent backup/restore harness |
| AC-D11 | FAIL pending final execution | Strict bounded files/DTO forgery,33000 records/1000 events/max batch cases, lock/deadline/IO/schema/corruption probes |
| AC-D12 | FAIL pending final execution | Outside-source wheel/Compose/AMD64/ARM64 full legacy+Discovery harnesses, logical nonmutation and separate invocations |
| AC-D13 | FAIL pending final execution | test_discovery_cli.py/test_discovery_logging.py redaction/result/count allowlists and errors null/omitted |
| AC-D14 | FAIL pending final CI | Frozen quality/coverage/regression/audit/scan/build and four exact candidate CI job bodies; schema1 unchanged |
| AC-D15 | FAIL pending final reviews | Two detached independent agents, completion docs/runbook/threat/debt/provenance, external exact-head PR ledger |

## Limitations, open issues and recommendation

No remaining author-design blocker was found before publication. Final gates above
are required before readiness. Empty-scope attestation remains conditional local
trust (TD005), not stored proof; stronger requirements need Orchestrator decision.
Whole-file integrity and append-only history growth can exhaust a finite budget;
the bounded row maximum is not a throughput/size promise. Producer tokens are
selected explicitly, and window changes can legitimately change novelty.
Synthetic assertions/hashes do not authenticate history or grant retention rights.
QEMU/process/IO simulation cannot qualify physical Pi/power-loss durability.

Publish one PR without merge, verify unchanged base/head/tree/mergeability/checks,
and complete final independent reviews and four CI bodies in its immutable-candidate
ledger. Only with that evidence propose readiness to the Phase Lead/Orchestrator.
Any substantive correction creates a new SHA requiring new relevant gates/reviews.
Only the Orchestrator accepts/closes P4a or authorizes integration of an exact SHA.
