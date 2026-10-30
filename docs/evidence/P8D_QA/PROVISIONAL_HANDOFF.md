# Independent P8d QA provisional handoff

Date: 2026-10-30. Actor: /root/p8d_qa_independent, NONAUTHOR.
Requested/selected gpt-6.1-sol/high; effective backend not independently verified.
Product authors: separate BE/DB/Lead actors; this actor edited no product or author tests.
Current status:22 independent case groups PASS on changing implementation worktree.
This is NOT a final-HEAD/tree attestation, candidate acceptance, live PASS or closure.
The observed branch remains feat/p8d-watchlist-telegram-delivery; execution occurred
before the Lead supplied a final product candidate commit/tree.

Probe: scripts/p8d_qa_probe.py
SHA256:ca639d9e798a9d9077973b89c0e72b48d3f6cc4ba2234ba9dfbfa96c9976a6d0
Actual current sanitized output: [PROVISIONAL_RESULTS.json](PROVISIONAL_RESULTS.json).
Initial derivation: [PLAN_AND_PROVISIONAL.md](PLAN_AND_PROVISIONAL.md).

Reproduce from C:/Projects/card-market-tracker-p8d with its frozen-installed .venv:

    .venv/Scripts/python.exe -B scripts/p8d_qa_probe.py --mode all
    .venv/Scripts/ruff.exe format --check scripts/p8d_qa_probe.py
    .venv/Scripts/ruff.exe check --no-cache scripts/p8d_qa_probe.py

Last observed result:22/22 groups PASS, process exit0; formatter says1 file already
formatted; Ruff says All checks passed. All fixture databases live only under a
unique temporary directory. No token value is read. Socket audit hooks reject all
socket.* events; connect/DNS helpers are also explicit tripwires. Offline and replay
children additionally deny imports of card_market_tracker.telegram_delivery before
any product import. Fake sends deliberately reuse accepted native P8b result/receipt
types but never instantiate production transport.

## Evidence covered by these executable cases

- Stdlib literal164-byte preimages, exactly one actual NUL, both frozen identities;
  independent complete route/consent/binding/source/evidence/entry/message oracle.
- Three genuinely independent complete public P5a/P5b/P8c bundles, five checkpoints,
  two price signals each; ancient journal replay; exact immutable revision1 admission
  after a genuinely different latest revision2 exists.
- Review, precise historical consent/strict bool and digest mismatch rollback;
  redacted exact delivery DTO; preparation replay and source-byte nonmutation.
- Genuine incompatible priority/config for same watch/revision: second prepare
  identity_conflict, byte-identical rollback, healthy get/verify and three-fold backup
  with independently reopened backup verification. Equivalent sources replay and
  recompute. Another genuine alias/route for the same signal yields same deliveryID
  and conflict without mutation.
- Missing and different genuine original Watchlist sources reject while local verify
  still succeeds. Complete malformed unrelated manifest rejects. Caller manifest is
  detached before callbacks. Full twelve-key pair stability includes operational
  first_prepared_at and rejects an intervening changed projection before writer use.
- Original-issued receipt: forged DTO/dataclass, shallow/deep copy, mutation, wrong
  Budget/operation/ledger, expired receipt and reuse all reject; writer-open tripwire
  proves invalid authority is refused before writable open. Missing source refuses.
  A receipt consumed by a failed writer cannot be reused.
- Eight native fake outcome/receipt cases cover timeout, arbitrary exception,
  permanent rejection, fake DTO, wrong recipient, bool receipt ID, bool retry_after
  and missing receipt: conservative uncertainty/terminal results never resend.
- Accepted fake receipt persists confirmed. Another SQLite connection sees committed
  in_flight/count1 before fake HTTP and can obtain the writer lock during dispatch.
  Equivalent route revalidation after an old claim leaves historical fold valid.
