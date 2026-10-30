# P8d security and operability design review

Date: 2026-10-30. Role: SEC/SRE design specialist, /root/p8d_sec_design.
Status: source audit and proposed controls only; no product implementation,
test execution, QA gate, final REVIEWER result or phase acceptance is claimed.
Live qualification remains BLOCKED — LIVE_UNVERIFIED and is NOT AUTHORIZED.

MODEL PROFILE USED: requested/selected tool profile gpt-6.1-sol / high as
recorded by Lead in [ownership](P8D_OWNERSHIP.md). Effective backend and reasoning
are not independently verifiable. This specialist is a design author, not the
future independent QA or final REVIEWER.

## Review authority and reproducibility

The complete [Orchestrator contract](P8D_MANUAL_WATCHLIST_TELEGRAM_DELIVERY_CONTRACT.md)
prevails over the [engineering brief](P8D_CODEX_ENGINEERING_BRIEF.md).
Exclusive edit scope is this report; all source, historical documentation and
other specialist documents are read-only. No credentials were inspected, no
Telegram/HTTP/socket operation was run, no database was opened or modified and
no Git mutation was performed by this specialist.

Authorized product baseline:
9dda9fba0aa9646a67596657d4ae9a7088903808, tree
dfd0414242cff364aad6082411ae88aef728783e. Read-only local observations during
this audit: HEAD e7519257f435f8c5f8c709a070b9f6603f1ce25e, tree
120cabf48614c238e99570a4a05fa713ae32476d; its subject is
"docs(p8d): record authorized baseline, handoff and Gate A ownership".
git diff --name-only from the authorized baseline to that HEAD for src/tests/scripts
returned no names. Source anchors below refer to that unchanged product source.
Later documentation integration must pin its own final HEAD/tree.

Commands actually executed from C:/Projects/card-market-tracker-p8d were
read-only Get-Content, rg searches, Get-Command and these Git observations:

```powershell
git rev-parse HEAD
git rev-parse 'HEAD^{tree}'
git show -s --format='%h %s' HEAD
git diff --name-only 9dda9fba0aa9646a67596657d4ae9a7088903808 HEAD -- src tests scripts
rg -n 'APPLICATION_ID\s*=|OWNER\s*=|PRAGMA application_id|application_id\s*=|CHECK\(owner=' src docs -g '*.py' -g '*.sql' -g '*.md'
rg --files -g '*.sql' -g '*schema*.py'
rg -n 'CMTZ|434[Dd]545[Aa]|1129141338|watchlist-telegram-delivery' . -g '*.py' -g '*.sql' -g '*.md' -g '!uv.lock'
[int]0x434D545A
[System.Text.Encoding]::ASCII.GetString([byte[]](0x43,0x4D,0x54,0x5A))
```

The last two outputs were 1129141338 and CMTZ. No standalone .sql file was
listed. SQL is embedded in Python schema strings and documentation fences, so
the allocation search covered those sources too. Earlier attempted rg pathname
globs using Windows wildcard path components failed; successful corrected
searches used directory roots and -g filters, as above. No failed search is
treated as absence evidence.

## Findings and required design controls

Severity describes the impact if the hazard is introduced into P8d; these are
not claims that the unchanged earlier phases must be rewritten.

