# P8a actual ownership and integration record

**Authority:** Orchestrator chat opens P8a on 2026-10-20. Phase OPEN; no merge or acceptance authorized. Actual branch `feat/p8a-offline-alert-outbox`, base `b89fff319a94e5eb6e4b7bdad944e879bad371f6`, base tree `8f62a1d85b375ee839dcd95e09a578cb643c85b6`.

The earlier ChatGPT handoff's connector403 did not prevent local work. Root verified a clean checkout, live remote baseline, GitHub CLI authentication, and preserved prior worktrees/branches before creating the authorized phase branch. The following agents were actually spawned through the collaboration tool with disjoint ownership.

| Role / actual agent | Exclusive ownership | Relationship |
| --- | --- | --- |
| Engineering Lead `/root` | Git, interfaces, shared docs, formatter, shell/CI wiring, integration, gates and PR | Author/integrator; sole Git writer |
| ARQ/DB-OWNER `/root/outbox_storage` | alerts schema/storage/errors, DB tests, storage contract, ADR0010 | Storage author |
| BE `/root/outbox_application` | alerts application/policy/render/CLI, root CLI registration, application/policy/CLI tests, eighth harness, API contract | Application author |
| QA `/root/independent_qa` | Independent SEC risk analysis and own oracle/probes under ignored .p8a-evidence/qa; no tracked source/test/doc edits | Nonauthor, distinct reviewer |
| REVIEWER `/root/independent_reviewer` | Read-only final SHA/tree, contracts/security/docs and four complete CI logs; attestation in final report/PR | Independent of QA and all authors |

Specialists requested gpt-6.1-sol/High; the spawn tool accepted those task selectors. This records requested/accepted arguments, not hidden backend introspection. Root remains the system-provided GPT-6-based Codex agent; no active root selector switch is claimed. User requested Medium routine coordination and High trust/identity/SQLite/security/final review; no root-selector mutation tool was available.

Frozen interfaces use integer renderer_version1, policy discovery_reference_alert_v1, one retained origin-verified comparison and one content-bound private receipt under a shared Budget. Storage reconstructs policy.prepare_event during evidence relationship checks. Root centralizes Git/shared edits; integration gates precede a frozen candidate. Provisional author/QA results are not final attestations. Candidate changes renew affected QA, review and gates. See the [phase report](P8A_OFFLINE_ALERT_OUTBOX.md).
