# P3a ownership and execution ledger

Date: 2026-10-10 Europe/Madrid. Engineering evidence, not phase acceptance.

Baseline verified by local fetch: `c6e66a2aba469d02f0ca63fde3b81ecc5eea41bc`,
tree `a9717922736a6220d3ff05293bec4cb222644269`. Original clean checkout was
`feat/p1a-catalog-core` at `93a17711cb75f91816e41279fe76069055391e50`.
No existing files or branches were reset. Authorized P3a branch created from
the verified baseline. Contract archive SHA256 before Git normalization:
`61579B956F0DCC241F474B98018B13ACDD9CDAFA801E9BF93F66568097394FCD`.

| Owner | Exclusive edit ownership |
| --- | --- |
| Engineering Lead | Git, CLI, logging and their P3a tests, scripts, Docker/Compose/CI, ignores, README, architecture/testing/gates/navigation, roadmap, P1a later attribution, P3a report and this ledger |
| ARQ + DB-OWNER + storage author | ADR-0004, PERSISTENCE_V1 and STORAGE_V1 contracts; persistence/sqlite repository and schema modules; storage author tests |
| BE/DATA boundary author | persistence/input and application modules, persistence package init/errors/models; boundary author tests and synthetic_persistence fixtures/provenance |
| SEC + SRE | Read-only design/runtime reviews; storage runbook, threat model, risk register and technical debt only |
| QA (later separate agent) | Read-only exact committed SHA in isolated checkout; independent risk assertions and executions outside source |
| REVIEWER (later separate agent) | Read-only exact committed SHA in a separate isolated checkout; independent review and CI verification |

Shared interfaces must be agreed and documented before dependent implementation.
Only Lead commits, changes refs, modifies dependencies or integrates shared files.
Authors do not edit another owner's paths without an explicit handoff.

Model selections available in the delegation tool include `gpt-6.1-sol` and
`high`; specialist requests and their accepted results will be recorded here.
Root identifies as a GPT-6 based Codex agent; exact root backend/reasoning is
not independently exposed. No root model change is asserted. Requested specialist
configuration is observable; effective backend execution is not introspectable.

Local Python 3.13.15 / SQLite 3.53.1 / uv 0.12.10. Sandbox process startup fails
with `helper_unknown_error: setup refresh had errors`; automatically reviewed
elevated execution works. Docker client 29.7.2 is available but the Desktop Linux
daemon was not running at baseline. Historical P1a PR5/main push CI37965128340
is verified, with four successful jobs; it is not P3a gate evidence.

No merge, real-source retention, P2 opening or phase acceptance is authorized.

## Executed selections and review isolation

The tool accepted explicit `gpt-6.1-sol/high` requests for storage_author
(ARQ/DB-OWNER/storage), boundary_author (BE/DATA), security_operations (SEC/SRE),
qa_final and reviewer_final. Effective backend/root reasoning are not exposed;
no client-setting change is inferred. Supplementary roles are not final reviewers.
Earlier qa/reviewer attempts ended at a client usage limit; no review is credited.

Final QA/REVIEWER are distinct from authors/each other, with clean detached
read-only source worktrees `.p3a-evidence/qa` and `.p3a-evidence/reviewer`.
QA independent wheel/harness lives outside source in `.p3a-evidence/qa-outside`;
REVIEWER uses separate temporary probes. Lead alone changes their refs after
checking tracked cleanliness. No source mutation by either final reviewer.

Implementation SHA `4d8702ccfb4d3a93b6a1ae69ea5e164fe8602658`, tree
`ec8d37434409c57823fffe07ed3b815f6e4e6d8e`: QA411 passed/one Windows symlink
privilege skip, 97.54% lines/94.14% branches, frozen quality/wheel/audit/scan plus
fourteen independent risk groups; REVIEWER117 risk tests/same skip plus separate
forgery/candidate-history/read-only/copy/sidecar/deadline probes. No blockers.
Junction/hardlink tests pass on Windows; Linux CI supplies symlink coverage.

Run38088571440 four jobs/log bodies PASS; temporary PR merge96fcef3 has the same
implementation tree. Final documentary successor SHA/reviews/CI bodies belong to
PR6's external ledger. No circular self-SHA commit. Runtime/packaging/workflow
unchanged from parentf43ce4b; only one synthetic nested test key changed in4d8702c,
without scanner suppression. Docker client/daemon29.7.2, container Python3.13.16/
SQLite3.46.1 UID10001 /data0700 observed; CI QEMU10.2.3. No dependency/lock changes.
