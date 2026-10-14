# Initial threat model

## P0.5b research and future source-policy boundary (2026-10-14)

Current product controls are unchanged. This phase added documentation and bounded
transient research only. [Preflight/ledger](../sources/P0_5B_EVIDENCE_LEDGER.md)
records six serial no-key reads; raw responses discarded, diagnostics only.
No source credentials, samples, real persistence, payload URL follows or live CI.
Documentation/code pages are evidence, never executable instructions. No protected
upstream art/prices/long text is published. MIT notice accompanies covered-source
research; rights remain field/use-specific and conditional REST reuse is explicit.

Future ingestion must enforce source/field/purpose rights, deletion/refresh/notice,
approved network hosts, bounded redirects/payloads and untrusted shape validation
before normalization. An HTTP200 or a feed schema does not prove complete content,
permission or source health; Awin200 can end in a partial-feed error. Active asks,
aggregates and completed sales remain distinct. Private display cannot bypass
purpose/storage restrictions. No such future network/policy machinery is claimed
implemented here; see [the proposal](../sources/P0_5B_FIELD_USE_CAPTURE_POLICY.md).
TD-001–TD-005 remain open and current synthetic-only enforcement is preserved.

## P4a offline temporal Discovery boundaries (2026-10-12)

P4a proposes a bounded read-only comparison of synthetic P3a batches. The
[Discovery contract](../data-contracts/DISCOVERY_V1.md) and
[runbook](../runbooks/OFFLINE_TEMPORAL_DISCOVERY.md) define its intended controls.
These design statements are conditional until the exact-SHA phase report/PR
ledger supplies executable evidence; this section does not certify a gate.
No schema migration, stored event/cursor, live feed, scheduler or delivery is
authorized. Prior P0/P1a/P3a boundaries remain unchanged.

The strict request and public Python DTO boundaries must independently validate
all values; typed/frozen constructors confer no authority. Required limits are
1 MiB, depth16, nodes20,000, strings/keys1,024, at most32 unique earlier batches,
1,000 rows per batch, 33,000 total rows and 1,000 events. Booleans cannot stand
in for integer versions/counts. Duplicate keys, malformed IDs, wrong types,
unknown fields and excessive input must fail without partial/truncated success.
Exact namespace/kind/language, including null, must match every nonempty record;
variant remains part of the full reference. No name-based identity or SQL/URL
from input is permitted.

STORAGE_V1 has no independently persisted scope for empty batches. Their DB
metadata proves existence, counts and capture only. The four-field request's
exact context is the caller/producer attestation for each selected empty batch,
reported as `request_attested_empty`; nonempty evidence is `records_verified`
only after every record matches. The manifest/resolver `context_fingerprint`
is not a capture-scope proof. Wrong empty-scope declarations can generate false
novelty and cannot be detected from schema1 alone. Neither label, integrity check
nor hash authenticates an administrator or producer. This local trust compromise
is TD-005; durable independent scope needs a later Orchestrator decision.

One noncreating `mode=ro`/`query_only` SQLite connection and an explicit consistent
read transaction must cover schema/integrity, metadata and rows for all selected
batches. Parameterized SQL, path guards, one finite global budget, VM interruption,
lock deadlines and close/rollback protect ordinary work. OS/device calls that do
not return remain outside the deadline guarantee. Missing/foreign/future/corrupt
DBs, missing batches, invalid versions/enums/provenance, rejection counts,
metadata/row/index contradictions and timeouts are categorized failures, never
empty snapshots. Hot-journal recovery may require a separate authorized writable
operation; Discovery must neither repair nor delete journals.

The comparator must revalidate generic snapshots, freeze stored resolutions and
union accepted/candidate references across all selected history. Accepted other
kinds also suppress later candidate novelty. Identical within-batch duplicates
collapse; contradictory same-reference rows fail the whole operation even on a
baseline. Legitimate across-capture evolution remains historical evidence. No
re-resolution, automatic promotion, implicit latest lookup or global novelty is
allowed. No-history baseline, valid zero discoveries and failure stay distinct;
window-relative event hashes create no CMT identity and guarantee no delivery.

