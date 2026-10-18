# Narrow reviewed public-digest scanner exceptions

P1c extends the same exact detector/path/value mechanism to four additional paths:
`docs/sources/P1C_REQUEST_LEDGER.json` (R1 revision + original blob/content digests),
`src/card_market_tracker/pinned_repository/approved_bundle_v2.json` and
`tests/fixtures/pinned_repository_bundle_v2.json` (same plus projection), and
`src/card_market_tracker/pinned_repository/bundle_v2.py` (R1 revision + exact
R1 package anchor). These public locks were independently recalculated by QA and
REVIEWER from the original approved bytes before freeze; see the
[P1c field ledger](../sources/P1C_FIELD_LEDGER.md). Unknown replacements, wrong
paths or detectors still fail. Added regression tests cover every new path.
Owner remains Engineering Lead/SEC; revisit upon any path/value/detector change.

Owner: Engineering Lead / SEC, P1b 2026-10-14. Independent REVIEWER checks the
exception implementation on the final candidate. Revisit when any allowed path,
source revision, artifact/package digest or scanner detector semantics changes.

P1b's fixed public Git revision/blob SHA1 and original-content/package/projection
SHA256 strings triggered Hex High Entropy String findings. These values are
public immutable integrity identifiers, independently calculated from approved
bytes and published in the contract/field ledger, not credentials. The scanner
still scans exactly all tracked files and retains all detectors. It dismisses a
candidate only when repository-relative path, exact detector type and
detect-secrets SHA1-of-value fingerprint match an explicitly reviewed public
value. New/replaced values, another path or detector remain FAIL. No regex,
glob/path exclusion or blanket high-entropy suppression is used.

| Exact path | Only reviewed public values |
| --- | --- |
| docs/sources/P1B_REQUEST_LEDGER.json | Fixed source revision and four original blob/content digests |
| src/card_market_tracker/pinned_repository/approved_bundle_v1.json | Same original identifiers plus exact projection digest |
| tests/fixtures/pinned_repository_bundle_v1.json | Same reviewed minimum package identifiers |
| src/card_market_tracker/pinned_repository/bundle.py | Fixed source revision and whole-package digest anchor |
| tests/test_pinned_repository.py | Exact MIT file content SHA256 |

The scanner's exception registry repeats those exact reviewed public values with
local per-line `pragma: allowlist secret` annotations. Other scanner-source lines
are still scanned. Values are listed in [field ledger](../sources/P1B_FIELD_LEDGER.md)
and [contract](../phases/P1B_PINNED_METADATA_INGESTION_CONTRACT.md), with full
rights/provenance evidence. Regression tests require same-value/wrong-path,
wrong detector, unknown/missing hash and replaced-value candidates to fail;
scanner output never prints candidate values. A real secret finding remains a
failed gate and must be corrected; this exception does not permit credentials.
