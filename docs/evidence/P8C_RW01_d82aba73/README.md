# P8c RW-01 evidence - new candidate, ARM64 pending

Prepared2026-10-28. P8c OPEN / REWORK_REQUIRED.
Old engineering READY recommendation suspended by Orchestrator/Phase Lead.
No merge/PHASE CLOSED/new phase. Existing PR18 is the only product PR.

Corrected HEAD d82aba73d9bc0eb455f8664e3ccddc0134ea9d9c.
Tree dfd0414242cff364aad6082411ae88aef728783e.
Parent defective360da646892e46545ca70e8838bc3a2a89e460a3/tree3ce94d6e214de74889475753807122b526085b98.
Authorized baseline228d5c8d0d91edf03ddb86a489c8232eeb7c08bc remains published main.
This separate reports-only evidence branch never changes the reviewed candidate.

## Failure first, same executable before/after

[Original exact probe source](pre-fix-public-invariant-probe.py),
[pre-fix FAIL](pre-fix-public-originals.log),
[post-fix PASS using unchanged source](post-fix-exact-same-probe.log).
Probe SHA2562d849cdbeae6b19395eb9c00520755a07748d0d1c3ddbb0373d1d1aa5c149725.
Python3.13.15/SQLite3.53.1. Only public APIs create two genuine P5a/P5b source
pairs with same historical key/different target900/1000. Old360 returns two
recorded, then verify/backup storage_corrupt. Correctedd82 returns recorded then
identity_conflict/exit2; first bytes/alert/evidence/timestamp/counts unchanged,
verify/backup healthy, all4sources unchanged, zero sockets.

Run from a clean matching source checkout with Python3.13 (both source versions
are immutable Git commits; no private helper/SQL/writer entrypoint needed):

    python pre-fix-public-invariant-probe.py --fixtures tests/fixtures --timeout 5

[Old verified installed wheel + new harness FAIL](old-wheel-new-harness-FAIL.log);
[old wheel provenance](old-wheel-provenance.json),[archived binary hash](old-wheel-archive-hash.json).
Original wheel retained locally; source360 and complete control code are public.
[Author12pre-fixFAIL](db-pre-fix-12-failures.log);
[author final128scopedPASS](db-scoped-final-128-pass.log).
Original run40586563511/evidence82570887057a1421ca24d2d8ceea09eb2db7e706 preserved
as historical defective-candidate evidence, never used as RW-01 proof.

## Corrective behavior and fresh independent review

One complete bounded semantic fold inside BEGIN IMMEDIATE yields transaction-local
canonical complete entry map and selected pair. Preexisting corruption wins;
same-ID valid frozen-content mismatch retains replay_conflict; new-ID same
watch/revision incompatible entry fails identity_conflict2. Verifier full checks,
fresh recovery folds, frozenDDL/IDs/default2max5Budget unchanged. Only product
storage.py changed; no source/prior owner/schema writer changes.
[RW-01 directive](rw01-request.txt) is archived as supplied; no design reopening.

New QA17cases PASS default2 AND explicit5; original isolated-package same-probe
control EXPECTED_FAIL. [Complete final artifact/source loader](qa-final.json).
QA source at reviewed candidate:scripts/p8c_rw01_qa_probe.py.
New REVIEWER28cases PASS default2, all13deltafiles/35authorregressions reviewed,
[complete final attestation](reviewer-final.json).
Reviewer source:scripts/p8c_rw01_reviewer_probe.py.
Both final new d82/tree checks clean before/after; prior360reviews not reused.
Git canonical LF and Windows working CRLF hashes are separately recorded;
normalization is not a source change. [Actual model profile](MODEL_PROFILE_USED.json):
requested/observable spawn gpt-6.1-sol/high, effective backend unverified;
root selector/effort not independently exposed.

    uv run --frozen python scripts/p8c_rw01_qa_probe.py --fixtures tests/fixtures --timeout 5
    uv run --frozen python scripts/p8c_rw01_reviewer_probe.py --fixtures tests/fixtures --timeout 5

## New gates and publication status

Native unfiltered2250PASS,1existing skip,8subtests,324.50seconds:
[full suite](full-suite.log),[coverage94.15/88.31](coverage.log).
Frozen installs,178filesformat/check,mypystrict90src,audit/scan/build PASS;
64existing exact public digest matches, no unreviewed secrets. No gate weakening.
All12outside-source installed-wheel harnesses PASS; individual complete logs here.
Twelfth retains five checkpoints/four signals and adds a genuine incompatible
source pair, exit2+byte-preservation+healthy recovery regression.
First11harness Git blobs unchanged.

New run40685550482 attempt1, associated head d82aba73.
[quality](ci-quality.log),[Compose](ci-compose.log),[AMD64](ci-container-amd64.log) PASS.
ARM64/QEMU is pending at this publication; final mandatory four-job gate not yet
complete. No READY claim. [Completed-job digests](ci-completed-before-arm64.json).
[Collector](collect_ci.py) validates actual testcheckoutedbd41c4cf118dbf462674738ddfa05513a92379,
whose tree is exactlydfd04142, parentsbaseline228/candidated82. No merge into main.

Complete API logs only sanitize terminal controls; all output/steps retained,
GitHub masks credentials. Evidence-folder attributes prevent newline conversion
altering artifact hashes; no global Git configuration changed.

## Provenance, history and limits

[candidate inventory](candidate-inventory.json) contains13RWdelta blobs and49
full P8c-from-baseline blobs. [preflight](preflight.json) records refs/worktrees.
Initial36worktrees preserved; one new evidence worktree added. Historical local
main5175 is unchanged and not confused with published main228.

[Local artifact provenance](local-evidence-manifest.json).
Own fixture mistakes (DB initial manifest and QA Windows cleanup/coordinator
line-ending checks) are not product findings; their records remain separate.
Raw execution logs kept locally, public copies redact user/worktree path prefixes.
No original failure/code/CI overwritten.

Local Docker info still fails absent dockerDesktopLinuxEngine pipe despite
punctual escalation. No local container/image/config/ACL change; localQEMU timing
unavailable. Mandatory remoteARM64 still required; no physicalPi certification.
Trusted directories/immutable revisions; no global multiDB atomicity/authenticated
producer/dedup acrosscopies or send consent. Preexisting contradictory stores
remain corruption, never auto-repaired/migrated/pruned. Only verified good backup
restore at a NEW path can recover earlier valid history. Full admission folds
can legitimately exhaust unchanged2s/5s Budget on larger histories.
P5global and TD-001..005 OPEN. Await Phase Lead after final corrective report.
