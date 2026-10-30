# Narrow reviewed public-digest scanner exceptions

P5b adds exactly one detector/path/value match for the supplied identity fixture
`tests/fixtures/p5b_identity_vectors_v1.json`: its synthetic canonical parent
projection SHA256 (registry name `_P5B_IDENTITY`). Engineering independently
recalculated it using stdlib sorted/ASCII/compact JSON and hashlib.sha256 over the
fixture's canonical_identity. QA/REVIEWER recheck that identity on the final tree.
It is a public synthetic equality digest, not a credential. Wrong paths, modified
values, different detectors and unknown findings continue to fail; all tracked
files and detectors remain enabled. Owner Engineering Lead/SEC; revisit when
fixture projection, path, value or detector semantics change. The scanner-source
registry's exact literal alone carries a local annotation, as in prior phases.

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

## P8d exact public-identifier review (2026-10-30)

The initial complete tracked-file scan failed on28 candidates across8 paths.
Every candidate was Hex High Entropy String and was verified as a public Git
commit/tree, exact unedited handoff content hash or the two fixed164-byte/NUL
synthetic identity vectors. No credential candidate was dismissed.
The scanner keeps all files/detectors and requires the existing exact detector/
path/value fingerprint match. Wrong path, changed digest, different detector
and missing/unknown hashes remain FAIL. No entropy threshold, regex/path exclusion
or blanket Markdown/JSON exception is introduced. Frozen inputs are not edited.

Exact added paths and permitted public values:

- docs/evidence/P8D_GATE_A/baseline.json: authorized baseline/tree/ordered parents,
  preserved original checkout head/tree and three original handoff SHA256s.
- docs/evidence/P8D_GATE_B/design_probe.py: baseline/tree, three handoff hashes,
  and the two independent format-vector digests.
- docs/evidence/P8D_REVIEWER/INITIAL_PROBE_RESULT.json,
  MANIFEST_CORRECTIVE_PROBE_RESULT.json and MANIFEST_GAP_PROBE_RESULT.json:
  only accepted design commit50fcb55a and treed8d3eac.
- scripts/p8d_qa_probe.py, scripts/p8d_reviewer_probe.py and
  tests/test_watchlist_delivery_policy.py: only the two frozen identity digests.

Git values were verified with local cat-file against the authorized history.
Handoff hashes were recomputed from byte-identical archived originals. Vector
hashes were recomputed via stdlib literal preimages, independently of product
identity code. The source registry repeats only those exact values with the
same per-line annotations as prior phases; all other lines remain scanned.
Additional regressions require matching path/value/detector and reject changed
values/paths/types. Owner Engineering Lead/SEC; independent final REVIEWER must
recheck these additions. Revisit on any path/value/detector-semantic change.