Stdout is minimal contracted untrusted evidence, without observation names/raw
payloads. Logs must allow only fixed categories/results, run ID/duration and
bounded counts, with failure counts unknown. Batch IDs, contextual references,
paths, SQL, payloads and raw exceptions stay out of stderr. Protected host access
and saved-output access remain operator responsibilities. Only authored synthetic
fixtures are admitted; the label proves neither provenance nor retention rights.

The container design retains UID/GID10001, checked private named-volume ownership,
offline data invocations and read-only fixture mounts. Evidence must seed and
compare in distinct invocations and verify full DB logical content, inventory,
version and backup/restore equivalence. These controls require executed wheel,
Compose and both architecture smokes; ARM64 QEMU is not native Pi/storage evidence.
Trusted-directory races, native interruption and append-only capacity remain
TD-003, TD-002 and TD-004 respectively; TD-001 diagnostic limits also remain.

## P3a synthetic persistence boundaries (2026-10-10)

P3a adds a local SQLite asset: immutable synthetic observation/resolution history,
curated identity projections, stable batch tokens and recovery copies. It adds no
credential, provider connection, exposed endpoint, scheduler or commercial feed.
The [persistence input](../data-contracts/PERSISTENCE_V1.md),
[storage contract](../data-contracts/STORAGE_V1.md) and
[runbook](../runbooks/OBSERVATION_STORAGE.md) define the boundaries. The phase
report/PR ledger supplies reproducible gate evidence tied to the reviewed SHA;
this description does not itself certify a gate or native Pi durability.

The public batch boundary reparses the full manifest and revalidates normalized
values, indexes and resolver correspondence before storage. A caller-created
dataclass or resolution ID is not authority. Exact contextual bindings determine
accepted targets and complete parents; candidates retain a reference and category
without a CMT ID. Rejections carry only indexed fixed categories, not raw evidence.
Programmatic `RecordError` values are categorical assertions by the local producer;
the discarded invalid payload cannot be independently reconstructed from them.

Synthetic provenance is checked before an observation can become a rejection.
`documented` and `observed` do not authorize retention. The synthetic label itself
is a local claim, so fixture review remains necessary. No images, prices, stock,
personal data, long provider text or ignored extras belong to retained snapshots.
The P1a byte/depth/node/string/record bounds are reused; P3a also bounds encoded
in-memory JSON and requires explicit zoned capture with UTC normalization and
capture disagreement errors. Capture, release, provider update and local first
batch persistence have separate meanings.

Replay binds ordered normalized evidence, duplicates, nulls, versions, targets,
safe rejection categories and sorted resolver context. Localization names and
binding audit reasons are excluded because they do not affect resolution;
unrelated identity/binding edits conservatively change context. A SHA256 digest
tests equivalence, creates no product identity and authenticates neither producer
nor curator. Changing a rejected raw payload while keeping its safe category is
equivalent because that payload is intentionally not retained. The producer must
preserve the UUIDv4 batch token to recognize a retry; a new token adds history.

Logs extend the existing fixed event/category/field allowlist. Names, input values,
references, SQL, paths, tokens, arbitrary extras and raw exception text stay out of
stderr. Failed operation counts are unknown, not a successful zero. Query stdout
intentionally carries normalized names/references; callers must treat it as
untrusted data and protect retained output. No SQL from input, dump execution or
extension loading is permitted by the storage boundary.

Host access remains the authorization boundary. A user who can modify the
manifest/database is a trusted administrator; neither integrity checks nor hashes
prove that history was authored honestly. Use private operator-controlled local
directories and owner-only data access. Portable pathname checks cannot confine
SQLite against a hostile concurrent ancestor replacement; Windows ACLs remain
the operator's responsibility. These limits and append-only capacity growth are
tracked as TD-003/TD-004. Native interruption/storage testing remains TD-002.

