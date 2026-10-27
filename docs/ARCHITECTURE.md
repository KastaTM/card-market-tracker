# Architecture

## P8c offline Watchlist signal outbox

Complete MANIFEST_V1 plus explicit original P5a/P5b paths and one wsig1_ select
a historical simulation. The additive P5b reader performs one accepted full deep
fold and reads the selected signal/from/to in one read transaction. P8c rechecks
the exact historical P5a revision and recomputes both results and the individual
fresh NO_MATCH-to-MATCH transition, then derives bounded evidence, intent and
pure deterministic plaintext.

A private receipt binds canonical content, exact issued instance, issuing Budget
and single use. Independent CMTY/schema1 revalidates semantics and commits alert
plus evidence under BEGIN IMMEDIATE. Equal alias/signal replays original bytes
and first time; conflicts never overwrite. Local verify reconstructs semantics;
origin recompute independently re-admits originals. Three fresh recovery folds
precede fsync/exclusive publication and safe owned-link compensation.

P5a/P5b remain read-only origins with immutable-source/trusted-directory assumptions,
no distributed transaction or authenticated producer. Root CLI defers Telegram
loading so P8c help/errors/commands import no Telegram and access no transport or
credentials. P8a/P8b admission stays unchanged. See
[ADR](adr/0014-offline-watchlist-signal-outbox.md),
[API](data-contracts/WATCHLIST_ALERT_OUTBOX_V1.md),
[storage](data-contracts/WATCHLIST_ALERT_OUTBOX_STORAGE_V1.md) and
[recovery](runbooks/WATCHLIST_ALERT_OUTBOX_RECOVERY.md).
These boundaries certify no gates; candidate evidence is recorded separately.

## P5b synthetic evaluation journal

Original full MANIFEST_V1 + exact P5a immutable revision + explicit synthetic
samples/as_of -> original identity admission -> normalized snapshot -> private
storage boundary -> BEGIN IMMEDIATE replay/head check -> recalculated per-rule
signals + evaluation + head committed atomically in independent CMTQ/schema1.
P5a retains preferences only; its evaluator, validation and store are unchanged.
There is no distributed origin/journal commit; immutable origin revisions are
an operational assumption. Local equality hashes are not origin authentication.

Four STRICT tables retain sequences, evaluations, signals and metadata. First
record is a signal-free baseline. Exact historical replay preserves head/time;
new appends require exact supplied previous, strictly advancing observed_at,
nondecreasing as_of and unused current sample ID. Independent rules emit only
fresh NO_MATCH-to-MATCH; uncertainty and stale predecessors break continuity.
Local verification reconstructs every P5a result, link, fold and head; explicit
recompute separately re-admits a selected evaluation against original P5a.
Bounded one-shot CLI and verified exclusive recovery use shared safety patterns.
No product sockets, outbox coupling or transport is introduced. See
[ADR0013](adr/0013-watchlist-synthetic-journal.md),
[freeze](phases/P5B_DESIGN_FREEZE.md) and
[journal API](data-contracts/WATCHLIST_JOURNAL_V1.md).

## P5a offline watchlist

Complete MANIFEST_V1 validation -> printing/sealed target plus exact canonical
parent closure -> bounded typed preferences -> separate CMTW/schema1 watchlist.
One stable wlt1_ key per existing CMT ID creates no product identity. Names,
dates, aliases and unrelated entities do not change the frozen identity;
canonical relation/language/variant changes conflict. Public Python values are
revalidated at admission. Existing catalog/capture/Discovery/journal/outbox/
delivery schemas, identities and algorithms remain unchanged.

BEGIN IMMEDIATE commits immutable revision, request replay and current pointer
together. Expected revision provides CAS. Complete normalized command equality
provides replay; old replay returns the original operation without reverting
newer state. Manifest input and watchlist transaction have no distributed commit.
Deep local verification, consistent backup and validated exclusive restore use
the existing trusted-directory path/inode/sidecar pattern. Prior stores have
separate recovery workflows and are never written by watchlist operations.

Frozen revision + validated manifest + ephemeral synthetic current/prior samples
+ explicit as_of -> pure deterministic rule evaluation. EUR integer cents,
inclusive freshness, per-rule reasons and OR produce MATCH/NO_MATCH/
INDETERMINATE or validated disabled SKIPPED. Evaluation has no SQLite, clock or
network dependency and persists no sample, price or result. Matches authorize no
event/transport. CLI operations are bounded explicit one-shot invocations; the
product network budget is zero. See [ADR0012](adr/0012-watchlist-offline-rules.md),
[API](data-contracts/WATCHLIST_V1.md),
[policy](data-contracts/WATCHLIST_SYNTHETIC_EVALUATION_V1.md) and
[recovery](runbooks/WATCHLIST_RECOVERY.md). P5a acceptance and gate evidence are
separate Orchestrator review concerns; sections below retain historical scopes.

