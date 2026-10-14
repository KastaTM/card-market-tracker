# Scrydex — P0.5b EUR/history qualification

Date: 2026-10-14 Europe/Madrid. Verdict **REJECTED_FOR_PROPOSED_USE** as CMT's
EUR/Spain market reference. This rejects the requested use, not the existence of
USD/JPY data or a potentially compatible separate scope. No API calls, plan,
team, key, account or expense; requests0. [P0.5 history](SCRYDEX.md) retained.

## Currency, fields, semantics and rights

[Pricing Data, Currency Correlation](https://scrydex.com/docs/getting-started/prices)
still describes USD/US and JPY/Japanese markets, with EUR a future expansion.
`low` is a minimum; `market` is aggregated across sources; trends are changes,
not transaction records. Do not convert those currencies to simulate Europe.

| Exact group / origin | Minimum use and evidence | Timestamp/coverage | Applicable right / uncertainty |
| --- | --- | --- | --- |
| `condition,type,low,market,currency,trends.*` / Scrydex aggregates | Possible reference metric; documented only | Market provenance/methodology for every point unknown; no operational EUR evidence | [Terms](https://scrydex.com/terms) §§4,9–11; IP reserved, no implied rights, extraction/mirroring/redistribution/commercial reuse restrictions |
| History `date,prices[].variant,condition,type,low,market,currency` and flags / daily provider history | Historical provider metric; [Price History](https://scrydex.com/docs/pokemon/price-history), object/Get price history | Calendar YYYY-MM-DD, one day per entry; timezone/cutoff unknown, never capture instant or individual sale | Operational local historical chart storage supported by guidance below; indefinite independent retention unresolved |
| Listing `id,source,card_id,title,variant,price,currency,sold_at,url` / upstream sold listing | Separate sold-sale class; [Listings](https://scrydex.com/docs/pokemon/listings), listing object/Search listings | `sold_at` documented YYYY/MM/DD; eBay/USD example is documentation, not observed EUR sale or upstream license | Upstream rights unresolved; no URL following, seller/title/image data excluded from minimal sample unless justified |

Material new evidence: [Best Practices, Caching / Implement Local Database Storage](https://scrydex.com/docs/getting-started/best-practices)
expressly recommends local DB storage for historical charts, card/expansion lists,
listings/recent sales, and at least24h pricing caching because updates occur at
most daily. This is positive evidence of operational storage, which the old
fiche did not fully describe. It does not establish perpetual, post-termination
or redistribution rights. Terms restrict dataset extraction/mirroring and end
service-use rights on termination. Client retention/deletion duration and
attribution requirements were not established; reconcile these documents for
the exact use before independent durable history. No blanket prohibition of
local history or blanket license is inferred.

## Access and decisions

[Authentication](https://scrydex.com/docs/getting-started/authentication) describes
normal team/key/plan access and heavily reduced anonymous limits; no entitlement
or quantified usable anonymous quota was observed. [Pricing](https://scrydex.com/pricing)
still advertises Starter USD29/month,5000credits; history typically costs3credits.
[Rate limits](https://scrydex.com/docs/getting-started/rate-limits) describes100/s
alongside credits/overage/abuse controls. No spending is authorized or incurred.

| Action | Decision for source data |
| --- | --- |
| Consult transiently | CONDITIONAL: entitlement, limits and compatible exact use |
| Save minimal sample | CONDITIONAL: scope/license/upstream rights reviewed |
| Store in future CMT | CONDITIONAL: operational guidance exists; duration/post-termination/future phase unresolved |
| Publish real fixture/documentation | NO without written authorization |
| Compare/derive/history | CONDITIONAL: local charts documented; durable independent history/redistribution unresolved |

| Dimension | Finding |
| --- | --- |
| ACCESS | Ordinary plan/key/team; reduced anonymous route documented, unobserved |
| RETENTION | Operational storage guidance positive; durable independent rights remain conditional |
| SEMANTICS | Aggregate/daily point/sold listing separate; timestamps are not interchangeable |
| COVERAGE | EUR future, actual ES/EU coverage unknown; fails proposed EUR route |
| OPERATIONAL_LIMITS | Credit/plan/rate controls; no actual operational sample |

Resolution for EUR: operational European currency/market evidence, compatible
rights and authorized access. A USD/JPY alternative needs a separate Orchestrator
scope decision. No authenticated or anonymous data probe was needed to resolve
the current currency blocker. P2 remains blocked.
