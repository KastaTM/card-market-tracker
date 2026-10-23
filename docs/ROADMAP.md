# Roadmap

## Orchestrator chat decision: P8b closed, P5a open (2026-10-23)

The user-supplied P5a opening contract records the Orchestrator decision that P8b
is ACCEPTED / PHASE CLOSED following PR #14 integration at
`d1038df1625a9727b44760866266b7124bb1d91a` (tree
`2bb06b79a04fefdc945f754e3611d5862192f5dc`). P5a Watchlist Core and Offline Rule
Evaluation is OPEN / IMPLEMENTATION AUTHORIZED on that baseline. This entry
records that chat decision under its explicit documentary authorization; the
earlier connector 403 did not publish it remotely. P5a does not close all P5 or
authorize real price monitoring. P2, P6a and retail Discovery remain BLOCKED;
TD-001 through TD-005 remain OPEN. Historical records below remain intact.

## Orchestrator chat decision: P8a closed, P8b open (2026-10-21)

The supplied [P8b contract](phases/P8B_TELEGRAM_ALERT_DELIVERY_CONTRACT.md)
records the Orchestrator chat decision accepting/closing P8a and opening P8b
manual private Telegram delivery. This attributes the decision to that contract;
it does not claim a new approval was published to GitHub. Verified baseline is
main `ac35d4df0f3a006ff60bb026de992c366e19cc09`, tree
`d604d3b8362c30af8b5dd516eddc0d8095fe7bf9`. P8b uses an independent ledger
and preserves outbox/capture/journal bytes, identities and schemas. No scheduler,
source acquisition or commercial signal expansion. P2/P6a/retail Discovery remain
BLOCKED; P5 stays unopened; TD-001..TD-005 remain OPEN. Merge and phase acceptance
are separate Orchestrator decisions. See [engineering plan](phases/P8B_IMPLEMENTATION_PLAN.md).

## Orchestrator chat decision: P4c closed, P8a open (2026-10-20)