## P8b manual Telegram delivery

`telegram_delivery.application` reuses original-capture outbox recomputation,
freezes the whole selected alert and comparison association, and issues a private
content-bound receipt. Ten commitments plus an immutable private route bind one
tdl1 delivery; provider/event uniqueness also prevents alternate aliases from
duplicating the same event. Earlier DBs, schemas, comparators and identities stay
unchanged and read-only.

CMTD/schema1 owns five STRICT tables: metadata, destinations, deliveries,
immutable attempt claims and immutable results. BEGIN IMMEDIATE commits claim
and unpredictable attempt ownership before sendMessage. No SQL transaction spans
network. Finish uses delivery/attempt/state CAS; local verification reconstructs
history. Opaque source commitments require origin recompute. Hashes and private
receipts do not authenticate privileged host code or replacement of all originals.

Stdlib official HTTPS, strict TLS/JSON/receipt checks, no proxy/redirect/retries,
and a supervised worker bound DNS/network time. Validated acceptance plus durable
local receipt means confirmed; ambiguity forbids resend. Only explicit later
valid429 retries are eligible, max3. Restore quarantines the whole ledger before
its final path can expose a usable snapshot. No P8b bypass. See
[ADR0011](adr/0011-telegram-manual-delivery-ledger.md) and
[storage](data-contracts/TELEGRAM_DELIVERY_STORAGE_V1.md).

## P8a offline alert outbox

Three explicit independent database paths and one cmp3 plus local destination
alias enter `alerts.application`. It retains one complete journal pair, reads
original verified captures through the existing reader, runs the unchanged v3
comparator and requires complete canonical equality plus comparison identity.
The same frozen content drives pure policy and renderer functions. A private
content-bound receipt admits only that content to the independent outbox writer.
The receipt is an application boundary, not a signature against privileged code.

`alerts` owns SQLite application CMTA/schema1 with ownership metadata, immutable
pending intentions and per-comparison evidence associations. alt1 hashes the
canonical destination/event preimage; it excludes window, renderer and clocks.
One event in two windows keeps one alert per destination and two full evidence
rows. BEGIN IMMEDIATE commits all additions atomically; replay preserves bytes
and initial preparation time, and intrinsic conflicts roll back everything.

Captures, journal and outbox have separate snapshots and backups. Origin checking
precedes the outbox commit and relies on contracted source immutability; no
distributed transaction is claimed. Local verify checks file consistency;
explicit association recompute checks it against original capture evidence.
Preview is read-only. Query pages are bounded keyset snapshots, with no shared
snapshot across successive pages. One cooperative deadline covers enqueue.

The package adds no dependency or transport. Earlier Discovery/capture APIs,
algorithms, schemas and source bytes are preserved. See
[ADR0010](adr/0010-offline-alert-outbox.md),
[API](data-contracts/ALERT_OUTBOX_V1.md),
[storage](data-contracts/ALERT_OUTBOX_STORAGE_V1.md) and
[recovery](runbooks/ALERT_OUTBOX_RECOVERY.md). Earlier sections describe their
own phase scope.

## P4c Discovery result and event journal

Strict v3 request + existing capture DB -> unchanged verified snapshot reader ->
unchanged pure comparator -> bounded canonical content-bound application receipt
-> independently validated journal writer -> atomic comparison + occurrences.
The capture snapshot and journal commit are separate transactions; immutable
verified capture evidence bridges them. No distributed commit is claimed.

The separate SQLite journal has its own application_id/owner/version1 and exactly
three tables. Captures retain schema2/five tables. PK(comparison_id,event_id)
preserves distinct window evidence sharing evt3. Replay compares complete bytes,
not just a digest, and preserves first_recorded_at. No overwrites or auto-init.

Local verify checks exact schema/JSON/digest/relational consistency; explicit
source recompute rereads captures and compares the full result. Privileged
coherent tampering is not authenticated by local verify. Keyset summary queries
are bounded and live across pages. Online backup copies a verified snapshot to a
new safe file and reopens it. The two DBs need separate backup/recovery workflows.

Application, journal storage and journal CLI are orchestration/IO modules under
discovery; multi_comparison and all existing pure algorithms remain independent
of SQLite/provider/IO. Standard-library dependencies only. No source acquisition,
delivery/outbox, scheduler, commercial metadata or API/frontend is introduced.
See [ADR0009](adr/0009-discovery-result-event-journal.md),
[journal API](data-contracts/DISCOVERY_JOURNAL_V1.md),
[storage](data-contracts/DISCOVERY_JOURNAL_STORAGE_V1.md) and
[recovery](runbooks/DISCOVERY_JOURNAL_RECOVERY.md).

