# P8c Integration Completion Report

**Status: INTEGRATION_VERIFIED — PASS. P8c phase remains OPEN.**

Prepared UTC: 2026-10-28T18:49:33.293368+00:00

## Authorization and scope

The supplied Orchestrator decision resolves RW-01 (PASS), accepts the exact corrected candidate and authorizes PR18 integration by merge commit. This report verifies that integration; only Orchestrator can accept and close the phase after review. P5 global, TD-001 through TD-005 and existing source blocks retain their accepted source states. No real Watchlist-to-Telegram delivery is enabled.

| Item | Exact identity |
| --- | --- |
| Repository / PR | KastaTM/card-market-tracker / [PR18](https://github.com/KastaTM/card-market-tracker/pull/18) |
| Authorized base | 228d5c8d0d91edf03ddb86a489c8232eeb7c08bc |
| Accepted HEAD | d82aba73d9bc0eb455f8664e3ccddc0134ea9d9c |
| Accepted and integrated source tree | dfd0414242cff364aad6082411ae88aef728783e |
| Real integration merge | [9dda9fba0aa9646a67596657d4ae9a7088903808](https://github.com/KastaTM/card-market-tracker/commit/9dda9fba0aa9646a67596657d4ae9a7088903808) |

The original authorization is preserved byte for byte in [ORCHESTRATOR_INTEGRATION_AUTHORIZATION.txt](ORCHESTRATOR_INTEGRATION_AUTHORIZATION.txt); its SHA256 is in preflight.json and the evidence manifest.

## Preflight and executed operations

PASS before any PR mutation: exact origin, repository, PR/base/head/tree, draft/open/unmerged/mergeable state, four completed successful checks on accepted HEAD, live main and source branch, auto-merge absent, branch deletion disabled, clean P8c checkout, every local ref and all 37 registered worktrees present and clean. All checks were repeated after leaving draft and before the single merge attempt. No product/documentation changes followed the accepted candidate.

An initial read-only helper called the repository metadata endpoint with an invalid trailing slash and received HTTP404. The endpoint was corrected before any GitHub write and the entire preflight then passed. This was not a repository identity discrepancy or permission bypass.

Commands actually executed (both exit 0; no automatic retries):

~~~powershell
gh pr ready 18 --repo KastaTM/card-market-tracker
gh pr merge 18 --repo KastaTM/card-market-tracker --merge --match-head-commit d82aba73d9bc0eb455f8664e3ccddc0134ea9d9c
~~~

Ready stdout was empty; stderr: Pull request KastaTM/card-market-tracker#18 is marked as "ready for review" (with CLI success checkmark). Merge stdout and stderr were both empty. Exact captured strings, UTC timestamps, exit codes and argv are in [ready-command.json](ready-command.json) and [merge-command.json](merge-command.json).

No squash, rebase, auto-merge, force push, branch deletion, fetch, reset, checkout, pruning, ACL/ownership modification, global Git configuration or branch-protection change was performed. Workstation commands needing network/evidence writes used punctual require_escalated without permanent prefix rules; this is not an administrator or persistent sandbox change.

See [preflight.json](preflight.json) and [post-ready-premerge.json](post-ready-premerge.json) for complete command/API evidence.

## Structural verification

PASS: GitHub confirms PR18 merged via real commit 9dda9fba0aa9646a67596657d4ae9a7088903808, with exactly two ordered parents:

1. 228d5c8d0d91edf03ddb86a489c8232eeb7c08bc
2. d82aba73d9bc0eb455f8664e3ccddc0134ea9d9c

Tree is exactly dfd0414242cff364aad6082411ae88aef728783e. The GitHub compare response contains zero changed files; its actual diff export is zero bytes (SHA256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855). API main and authenticated git ls-remote both identify the real merge. This is not the historical PR test-merge edbd41c4cf118dbf462674738ddfa05513a92379.

Proof: [postmerge-structural-verification.json](postmerge-structural-verification.json), [accepted-head-to-merge.diff](accepted-head-to-merge.diff) and [local-preservation-final.json](local-preservation-final.json). All 21 local branch heads and all 37 worktree registrations/HEADs remain unchanged; approved status checks return empty stdout/stderr for all 37; original checkout remains rework/p5b-rw03-publication-rollback at f80bc8cdb877946f37d76b09212d68dd8da3e246. The P8c worktree remains on the accepted feature HEAD. Historical local main (5175d5b09e8d412e11b2ddf4c24bff41df133843) was preserved. At 18:33:00Z, a fetch fast-forward refreshed only origin/main to the authorized real merge; origin/HEAD remains the unchanged symbolic alias. Actor is unknown and the Lead recorded no fetch command. See tracking-ref-readonly-facts.json, local-ref-anomaly.json and integration-readonly-review.json. Live remote main is the integration merge.

## New push/main CI and all harnesses

[Run 40737659939](https://github.com/KastaTM/card-market-tracker/actions/runs/40737659939), event push, branch main, attempt 1, head/actual checkout 9dda9fba0aa9646a67596657d4ae9a7088903808. All four jobs completed successfully. Each log contains the actual integration checkout SHA. No historical PR checks are substituted.

| Environment | Job | Result | Harnesses | RW-01 | Complete readable / exact raw log |
| --- | --- | --- | --- | --- | --- |
| compose | [122990457419](https://github.com/KastaTM/card-market-tracker/actions/runs/40737659939/job/122990457419) | PASS | 12/12 | PASS | [Readable](ci-compose.log) / [Raw](ci-compose.raw.log) |
| quality | [122990457834](https://github.com/KastaTM/card-market-tracker/actions/runs/40737659939/job/122990457834) | PASS | 12/12 | PASS | [Readable](ci-quality.log) / [Raw](ci-quality.raw.log) |
| container (linux/arm64) | [122990458373](https://github.com/KastaTM/card-market-tracker/actions/runs/40737659939/job/122990458373) | PASS | 12/12 | PASS | [Readable](ci-container-arm64.log) / [Raw](ci-container-arm64.raw.log) |
| container (linux/amd64) | [122990459543](https://github.com/KastaTM/card-market-tracker/actions/runs/40737659939/job/122990459543) | PASS | 12/12 | PASS | [Readable](ci-container-amd64.log) / [Raw](ci-container-amd64.raw.log) |

The 12 harnesses in every environment are catalog, observation persistence, discovery, pinned metadata, scoped discovery, multi-revision metadata, discovery journal, offline alert outbox, simulated Telegram delivery, watchlist, watchlist journal and Watchlist Signal Outbox. The twelfth includes genuine RW-01 conflicting originals rejected without mutation. Total: **48 harness PASS markers plus RW-01 in all four environments**.

[harness-matrix.json](harness-matrix.json) records each individual check. [ci-metadata.json](ci-metadata.json) preserves full run/jobs/steps. [ci-log-manifest.json](ci-log-manifest.json) records raw/readable hashes and terminal-control sanitization; readable exports remove no log lines. The exact raw exports are retained alongside them.

## Quality gates

| Gate | New push/main result |
| --- | --- |
| Frozen installs; Ruff formatting/lint | PASS; 178 files formatted, all lint checks pass |
| Strict mypy | PASS; 90 source files |
| Full pytest | PASS; 2250 passed, 1 pre-existing skip; no new skips |
| Runtime coverage | PASS; 94.15% lines / 88.31% branches; required 85% / 80% unchanged |
| Original independent QA/reviewer probes | Re-executed successfully by CI: 101 QA observations and 9 reviewer checks |
| RW-01 probes | Public-original invariant PASS; independent QA 17 checks PASS; distinct reviewer 28 checks PASS |
| Build and installed-wheel harnesses | PASS; sdist/wheel built, 12 installed-wheel harnesses pass |
| Dependency audit | PASS; no known vulnerabilities |
| Secret scan | PASS; no unreviewed candidates, 64 exact public digest matches |

The original QA probe explicitly reports preliminary observations and final_qa_acceptance=false. These are CI replays of previously independently authored probes, not invented new specialist sessions or new final acceptance. Candidate acceptance is the supplied Orchestrator decision; accepted and integrated source trees are identical. [quality-gate-summary.json](quality-gate-summary.json) contains exact steps and parsed probe outputs.

## Preservation, historical evidence and models

All four frozen design documents retain their accepted SHA256 values; the normative contract remains byte-identical to the original handoff ([freeze-integrity.json](freeze-integrity.json)). The integration introduces exactly the accepted candidate, with no additional edits to product code, source schemas/identities/writers, CLI, thresholds, migrations, dependencies, source interfaces or main documentation. New report/log artifacts are additive under the evidence prefix on a separate remote evidence branch; existing local branches and historical worktrees were preserved. The separately recorded tracking refresh was not a local branch/worktree rewrite.

Historical failure-first evidence is retained, not rewritten:

- Defective 360da646 candidate and historical green run40586563511: evidence commit 82570887057a1421ca24d2d8ceea09eb2db7e706; not valid correction/integration proof.
- Accepted d82aba73 correction and independent QA/reviewer/failure-first/recovery readbacks: [RW-01 report](https://github.com/KastaTM/card-market-tracker/blob/57bdf94391be307197df2a59526acf59bc6ff681/docs/evidence/P8C_RW01_d82aba73/RW01_CORRECTIVE_IMPLEMENTATION_REPORT.md). Historical PR run40685550482 and its virtual merge remain historical candidate evidence only.
- The historical connected-app branch-creation HTTP403 is a supplied prior fact; no such denial occurred in this normal authenticated gh integration.

Requested Lead profile: gpt-6.1-sol / Medium. This root session exposes no independently verifiable selector or effort; backend remains unverified. One independent read-only Git preservation reviewer (/root/p8c_integration_ref_review) was started after the tracking observation. The spawn tool accepted the requested gpt-6.1-sol / high input; effective backend remains unverified. This specialist authored no product or shared documents and did not perform final implementation QA. Historical specialist identities and observed spawn selectors remain in the accepted RW-01 report. See [model-profile.json](model-profile.json) and [historical-evidence-ledger.json](historical-evidence-ledger.json).

## Publication, readback and reproducibility

Only a new remote evidence ref is used for documentary publication; there are no additional main commits. The manifest covers every artifact except itself. Readback independently downloads GitHub blobs, checks Git blob SHA1, SHA256, byte length, exact local bytes, absence of missing/unexpected files and unchanged source outside the evidence prefix. Exact immutable evidence commit, final report URL and final readback receipt are pinned in the completion comment on PR18.

~~~powershell
python collect_integration_ci.py --state integration-state.json --output reexported
python readback_integration_evidence.py --commit EVIDENCE_SHA --prefix docs/evidence/P8C_INTEGRATION_9dda9fba --output downloaded --reference LOCAL_PUBLISHED --receipt readback.json
~~~

Public bundle readback: PASS at immutable evidence commit 54dbaab5a5dec17de726f7c10387de7ff9daf8a1, 33 artifacts checked byte for byte. Full receipt: [public-bundle-readback.json](public-bundle-readback.json). The final report snapshot is downloaded and rechecked before the completion comment is posted.

## Limits and handoff

Linux ARM64 evidence is GitHub-hosted QEMU, not physical Raspberry Pi qualification. No local Docker engine/container/image operation was performed during integration; prior Docker/uv infrastructure diagnoses are not substitutes for this CI. Product-network/socket tripwires remain zero and no Watchlist Telegram delivery is enabled. The one pytest skip is pre-existing, with no source or threshold changes. No CI failures or reruns occurred. The initial private blanket-ref equality assertion failed on the tracking refresh; the failure is preserved in local-preservation-initial-assertion-failure.json and reconciled against the exact preservation criterion by an independent read-only review. A historical cache access warning appeared in that specialist sandbox; the Lead approved read-only sweep verified all 37 statuses with empty stdout/stderr (privileged-readonly-worktree-statuses.json), without ACL/config changes. Fetch actor remains unknown; source identities and preservation criteria are verified. Full historical failures remain available separately.

**P8c remains OPEN for Phase Lead/Orchestrator integration review.** No phase closure or additional phase is declared.
