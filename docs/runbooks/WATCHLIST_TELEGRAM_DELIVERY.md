# P8d proposed operating, recovery and qualification runbook

Status: PROPOSED, 2026-10-30. Gate B design review target. P8d commands below
describe the frozen implementation target; they do not exist yet and were NOT
executed in Gate A/B. No product writer/schema/definitive identity implementation
is authorized before Phase Lead design acceptance. This runbook gives no live
authorization. [API](../data-contracts/WATCHLIST_TELEGRAM_DELIVERY_V1.md) and
[storage](../data-contracts/WATCHLIST_TELEGRAM_DELIVERY_STORAGE_V1.md) define exact
arguments, canonical fields, failures and budgets.

## Preconditions and offline setup

Use one designated active ledger, trusted private directories/ACLs, adequate
disk/recovery headroom and maintained UTC. Pin an accepted candidate HEAD/tree
and install its built wheel in a separate environment outside source. Preserve
the original P5a Watchlist, P5b journal, P8c outbox, complete MANIFEST_V1 and
earlier delivery ledgers. Never copy a restored/cloned ledger into live service.

The eventual thirteenth smoke scripts/watchlist_telegram_delivery_smoke.py must
construct originals through their normal accepted APIs: five explicit synthetic
checkpoints and four genuine per-rule signals, then original P8c enqueue with a
chosen local alias. It must select one walt1_ explicitly and use fake transport
only. The twelve existing harnesses remain intact. No caller-created binding,
hash, DTO, arbitrary text or relabelled real observation is an origin fixture.
This setup script is a future implementation deliverable, not an existing file
or an executed result in this design handoff.

For operator commands below, resolve and privately retain four different safe
absolute DB paths and one manifest file. Local PowerShell variables are
$p8dLedger, $p8dWatchlist, $p8dJournal, $p8dOutbox, $p8dManifest,
$p8dAlias and $p8dAlert. These are operator-supplied paths/IDs, not presumed
existing files. Confirm each exists/owner matches except the explicitly new
ledger initialization destination. Use a new alias distinct from P8b's historical
qualification route. Never paste private IDs or credentials into chat/PR.

The following is the future offline command sequence. Stop on any nonzero exit.
Keep transcripts, preview text, route IDs and ledger private.

~~~powershell
cmt watchlist-telegram-delivery init --ledger-db $p8dLedger --timeout 5
cmt watchlist-telegram-delivery destination-add --ledger-db $p8dLedger --alias $p8dAlias --bot-id $env:CMT_GATE_BOT_ID --chat-id $env:CMT_GATE_CHAT_ID --operator-private-owned --timeout 5
cmt watchlist-alert-outbox verify --outbox-db $p8dOutbox --timeout 5
cmt watchlist-alert-outbox recompute --outbox-db $p8dOutbox --watchlist-db $p8dWatchlist --journal-db $p8dJournal --manifest $p8dManifest --alert-id $p8dAlert --timeout 5
cmt watchlist-alert-outbox preview --outbox-db $p8dOutbox --alert-id $p8dAlert --timeout 5
~~~

Bot/chat IDs above are local operator configuration, not secrets to ask for in
chat and not evidence of ownership by themselves. Route registration requires
explicit ownership attestation and does not contact Telegram. New destination
is unvalidated; a future authorized destination-validate is required before
send. No token is required by any offline command. Repeated identical route
registration replays; changed bot/chat/ownership under an alias conflicts.

## Review and specific historical acknowledgement

Read the exact private original preview, including SYNTHETIC — DEMONSTRATION ONLY
and historical revision framing. It represents neither present preferences nor
current real stock/price. Run the proposed redacted review:

~~~powershell
$p8dReviewEnvelope = cmt watchlist-telegram-delivery review --ledger-db $p8dLedger --watchlist-db $p8dWatchlist --journal-db $p8dJournal --outbox-db $p8dOutbox --manifest $p8dManifest --alert-id $p8dAlert --alias $p8dAlias --timeout 5 | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw 'Review failed; stop' }
$p8dReview = $p8dReviewEnvelope.review
~~~

The review contains the API's exact binding and commitments, no message, private
route IDs or raw evidence. Inspect alert/signal/watch/revision/message/evidence/
route commitments against the private local preview and route. Do not pipe a
fresh review blindly into acknowledgement: the operator must review this exact
historical selection. It cannot grant future generic sending consent.

The proposed prepare command requires the phrase plus every selected commitment:

~~~powershell
cmt watchlist-telegram-delivery prepare --ledger-db $p8dLedger --watchlist-db $p8dWatchlist --journal-db $p8dJournal --outbox-db $p8dOutbox --manifest $p8dManifest --alert-id $p8dAlert --alias $p8dAlias --acknowledge-historical-demonstration SYNTHETIC_HISTORICAL_DEMONSTRATION --expected-signal-id $p8dReview.signal_id --expected-revision $p8dReview.revision --expected-message-sha256 $p8dReview.message_sha256 --expected-evidence-sha256 $p8dReview.evidence_sha256 --expected-route-sha256 $p8dReview.route_sha256 --expected-binding-sha256 $p8dReview.binding_sha256 --timeout 5
~~~

Capture returned delivery.delivery_id privately as $p8dDelivery. A different route,
message, evidence, revision or binding fails before persistence. Identical
prepare is replay of the first immutable preparation; a second alias or route
for the same signal conflicts. Semantically equivalent source copies are allowed;
operational P8c first_prepared_at does not change the semantic source binding.

~~~powershell
cmt watchlist-telegram-delivery get --ledger-db $p8dLedger --delivery-id $p8dDelivery --timeout 5
cmt watchlist-telegram-delivery verify --ledger-db $p8dLedger --timeout 5
cmt watchlist-telegram-delivery recompute --ledger-db $p8dLedger --delivery-id $p8dDelivery --watchlist-db $p8dWatchlist --journal-db $p8dJournal --outbox-db $p8dOutbox --manifest $p8dManifest --timeout 5
~~~

A local verify is not original authenticity. If originals are missing or changed,
recompute/unconfirmed send must fail. No new alias, latest revision, rerendered
message or fresh deadline may make the stored preparation eligible.

## Offline falsification and candidate readiness

Before requesting live permission, run full format/lint/types/pytest/coverage/
build/outside-source install/audit/secret gates, all13 fake harnesses and final
four CI jobs. Independent nonauthor QA and a distinct final REVIEWER must publish
their own probes/results on the exact candidate HEAD/tree. Preserve failed
attempts. Include actual two-process races, crash barriers, global watch/revision
incompatibility, clock/deadline/ENOSPC/sidecar/publication failures, token/import/
socket denial, old-backup unknown-delivery quarantine and postreceipt replay.

Use denied token lookup/Telegram import/socket sentinels for every offline
command and help/invalid args. Fake response success is only synthetic test
evidence. No real destination validation or send may be hidden in a test,
smoke, CI, environment setup, specialist probe or review.

## Separate AC-WT20 authorization and evidence reservation

This section is INERT until offline implementation, exact-candidate QA/REVIEWER,
draft PR and four jobs are complete AND explicit operator/Orchestrator permission
has been recorded for this exact historical synthetic alert and private route.
P8b-T17 and old credentials grant no permission.

Prepare a sanitized preflight dossier containing exact candidate HEAD/tree,
signal/alert/delivery/watch/revision, message/evidence/route/binding/consent
digests, operator acknowledgement, one designated private unquarantined ledger,
verified originals, expected calls, failure stop rules and private evidence
reservation location. The private copy may hold the route and receipt; the public
projection must not. Do not request token/chat IDs in chat.

Before the first network call, the later qualification wrapper must exclusively
reserve durable per-qualification evidence with cumulative counters and candidate
identity. Reserve conservative request upper bounds durably before each narrow transport
method: validate_destination reserves2 metadata requests, validate_bot reserves1,
and send reserves1 sendMessage attempt. Counts never decrease or reset after
failure/restart. Refuse a used send reservation even if HTTP may not have begun.
The unchanged supervised transport exposes no actual per-HTTP callback: failed
method request counts are unknown but bounded by these reservations. Label
instrumented method invocations and request upper bounds separately; only a
successful validated completion establishes its expected request count. Do not
patch worker internals, change P8b transport, or invent packet observation.
The wrapper is a required future Lead-owned implementation artifact; it has not
been created or executed in this design stage. This instrumentation proves a
conservative cap, not independent packet capture or proof of human reading.

Hard qualification limits: at most8 getMe/getChat combined, at most1 real
sendMessage ATTEMPT total, even if failed,429,timeout or uncertain. A normal
sequence needs2 metadata calls for destination validation and1 getMe before
send. No automatic retry or additional send under the product's max3 feature.
Any extra attempt requires a new explicit operator and Orchestrator decision.

ONLY under that separate authority, inject CMT_TELEGRAM_BOT_TOKEN locally from
protected secret storage, not arguments/files/transcripts/chat. The approved
wrapper then invokes the following target operations while accounting for calls:

~~~powershell
cmt watchlist-telegram-delivery destination-validate --ledger-db $p8dLedger --alias $p8dAlias --timeout 30
cmt watchlist-telegram-delivery send --ledger-db $p8dLedger --delivery-id $p8dDelivery --watchlist-db $p8dWatchlist --journal-db $p8dJournal --outbox-db $p8dOutbox --manifest $p8dManifest --timeout 30
~~~

