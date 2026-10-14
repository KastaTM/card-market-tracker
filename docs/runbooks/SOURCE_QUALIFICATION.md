# Source qualification research runbook — P0.5b

Documentation only; no production collector or real-data storage command.
See [contract](../phases/P0_5B_REAL_SOURCE_QUALIFICATION_CONTRACT.md),
[field policy](../sources/P0_5B_FIELD_USE_CAPTURE_POLICY.md) and
[ledger](../sources/P0_5B_EVIDENCE_LEDGER.md).

1. Establish baseline/authority and source-specific field-use rights before data
   requests. Separate current documentation, historical observations and inference.
2. Lead owns one shared serial budget and writes each preflight before execution.
   No accounts, accepted contracts, tokens/cookies, costs, contacts or evasion.
3. Inspect public documentation freely within source scope; do not confuse it
   with direct data or claim origin status/timing/bytes that browser tools hide.
4. Direct permitted GETs are <=15s/256KiB,12 total/6 provider, no retry or unchecked
   redirect/link follow. Count emitted failures, stop401/403/429 or quota/overrun.
   Only minimal diagnostics remain if retention rights are unresolved.
5. Record successful empty/nonempty, partial, policy/access denial, rate limit,
   timeout, invalid/oversized response and network failure separately. Missing or
   partial never means zero products, removed SKU, out-of-stock or healthy source.
6. Do not repeat live probes for QA/REVIEWER. Six TCGdex requests are already used;
   its allowance is exhausted. Review diagnostic evidence and official docs.
7. Future source/scope/rights changes need a new approved investigation budget or
   consumer-phase contract. Current `persist`/`discover` remain synthetic-only;
   do not relabel observed data, modify schema1 or process real samples through DB.

The final PR ledger records exact head/base/tree and final automated gates/reviews.
All required unexecuted gates are FAIL. Readiness is engineering review status,
never phase acceptance or integration permission. Only the Orchestrator decides.
