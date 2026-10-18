# PHASE COMPLETION REPORT ? P1c

Phase: Multi-Revision Metadata Capture. Implementation evidence map dated
2026-10-18, Europe/Madrid. Proposed readiness is determined by the final external
PR ledger after immutable candidate reviews and CI, not by this map alone.
No merge, phase acceptance/closure or successor phase is authorized here.

Branch: `feat/p1c-multi-revision-metadata-capture`; repository
[KastaTM/card-market-tracker](https://github.com/KastaTM/card-market-tracker).
Base `112916382ce02486ca38eb14487220dbb24196e7`, tree
`c79edde3f13c5983d11505f5917f91559265b506`. Final PR/head/tree, four CI jobs/full
logs and independent exact-candidate reviews are published in the PR conversation
rather than creating a circular SHA-only evidence commit. The branch's PR is the
review boundary; history below preserves implementation-time observations.

## Model profile and specialists

[Ownership/model/preflight](P1C_OWNERSHIP.md) records requested versus observable
configuration. Lead requested GPT-6.1 Sol/Medium (High for integrity); root system
identifies Codex based on GPT-6, without independently observable backend or active
reasoning. Three distinct specialists were spawned with accepted tool configuration
gpt-6.1-sol/high; that is not backend authentication. Root authored discovery,
source/CLI/tests/harness/integration. ARQ/DB-OWNER authored registry/persistence
and ADR/contracts/runbook. Independent QA and REVIEWER authored neither production
nor repository tests and are distinct from both authors and each other. REVIEWER
also covers SEC/SRE/architecture/docs. No model escalation was used.

## Delivered behavior and architecture

R0 is retained byte/semantically unchanged. R1 adds an independently contrasted
minimum package from exactly the second authorized revision, with unchanged
projection. Exact whole-package registry in `bundle_v2.py` admits only R0/R1;
caller hashes/registries, observed assertions and manufactured Python values
confer no admission. Entry points `bundle-v2 verify/import` and
`persist_bundle_v2` are explicit. Existing `bundle` v1 remains R0-only.

[ADR0008](../adr/0008-multi-revision-metadata-capture.md) separates acquisition
identity, replay equivalence and semantic compatibility. [Bundle v2](../data-contracts/PINNED_REPOSITORY_BUNDLE_V2.md)
and [Discovery v3](../data-contracts/DISCOVERY_V3.md) define exact APIs, canonical
cmp3/evt3 identities, profiles, outputs/bounds/errors and compatibility. Generic
pure comparison imports neither provider nor SQLite. Stored profile receipts
bind complete reconstructed package evidence; ordinary objects cannot manufacture
membership. Public v3 output retains original revisions/digests/artifact locks/
acquisition times while compatibility normalizes only approved differences.

DB stays schema2 and exactly five tables, with no new migration. R0 envelope1 and
historical fingerprints are preserved; R1 uses envelope2/scope2. Query, verify,
replay and backup/restore rebuild the versioned package, manifest, parent closure,
resolution and snapshot before returning. Same-token identical replay writes
nothing; revision/context conflict fails atomically. New capture time never comes
from import time. PERSISTENCE_V1 stays synthetic-only, and Discovery v1/v2 keep
prior behavior/hashes; v2 explicitly rejects R1, including baseline.

V3 reads the full selected window through one mode=ro/query_only connection and
explicit BEGIN. Every envelope/unit/row, including unselected units, is checked.
Exact profiles distinguish the reviewed real pair from explicit synthetic tests;
unknown/mixed/partial/legacy/forged scope fails. Budgets remain 32 histories,
33 batches, 33000 rows, 1000 events, existing JSON limits, 2s default/5s max.
Cronology is strictly original captured_at; reverse/equal-time history fails.

## Source, rights and immutable clocks

[Request ledger](../sources/P1C_REQUEST_LEDGER.json) records **4 of 12** allowed
requests: four sequential content reads, no redirect/retry or Git metadata call.
QA/REVIEWER independently computed locks/fields/projection/MIT from engineering
originals, without another fetch, before freeze. [Field ledger](../sources/P1C_FIELD_LEDGER.md)
records eight UTF8 spans, transformations, per-field rights and original disposal.
Originals were deleted after both contrasts, verified by REVIEWER. No excluded
TS/README bodies are retained in Git/DB/fixtures/logs.

R0 revision `4199850a6af49665db0080fa2bb9ef751750a406`, bundle
`3b43e1a78c117ef1ecb5cf200a4b2fc7e57af8fd29e3fcf29b06f4291ae58085`, capture
`2026-10-14T17:53:09.118954Z`. R1 revision
`af57972e8f784c2507ab9e573c99bf02ae2e5e42`, bundle
`e3b6ec38358a8fc089e65a365fe2f5566459df441e67c3e8ad51b3b5352b50c0`, capture
`2026-10-18T12:18:50.379756Z`. Same projection hash
`53100248a987378fb3ca2273b7ec219747b876b515f57087faf6becdd0caa479`.
Times are engineering producer declarations backed by read ledger, not provider
signatures or commit dates. Complete MIT notice is preserved; no separate
artwork/brand/third-party rights or REST license is inferred.

## Tests and evidence recipes

Author suites `test_multi_revision_storage.py`, `test_multi_revision_discovery.py`
and `test_multi_revision_cli.py` cover real eight scenarios (four units ? empty/
coherent-set manifests), synthetic positives/union/metadata/duplicates, admission
forgeries, atomicity, migrated history, recovery, chronology, CLI/log redaction.
Existing tests cover unchanged v1/v2 goldens, shared snapshot reader concurrency,
locks, deadlines, lexical/byte limits and schema constraints. Independent QA
also derives its own external adversaries, including interleaved writer/window
consistency and unselected-unit corruption. Final reports identify their exact
probe scripts/results separately from author tests.

Pre-freeze observations: 1040 passed/1 inherited skip before the final CLI and
scanner regression additions; coverage 94.57% lines/90.47% branches. A subsequent
10-test CLI suite and seven scanner exception tests passed. These observations
are not a substitute for final exact-candidate execution. Frozen dependency
installs, strict mypy, Ruff, sdist/wheel build and dependency audit passed locally.
Scanner initially detected new public hashes; narrow detector/path/value exceptions
were reviewed and tested, preserving all detectors and unknown-finding failures.

The sixth [harness](../../scripts/multi_revision_metadata_smoke.py) preserves all
five earlier smokes. It exercises separate offline processes for import/read/
compare/replay/equal/reverse-time rejection/copy/reopen; fixtures readonly,
UID10001 and data mode0700 in containers. Real four-unit output is no_discoveries
with zero events; positive novelty is explicitly synthetic. New harness passed
installed wheel, AMD64 and Compose during development; final ARM64/full six-harness
results and immutable job logs belong in the external ledger. Explicit existing
5s copy budget is used in harnesses; runtime/reader defaults stay2s. QEMU is not
physical Raspberry Pi or power-loss validation.

| Mandatory gate | Reproducible command/evidence required on frozen candidate |
| --- | --- |
| Frozen dependency install/lock | `uv sync --frozen --no-install-project`; `uv sync --frozen --no-build-isolation`; unchanged uv.lock |
| Format/lint/types | `uv run --frozen ruff format --check .`; `uv run --frozen ruff check .`; `uv run --frozen mypy src` (strict config) |
| Full suite/coverage85/80 | `uv run --frozen coverage run -m pytest`; `coverage json`; `python scripts/check_coverage.py coverage.json` under uv run --frozen |
| Dependency audit | `uv export --frozen --all-groups --no-emit-project -o requirements-audit.txt`; `uv run --frozen pip-audit -r requirements-audit.txt` |
| Secret scan | `uv run --frozen python scripts/check_secret_scan.py` including all tracked new files; narrow reviewed public IDs only |
| sdist/wheel/outside checkout | `uv build --no-build-isolation`; `sh scripts/wheel_smoke.sh` or equivalent Windows external venv with explicit cmt.exe |
| Compose | CI compose job, all six harnesses with readonly fixtures/network none/private volume |
| AMD64 | `sh scripts/container_smoke.sh IMAGE linux/amd64`, all six harnesses |
| ARM64/QEMU | same linux/arm64, all six harnesses; emulation explicitly labeled |
| Independent QA/REVIEWER | Distinct nonauthors, isolated exact-SHA worktrees, full candidate and all four complete CI job logs |
| Quality/CI | Exact final head/base/tree and four successful job bodies in external PR ledger |

An unexecuted mandatory gate is FAIL/BLOCKED, never inferred PASS. Readiness is
conditional on final external ledger entries completing every row above. A failed
candidate must be corrected and affected reviews/gates repeated; no threshold
reductions, removed tests or convenience skips are authorized.

## Acceptance criteria evidence map

| ID | Required evidence (final PASS/FAIL recorded in external ledger) |
| --- | --- |
| AC-M01 | Archived contract/brief, ownership preflight and roadmap attributed Orchestrator P4b closure/P1c opening |
| AC-M02 | Request ledger4/12, four independently verified byte/blob locks and acquisition clocks; field rights ledger |
| AC-M03 | Equal four-record projection, full MIT, eight spans and confirmed original disposal |
| AC-M04 | Exact registry, unchanged R0 package, tamper/third revision/forgery pre-write tests |
| AC-M05 | Explicit v2 entrypoint, old bundle/PERSISTENCE_V1 guards and curated identity regressions |
| AC-M06 | Five-table schema2, strict reconstructed query/verify/rows/envelopes and migrated-history tests |
| AC-M07 | Replay/conflicts/atomic rollback/reopen/recovery tests and sixth process harness |
| AC-M08 | Registry membership/profile receipts plus mixed family/scope/unknown profile/forgery negatives |
| AC-M09 | One ro snapshot, complete unselected-unit integrity, concurrency/deadline tests and independent QA probes |
| AC-M10 | Reverse/equal-time reimport rejection, acquisition/capture immutable in query/replay |
| AC-M11 | Eight real cases/four units, no_discoveries/zero events with both revisions/digests/times visible |
| AC-M12 | Synthetic positives/union/alias/metadata/duplicate contradictions, cmp3/evt3 determinism, old golden regressions |
| AC-M13 | CLI version/errors/redaction/no-network and preserved JSON/deadline/volume bounds |
| AC-M14 | Outside-tree wheel plus Compose/AMD64/QEMU ARM64 six harnesses with UID10001/recovery |
| AC-M15 | ADR0008/versioned contracts/field rights/runbook/architecture/threat/roadmap/debt/tests/gates coherent |
| AC-M16 | All final exact-SHA gates, full four CI logs, distinct independent QA and REVIEWER |

## Threat model, observability, debt and limitations

[Threat model](../threat-model/THREAT_MODEL.md) addresses registry spoofing,
poisoned third packages, forged evidence/time/profile, provenance loss while
normalizing, snapshot mixing, hidden unselected corruption, false replay novelty,
resource/FS/disk/recovery and version serialization. Safe structured logging adds
fixed v3 event/operations with run ID/duration/categories/bounded counts. It never
logs source bodies/names/paths/tokens/input/SQL/raw exception text. Errors have
unknown counts and no events; zero discoveries is not source health.

TD-001?TD-005 remain open with existing owners/exit conditions. This bounded pair
adds no source authenticity, full coverage, quota/retention policy, physical Pi
power-loss qualification or future commercial feature. No new canonical identity,
scheduler, REST, frontend, price/stock/retail/alert, schema3 or event store exists.
P2/P6a/retail Discovery stay BLOCKED.

Local shell initially failed sandbox setup before launch; normal authorized
operations used reviewed escalation. Docker daemon initially was unavailable,
then started hidden. First Windows outside-wheel harness invocation lacked its
required explicit cmt.exe path and was corrected; no product code/threshold was
changed for that environment issue. Pre-freeze QA/REVIEWER caught omitted public
acquisition evidence; dedicated v3 serialization fixed it while v2 stayed intact.

Recommendation: Phase Lead/Orchestrator evaluate only the final immutable PR
candidate with the external gate/AC/review ledger. No acceptance or merge is
implied by this implementation map or historical P4b evidence.
