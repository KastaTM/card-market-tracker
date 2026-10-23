# P5a engineering brief and ownership

Date: 2026-10-23. OPEN / IMPLEMENTATION AUTHORIZED. Only the Orchestrator may
accept, integrate or close this phase. Source: the user-supplied P5a opening
contract and Codex execution request; the offline handoff is reference material,
not integrated evidence.

## Preflight and model profile used

Remote https://github.com/KastaTM/card-market-tracker.git, remote main
d1038df1625a9727b44760866266b7124bb1d91a, tree
2bb06b79a04fefdc945f754e3611d5862192f5dc. Parents ac35d4df0f3a006ff60bb026de992c366e19cc09
and 9dab8a9b31dcc93cced8e90da20f81dae685661b. Initial worktree clean on P8b;
existing branches/worktrees preserved. Dedicated branch feat/p5a-offline-watchlist
created from the authorized base. Local main is older; no reset or merge used.

Requested lead GPT-6.1 Sol / Medium, High for complex decisions. Observable lead
identity from session instructions: GPT-6; effective reasoning setting is not
observable. Specialist selections and actual execution will be recorded separately;
a requested selector is not proof of the serving model.

## Ownership before parallel implementation

- Engineering Lead: integration, watchlist CLI, root CLI/logging wiring, docs,
  harness and CI wiring, author tests of those surfaces; Git state changes.
- BE/ARQ author: watchlist errors/models/validation/evaluation/application and
  domain/application author tests. No storage/CLI/shared-state edits.
- DB-OWNER author: watchlist schema/storage and storage author tests. No
  domain/CLI/shared-state edits. Coordinate domain interfaces with BE first.
- Independent QA and a separate independent REVIEWER: no runtime authorship;
  their own read-only probes on the frozen final SHA/tree. Assigned after author
  integration; substantive fixes require renewed final-candidate reviews.

## Frozen decisions

Full MANIFEST_V1 parser at add/update/evaluate boundaries; only existing printing
or sealed. Identity projection includes printing/card/set closure or sealed and
optional set, excludes names, dates, aliases and unrelated entities. Nulls and
unknowns remain exact. watch_id = wlt1_ + SHA256(UTF8("CMT_WATCHLIST_V1\\0" + cmt_id)),
where \\0 denotes one NUL byte. Canonical JSON uses sorted keys, ASCII escaping,
compact separators and no NaN. One entry per CMT ID; no retarget/delete.

Config: priority high/normal/low (normal default), enabled true, optional positive
target cents, restock_enabled false, at least one rule; max age default 86400,
range 1..604800. Money bounded to 1000000000 cents per field, positive target/unit,
shipping >=0, exact integers only. Request token ASCII token 1..128; revisions
positive bounded integers; add expected revision 0, updates CAS exact revision.
Atomic immutable revision plus current pointer plus replay record in BEGIN
IMMEDIATE. Canonical command includes action, target, precondition and complete
effective config; old replay returns original operation without reverting current.

Separate synthetic sample v1, provenance synthetic, EUR, explicit current/prior
and as_of; offset timestamps normalize UTC. No sample/result persistence. Reject
invalid identity/context/order/future before disabled SKIPPED. Freshness inclusive
0..max_age_seconds; current freshness before stock, previous freshness only for
restock toward AVAILABLE. Per-rule reasons and OR aggregate. Pure evaluator has
no SQLite/network/clock. Public Python boundaries revalidate objects.

Separate CMTW/schema1 STRICT storage, exact inventory/owner/index/trigger checks,
deep history/request/current consistency. Explicit init. Keyset list by priority
then watch_id, history ascending revision; cursors bind filters. Pages 100 default,
1000 maximum, 1 MiB cap. Shared total budget 2 seconds default, 5 maximum.
Consistent backup, exclusive new-destination restore validated before exposure;
reuse trusted-directory inode/sidecar protection. No distributed atomicity.

All ten installed-process harnesses and existing four CI jobs remain mandatory.
No product network calls, live gate, real prices, capture/journal/outbox/delivery
mutations or schema/identity changes. P2/P6a/retail Discovery BLOCKED; TD001..005
OPEN. No readiness until exact-candidate checks and independent reviews pass.
