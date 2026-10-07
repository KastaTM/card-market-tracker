# Technical debt register

Entries describe a known compromise, not a planned feature. New significant debt needs ID, reason, impact, module/owner, exit condition, and review horizon.

| ID | Reason and impact | Module / owner | Exit condition | Review horizon |
| --- | --- | --- | --- | --- |
| TD-001 | P0 uses only a local work-directory probe; it cannot establish source or long-running service health. Operators must not infer those states from `diagnose`. | CLI / future SRE owner | Service and source-specific health states defined and tested when components exist | P6a and P9.5 |
| TD-002 | ARM64 CI smoke uses emulation, leaving native Pi performance and interruption behavior unverified. | Container / SRE | Native Pi soak and recovery evidence | P9.5 |

No commercial schema, scheduler, or canonical identifier is recorded as debt merely because P0 intentionally excludes them. Those are future decisions requiring their own phase contracts.