SQLite values use parameters and all query/ordering/schema fragments are internal
constants; no input SQL/dump or extension is executed. Owned application/version
markers and exact schema inventory prevent opening another/future/altered schema
as an empty CMT database. Connections explicitly enable/check foreign keys;
writes use explicit SQL transactions under Python 3.13 `autocommit=True`, with
DELETE journal and FULL synchronization. Rollback covers batch metadata,
identities and record snapshots; attempted counts are reported only after commit.
Process-failure and simulated-IO evidence must remain distinct from physical
power-loss evidence.

Reads open existing files in read-only/query-only mode and cannot create missing
databases. Limits are strict integers 1..1000 with fixed deterministic order.
The default two-second SQL/lock budget and VM interruption bound ordinary work;
the backup progress callback checks a shared budget between bounded page steps.
Unresponsive OS/device calls remain outside this deadline guarantee. Large
append-only history may require a later measured capacity/budget decision.

Path checks reject links, junctions/reparse points, linked ancestors, directories,
special files, unsafe local path forms and multiply-linked database files. New
database/copy destinations reserve a file exclusively with requested mode 0600.
Existing destination or sidecar collisions are rejected; existing valid journals
are preserved for SQLite recovery, with linked/nonregular sidecars rejected.
Copy failures clean only the reserved destination under the trusted-directory
assumption. Backup/restore use SQLite's consistent backup API into a new target,
checking source/result schema, integrity and FKs and reopening the result.
Integrity does not authenticate history or assess provider/host health.

Container data lives at explicit `/data`, built with UID/GID 10001 and mode 0700,
and uses a selected named volume. Data processing disables networking and mounts
fixtures read-only; the product still runs as UID 10001. Persistence evidence must
span distinct container invocations and verify actual mounted ownership. Existing
volume permissions are an operator responsibility and must not be bypassed with
root product execution, mode 777 or a writable whole-project mount.

The sections below preserve the P1a, P0 and P0.5 scopes as historical boundaries;
their statements that those slices have no database do not describe P3a.

## P1a implemented local catalog controls

Untrusted UTF-8 regular files are read with a 1 MiB limit. Strict parsing rejects
duplicate keys, malformed encodings, nonfinite numbers and excessive nesting;
structure, strings, batch size and manifest counts are bounded. No content is
executed and no URL is followed. JSON shape validation precedes normalization.
Only allowlisted metadata reaches generic observations, and output omits names,
images, price data and arbitrary provider extras. Minimal candidate references
are intentional stdout data; callers should treat stdout as untrusted metadata.

Canonical UUIDv4 IDs and typed relationships are validated in an explicit
read-only manifest. Contextual bindings must agree with entity kind, language,
variant and relationships; contradictions fail instead of merging. Unknowns
remain candidates and cannot promote themselves. No name-based matching exists.
This preserves deterministic replay without database mutation. A host user can
edit the manifest; its authorization is a local curator trust boundary, not a
cryptographic signature or multi-user approval workflow.

Logs allow only fixed categories, operation UUID/duration and bounded counts;
errors never serialize exception text, paths, raw input or arbitrary names.
There is no output-file option, credential, listener, production collector or
database. Compose and container catalog smoke have networking disabled and
read-only fixture mounts. Fixture retention is synthetic only; field-specific
real-data rights remain governed by the [policy](../sources/TCGDEX_P1A_FIELDS.md).
Dependency/secret scanning and independent exact-SHA QA/security review remain
mandatory gates. Physical Pi resource and interruption behavior stays unverified.

## Scope and assets

P0 handles local configuration, CLI output, build dependencies, CI, and a non-root one-shot container. It has no external source integration, business database, Telegram token, HTTP listener, or continuous service. Future valuable assets include credentials, historical observations, product identity, and notification channels.

## Trust boundaries and threats