## P1c multi-revision capture

Strict bundle-v2 admission -> code-controlled exact R0/R1 registry -> independent
retained envelope/resolution reconstruction -> schema2 five-table store. R0 uses
unchanged envelope1 and fingerprints; R1 uses envelope2/scope2. All readers,
verify and recovery reconstruct the correct version before returning evidence.

Strict v3 request -> one bounded ro/query_only BEGIN snapshot -> complete window
reconstruction and profile membership -> content-bound generic profile receipts
-> pure comparator -> cmp3/evt3 output retaining per-capture acquisition evidence.
Only the compatibility key normalizes reviewed acquisition differences. Replay
and comparison identities still bind full evidence. Provider logic remains in
admission/storage; Discovery imports neither provider nor SQLite. Separate
synthetic profile never grants real admission. V1/v2 semantics stay unchanged;
v2 explicitly rejects R1. See [ADR0008](adr/0008-multi-revision-metadata-capture.md),
[bundle v2](data-contracts/PINNED_REPOSITORY_BUNDLE_V2.md) and
[Discovery v3](data-contracts/DISCOVERY_V3.md).

## P4b scoped capture Discovery

Strict request v2 -> one schema2 read-only transaction -> complete retained
capture reconstruction and generic storage-issued DTOs -> pure unit selection/
comparison -> version2 JSON and correlated allowlisted logs. Storage owns pinned
verification. Discovery imports no provider/SQLite/current manifest and has no
I/O. Constructors grant no evidence authority. Original indexes and frozen
resolution survive selection. No schema or writer admission changes.

[ADR0007](adr/0007-scoped-capture-discovery.md),
[DISCOVERY_V2](data-contracts/DISCOVERY_V2.md) and the
[runbook](runbooks/SCOPED_CAPTURE_DISCOVERY.md) define scope/family/completeness/time
checks. Four units of the fixed real package are one acquisition; real baselines
prove no temporal transition. Positive evidence is synthetic/producer_declared.
Discovery v1 and cmp1/evt1 remain synthetic-only and unchanged. Earlier sections
below preserve their original phase scope.

## P1b pinned repository ingestion and capture

Engineering acquires four exact pinned files once under a shared eight-request
budget. A bounded non-executing structural TypeScript parser extracts only the
approved fields with byte spans. Original source bodies stay transient. The
distribution contains a reviewed minimal package, field ledger and full MIT
notice; runtime and CI use it offline.

`pinned_repository` owns source grammar, namespace, reviewed digest anchor and
translation to generic observations. `persistence.capture` independently
revalidates package and manifest, freezes resolution and scopes, and writes
through SQLite v2. The domain and Discovery import no source model. Curated
UUIDs and exact contextual bindings remain the only identity authority.

See [ADR0006](adr/0006-pinned-capture-storage.md),
[bundle v1](data-contracts/PINNED_REPOSITORY_BUNDLE_V1.md),
[capture v1](data-contracts/CAPTURE_SCOPE_V1.md) and
[storage v2](data-contracts/STORAGE_V2.md). Reads support exact v1/v2 inventories;
migration is explicit, transactional and preceded by a verified exclusive
backup. History and v1 fingerprints remain unchanged, with legacy scope marked
unverified. New initialization uses v2. PERSISTENCE_V1 remains synthetic-only;
Discovery explicitly rejects selected observed or mixed batches.

The reviewed digest proves equivalence to the locally reviewed minimum package,
not independent producer authenticity, current availability, total catalog
coverage or physical product truth. Acquisition/capture/local insertion clocks
remain distinct. The historical sections below describe their original scope.

## P0.5b source qualification — documentation only

[Field/capture proposal](sources/P0_5B_FIELD_USE_CAPTURE_POLICY.md) names the future
boundary `External Source -> Validated Source Model -> Normalized Ingestion ->
CMT Domain`. Validated source model describes existing adapter responsibility;
no new runtime class, source collector, schema or dependency is added. Per-field
rights precede retention, and producer provenance is not rights/authenticity.
P1a curated identity, P3a frozen history/replay and P4a selected-window semantics
remain unchanged. Persistence/Discovery remain synthetic-only. Independent
capture context for empty/multiple producers is a later-contract proposal;
TD-005 is not resolved. Existing ADR-0003–0005 suffice; no new adopted ADR.

## P4a offline temporal discovery

```text
strict request -> one P3a consistent read transaction -> generic snapshots
  -> revalidation -> pure window/reference comparison -> typed result
  -> JSON stdout + allowlisted correlated execution logging
```

`discovery` depends on generic P1a evidence/validators, without SQLite, adapters,
CLI, current manifest or resolver execution. Public constructors are revalidated.
`persistence.sqlite_repository.read_snapshots` reads selected metadata/complete
rows/identity closure in one mode=ro/query_only snapshot. It consumes no query
stdout, creates no missing DB and changes no schema or business data.

