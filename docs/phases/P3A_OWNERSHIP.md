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
