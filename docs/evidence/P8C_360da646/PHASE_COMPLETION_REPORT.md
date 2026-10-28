# P8c Phase Completion / Implementation and Integration Report

Prepared2026-10-28(Europe/Madrid); test times below are UTC.
P8c remains OPEN / IMPLEMENTATION AUTHORIZED. Engineering recommendation:
READY_FOR_ORCHESTRATOR_REVIEW, effective after the final PR publication/readback
entry confirms this evidence commit. Phase Lead makes its own readiness decision;
only Orchestrator accepts, authorizes integration or closes. No merge authorized.

## Candidate, source of truth and provenance

[PR18](https://github.com/KastaTM/card-market-tracker/pull/18).
Source branch feat/p8c-watchlist-signal-outbox.
Reviewed HEAD360da646892e46545ca70e8838bc3a2a89e460a3.
Tree3ce94d6e214de74889475753807122b526085b98.
Parent/base228d5c8d0d91edf03ddb86a489c8232eeb7c08bc.
Baseline tree dde865b6d215efc4075918088d6deddfe7cdeb1f; ordered parents
62ecd7ab792a93a6071b83277d870f1d95f61f9f,
f80bc8cdb877946f37d76b09212d68dd8da3e246.
[Final preflight](preflight-final.json) verifies objects, origin/live refs,
local branches/worktrees, clean candidate and original checkout. Original remains
rework/p5b-rw03-publication-rollback at f80bc8cdb877946f37d76b09212d68dd8da3e246.
Initial35 worktrees preserved; one separate evidence worktree added,total36.
No reset/removal/force/ACL/global Git configuration modification.

[All44 changed files/blob hashes](candidate-inventory.json).
The evidence branch evidence/p8c-360da646 contains reports/logs only above this
candidate, never changes PR HEAD/main and has no merge request of its own.
The committed candidate integration record predates final CI and explicitly
defers final AC/gate disposition to this PR evidence ledger; its BLOCKED rows
are preserved historical statuses, superseded by this report after readback.

Actual Actions test checkout:c08800bc7a255255a287ddce884ebe7ee749722f.
Parents baseline/candidate; tree exactly3ce94d6e214de74889475753807122b526085b98.
Actions run head_sha is360da646892e46545ca70e8838bc3a2a89e460a3. The test-merge
object is disclosed rather than misreported as the checked-out candidate commit.
It is not integration into main; main remains the authorized baseline.

## Models, ownership and actual specialists

[MODEL PROFILE USED](model-profile.json), [independent attestations](INDEPENDENT_REVIEWS.md).
Lead requested gpt-6.1-sol/Medium, High for critical decisions; actual root
selector/effort not independently exposed. No selection claimed.
Five actual specialist sessions have requested/observable spawn arguments
gpt-6.1-sol/high; backend unverified. No strongest-model escalation claimed.
Phase Lead chat model/profile is user-reported, not independently measured.

| Role/session | Authorship and observed work |
| --- | --- |
| Lead/root | Shared CLI/logging/harness/CI/docs, integration/Git, full gates and publication/readback |
| ARQ/BE p8c_freeze_arq | New errors/models/policy/render/application/init, additive P5b reader, domain/source/application tests, identity oracle/vector fixture |
| DB-OWNER p8c_freeze_db | New schema/storage, storage/recovery/real-process author tests |
| SEC/SRE p8c_freeze_sec | Read-only security/operability review; no runtime/author claims |
| QA p8c_qa | Independent own probe/oracles and supplementary helpers; no product/author-test writes |
| REVIEWER p8c_reviewer | Distinct final reviewer; own probe/oracles; all44-file review, no product/author-test writes |

Exclusive ownership preceded parallel work; shared Git/docs remained sequential.
Author sessions were relinquished before integration. QA/REVIEWER are actual
distinct nonauthor agents, not fabricated prior sessions or human GitHub approvals.

## Implementation and architectural boundaries

The new watchlist_alerts package admits one explicitly selected genuine P5b
signal and a local destination alias. Every call including ancient replay
revalidates complete MANIFEST_V1, exact historical P5a revision and original
journal. Minimal additive P5b helper performs one accepted complete deep fold
under one read-only transaction and shared Budget. Its existing writer/schema/
identity/evaluator/recovery APIs were not changed.

Pure policy/renderer reconstructs per-rule fresh NO_MATCH-to-MATCH evidence,
both normalized snapshots/results and wsig1_ relationships. Private single-use
receipt binds exact content, instance and issuing Budget; caller DTO/hash/
verified claims do not grant authority. New walt1_ identity uses the frozen NUL
domain separation and canonical alias/signal identity. Price/restock, aliases,
episodes, revisions, series and products remain isolated; no Discovery IDs made.

CMTY0x434d5459/schema1 is separate. Exact ten frozen SQL statements produce
three tables,four indexes(including autoindexes),six immutable triggers.
Owner/header/version+inode check precedes writable-open, then full literal schema
verification occurs in transaction. BEGIN IMMEDIATE atomically records intent/
evidence. Ancient replay preserves bytes/cardinality/first timestamp; conflicts
roll back. Real-process tests cover one record/one replay and crash boundaries.

Verify is local semantic reconstruction; recompute separately reopens originals.
Backup/restore use source/copy/independently reopened-copy folds before fsync/
exclusive publication, one deadline and safe own-link compensation. Foreign
replacement/sidecars/additional hardlinks/recovery evidence are preserved.

CLI supports init/enqueue/get/list/evidence-get/preview/verify/recompute/backup/
restore with exact versioned JSON/closed errors/exit codes. Default2/max5-second
cooperative Budget covers parsing/source/storage/recovery/serialization. Unchanged
P5a get receives residual time and immediate parent checks. Success checks the
deadline immediately before first stdout, then emits one completion event.
Renderer is bounded4096-byte UTF8, escaped deterministic synthetic plaintext.
Logging is allowlisted; no aliases/messages/samples/paths/SQL/credentials.
P8c help/errors/success do not import Telegram transport or open sockets.
P8a/P8b retain their existing schemas/identities/admission and reject this route.

## Frozen design and documentation

The accepted design and normative bytes remain unchanged in disk/Git/handoff:

| Document | SHA256 |
| --- | --- |
| ADR0014 | 79d2194800d3ae2e88b35669ff2cd6b8603d99210d25c6dccaa723292c6debd3 |
| API V1 | acc47dcb491841851544db11da96dd58b4bb23f174a09a966207e9fa24ceae31 |
| Storage V1 | 60aa73f5d12f3f6cc3df5c509f5a094fe71083e6808fd00c0fe740738b313ebf |
| Normative contract | e5af71ad901460abc5bdff1474c7230eaa781d70c2f67c46dd0ec43a70223e14 |

Accepted ADR design status is not candidate/merge/phase acceptance.
Architecture, threat model, LOGGING_V1, testing/quality gates, recovery runbook,
ownership, AGENTS and dated ROADMAP synchronized. P5b closure attributed to
Orchestrator chat; no invented remote closure comment. Historical reports kept.
No new technical-debt concession; P5global and TD-001..005 remain OPEN.

## Tests and quality gates

Windows CPython3.13.15 final unfiltered suite2215PASS,1existing skip,8subtests,
266.54seconds; [complete log](local-final-suite.log).
[Coverage](local-coverage.log):94.14%lines/88.30%branches, thresholds85%/80%.
Native skip: existing inability to create symlinks; [explicit check](local-existing-skip.log).
Linux quality independently2215PASS/1existing platform skip,217.87seconds and
94.14%/88.30%, verified in [full quality log](ci-quality.log). No new skips/filters.
Ruffformat/check174files,mypystrict90source files,frozen installs,sdist/wheel,
external installation,dependency audit and secret scan all PASS in quality.
No known vulnerabilities;64existing exact public-digest matches and no unreviewed
secret candidates; scanner/allowlist/thresholds unchanged.
Final native build/wheel P8c check:[build](local-build.log),[external wheel](local-wheel-p8c.log).

Reproduce from the candidate (use uv --no-cache when preparing Windows env):

    uv --no-cache sync --frozen --no-install-project
    uv --no-cache sync --frozen --no-build-isolation
    uv run --frozen ruff format --check .
    uv run --frozen ruff check .
    uv run --frozen mypy src
    uv run --frozen coverage run -m pytest
    uv run --frozen coverage json -o coverage.json
    uv run --frozen python scripts/check_coverage.py coverage.json
    uv run --frozen python scripts/p8c_identity_oracle.py --check
    uv run --frozen python scripts/p8c_qa_probe.py --fixtures tests/fixtures --timeout 5
    uv run --frozen python scripts/p8c_reviewer_probe.py --fixtures tests/fixtures --timeout 5
    uv build --no-build-isolation
    sh scripts/wheel_smoke.sh
    uv export --frozen --all-groups --no-emit-project -o requirements-audit.txt
    uv run --frozen pip-audit -r requirements-audit.txt
    uv run --frozen python scripts/check_secret_scan.py

## Four exact CI jobs and full preserved logs

[Run40586563511](https://github.com/KastaTM/card-market-tracker/actions/runs/40586563511),
pull_request,attempt1,all4PASS. No same-SHA reruns or failed CI attempts.
[Metadata/source checkout/48 markers](ci-metadata.json),
[raw and sanitized log digests](ci-log-manifest.json),
[complete reproducible collector](collect_ci.py).
Complete logs below remove only terminal escape sequences; all printable
output/steps remain, existing GitHub credential masking retained. Files preserve
their exact bytes using evidence-folder attributes, not global Git settings.

| Job | Result | Elapsed | Complete log | Sanitized SHA256 |
| --- | --- | --- | --- | --- |
| [compose](https://github.com/KastaTM/card-market-tracker/actions/runs/40586563511/job/122479425827) | PASS | 0:03:49 | [ci-compose.log](ci-compose.log) | b108d2769b9a81400d3ae84e95bfe9d37450528dca5fb968d7587bd677bc1783 |
| [container (linux/amd64)](https://github.com/KastaTM/card-market-tracker/actions/runs/40586563511/job/122479425825) | PASS | 0:04:19 | [ci-container-amd64.log](ci-container-amd64.log) | cbabb4305f653e1b63ce0797d9f52d4b3e6a26a10651b90b404b5a5deee122ac |
| [container (linux/arm64)](https://github.com/KastaTM/card-market-tracker/actions/runs/40586563511/job/122479425491) | PASS | 0:36:17 | [ci-container-arm64.log](ci-container-arm64.log) | b0e272503daf3be60f22a785447dc0669b17d6d40bd8622ef7a297ba9bb43a75 |
| [quality](https://github.com/KastaTM/card-market-tracker/actions/runs/40586563511/job/122479425832) | PASS | 0:05:01 | [ci-quality.log](ci-quality.log) | d72a5ca3d3d4b3ab1c8d67f454157eed9b24e1c35ed3eb4a980c8d897ac0acba |

Each job contains all12 PASS markers: catalog,persistence,discovery,pinned,
scoped,multi-revision,discovery journal,prior alert outbox,prior fake Telegram
delivery,watchlist,watchlist journal,new watchlist signal outbox.
Thus all12 pass in installed wheel,Compose,linux/amd64 and linux/arm64/QEMU.
The twelfth retains the normal full five-checkpoint/four-signal fixture, distinct
processes,replay/preview/recompute/recovery,private stores/UID10001 and no network.
Prior11 harnesses preserved. Remote QEMU is emulation, not Raspberry Pi hardware.
The full ARM64 job duration is not a product operation deadline measurement.

## Independent evidence and resolved findings

[Full local attestations and source links](INDEPENDENT_REVIEWS.md).
QA101checks+3fresh CLI cases PASS; additional complete public helpers prove
firststdout/immediateP5aget boundaries and6actual P8a/P8b rejection cases.
REVIEWER9own checks PASS and all44changed files reviewed. Both exact clean
candidate executions occurred before publication, with no later product change.
CI also reran both standalone main probes. Expected values use their own stdlib
references rather than production policy/evaluator/renderer/identity as oracle.

Failure-first findings were resolved before360da646:
foreign hot-journal recovery before wrong-owner rejection; missing immediate
post-P5aget timeout check; stdout ok after a slow logger exhausted the deadline.
Bounded header check, exact private P8c original reader and final-first-stdout
check/single completion reporting fix them. No frozen contract change needed.

## AC-WA01..20 assessment

Evidence status PASS below describes reproducible engineering criteria, not
Orchestrator acceptance. Publication/readback criterion becomes effective only
when the final PR ledger records successful readback of this report/evidence.

| AC | Result | Concrete evidence / rerunnable check |
| --- | --- | --- |
| AC-WA01 | PASS | preflight-final.json: baseline/tree/orderedparents, live main, original/phase clean, frozen byte identity; candidate ROADMAP/AGENTS/archive |
| AC-WA02 | PASS | tests/test_watchlist_alert_source.py and tests/test_watchlist_alert_application.py; QA full-manifest/exact-original-revision rejection matrix even on replay |
| AC-WA03 | PASS | QA single_held_journal_fold and forged/copy/mutation/differentBudget/reuse checks; source tests assert one accepted fold/one held snapshot |
| AC-WA04 | PASS | domain/storage tests and QA own complete evidence/result reconstruction; immutable schema and payload limits |
| AC-WA05 | PASS | p8c_identity_oracle.py --check, committed3literal vectors and independent QA stdlib/NUL preimages |
| AC-WA06 | PASS | QA alias_rule_episode_isolation and revision_series_product_isolation, own expected signals/results/identities |
| AC-WA07 | PASS | QA ancient replay after appends/new revision and invalid originals; application/storage conflict/byte/time/count tests |
| AC-WA08 | PASS | tests/test_watchlist_alert_concurrency.py: two real processes, between-insert/postcommit/publication crashes; atomic storage rollback tests |
| AC-WA09 | PASS | domain exact plaintext/golden/control/bidi/oversize tests; QA/REVIEWER own complete message byte references and fresh guarded CLI |
| AC-WA10 | PASS | storage hostile-cell/schema/trigger/coherently-rehashed tests; QA rehashed_invalid_result_local_fold |
| AC-WA11 | PASS | QA local_coherent_ancestry_is_not_origin_proof/original mismatch/missing-original cases; recompute/source byte tests |
| AC-WA12 | PASS | CLI/storage limits/cursor/filter/error/budget tests; QA/REVIEWER deadline/serialization/firststdout helpers |
| AC-WA13 | PASS | recovery fault matrix and real process publication tests; both independent probes assert3fresh fold connections/noearlypublication/deadline/retry |
| AC-WA14 | PASS | fresh guarded CLI zero sockets/Telegram imports; source byte assertions, foreign-hot-journal regression and6actual prior-route/owner helper checks |
| AC-WA15 | PASS | CLI structured allowlist/privacy/count-type sentinels; secret scan; threat model/LOGGING_V1; no sensitive raw data logged |
| AC-WA16 | PASS | ci-metadata.json48verified markers,12per installed-wheel/Compose/AMD64/ARM64 job; full normal fixture retained |
| AC-WA17 | PASS | full quality log: frozen install,Ruff,mypy,unfiltered2215tests,94.14/88.30coverage,sdist/wheel,external12harnesses,audit,scan;4jobsPASS |
| AC-WA18 | PASS | exactclean360da646/tree3ce94local independent QA+distinct REVIEWER attestations, complete public probes/oracles/helper source/results; findings resolved |
| AC-WA19 | PASS | four frozen hashes and synchronized architecture/logging/threat/testing/gates/recovery/ownership/roadmap; debt retained |
| AC-WA20 | PASS | PR18,complete4logs/report/helper source and final bytewise public readback recorded by final PR ledger; failures preserved; no merge/closure |

All test/probe paths above are committed at the reviewed candidate. Full file
links/blob identities are in candidate-inventory.json. The candidate phase
record contains the exact commands and additional failure-first test rationale.

## Preserved failures and limitations

Local raw predecessor attempts remain failures, not overwritten by later PASS.
Public records:[Windows setup metadata](historical-windows-setup-failures.json),
[logging regression](failure-logging-before-fix.log),
[P5a deadline regressions](failure-p5a-deadline-before-fix.log),
[foreign hot-journal author transcript](failure-foreign-hot-journal-author-transcript.md),
[editable wheel guard](failure-editable-wheel-prefix.log),
[scanner environment](failure-environment-secret-scan.log),
[QA helper attempt1](qa-prior-boundaries-attempt1.json).
DB pre-fix stdout existed only in its author tool transcript, transparently
reported rather than fabricated as an original raw log. Original huge Windows
logs are retained locally; public summaries preserve hashes/commands/root cause.
Their payloads remain in tests with bounded parameter IDs. No gate is weakened.

Historical connected branch-create HTTP403 was reported before this run; no
remote write claimed for it. This run's ordinary authenticated git/gh branch,
PR and evidence publications succeeded. No credentials/ACL/owners/groups were
extracted/modified or bypassed. Existing uv cache untouched; --no-cache used.

Local Docker engine pipe remained absent even with punctual escalation:
[build](failure-local-docker-build.log),[info](failure-local-docker-info.log).
No local container/image created; localCompose/AMD64/ARM64 remain BLOCKED.
Required remote environments passed separately. LocalQEMU unavailable means
three local backup/restore timing controls could not run; no local timing claim.
The contract allows that limitation when local emulation is unavailable.
No physicalPi,physicalpower-loss or hostile-admin qualification is claimed.

A subsequent optional specialist publication-readback task hit usage limit.
No new completed QA/REVIEWER readback session is invented. Completed independent
final candidate executions remain valid; Lead performs full bytewise GitHub
readback and CI independently executed the committed probes.

Trusted immutable origins/directories are assumed. No distributed atomic
three-DB snapshot,authenticated producer,global dedup acrosscopies,delivery
consent or current preference is inferred. Blocking OS/stdout cannot be hard
preempted; postcommit/postpublication errors may leave complete data and require
explicit verify/recovery. Physical cleanup is not promised under persistent
filesystem refusal. No provider/Telegram calls,scheduler,bulk,migrations or UI.

## Publication/readback and handoff

Initial evidence commit326636edf639219ef36e8390432082a5667e7acd and its30-file
bytewise readback are preserved; it correctly recorded ARM64 pending then.
This final evidence update adds the now-complete fourth log/metadata/report.
Lead must record the final immutable evidence commit and full readback results
in PR18 before presenting this recommendation. Full helper source is in public
JSON, so hashes/private paths are not the only reproduction material.
The PR source candidate remains360da646; changes in the evidence branch do not
substitute a new product candidate.

Recommendation to Phase Lead: READY_FOR_ORCHESTRATOR_REVIEW after final readback.
P8c stays OPEN. No merge,phase acceptance/closure or follow-on phase authorized.
P5global OPEN;TD-001..005 OPEN;P2/P6a/Discovery retail BLOCKED.
