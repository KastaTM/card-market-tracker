# Technical debt register

Entries describe a known compromise, not a planned feature. New significant debt needs ID, reason, impact, module/owner, exit condition, and review horizon.

| ID | Reason and impact | Module / owner | Exit condition | Review horizon |
| --- | --- | --- | --- | --- |
| TD-001 | P0 uses only a local work-directory probe; it cannot establish source or long-running service health. Operators must not infer those states from `diagnose`. | CLI / future SRE owner | Service and source-specific health states defined and tested when components exist | P6a and P9.5 |
| TD-002 | ARM64 CI smoke uses emulation, leaving native Pi performance and interruption behavior unverified. | Container / SRE | Native Pi soak and recovery evidence | P9.5 |
| TD-003 | P3a (2026-10-10) deliberately relies on an operator-controlled local directory. Exclusive file reservation and link checks cannot confine SQLite's pathname reopen against a hostile administrator replacing an ancestor concurrently. Windows ACLs also remain an operator responsibility. Exposure to an untrusted shared directory could redirect writes or cleanup. | Persistence paths / SEC + SRE | Define and implement stronger directory/descriptor confinement with adversarial race evidence, or retain an enforceable trusted-directory deployment policy before any shared or multi-user deployment | Before shared-directory support; P9.5 operational review |
| TD-004 | P3a (2026-10-10) bounds individual SQL operations and inputs but its append-only history has no disk quota or automatic retention. Sustained growth can exhaust local storage and prevent batches/backups. Destructive cleanup would require a separate approved policy, so operators must track capacity and keep space for recovery. | Persistence capacity / SRE + DB-OWNER | Establish measured growth/capacity budgets, monitoring and backup-space thresholds; introduce retention only under an authorized contract and source-specific rights | Before continuous collection; P9.5 |

No commercial schema, scheduler, or canonical identifier is recorded as debt merely because P0 intentionally excludes them. Those are future decisions requiring their own phase contracts.
