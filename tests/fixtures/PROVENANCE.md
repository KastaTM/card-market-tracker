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
