# P8d Design Freeze submission

Date: 2026-10-30. Proposed status: OPEN / DESIGN REVIEW REQUESTED.
Gate A: PASS at documentary checkpoint1f3f9cabd9381e8f2833d89dcaf20961cffadac7,
tree c7f7a31767ae5e5ad7fbe90a78d7b15f9d0677f4.
Gate B: PROPOSED / AWAITING PHASE LEAD DESIGN ACCEPTANCE.
Implementation: NOT STARTED. Live: BLOCKED - LIVE_UNVERIFIED / NOT AUTHORIZED.
No merge, acceptance or phase closure recommendation.

This is an interim engineering handoff at the next required review gate, not
a Phase Completion Report or a claim that the later implementation gates pass.
The Phase Lead's CONTINUE GATE A decision authorizes work up to this review.
The contract/Brief require Phase Lead acceptance of design before Gate C.

## Baseline, branch, ownership and actual Git actions

- Worktree: C:/Projects/card-market-tracker-p8d.
- Local branch: feat/p8d-watchlist-telegram-delivery.
- Authorized base and fetched/ls-remote main:
  9dda9fba0aa9646a67596657d4ae9a7088903808.
- Base tree: dfd0414242cff364aad6082411ae88aef728783e.
- Ordered base parents: 228d5c8d0d91edf03ddb86a489c8232eeb7c08bc and
  d82aba73d9bc0eb455f8664e3ccddc0134ea9d9c.
- First Gate A documentation commit e7519257f435f8c5f8c709a070b9f6603f1ce25e,
  tree120cabf48614c238e99570a4a05fa713ae32476d.
- Gate A follow-up1f3f9cabd9381e8f2833d89dcaf20961cffadac7 adds narrowly
  scoped -text attributes as preventive exact-archive protection. Raw blob
  comparison proved the initial archived handoff already matched bytes.
- Branch/path did not exist and no matching worktree ownership was observed
  before exclusive creation. The original rework branch remains at
  f80bc8cdb877946f37d76b09212d68dd8da3e246 and its checkout remains clean.
  Historical worktrees/branches/evidence are preserved.
- Gate A commit was clean before proposed design edits began. Final design
  documentation is committed separately; run the probe and Git commands below
  at that exact commit to obtain final HEAD/tree/clean evidence without a
  circular self-embedded SHA.
- No push/PR/CI/merge/protection/credential changes. Git network operations
  were authorized fetch and remote read only; sandbox escalation succeeded.

[Preflight](P8D_PREFLIGHT.md) and
[machine-readable baseline](../evidence/P8D_GATE_A/baseline.json) preserve
actual observations, full worktree inventory and three source/ZIP/copy/archive
SHA256 checks. The archived contract is complete and unedited; old P8c RW-01
entries remain historical. P8c closure is attributed to the Orchestrator chat
decision recorded by the P8d contract, not an invented GitHub closure comment.

## Model profile used and disjoint specialists

[Ownership](P8D_OWNERSHIP.md) was written before delegation. Lead is the sole Git/
shared-doc integrator. All edits are in the new worktree.

| Role/session | Actual assigned authorship | Observable model arguments |
| --- | --- | --- |
| Engineering Lead / root | Git, shared docs, ADR0015, runbook, this report, design probe | Root selection arguments are not exposed; no model switch/backend claim |
| /root/p8d_arq_design | Proposed API document only | fork_turns=none, model=gpt-6.1-sol, reasoning_effort=high |
| /root/p8d_db_design | Proposed storage document only, including chronology revision | same explicit selection |
| /root/p8d_sec_design | Isolated security design report only | same explicit selection |
| Future independent QA | Not activated; no product authorship allowed | Not selected/run |
| Future distinct final REVIEWER | Not activated; distinct from QA/authors | Not selected/run |

GPT-6.1 Sol/Medium coordination and High critical design were the requested
profiles. Specialist selection is observable through spawn arguments; effective
backend/effort is not independently verifiable. These three specialists are
design authors/reviewers, not future independent runtime QA or final REVIEWER.
No overlapping edits occurred; handed-back ownership was reassigned explicitly
for the isolated DB/SEC chronology revision.

## Read-first dependency and authority map

