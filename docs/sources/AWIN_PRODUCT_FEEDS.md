# Awin Product Feeds — P0.5b qualification

Date: 2026-10-14 Europe/Madrid. Route R2, verdict **CONDITIONAL**. A materially
different affiliate feed route, not retailer HTML. Evidence `documented` schema
and access rules; concrete Pokémon ES/EU feed, CMT entitlement and usable fields
are `unknown`. No account, programme application, token, contract acceptance,
payment, feed download or direct data request; requests0.

## Eligibility and rights

[Publisher Guide, introduction](https://help.awin.com/developers/docs/product-feed-publisher-guide-intro)
describes promotion/price-comparison use. [Feed List Download](https://help.awin.com/developers/docs/product-feed-list-download)
and [Create-a-Feed](https://help.awin.com/developers/docs/downloading-feeds-using-create-a-feed)
require a distinct data-feed key and joined programmes or advertiser-enabled
pre-join access. Documentation is not an observed account entitlement.

[Publisher Terms routing](https://www.awin.com/ca/publisher-terms), Which T&Cs
apply, routes EU tax residents to AWIN AG terms. Full retrieval of linked
[August2025 Spanish terms](https://www.awin.com/docs.awin.com/Legal/Publisher%2BTerms/2025/ES_Awin-AG-Publisher-terms_August-2025.pdf)
failed in the browser; official indexed primary extracts were readable. Evidence
is **provisional indexed locator, not verified applicable conditions**. The
extract points to sections10.1/10.4/10.6–10.7 about promotion/programme purpose,
IP and disclosure, but does not substitute reading the full primary source.
On a supplementary document attempt at11:20:50UTC the browser reported403;
no retry of that denied endpoint or evasion followed. No license or deletion
deadline is concluded from the index. Full applicable terms remain unknown.

Personal private-tool eligibility and non-promotional historical analytics are
unresolved. Marketing comparison examples do not grant them. Retention duration,
deletion, after-termination use, modifications, attribution/deep-link obligations
and raw redistribution require the complete applicable terms plus the concrete
advertiser's conditions. No specific eligible Pokémon programme/feed was verified
without creating an account. Do not claim that none exists.

## Exact field groups and evidence

All groups are advertiser content or Awin enrichment, subject to the same
conditional programme/purpose rights above. Minimum use: external sealed-offer
reference and time-scoped lifecycle/price evidence in a future authorized phase.
Schema support does not demonstrate population, correctness or rights in a feed.
No real values are retained. Images, extensive text and user data excluded.

| Format / exact fields | Origin and minimum meaning | Evidence/retention uncertainty |
| --- | --- | --- |
| Legacy download: `merchant_id,merchant_name,merchant_product_id,aw_product_id,aw_deep_link,merchant_deep_link` | Advertiser identity/product reference plus network IDs/links | [Feed List Download](https://help.awin.com/developers/docs/product-feed-list-download), Example output; identity external only, no evidence advertiser equals seller |
| Legacy: `search_price,store_price,currency,delivery_cost,delivery_restrictions` | Offer amount/currency and logistics | Same format documentation; actual EUR/tax/destination context unknown; absent shipping never zero |
| Legacy: `in_stock,stock_quantity,stock_status,is_for_sale,pre_order,last_updated,valid_from,valid_to` | Availability/orderability/product update assertions | [Hosting feeds](https://help.awin.com/developers/docs/hosting-feeds), Generic column descriptions; private history rights unresolved |
| Legacy: `ean,product_GTIN,mpn,parent_product_id` | Manufacturer/advertiser identifiers and grouping | Documentation only, no validated GTIN or exact variant in actual feed |
| Enhanced: `meta.advertiser_id,meta.advertiser_name,product_basic.id`; product `gtin,mpn,brand` | Advertiser and product identity | [Enhanced API](https://help.awin.com/apidocs/retail-publisher-productapidocumentation-1) and [specification](https://help.awin.com/developers/docs/enhanced-feeds-prod-spec); no seller attribution proof |
| Enhanced: `availability,availability_date,price,sale_price,shipping` | Retail offer, ISO currency and destination shipping | Specification, Price and availability; supported in_stock/out_of_stock/preorder/backorder, not a sold transaction |

Do not silently equate legacy download column names with advertiser upload
`product_id/price` or enhanced JSON. Preserve format/version and transformation.
Hosting documentation describes `last_updated` as product update, not CMT capture;
`pre_order` as orderable before stock. Legacy `in_stock` normalization can treat
blank as unavailable and arbitrary non0/1 text as available; raw schema semantics
require careful validation, not direct CMT stock truth. Documentation language is
not product/card language. Feed import, product update, capture and first seen
are separate times; no feed timestamp automatically supplies `sold_at`.

## Completeness and operations

Enhanced API, Authentication/Last Line/Usage Limits: bearer token, publisher ID
and feed permission; <=5 requests/minute and no simultaneous downloads of the
same advertiser feed. An HTTP200 can end with an error and incomplete feed.
Feed-list metadata includes last import and mapped columns; verify actual
population and refresh policy for the advertiser. No SLA or complete Pokémon
ES/EU availability was established.

A future permitted comparison must namespace advertiser+feed+product, record
selector/language/currency/capture interval and validate a complete successful
feed. New reference means first seen in that explicit scope, not product launch.
Filtered/inaccessible/partial feeds, missing products and import failure must not
produce withdrawal/stock or zero-product success. No recurring feed importer
or detection is implemented.

| Action | Decision for source data |
| --- | --- |
| Consult transiently | CONDITIONAL: publisher/feed eligibility and compatible purpose |
| Save minimal sample | CONDITIONAL: exact advertiser/network conditions and fields |
| Store in future CMT | CONDITIONAL: personal/private history permission, duration/deletion/future phase |
| Publish real fixture/documentation | NO for this task: permission has not been evidenced; not a conclusive terms prohibition |
| Compare/derive/history | CONDITIONAL: promotional comparisons documented; private durable history unresolved |

| Dimension | Finding |
| --- | --- |
| ACCESS | Network/programme/key or enhanced token; no actual entitlement |
| RETENTION | Guide describes promotional use cases, not a verified applicable grant; private history/duration/deletion/publication unknown |
| SEMANTICS | Strong schema possibilities, format normalization/advertiser-seller/timestamps need qualification |
| COVERAGE | Concrete Pokémon ES/EU/EUR feed and required populated fields unknown |
| OPERATIONAL_LIMITS | Enhanced5/min/no concurrent advertiser downloads/final-line check; advertiser update policy unknown |

Human pending actions: choose whether to seek publisher/programme eligibility,
obtain full applicable network and advertiser terms, confirm personal/private
storage/history rights and one concrete eligible feed, then authorize a bounded
probe in a later approved budget. Nothing here executes those actions or qualifies
a retailer. P6a/retail Discovery remains blocked.
