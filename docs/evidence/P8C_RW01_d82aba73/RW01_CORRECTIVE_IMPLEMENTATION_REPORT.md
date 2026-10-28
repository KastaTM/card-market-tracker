# P8c RW-01 Corrective Implementation Report

2026-10-28. **P8c OPEN ? REWORK_REQUIRED**, pending Phase Lead review.
Engineering correction and all applicable gates PASS. This does not automatically
restore the previous READY recommendation, accept the phase, authorize merge or
declare PHASE CLOSED. Stop for Phase Lead review after the final PR ledger
records publication/readback. No alternative product PR or new phase.

## Identity, baseline and status

[Existing PR18](https://github.com/KastaTM/card-market-tracker/pull/18), retained draft/unmerged.
Defective HEAD360da646892e46545ca70e8838bc3a2a89e460a3,
tree3ce94d6e214de74889475753807122b526085b98.
Corrected HEADd82aba73d9bc0eb455f8664e3ccddc0134ea9d9c,
tree dfd0414242cff364aad6082411ae88aef728783e, parent360da646.
Authorized baseline/live main228d5c8d0d91edf03ddb86a489c8232eeb7c08bc,
tree dde865b6d215efc4075918088d6deddfe7cdeb1f; ordered parents
62ecd7ab792a93a6071b83277d870f1d95f61f9f,
f80bc8cdb877946f37d76b09212d68dd8da3e246.
[Final preflight](final-preflight.json): corrected/original checkouts clean,
original remains rework/p5b-rw03-publication-rollback at f80bc8cd.
Historical local main5175 unchanged, never mistaken for published main228.
Initial36worktrees preserved; separate new reports worktree,total37.
No reset/removal/force/merge or ownership/ACL/globalGit config manipulation.

[13RWdelta and49full P8c candidate file/blob identities](candidate-inventory.json).
Only product delta is watchlist_alerts/storage.py; new tests/probes/harness/CI/docs
complete the13-file correction. The separate evidence branch adds only files
below docs/evidence/P8C_RW01_d82aba73; it never substitutes an artifact-tree SHA
for the reviewed product tree. The source candidate record predates CI and
explicitly defers final gate/AC dispositions to this external PR ledger.

## MODEL PROFILE USED and actual ownership

[Requested/observable/unverified profile](MODEL_PROFILE_USED.json).
Lead requested gpt-6.1-sol/Medium;High for critical integrity decisions. Actual
root selector/effort not independently exposed. Five actual new specialist spawn
arguments gpt-6.1-sol/high are observable; effective backend unverified.
Phase Lead GPT-6/High is user-reported. No backend/model introspection or
strongest-model escalation claimed.

| Session | Exclusive authoring / completed scope |
| --- | --- |
| /root | Public before/after probe; twelfth harness/CI/shared docs/Git/publication/readback |
| p8c_rw01_db | storage.py + test_watchlist_alert_rw01.py author;35regressions,128scopedPASS |
| p8c_rw01_arq | Read-only contract/identity/conflict analysis and fix readback; no runtime claim |
| p8c_rw01_sec | Read-only atomicity/corruption/Budget/failure review; no runtime claim |
| p8c_rw01_qa | New independent17case own probe, final clean candidate and public source/loader replay |
| p8c_rw01_reviewer | New distinct28check probe, all13files/35tests review and public publication readback |

Ownership assigned before parallel work; DB waited for actual pre-fix reproduction
before product edits. QA/REVIEWER authored only their own probe scripts, never
product or author tests. Previous360attestations were not reused as new verdicts.
[Full completed scopes](INDEPENDENT_REVIEWS.md),[QA](qa-final.json),
[REVIEWER](reviewer-final.json).

## Mandatory pre-fix reproduction and root cause

[Immutable original source](pre-fix-public-invariant-probe.py),
[original FAIL output](pre-fix-public-originals.log).
Source SHA2562d849cdbeae6b19395eb9c00520755a07748d0d1c3ddbb0373d1d1aa5c149725.
Executed before product changes on clean360da646/tree3ce94d6e,
CPython3.13.15/SQLite3.53.1. Two independently created genuine P5a/P5b pairs
share watch_id/revision1 but target_price_minor900/1000. Public initialize/add/
record/verify/enqueue APIs only; no source SQL mutation, DTO fabrication or
private writer. Baseline price1500 then500 yields legitimate eligible signals.

Both enqueues returned recorded with different signal/alert IDs; complete verify
and backup failed storage_corrupt. Source4files unchanged, zero sockets.
Failure exit1 is preserved, not relabeled PASS.
[Exact same executable after correction](post-fix-exact-same-probe.log) returns
identity_conflict/exit2 on second admission, counts1/1, byte-identical retained
outbox/alert/evidence/first timestamp and healthy verify/backup. Source2d hash
is identical across both executions; corrected HEAD/tree are explicitly recorded.

Root cause: selected-pair admission checks did not enforce the global complete
entry equality that the full verifier already required for(watch_id,revision).
The previous tests did not combine independently valid conflicting source
histories in one outbox; historical green CI therefore did not establish this
invariant. It remains historical evidence of the defective candidate.
[Original external wheel/new harness FAIL](old-wheel-new-harness-FAIL.log)
additionally proves the regression catches the installed defective product;
[wheel provenance](old-wheel-provenance.json),[archived binary digest](old-wheel-archive-hash.json).
[Author12pre-fixFAILs](db-pre-fix-12-failures.log) retained before code correction.

Reproduce from a clean source checkout/environment of the named commit:

    python PATH_TO_DOWNLOADED/pre-fix-public-invariant-probe.py --fixtures tests/fixtures --timeout 5
    python scripts/p8c_rw01_invariant_probe.py --fixtures tests/fixtures --timeout 5

The first downloaded source remains byte-exact; the committed public version has
only formatting/doc/import cleanup. [QA final artifact](qa-final.json) contains a
complete standalone archive-loader and exact command for original360negative
control, so no private helper or source path is needed.

## Diff, transactional correction and invariant

The writer now performs one full verified semantic fold within its existing
BEGIN IMMEDIATE and shared Budget, obtaining counts, canonical complete entry
map and the selected validated pair. Every retained pair undergoes bounded
cell/JSON/identity/result/transition/render reconstruction, not raw-hash trust.

Precedence after valid source/private-receipt admission:
1. Preexisting malformed/contradictory retained state/counts => storage_corrupt.
2. Same alert ID with valid different frozen content => existing replay_conflict.
3. New distinct alert ID whose complete canonical entry differs for the same
   watch_id/revision => identity_conflict/exit2, before INSERT/COMMIT.
4. Equal entries may coexist across aliases/signals/series; other revisions/
   watch IDs/products remain independent.

Full canonical entry includes version,cmt_id,watch_id,canonical_identity,
identity_digest,revision and all config fields(priority,enabled,target_price_minor,
restock_enabled,max_age_seconds). Alias/series never partition this invariant.
The verifier wraps the same full fold without weakening any checks/result.
Map/selected-pair authority lives only in one operation/transaction; no cache
crosses operations or recovery snapshots. No duplicate existing-pair fold.
Existing rollback clears expired SQL progress before rollback; no partial pair.
Postcommit response timeout can still follow a complete valid commit, the
existing documented ambiguity rather than a universal no-write-on-error claim.

No DDL/application_id/schema/identity/Budget/evaluator/source-writer modification.
No retries or new deadlines. Full admission fold is O(history), legitimately
storage_timeout at frozen capacity rather than unchecked success.
No migration/repair/deletion reconciles preexisting contradictory stores.
Preserve them and restore only a verified good backup to a NEW path.

## Twelve requested regressions and independent controls

| Requirement | Result | Concrete coverage |
| --- | --- | --- |
| 1 samewatch/revision,different entry/signal | PASS | genuine target900/1000 probe; author target/priority/freshness/restock/fullidentity matrix |
| 2 different destination | PASS | author same/other alias and independent QA/REVIEWER; twelfth harness uses rw01-other |
| 3 different series | PASS | genuine incompatible-source series variants; alias/series cannot evade entry key |
| 4 concurrent processes | PASS | two real processes/CLI: one recorded,one identity_conflict; healthy1/1 |
| 5 same semantic independent copies | PASS | aliases/series/sample-ID positive controls coexist, no false conflict |
| 6 different revisions | PASS | genuine revision2 with different config accepted separately |
| 7 different products/watch IDs | PASS | independent CMT/watch histories accepted |
| 8 ancient replay | PASS | source appends/new revisions + rejection, identical old replay/time/evidence |
| 9 retained bytes/counts/evidence/time | PASS | full before/after bytes and get/evidence/list comparisons on every rejection |
| 10 verify/backup after reject | PASS | counts exact; backup plus reopened copy independently healthy |
| 11 original source bytes | PASS | quiescent P5a/P5b source bytes before/after all relevant operations |
| 12 timeout/error between check/write | PASS | IO/timeout at first INSERT,evidence INSERT,COMMIT; same Budget and full rollback |

35new author regressions,128scopedPASS/25.17s:
[complete author log](db-scoped-final-128-pass.log).
Primary legitimate-source cases do not use private writer/SQL source edits.
Only clearly marked negative OUTBOX corruption fixtures use SQL to represent
preexisting invalid data; sources remain untouched. Existing same-ID content
conflict tests remain, plus new REVIEWER genuine different-ancestry same-ID case.

New QA17/17PASS default2 and explicit5, exact clean d82/tree dfd before/after.
New REVIEWER28PASS default2, no findings, all13files/final35tests inspected.
[Public QA readback/actual downloaded loader replay](qa-public-readback-5872a891.json)
reproduced EXPECTED_FAIL original360 from GitHub-recovered complete helper.
[Independent reviewer publication readback](reviewer-public-readback-5872a891.json)
verified14selected artifacts and three completed full raw job logs at that time:
36harness markers+3RWmarkers, real checkout/tree, no findings.
Those readbacks correctly reported ARM64 pending then; Lead separately verifies
the final fourth log below. No extra completed specialist work is invented.

## Quality gates on corrected candidate

| Gate | Result | Evidence |
| --- | --- | --- |
| frozen install/no dependencies/lock change | PASS | frozen-install-no-project.log and frozen-install-editable.log; uv --no-cache |
| Ruffformat/check | PASS | format.log / ruff.log;178files |
| strict mypy | PASS | mypy.log;90runtime source files |
| full unfiltered native pytest | PASS | full-suite.log;2250passed,1existing platform skip,8subtests,324.50s |
| Linux full unfiltered pytest | PASS | ci-quality.log;2250passed,1existing platform skip,276.34s |
| line/branch coverage | PASS | coverage.log +CI:94.15%/88.31%,unchanged85%/80% thresholds |
| sdist/wheel +external install | PASS | build.log and12individual wheel-* logs |
| dependency audit | PASS | dependency-audit.log andCI;no known vulnerabilities |
| secret scan | PASS | secret-scan.log andCI;64existing exact public digests,no unreviewed candidates |
| integration/concurrency/corruption/recovery | PASS | full suite/new35,17QA/28REVIEWER and12smokes |
| four new CI jobs/12harnesses | PASS | full logs/metadata below;attempt1 |
| new exactcandidateQA/REVIEWER | PASS | complete final artifacts and own public code |

No collection filter,new skip,broad scanner exception, threshold/deadline increase
or reduced acceptance fixture. First11harness Git blobs unchanged. Twelfth retains
full5checkpoints/4signals and adds genuine incompatible original-source rejection,
exact exit2/bytes/evidence/counts/healthy subsequent recovery in all4environments.
Oldcandidate run40586563511 is preserved and never substituted for new gates.

Reproduce from the corrected source (existing Python3.13; use --no-cache for prep):

    uv --no-cache sync --frozen --no-install-project
    uv --no-cache sync --frozen --no-build-isolation
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

## Four new complete CI logs

[Run40685550482](https://github.com/KastaTM/card-market-tracker/actions/runs/40685550482),
head_sha=d82aba73,attempt1,all4PASS. No failed-CI same-SHA rerun.
Actual checkout edbd41c4cf118dbf462674738ddfa05513a92379 has exact candidate
treedfd04142, parentsbaseline228/candidated82. This is only an Actions testmerge,
not integration into main. Every log records this actual checkout SHA.
[Full metadata/12markers per job plusRW01](ci-metadata.json),
[raw/sanitized digests](ci-log-manifest.json),[complete collector](collect_ci.py).
API logs preserve all output/steps; terminal controls only sanitized, existing
GitHub credential masking retained. Scoped attributes preserve artifact bytes.

| Job | Result | Elapsed | Full preserved log | Sanitized SHA256 |
| --- | --- | --- | --- | --- |
| [compose](https://github.com/KastaTM/card-market-tracker/actions/runs/40685550482/job/122806861332) | PASS | 0:03:35 | [ci-compose.log](ci-compose.log) | 89c5e8e1e2f28c0bcd5cd3ae316ccf82cd20a56da5a586629b408e843dd52142 |
| [container (linux/amd64)](https://github.com/KastaTM/card-market-tracker/actions/runs/40685550482/job/122806861943) | PASS | 0:04:29 | [ci-container-amd64.log](ci-container-amd64.log) | 3b14b50da3955c48e8832a39efa788511caf4ffdff9e357a2085fa5e605537cf |
| [container (linux/arm64)](https://github.com/KastaTM/card-market-tracker/actions/runs/40685550482/job/122806861716) | PASS | 0:59:25 | [ci-container-arm64.log](ci-container-arm64.log) | eefa6fc72ffc27b420796a1a1a7a195fa4327ee70a3bb1ddcd3cebafcaa52226 |
| [quality](https://github.com/KastaTM/card-market-tracker/actions/runs/40685550482/job/122806861711) | PASS | 0:06:14 | [ci-quality.log](ci-quality.log) | 8a1c944c9bbd7b3de056da2f29c0725c66e9dcd96caed28fbda13d76ab0fd0d0 |

Native/quality observed Python3.13.15/SQLite3.53.1. Container runtime records:
{"compose": ["3.13.16 3.46.1 uid=10001"], "container (linux/amd64)": ["3.13.16 3.46.1 uid=10001"], "container (linux/arm64)": ["3.13.16 3.46.1 uid=10001"], "quality": []}
ARM64 uses QEMU emulation. Full job duration is not a single-operation deadline
measurement or physical RaspberryPi qualification.

## AC-WA01..20 renewed assessment

All PASS entries assess engineering evidence on the corrected candidate.
AC-WA20 becomes effective only after final published report/artifact readback
is recorded by the PR ledger; no phase acceptance follows.

| AC | Result | Corrected-candidate evidence |
| --- | --- | --- |
| AC-WA01 | PASS | final-preflight.json,old/new SHA/tree,live main and frozen bytes |
| AC-WA02 | PASS | complete original admission tests plus genuine independent source cases |
| AC-WA03 | PASS | source onefold/receipt tests and one fresh writer fold/shared Budget instrumentation |
| AC-WA04 | PASS | full semantic reconstruction and complete-entry config/identity comparison |
| AC-WA05 | PASS | unchanged walt/wsig identities/golden vectors; independent stdlib identity controls |
| AC-WA06 | PASS | alias/series/equal-copy/revision/product controls accepted/rejected as required |
| AC-WA07 | PASS | newidentity_conflict2 preserves bytes/time/evidence/cardinality; ancient replay stable |
| AC-WA08 | PASS | real conflicting race,atomic pair and before-COMMIT error/timeout rollback |
| AC-WA09 | PASS | full renderer/preview/privacy/offline regressions retained |
| AC-WA10 | PASS | same complete verifier; preexisting corruption wins before candidate conflict |
| AC-WA11 | PASS | originals/recompute tests and four-source byte preservation |
| AC-WA12 | PASS | unchanged strict CLI/pages/errors/2smax5Budget;stable conflict exit2 |
| AC-WA13 | PASS | verify/backup/restore healthy after rejected attempt;fresh3recovery folds |
| AC-WA14 | PASS | zero product sockets,unchanged prior owners/schemas/writers/transport boundaries |
| AC-WA15 | PASS | allowlisted identity_conflict logging/privacy/threat/secret scan |
| AC-WA16 | PASS | 12harnesses?4environments and4explicit RW01 rejection markers |
| AC-WA17 | PASS | 2250fulltests,94.15/88.31coverage,all format/type/build/audit/security gates |
| AC-WA18 | PASS | freshQA17+REVIEWER28/all13files on exactclean d82/dfd,own public probes/readbacks |
| AC-WA19 | PASS | RWdocs/ownership/roadmap/runbook;four frozen documents unchanged |
| AC-WA20 | PASS | updated existingPR18,complete4logs/report/helpers and final public bytewise readback |

## Frozen design, history and residual risks

Final preflight records unchanged normative/accepted SHA256:
ADR79d2194800d3ae2e88b35669ff2cd6b8603d99210d25c6dccaa723292c6debd3;
APIacc47dcb491841851544db11da96dd58b4bb23f174a09a966207e9fa24ceae31;
Storage60aa73f5d12f3f6cc3df5c509f5a094fe71083e6808fd00c0fe740738b313ebf;
Orchestratore5af71ad901460abc5bdff1474c7230eaa781d70c2f67c46dd0ec43a70223e14.
Accepted design remains sound; no incompatibility needed schema/identity/ADR change.
Public identity_conflict2 already exists in frozen API; RWcondition documented in
corrective source record/runbook. Earlier source/writer/policy modules untouched.

[Original request](rw01-request.txt),all pre-fix failures,initial fixture mistakes,
oldCI/oldreports preserved. DB initial manifest fixture error is not a product
finding; QA Windows cleanup/coordinator CRLF checks corrected without product
changes. Canonical Git and working hashes are separately recorded. Historical
connectedHTTP403 preceded this work; current ordinary authenticated git/gh
publication succeeds. No credentials or permissions bypass.

The documented local Docker check failed at missing dockerDesktopLinuxEngine
pipe despite punctual escalation. No local container/image or QEMU controls run;
three local backup/restore timing controls unavailable. Required remote jobs
passed separately. No physicalPi,power-loss or hostile-admin certification.
Trusted directories/immutable source revisions,cooperative OS limits,no global
multiDB transaction/authenticatedproducer/copy-wide dedup/delivery consent remain.
P5global/TD-001..005 remain OPEN;no new debt concession or out-of-scope feature.

## Publication and handoff

Initial evidence5872a89191f817583fe5c23989ffa0f6a58c8be0 with50-artifact Lead
readback is preserved. New QA and REVIEWER publicly recovered their own source/
records and original failure; no private-helper-only evidence.
This final update adds ARM64,fullmetadata/report and independent readback records.
The final PR comment must bind its immutable evidence commit and exact bytewise
readback. Artifact-only commits never change the reviewed product SHA/tree.

RW-01 corrective engineering work/gates complete. Submit this report for Phase
Lead review. P8c remains OPEN?REWORK_REQUIRED until that decision; old READY is
not silently restored. No merge,PHASE CLOSED or new phase. Stop after report.
