# Risk register

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

Risks should be updated when evidence changes. A risk is not closed by adding an untested design statement.
