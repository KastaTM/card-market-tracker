# eBay Browse — P0.5b narrow ES/EUR review

Date: 2026-10-14 Europe/Madrid. Verdict **CONDITIONAL** for active-listing
discovery. No authenticated probe, CMT production approval, listing sample,
account or credential. Requests: 0. Preserve [P0.5 history](EBAY_BROWSE.md).
SEC reviewed only the points relevant to a limited ES/EUR use, not a new full
provider investigation. Evidence below is `documented`; actual supply is `unknown`.

## Rights by field/use

| Exact group / origin | Minimum use | Primary evidence and applicable condition | Retention, display, publication and uncertainty |
| --- | --- | --- | --- |
| `itemId,itemWebUrl,title`, condition/aspects / eBay listing and seller/catalog content | External offer reference and conservative candidate matching | [Browse guide](https://developer.ebay.com/api-docs/buy/api-browse.html), Search/Retrieve/Item ID; [API license](https://developer.ebay.com/join/api-license-agreement) §§3.1(2),5,9.7 | Necessary intermediate copies only within authorized use; no general dataset/fixture grant. Title/aspects do not prove language/finish/authenticity |
| `price.value,price.currency,buyingOptions`, shipping-cost fields / seller offer | Separate fixed ask, auction bid and delivery cost | Browse guide, Header for shipping information accuracy; license §§8.1(2–4),9.5 | Display freshness <=6h for listings, <=24h for other content; disclose lag and remove no-longer-public content. These are not history retention periods |
| `itemCreationDate,itemEndDate`, estimated availability / listing lifecycle | Offer timing, never product release or sale | Historical method evidence; current method page was not readable; guide supports purchasable listings | Not newly method-verified; active offers never supply `sold_at`. Do not infer completed sales |
| Seller identity/feedback, images, extended descriptions / user or third-party content | No minimum CMT need demonstrated | License ownership/no-implied-rights clauses | Excluded from candidate scope; reduce personal/IP data |

License §8.1(2) requires visually separate eBay content. §8.1(4) requires written
permission for the statistics enumerated there; this does not mean every possible
comparison is expressly banned. §9.5 restricts price suggestion/modeling.
§3.1(2) requires deleting intermediate copies when unnecessary; §16.3 requires
destroying content copies within ten days of termination, and §17 limits disclosure.
Private display does not eliminate the authorized-purpose/storage limits. A
durable cross-source CMT history is not established by the standard grant.

## Access, coverage and operational limits

[Buy overview](https://developer.ebay.com/develop/api/buy) and
[Buy requirements](https://developer.ebay.com/api-docs/buy/buy-requirements.html),
Production eligibility/Contractual requirements: keyset/OAuth application token,
approval and contracts; sandbox is distinct from production. CMT entitlement
remains unknown. No human action was executed.

[Marketplace support](https://developer.ebay.com/api-docs/buy/static/ref-marketplace-supported.html)
documents `EBAY_ES` for Browse item_summary/item. [Filters](https://developer.ebay.com/api-docs/buy/static/ref-buy-browse-filters.html)
describe deliveryCountry/postcode, item-location constraints and priceCurrency
with price range. Actual returned currency, origin, delivery, tax and language
need verification; marketplace EUR/ES is not Spanish supply or landed cost.

[Call limits](https://developer.ebay.com/develop/get-started/api-call-limits)
official indexed text suggests default5000/day except getItems, separately5000/day,
and an additional Buy license. Full canonical page retrieval failed: these quota
figures are provisional locator information requiring full-source verification,
not a validated current operational quota. Earlier pagination/newlyListed/10000-result-cap claims
remain dated P0.5, not newly method-verified. Quota is not permission.

| Action | Decision for source data |
| --- | --- |
| Consult transiently | CONDITIONAL: approved production access/exact authorized use |
| Save minimal sample | CONDITIONAL: necessary licensed intermediate copy, deletion rules |
| Store in future CMT | CONDITIONAL: explicit retention scope, future phase authorization |
| Publish real fixture/documentation | NO under evidenced standard grant; separate permission required |
| Compare/derive/history | CONDITIONAL: precise comparison/statistics/history permission |

| Dimension | Finding |
| --- | --- |
| ACCESS | Production approval/token/contracts not established |
| RETENTION | Standard-purpose/deletion/freshness restrictions; durable history unsupported |
| SEMANTICS | Active listing asks/bids, never sold-price feed; seller fields unverified |
| COVERAGE | ES marketplace documented, real Pokémon/EUR/delivery unknown |
| OPERATIONAL_LIMITS | Quota figures provisional indexed locator only; current method pagination not reverified |

Resolution: human production eligibility and written use review covering samples,
private display, storage duration, deletion, comparisons and publication.
No eBay probe justified now. P2 EUR historical market reference stays blocked.
