# Technical debt register

P4c (2026-10-19) adds a separate bounded append-only journal, local integrity and
explicit source recompute. It does not authenticate independent producers or an
administrator controlling both files, establish native Pi durability, confine
hostile ancestor replacement, add global quotas/retention, or recover legacy
empty scope. TD-001 through TD-005 remain OPEN with existing owners/exits. The
16MiB result and finite verification budgets are explicit contract limits; event
delivery and other excluded features are not artificial implementation debt.

P1c (2026-10-18) separates exact-package replay from a reviewed pair's semantic
comparability. It authenticates neither independent producers nor provider time,
and does not recover legacy scope, add retention quotas or qualify power loss.
TD-001?TD-005 remain open with their existing owners/exit conditions. Exactly two
packages and unchanged real projections are intentional scope; no excluded
commercial feature is recorded as artificial implementation debt.

P4b (2026-10-16) consumes supported persisted scope through separate read-only v2
Discovery. It does not authenticate independent producers or recover legacy empty
scope, so TD-001–TD-005 remain open. The one approved real capture cannot prove
a provider transition; synthetic positive demonstrations are intentional scope,
not a future commercial feature recorded as new debt.

P1b (2026-10-14) adds reviewed local pinned capture context in schema2 under the
Orchestrator contract. This addresses new supported captures, not TD-005 legacy
empties or independent/multiple producers, and does not authenticate source
completeness. TD-001–TD-005 remain open. Fixed two-artifact scope is intentional,
not an unimplemented full-catalog feature added as debt. Earlier entries preserve
historical phase boundaries. No quotas, retention or native Pi qualification is claimed.

Entries describe a known compromise, not a planned feature. New significant debt needs ID, reason, impact, module/owner, exit condition, and review horizon.

P0.5b (2026-10-14) preserves all five entries below. Its documentary
[capture proposal](sources/P0_5B_FIELD_USE_CAPTURE_POLICY.md) addresses TD-005's
future independent/multi-producer scope questions without changing schema1,
authenticating producer claims or closing the debt. No new deliberate runtime
compromise was introduced, so no artificial debt item is added.

| ID | Reason and impact | Module / owner | Exit condition | Review horizon |
| --- | --- | --- | --- | --- |
| TD-001 | P0 uses only a local work-directory probe; it cannot establish source or long-running service health. Operators must not infer those states from `diagnose`. | CLI / future SRE owner | Service and source-specific health states defined and tested when components exist | P6a and P9.5 |
| TD-002 | ARM64 CI smoke uses emulation, leaving native Pi performance and interruption behavior unverified. | Container / SRE | Native Pi soak and recovery evidence | P9.5 |
| TD-003 | P3a (2026-10-10) deliberately relies on an operator-controlled local directory. Exclusive file reservation and link checks cannot confine SQLite's pathname reopen against a hostile administrator replacing an ancestor concurrently. Windows ACLs also remain an operator responsibility. Exposure to an untrusted shared directory could redirect writes or cleanup. | Persistence paths / SEC + SRE | Define and implement stronger directory/descriptor confinement with adversarial race evidence, or retain an enforceable trusted-directory deployment policy before any shared or multi-user deployment | Before shared-directory support; P9.5 operational review |
| TD-004 | P3a (2026-10-10) bounds individual SQL operations and inputs but its append-only history has no disk quota or automatic retention. Sustained growth can exhaust local storage and prevent batches/backups. Destructive cleanup would require a separate approved policy, so operators must track capacity and keep space for recovery. | Persistence capacity / SRE + DB-OWNER | Establish measured growth/capacity budgets, monitoring and backup-space thresholds; introduce retention only under an authorized contract and source-specific rights | Before continuous collection; P9.5 |
| TD-005 | P4a (2026-10-12) intentionally consumes schema1 without migration. Empty batches store existence/counts/capture but no namespace/kind/language scope; resolver/manifest context hashes cannot reconstruct it. The four-field request supplies explicit caller/producer scope attestation (`request_attested_empty`), so an incorrect assertion can produce false window-relative novelty despite a valid DB. Nonempty `records_verified` is a different evidence level. | Empty snapshot scope / SEC + DB-OWNER | Under an Orchestrator-authorized later contract, persist and validate independent capture-scope evidence with compatibility and adversarial tests, or retain an enforceable producer-attestation policy restricted to reviewed local synthetic use. No fix/schema change is claimed in P4a. | Before independent or multi-producer empty-scope consumption; revisit when P6a ingestion or P9.5 operational readiness opens |

No commercial schema, scheduler, or canonical identifier is recorded as debt merely because P0 intentionally excludes them. Those are future decisions requiring their own phase contracts.
