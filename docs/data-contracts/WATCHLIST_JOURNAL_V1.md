# WATCHLIST_JOURNAL_V1 — admission and evaluation identity

**Status:** PROPOSED v1 implementation contract; gates tracked separately. **Producer:** explicit
one-shot local operator request. **Consumer:** independent P5b journal.
References: P5a WATCHLIST_V1, WATCHLIST_SYNTHETIC_EVALUATION_V1, ADR-0013.

## Record request and admission

Required distinct paths: `--watchlist-db`, `--journal-db`, `--manifest`,
`--watch-id`, `--revision`, `--sample`, `--as-of`. Optional `--previous`.
There is no implicit latest revision or sample selection, no init on record.

1. Parse `manifest` as the **entire** MANIFEST_V1 and revalidate all P5a
   constraints (including unrelated entities/bindings) before use. Retrieve
   the specified immutable P5a watch revision without changing it and recheck
   identity_projection(manifest, entry.cmt_id), watch_id, revision, canonical
   identity and config. Treat neither caller-supplied entry nor snapshot JSON as
   trusted. Historical revisions are valid *simulation* authority only.
2. Validate current and optional previous with P5a parse_sample (strict v1,
   declared `provenance=synthetic`, EUR, no extras, 1MiB input/depth16/
   nodes20000/string1024). Revalidate at the public Python boundary too.
   Normalize UTC timestamp and explicit as_of with P5a timestamp; P5a evaluator
   rejects future, duplicate, reversed or mismatched source samples even if
   the revision is disabled.
3. Reuse the pure P5a evaluator, storing the **entire** recalculated result,
   all reasons and per-rule outcomes. Never accept user-provided MATCH, SKIPPED,
   digest, sequence identity, saved result or `verified` flag. Original manifest,
   names, aliases, bindings and unrelated entity data are *not retained*.
4. Freeze exact normalized entry (the complete P5a `parse_entry` output),
   current, nullable previous, UTC as_of, policy version and recomputed result.
   Canonical evaluation snapshot (below) is <=65536 UTF-8 bytes; reject before
   any write. This retention exception applies **only** to the new journal.

## Canonical JSON and identities — immutable v1 preimages

Canonical object encoding equals P5a `validation.canonical` after strict
normalization: sorted object keys, ASCII escapes, compact separators, no NaN;
UTF-8 bytes. Null is JSON `null`, bool has true/false (not 1/0); timestamps
already normalized to UTC Z; numeric cents are exact integers. The bytewise
preimage for each ID is `ASCII(domain) + byte(0x00) + UTF8(canonical(object))`.
Never use a printable two-character `\\0` in the bytewise preimage. Lowercase
hex SHA-256 output is prefixed as shown. No insert clock, run_id, paths, order,
destination or claimant field appears in the ID.

```
sequence object exactly:
{"watch_id":<wlt1_ id>,"revision":<int>,
 "policy_version":"watchlist-rules-v1","series_key":<synthetic token>}
domain = CMT_WATCHLIST_JOURNAL_SEQUENCE_V1
id = wjs1_ + sha256(preimage).hexdigest()

evaluation object exactly:
{"version":1,"sequence_id":<wjs1_ id>,
 "policy_version":"watchlist-rules-v1", "entry":<normalized P5a entry>,
 "current":<normalized P5a sample>,"previous":<normalized sample or null>,
 "as_of":<normalized UTC timestamp>}
domain = CMT_WATCHLIST_JOURNAL_EVALUATION_V1
id = wje1_ + sha256(preimage).hexdigest()
```

Rule-result DTO is **not** in the evaluation ID preimage: it is recomputed from
entry/current/previous/as_of and checked on read. The evaluation ID therefore
commits every input necessary to derive it, including the immutable watchlist
revision and projection. A forged result cannot become true by rehashing a local
row; deep verify recalculates and compares it.

Sequences commit `watch_id, revision, policy_version, series_key`; the stored
normalized entry MUST be identical for every evaluation sharing `(watch_id,
revision)` even across separate synthetic series. An incompatible entry for a
nominally immutable watch revision is `identity_conflict` and cannot fork an
alternate sequence. Changing revision or policy starts a different sequence.
Different watched product/variant cannot share a valid watch_id because P5a
binds watch_id to canonical cmt_id and selected revision entry.

## Sequence and replay

- First evaluation in sequence: predecessor null, signal-free baseline.
  Its optional well-formed previous may be outside the sequence; it is not a
  logged predecessor and does not activate transitions.
- New evaluation: observed_at(current) **strictly greater** than predecessor's
  observed_at(current); as_of **not earlier** than predecessor's as_of. Current
  sample_id has never appeared as current in the sequence. Explicit `previous`
  is required and byte-for-byte canonical equal to predecessor current sample.
  It must also satisfy the existing P5a sample/context/chronology rules.
- Duplicate semantic evaluation already stored: replay, even if not head;
  return its original ID/time/signals without updating the sequence or sending
  anything. The replay branch precedes append chronology checks, but never
  bypasses input revalidation or revision/identity checks.
- Same sequence/current sample_id but changed semantic input, previous, as_of
  or result: conflict; no updates. Different current sample at same timestamp,
  distinct successor from old head or attempt to backfill is also conflict.
  Re-evaluating a current sample at another as_of is **not** a new observation.
- P5a is only read by record and recompute. Journal writes are a separate
  transaction; there is no distributed atomic commit, hence the operational
  assumption of immutable P5a revision/origin.

## Output and safe handling

`record` success JSON includes `version:1, result:recorded|replayed,
sequence_id, evaluation_id, predecessor_evaluation_id:null|id,
signal_ids:[...], signals_count, persisted_at` (first persisted time unchanged on
replay). `get` returns the full stored, recomputable snapshot/result; lists are
bounded and cursor-paginated. stdout and on-disk snapshots/backups are local
operator-sensitive (prices/preferences); redacted structured logs emit only
operation, duration, category and counts. No credentials or commercial sources.

## Executable identity oracles

See `scripts/p5b_identity_oracle.py`: an independent stdlib reference producing
literal canonical JSON preimages, exact digests and a two-rule baseline-to-MATCH
fixture. The source and expected values must be versioned in tests, and QA must
reimplement hashing independently of the production helper. A passing script
alone is design validation, not a P5b implementation or CI PASS.
