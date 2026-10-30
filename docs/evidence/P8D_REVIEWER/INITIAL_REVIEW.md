# P8d independent final REVIEWER - initial working-tree review

Date: 2026-10-30. Actor: `/root/p8d_final_reviewer`.
Requested/selected profile: gpt-6.1-sol/high as attributed by Lead; effective backend/effort unverified.
Status: PROVISIONAL; exact final committed candidate verification remains pending.

This actor authored only `scripts/p8d_reviewer_probe.py` and files under this
reviewer evidence directory. No product, author tests, QA probes, Git/index/refs,
credentials or live Telegram operations were authored or changed. The source
pipeline and assertions were independently derived from frozen contracts/public
source; no author/QA tests or smoke helpers are imported. Native P8b receipt/result
DTOs appear only in fake sends. No actual Telegram client is instantiated.

Authorities read: AGENTS, P8D_DESIGN_ACCEPTANCE, ownership, complete ADR0015,
WATCHLIST_TELEGRAM_DELIVERY_V1 and STORAGE_V1, opening contract and engineering
brief. The implementation admission/policy/budget/storage/schema/transport/CLI and
additive root CLI/logging integrations were reviewed against those boundaries.

The initial branch HEAD remained the accepted design commit
`50fcb55a0b0e467bcb9d94561412a0f3c6ebc8f9`, tree
`d8d3eac1580dbfb3fa6aafcf94d033a8781204e2`, with uncommitted product work.
Those identities describe the design checkpoint, NOT the reviewed runtime
implementation. These provisional executions cannot establish a candidate gate.

## Findings

1. **Medium - manifest physical safety missing.** The CLI deferred manifest path
   passed directly to inherited `watch_validation.read_json` /
   `catalog.validation.read_json`; `stat()` followed links and no inode/nlink/
   ancestor reparse safety check was performed. Frozen storage section8 expressly
   includes manifest path and rejects multiple hardlinks/reparse paths. Independent
   reproduction built fresh genuine original stores and two hardlinks to its
   synthetic manifest: nlink2 was observed and review returned result=ok. The
   committed rejection oracle `manifest_multiple_hardlinks_refused` fails on this
   provisional implementation. See MANIFEST_GAP_PROBE_RESULT.json (17PASS/1FAIL).
   Lead was notified; remedy belongs to the product author/Lead, with no prior
   source-validator change required.

2. **Medium - durable send errors exited0 / omitted log category.** Source review
   found application.send returns result:error for durable429/permanent/uncertain
   outcomes while CLI dispatch always passed code0 to reporting. This contradicted
   frozen exit mapping and error completion logging. Lead acknowledged and fixed
   dispatch. Independently constructed genuine originals plus fake429 now produce
   exit1, rate_limited envelope and exactly one error completion carrying that
   category. No pre-fix executable FAIL is claimed: the finding was static and the
   concrete reproduction ran after the correction.

3. **Low - catalog name bounds32768 instead of128.** Source review found type,
   name and tbl_name guarded with32768 while frozen storage section3 sets128;
   SQL alone allows32768. Lead corrected guards. Independent SQL-recording oracle
   now observes all three128 bounds and SQL32768, PASS. No pre-fix executable FAIL
   is claimed.

## Reproduction

From the authorized P8d worktree:

```powershell
& .venv/Scripts/python.exe -B scripts/p8d_reviewer_probe.py
& .venv/Scripts/python.exe -B -m ruff check --no-cache scripts/p8d_reviewer_probe.py
& .venv/Scripts/python.exe -B -m ruff format --no-cache --check scripts/p8d_reviewer_probe.py
```

Python3.13.15 / SQLite3.53.1 Windows. Probe duration about10seconds, entirely fake
transport. Temporary SQLite/manifest fixtures are restricted to this reviewer
folder and removed after execution. Failures emit fixed probe/type/category only;
no message/evidence/routes/credentials are printed.

Independent checks cover literal34DDL/45catalog and two byte-literal NUL identity
vectors; fresh complete-manifest P5a/P5b/P8c admission with equivalent independent
copies and genuine incompatible full-entry RW01 rollback/healthy verify/backup;
private receipt copy/fake/reuse/mutation/wrong Budget/operation/expiry; durable
in_flight observed before fake HTTP plus an independent BEGIN IMMEDIATE proving
no SQLite transaction spans send; token/socket/Telegram-import denied fresh-process
confirmed replay; old/unknown/fresh-preparation restore quarantine; all three429
claims, exact cooldown, event-only watermark; missing receipt conservative outcome;
revalidation preserving historic claim snapshots; oversized message/nullable
clock/full-entry tamper rejection; explicit recovery/clock clamping/stale finalizer;
canonical padded cursor/filter oracle; two real sender processes/one fake effect;
actual child process exit77 during fake HTTP, reopen in_flight/recovery uncertain;
SQL catalog guard bounds and original source-byte nonmutation.

INITIAL_PROBE_RESULT.json preserves the17-check provisional run before adding the
manifest safety rejection. MANIFEST_GAP_PROBE_RESULT.json preserves the subsequent
18-check run including its actual failure. Initial probe development also exposed
incorrect DTO access, an incorrectly constructed fake DTO, a Windows probe-handle
cleanup error, nondeterministic too-short probe allowance, and temporary Ruff
issues; these were probe defects corrected locally, not product failures. They
are not represented as implementation FAIL/PASS evidence.

## Limits and pending work

Await Lead's exact committed final HEAD/tree, rerun these probes and inspect the
final product diff/source identity without product changes during execution.
Corrective changes invalidate affected provisional checks. This review does not
replace separate QA, author suite, four final CI jobs, thirteen installed/container
harnesses, physical power-loss/Pi testing or original-backed live qualification.
No live authorization was received or exercised; AC-WT20 remains
BLOCKED - LIVE_UNVERIFIED. No candidate acceptance, merge or phase closure is
asserted. Only the Orchestrator retains acceptance/closure authority.
