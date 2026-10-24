# Card Market Tracker — P5b offline engineering handoff

Archive note: this README describes the supplied 2026-10-23 design bundle.
The integrated implementation and current evidence are tracked in
`docs/phases/P5B_WATCHLIST_EVALUATION_JOURNAL.md`; old execution blockers below
are historical and are not substituted for current verification.

**Date:** 2026-10-23. **State:** PREIMPLEMENTATION; repository publication BLOCKED by
403 (branch creation). No PR, merge, source implementation, integrated suite,
independent QA or reviewer, or Orchestrator acceptance is claimed.

## Contents

- `CODEX_START_PROMPT.md`: resume implementation through a real authorized Codex
  engineering session. Start there when providing this bundle to Codex.
- `docs/phases/P5B_WATCHLIST_EVALUATION_JOURNAL_CONTRACT.md`: the supplied opening
  contract preserved verbatim.
- `docs/phases/P5B_CODEX_ENGINEERING_BRIEF.md`: scoped decisions, system anatomy,
  operational constraints, acceptance matrix and actual blockers.
- `docs/phases/P5B_OWNERSHIP.md`, `P5B_STATUS.md`: ownership/review rules and
  verified vs missing evidence.
- `docs/adr/0013-watchlist-synthetic-journal.md`: proposed significant
  architecture decision and revisit triggers.
- `docs/data-contracts/`: proposed WATCHLIST_JOURNAL_V1,
  WATCHLIST_JOURNAL_STORAGE_V1 and WATCHLIST_SIGNAL_V1.
- `docs/runbooks/WATCHLIST_JOURNAL_RECOVERY.md`: prospective recovery procedure.
- `ROADMAP_INSERT_P5B.md`: an insertion snippet for top of `docs/ROADMAP.md`,
  **not an overwrite** of prior roadmap history.
- `scripts/p5b_identity_oracle.py`, `scripts/p5b_transition_oracle.py` and
  `tests/`: standalone stdlib oracles/fixture and 8 reference tests. They are
  design assertions only, not proof that P5b production software exists.

## Integrating safely into checked-out repo

1. Confirm GitHub `main` still equals the authorized baseline; inspect local
   worktree/branches before any modifications. Do **not** force reset/rebase.
2. Create the phase branch with approved permissions; if blocked, preserve
   worktree and report the blocker. Do not modify tokens or bypass a 403.
3. Copy `docs/`, `scripts/`, `tests/` overlay into existing repo, **review for
   collisions** rather than replacing source files; the new files are named
   distinctly. Insert `ROADMAP_INSERT_P5B.md` after `# Roadmap` in the original
   file, preserving all history. Do not copy README_HANDOFF as a root README.
4. Run `python -m unittest discover -s tests -p 'test_p5b_*_reference.py' -v`
   and `python scripts/p5b_identity_oracle.py`; treat PASS solely as design-gate
   evidence. Review and freeze preimages and SQL before implementing.
5. Follow `CODEX_START_PROMPT.md` and the Engineering Brief to implement the
   **entire** phase and publish only a non-merged PR after actual gates.

## Limitations

The bundle is a portable specification/handoff, not an installed package nor a
running journal. The contributor using it must verify the existing repository
and integrate the final documentation, code and tests, securing QA/reviewer
independence and Orchestrator acceptance before closure.
