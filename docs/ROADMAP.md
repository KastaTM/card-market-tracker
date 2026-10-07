# Roadmap

This order is set by the Orchestrator and preserves the original phase IDs. A subphase limits scope; it does not renumber a phase.

The P0.5 Engineering Brief relays the Orchestrator's 2026-10-07 decision that P0 was `ACCEPTED` and `PHASE CLOSED`; the Engineering Lead verified integrated `main` at `5175d5b09e8d412e11b2ddf4c24bff41df133843` and successful [push CI 37649030624](https://github.com/KastaTM/card-market-tracker/actions/runs/37649030624). P0.5 is the active feasibility investigation; no later phase is opened by this note.

| Order | Phase | Intended outcome |
| --- | --- | --- |
| 1 | P0 Foundation | Installable, observable local baseline and quality process |
| 2 | P0.5 Source Feasibility | Legal, technical, and data-quality feasibility of candidate sources |
| 3 | P1a Catalog Core | First provider-independent catalog slice |
| 4 | P3a Observation Persistence | Store a minimal validated observation history |
| 5 | P2 Market Data | First market-price ingestion and semantics |
| 6 | P6a First Retail Adapter | One isolated retailer adapter and stock/price observations |
| 7 | P4 Discovery | Detect and review previously unknown products |
| 8 | P8a Alert Delivery | Initial delivery capability with deduplication |
| 9 | P5 Watchlist | Known-product monitoring rules |
| 10 | P7 Launch/Preorder | Launch, coming-soon, and preorder signals |
| 11 | P6b Retail Expansion | More retail sources after first-adapter learning |
| 12 | P3b/P10a Historical Queries/Reference Metrics | Query history and derive cautious reference metrics |
| 13 | P9 Opportunities | Explainable prioritization combining evidence and costs |
| 14 | P9.5 Operational Readiness | Long-running Pi operations, recovery, and monitoring |
| Later | Extensions | Broader markets, portfolio, advanced analytics when justified |

Each subsequent phase needs its own contract and acceptance gates. Source legality and feasibility remain open until P0.5. Graded valuation, automated trading, native mobile, Kubernetes, Kafka, and speculative forecasting are outside the initial plan.

## P0.5 feasibility dependency (candidate; Orchestrator decision pending)

The dated [P0.5 selection](sources/SOURCE_SELECTION.md) supports TCGdex as a bounded singles/set catalog seed; Scrydex documents sealed products and sold listings but has no verified access, Spanish/EUR coverage or reuse rights. No currently qualified EUR market-history feed or authorized retail monitoring route was found. P1a still requires coverage, variant and field-rights checks. P2 needs a compatible market-data license and explicit price semantics. P6a and retail P4 discovery need written retailer or feed access and a lawful bounded probe; P4 may study new card/set candidates from TCGdex while Scrydex sealed candidates remain conditional. The Orchestrator must decide any schedule or product-scope change. This note neither opens those phases nor changes their acceptance criteria.

RW-01 supports AC-F05's discovery route narrowly through TCGdex's existing ES set-list probe: future unknown-set candidates can be proposed without making the provider ID canonical. No temporal comparison or new launch was observed. This feasibility result does not remove P6a's access gap or the retail part of P4; coverage, pagination, order, ID stability, freshness and field-retention policy still require validation in an implementing phase. RW-02 was conditional and was not executed because RW-01 was sufficient for this limited criterion.
