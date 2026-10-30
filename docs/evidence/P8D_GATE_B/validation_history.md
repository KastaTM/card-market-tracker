# P8d documentary validation history

Scope: Gate A/B documentation only, 2026-10-30. Author checks are not QA,
product acceptance, Gate B acceptance or live qualification.

| Attempt | Actual observation | Resolution / status |
| --- | --- | --- |
| Gate A initial archive verification | All three raw files matched Git blobs already; Git printed potential LF/CRLF warnings | Added only three -text archive attributes preventively; no contract byte rewrite |
| Specialist long document writes | ARQ/DB first oversized Windows command failed process launch (206/command limit) | Bounded authorized writes; no failed process ran or product/database file changed |
| DB initial SQL proposal | :memory:34statements/45objects,32invalid actions rejected | Preserved in storage doc as superseded; chronology gap found in Lead review |
| DB chronology revision | immutable claim validation snapshot and event-only watermark;35invalid actions rejected | Stronger proposed DDL; no schema.py or persisted ledger |
| Lead probe Ruff first run | format reformatted1file; check exit1 with two E501 long digest literal lines | Split constants; next format/check passed; no exclusions/rule suppression |
| Lead first integrated stdlib probe | exit1 on missing local link docs/QUALITY_GATES.md -> phases/P8D_DESIGN_FREEZE.md | Handoff still under construction; SQL/vector steps completed but no overall PASS; create report/history and rerun |
| Lead integrated precommit checks | Ruff format/check PASS; stdlib probe PASS on Python3.13.15/SQLite3.53.1:34statements/45objects/35rejections/74new local links; exact input hashes emitted | Working tree deliberately dirty with proposed docs; not exact final-commit evidence |
| Lead staged whitespace check | exit1: SEC report had one extra blank line at EOF (previous working-tree diff did not include this then-untracked file) | Removed only trailing blank line; staged check rerun required; no substantive security text change |
| Lead final postcommit check | Required rerun on committed documentation; prints exact HEAD/tree and clean flag | Saved separately in handoff as P8D_GATE_B_VALIDATION.json to avoid circular commit identity |

Source snapshots, API inherited38-category check and complete SQL probe are
recorded in their author documents/security report. A tool readback helper after
DB's successful35-action probe failed only its subsequent hash-print step due to
variable shadowing; standalone Get-FileHash provided the corrected document
hash. That diagnostic failure was not a SQL PASS reversal and is not hidden.

Reproduce from checkout root using Python3.13 -B on
docs/evidence/P8D_GATE_B/design_probe.py. It prints exact observed Git identity,
working-tree state, document SHA256, source allocations, format vectors and
SQL output. Final commit hashes are external observations rather than
self-referential contents in this same report. No full suite/CI/publication,
independent QA/REVIEWER or Telegram gate has been run.