[ADR-0005](adr/0005-offline-temporal-discovery.md) and
[DISCOVERY_V1](data-contracts/DISCOVERY_V1.md) define exact contexts, explicit
historical union, bootstrap, bounds, frozen states and deterministic hashes.
Empty capture scope is explicitly caller/producer-attested and labeled
`request_attested_empty`; schema1 cannot prove it. Nonempty batches require every
row to match. Reference novelty implies neither launch/global/product novelty
nor disappearance/source health/delivery. No event tables or migration exist.

## P3a observation persistence

```text
strict local persistence wrapper + read-only manifest
  -> existing P1a adapter/normalized evidence
  -> persistence.input + application validation/UTC capture/resolution binding
  -> immutable PersistenceBatch
  -> SQLite repository (independent validation again)
  -> atomic identity projection + batch + accepted/candidate/rejection snapshots
CLI persist / observations / db operations -> JSON stdout + allowlisted stderr
```

`persistence.application` composes P1a without importing SQLite; P1a domain and
resolver remain unchanged and independent of persistence/adapters. The repository
depends inward on validated values and uses standard-library SQLite. The curated
manifest remains the canonical identity/binding authority. DB entity projections
preserve UUIDs and required parents; snapshots never promote candidates or reassign
old decisions after manifest edits. Storage never consumes P1a stdout as the sole
evidence source because that serialization omits normalized timestamps/metadata.

[ADR-0004](adr/0004-offline-observation-persistence.md) and
[input](data-contracts/PERSISTENCE_V1.md)/[storage](data-contracts/STORAGE_V1.md)
define initial schema1, DELETE/FULL, explicit transaction lifecycle, validated
producer tokens/replay context, safe summaries, bounded read/lock/backup and new
restore destinations. Separate commands make writes explicit; `catalog` remains
read-only. Fixtures are exclusively synthetic. There is no network collector,
market/retail schema, scheduler, promotion workflow, analytic query or server.
The sections below describe their original phase implementations.

## P1a catalog core

```text
local external JSON -> bounded strict JSON -> TCGdex shape validation
  -> generic Observation / RecordError -> explicit manifest resolver
  -> provider-independent Entity / candidate / categorized rejection
CLI -> structured stdout + allowlisted JSON stderr
```

The implemented domain in `catalog.models` contains set, card, printing and
sealed entities with opaque UUIDv4 identities and explicit relationships.
`catalog.ingestion` describes source evidence without making provider references
domain IDs. `catalog.manifest` validates curated identities and contextual
bindings; `catalog.resolver` uses those bindings conservatively without name
matching or mutation. `catalog.adapters.tcgdex` owns provider shapes. No domain
module imports the adapter. Shared validation bounds local untrusted JSON.
CLI orchestrates these components without network, persistence or export files.
See [ADR-0003](adr/0003-catalog-identity.md) and versioned catalog, ingestion and
manifest contracts. The P0 section below remains its historical implementation
description; its version/diagnose/configuration behavior is preserved.

## P0 implementation

P0 is a single installable Python 3.13 application using `src/` layout. `card_market_tracker.cli` owns argument parsing and the one-shot `diagnose` command. `config` loads and validates two local settings. `logging_json` emits allowlisted JSON fields. There are no runtime third-party dependencies, network calls, database, scheduler, server, or published ports.

```text
CLI --> configuration
  |          |
  +--> JSON logging
  +--> local work-directory probe
```

Dependencies point inward: future source adapters must translate untrusted provider data before domain use; provider identifiers cannot become domain identity. The intended boundary is `External Source -> Validation -> Normalized Ingestion -> Domain`. This is an architectural constraint, not an implemented pipeline. Do not add empty module hierarchies to imply features exist. SQLite remains a future initial persistence preference; no business schema is selected in P0.

Configuration is loaded from defaults, an explicitly named env file, then the process environment. The diagnostic verifies the configured directory with a temporary file and removes it automatically. It does not test source health. Failures are categorized as configuration (`2`) or local execution (`1`). Logs contain run correlation and safe event fields. See [logging v1](data-contracts/LOGGING_V1.md).

The container is a one-shot process with non-root UID 10001. CI runs quality/security gates and builds smoke-tested AMD64 and emulated ARM64 images. These checks cannot establish long-running Raspberry Pi behavior. [ADR-0001](adr/0001-modular-application-boundary.md) and [ADR-0002](adr/0002-multiarch-validation.md) record the adopted choices.

Future capabilities are phased in the [roadmap](ROADMAP.md). P1a adopts catalog
identity in ADR-0003. Commercial observation schema, scheduler, healthcheck and
service API remain decisions for their owning phases.
