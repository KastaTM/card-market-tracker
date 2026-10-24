# P5b ownership and independent review protocol (proposed)

**Status:** Implementation assignments made 2026-10-24. Original proposed duties
below remain the ownership protocol; current execution is recorded here and in
the [engineering report](P5B_WATCHLIST_EVALUATION_JOURNAL.md).

Actual disjoint ownership: `/root` Engineering Lead owns journal CLI/root wiring,
logging extension, harness/CI and DOCS; `/root/arq_be` owns errors/models/identity/
transitions/application and domain/application author tests; `/root/db_owner`
owns schema/storage and storage author tests. `/root/sec_sre` performed read-only
SEC/SRE review and performs independent QA; `/root/reviewer` is a different
non-author final REVIEWER. QA owns only p5b_qa_probe.py; REVIEWER owns only
p5b_reviewer_probe.py and their review notes. Neither writes product code.
All shared Git/commit/publication state belongs to the root lead. Final probes
must check the frozen commit/tree, with outputs in the external PR evidence ledger.

The specialist spawn tool accepted explicit `gpt-6.1-sol` and `high` arguments.
This observes the requested tool selection, not hidden backend internals. The
root environment identifies a Codex agent based on GPT-6; its exact model variant,
selector and effective reasoning are not exposed. Historical model statements
below apply to the earlier design session, not to these new specialist calls.

| Role | Write ownership / duties |
| --- | --- |
| Engineering Lead | Git preflight and branch, integration, root CLI wiring, harness/CI, documentation, final evidence and PR; authorize shared-file edits only after owners' handoff |
| ARQ + BE (author) | P5b admission/application and pure sequence/transition functions; no P5a edits |
| DB-OWNER (separate author) | P5b schema, atomic SQLite storage, deep verification and recovery code; coordinate frozen DTO/IDs before edits |
| SEC/SRE (read-only first) | Path/IO/time-limit/deadline, threat boundary, concurrency/failure-mode review |
| QA (non-author) | Independent acceptance probes, fold and SHA oracle on final head/tree; test fixture ownership separated from BE/DB code |
| REVIEWER (non-author, not QA) | Final read-only architecture/security/data-integrity review and own independently reproducible probes on the **same final head/tree** |
| DOCS | Contract/ADR/runbook/roadmap/quality-evidence synchronization; no incompatible changes to accepted contracts |

Parallelism only for separate files or read-only analyses. Never concurrent
schema/CLI/shared file edits. If review finds defects, authors fix then both
independent reviewers repeat final-candidate probes. Do not mark tests PASS on
source review or a historical run alone.

## MODEL PROFILE requested vs observed

- ChatGPT Phase Lead requested GPT-6.1 Sol/High in Work (or Astra/High normal).
  This conversation reports GPT-6; effective reasoning selection is not
  exposed. Requested variant therefore **not verified as selected**.
- Codex Engineering Lead requested GPT-6.1 Sol/Medium; ARQ/DB/SEC/SRE/QA and
  reviewer GPT-6.1 Sol/High. No Codex tool/session available here, so **no
  Codex model or reasoning selection observed**. Reconfirm actual selector in
  the Codex environment rather than claiming a backend identity.
- Escalate architectural disagreements, replay/ordering, CAS, or integrity
  failures to strongest actually available High reasoning. Use Medium for
  routine implementation and documentation.

## Evidence needed

Capture remote SHA/tree, clean worktree, origin/main baseline, branch, commit,
full test commands and untruncated logs, four CI job URLs/status, coverage
line/branch counts, SHA-bound QA and REVIEWER oracles, AC-S01..18 evidence,
zero-socket probes, threat-runbook updates and a complete Phase Completion Report.
Only then may this Phase Chat declare READY_FOR_ORCHESTRATOR_REVIEW; only the
Orchestrator may accept/integrate/close.