The supplied [P8a contract](phases/P8A_OFFLINE_ALERT_OUTBOX_CONTRACT.md) records
the Orchestrator's acceptance and closure of P4c in chat and opens P8a Offline
Alert Outbox. [PR12](https://github.com/KastaTM/card-market-tracker/pull/12) is
merged at `b89fff319a94e5eb6e4b7bdad944e879bad371f6`, tree
`8f62a1d85b375ee839dcd95e09a578cb643c85b6`, ordered parents
`de63457bd6de26874a30d2afd688dcd8901e01ff` and
`9fb53144dec521d0dde49c02d41022be831421c2`. Local Git objects and live main
were checked before edits. No GitHub closure comment is asserted. Historical
[P4c main CI](https://github.com/KastaTM/card-market-tracker/actions/runs/39462043464)
is not P8a evidence.

P8a authorizes a separate pending offline outbox, deterministic identity per
destination/event, complete evidence per comparison, origin recomputation,
read-only preview and local recovery. Acquisition budget is zero. Captures
schema2, journal schema1, existing comparators/identities and exact R0/R1 plus
synthetic constraints remain. P2, P6a and retail Discovery remain BLOCKED;
P5/P8b are not open. TD-001 through TD-005 remain OPEN. The
[P8a report](phases/P8A_OFFLINE_ALERT_OUTBOX.md) records executable evidence;
only the Orchestrator may accept or close the phase. Merge is not authorized.
Earlier entries below preserve historical decisions.

## Orchestrator chat decision: P1c closed, P4c open (2026-10-19)

The supplied [P4c contract](phases/P4C_DISCOVERY_RESULT_JOURNAL_CONTRACT.md)
records P1c ACCEPTED / PHASE CLOSED and opens P4c Discovery Result & Event Journal.
This attributes the decision to the Orchestrator chat; no GitHub closure comment
is asserted. P1c PR11 merge/base is de63457bd6de26874a30d2afd688dcd8901e01ff,
tree41c0f758c8a4bf09cc719a1ce16073245a5aadda, ordered parents
112916382ce02486ca38eb14487220dbb24196e7 and
8af647697dd67859b38fc007d493a54642a1d62f. Host fetch verified those objects.

P4c adds only a separate journal for verified v3 results and event occurrences,
bounded queries, replay, verification/recompute and recovery. No new acquisition.
P2/P6a and retail Discovery stay BLOCKED; P5/P8a are not opened. P4c engineering
readiness, merge, acceptance and closure remain distinct decisions. Existing
sections below preserve historical snapshots.

## P4b closure and P1c opening ? Orchestrator decision, 2026-10-17

The supplied [P1c contract](phases/P1C_MULTI_REVISION_METADATA_CAPTURE_CONTRACT.md)
records the Orchestrator's P4b **ACCEPTED / PHASE CLOSED** decision in chat and
opens **P1c Multi-Revision Metadata Capture**. No published closure comment is
invented. [PR10](https://github.com/KastaTM/card-market-tracker/pull/10),
[integration record](https://github.com/KastaTM/card-market-tracker/pull/10#issuecomment-6235092935)
and [historical main CI39040138813](https://github.com/KastaTM/card-market-tracker/actions/runs/39040138813)
remain historical P4b evidence. Fetched baseline/main is
`112916382ce02486ca38eb14487220dbb24196e7`, tree
`c79edde3f13c5983d11505f5917f91559265b506`, ordered parents
`430e2049c9ffdffb68508329df6556bfed62baa2` and
`ab5e0fa7d4225c2ce137ce2261cd9686ef765a32`.

P1c permits exactly R0/R1 minimum packages and a separate profile-authorized v3
comparison in schema2. Four real units must compare with no_discoveries/zero
events because the approved projections are equal. Positive tests are synthetic.
No third capture, source, corpus expansion, schema3 or commercial operation is
authorized. P2/P6a/retail Discovery remain BLOCKED, TD-001?TD-005 remain open.
P1c acceptance/closure/integration remain Orchestrator decisions; earlier entries
preserve historical scope.

## P1b closure and P4b opening — Orchestrator decision, 2026-10-16

The user-supplied [P4b contract](phases/P4B_SCOPED_CAPTURE_DISCOVERY_CONTRACT.md)
records the Orchestrator's **P1b ACCEPTED / PHASE CLOSED** decision in chat and
opens **P4b Scoped Capture Discovery**. No published closure comment is invented.
[PR9](https://github.com/KastaTM/card-market-tracker/pull/9), its
[integration record](https://github.com/KastaTM/card-market-tracker/pull/9#issuecomment-6212185019)
and [main CI38877640587](https://github.com/KastaTM/card-market-tracker/actions/runs/38877640587)
are historical evidence. Fetched main is `430e2049c9ffdffb68508329df6556bfed62baa2`,
tree `c3988a86cedf525cce364bd9cc4709689c510053`, parents base
`acca10e406dac8809edc289c3077a6ec8785a622` then head
`252c394141948e3ab77a54bcf628e4290ba69652`.

P4b authorizes a separate read-only v2 route over persisted capture units,
without a schema change or further source acquisition. The fixed P1b package
has one acquisition/capture instant: four unit baselines are real evidence;
positive temporal events use explicitly synthetic persisted captures only.
Discovery v1 remains synthetic-only. P2/P6a/retail Discovery remain BLOCKED,
TD-001–TD-005 remain open, and merge/phase closure require Orchestrator decisions.
Earlier entries below remain historical snapshots.

## P0.5b closure and P1b opening — Orchestrator decision, 2026-10-14

The supplied [P1b contract](phases/P1B_PINNED_METADATA_INGESTION_CONTRACT.md)
records P0.5b **ACCEPTED / PHASE CLOSED** and opens P1b Pinned Metadata
Ingestion & Capture Scope. Codex verified fetched baseline
`acca10e406dac8809edc289c3077a6ec8785a622`, tree
`26011d0375f3716a7fffb31956665eb97567a0df`, ordered parents
`6385c952a9f2024c8b7bdb33d37fa21017029bd5` then
`302e8d3f3155c14091d26841b8a230791109f220`. [PR8](https://github.com/KastaTM/card-market-tracker/pull/8)
and its [main CI](https://github.com/KastaTM/card-market-tracker/actions/runs/38595222923)
are historical P0.5b evidence. This note attributes the decision to Orchestrator;
it does not invent a published closure comment or certify P1b gates.

P1b permits only the pinned two-artifact/four-projection repository route,
explicit capture context and SQLite v1→v2 migration. TCGdex REST and all broader
source grants retain their conditions; P2/P6a/retail Discovery remain BLOCKED.
P4a stays synthetic-only. No merge or later phase opening is authorized.
TD-001–TD-005 remain open; new local scope cannot authenticate legacy or
independent producers. Entries below are dated historical snapshots.

## P4a closure and P0.5b opening — Orchestrator decision, 2026-10-13

The user-supplied [P0.5b contract](phases/P0_5B_REAL_SOURCE_QUALIFICATION_CONTRACT.md)
records **ACCEPTED / PHASE CLOSED** for P4a and opens **P0.5b Real Source
Qualification**. These are Orchestrator decisions, not Codex acceptance. Local
fetch verified main `6385c952a9f2024c8b7bdb33d37fa21017029bd5`, tree
`8fa2abeb9f4e8991bab1b2895fc397f64bb39a19`, ordered parents
`734641a7ef920688677cdea6bc82f908a2856927` and
`c5ed228af831a2a6ed8a12c7072777d3908296a5`. [PR7 integration ledger](https://github.com/KastaTM/card-market-tracker/pull/7#issuecomment-6155836622)
and [main push CI38471731980](https://github.com/KastaTM/card-market-tracker/actions/runs/38471731980)
are historical P4a evidence. No published closure comment is invented and no
historical tests are credited as P0.5b execution.

P0.5b investigates exact source fields/rights/access and proposes capture policy;
it changes no runtime, schema, identity or synthetic-only control. Its current
[selection](sources/SOURCE_SELECTION.md) leaves TCGdex/eBay/GAME/Awin conditional
and rejects Scrydex for the requested EUR route. P2/P6a/retail Discovery stay
**BLOCKED**; no P1b or other phase is opened. TD-001–TD-005 remain open. Earlier
entries below retain their historical dates and phase state.

## P3a closure and P4a opening — Orchestrator decision, 2026-10-12

The archived [P4a contract](phases/P4A_OFFLINE_TEMPORAL_DISCOVERY_CONTRACT.md)
records the Orchestrator's **ACCEPTED / PHASE CLOSED** decision for P3a and opens
**P4a Offline Temporal Discovery** ahead of P2/P6a. Local fetch verified baseline
`734641a7ef920688677cdea6bc82f908a2856927`, tree
`ae61fe57e6f874b138c98ecdaaa8cbd830406354`, ordered parents
`c6e66a2aba469d02f0ca63fde3b81ecc5eea41bc` then
`e9c5f02e7f093dedff55b67f137c4446f22e8735`. Historical [PR6 integration ledger](https://github.com/KastaTM/card-market-tracker/pull/6#issuecomment-6131957615)
and [exact-main CI](https://github.com/KastaTM/card-market-tracker/actions/runs/38302824438)
support the opening; they do not prove P4a gates. The contract reports the
Orchestrator's closure comment publication failed with403; its decision was issued
in chat. No successfully published closure comment is asserted here.

P4a compares explicit bounded synthetic capture windows, without sources,
schema migration, delivery or promotion. It does not implement all of P4 or
prove launch/global novelty/source health. P2 and P6a/retail Discovery remain
**BLOCKED**; TCGdex remains provisional and TD-001–TD-004 remain open. Phase IDs
retain their meaning; earlier scheduling and status entries below are historical.

## P1a closure and P3a opening — Orchestrator decision, 2026-10-10

The [P3a contract](phases/P3A_OBSERVATION_PERSISTENCE_CONTRACT.md) records the
Orchestrator's **ACCEPTED / PHASE CLOSED** decision for P1a and opens **P3a
Observation Persistence** for offline synthetic metadata only. Local `git fetch
origin` verified main `c6e66a2aba469d02f0ca63fde3b81ecc5eea41bc`, tree
`a9717922736a6220d3ff05293bec4cb222644269`, with ordered parents
`af573f04586024e7666a8999526e0aaab238c0dc` then
`93a17711cb75f91816e41279fe76069055391e50`. [PR5](https://github.com/KastaTM/card-market-tracker/pull/5)
is merged; its exact-main [push CI37965128340](https://github.com/KastaTM/card-market-tracker/actions/runs/37965128340)
has four successful jobs, whose execution logs were inspected. These are historical
P1a results, not P3a gates. P3a requires its own candidate, independent reviews and
CI; merge is not authorized. P2 and P6a/retail Discovery remain **BLOCKED** for
source access, retention rights and semantics. Earlier entries below are historical.

## Subsequent Orchestrator decision — 2026-10-09

The authorized [P1a contract](phases/P1A_CATALOG_CORE_CONTRACT.md) records the
Orchestrator's acceptance and closure of P0.5 after PR #4 and
[main push CI 37956251863](https://github.com/KastaTM/card-market-tracker/actions/runs/37956251863).
Baseline `af573f04586024e7666a8999526e0aaab238c0dc`, tree
`878cba9cfadfea47beaf0b6727469c3926dc25c9`, has ordered parents
`1dc890c7410e3d9c718654e9f64380f9e5026042` and
`253a5354d8645fa8c72cbd7038e213832ab8ce18`. Local fetch and Git objects were
verified before P1a edits. P1a is now authorized for an offline catalog core.
P3a is not opened; P2 and P6a/retail Discovery remain blocked by source access,
retention and semantics. Historical statements below describe earlier decisions.

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

## P0.5 integration and dependencies — Orchestrator decision, 2026-10-08

The Orchestrator authorized integration of [PR #3](https://github.com/KastaTM/card-market-tracker/pull/3) exclusively at reviewed head `61ab2fcb630e2504869b68c97ea8cd1385e4ee00`, base `5175d5b09e8d412e11b2ddf4c24bff41df133843` and tree `682e914beb25263c7e73d4e5540553f7b5b356ee`. The Engineering Lead verified and integrated it by guarded GitHub merge commit `1dc890c7410e3d9c718654e9f64380f9e5026042`, preserving that tree and those ordered parents. Its exact-SHA [main push CI 37693923894](https://github.com/KastaTM/card-market-tracker/actions/runs/37693923894) passed quality, Compose, AMD64 and QEMU ARM64. [The phase record](phases/P0_5_SOURCE_FEASIBILITY.md) contains the evidence and limits. Integration is not phase acceptance or closure.

The Orchestrator's dependencies are explicit: **P1a is next only after P0.5 closure**, and is not opened here. **TCGdex is provisional for card/set metadata**, subject to fields and rights. **P2 remains blocked** until EUR source access, retention and price semantics are evidenced. **P6a and retail Discovery remain blocked** until a compatible source is evidenced. Set enumeration does not prove retail, sellable sealed products, stock or preorders. No purchases, signups or external contacts are authorized. This post-integration documentary update is proposed separately; its own review and CI are tracked in its documentary PR, without modifying PR #3's approved head.

The dated [P0.5 selection](sources/SOURCE_SELECTION.md) supports TCGdex as a bounded singles/set catalog seed; Scrydex documents sealed products and sold listings but has no verified access, Spanish/EUR coverage or reuse rights. No currently qualified EUR market-history feed or authorized retail monitoring route was found. P1a still requires coverage, variant and field-rights checks. P2 needs a compatible market-data license and explicit price semantics. P6a and retail P4 discovery need written retailer or feed access and a lawful bounded probe; P4 may study new card/set candidates from TCGdex while Scrydex sealed candidates remain conditional. The Orchestrator must decide any schedule or product-scope change. This note neither opens those phases nor changes their acceptance criteria.

RW-01 supports AC-F05's discovery route narrowly through TCGdex's existing ES set-list probe: future unknown-set candidates can be proposed without making the provider ID canonical. No temporal comparison or new launch was observed. This feasibility result does not remove P6a's access gap or the retail part of P4; coverage, pagination, order, ID stability, freshness and field-retention policy still require validation in an implementing phase. RW-02 was conditional and was not executed because RW-01 was sufficient for this limited criterion.
