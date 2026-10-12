# P1a fixture provenance

All `synthetic_*` files in this directory are authored examples, not captured API
responses or commercial records. Date: 2026-10-09. Source shape:
[TCGdex REST card](https://tcgdex.dev/rest/card),
[card reference](https://tcgdex.dev/reference/card),
[REST set](https://tcgdex.dev/rest/set), and
[set reference](https://tcgdex.dev/reference/set), reviewed that date.
See [field and rights policy](../../docs/sources/TCGDEX_P1A_FIELDS.md).

| Fixture | Purpose |
| --- | --- |
| `synthetic_tcgdex_valid.json` | ES/EN set localizations; separate curated normal/holo/reverse observations; leading-zero and prefixed card numbers. |
| `synthetic_tcgdex_candidates.json` | Unmapped set and unknown printing variant despite true availability flags. |
| `synthetic_tcgdex_mixed.json` | Valid set, ambiguous card candidate, incompatible null card number. |
| `synthetic_tcgdex_empty.json` | Valid empty records, distinct from failure. |
| `synthetic_tcgdex_invalid.json` | Globally incompatible envelope version. |
| `synthetic_tcgdex_malformed.json` | Intentionally invalid JSON to exercise parsing failure. |
| Other `synthetic_*` manifests/ingestion | Curated internal IDs, equivalences and sealed samples authored for the domain tests; no real products or provider responses. |

`version`, `provenance`, `records`, wrapper `language`, `kind`, and `variant` are CMT
local envelope fields. The explicit variants in the valid fixture are synthetic
curated choices; provider availability flags do not prove them. Names, IDs and
dates are invented. Synthetic demonstrates the translator/resolver contract, not
TCGdex coverage, license approval for real third party data, or source health.
No P1a live API GET was performed and no P0.5 JSON was reconstructed. Test-only
forbidden-field sentinels are invented, including `.invalid` URL placeholders.

## P3a synthetic persistence fixtures — 2026-10-10

All `synthetic_persistence_*.json` files are authored local wrappers around the
invented P1a metadata above. No provider response, real product, commercial price,
image or personal data was acquired. Capture/update instants and batch UUIDs are
fixed authored test values. The synthetic label is a local producer assertion,
not cryptographic evidence of origin or permission to retain real source data.

| Fixture suffix | Purpose |
| --- | --- |
| `valid` | Seven P1a accepted records; explicit capture and distinct fixed provider update. Stable token `824d9220-d225-4d09-9964-6d33142408a7`. |
| `mixed` | One accepted, one candidate, one rejected; safe rejected summary only. |
| `candidates` | Two unresolved observations with exact context and no CMT ID. |
| `empty` | Valid empty batch still requires explicit capture and provenance. |
| `rejected` | Two malformed authored records; rejected sentinels must not persist. |
| `invalid` | Unsupported wrapper version; no batch is retained. |
| `later` | Same seven evidence values, new token `5c367329-bd86-4652-b0ac-8b68ed9a08a9` and capture one day later. |
| `conflict` | Reuses the valid token with a changed capture, requiring atomic replay conflict. |
| `missing_capture`, `contradictory_capture` | Required capture and wrapper/envelope disagreement even for an empty batch. |
| `offset` | Equivalent explicit UTC offsets normalize to the valid capture. |
| `documented`, `observed` | Invented negative provenance claims; both globally fail, even for empty input. |

The valid capture is `2026-10-10T09:00:00.000000Z`; later capture is
`2026-10-11T09:00:00.000000Z`. Offset representation is equivalent by instant.
Programmatic tests author generic synthetic sealed observations, malicious
dataclass constructions and hostile strings in memory without retaining raw
invalid payloads. Safe `RecordError` values are trusted producer rejection
assertions, not a retained quarantine or independently reconstructed raw input.