| ID / severity | Source-grounded finding | Required exact P8d control and falsification |
| --- | --- | --- |
| SEC-01 / High | P8b application.send returns confirmed replay before _preflight, and _claim_verified also checks confirmed before quarantine. Its replay additionally checks original paths. Blind reuse would violate the new global quarantine and original-free replay contract. [application.py lines277–300](../../src/card_market_tracker/telegram_delivery/application.py#L277), [storage.py line908](../../src/card_market_tracker/telegram_delivery/storage.py#L908). | P8d send must deep-verify the local ledger and inspect global quarantine before any replay/state branch. Healthy confirmed replay then requires only local binding/receipt, with no origin path, token, adapter or network requirement. Repeat this ordering under claim's write lock. Probe confirmed+quarantined and missing-delivery+quarantined with token/network denied. |
| SEC-02 / High | P8b _Budget.local gives each helper up to5s of the global remaining allowance. That does not cap the combined P8d origin stage to5s. [application.py line51](../../src/card_market_tracker/telegram_delivery/application.py#L51). | Use one immutable global monotonic deadline and one nonrenewable origin phase ceiling; all P8c/P5b callbacks and SQL progress handlers honor it. Reserve finalization time before bot/claim/send. Probe helpers that individually fit5s but cumulatively exceed5s: zero claim and zero send. |
| SEC-03 / High | P8b's private receipt checks content+instance but is reusable and not Budget-bound. P8c's receipt additionally consumes once and binds the exact Budget. [P8b line82](../../src/card_market_tracker/telegram_delivery/application.py#L82), [P8c line56](../../src/card_market_tracker/watchlist_alerts/application.py#L56). | P8d authority must bind exact instance, canonical full binding, operation/scope, source identities, route/consent, issuing Budget and immutable global deadline, with one-use consumption before opening writer. Reject fake type, copy/deepcopy, object mutation, second use, another operation, another Budget and expired authority. SQL rechecks all invariants; receipt is not authority against privileged Python. |
| SEC-04 / High | P8c _get_pair provides one consistent selected pair, while recompute independently admits the original journal/Watchlist. Separate get and evidence_get calls would allow a torn projection. None of four stores has a distributed snapshot. [storage.py line436](../../src/card_market_tracker/watchlist_alerts/storage.py#L436), [application.py line194](../../src/card_market_tracker/watchlist_alerts/application.py#L194). | Use the existing pair-consistent helper; full P8c verify, pair-before, original recompute, pair-after and exact projection equality under the single budget. Do not call enqueue or P8b prepare/send. Preserve immutable-original/trusted-directory assumptions; source substitution by privileged administrator remains outside authentication. |
| SEC-05 / High | RW-01 was a write-time/global-invariant failure: valid independent originals can disagree for one nominal immutable watch/revision. P8c now folds all retained entries under BEGIN IMMEDIATE before replay/conflict. [storage.py line369](../../src/card_market_tracker/watchlist_alerts/storage.py#L369), [line509](../../src/card_market_tracker/watchlist_alerts/storage.py#L509). | Full retained P8d fold before prepare/claim commit, global key (watch_id,revision), complete canonical entry equality and original-reconstructed digest. No partition by signal, alias, route, series or product. A second incompatible genuine origin must fail identity_conflict with byte-identical healthy ledger; preexisting contradiction must be storage_corrupt even on replay. |
| SEC-06 / High | Process timeout, death or recovery does not revoke an already issued HTTP effect. P8b uses durable attempt ownership/state CAS and uncertain-only recovery. [storage.py line961](../../src/card_market_tracker/telegram_delivery/storage.py#L961), [line1085](../../src/card_market_tracker/telegram_delivery/storage.py#L1085). | P8d uses independent unpredictable attempt and owner, durable in_flight commit before HTTP, exact owner+attempt+state CAS and no DB transaction during HTTP. Recovery requires real worker quiescence, sets uncertain only, and defeats late finishers. Lease expiration is never send permission. Probe two OS processes, stale owner, recovery/finish race and crash barriers. |
| SEC-07 / High | Typed TransportResult and Receipt are constructible Python DTOs. A caller/fake transport can fabricate confirmed, rate-limit or mismatched receipt values. The existing HTTP validator authenticates only a live provider response processed through the trusted adapter. [transport.py line42](../../src/card_market_tracker/telegram_delivery/transport.py#L42), [line193](../../src/card_market_tracker/telegram_delivery/transport.py#L193). | Narrow trusted adapter plus strict result-shape/type validation before finalization; reject bool-as-int, receipt on nonconfirmed, extra/missing receipt fields, route mismatch, invalid combinations. Confirm only validated trusted-provider acceptance plus durable local result. Fakes remain offline evidence, never live confirmation. |
| SEC-08 / High | Every old backup may omit a later delivery entirely. Per-row quarantine cannot cover that missing row. P8b quarantines staging before final restore exposure. [storage.py line1181](../../src/card_market_tracker/telegram_delivery/storage.py#L1181). | Global durable metadata quarantine on every restore, set and verified before destination publication and verified after reopen; no unquarantine/force path. It blocks send for known confirmed and newly prepared/previously absent deliveries. Raw file clones remain an operator single-authority risk; no cross-ledger dedup claim. |
| SEC-09 / Medium | Root CLI normally imports P8b CLI/application/transport; P8c has a special lazy parser that avoids that path. [cli.py line50](../../src/card_market_tracker/cli.py#L50), [line118](../../src/card_market_tracker/cli.py#L118), [line490](../../src/card_market_tracker/cli.py#L490). | Add lazy P8d routing; offline P8d package imports/help/errors/prepare/recompute must never import Telegram transport, instantiate an adapter, read token or open sockets. Keep P8c's fresh-process import denial tests intact. Test token access itself, not just missing token and zero sockets. |
| SEC-10 / Medium | UTC cooldown relies on trusted wall time; P8b refuses backwards finish timestamps, potentially leaving in_flight. [application.py line261](../../src/card_market_tracker/telegram_delivery/application.py#L261), [storage.py line961](../../src/card_market_tracker/telegram_delivery/storage.py#L961). | Freeze 27-byte UTC microsecond-Z grammar. Claim refuses now below ledger operational highwater, validated_at or updated_at. Postclaim rollback cannot produce confirmed/retryable: persist uncertain/clock_skew with explicit clamped operational timestamp if budget/storage permit, otherwise retain blocked in_flight. Provider accepted_at remains independent. Test before/after claim skew. |
| SEC-11 / Medium | The initial proposed storage prose said highwater dominates every retained operational timestamp; not_before is a future eligibility timestamp after valid429, so that definition would falsely reject a healthy ledger immediately. | Define highwater over event timestamps only: initialization, route registration/validation, prepare, claim, result and derived updated_at. Exclude not_before, source as_of/observed_at and provider accepted_at. Probe a valid429 with not_before>highwater: verify remains healthy, early claim refused and due claim allowed. |
| SEC-12 / Medium | Route revalidation advances current validated_at after historical claims. Comparing old claimed_at to the latest current route validation would falsely invalidate valid history; retaining only latest validation also loses the exact validation fact used by an old claim. | Freeze an immutable UTC27 route_validated_at snapshot on each claim, copied exactly from current route validation by claim INSERT guard. Historical fold checks registered_at<=snapshot<=claimed_at and snapshot<=current validated_at; current claim admission still checks latest validation. No full validation history table or route binding change is needed. Probe claim, later revalidation, healthy historical verify and tokenless confirmed replay. |

These controls were sent to the ARQ and DB design authors during preparation.
They address P8d reuse risks without changing accepted P8b/P8c source. A document
proposal is not proof of implementation, race safety or a passing gate.

## Actual accepted transport boundary and mapping limits

Reuse only [TelegramTransport and its types](../../src/card_market_tracker/telegram_delivery/transport.py)
through the new module's narrow port. Its public methods are
check_configuration, validate_bot(bot_id,timeout=15),
validate_destination(bot_id,chat_id,timeout=15), and
send(bot_id,chat_id,message_text,timeout=15)->TransportResult.
Timeout inputs are finite positive <=30; bot/chat IDs are exact positive
integers <=2^52-1; message is strict UTF-8 with1..4096 bytes.

TransportResult is a frozen dataclass with state, error_category, retry_after and
receipt. State is confirmed/retryable/permanent_failure/uncertain. Receipt
contains message_id, accepted_at, bot_id and chat_id; repr hides the IDs but is
not a publication-safe redaction mechanism. Do not log either DTO wholesale.

The validator checks critical fields and contradictory envelopes; it is not a
closed-key schema for every Telegram response property. Bounded unrelated
provider fields may be ignored, including names. No new P8d requirement should
claim the preserved P8b transport rejects all unknown Telegram keys.

| Actual observation at transport boundary | Actual output / exception | P8d durable consequence after claim |
| --- | --- | --- |
| 200, ok is True, valid positive message_id<=2^63-1/date1..253402300799, exact bot and is_bot=True, exact private chat, exact echoed text, forbidden alternate sender/business/guest fields absent | confirmed with Receipt; no error/retry | confirmed only after strict receipt/binding checks and atomic durable result commit |
| Strict rejection envelope: ok=False, integer error_code exactly HTTP status, no result, nonempty description<=4096UTF8 bytes; status429, object parameters, retry_after exact int1..86400, no migrate_to_chat_id | retryable/provider_rate_limit with retry_after | persist not_before from operational completion time; later manual invocation only; third lifetime claim becomes permanent_failure/retry_exhausted |
| Same strict rejection, other400..499 excluding408/409/425/429, parameters absent | permanent_failure/provider_rejection | permanent_failure; no retry |
| 408/409/425, 5xx, redirects, contradictory/malformed rejection | uncertain/provider_invalid, or DeliveryError handled below | uncertain; never reinterpret as safe retry |
| Invalid/truncated/oversized/duplicate-key/NaN/UTF8/depth/critical type response; invalid success, bot/chat/text/date/message mismatch | DeliveryError(provider_invalid) inside supervision, converted by send into uncertain | uncertain |
| DNS/connect/TLS/write/read/drip/worker/IPC failure or timeout inside supervised send | uncertain with fixed transport_timeout/transport_failure/provider_invalid category | uncertain |
| Invalid inputs/configuration checked before send's internal try | DeliveryError can escape | preclaim error creates no claim; after claim conservatively uncertain if persistence works, otherwise in_flight |
| Adapter exception, wrong result type or invalid field combination | not provider proof | uncertain if possible; never use invalid DTO to create retryable/confirmed |
| Provider-valid result followed by local DB/commit/output failure | HTTP result does not prove durable receipt | if durable result is already confirmed, subsequent read/replay discovers it; otherwise attempt uncertain fallback within remaining budget, or leave in_flight blocked |

Source: [_receipt](../../src/card_market_tracker/telegram_delivery/transport.py#L193),
[_perform](../../src/card_market_tracker/telegram_delivery/transport.py#L248),
[_supervise](../../src/card_market_tracker/telegram_delivery/transport.py#L308),
[send](../../src/card_market_tracker/telegram_delivery/transport.py#L386).
No automatic resend follows any row in this table. A response/exit error is not
proof the remote side had no effect. Receipt accepted_at is a provider Unix
timestamp, not market freshness or human reading evidence.

The HTTPS request uses only api.telegram.org:443 and allowed getMe/getChat/
sendMessage methods, verified default TLS, POST, debug0, no redirect/proxy
handling and no retries. send payload is exactly chat_id, frozen text and
link_preview_options.is_disabled=True, without parse_mode/entities/topic.
The token is read from CMT_TELEGRAM_BOT_TOKEN locally, authenticated URL is
constructed only in worker, and the token is not an argument or IPC field.
The worker sends only sanitized small JSON projection; raw response bodies and
exceptions do not cross to parent. _request caps body64KiB, validates framing;
strict parsing rejects duplicate keys/nonfinite values and depth>16.
Host process environment/debugger/core dump access is still a trusted-host
boundary, not solved by redaction.

## Deadline composition and persistence reserve

Freeze one Budget at CLI entry before argument/input parsing, with immutable
global deadline D. Local operations default2/max5s; destination validation/send
default15/max30s. API-created budgets begin at API entry. No helper renews D.
Carry the same Budget through source admission, SQL busy/progress callbacks,
canonicalization, projection and final pre-stdout validation.

Coordinated design proposal: R=min(0.5,total_timeout/5) seconds. Preclaim work,
bot metadata, claim and send receive only allowance before D-R. Finalization,
bounded response formatting and sanitized completion use remaining time up to D.
Do not reserve a fresh R at each helper or grant a new timeout on fallback.

The send origin phase starts once, with O=min(D-R,origin_start+5s). The SAME
Budget instance exposes O as its temporary effective deadline to every original
helper, including P8c.verify/_get_pair/recompute and P5b verification. remaining()
and progress() must both honor O. The scope cannot be reentered to refresh its
start, and receipt checks still bind the immutable D and original Budget.
Removing O after successful origin admission is an explicit phase transition,
not deadline renewal. No sealed authority can be created from an unfinished or
expired origin scope.

validate_destination makes getMe then getChat under one supervised timeout;
validate_bot makes getMe; send makes one sendMessage. Pass shared remaining
allowance each time, never default15 to consecutive calls. Before claim require
positive usable send allowance after reserve. After claim, expired allowance
produces no HTTP call and a conservative uncertain/blocking result.

_supervise bounds the joined worker and terminates/kills it, with up to two
0.1s cleanup joins in finally. Process startup/termination and kernel/device/
SQLite/stdout calls are not hard realtime guarantees. R includes this cleanup;
very small configured budgets can leave no useful finalization window. Safety
then means blocked in_flight rather than inventing more time or retrying. A
bounded finalization reserve is a conservative allowance, not a guarantee of
durability during ENOSPC, scheduler starvation or an unreturning syscall.

Highwater refers only to event timestamps: init, route registration/validation,
prepare, claim, result completion and derived state.updated_at. Future
not_before is an eligibility boundary, not a completed event; it may exceed
highwater after a valid429 without corruption. Source observed_at/as_of and
provider accepted_at are separate clocks and excluded from highwater.

A route's current validated_at may advance after old claims. Each new claim
must copy the exact current validation time into immutable route_validated_at;
SQL admission checks equality and the current latest validation. Later deep
folds instead require registered_at<=snapshot<=claimed_at and
snapshot<=current validated_at. Old claimed_at is never required to dominate
a later revalidation. This adds one claim field, no route-identity/digest change
or full validation-history table.

## Consent, original authority and privacy

The accepted P8c preview alias is not destination consent. Before prepare,
operator reviews the exact historical preview privately and acknowledges
SYNTHETIC — DEMONSTRATION ONLY / historical-not-current meaning. The API must
require the concrete content-and-route acknowledgement frozen by ARQ, including
alert_id/signal_id/watch revision/message digest/evidence digest/route digest.
A generic --yes, historical enabled preference or P8b-T17 permission is
insufficient. Route registration separately requires explicit private ownership
attestation and immutable provider/alias/bot/chat binding; validation refreshes
validated_at without changing identity.

Admission must freeze the complete selected evidence, intent, exact message
UTF8 bytes, P5a full entry/configuration and identities, route and consent.
Compare canonical bytes with strict types; bool/int equality is insufficient.
Require actual pending/offline_preview/watchlist_synthetic_alert_v1/synthetic/
WATCHLIST_RULE_ENTERED_MATCH. Both historical snapshots must equal the exact
original P5a revision and complete explicit manifest. No latest fallback,
clock-based reinterpretation, rerender or arbitrary caller text/hash is allowed.

P8c _get_pair already meets selected pair consistency, so the audit found no
need to widen source interfaces. It does not by itself full-fold the outbox;
call accepted verify as the additional full-history health check. P8c recompute
reconstructs both snapshots/results/signals through the accepted original route.
Pair-before/recompute/pair-after equality detects ordinary changes, not a
privileged coherent replacement of all authorities.

Store sensitive bot/chat/receipt route information only in private ledger.
Ordinary CLI output admits only its closed safe DTO, including local IDs and
content commitments; completion logs admit only validated delivery/attempt IDs,
fixed categories, counts, state and bounded duration, without hashes or source IDs. Exclude token, owner fence, bot/chat/
message IDs, full receipt, message/evidence/preferences/samples/amounts,
authenticated URL, raw exception/SQL and personal paths. Aliases may themselves
be operator-sensitive; do not add them to completion logs. Content/digests are
commitments, not cryptographic authentication or proof of a human identity.

Fresh-process tests must install an import finder denying
card_market_tracker.telegram_delivery for all offline P8d operations, help,
invalid arguments and package imports, plus deny sockets and token-environment
access. The P8c fixture at
[test_watchlist_alert_cli.py line266](../../tests/test_watchlist_alert_cli.py#L266)
already denies transport imports/socket calls, but does not prove token-access
denial. Add explicit sentinels for token and private IDs and assert none reach
stdout/stderr/logs/IPC fixtures. Do not inspect a real secret to test redaction.

## Single ledger, fencing and restore operations

The identity is provider+genuine signal, not alert alias. UNIQUE(provider,signal_id)
and first immutable binding prevent alternate preview/route duplication in this
ledger. New actual signal episode permits a new identity. Consistent copies of
origins are equivalent; copied ledgers are independent authorities and can each
send. Operate exactly one designated writable ledger. No exactly-once or
cross-copy dedup promise is supportable with Telegram sendMessage and local
SQLite alone.

Coordinated attempt grammar: wtat1_ plus64lowerhex, and independent64lowerhex
owner fence, each from secrets.token_hex(32). Owner is internal and never CLI
authority. BEGIN IMMEDIATE repeats healthy full fold, quarantine, route/
consent/binding, global entry invariant, state/cooldown/count/skew checks.
Only ready or due retryable with count<3 can append a contiguous claim and
transition in_flight. No HTTP until commit succeeds. Each invocation may call
sendMessage at most once, even if postclaim pre-network steps fail.

Finish requires exact delivery/current attempt/current owner/state=in_flight,
with atomic append-only result and state update. Rowcount !=1 is stale_attempt.
Recovery is explicit worker-quiesced and can append only uncertain/recovered
for current in_flight; stale finisher then fails CAS. A SQLite fence cannot
cancel an HTTP worker already executing: false quiescence attestation may race a
real send, which is why recovery never reopens eligibility.

Backup must use a consistent verified snapshot. Restore publishes only a
globally quarantined candidate after independent source, copy and reopened-copy
verification with the same Budget, durable quarantine and fsync. Backup preserves
quarantine; restore always sets it, including empty ledgers. Recovered files
remain inspectable/preparable but every send is blocked; unknown post-backup
signals are covered by metadata, not row enumeration.

Preserve accepted owner/header-before-writable-open checks, exact inventory,
SQL typeof/byte guards, FK/STRICT/triggers, inode/link/reparse/sidecar guards,
exclusive provisional reservation and safe post-link compensation. Reopen
verification cannot reuse source verification authority. Never delete another
process's journal, foreign file or failed-publication recovery evidence.
Persistent filesystem refusal may leave controlled names for manual inspection.
Trusted ancestors/ACLs, one active authority, immutable originals and available
disk are assumptions. TD-001..005 remain OPEN; process-kill/QEMU evidence cannot
certify native Pi power loss, privileged tampering or hard realtime deadlines.

## Allocation audit: CMTZ

Observed source allocations are distinct:

| ASCII / hexadecimal | Owner | Literal source |
| --- | --- | --- |
| CMT1 /0x434D5431 | card-market-tracker | persistence/schema.py lines8,10 |
| CMTA /0x434D5441 | card-market-tracker.alert-outbox | alerts/schema.py lines6,8 |
| CMTD /0x434D5444 | card-market-tracker.telegram-delivery | telegram_delivery/schema.py lines6,8 |
| CMTJ /0x434D544A | card-market-tracker.discovery-journal | discovery/journal_schema.py lines6,8 |
| CMTQ /0x434D5451 | card-market-tracker.watchlist-journal | watchlist_journal/schema.py lines6,8 |
| CMTW /0x434D5457 | card-market-tracker.watchlist | watchlist/schema.py lines6,8 |
| CMTY /0x434D5459 | card-market-tracker.watchlist-alert-outbox | watchlist_alerts/schema.py lines3,5 |
| Proposed CMTZ /0x434D545A /1129141338 | card-market-tracker.watchlist-telegram-delivery | P8d new authority/schema1 only |

All prior writers' PRAGMA application_id assignments reference their own schema
constants. Embedded owner CHECK strings agree with those owners. CMTZ/new owner
appeared only in P8d preparation documents at the time of the collision search;
no existing source allocation was found. This supports documentary reservation
in ADR-0015; repeat the source+SQL inventory against the final design/implementation
candidate. No actual prior database inventory was inspected and none may be
migrated to this authority.

## First failure-first probes and eventual runbook requirements

These are required future probes, NOT executed results. Future QA and final
REVIEWER must author independent falsification code/oracles on final HEAD/tree.

1. Genuine separate P5a→P5b→P8c bundles, same watch/revision but incompatible
   full configuration: second prepare and competing processes reject without
   changing healthy ledger; verify and backup still work. Semantically identical
   independent originals coexist; another revision/product remains independent.
   Derive expectations without reusing production identity helpers.
2. Counterfeit/copied/mutated/reused/wrong-operation/wrong-Budget/expired private
   admission and forged transport receipts: no writer authority. Missing/mutated
   original or changed selected pair before claim: zero claims/send calls.
3. Confirmed replay after fresh process reopen with no token, unavailable
   originals, denied transport import/socket: replay and unchanged one-attempt
   history. Repeat against quarantined confirmed/empty/unknown-delivery restore:
   send_quarantined and zero token/network work.
4. Two actual OS sender processes synchronized at claim boundary: durable
   in_flight observable before fake HTTP; only one sender. Kill before/after
   claim, during response, before/after receipt commit. Expired lease/dead process
   never automatically resends. Recovery/late finisher/wrong owner cannot erase
   newer history or release uncertain.
5. Outcome matrix: valid429 boundaries1/86400 and cooldown/exact third cap;
   bool/zero/negative/overflow retry_after; permanent4xx versus408/409/425;
   5xx/redirect/duplicate/truncated/malformed JSON; mismatched bot/chat/text/
   provider date; TLS/network failure; local ENOSPC/locked/commit failure.
   Uncertain never becomes retryable. Preserve durable confirmed if output alone
   failed; do not fabricate uncertain over an existing terminal result.
6. Shared budget probes across parsing/canonicalization/pair reads/full folds/
   metadata/claim/HTTP/finalization/stdout; aggregate-original>5s despite
   individually fast helpers; real spawned fake DNS/read/drip stalls and cleanup
   overhead; budget expiry creates no fresh deadline or send permission.
7. Restore older empty backup after a later confirmed delivery in original:
   newly prepare that absent signal into restore, then send is still globally
   blocked. Inject publication/link/unlink/fsync failures, foreign hot journals,
   oversized guarded SQL cells, coherently rehashed semantic corruption and
   hostile path/owner/inventory/FK changes. Preserve all source DB bytes and
   unrelated files/sidecars.
8. Installed fresh-process import/help/error/privacy probes plus thirteenth
   offline full five-checkpoint/four-signal harness across wheel/Compose/AMD64/
   ARM64-QEMU. Existing12 harnesses and complete suite remain required. Fake
   transport and synthetic sentinels only; no production token in CI.

The future [P8d runbook](../runbooks/WATCHLIST_TELEGRAM_DELIVERY.md)
must make these steps executable using the frozen CLI, not pseudocode accepted
as test evidence: pin candidate HEAD/tree and installed wheel, build genuine
offline originals, select exact walt1_, privately review exact preview/digests,
register/attest immutable private route without publishing IDs, provide the
specific historical content+route acknowledgement, prepare/verify/recompute,
run all offline gates, and prepare sanitized qualification evidence reservation
before requesting separate live authorization. Do not copy a P8b qualification
wrapper as new permission.

AC-WT20 later requires explicit operator/Orchestrator authorization for this
exact candidate/alert/signal/delivery/message/evidence/route, recorded privately
with date. The total qualification limit is <=8 getMe/getChat and <=1
sendMessage attempt across all processes and failures. Reserve durable wrapper
evidence before network. The unchanged transport exposes narrow method entries,
so reserve conservative metadata upper bounds (destination validation2, bot
validation1) and one send invocation before dispatch. They are exact on validated
successful completion and upper bounds on failure; do not claim observed HTTP
request counts or independent packet observation. This follows the accepted
scripts/telegram_live_gate.py lines38-60 instrumentation limit without widening
P8b transport. A normal sequence uses2 metadata calls for route validation,
1 getMe before send and1 sendMessage, leaving no reason to spend the cap.

A valid429, failed or ambiguous single qualification attempt consumes its sole
send permission. Product retryable/max3 does not authorize another live attempt.
Stop dependent live work and seek a new explicit decision; no retry loop.
After a confirmed receipt, close/reopen, remove token and deny network in a
different process; require replay, zero further method calls and one preserved
attempt. Verify original bytes unchanged and ledger neither restored nor
quarantined. Publish only sanitized attestation/digests/counts/candidate identity,
never token, bot/chat/message IDs, full text/HTTP bodies/paths or raw errors.
Human observation is separate from API acceptance.

The runbook must also show ready/preclaim failure handling, blocked in_flight
and actual worker-quiescence establishment, uncertain/no-resend escalation,
manual429 cooldown outside qualification, immutable permanent failure, verified
backup/new-path restore/global quarantine and preservation of sidecar evidence.
No force, bulk, arbitrary-text, uncertain reset or quarantine-lift command.

## Cross-document design review disposition

Read-only cross-review covered the complete proposed API/storage documents,
ADR-0015, Lead runbook and additive threat/logging/testing/quality sections.
The following concrete inconsistencies were reported to their exclusive authors
and corrected in the observed drafts: source operational first_prepared_at was
removed from immutable semantic delivery storage; route cap aligned to2048
bytes; normalized permanent category aligned to provider_rejection; SQL admitted
all closed uncertain categories, including token_configuration,
local_commit_failed and deadline_exceeded; recovery now uses clock_skew on UTC
rollback and recovered otherwise; runbook review DTO access was corrected to the
API's flat review object. The full registry fold explicitly rejects orphan
entries/state/claims/results. Equivalent original copies remain admissible.

Lead agreed qualification instrumentation must reserve conservative request
upper bounds before narrow method calls, distinguish failed-call bounds from
validated-success counts and avoid changing P8b transport or claiming packet
observation. API/DDL and the runbook preserve no-send authority at this stage.

A later Lead chronology review identified SEC-11/SEC-12 after the initial
cross-review. Lead authorized the event-time highwater clarification and immutable
per-claim validation snapshot correction in the documentary design. Fresh readback confirmed the immutable UTC27 snapshot, exact current-validation
INSERT equality, historical snapshot bounds and event-only watermark exclusions
in API/DDL/prose/runbook. The revised author memory probe now reports35 invalid
SQL actions rejected, including stale/future snapshots and snapshot mutation,
with old claims remaining valid after route revalidation and future cooldown
not advancing highwater. This is attributed author evidence, not a probe run
by this specialist. No unresolved critical security/operability design
contradiction was identified in this refreshed static document snapshot.
No review establishes that future code enforces the controls or that a gate passes.
DB's section9 reports author in-memory documentary
SQL probes with complete source/output. Those are attributed author evidence;
this specialist did not run them or claim independent runtime verification.

Reviewed documentation snapshot SHA256 values (not this report's hash, avoiding
a self-reference; later Lead edits require readback/new snapshot as applicable):

| Document | SHA256 |
| --- | --- |
| WATCHLIST_TELEGRAM_DELIVERY_V1.md | a444b87af415539122ad20c726f3083256abce458b2c2b420dad9fcfcd737904 |
| WATCHLIST_TELEGRAM_DELIVERY_STORAGE_V1.md | 0a9be49cb68e5c83885d94d639351e35074de6bc3570200a5ab6ec65b56f2df0 |
| 0015-manual-watchlist-telegram-delivery.md | 34cb34a1b38ac35c5be33ff331c7f8144bea6045265fffba516be1971860cf36 |
| WATCHLIST_TELEGRAM_DELIVERY.md | c68178f6d7257867b7d0af3c3423fede5f3a2343ccc2f72ac3a17df4e5040562 |

Hashes were obtained with Get-FileHash -Algorithm SHA256 on the exact local
paths, without product imports, database operations or network. Lead pins the
final integrated documentation HEAD/tree; these per-file snapshots do not
substitute for that final commit identity.

## Handoff

This report supplies source-backed hazards, mitigation requirements and future
probe/runbook acceptance inputs. It does not accept Gates A/B or authorize
implementation/live effects. ARQ/DB design authors must align their exact API,
DDL/CAS, Budget/skew and privacy rules with these controls before Phase Lead
design review. Lead must reconcile shared ADR/runbook/threat/logging/quality
documents, then pin the integrated documentation HEAD/tree. This specialist
hands ownership of this report back to Engineering Lead on completion.
