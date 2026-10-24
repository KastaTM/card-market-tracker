# WATCHLIST_SIGNAL_V1 — per-rule transition, offline synthetic only

**Status:** PROPOSED v1 implementation contract; gates tracked separately. A signal is **not**
an observed restock or commercial market alert. No destination, delivery state,
Telegram transport or bridge to Discovery/P8 outboxes exists in P5b.

## Transition algorithm (pure)

For each new append in an independent `(watch_id, revision, policy_version,
series_key)` sequence, inspect the immediate predecessor evaluation and the
current evaluation's **per-rule** P5a results, never the aggregate OR:

1. First evaluation: 0 signals regardless of MATCH, including external
   previous passed for P5a evaluation.
2. Only if predecessor has *the same configured rule* with `NO_MATCH`, current
   has `MATCH`, and the predecessor's current and new current observed_at are
   both fresh against **new evaluation as_of**, produce one signal. Fresh means
   `0 <= (new_as_of - observed_at) <= entry.max_age_seconds` including boundary.
   Explicit previous must equal predecessor current. Current P5a evaluation
   must have validated all timestamps and context.
3. MATCH -> MATCH: none. INDETERMINATE or SKIPPED -> MATCH: none; re-establish
   satisfied baseline. Anything -> NO_MATCH: none; current is a new unsatisfied
   baseline. Stale prior current against new as_of: none, even if prior was
   NO_MATCH when originally evaluated. Disabled entry: none.
4. Independent `price` and `restock` rules may both emit on the same append.
   Rule switches/unknown/expired evidence must not emit and must not be
   conflated with `OUT_OF_STOCK` or a confirmed real restock.
5. P5a result semantics remain unchanged (EUR integer cents, known shipping,
   fresher-than-max-age inclusive, validation before SKIPPED, UNKNOWN stock !=
   out-of-stock, current freshness before stock decision).

A configured rule's result is held only for the selected checkpoints. No claim
about unobserved intermediate states. NO_MATCH -> MATCH -> MATCH -> NO_MATCH ->
MATCH produces exactly two signals for that rule (assuming fresh continuity).

## Identity and fields

For each transition, preimage object exactly:

```
{"version":1,
 "kind":"WATCHLIST_RULE_ENTERED_MATCH",
 "mode":"synthetic",
 "sequence_id":<wjs1_>,
 "rule":"price"|"restock",
 "from_evaluation_id":<wje1_ predecessor>,
 "to_evaluation_id":<wje1_ current>}
```

Canonical bytes and domain separation follow WATCHLIST_JOURNAL_V1.
`signal_id = "wsig1_" + sha256(ASCII("CMT_WATCHLIST_SIGNAL_V1") + 0x00 +
canonical(preimage-object)).hexdigest()`. ID never includes a message,
recipient, insert time, run_id, filename or network source. Store exact
version/kind/mode/rule/evaluation links, derive and validate sequence membership
and the individual rule transition during deep verification. At most one per
`(sequence_id, to_evaluation_id, rule)`; no send counter or `sent` status.

### Expected independent reference vector

For synthetic target `541b9d13-9669-4973-8413-397bea14c045` in the existing
P5a synthetic manifest, revision1, high-priority price1000/restock enabled,
series `synthetic-series`, baseline OUT_OF_STOCK at 11:00Z, current AVAILABLE
at 12:00Z with price900+shipping100; see the oracle script for **literal full
preimages**:

- sequence: `wjs1_380dce2c23fa07657ddf95adac1c9f96c36c8449235e3462140dd88b684e676f`
- baseline: `wje1_411e24c6f8f6cf4089d335f5c1886b4f71b34cae34f69a9e54251007863aa284`
- next: `wje1_017178f97a80245df9bb2e997afef80e17894af07380621530c290ccc30f5b33`
- price signal: `wsig1_d9f9c7f0d4ca8767a6cdb9a917cc27a61c369cecea629c790ed42fd4421bf4f0`
- restock signal: `wsig1_4bd7f7a2ca57d7e8c9e340dc5f3c27aa5f3dbe433c7ef01a0ac897675e4e8bd4`

All keys are local synthetic equality hashes, not cryptographic attestation of
provider data. A replay yields the same ID set and no new signal rows.
