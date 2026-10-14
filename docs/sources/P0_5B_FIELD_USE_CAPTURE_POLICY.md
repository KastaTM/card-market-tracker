# P0.5b field-use and capture policy proposal

Date: 2026-10-14. Status: **documentary proposal for Phase Lead/Orchestrator**,
not a new runtime model, permission grant, adopted ADR or storage contract.
ARQ/DB-OWNER reviewed existing ADR-0003–0005; they already establish the required
boundaries. No new adopted architectural decision is justified by this research.

`External Source → Validated Source Model → Normalized Ingestion → CMT Domain`

Source content is untrusted. The validated source model names adapter-owned
shape/field/bounds/context/completeness validation. Existing adapter code already
has that responsibility; no new class or dependency is introduced. Translate
only permitted supported fields into generic ingestion evidence. The curated
manifest remains identity authority. Unknown references stay candidates;
contradictory immutable evidence rejects instead of forcing a match. Canonical
UUIDs never come from source IDs/names/URLs/SKUs or hashes.

## Per-field permission record and uses

For each future source-field-use, record exact field/format, origin/upstream,
artifact+revision/deployment uncertainty, localized selector, transformation,
primary rights document/section/date, action, retention/deletion/refresh rules,
attribution/complete notice, evidence class and unresolved human action. A
schema/example does not establish populated data or ownership. No implied grant
from absent prohibitions, HTTP success, private display or paid access.

Evaluate separately: transient consultation, minimal sample retention, future
CMT storage, real-value fixture/document publication and comparison/derived
history. Each is YES/NO/CONDITIONAL; route verdict additionally separates ACCESS,
RETENTION, SEMANTICS, COVERAGE, OPERATIONAL_LIMITS. A conditional decision grants
no present use. Private display, redistribution and commercial exploitation are
different purposes. Do not aggregate dimension scores into permission.

Evidence classes `documented/observed/inferred/unknown` describe research claims.
Runtime `synthetic/documented/observed` provenance is a producer assertion, not
rights, authenticity or completeness. Current persistence/Discovery remain
synthetic-only; no observed record is relabeled synthetic. All real bodies from
this investigation were discarded, no real fixture added.

## Times and scope

| Concept | Future evidence meaning / existing limit |
| --- | --- |
| `captured_at` | Explicit producer-declared UTC capture. Current persistence requires it. Future multipage source captures disclose interval and convention, not an atomic-provider snapshot claim |
| `provider_updated_at` | Optional documented provider metadata update; TCGdex update can use Git/compiler fallback and excludes pricing; never freshness proof |
| `first_seen_at` | Future earliest supported capture for exact reference in declared history/scope; currently unimplemented. Not first persistence or worldwide first appearance |
| `release_date` | Optional provider calendar date; region may be unknown. No invented timezone/instant |
| `price_observed_at` | Future documented price observation time; unknown if unsupported. No current runtime field |
| `sold_at` | Future completed-sale event date/time with documented precision; active offer/end date/provider aggregate cannot supply it. No current runtime field |

P4a `first_observed_in_window_at` retains its exact selected-window meaning.
`first_persisted_at` dates local batch storage and never a product launch.

## Empty, incomplete and failed captures — TD-005

Distinguish valid empty, successful nonempty, partial, policy/access denial,
rate limit, timeout/network failure and invalid/incompatible/oversized payload.
Zero rows from a limited page proves only that selector's response; it establishes
neither source health, completeness, product withdrawal nor stock. A partial
capture is never silently complete. Current P4a rejects selected rejection rows
rather than interpreting the admitted subset as a complete snapshot.

Schema1 proves empty-batch existence/capture/counts, not namespace/kind/language.
`request_attested_empty` is unauthenticated caller/producer scope attestation.
`records_verified` checks each admitted row's context, not corpus completeness.
Replay hashes are validated-context equivalence metadata, not authenticity or
independent scope evidence. **TD-005 remains open**; no migration/schema2 fix.

Before independent or multi-producer real empty-scope use, propose a later
authorized immutable capture record covering producer/method/source revision,
namespace/kind/language, selectors, pagination boundaries/completion, outcome,
capture convention, counts and bounded verification references. Define what
independent verifier/evidence supports it; merely storing/signing a producer
declaration proves neither source truth nor coverage. Require compatibility,
replay and adversarial empty/multi-producer tests in that future contract.
No new envelope fields, schema/model/reader/comparator or migration is added here.

## Current compatibility and review boundaries

INGESTION_V1 handles bounded set/card IDs/names, text localId/parent, optional
date/update and explicit CMT language/capture/variant context. Counts are ignored
extras with no normalized destination. Flags are validated then discarded;
availability does not create observed finish. `variants_detailed` is ignored.
Future capture-policy metadata cannot be injected into strict current envelopes.
No changes to MANIFEST/PERSISTENCE/STORAGE/DISCOVERY v1 or identity/history.

Preserve TD-001–TD-005. Source-policy limits refine R-03/R-04/R-06/R-10; no debt
is closed, and absent future commercial features are not invented technical debt.
Probes use safe documented endpoints, serial bounds and redacted diagnostics;
untrusted payload URLs are never followed. No provider calls enter CI.
