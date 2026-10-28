# P8c implementation ownership

Date2026-10-27. P8c OPEN; Phase Lead accepted design only. Orchestrator alone
accepts candidates, authorizes merge or closes phases.

| Session | Exclusive authoring / role |
| --- | --- |
| /root | CLI, logging, harness/CI, shared docs, integration/Git/publication |
| /root/p8c_freeze_arq | New errors/models/policy/render/application/init; additive P5b reader; domain/application/source tests; oracle/fixture |
| /root/p8c_freeze_db | New schema/storage; storage/concurrency/recovery author tests |
| /root/p8c_freeze_sec | Read-only security/operability review, no product authorship |
| /root/p8c_qa | Independent nonauthor QA; only scripts/p8c_qa_probe.py; own stdlib reference/oracles |
| /root/p8c_reviewer | Distinct final nonauthor reviewer; only scripts/p8c_reviewer_probe.py; own oracles/readback |

Specialist selector arguments gpt-6.1-sol/high are observable; backend unverified.
Root selector/effort are not independently exposed. QA/REVIEWER preparation ran on
the working candidate; final execution/attestation requires the committed SHA/tree.
Their scripts are independent of author tests and each other's helpers. Shared files/Git are sequential Lead-owned.
Tests/gates/reviews need final SHA/tree evidence; historic design reviews do not
certify runtime. Frozen four contracts retain accepted hashes.

## RW-01 ownership (2026-10-28)

Orchestrator REWORK_REQUIRED, accepted by Phase Lead. Prior readiness suspended.

| Session | Exclusive ownership / role |
| --- | --- |
| /root | Standalone public-API regression probe, shared docs/CI/Git/evidence publication |
| /root/p8c_rw01_db | watchlist_alerts/storage.py and new test_watchlist_alert_rw01.py; author |
| /root/p8c_rw01_arq | Read-only identity/conflict/complete-entry semantics and fix readback |
| /root/p8c_rw01_sec | Read-only transaction/corruption/deadline/failure-mode review |
| /root/p8c_rw01_qa | New independent QA, only scripts/p8c_rw01_qa_probe.py; no product authorship |
| /root/p8c_rw01_reviewer | New distinct final reviewer, only scripts/p8c_rw01_reviewer_probe.py; no product/QA authorship |

Actual specialist spawn selector arguments gpt-6.1-sol/high; backend unverified.
Root requested gpt-6.1-sol/Medium with High for critical decisions; actual root
selector/effort not exposed. No reuse of previous candidate attestations as
corrected-candidate acceptance. Frozen DDL/identities/contracts remain unchanged.
