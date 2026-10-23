# Watchlist synthetic evaluation v1

P5a-only sample and policy contract, separate from observation/capture contracts.
The application reparses the full raw manifest and compares its target projection
with the selected frozen revision. The pure evaluator then consumes that revision,
current sample, optional previous sample and explicit as_of. It has
no SQLite, network or implicit clock. Samples, prices and evaluation results are
never persisted by the watchlist. A MATCH creates no event and authorizes no send.

## Sample grammar

All fields below are required; unknown fields are forbidden.

| Field | Constraint |
| --- | --- |
| version | Exact integer 1, not bool |
| provenance | Exactly `synthetic` |
| sample_id | Synthetic ASCII token, 1..128 characters |
| cmt_id | Canonical lowercase UUIDv4, exactly the watched target |
| series_key | Synthetic ASCII token, 1..128; identical for current and previous |
| observed_at | Explicit zoned instant, normalized to UTC |
| currency | Exactly `EUR` |
| unit_price_minor | Null or exact integer 1..1000000000 |
| shipping_minor | Null or exact integer 0..1000000000 |
| stock | `AVAILABLE`, `OUT_OF_STOCK`, `UNKNOWN` |

Amounts are integer cents, never floats/coerced strings/bools/negative/NaN/
infinity. Unit zero is invalid. Shipping zero is known free shipping; null is
unknown. Unit and shipping sum uses exact integer arithmetic. No URL, real
observation, arbitrary extras or executable expression is admitted. Strict JSON
parsing rejects duplicate keys and observes max1MiB, depth16, nodes20000 and
strings1024, plus tighter field bounds. Public Python objects are revalidated.

Tokens match `[A-Za-z0-9][A-Za-z0-9_.:-]*`. Timestamp grammar is
`YYYY-MM-DDTHH:MM:SS[.fraction](Z|+HH:MM|-HH:MM)`, fraction1..6 digits,
maximum40 characters; dates/offsets must form a valid UTC-normalizable instant.
Normalization emits ISO UTC with Z and canonical microsecond representation.
The amount sum is capped at2000000000 cents; each operand is capped at1000000000.

`provenance=synthetic` is an operator declaration, not origin authentication.
The operator must author/review synthetic fixtures; relabeling real commercial
data does not grant retention or usage rights.

## Validation order and time

First validate complete manifest, frozen watch identity/configuration and sample
shape/context. Previous, if supplied, has identical cmt_id and series_key and
strictly precedes current. Reject future current or supplied previous relative to
explicit as_of, invalid chronology and incompatible contexts even when the watch
is disabled or a particular rule would not need previous evidence. An invalid
input produces an explicit error rather than SKIPPED or INDETERMINATE.

Current/previous sample_id must also differ; duplicate IDs produce
invalid_chronology. Context mismatch produces incompatible_context, future
evidence future_sample and nonpreceding previous invalid_chronology.

Offset-equivalent instants normalize to the same UTC instant. No system clock,
local timezone or implicit latest revision participates. Fresh means
`0 <= as_of - observed_at <= max_age_seconds`, inclusive at both boundaries.
Current freshness precedes stock decisions. Previous freshness is needed only
for restock toward AVAILABLE; an expired previous does not invalidate a fresh
current OUT_OF_STOCK NO_MATCH. Structurally invalid supplied previous always fails.

## Rule outcomes

| Price evidence | Outcome |
| --- | --- |
| Current stale | INDETERMINATE |
| Fresh OUT_OF_STOCK | NO_MATCH |
| Fresh UNKNOWN | INDETERMINATE |
| Fresh AVAILABLE, unit or shipping unknown | INDETERMINATE |
| Fresh AVAILABLE, known unit+shipping <= target | MATCH |
| Fresh AVAILABLE, known unit+shipping > target | NO_MATCH |

| Restock evidence | Outcome |
| --- | --- |
| Current stale | INDETERMINATE |
| Fresh current OUT_OF_STOCK | NO_MATCH |
| Fresh current UNKNOWN | INDETERMINATE |
| Fresh current AVAILABLE, previous absent/stale/UNKNOWN | INDETERMINATE |
| Fresh previous OUT_OF_STOCK -> fresh current AVAILABLE | MATCH |
| Fresh previous AVAILABLE -> fresh current AVAILABLE | NO_MATCH |

Disabled configuration returns aggregate SKIPPED after validation. Enabled rules
retain individual outcomes and stable machine-readable reasons. OR aggregate:
any MATCH -> MATCH; otherwise any INDETERMINATE -> INDETERMINATE; otherwise
NO_MATCH. Priority affects list ordering, never rule truth. No missing evidence
is invented and a configured rule is not discarded to improve the aggregate.

Stable reasons are current_stale, current_out_of_stock, current_stock_unknown,
price_unknown, at_or_below_target, above_target, previous_missing,
previous_stale, previous_stock_unknown, restocked and already_available.
Rules are ordered price then restock when configured, each object exactly
`{rule,result,reason}` with rule `price` or `restock`. Disabled output has
rules=[] and reason=disabled.

## Evidence and reproducibility

Output has exactly version1, policy_version=`watchlist-rules-v1`, watch_id,
revision, cmt_id, as_of, current_sample, previous_sample, result and rules,
plus reason=disabled only for SKIPPED. Sample references contain exactly
sample_id and digest; previous_sample is null when no previous was supplied.

Versioned output binds watch_id, immutable revision, policy_version, current and
optional previous sample IDs/digests and normalized as_of, plus aggregate and
individual rule reasons. Canonical sample JSON uses sorted keys, ASCII escaping,
compact separators and no NaN, UTF-8 SHA-256. Same validated inputs yield the
same canonical JSON bytes. Digests establish equality of declared local evidence;
they authenticate neither source nor administrator. Stdout is contracted operator
data; structured logs exclude samples, prices, preferences and raw input.

Evaluation has no side effects, source requests, notifications, journal/outbox
rows or mutations of any database. Changes to grammar, identity, freshness,
stock, money, reason or aggregate semantics require versioned contract review.
