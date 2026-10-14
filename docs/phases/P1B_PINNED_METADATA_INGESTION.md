# PHASE COMPLETION REPORT — P1b Pinned Metadata Ingestion & Capture Scope

Phase: P1b. Proposed status at committed snapshot: **FAIL pending final evidence**.
This report describes delivered implementation and reproducible recipes. The
external PR delivery ledger records actual final SHA/tree/base, CI, independent
reviews and PASS/FAIL results, avoiding a circular commit with its own identity.
Only that completed evidence can support READY_FOR_ORCHESTRATOR_REVIEW.
No merge, acceptance or closure is authorized here.

Branch: `feat/p1b-pinned-metadata-ingestion`.
Baseline: `acca10e406dac8809edc289c3077a6ec8785a622`.
Baseline tree: `26011d0375f3716a7fffb31956665eb97567a0df`.
PR/head/tree/commits: actual identities in external delivery ledger.

## MODEL PROFILE USED and ownership

Root `/root`: GPT-6-based Codex per runtime; precise serving variant/client
reasoning selector unobservable. Contract recommends GPT-6.1 Sol/Medium for
mechanics and High for integrity; no unobserved model switch is claimed.
`source_author` (INTEGRATIONS/DATA), `storage_author` (ARQ/DB-OWNER),
`qa_final` and `reviewer_final` explicitly requested `gpt-6.1-sol/high` and
spawn calls accepted that available configuration. Acceptance of configuration
is observable, independent serving-backend verification is not. Phase Lead
client model is unobserved; no Astra escalation. Lead performs SEC/SRE analysis;
independent reviewer checks security/architecture without authorship.

[Ownership](P1B_OWNERSHIP.md) fixed disjoint paths before parallel edits. Lead
owns Git/requests/CLI/logging/harness/CI/shared docs. Source author owns bounded
parser, fixed package and projection. Storage author owns schema/migration/capture
admission and recovery. QA and REVIEWER are separate nonauthors; exact detached
SHA reviews and findings are external. Preliminary working-tree QA source
contrast cannot alone satisfy final review gates. QA's giant-integer uncategorized
serialization finding was fixed with an author regression and independently rechecked.

## Objectives and implementation

Implemented four offline ES/EN observations from the exact set/card artifacts,
source namespace `tcgdex_repository`, strict non-executable TS extraction with
UTF-8 field offsets, exact Git blob SHA1/content SHA256 verification, minimum
licensed package and complete MIT notice. The distributed canonical package
anchor is `3b43e1a78c117ef1ecb5cf200a4b2fc7e57af8fd29e3fcf29b06f4291ae58085`.
The projection digest is
`53100248a987378fb3ca2273b7ec219747b876b515f57087faf6becdd0caa479`.
Policy and extractor versions, artifact locks and immutable acquisition/capture
times participate in reviewed admission and replay. No runtime HTTP dependency.

Sets require explicit curated bindings. The shipped synthetic manifest has none
for this namespace: all four remain candidates. Card number stays textual `136`,
contextual external ID is explicitly `swsh3-136`, finish stays unknown and card
candidates are `unknown_variant`. No name matching, CMT ID generation, manifest
mutation or promotion occurs. Explicit ES/EN curated-set tests preserve supplied UUIDs.

Public storage independently reconstructs reviewed package, normalized evidence,
manifest resolution and immutable scope; manually forged objects do not bypass
admission. PERSISTENCE_V1 is unchanged and remains synthetic-only. Dedicated
synthetic scoped tests cover complete empty, partial, failed and rejected source
semantics without inventing an empty real capture. Acquisition/import remain separate.

## Architecture, contracts and DB

[ADR0006](../adr/0006-pinned-capture-storage.md) defines the narrow real route,
schema2 and explicit migration. New contracts:
[PINNED_REPOSITORY_BUNDLE_V1](../data-contracts/PINNED_REPOSITORY_BUNDLE_V1.md),
[CAPTURE_SCOPE_V1](../data-contracts/CAPTURE_SCOPE_V1.md),
[STORAGE_V2](../data-contracts/STORAGE_V2.md). Historical v1 contracts remain intact.

New DB initialization uses v2; existing v1 init/read/verify never auto-upgrades.
Explicit migration validates exact owned schema/integrity, holds an exclusive
transaction, reserves/fsyncs/verifies original backup before transactional DDL,
preserves entities/batches/records/fingerprints/times and marks legacy scope
unverified. Rollback tests include injected DDL/version/commit faults and process
exit, preserving v1 and backup. General backup/restore uses bounded SQLite backup
API, exclusive destinations, verification and reopen. No downgrade deletes v2 history.

Capture+records read in one checked bounded snapshot; fixed source metadata,
per-unit paths/selectors/languages/counts, frozen manifest context, outcome and
policy evidence are immutable. Replay includes all context; a same-token change
conflicts with zero writes. New v2 integrity checks validate capture relationships
and replay reconstruction. Discovery rejects selected observed/mixed batches explicitly.

## Rights, security, observability and debt

