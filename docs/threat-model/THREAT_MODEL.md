# Initial threat model

## Scope and assets

P0 handles local configuration, CLI output, build dependencies, CI, and a non-root one-shot container. It has no external source integration, business database, Telegram token, HTTP listener, or continuous service. Future valuable assets include credentials, historical observations, product identity, and notification channels.

## Trust boundaries and threats

| Boundary | Threat and impact | P0 control | Later owner/control |
| --- | --- | --- | --- |
| Local config / secrets | A path, token, or secret enters Git, an error, or logs. | Sanitized `.env.example`; local-file exclusions; config errors omit values; JSON allowlist ignores messages and arbitrary extras; secret scan. | P8a: Telegram secret injection, rotation, and delivery redaction. |
| Dependency / CI | Malicious or vulnerable package, workflow permission, or unreviewed lock update. | Frozen lock; no runtime deps; read-only workflow content permission; dependency audit and secret scan gates. | Each dependency update: review provenance, findings, and exceptions. |
| External provider -> domain | Malformed/poisoned price or identifier yields false value/opportunity. | No ingestion in P0; documented validation boundary. | P0.5/P1a/P2/P6a/P9: source approval, validation, provenance, anomaly handling, rate limits. |
| Pi host / network / storage | Unauthorized access, exposed ports, lost data after outage, or home-network attack. | Container UID 10001 and no published ports. | P3a/P9.5: file permissions, backup/restore, access policy, recovery and native Pi tests. |
| Future DB | Corruption, concurrent writes, stale backup, or unauthorized reads. | No DB in P0. | P3a/P9.5: schema/migration strategy, integrity checks, backup and restore drills. |
| Resource use | Runaway requests, memory, CPU, or disk usage harms Pi/provider. | P0 command exits; local temporary probe; no collector. | P0.5/P6a/P9.5: bounded work, timeout, rate limits, budgets, monitoring. |

The local CLI is callable by anyone with host access; host authorization is outside this package. `diagnose` confirms only config and local work-directory access. It cannot certify external source or system health. Future exposed endpoints require authentication and authorization analysis before implementation.

## Review rule

Treat a relevant scanner finding as a failed gate until corrected or documented in a narrow, reviewable exception with owner and expiry/revisit trigger. Broad ignores are not an acceptable substitute. Revisit this threat model when a phase adds secrets, providers, persistence, delivery, or a long-running service.
