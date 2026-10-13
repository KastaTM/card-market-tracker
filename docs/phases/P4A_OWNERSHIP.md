# P4a ownership and execution ledger

Date: 2026-10-12 Europe/Madrid. Engineering evidence, not phase acceptance.

Authorized baseline and fetched remote main:
`734641a7ef920688677cdea6bc82f908a2856927`, tree
`ae61fe57e6f874b138c98ecdaaa8cbd830406354`; ordered parents
`c6e66a2aba469d02f0ca63fde3b81ecc5eea41bc` then
`e9c5f02e7f093dedff55b67f137c4446f22e8735`.
Initial checkout was clean P3a at its second parent with the same tree. Existing
branches, local main and detached `.p3a-evidence/qa` and `reviewer` are preserved.
Remote fetch/push is `https://github.com/KastaTM/card-market-tracker.git`.
P4a branch was absent remotely and created locally from the exact baseline.

The full contract and brief were read and archived byte for byte. Archive SHA256:
contract `89B5BEBF133F51B7DCD4F46EC67143D152B549F5CC7E7644980FD8B6431FDF42`;
brief `FFBDCD1A4B00C15DD0D54DF77E653648D6ABEE55FE220943DBA738C4C654F15F`.
Repository governance, contracts, phase reports/PR ledgers and relevant runtime,
tests, CI and harnesses were inspected before implementation.

| Owner | Exclusive responsibility |
| --- | --- |
| Engineering Lead | Git/refs, CLI/logging and their tests, scripts/CI/Compose, shared docs, archives, navigation, integration and completion report |
| ARQ + DB-OWNER (`arq_checkpoint`) | Initially read-only empty-context checkpoint; after explicit handoff, ADR-0005, DISCOVERY_V1/STORAGE_V1 read extension, additive SQLite snapshot reader and its tests |
| DATA/DISCOVERY + BE (`discovery_author`) | Generic discovery DTOs, strict input, pure comparator, disjoint author tests and synthetic Discovery fixtures |
| SEC + SRE (`security_operations`) | Read-only boundary/runtime inspection and coordinated threat/risk/debt/runbook ownership |
| QA (`qa_final`) | Read-only detached final-SHA worktree and independent outside-source risk tests; no production authorship |
| REVIEWER (`reviewer_final`) | Different detached final-SHA worktree, independent probes/code/contracts/Git/CI review; no production authorship |

Only Lead commits or changes shared Git/workflow/dependency state. Freeze shared
DTO/error contract before dependent edits. No edits across ownership without
explicit handoff. No merge, real feeds, new schema or phase acceptance authorized.

Root identifies as GPT-6 based Codex; exact variant/reasoning and effective backend
are not introspectable. Root model change is not asserted. Tool offers
`gpt-6.1-sol/high`; explicit request for ARQ/DB-OWNER was accepted (fresh context).
Requested/accepted settings do not independently verify actual serving backend.
QA and REVIEWER selections/executions will be recorded when actually performed.

The tool also accepted fresh-context `gpt-6.1-sol/high` selections for `qa_final`
and `reviewer_final`. Each has separate detached source worktree `.p4a-evidence/qa`
and `.p4a-evidence/reviewer` respectively when handed off after the candidate
commit; source is read-only. Their isolated output/probe directories are separate.
Final SHA/results/independent CI-body verification belong in the external PR ledger.

`discovery_author` (DATA/DISCOVERY + BE) and `security_operations` (SEC + SRE)
were separately requested with `gpt-6.1-sol/high` and accepted. DATA owns only
discovery modules/core-input tests/Discovery fixtures; SEC/SRE owns only its
runbook and additive threat/risk/debt sections. ARQ/DB-OWNER received explicit
author handoff for its stated files after the read-only checkpoint. All three
agents are supplementary specialists/authors, distinct from later QA/REVIEWER.

Sandbox process startup fails before shell execution with
`helper_unknown_error: setup refresh had errors`; automatically reviewed elevated
execution works. uv0.12.10, gh2.100.0, Docker client29.7.2 observed. Default system
Python is3.12.10; project Python3.13 and SQLite will be measured through frozen uv.
Docker Desktop Linux daemon is initially stopped; container gates are unexecuted.

## Initial ARQ/DB-OWNER checkpoint

STORAGE_V1 stores no empty capture namespace/kind/language. Its context hash covers
resolver/manifest identity, not capture scope. ES set, EN set and empty under the
same manifest have the same context hash; this is information loss, not hash
collision. Request context can serve an explicit local caller/producer attestation
for selected empty captures, as contemplated by the brief, with output labeled
`request_attested_empty`. Nonempty batches require every stored record to match
the exact context and are labeled `records_verified`. Neither label authenticates
the producer. DB evidence proves empty existence/counts/capture only. This compatible
choice needs no schema/request expansion; durable independently verified empty
scope would require Orchestrator authorization of a later persistence contract.
