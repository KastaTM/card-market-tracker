# P8b engineering evidence map

Authority: [verbatim Orchestrator contract](P8B_TELEGRAM_ALERT_DELIVERY_CONTRACT.md)
and [Engineering Brief](P8B_CODEX_ENGINEERING_BRIEF.md). This committed map defines
the reviewed implementation and evidence recipes; final exact head/tree, full CI
logs, independent attestations and phase verdict are published and re-read in
the unmerged PR ledger. It avoids a self-referential SHA-only evidence commit.
Only the Orchestrator can accept, authorize merge or close P8b.

## Baseline, ownership and MODEL PROFILE USED

Baseline main `ac35d4df0f3a006ff60bb026de992c366e19cc09`, tree
`d604d3b8362c30af8b5dd516eddc0d8095fe7bf9`; clean registered worktrees and no
branch collision; local fetch and independent GitHub branch/tree response agree.
Dedicated branch `feat/p8b-telegram-alert-delivery`. Contract/protocol freeze
commit `ea3cacf` precedes implementation. See
[ownership/model/preflight](P8B_IMPLEMENTATION_PLAN.md). Requested lead profile is
GPT-6.1 Sol/Medium with High critical work. Root identifies as GPT-6-based Codex,
exact selector/reasoning unknown. Collaboration selector offered and selected
`gpt-6.1-sol` / `high` for DB, transport and application authors. QA and REVIEWER
must be distinct new nonauthors; their actual selections/attestations belong in
the exact-candidate ledger. Do not interpret a planned role as an executed review.

## Final behavior and compatibility

New `telegram_delivery/` separates storage, application, transport and CLI.
Captures/journal/outbox schemas and source code, renderers, cmp3/evt3/alt1, R0/R1
and synthetic constraints remain unchanged. Only shared CLI/logging registration
extends prior runtime surfaces. No new runtime/development dependency or lock
change. No source acquisition, scheduler, daemon, groups, topics, webhooks,
inbound command, arbitrary-text send, prices or stock.

ADR0011 freezes tdl1 identity, provider/event uniqueness, immutable private routes,
ten content commitments, five CMTD/schema1 STRICT tables and claim/results history.
Claim commits before sendMessage; CAS exact owner/state finalizes. Confirmed
needs validated sender/private recipient/exact text/date/message ID plus durable
receipt. Timeout/crash/5xx/malformed success/lost commit blocks resend. Valid429
alone permits explicit later due retry, max3; third429 is retry_exhausted. Restore
always quarantines the whole ledger through pre-quarantined staging. No force.

## AC evidence index

All test files are under tests/; the following are executed by the complete
suite. Final PASS/FAIL/BLOCKED is assigned individually in the immutable PR ledger
using observed results, never merely because a test/requirement exists.

| AC | Concrete implementation and evidence |
| --- | --- |
| T01 | authorized preflight, plan, exact contract import, attributed ROADMAP decision |
| T02 | git diff older source/lock nonmutation; full previous regression suite; ninth smoke origin-file digests |
| T03 | storage route attestation/conflict tests; application bot mismatch; transport getMe/getChat/private projections |
| T04 | application full source proof, independent commitment digests, changed outbox/coherent journal/alias/path probes |
| T05 | independent tdl1 oracle in storage tests and smoke; transport exact request JSON; fake observes exact frozen text |
| T06 | storage exact inventory/owner, replay/conflict, hostile cells, rollback/error mapping/history reconstruction |
| T07 | two independent claim processes; stale finish/recovery fencing, immutable result constraints |
| T08 | application durable receipt/replay; separate installed-process smoke reopen with zero new calls |
| T09 | storage os._exit before receipt commit, interrupted claimant; application confirmation/fallback failure; uncertain no-resend |
| T10 | 4291..86400, not_before/clock rollback, max3/third429; strict validated permanent rejection vs ambiguity |
| T11 | fixed TLS POST/no proxy/redirect/retry; strict64KiB/depth/type/framing; real spawned DNS/read/drip deadline probes |
| T12 | malformed/reflected exceptions and bodies, configuration grammar; CLI/error/log redaction and allowlists |
| T13 | twelve strict CLI operations, args/exit codes; bounded state/keyset pages; local verify vs origin-recompute |
| T14 | consistent exclusive backup, global quarantine empty/stale/absent rows, final-path restore dispatch-race probe, sidecar preservation |
| T15 | complete frozen gates, ninth harness in wheel/Compose/AMD64/ARM64-QEMU; requires four final CI logs |
| T16 | distinct nonauthor QA and REVIEWER exact-SHA/tree reports with own probes and findings; required externally |
| T17 | BLOCKED / LIVE_UNVERIFIED until operator authorizes specific private route and observes one real receipt + restart replay |
| T18 | ADR0011/API/storage/threat model/logging/runbook/quality/testing/ownership/roadmap/debt and external final report |

Focused author probes initially observed transport129 PASS, application/CLI120
PASS, storage56 PASS. These are working-tree observations, not independent or
final-SHA attestation. First full regression before last added storage/application
probes observed1602 PASS/1 skip,93.89% lines/87.74% branches. Final exact-candidate
results supersede those in the external ledger. Preliminary isolated wheel ninth
smoke passed with no Telegram token or network and no original-file mutation.

## Reproducible gates

```text
uv sync --frozen --no-install-project
uv sync --frozen --no-build-isolation
uv run --frozen ruff format --check .
uv run --frozen ruff check .
uv run --frozen mypy src
uv run --frozen coverage run -m pytest
uv run --frozen coverage json -o coverage.json
uv run --frozen python scripts/check_coverage.py coverage.json
uv build --no-build-isolation
sh scripts/wheel_smoke.sh
uv export --frozen --all-groups --no-emit-project -o requirements-audit.txt
uv run --frozen pip-audit -r requirements-audit.txt
uv run --frozen python scripts/check_secret_scan.py
```

On Windows install the built wheel in .p8b-evidence/wheel, run its Python over
all nine installed harnesses with --mode installed --fixtures tests/fixtures;
each starts isolated installed processes outside checkout. On Linux CI,
wheel_smoke.sh performs the complete outside-checkout installation. Compose runs
all nine; container_smoke.sh builds each matrix architecture and runs all nine.
UID10001, private persistent volume, readonly fixtures and network-none remain.
The local Docker daemon was unavailable; container PASS requires real CI, not
historical P8a success. Four jobs remain quality, compose and two architectures.

## Live gate and limitations

[Concrete local instructions](../runbooks/TELEGRAM_DELIVERY_RECOVERY.md) use
prepare_telegram_live_gate.py for normal synthetic evidence and an empty ledger,
then explicit operator-owned route/validation/preparation. telegram_live_gate.py
wraps production CLI entry with request counters and one-attempt evidence
reservation, without changing its network worker. One send only; separate-process
replay removes token and forbids network. Never request a token in chat. Specific
private-destination authorization is absent at kickoff. No real call or receipt
is inferred from offline tests. T17 is mandatory for full readiness.

Accepted is API acceptance plus committed receipt, not human delivery/read.
No exactly-once claim; conservative no-resend may omit a notification. One active
trusted ledger authority and immutable originals are assumed; copied authorities
and privileged coherent rewrites are outside authentication. Local verify cannot
rederive opaque original hashes; origin recompute can. Host UTC supports persisted
cooldowns; rollback is blocked. Network hard supervision has bounded process
cleanup overhead; cooperative SQLite cannot bound a stalled device/kernel.
QEMU/process interruption is not native Pi electrical durability. TD-001..TD-005
remain OPEN, P2/P6a/retail Discovery BLOCKED, P5 unopened. No merge is authorized.