| Boundary | Threat and impact | P0 control | Later owner/control |
| --- | --- | --- | --- |
| Local config / secrets | A path, token, or secret enters Git, an error, or logs. | Sanitized `.env.example`; local-file exclusions; config errors omit values; JSON allowlist ignores messages and arbitrary extras; secret scan. | P8a: Telegram secret injection, rotation, and delivery redaction. |
| Dependency / CI | Malicious or vulnerable package, workflow permission, or unreviewed lock update. | Frozen lock; no runtime deps; read-only workflow content permission; dependency audit and secret scan gates. | Each dependency update: review provenance, findings, and exceptions. |
| External provider -> domain | Malformed/poisoned price or identifier yields false value/opportunity. | No ingestion in P0; documented validation boundary. | P0.5/P1a/P2/P6a/P9: source approval, validation, provenance, anomaly handling, rate limits. |
| Pi host / network / storage | Unauthorized access, exposed ports, lost data after outage, or home-network attack. | Container UID 10001 and no published ports. | P3a/P9.5: file permissions, backup/restore, access policy, recovery and native Pi tests. |
| Future DB | Corruption, concurrent writes, stale backup, or unauthorized reads. | No DB in P0. | P3a/P9.5: schema/migration strategy, integrity checks, backup and restore drills. |
| Resource use | Runaway requests, memory, CPU, or disk usage harms Pi/provider. | P0 command exits; local temporary probe; no collector. | P0.5/P6a/P9.5: bounded work, timeout, rate limits, budgets, monitoring. |

The local CLI is callable by anyone with host access; host authorization is outside this package. `diagnose` confirms only config and local work-directory access. It cannot certify external source or system health. Future exposed endpoints require authentication and authorization analysis before implementation.

## Review rule

Treat a relevant scanner finding as a failed gate until corrected or documented in a narrow, reviewable exception with owner and expiry/revisit trigger. Broad ignores are not an acceptable substitute. Revisit this threat model when a phase adds secrets, providers, persistence, delivery, or a long-running service.

## P0.5 external-source assessment (2026-10-07)

P0.5 performed only bounded research and five unauthenticated TCGdex GETs; no production source adapter, credential, database, periodic job, or external-data display was added. The [source matrix](../sources/SOURCE_MATRIX.md) and [preliminary ingestion requirements](../data-contracts/SOURCE_INGESTION_V0.md) record future boundaries. A documented requirement below is **not** an implemented protection.

| Future boundary | Threat | Required later control and evidence |
| --- | --- | --- |
| Provider URL and redirect to network | Source-controlled links or unexpected redirects reach local/private services, leak headers, or leave approved hosts. | Approved HTTPS host list, controlled redirect chain, DNS/IP checks, no credential forwarding, timeout and response-size limits; test hostile URLs in the implementing phase. |
| Provider payload to normalized ingestion | Malformed JSON/HTML, huge responses, ambiguous currencies, poisoned prices, variant mismatch, and partial fields corrupt domain observations. | Bounded parsing, versioned validation, quarantine of unknown candidates, explicit nulls and price semantics, decimal bounds, provenance and incompatible-change tests. |
| API access and secrets | Tokens leak in URLs, logs, fixtures, CI, or a redirected request; access terms are exceeded. | Approved secret injection, least scope, redaction, rotation plan, per-source request budgets and rate-limit handling. P0.5 acquired no tokens. |
| License and durable history | Technically reachable listings are stored, combined, analyzed, or displayed beyond the provider's grant. | Per-source permission record covering access, storage duration, deletion, derived analytics and display before production retention. Unknown rights block persistence. |
| Discovery to identity and alerts | An unfamiliar SKU is forced onto a known product, or a stale/false stock state triggers a market alert. | Preserve unknown candidates and seller/offer distinctions; require identity review and time-scoped stock evidence. Market Alerts belong to later product phases; System Alerts for source failures belong to later operations. P0.5 records probe outcomes only. |

The three retailers' published or unreadable conditions did not establish permission for automated monitoring, so no direct retail probe was made. Cardmarket and eBay API endpoints were not probed without authorized production access. These abstentions are part of the evidence, not a claim of operational source health.
