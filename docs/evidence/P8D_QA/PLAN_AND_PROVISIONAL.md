# Independent P8d QA falsification plan and provisional execution

Date: 2026-10-30. Role: /root/p8d_qa_independent, NONAUTHOR.
Authority: P8D_DESIGN_ACCEPTANCE.md, accepted design50fcb55a / treed8d3eac.
Requested tool model gpt-6.1-sol/high; effective backend not independently observable.
Exclusive writes: scripts/p8d_qa_probe.py and this evidence directory only.
No product/author-test edits, Git/index/ref mutations, actual credentials or live Telegram.
No candidate acceptance, Gate E attestation or phase closure is asserted.

## Independent derivation

The probe imports no author tests or prior probe helpers. Genuine fixtures are
created solely through public P5a/P5b/P8c APIs from the complete synthetic manifest:
product b980e1f7-9bae-432e-b02a-182dbcca478d, price1300 threshold, five prices
1725/875/875/1725/875, one price rule, June17 historical explicit timestamps.
Those five checkpoints give two genuine distinct episodes; ancient replay is
checked after the final episode. Three independent original bundles include
identical normalized entries and priority-only incompatible entries for the same
watch/revision. Every bundle independently verifies and origin-recomputes.

The stdlib oracle uses literal ASCII preimages with exactly one actual NUL,
length164, and both frozen SHA256 constants without importing product helpers.
A second stdlib oracle reconstructs all route, entry, message, evidence, intent,
semantic source-alert, consent, binding and delivery commitments directly from
public P8c rows. It deliberately omits only first_prepared_at from source identity.
It is an equality/format oracle; original authenticity comes from normal public
admission, never the oracle itself.

## Executable present cases

- Literal independent identity/preimage/NUL vectors.
- Genuine public source pipeline, two episodes and ancient replay.
- Entire review DTO equals independently derived commitments.
- Every consent selection/hash mismatch rejects before writes; strict bool revision.
- Prepare insert and exact replay preserve immutable delivery DTO and source bytes.
- Semantically equivalent independent original bundle permits replay/recompute.
- RW01 genuine incompatible same watch/revision entry reaches review, then second
  prepare must reject identity_conflict with byte-identical rollback; get, full
  verify counts, backup and independent backup reopen must remain healthy.
- Missing original rejects recompute while local verify succeeds; malformed unrelated
  manifest entity rejects complete-manifest review without ledger mutation.
- Closed redacted delivery DTO, route IDs absent, two-page keyset, cursor filter
  binding, strict bool/range limits, finite timeout and local maximum.

All offline cases install import/token/socket/DNS tripwires before product import.
All databases are unique temporary fixtures; no retained operational store is opened.

## Required extensions after product integration

Use only application._transport_factory fake-port injection, retaining actual accepted
P8b result/receipt types. Remote fake tests still deny token and socket access.
Inspect and attack private original-issued authorities: forged DTO, copied instance,
mutated bytes, wrong operation, new Budget, expired genuine receipt and second use.
Run actual two sender processes with shared start barrier and a fake HTTP callback
which reads a committed in_flight claim through another SQLite connection, verifies
that no SQLite write lock spans HTTP, and records at most one fake dispatch.
Fence stale/wrong owner handles and late finalize after explicit worker-quiesced
recovery; crash/kill windows must never enable resend. Map each fake native outcome,
including malformed native combinations, exceptions and receipt mismatch, to the
frozen conservative state/category. Only valid429 allows retry; exact cooldown,
third429 cap, future not_before excluded from high-water, postclaim clock rollback,
route revalidation after historical claims, shared origins/global deadlines.
Restore an old/empty snapshot: unknown delivery send must fail global quarantine
before lookup; prepare after restore may succeed but send must remain blocked.
Confirmed replay must run in a fresh process with unavailable originals, Telegram
imports denied, token reads denied and sockets denied; quarantined replay blocked.
Exercise SQL bounds/inventory/calendar corruption and path/sidecar/foreign evidence
refusals without destroying evidence. Additional CLI privacy and one-log checks
will use public CLI and safe fake-port setup, never actual transport.

## Provisional execution observed

Command from C:/Projects/card-market-tracker-p8d:

    .venv/Scripts/python.exe -B scripts/p8d_qa_probe.py --mode all

Result: literal_identity_preimages_stdlib_oracle PASS;
public_original_pipeline_ancient_replay_two_episodes PASS;
p8d_public_api_cases BLOCKED because P8d application was not yet present.
This is provisional concurrent-worktree evidence, not an exact-final-commit gate.
No P8d API, receipt, fake HTTP, concurrency, recovery or backup PASS is claimed yet.

    .venv/Scripts/ruff.exe format scripts/p8d_qa_probe.py
    .venv/Scripts/ruff.exe check --no-cache scripts/p8d_qa_probe.py

Result: formatter completed; All checks passed. Earlier non-elevated Ruff check
could not create its external-worktree cache, so validation uses --no-cache.
Writes/formatter used explicit authorized worktree escalation. No broad permission
or edit scope expansion was requested. AC-WT20 remains BLOCKED - LIVE_UNVERIFIED.

Final execution will record supplied candidate HEAD/tree and script digest,
repro commands, per-case PASS/FAIL/BLOCKED and material residual limitations.
A corrective product commit invalidates affected earlier attestations.
