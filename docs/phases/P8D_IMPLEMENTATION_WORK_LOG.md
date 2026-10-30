# P8d implementation construction history

Scope: provisional offline work after explicit design acceptance,2026-10-30.
This is not a final gate ledger. Frozen design and original whitespace FAILs
remain preserved at50fcb55a and PR19.

| Observation | Outcome / correction |
| --- | --- |
| BE original implementation |68 author cases PASS; strict API decorator changed from Any to ParamSpec to retain public typing; no suppression |
| DB author implementation |38 author cases PASS; initial test incorrectly byte-compared SQLite backup pages, corrected to logical/source equality; BOM/import/type construction issues corrected; not product acceptance |
| Root CLI privacy |First92-case run found missing consent_mismatch completion category; scoped new-producer allowlist fixed;92PASS |
| REVIEWER durable error reproduction |CLI incorrectly returned exit0 for durable retryable/permanent/uncertain error envelopes; mapped frozen exits and error logs, actual fake-send regression passes |
| REVIEWER catalog guards |Names/type/table128-byte frozen cap corrected from32768; SQL32768 retained; exact DDL unchanged |
| QA own expectations |Preserved20PASS/2FAIL probe revision: fresh authority required after wrong-ledger consumption, competing-sender writer-lock oracle needed bounded1s rather than0; corrected22PASS, no product weakening |
| REVIEWER manifest safety |Preserved17PASS/1FAIL; checked descriptor reader added with original parser limits and shared origin Budget; independent18PASS |
| Root manifest regressions |Legacy test hook adapted to new checked reader; real unlink-on-open is unavailable on Windows, so explicit post-open inode substitution injected; 1MiB case retains its bound with bounded pytest IDs instead of enormous auto-generated diagnostics; targeted118PASS |
| Complete provisional gates |Full suite2451PASS/1existing skip;93.19%lines/86.17%branches, frozen installs, format/lint/mypy PASS; later corrections require final rerun |
| Mypy diagnostic |One later1.20.2 INTERNAL ERROR was observed; immediate show-traceback rerun passed100sourcefiles without code/config/dependency change. Cause not asserted; final clean-candidate default check required |
| Initial installed and AMD64 harness |Full thirteenth smoke PASS using fake provider and no product sockets; final source changes require new wheel/container evidence |
| Qualification author interruption |BE emitted draft wrapper then returned model usage-limit error before tests; Lead took ownership and completed deadline/accounting/privacy tests. No effective backend claim or author-test independence |
| Wrapper author tests |Fixture originally supplied SQLite as JSON manifest, then expected FileExistsError instead of accepted physical unsafe_destination refusal; corrected fixture/expectation, nine cases PASS; reserve-expiry negative added with concrete storage_timeout/no fake HTTP |
| Whitespace |Seven received Brief hard breaks remain FAIL; copied original checksum CRLF remains separately classified FAIL in documentary PR19; neither is suppressed or rewritten |

All fixture values are synthetic and all provider behavior fake. No new test skip,
coverage reduction, weakened threshold, raised contractual timeout or same-SHA CI
rerun is authorized by this log. Full logs of final checks are distinct evidence.
The exact final source identity and renewed nonauthor review remain required.

The precommit tracked-file secret scan retained a FAIL with28 public hash candidates
across8 paths. Git/content/oracle provenance was verified and only the established
exact detector/path/value registry was extended;36 scanner boundary regressions
passed after correcting an initially missing test-only sha1 import. Unknown values,
paths/types still fail; no detector/path exclusion or threshold reduction.
A later default-sandbox lint invocation could not write this external worktree's
cache (Ruff access denied; mypy internal error). Authorized escalated checks use
the same unmodified configuration; final checks must record their own results.
Qualification tests now include reservation-expiry/no provider dispatch and
separate-process confirmed replay,10 cases total on fake transport only.
