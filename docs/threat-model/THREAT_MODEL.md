# Initial threat model

## P1a implemented local catalog controls

Untrusted UTF-8 regular files are read with a 1 MiB limit. Strict parsing rejects
duplicate keys, malformed encodings, nonfinite numbers and excessive nesting;
structure, strings, batch size and manifest counts are bounded. No content is
executed and no URL is followed. JSON shape validation precedes normalization.
Only allowlisted metadata reaches generic observations, and output omits names,
images, price data and arbitrary provider extras. Minimal candidate references
are intentional stdout data; callers should treat stdout as untrusted metadata.

Canonical UUIDv4 IDs and typed relationships are validated in an explicit
read-only manifest. Contextual bindings must agree with entity kind, language,
variant and relationships; contradictions fail instead of merging. Unknowns
remain candidates and cannot promote themselves. No name-based matching exists.
This preserves deterministic replay without database mutation. A host user can
edit the manifest; its authorization is a local curator trust boundary, not a
cryptographic signature or multi-user approval workflow.

Logs allow only fixed categories, operation UUID/duration and bounded counts;
errors never serialize exception text, paths, raw input or arbitrary names.
There is no output-file option, credential, listener, production collector or
database. Compose and container catalog smoke have networking disabled and
read-only fixture mounts. Fixture retention is synthetic only; field-specific
real-data rights remain governed by the [policy](../sources/TCGDEX_P1A_FIELDS.md).
Dependency/secret scanning and independent exact-SHA QA/security review remain
mandatory gates. Physical Pi resource and interruption behavior stays unverified.

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

## P0.5 external-source assessment (2026-10-07)

P0.5 performed only bounded research and five unauthenticated TCGdex GETs; no production source adapter, credential, database, periodic job, or external-data display was added. The [source matrix](../sources/SOURCE_MATRIX.md) and [preliminary ingestion requirements](../data-contracts/SOURCE_INGESTION_V0.md) record future boundaries. A documented requirement below is **not** an implemented protection.

| Future boundary | Threat | Required later control and evidence |
| --- | --- | --- |
| Provider URL and redirect to network | Source-controlled links or unexpected redirects reach local/private services, leak headers, or leave approved hosts. | Approved HTTPS host list, controlled redirect chain, DNS/IP checks, no credential forwarding, timeout and response-size limits; test hostile URLs in the implementing phase. |
| Provider payload to normalized ingestion | Malformed JSON/HTML, huge responses, ambiguous currencies, poisoned prices, variant mismatch, and partial fields corrupt domain observations. | Bounded parsing, versioned validation, quarantine of unknown candidates, explicit nulls and price semantics, decimal bounds, provenance and incompatible-change tests. |
| API access and secrets | Tokens leak in URLs, logs, fixtures, CI, or a redirected request; access terms are exceeded. | Approved secret injection, least scope, redaction, rotation plan, per-source request budgets and rate-limit handling. P0.5 acquired no tokens. |
| License and durable history | Technically reachable listings are stored, combined, analyzed, or displayed beyond the provider's grant. | Per-source permission record covering access, storage duration, deletion, derived analytics and display before production retention. Unknown rights block persistence. |
| Discovery to identity and alerts | An unfamiliar SKU is forced onto a known product, or a stale/false stock state triggers a market alert. | Preserve unknown candidates and seller/offer distinctions; require identity review and time-scoped stock evidence. Market Alerts belong to later product phases; System Alerts for source failures belong to later operations. P0.5 records probe outcomes only. |

The three retailers' published or unreadable conditions did not establish permission for automated monitoring, so no direct retail probe was made. Cardmarket and eBay API endpoints were not probed without authorized production access. These abstentions are part of the evidence, not a claim of operational source health.
