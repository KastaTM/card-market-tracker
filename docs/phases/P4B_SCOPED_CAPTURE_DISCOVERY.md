# P4b engineering evidence map

Status: implementation candidate, pending exact-candidate gates and independent
review. Only the Orchestrator decides acceptance/integration/closure. This file
maps reproducible evidence; the external PR ledger binds the final SHA/tree,
complete logs, actual verdicts and completion report without circular SHA commits.

Authority: [contract](P4B_SCOPED_CAPTURE_DISCOVERY_CONTRACT.md),
[brief](P4B_CODEX_ENGINEERING_BRIEF.md), [ownership/preflight](P4B_OWNERSHIP.md).
Base `430e2049c9ffdffb68508329df6556bfed62baa2`, tree
`c3988a86cedf525cce364bd9cc4709689c510053`. Branch
`feat/p4b-scoped-capture-discovery`. No merge authorized.

## Implementation and review boundaries

Additive generic `discovery/scoped_*` modules implement request v2, independent
snapshot/scope validation, cmp2/evt2 and a pure comparator. Storage adds one
window-wide bounded read-only transaction using retained P1b reconstruction.
CLI/logging add separate v2 dispatch/operation. No schema, migration, dependency,
v1 hash/validator/comparator or writer admission change. All original harnesses
and the four CI jobs remain. [ADR0007](../adr/0007-scoped-capture-discovery.md),
[DISCOVERY_V2](../data-contracts/DISCOVERY_V2.md), compatible storage/capture/logging
notes, architecture, runbook, testing/gates, threat/risk/debt/fixture ledger and
roadmap document the final boundaries.

Authors are Lead, db_owner and be_discovery. Independent QA is `/root/qa`, owning
only `tests/test_scoped_discovery_qa.py`; final reviewer is a different nonauthor
agent. SEC/SRE `/root/sec_sre` reviews without writes. Model/reasoning were
inherited without overrides; backend identity is not independently attested.
Final actual agent identities/verdicts belong to the external ledger.

QA finding QAF-01: contradictory observations in an unselected unit must fail
the whole operation. QA independently reproduced baseline/current/history
failures; BE added complete-unit contradiction validation. QA rechecked its
25 cases successfully on the provisional working tree. Final exact-SHA recheck
and disposition belong to the external ledger; this note alone certifies no gate.

## Acceptance evidence map

Run `uv run --frozen pytest -q tests/test_scoped_discovery_*.py` on shells expanding
that pattern; on Windows pass each file explicitly or run the complete suite.
The table names evidence locations, not unexecuted PASS claims.

| AC | Reproducible evidence |
| --- | --- |
| S01 | Ownership preflight, archived unchanged contract/brief, fetched Git object identities, attributed roadmap opening/closure, final external ledger |
| S02 | `test_scoped_discovery_input.py`; core exact unit/no-match; QA null/scope/tuple/constructor tests |
| S03 | storage `test_one_snapshot_covers_all_requested_capture_rows_and_envelopes`; ro/query_only/schema/metadata/full envelope/rows under one BEGIN |
| S04 | core four real units/mixed/constructor; storage mode/evidence/legacy/schema1; QA real pinned mixed-family case |
| S05 | core different_selector_or_path_set; QA scope_change/path_permutation; full-unit validation and QAF-01 |
| S06 | core partial_failed/selected_rejection/complete_empty; QA incomplete_empty/unselected_rejections; storage corruption and byte guards |
| S07 | core same_real_package_two_import_tokens/history_equal_or_future; storage four_real_units reimport; QA chronology offsets/ties |
| S08 | core synthetic_baseline/union/accepted_non_set/duplicates; QA candidate_union/alias/contradiction; QAF-01 across all units |
| S09 | core path_order_history_order_replay_and_restore; QA path_permutation_history_ties_and_backups; harness replay and restore equality |
| S10 | core/storage four_real_units with empty and coherent curated set bindings, original indexes; process harness real baselines and synthetic positives |
| S11 | storage missing/corrupt/limits/lock/deadline/parent_closure/concurrency; CLI failures; QA no-network/no-mutation; full logical/schema/bytes and restore checks |
| S12 | Full pytest suite, unchanged v1 modules/schema/lock, CLI v1 observed rejection, all prior installed/Compose/architecture harnesses |
| S13 | `scoped_capture_discovery_smoke.py`, wheel_smoke, Compose scoped service, container_smoke both platforms; distinct processes/UID10001/ro fixtures/no network |
| S14 | ADR0007/DISCOVERY_V2/storage/capture/logging/runbook/threat/debt/architecture/README and SEC/SRE/docs review against frozen tree |
| S15 | Frozen installs, Ruff/mypy/full coverage85/80/build/outside-tree/audit/scan; four final-SHA CI jobs with full logs; separate exact-SHA QA and REVIEWER |

## Required final gates and limitations

Execute the complete commands in the archived brief, including both frozen
installs, Ruff format/check, strict mypy, coverage full pytest/JSON/threshold,
sdist/wheel, outside-source installed old and new smokes, frozen export/audit and
secret scan. Check lock/schema/v1 module diff remains empty. Review all four final
CI job bodies, not merely status summaries. Independent QA and REVIEWER use
separate detached final-SHA worktrees. Each unexecuted mandatory gate is FAIL
with cause; historical P1b numbers are never credited as P4b results.

Local Windows preflight found Docker CLI but no running Linux daemon. Container
and Compose execution must therefore be evidenced by exact-candidate CI unless
the daemon becomes available. Windows uses the equivalent outside-tree wheel
environment; Linux CI executes the literal wheel_smoke.sh recipe.

The approved unchanged real bundle is two metadata artifacts/four projections
and one capture instant. Its four unit baselines and equal-time rejection do not
demonstrate a real provider transition. Positive comparisons and complete empties
are synthetic producer declarations. No source acquisition, global novelty,
launch/stock signal, external authentication, event delivery or native Pi/power
loss certification is claimed. TD-001–TD-005 and P2/P6a/retail blockers remain.
