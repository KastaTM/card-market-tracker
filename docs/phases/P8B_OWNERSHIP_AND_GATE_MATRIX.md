# P8b — Original Phase Lead ownership and acceptance matrix

**Provenance:** original pre-implementation Phase Lead handoff, retained below as
a historical planning matrix. Its NOT RUN/BLOCKED statements describe that prior
environment, not the current engineering run. Current exclusive ownership and
model selections are in [implementation plan](P8B_IMPLEMENTATION_PLAN.md);
current code/evidence map is [P8b engineering report](P8B_TELEGRAM_ALERT_DELIVERY.md).
Final exact-candidate CI/reviews and verdict belong in the unmerged PR ledger.

| Domain / files | Assigned future owner | Independent check |
| --- | --- | --- |
| `telegram_delivery/schema.py`, `storage.py` | DB-OWNER one author, ARQ review | QA, REVIEWER |
| `telegram_delivery/transport.py` | INTEGRATIONS/SEC/SRE single author | QA, REVIEWER |
| `telegram_delivery/application.py`, `errors.py`, `cli.py` | BE single author | QA, REVIEWER |
| `src/card_market_tracker/cli.py`, CI, smoke integration | Engineering Lead integrator | QA, REVIEWER |
| ADR, contracts, threat model, roadmap, runbook | DOCS (or Engineering Lead) | REVIEWER |
| Independent adversarial probes | QA non-author | REVIEWER |
| Final exact SHA/tree architecture/security diff | REVIEWER non-author | Orchestrator |

## Gates — baseline vs phase evidence

| Criterion | Required evidence | Current state |
| --- | --- | --- |
| T01 | baseline SHA/tree verified; archived contract/roadmap in Git | baseline PASS; repo update BLOCKED |
| T02 | outbox unchanged, schema/identities regression pass | NOT RUN |
| T03 | pinned private route, getMe/getChat validation, conflict probes | NOT RUN |
| T04 | original-capture recompute at prepare and send, negative tests | NOT RUN |
| T05 | exact P8a message bytes + identity vectors | NOT RUN |
| T06 | ledger exact schema/semantic verification + replay | NOT RUN |
| T07 | multi-process claim, CAS fencing, stale finalize probes | NOT RUN |
| T08 | durable confirmed receipt and process-restart replay | NOT RUN |
| T09 | crash/uncertain no-resend matrix | NOT RUN |
| T10 | 429/not_before/3-attempt cap and permanent rejection tests | NOT RUN |
| T11 | official TLS/no redirects/retries/proxy; overall timeout | NOT RUN |
| T12 | token/PII redaction including malicious response/exception | NOT RUN |
| T13 | CLI arguments/limits/exit codes/keyset paging | NOT RUN |
| T14 | consistent backup/exclusive restore/quarantine-global | NOT RUN |
| T15 | new tests, 9th harness; Quality/Compose/AMD64/ARM64 CI | NOT RUN |
| T16 | two independent reviewers on exact SHA/tree | NOT RUN |
| T17 | one authorized real send, receipt+replay, <=8 metadata | BLOCKED / LIVE_UNVERIFIED |
| T18 | committed ADR/contracts/threat model/runbook/ledger docs | NOT RUN |

**Quality gates:** Ruff format/check NOT RUN; mypy strict NOT RUN; pytest NOT RUN; unit/integration/contract/regression NOT RUN; coverage NOT RUN; sdist/wheel NOT RUN; audit/secret scan NOT RUN; Docker/Compose/AMD64/ARM64 NOT RUN; CI NOT RUN. The P8a CI from the opening contract is historical evidence **only**.

**Current blocking issue:** `GH-403`: GitHub connector can read repository metadata/contents but `create_branch` to `KastaTM/card-market-tracker` was rejected `Resource not accessible by integration`. No local checkout/network/`codex` executable available in this environment. Resolve in the authorized VS Code/Codex execution environment, not by granting unrestricted token in a chat.

**Additional live gate dependency:** operator-controlled Telegram token and a specifically authorized private destination + synthetic test alert. Do not seek those until offline implementation, review and CI are ready.

**Allowed report today:** P8b IMPLEMENTATION BLOCKED, with an actionable engineering handoff. **Not** `READY_FOR_ORCHESTRATOR_REVIEW`, `ACCEPTED` or `PHASE CLOSED`.