- Valid429 exact inclusive cooldown, future not_before excluded from event high-water,
  second retry, third claim permanent retry_exhausted, no fourth dispatch. Historical
  validation snapshots remain valid after later equivalent route validation.
- Exact-instance owner-handle forgery/copy/wrong-Budget/second-use fencing; injected
  finalization failure leaves blocked in_flight; recovery requires explicit quiescence,
  yields only uncertain/recovered, and fences late successful completion/no resend.
- Aggregate original helpers share one identical Budget:3+3 synthetic monotonic seconds
  exceed one5s ceiling before metadata/claim. Postclaim pre-dispatch allowance expiry
  uses unchanged reserved budget for uncertain/deadline_exceeded with zero dispatch.
  Postclaim UTC rollback overrides provider acceptance with uncertain/clock_skew.
- Old empty restore establishes global durable quarantine before unknown ID lookup;
  subsequent preparation remains quarantined. Restored confirmed replay also blocked.
- Two actual sender processes share a start barrier: one fake HTTP file, one durable
  claim/result, one confirmed receipt. Fresh interpreter confirmed replay requires no
  originals, denies Telegram import/token/socket, adds zero fake HTTP and preserves counts.
- Fresh-process CLI success/errors/NaN timeout/unknown option abbreviation/force refusal,
  canonical ASCII JSON+LF, closed versioned DTO/error exits, one completion record,
  route/message/config/SQL privacy and offline root/new/old help.
- Negative fixture SQL with exact restored trigger inventory: invalid Gregorian date,
  overlength message and rehashed inconsistent full entry reject storage_corrupt;
  prepare refuses corrupt retained stores without writes/repair.

## Preserved failed attempts and probe corrections

[PROVISIONAL_ATTEMPT_1.json](PROVISIONAL_ATTEMPT_1.json) retains20 PASS/2 FAIL from an
intermediate QA-only revision. The authority case expected a genuine wrong-ledger
receipt to remain usable; the frozen contract permits/needs consumption before a
failed writer. The corrected probe obtains fresh normal admission after that attack.
The concurrent fake HTTP oracle tried BEGIN IMMEDIATE with timeout0, which can
collide with the OTHER sender's short claim transaction despite this sender releasing
its own transaction. The oracle now allows a bounded1s lock acquisition; retaining
a transaction across HTTP would still block this independent writer. No product
change was requested for these incorrect QA expectations. Rerun after those probe
corrections produced22/22 PASS under the stronger socket audit tripwire.

An earlier intermediate owner-handle test attempted the obsolete constructor with
no content argument while DB author was changing its private handle from a registry
to a sealed dataclass; it raised TypeError in the QA helper. Probe was adapted to the
actual private signature. One earlier QA fixture omitted explicit closing of its
own sqlite3.Connection; Windows temp cleanup correctly exposed a sharing violation.
Probe connections now use contextlib.closing. Neither issue was a product finding.
No historical attempt is promoted to PASS or omitted from this explanation.

## Explicit residual scope

No confirmed product defect remains from executed cases. This independent probe is
not a replacement for the full author suite/coverage/four CI jobs, installed thirteen
harnesses or a distinct final REVIEWER. Raw HTTP/TLS/DNS body-drip parsing is the
unchanged P8b transport boundary; this probe attacks its normalized native outputs,
not a real socket or Telegram. Exhaustive ENOSPC/hot-journal/reparse/publication fault
matrix and kill-at-every-instruction windows are not independently claimed by this
probe. Full elapsed deadlines are cooperatively enforced; synthetic monotonic clock
injection checks allowance accounting, not hard preemption of kernel syscalls.
Windows directory fsync is unsupported; no physical Pi/power-loss durability claim.

AC-WT20:BLOCKED - LIVE_UNVERIFIED. Real Telegram remains NOT AUTHORIZED/NOT RUN.
Final exact candidate HEAD/tree rerun and attestation remain pending Lead handoff.
Any corrective product commit invalidates affected earlier candidate attestations.
