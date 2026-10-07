# Source ingestion requirements v0

**Status:** preliminary P0.5 requirements; no provider contract, runtime model, or persistence schema is active.

**Future producer:** an isolated, authorized source adapter. **Future consumer:** validation, then normalized ingestion, then the provider-independent domain. The boundary is `External Source → Validation → Normalized Ingestion → Domain`. [The source matrix](../sources/SOURCE_MATRIX.md) and individual dated fiches record which providers could eventually supply each field. Their documented behavior is not an implemented guarantee.

## Semantics and provenance

An external identifier or name is evidence about a source record, never CMT's canonical product identity. A record for an unfamiliar product must remain an unknown candidate for later review; it must not be discarded or forced onto a known product. Keep singles and sealed separate. A listing price, completed-sale price, provider aggregate, and MSRP are different observations and cannot be substituted for one another. EUR alone does not establish that an offer is relevant to Spain or Europe. Every future observation needs its source, method, capture time, source terms reference, and scope.

## Preliminary fields

These are requirements to refine in P1a, P2, P6a, and P4. `Required` means the future normalized boundary should reject or quarantine an observation that lacks the field; it does not claim every candidate provider supplies it.

| Concept | Requirement | Validation and null rule |
| --- | --- | --- |
| `source_key` and `captured_at` | Required | CMT-assigned provider key and UTC capture timestamp with provenance; never infer capture time from a release date. |
| `source_record_id`, `source_url`, `source_sku` | At least one stable traceable reference required where available | Keep the provider namespace. URLs must be validated against an approved host and safe redirects before any future fetch; do not promote external IDs to domain IDs. A missing stable ID is a source-specific feasibility risk. |
| `entity_kind` | Required | Distinguish single card, sealed product, listing, and unknown candidate. A source's broad label is not proof of the correct kind. |
| `name`, `set`, `card_number`, `language`, `variant`, `condition` | Nullable source evidence | Preserve raw distinctions and explicit null/unknown. Card number and set can identify a source card but do not establish canonical matching. Variants and conditions must not collapse into a base card. |
| `release_at`, `source_updated_at`, `first_seen_at` | Optional and semantically distinct | Store a source date only when provided with known meaning. `first_seen_at` is CMT's own first observation, never copied from a provider's release or publication date. |
| `price_amount`, `price_currency`, `price_type` | Required together when a price exists | Parse decimal text losslessly and validate finite nonnegative values; currency uses an explicit ISO 4217 code. `price_type` must distinguish active listing, completed sale, aggregate, and MSRP, with unknown when the provider does not prove the type. Do not convert USD/JPY to EUR without a separately evidenced conversion policy. |
| `shipping_amount`, `tax_inclusion`, `marketplace`, `seller_kind` | Nullable | Shipping and tax scope affect effective acquisition cost; absence is unknown, not zero. Marketplace and seller kind distinguish Spain/EU relevance and retailer-owned from third-party offers. |
| `stock_status`, `preorder_status` | Nullable, time-scoped | Distinguish available, out of stock, preorder, coming soon, and unknown only when source text and terms support the meaning. A missing field is not out of stock. |
| `source_license`, `retention_rule`, `redistribution_rule` | Required policy metadata before production use | Link dated terms and record permitted storage, caching, display, and deletion requirements. Unknown permission blocks retention or redistribution. |

## Partial responses, errors, and safety

Validation must preserve a partial-data flag and field-level nulls; an incomplete result must not silently become a complete product or zero-price observation. Classify authentication denial, policy/access block, rate limit, timeout, network failure, oversized response, invalid format, incompatible field change, and valid empty result separately. A one-time HTTP success is not a source-health state. Future adapters need bounded request counts, timeout, response-size limits, controlled pagination and redirects, and redacted logs. No credentials, cookies, personal data, or full payloads belong in fixtures or logs.

## Compatibility and future tests

P0.5 only records requirements. An implementing phase must define its own versioned provider contract, allowed field additions, breaking-change behavior, minimal permitted fixtures, contract tests, and retention enforcement. External input remains untrusted until validated. No live source test is added to CI by this document.
