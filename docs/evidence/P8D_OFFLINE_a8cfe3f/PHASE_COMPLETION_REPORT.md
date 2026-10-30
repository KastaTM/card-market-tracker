# P8d Phase Completion Report — offline dossier

Date: 2026-10-30. Phase OPEN. Proposed phase status: **BLOCKED — LIVE_UNVERIFIED**.
Offline implementation and verification completed. No phase acceptance, readiness,
merge, protection change, force push or real Telegram call is authorized or claimed.
Only the Orchestrator accepts/integrates/closes.

## Candidate and authority

- Worktree: C:/Projects/card-market-tracker-p8d.
- Branch: feat/p8d-watchlist-telegram-delivery.
- Product [draft PR20](https://github.com/KastaTM/card-market-tracker/pull/20).
- Final source commit: a8cfe3f4e9e2bc50558f3a9aee13a1fbd9bf6abd; tree: 820ddbdfc278ada9b2d713a1c0b834f5d59e5dbd; parent:e14f9383d8c71dcf0b1df5b0115d936c1c81c85b.
- Product implementation parent: accepted design50fcb55a0b0e467bcb9d94561412a0f3c6ebc8f9,
  accepted tree d8d3eac1580dbfb3fa6aafcf94d033a8781204e2.
- Baseline/main:9dda9fba0aa9646a67596657d4ae9a7088903808,
  tree dfd0414242cff364aad6082411ae88aef728783e; ordered parents
  228d5c8d0d91edf03ddb86a489c8232eeb7c08bc and d82aba73d9bc0eb455f8664e3ccddc0134ea9d9c.
- PR19 remains the documentary draft; [original design evidence](https://github.com/KastaTM/card-market-tracker/blob/c19e2c7a710e05102407b0db379f6dcff6d9827e/docs/evidence/P8D_DESIGN_50fcb55a/README.md) is preserved.
- Explicit Phase Lead DESIGN_ACCEPTED/GateC authorization controls current scope.
  Attached archived documents supply technical requirements; they are not new
  authority for live calls. Earlier PROPOSED design labels are historical and
  superseded by P8D_DESIGN_ACCEPTANCE, without rewriting accepted frozen blobs.

Original checkout rework/p5b-rw03-publication-rollback remains clean at its
original f80bc8cdb877946f37d76b09212d68dd8da3e246. Historical refs/worktrees were
preserved; no reset, destructive clean, rebase or forced publication occurred.
[Identity/preservation proof](gates/IDENTITY_AND_PRESERVATION.json).

## MODEL PROFILE USED and ownership

The user requested Lead GPT-6.1Sol/Medium and High for critical engineering.
The root session exposes no selector/backend proof, so effective Lead model and
effort remain unverified. Specialist selection requested gpt-6.1-sol/high, as
recorded in source P8D_OWNERSHIP; selection arguments do not prove effective backend.
BE's qualification-tooling turn returned a usage-limit error; Lead took back
those paths and completed/tests the draft. No specialist success is inferred
from that interrupted turn.

Exclusive authors: BE/application-policy-budget-models-errors and own tests;
DB/schema-storage and own tests; Lead/CLI-adapter-logging-harness-CI-wrapper/docs
integration. Independent QA and distinct final REVIEWER authored only their own
probes/reports, with no product authorship. Ownership was assigned before
delegation and returned before integration. [Final read-only ownership](FINAL_OWNERSHIP.json).
QA and reviewer reports bind all 444 tracked SHA256s and pristine before/after
to the exact final commit/tree. Reviewer additionally read final QA evidence
and independently matched all 444 source hashes.

## Implemented behavior and design boundaries

New watchlist_delivery is a separate CMTZ/schema1 authority with exact frozen34
DDL statements,7 STRICT tables,45 catalog objects and immutable full-entry
watch/revision agreement. Genuine P5a/P5b/P8c original admission, complete manifest,
twelve-key pair stability, specific historical acknowledgement and content/route
consent bind a one-use instance/operation/Budget/path authority. Semantic binding
excludes only the P8c first-preparation operational timestamp.

Claim commits before one fake/native port dispatch without holding SQLite over
HTTP. Exact owner/attempt/state fencing, durable receipts, strict 429 only/manual
cap of 3 and conservative uncertainty prevent automatic resend. Confirmed replay
needs neither originals, token, transport import nor sockets. Restore is globally
and permanently quarantined before any lookup/replay/send, including deliveries
unknown to an old backup. No prior writer/schema/identity/transport authority or
earlier12Python harness implementation changed.

Root/old offline CLI routes remain lazy; new closed completion logging excludes
text, route identifiers and raw errors. One deadline starts before parsing;
checked-fd manifest input and original admission share the frozen aggregate.
Local timeout defaults to 2 s (maximum 5 s); remote operation defaults to 15 s (maximum 30 s), with
one nonrenewable original-admission ceiling of 5 s and reserved finalization
min(0.5 s, timeout/5). No helper starts a fresh allowance.
Qualification tooling is inert here and fake-tested only: exclusive private
dossier, exact external operator decision, durable hash-chained reservations,
nonrenewable <=8metadata/<=1send, crash marker and separate guarded replay.

Architectural/security documentation remains in candidate ADR0015, the two
WATCHLIST_TELEGRAM_DELIVERY v1 contracts, ARCHITECTURE, THREAT_MODEL, LOGGING_V1,
TESTING_STRATEGY, QUALITY_GATES, ownership, implementation record and two
operator runbooks. TD-001..005 and P5 global stay OPEN; P2/P6a/retail stay BLOCKED.
No new design concession, schema adjustment or identity revision was introduced.

## Gates and exact-candidate results

| Gate | Status | Scope |
| --- | --- | --- |
| A | PASS | Baseline/handoff/exclusive worktree evidence, remote baseline reconfirmed |
| B | ACCEPTED | Explicit Phase Lead Design Freeze decision; accepted original unchanged |
| C | PASS | Offline implementation; no Telegram invocation |
| D | PASS | Author/fault/concurrency regressions; full local quality and all 13 external-wheel smokes |
| E | PASS | Independent QA 22 + 6, distinct REVIEWER 18 + 5; exact candidate/pristine444hash proof |
| F | PASS | Four final CI jobs and all 13 harnesses PASS; full CI logs inspected at their GitHub URLs; complete document-body readback verified |
| G | BLOCKED | AC-WT20 LIVE_UNVERIFIED; real qualification not authorized |

Local full suite: **2494 passed, 1 skipped in 638.21s (0:10:38)**. The host-specific skip predates P8d; no new
skip/filter/threshold reduction was added. Runtime line coverage **93.22%**,
branch coverage **86.17%**, above unchanged 85/80 thresholds.
Frozen two-stage install,201-file format/lint,strict 100-source-file mypy,
build sdist/wheel, installation outside checkout, all 13 installed smokes,
dependency audit and secret scan PASS. Scan has 92 exact public digest matches,
0 unreviewed candidates; narrowly verified path/type/value entries preserve
wrong-path/type/value rejection. [Local commands/results](gates/RESULTS.json).

[Final CI workflow41122041749](https://github.com/KastaTM/card-market-tracker/actions/runs/41122041749),
normal attempt 1, on candidate head a8cfe3f4e9e2bc50558f3a9aee13a1fbd9bf6abd:

| Job | Result | Full job |
| --- | --- | --- |
| compose | PASS | [124290271458](https://github.com/KastaTM/card-market-tracker/actions/runs/41122041749/job/124290271458) |
| container (linux/amd64) | PASS | [124290271899](https://github.com/KastaTM/card-market-tracker/actions/runs/41122041749/job/124290271899) |
| quality | PASS | [124290271910](https://github.com/KastaTM/card-market-tracker/actions/runs/41122041749/job/124290271910) |
| container (linux/arm64) | PASS | [124290272321](https://github.com/KastaTM/card-market-tracker/actions/runs/41122041749/job/124290272321) |

[Full job-log inspection](CI_LOG_INSPECTION.json) confirms all 13 success markers
in installed-wheel/Compose/AMD64/ARM64 jobs, non-root/private data/no product
network and full fixture. GitHub PR checkout may be its synthetic merge HEAD;
published probe records prove its tree exactly equals reviewed tree 820ddbdfc278ada9b2d713a1c0b834f5d59e5dbd.
It is distinguished from the candidate/run head; no checkout-HEAD equality is invented.
Complete logs remain on the four linked GitHub Actions jobs; no raw CI log is re-exported here. No failed same-SHA job was rerun.

Local ARM64 uses Docker Desktop QEMU, not native hardware. The full new P8d
harness passed all fake-send/replay/recompute/recovery/quarantine checks.
Three actual full-fixture backup/restore controls, milliseconds, with explicit
per-operation local budget5s (within frozen max5):

| Control | Backup ms | Restore ms |
| --- | --- | --- |
| 1 | 1336.804 | 1396.389 |
| 2 | 1303.862 | 1310.036 |
| 3 | 1293.124 | 1301.596 |

[Measurement log](gates/containers/ARM64_MEASUREMENT_SUMMARY.json). Timing applies
to this host/full fixture, not maximum retained history or native Pi. Any extra
local replay logs are supplementary; the four complete CI bodies establish
all 13 per required environment. Job duration is not substituted for operation time.

Supplementary local all-environment repeats were stopped after mandatory final CI/all13 environments, full external wheel and measured local P8d QEMU gates passed. Nine completed supplementary ARM64 harnesses remain recorded locally; unexecuted supplemental steps are not claimed PASS. No CI job was canceled or rerun.

## Independent acceptance evidence

[QA attestation](qa/a8cfe3f/ATTESTATION.md):22/22 committed groups plus6/6 own extras.
[Final reviewer](reviewer/a8cfe3f/FINAL_REVIEW.md):18/18 normal committed groups plus
5/5 own extras, no outstanding findings.
[Reviewer consideration of QA](reviewer/a8cfe3f/QA_CONSIDERATION_SUPPLEMENT.md).
Complete runnable fake-only extra probes, helpers, sanitized results and public tracked-source hashes accompany
both reports. Committed independent probes and all author tests are in the already published immutable candidate. Mocking the installed-wheel guard occurs only in a
clearly labeled fake wrapper case; actual guard rejection was separately tested.

## Failure preservation

Historical baseline-to-candidate whitespace remains **FAIL**, seven received
Engineering Brief Markdown hard-break lines; the copied original checksum
CRLF FAIL remains in PR19 evidence with its original classification. No contract
was edited, no FAIL was converted to PASS and no whitespace rule was suppressed.
The new authored diff from accepted design passes whitespace independently.

Initial reviewer17PASS/1FAIL manifest-hardlink evidence, QA20PASS/2FAIL provisional
expectation corrections, failed construction diagnostics and provisional suite
results remain in source/worklog and copied reports. Candidate e14's normal
reviewer16PASS/2FAIL, separately labeled frozen-clock18PASS diagnosis and its
actual CI QualityFAIL are retained. Cause: old fixed test times triggered correct
clock_skew. The narrow corrective commit changed only the reviewer probe and
worklog; current source/probe passes normal exact final validation.
[CI failure classification](gates/CI_E14_FAILURE_CLASSIFICATION.json).
No product budget, state, schema or identity was relaxed.

## Individual acceptance criteria

PASS below qualifies the stated offline behavior only. AC-WT20 remains the
separate mandatory real-provider gate.

| AC | Status | Reviewed evidence/limit | Reproducible record |
| --- | --- | --- | --- |
| AC-WT01 | PASS | Baseline, ordered parents, original contract/brief/audit exact blobs and preserved checkout | [evidence](gates/IDENTITY_AND_PRESERVATION.json) |
| AC-WT02 | PASS | Independent CMTZ/schema1; exact 34 DDL/45 objects; unchanged P8b/P8c/P5a/P5b | [evidence](reviewer/a8cfe3f/EXACT_NORMAL_PROBE_RESULT.json) |
| AC-WT03 | PASS | Genuine original pipeline; incompatible originals/RW01; fabricated/reused authority rejected | [evidence](qa/a8cfe3f/committed.stdout.json) |
| AC-WT04 | PASS | Historical acknowledgement exact content/route binding and closed matching authorization | [evidence](qa/a8cfe3f/extra.stdout.json) |
| AC-WT05 | PASS | Independent literal-NUL oracle; provider+signal identity; alias/route conflict rollback | [evidence](reviewer/a8cfe3f/EXACT_NORMAL_PROBE_RESULT.json) |
| AC-WT06 | PASS | Global entry agreement under prepare/claim and verify; genuine incompatible original rollback/races | [evidence](qa/a8cfe3f/committed.stdout.json) |
| AC-WT07 | PASS | Two real processes/fake port; durable claim before HTTP; no SQL lock over dispatch; stale CAS fenced | [evidence](reviewer/a8cfe3f/EXACT_NORMAL_PROBE_RESULT.json) |
| AC-WT08 | PASS | Offline exact text/native P8b transport reuse; strict outcome/TLS/HTTP privacy regression. No live acceptance inferred | [evidence](https://github.com/KastaTM/card-market-tracker/actions/runs/41122041749/job/124290271910) |
| AC-WT09 | PASS | Durable fake receipt and persistent token/import/socket-denied replay without originals | [evidence](gates/containers/ARM64_MEASUREMENT_SUMMARY.json) |
| AC-WT10 | PASS | Valid429/cooldown/attempt3 cap; ambiguous and missing receipt conservatively nonresendable | [evidence](reviewer/a8cfe3f/EXACT_NORMAL_PROBE_RESULT.json) |
| AC-WT11 | PASS | Shared operation Budget, aggregateorigins5, reserve, clock regression and expired reservation block dispatch | [evidence](qa/a8cfe3f/extra.stdout.json) |
| AC-WT12 | PASS | Deep local fold versus original-backed recompute; bounded/tampered catalog rejected | [evidence](reviewer/a8cfe3f/EXACT_NORMAL_PROBE_RESULT.json) |
| AC-WT13 | PASS | Three-fold exclusive restore and global quarantine including unknown post-backup delivery/replay | [evidence](gates/containers/ARM64_MEASUREMENT_SUMMARY.json) |
| AC-WT14 | PASS | Fault-injection/crash/concurrency/fsync/link/sidecar/fencing tests; original byte nonmutation | [evidence](https://github.com/KastaTM/card-market-tracker/actions/runs/41122041749/job/124290271910) |
| AC-WT15 | PASS | Lazy offline CLI; guarded manifest/cursors/limits; strict durable exit/log category/privacy | [evidence](reviewer/a8cfe3f/EXACT_NORMAL_PROBE_RESULT.json) |
| AC-WT16 | PASS | All13 harnesses in external wheel, Compose, AMD64 and ARM64/QEMU; full fixture, read-only sources, UID10001/network-none | [evidence](CI_LOG_INSPECTION.json) |
| AC-WT17 | PASS | Full suite, coverage thresholds, frozen install, Ruff/mypy, sdist/wheel/external install/audit/scan; four final jobs | [evidence](gates/RESULTS.json) |
| AC-WT18 | PASS | Distinct nonauthor QA 22 + 6 and REVIEWER 18 + 5 on exact source; published runnable extras/results;444hashes stable | [evidence](qa/a8cfe3f/ATTESTATION.md) |
| AC-WT19 | PASS | Accepted frozen ADR/API/storage unchanged; acceptance, implementation, architecture/threat/logging/debt/runbooks/ownership linked | [evidence](gates/IDENTITY_AND_PRESERVATION.json) |
| AC-WT20 | BLOCKED | LIVE_UNVERIFIED. No specific operator authorization or provider qualification performed; token/route configuration uninspected | [evidence](../../runbooks/WATCHLIST_TELEGRAM_QUALIFICATION.md) |
| AC-WT21 | PASS | Complete remote commit/tree and every published document body recovered; source unchanged and failures retained | [evidence](PUBLICATION_READBACK.json) |

## Live blocker, limits and handoff

**AC-WT20: BLOCKED — LIVE_UNVERIFIED.** No actual token was inspected and no
getMe/getChat/sendMessage was called. No operator authorization for an exact
historical synthetic selection/private route has been supplied for execution.
The qualification runbook/wrapper define the reviewable future procedure,
exact candidate/selection/message/evidence/route binding, local-only token,
<=8metadata and<=1send cumulative cap including failures, durable receipt/reopen,
separate tokenless/socket-denied replay, source-byte checks and sanitized
independent review. Preparing/testing the tool is not a real preflight or receipt.
Future private configuration/selection must be supplied and specifically
authorized by the operator/Phase Lead; none is invented here.

Dedup applies to this active authority only; clones/different ledgers and coherent
privileged rewrites remain outside guarantees. Provider acceptance would not
prove human reading. Windows directory fsync is unsupported by this API;
file fsync is used, and Linux/process/QEMU tests do not establish physical Pi
power-loss durability. Original-store reads are not a distributed transaction.
Max-history timing is not inferred from this bounded fixture.

Automatic approval review rejected exporting the complete source/log/binary-artifact bundle. This narrower publication contains only sanitized review documents, fake-only probes and result JSON; complete CI/source evidence is inspected through its existing GitHub URLs. Original full local evidence, artifacts and failed retrieval attempts remain preserved. This limitation is explicit and does not authorize an alternative export of that full bundle.

The evidence branch is separate from product/runtime and cannot silently move
the reviewed candidate. The complete local dossier contains exact sdist/wheel/sourceZIP; LOCAL_ARTIFACT_HASHES.json records them. The immutable source candidate and all complete CI job logs already exist on GitHub and are linked instead of re-exporting their bytes;
MANIFEST.json binds public files and sanitization. PUBLICATION_READBACK.json is
created only after the first remote readback and appended in a separate evidence
commit; it binds that immutable published tree and blob observations without a
self-referential source-SHA edit. Product PR description links the final dossier.

Recommendation: Phase Lead review of completed offline dossier; retain
**P8d OPEN / BLOCKED — LIVE_UNVERIFIED**, draft product PR and all historical
evidence. No READY_FOR_ORCHESTRATOR_REVIEW, merge or phase closure.