Do not bypass wrapper reservation by running these target commands manually in
qualification. The wrapper must stop after the sole send attempt regardless of
its outcome. Provider accepted receipt plus durable confirmed state is required.
An error after claim may still mean remote acceptance; no new send is authorized.

After successful confirmation, close/reopen ledger, remove the token from that
process and spawn a separate replay process with token lookup, Telegram import
and sockets actively denied. The future command requires only the ledger and ID:

~~~powershell
cmt watchlist-telegram-delivery send --ledger-db $p8dLedger --delivery-id $p8dDelivery --timeout 5
~~~

This must return confirmed replay with unchanged one-attempt history and zero
new metadata/send calls; no original paths need remain available. Confirmed
replay still refuses a quarantined ledger. Verify source bytes unchanged and
ledger never restored/quarantined. QA/REVIEWER inspect sanitized evidence read-only
without more calls. Report actual receipt/counters separately from any human
observation. Failure to authorize/complete this gate is BLOCKED - LIVE_UNVERIFIED.

## Failure, clock and recovery decisions

| Durable state / condition | Required operator action |
| --- | --- |
| ready / rejected before claim | Inspect category and originals/consent/route/budget; verify zero new claims/send. Never infer live permission from fixing configuration. |
| in_flight | Preserve DB/sidecars and worker evidence. Treat possible acceptance as unresolved; no automatic expiry/retry. |
| uncertain | No resend/force/reset. Preserve evidence and escalate reconciliation to a later Orchestrator contract. |
| retryable | Only explicit valid429; wait until stored not_before, then a separate manual action, max3 lifetime attempts. Qualification still allows only its one total send. |
| permanent_failure | Terminal; no route overwrite or automatic retry under this signal. |
| confirmed | Verified local replay only; no provider/original/token requirement, no claim increment. |
| clock rollback before claim | Refuse; inspect maintained UTC without editing stored timestamps. |
| clock rollback after claim | Conservative uncertain/clock_skew with explicit high-water timestamp clamp if persistence succeeds, otherwise blocked in_flight. |
| result commit succeeded but stdout failed | Verify/get/replay local state; never overwrite a durable terminal result as uncertain. |
| quarantine | All send commands blocked, including replay and records absent from the backup. Reads and offline preparations do not lift it. |

For recovery, first establish actual worker quiescence: stop all relevant
application processes through controlled shutdown, verify their supervised
workers exited, retain process/claim evidence, and confirm no outstanding network
worker can continue. A timeout/lease or boolean alone does not establish this.
Only then use the proposed explicit recovery; it fences the active attempt and
records uncertain, never ready:

~~~powershell
cmt watchlist-telegram-delivery recover --ledger-db $p8dLedger --delivery-id $p8dDelivery --worker-quiesced --timeout 5
~~~

The ledger high-water tracks event times, not future retry eligibility
not_before or source/provider dates. A claim privately retains the route
validation timestamp used at claim time; later successful revalidation of the
same immutable route does not invalidate older claims.
A wrong/stale attempt owner cannot finalize after recovery. If quiescence cannot
be established or storage fails, keep in_flight and escalate; do not force.

## Backup, restore and permanent quarantine

Quiesce relevant local writes, preserve source/sidecars and verify. Supply only
new exclusive safe destinations, here operator-chosen $p8dBackup and
$p8dRestore. Never overwrite active/historical files or remove a foreign journal.

~~~powershell
cmt watchlist-telegram-delivery backup --ledger-db $p8dLedger --destination $p8dBackup --timeout 5
cmt watchlist-telegram-delivery restore --ledger-db $p8dBackup --destination $p8dRestore --timeout 5
cmt watchlist-telegram-delivery verify --ledger-db $p8dRestore --timeout 5
~~~

The source, copied provisional and independently reopened copy need fresh full
verification under one budget. Restore must durably set global quarantine before
publishing the new path and verify it after reopen. Even an empty backup must
block a delivery prepared later: missing rows cannot prove no earlier send.
Backup preserves existing quarantine; restore always sets it. There is no
unquarantine command and a raw file clone is not a safe alternative.

On hot-journal/owner/schema/FK/cell/inode/reparse/hardlink/sidecar mismatch,
ENOSPC/fsync/link/unlink failure or timeout, preserve the original failure and
foreign/residual evidence. Cleanup may unlink only demonstrably owned controlled
names under the frozen safety checks. Persistent filesystem refusal may leave
names for manual investigation. Never change permissions/remove unrelated
evidence to manufacture success. SQLite/filesystem/stdout deadlines are
cooperative, not hard real time; process-kill and QEMU do not certify Pi power loss.

TD-001..TD-005 and P5 global remain OPEN. No scheduler/bulk/arbitrary-text/new
source/market data/group/channel/commercial send or phase closure is implied.