| Boundary | Reused/read authority | Explicit exclusion |
| --- | --- | --- |
| P5a watchlist | Full MANIFEST_V1, exact immutable revision/entry and canonical identity through unchanged P8c original admission | No latest, preference rewrite, stored result or current consent inference |
| P5b journal | _verified_signal_bundle one ro/query_only transaction/full fold, genuine per-rule fresh transition, original evaluations | No invented signals or modified journal writer/schema/identity |
| P8c outbox | storage.verify, existing _get_pair, application.recompute, exact stable selected pair before/after, semantic source-alert eleven-key projection | No enqueue side effect, renderer/policy/schema/writer edit or new accessor needed |
| P8b delivery | Lazy TelegramTransport/TransportResult/Receipt only, exact accepted transport validation | No P8b application prepare/send, ledger reuse or broadened alt1:/evt3: authority |
| P8a Discovery outbox | Historical independent authority retained | No Discovery event fabrication or bridge |
| New P8d | Own ledger, consent, provider+signal identity, claim/result history, quarantine | No prior-store mutation or distributed four-store/remote commit |

Read/review inputs include context/AGENTS, architecture/operating model/roadmap,
ADRs0011..0014, source/API/storage/recovery contracts for P5a/P5b/P8a/P8b/P8c,
testing/quality/coding, logging, threat/debt and actual source/test/import guards.
The specialists' source anchors and limitations are recorded in their artifacts.

## Proposed exact design package

- [ADR0015](../adr/0015-manual-watchlist-telegram-delivery.md): separate authority,
  choices/alternatives/consequences/revisit conditions.
- [API v1](../data-contracts/WATCHLIST_TELEGRAM_DELIVERY_V1.md): complete
  canonical route/consent/binding schemas, original admission, sealed one-use
  authority, exact CLI/DTO/error/exit/cursor/time/outcome protocol.
- [Storage v1](../data-contracts/WATCHLIST_TELEGRAM_DELIVERY_STORAGE_V1.md):
  34 literal SQL statements; exact45-object inventory (7STRICT tables,
  14indexes including11autoindexes,24triggers), guarded materialization,
  immutable bindings/global entry map, claim/owner CAS and recovery.
- [SEC/SRE review](P8D_SECURITY_DESIGN_REVIEW.md): source-anchored reuse hazards,
  fixes and reviewed document hash snapshots; static design scope only.
- [Operator runbook](../runbooks/WATCHLIST_TELEGRAM_DELIVERY.md): offline
  preview/review/acknowledgement, future exact command sequence, conservative
  failure/recovery/restore actions and inert separate live qualification.
- Additive architecture/threat/logging/testing/gates/debt/maps reference this
  proposal; existing dated history and prior runtime code stay unchanged.

CMTZ=0x434D545A/1129141338 is proposed for
card-market-tracker.watchlist-telegram-delivery/schema1. Source+embedded SQL
audits found seven prior allocations CMT1/A/D/J/Q/W/Y and no CMTZ collision.
This is repository-local evidence, not a global external allocation claim.

The identity remains the exact mandated wtdl1_ provider+signal/NUL formula.
First accepted alert/alias/route/content binds forever in this ledger.
Specific acknowledgement SYNTHETIC_HISTORICAL_DEMONSTRATION plus selected
signal/revision/message/evidence/route/full-binding commitments is mandatory.
No generic yes or historical enabled preference grants consent.

Full retained entry equality for each watch_id/revision is checked before
prepare/claim commit and by verify; no alias/series partition. Claim is durable
before one HTTP send; owner/attempt/state CAS fences all late outcomes.
Only strict429 permits later manual retry, maximum3 lifetime claims; third429
is permanent_failure/retry_exhausted. All ambiguous postclaim outcomes are
uncertain or blocked in_flight. No automatic resend, force or quarantine lift.

Global quarantine is inspected before lookup/confirmed replay and under claim.
Healthy confirmed replay requires only local ledger/binding/receipt, no originals,
token/transport import or sockets. Restore quarantines staging durably before
exposure, covering omitted/new deliveries as well as known rows.

## Design review corrections and remaining risks

Lead/DB/SEC resolved two chronology gaps before submission:

1. A claim retains immutable route_validated_at copied from the current validated
   route under the claim lock. Old claims compare against their own snapshot,
   not a newer route validation; local fold checks registered<=snapshot<=claim
   and snapshot<=current validated_at. No route/binding/delivery identity changes
   and no validation-history table is needed. This is local recorded evidence,
   not cryptographic proof a provider call occurred.
2. operational_high_water bounds persisted EVENT times only. Future cooldown
   not_before, source historical dates and provider accepted_at are excluded.
   A later global watermark is not a retroactive lower bound on old events.

Other resolved design mismatches: runbook uses the exact flat review object
inside the envelope; logging allows only delivery/attempt IDs, states/counters,
not source IDs/digests/aliases; recovery rollback records clock_skew; transport
category/cap mappings agree; semantic source_alert excludes only operational
P8c first_prepared_at. API static source-taxonomy check found38 inherited
categories and zero missing names/exit mismatches.

Qualification instrumentation can reserve durable conservative request upper
bounds before narrow transport method calls (destination validation2, bot1,
send1). Failed methods do not expose actual per-HTTP counts; never claim they do.
These reservations enforce <=8metadata/<=1send without changing P8b transport.
A failed/ambiguous qualification call consumes the sole send reservation.

Remaining operational limitations are explicit: one trustworthy live ledger,
trusted directories/ACLs, immutable originals/no global snapshot, maintained UTC,
capacity/headroom and cooperative filesystem/SQLite/stdout deadlines. Native
Pi power loss, privileged coherent rewrites and clone-wide dedup are unverified.
Full folds can exhaust2s/max5s, especially QEMU; no reduced checking or widened
timeout is proposed. These are constraints to test, not waivers or new debt.
P5global/TD-001..TD-005 stay OPEN; P2/P6a/retail Discovery stay BLOCKED.

## Actual design-only verification and reproducibility

The [standalone probe](../evidence/P8D_GATE_B/design_probe.py) imports only stdlib,
reads current source/docs/Git, uses SQLite :memory: and creates no database file.
It checks exact archived raw Git blobs, seven source allocations/CMTZ absence,
two literal164-byte/NUL format vectors, all34DDL statements/45objects,
SQL inventory/STRICT/integrity/FK, full embedded author SQL probe, preserved
product paths, added local Markdown links and input document hashes.
It reports observed HEAD/tree/clean state and its precise non-runtime scope.

DB's first memory-only draft rejected32 invalid actions. The chronology revision
supersedes it with35 rejections plus old-claim/later-revalidation and future-
cooldown checks. Both results and full executable probe source are retained in
the storage document. No product authority, original-backed RW-01 race,
concurrency, backup durability or live effect is established by these shape-only
SQL fixtures. Lead re-execution is author integration, not independent QA.

Targeted Ruff format/check applies only to this new documentary probe. The first
check found two E501 long digest lines; both were split without rule suppression.
The first integrated link probe failed because this handoff file was not yet
created. The SQL/vector portions had completed; no partial overall PASS was
claimed. These construction failures and final results are recorded in
[validation history](../evidence/P8D_GATE_B/validation_history.md).

From the final documentary commit, run:

~~~powershell
git show -s --format='%H %T %P' HEAD
git status --porcelain=v2 --branch
git diff --check 9dda9fba0aa9646a67596657d4ae9a7088903808 HEAD
git diff --exit-code 9dda9fba0aa9646a67596657d4ae9a7088903808 -- src tests scripts .github pyproject.toml uv.lock Dockerfile compose.yaml docker-compose.yml
& 'C:\Projects\card-market-tracker\.venv\Scripts\python.exe' -B -m ruff format --check docs/evidence/P8D_GATE_B/design_probe.py
& 'C:\Projects\card-market-tracker\.venv\Scripts\python.exe' -B -m ruff check docs/evidence/P8D_GATE_B/design_probe.py
& 'C:\Projects\card-market-tracker\.venv\Scripts\python.exe' -B docs/evidence/P8D_GATE_B/design_probe.py
git -C C:/Projects/card-market-tracker status --porcelain=v1
~~~

The existing interpreter is used read-only with -B; no install/environment
mutation. Any Python3.13 interpreter with compatible SQLite can run the stdlib
probe; the path above is the actual observed local invocation. Final committed
evidence contains input hashes and the script; a postcommit rerun reports exact
commit/tree. Publication/readback and runtime checks remain NOT RUN.

