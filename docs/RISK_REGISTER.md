# Risk register

## P1a controls and remaining limits

R-03 identity/metadata poisoning is mitigated for the offline slice by strict validation, explicit contextual
bindings, unknown candidates and contradiction rejection; curator mistakes remain
possible and require manifest review. R-04 uses additive allowlisted logs and
sanitized errors. R-06 uses byte/depth/node/string/record bounds and no network.
R-09 has no network path in this implementation. R-10 remains open for real data:
fixtures are synthetic; modeled metadata and MIT documentation do not approve
third-party images, brands or pricing. R-07 remains QEMU-only pending native Pi.
These controls do not unblock market, retail or temporal Discovery phases.

Status reflects what P0 can address. P0 controls are described in the [threat model](threat-model/THREAT_MODEL.md); future controls are not represented as implemented.

| ID | Risk / effect | P0 response | Owner / next review |
| --- | --- | --- | --- |
| R-01 | Source terms, robots rules, access controls, or unstable APIs may prevent a legal reliable adapter. | Do not ingest or scrape in P0; require feasibility evidence. | P0.5 Source Feasibility |
| R-02 | Listings confused with sales or market value lead to false signals. | Preserve distinction in architecture and contracts. | P2 Market Data |
| R-03 | Extreme or poisoned prices create false opportunities. | Treat external input as untrusted; no P0 opportunity engine. | P2/P9 |
| R-04 | Secrets in config, logs, repository, or CI leak credentials. | Sanitized example, allowlisted logs, ignore local files, CI scans. | Every phase; Telegram key in P8a |
| R-05 | Home Pi power/network/storage interruption corrupts future history. | P0 contains no DB; record need for backup/recovery testing. | P3a/P9.5 |
| R-06 | Excessive CPU, memory, storage, or requests harm Pi or providers. | Small one-shot P0; later timeouts, bounds, and rate limits required. | P0.5/P6a/P9.5 |
| R-07 | Emulated ARM64 passes while physical Pi fails. | Label emulated evidence; require native validation later. | P9.5 |
| R-08 | CI or dependencies introduce supply-chain compromise. | Frozen lockfile, minimal permissions, vulnerability and secret scans. | Every dependency update |

## P0.5 source-feasibility update (2026-10-07)

The dated [source matrix](sources/SOURCE_MATRIX.md) and fiches provide evidence for this update. P0.5 implements no adapter or continuous collection. These risks remain open for the owning phase; a proposed boundary is not an implemented control.

| ID | Evidence and effect | Required decision or later control |
| --- | --- | --- |
| R-01 | Cardmarket is closed to new API applicants and its published terms do not grant CMT's recurring market collection. eBay production access and license compatibility are conditional; retailer monitoring rights are unresolved. | Obtain explicit source access and rights for collection, retention, analysis, and display before selecting a production feed. Record an alternative or gate the dependent phase. |
| R-02 | Active listing asks, completed sales, provider aggregates, and MSRP have different meanings. Scrydex's current prices are USD/JPY, not a EUR market reference. | Preserve `price_type`, currency, region, shipping, taxes, and provenance; do not derive a EUR reference until a licensed source and method are evidenced. |
| R-03 | Third-party names, variants, conditions, sealed contents, and prices can be wrong or malicious. | Quarantine unknown or inconsistent candidates; validate decimal bounds and source records; require review before canonical matching or opportunity logic. |
| R-04 | Future authenticated sources introduce app keys, tokens, and possibly buyer-location data. | Use approved secret storage, redact requests/logs/fixtures, limit credential scope, and review rotation in the implementing phase. No credential was acquired in P0.5. |
| R-06 | Search pages, pagination, rate limits, large bodies, redirects, and repeated polling can exhaust providers or a Pi. | Future adapters require request and size budgets, deadlines, controlled redirects, retry/backoff limits, and provider-specific rate policy. P0.5 probes are capped at five per source. |
| R-09 | Untrusted source URLs or redirects could reach private-network services or unexpected hosts. | Use approved hosts, DNS/IP and redirect checks, HTTPS, and bounded fetches before adding any URL-following adapter. |
| R-10 | Licensing and retention terms may forbid the durable multi-source history central to later phases. | Record per-source storage, deletion, derived analytics, and redistribution rights; unknown rights block production retention and display. |

Risks should be updated when evidence changes. A risk is not closed by adding an untested design statement.
