# Capture scope and dedicated admission v1

Status: P1b implementation candidate; Orchestrator acceptance pending.

`persistence.capture.persist_bundle(path, bundle, batch_id, manifest)` is the new
real admission boundary. It accepts a strict raw bundle document or frozen
VerifiedBundle, and always reconstructs/revalidates it against the packaged,
review-controlled exact bundle digest. Python construction, self-declared hashes,
`observed` strings and altered timestamps confer no authority. No caller-selected
upstream path is opened. Runtime uses only the installed minimum licensed bundle.

The adapter produces four source records: set/card in ES/EN, namespace
`tcgdex_repository`, method `pinned_repository_bundle`, fixed revision
`4199850a6af49665db0080fa2bb9ef751750a406`. Its card references retain textual 136,
relation to swsh3 and variant unknown. UUID/bindings remain explicitly curated;
sets require coherent bindings, cards remain candidates unknown_variant. Records
rejected by resolution remain counted source records, not evidence of emptiness.

Each envelope stores version, reviewed bundle, scope evidence, resolver-relevant
manifest context and complete frozen resolution snapshot. Scope records source,
method, revision, policy/extractor, bundle/projection/artifact digests, original
acquisition and declared capture timestamps, exact selected/completed paths and
four separate kind/language/selector units. Units include source_count,
record_indexes and accepted/candidate/rejected counts. Top counts describe all
four inputs. `first_persisted_at` is separate and never redates acquisition.
Evidence state is `verified_local_pinned_bundle`: checked local reviewed package,
not independent producer authenticity or physical/current source truth.

Missing translations, incorrect digests, altered policy/parser evidence, omitted
files, empty projections and arbitrary extra fields fail before opening storage.
There is no valid empty real selection in this package. Complete_nonempty refers
to the selected files only, never the full catalog or regional availability.

`persist_capture(path, batch, scope)` provides generic synthetic demonstrations.
It revalidates PERSISTENCE_V1 batches and requires this exact scope document:

```json
{
  "version": 1,
  "acquired_at": "2026-10-14T17:53:09.118954Z",
  "captured_at": "2026-10-14T17:53:09.118954Z",
  "outcome": "complete",
  "units": [{
    "namespace": "synthetic_scope", "kind": "set", "language": "es",
    "selector": "explicit selection",
    "selected": ["synthetic/a"], "completed": ["synthetic/a"],
    "record_indexes": []
  }]
}
```

Units never mix namespace/kind/language. Each input index occurs exactly once;
nonrejected observations must match its unit. Rejected indexes are explicit local
producer assertions whose original invalid payload is not retained. Bounds are
32 units and 1000 input indexes total; each unit's selected and completed lists
may each contain at most 1000 unique paths. The path limit is per unit list, so
two units can contain 1002 distinct selected paths. Selector/path strings are
limited to 256 characters and namespace to 128. Combined JSON bytes, depth and
nodes remain bounded by the existing generic limits. Completed paths must be a
subset of nonempty selected paths. Lists canonicalize for replay; selectors and
contexts are exact. Outcomes are complete, partial, failed. Complete requires
all selected paths completed; partial never becomes complete. Failed has zero
admitted inputs. Complete zero-record selection is a valid synthetic empty;
resolution rejects/candidates do not erase source input. Evidence is
`producer_declared`, not independently authenticated completeness.

The unchanged PERSISTENCE_V1 synthetic guard rejects documented/observed input.
Its historical and new unscoped writes have `legacy_unverified`, scope null.
Migration does not infer old scope from bindings or upgrade producer declarations.

`query_capture(path, batch_id)` reads schema, one batch, envelope and all ordered
records in one owned read transaction, with the repository 2-second default,
5-second maximum budget and 1001-row overrun sentinel. Missing token fails;
existing empty capture returns its metadata and scope. Output includes version,
result, schema_version, evidence_state, capture, batch and records. New envelopes
are independently reconstructed and checked before returning. SQL byte-length
guards precede envelope materialization; lexical depth/node/string bounds precede
complete JSON decoding. Tests replace valid scope, metadata and rows concurrently
and demonstrate that readers retain one consistent snapshot. Selected v2
synthetic/legacy captures are revalidated within the Discovery read snapshot,
without a current manifest or an additional transaction. Query is explicit
bounded output; source content and IDs do not enter automatic logs.

Reusing a token returns replay only for identical normalized scope, immutable
times, policy/artifacts/digests, resolver context and ordered frozen records.
Imported/persisted time stays the first insertion time; committed counts are zero.
Changed evidence/context conflicts atomically. Names/audit reasons on curator
entities are excluded, consistently with resolver inputs; no arbitrary curator
text is retained. Hashes check equality/integrity, not external authenticity.