## Gate and acceptance ledger at this handoff

| Gate | Individual state | Evidence / next dependency |
| --- | --- | --- |
| A preflight/documentation | PASS | exact fetched baseline, exclusive clean worktree, matching handoff/archives, ownership, attributed maps; Gate A checkpoint above |
| B Design Freeze | PENDING PHASE LEAD REVIEW | complete proposed ADR/API/storage/runbook and design-only probes; no acceptance inferred |
| C implementation | NOT RUN / BLOCKED | requires B acceptance |
| D offline runtime/harness | NOT RUN / BLOCKED | requires implementation; no fake acceptance claimed |
| E independent QA/final REVIEWER | NOT RUN / BLOCKED | future distinct nonauthors on exact product candidate |
| F quality/CI/publication | NOT RUN / BLOCKED | full runtime gates/four jobs/13harnesses not executed |
| G live AC-WT20 | BLOCKED - LIVE_UNVERIFIED | no specific live authorization, credentials or real calls |

| AC | State now | Evidence / outstanding |
| --- | --- | --- |
| AC-WT01 | PASS | Gate A exact baseline/archive/attribution evidence; not a phase acceptance |
| AC-WT02 | BLOCKED | prior paths unchanged; separate ledger/transport implementation not run |
| AC-WT03 | BLOCKED | proposed complete admission only |
| AC-WT04 | BLOCKED | exact acknowledgement/binding designed, not executed |
| AC-WT05 | BLOCKED | format vectors checked; production authenticity/dedup not implemented |
| AC-WT06 | BLOCKED | SQL/global-map design only; genuine incompatible-source/process tests pending |
| AC-WT07 | BLOCKED | memory CAS shape probes only; durable two-process send tests pending |
| AC-WT08 | BLOCKED | accepted transport inspected; new route/receipt/text execution pending |
| AC-WT09 | BLOCKED | no product receipt/reopen/confirmed replay |
| AC-WT10 | BLOCKED | SQL outcome probes only; product transport/cooldown/skew pending |
| AC-WT11 | BLOCKED | budget protocol specified, runtime supervision/aggregate tests pending |
| AC-WT12 | BLOCKED | verify/recompute design only |
| AC-WT13 | BLOCKED | memory flag guard only; exclusive restore/durable global quarantine pending |
| AC-WT14 | BLOCKED | filesystem/crash/ENOSPC/fault injection not run |
| AC-WT15 | BLOCKED | exact CLI/DTO/logging designed; imports/privacy/installed behavior pending |
| AC-WT16 | BLOCKED | thirteenth harness not implemented; prior12 unchanged |
| AC-WT17 | BLOCKED | no complete suite/coverage/build/audit/secret scan or four final jobs |
| AC-WT18 | BLOCKED | no independent runtime QA/final REVIEWER |
| AC-WT19 | BLOCKED | proposed synchronized design package; implementation candidate not accepted |
| AC-WT20 | BLOCKED - LIVE_UNVERIFIED | explicitly unauthorized; no metadata/send/credentials |
| AC-WT21 | BLOCKED | interim handoff only; final report/publication/readback pending |

## Phase Lead decision requested and next authorized step

Review this exact proposed design package and accept or return design rework.
The required acceptance is design only. Until it arrives, no product schema,
definitive identity implementation or writer may begin. After acceptance,
implement failure-first original admission/consent/global-invariant and
claim/fencing/quarantine tests, then offline product code under assigned owners.

First independent negative tests to reserve for future QA: genuine incompatible
watch/revision originals and race rollback; counterfeit/copy/Budget-renewal
authority; missing originals/changed selected pair; two senders with durable
claim observed before fake HTTP; crash after possible acceptance; late owner
after quiesced recovery; confirmed replay under token/import/socket denial;
old empty restore plus post-backup unknown signal; revalidation after old claim;
future cooldown/high-water; aggregate-origin timeout and raw privacy sentinels.

No specific operator live permission is sought at this design stage. Even after
design acceptance, AC-WT20 remains separate and unauthorized until the later
offline candidate/gates/dossier exist.
