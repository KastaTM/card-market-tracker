# P4b engineering ownership and preflight

Engineering Lead approved this allocation before implementation on 2026-10-16
(Europe/Madrid). Only the Lead mutates Git, shared contracts, CI and the lockfile.
No merge or phase acceptance is authorized.

| Actual agent | Role and exclusive writing ownership |
| --- | --- |
| `/root` | Engineering Lead; docs/contracts/ADR, roadmap, scripts, fixture ledger, Compose/CI, Git and integration |
| `/root/db_owner` | ARQ / DB-OWNER; `persistence/sqlite_repository.py`, necessary capture helpers, `tests/test_scoped_discovery_storage.py` |
| `/root/be_discovery` | BE / DISCOVERY; new `discovery/scoped_*.py`, CLI/logging, separate input/core/CLI/logging tests |
| `/root/sec_sre` | SEC / SRE; read-only boundary/operational review; no authorship |
| `/root/qa` | Independent QA; only `tests/test_scoped_discovery_qa.py`; final frozen-tree validation without edits |

QA and final REVIEWER are reserved for separate nonauthor agents, distinct from
each other. Their actual identifiers, reviewed SHA/tree, findings and commands
will be recorded in the external PR ledger after the candidate is frozen.

All spawned agents requested the inherited model/reasoning configuration; no
override was selected. The tool confirms task identities and accepted delegation,
but exposes no independent backend-model or reasoning attestation. The supplied
Sol/High recommendations are recorded in the archived brief; they are not proof
of the execution backend. No model switch is claimed.

## Preflight observations

The original checkout was clean on `feat/p1b-pinned-metadata-ingestion`, HEAD
`252c394141948e3ab77a54bcf628e4290ba69652`. Remote is
`https://github.com/KastaTM/card-market-tracker.git`. `git fetch origin` succeeded.
Fetched main exactly equals the authorized baseline
`430e2049c9ffdffb68508329df6556bfed62baa2`, tree
`c3988a86cedf525cce364bd9cc4709689c510053`, ordered parents
`acca10e406dac8809edc289c3077a6ec8785a622` then
`252c394141948e3ab77a54bcf628e4290ba69652`. Baseline and old P1b head have
identical trees. The authorized P4b branch did not exist locally or in fetched
remote refs and was created from that exact baseline.

Eight detached historical worktrees were preserved: `.p1b-evidence/qa` and
`reviewer` at `252c394…`; `.p3a-evidence/qa` and `reviewer` at `e9c5f02…`;
`.p4a-evidence/qa` and `reviewer` at `c5ed228…`; and
`.p4a-evidence/p05b/qa` and `reviewer` at `302e8d3…`. The main working directory
is the only attached worktree. No reset, cleanup, force push or historical report
rewrite occurred.

Sandbox processes failed before launch with `setup refresh had errors`.
The authorized escalation path executes commands successfully. `uv` is 0.12.10;
both initial frozen installations succeeded. Docker CLI exists but its local
Linux daemon was unavailable at preflight. These observations do not certify
candidate tests or container gates; final results belong to the evidence ledger.

## Interfaces and checkpoints

`read_scoped_snapshots` returns generic immutable scoped capture DTOs after
one read-only SQLite transaction validates schema2, full envelopes, all records
and retained identity closure. Source bundle reconstruction stays in storage.
The comparator imports neither SQLite nor source models, revalidates public
request/DTO boundaries, and selects original indexes from persisted scope only.
Python construction cannot establish verified storage provenance.

Milestones: contract/ADR and interfaces; storage plus pure comparator/CLI;
negative/temporal/concurrency matrix; installed process harness plus all four CI
jobs; hardening/docs; freeze exact SHA/tree; independent QA and REVIEWER;
external completion ledger and PR handoff. Every unexecuted mandatory gate is
FAIL, with its reason. Historical P1b results are never P4b evidence.