[Field ledger](../sources/P1B_FIELD_LEDGER.md) and
[request ledger](../sources/P1B_REQUEST_LEDGER.json) retain exact permission,
byte offsets/digests/transforms and actual acquisition observations. Four serial
HTTP200 requests, zero redirects/retries; **4/8** shared budget consumed. QA reuses
fixed bytes with independent digests/structural projection/license checks, zero
extra requests. Original bodies are transient and excluded from repository,
fixtures, logs and DB. Full MIT notice is shipped. No additional mark/art or
third-party rights are inferred. No source or data network requests enter CI.

Threat model adds provenance/policy spoofing, false completeness, interrupted
migration and immutable scope corruption. Bounded bytes/depth/nodes/strings,
fixed errors, exact inventory/FK/count checks, trusted paths and deadlines remain.
Logs use existing allowlisted event with fixed new operations/categories,
run ID/duration/confirmed counters; no names/paths/URLs/SQL/tokens/raw exceptions.
Explicit query stdout is bounded untrusted metadata.

TD-001–TD-005 remain open, with TD-005 improved for new reviewed local captures
only. Legacy/independent producer authentication, total catalog coverage, source
health, capacity automation, hostile administrator path races and physical Pi
durability remain unqualified. P2/P6a/retail Discovery remain BLOCKED; REST,
market, retail, real temporal comparison, scheduler, frontend and delivery excluded.

## Tests and gates

Reproduce frozen install/unchanged lock; Ruff format/check; mypy src; full
coverage pytest plus coverage JSON threshold check; sdist/wheel build and
outside-tree installed smokes; frozen pip-audit export and secret scan. New
`scripts/pinned_repository_smoke.py` extends all earlier harnesses in wheel,
Compose and both architecture jobs with separate process import/reopen/replay/
conflict/migration/backup/restore, readonly fixtures, network disabled, UID10001.
CI preserves four jobs: quality, Compose, AMD64 and QEMU ARM64.
Version regression assertions advance unsupported schema2→3; they retain their
original malformed/future-schema invariant. No coverage reduction or new skip.

| Mandatory gate | Committed report snapshot |
| --- | --- |
| Source/policy/license independent contrast | FAIL pending exact final review |
| Frozen install/lock, Ruff/mypy | FAIL pending exact final execution |
| Unit/contract/integration/migration/regression, coverage85/80 | FAIL pending exact final execution |
| Build and outside-tree wheel smokes | FAIL pending exact final execution |
| Audit/secret scan, SEC/SRE/ARQ/DB review | FAIL pending exact final execution/review |
| Compose/AMD64/ARM64 QEMU, four CI job bodies | FAIL pending exact final execution/CI |
| Distinct exact-SHA QA and REVIEWER | FAIL pending exact final review |

The external ledger supplies actual final evidence for every gate and AC below.
Unexecuted mandatory criteria are FAIL, never N/A or historical PASS.

## Acceptance criteria traceability

| ID | Evidence locations and required final verification |
| --- | --- |
| AC-I01 | Archived contract/brief/ownership, roadmap; Git remote/fetch/base/tree/parents/worktrees |
| AC-I02 | Field ledger, packaged complete MIT notice and minimum fixture; independent license/allowlist review |
| AC-I03 | Request ledger, structural extractor, source tests and independent QA byte/field-span contrast |
| AC-I04 | Source tests: four exact projections, textual numbers, ES/EN, no fallback/finish |
| AC-I05 | Source/manifest resolver tests: curator aliases, unknown candidates, immutable UUIDs/conflicts |
| AC-I06 | Source/capture forged-object/tamper tests; existing persistence synthetic-only regressions |
| AC-I07 | capture scope contract/API/tests and process harness; immutable clocks/evidence/replay |
| AC-I08 | Synthetic scope complete-empty/partial/failed/rejected tests; missing translations/artifacts rejected |
| AC-I09 | test_migration_capture.py: exact v1 history/backup/replay, faults/process exit/legacy context |
| AC-I10 | test_capture_storage.py and process harness: atomic writes, replay/conflict/reopen |
| AC-I11 | Capture integrity/bounded snapshot tests and v1/v2 verify/backup/restore regressions |
| AC-I12 | Full previous suites/harnesses and observed/mixed Discovery refusal tests |
| AC-I13 | test_bundle_cli.py, logging and input tests; fixed categories/no raw payload/errors |
| AC-I14 | Installed wheel/Compose/architecture harness bodies, UID10001/offline/readonly/process checks |
| AC-I15 | ADR0006/new contracts/source policy/threat/debt/architecture/runbook and reviewer consistency audit |
| AC-I16 | Exact final frozen tests/CI/job bodies and distinct QA/REVIEWER ledger with no blocking findings |

## Recommendation

Submit this bounded candidate for Phase Lead review only after the external
ledger establishes every mandatory final PASS and independent exact-SHA reviews.
Otherwise report blockers and remaining actions accurately. Engineering does
not accept/close phases or merge; Orchestrator alone decides those actions.
