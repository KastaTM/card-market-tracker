# WATCHLIST_TELEGRAM_DELIVERY_V1 — proposed engineering API freeze

**Status: PROPOSED — NOT ACCEPTED. Date: 2026-10-30.**
Gate A/B documentation only; no writer/schema/definitive identity implementation,
implementation gate PASS, real Telegram authorization, phase acceptance or closure.
Authority: [P8d opening contract](../phases/P8D_MANUAL_WATCHLIST_TELEGRAM_DELIVERY_CONTRACT.md),
[brief](../phases/P8D_CODEX_ENGINEERING_BRIEF.md),
[ownership](../phases/P8D_OWNERSHIP.md). Proposed persistence is specified in
[storage v1](WATCHLIST_TELEGRAM_DELIVERY_STORAGE_V1.md) and
[ADR-0015](../adr/0015-manual-watchlist-telegram-delivery.md).
Phase Lead must accept the complete design before Gate C. Only Orchestrator
accepts a candidate, authorizes integration and closes a phase.

ARQ/BE specialist model profile: requested and selected tool arguments
GPT-6.1 Sol / High (gpt-6.1-sol, reasoning_effort=high); effective backend and
reasoning are not independently verifiable. This is author design, not QA.

## 1. Scope and public Python boundary

The new watchlist_delivery authority delivers one exact historical synthetic P8c
message to one registered private Telegram route. It never changes P5a, P5b,
P8c, P8b or other accepted source schemas, writers, identities, rendering or
admission. No scheduler, polling, bulk selection, arbitrary text, real market
data, migration, web interface, current preference consent or global exactly-once
claim. Live Telegram remains NOT AUTHORIZED at this design stage.

All public paths are pathlib.Path. Caller selections/manifest/flags are object
until strictly validated. Every operation returns the same redacted dict DTO as
its CLI response. Public operations and argument order:

    initialize(ledger_db, *, timeout=2.0)
    destination_add(ledger_db, alias, bot_id, chat_id,
                    *, operator_private_owned=False, timeout=2.0)
    destination_validate(ledger_db, alias, *, timeout=15.0)
    review(ledger_db, watchlist_db, journal_db, outbox_db, manifest,
           alert_id, alias, *, timeout=2.0)
    prepare(ledger_db, watchlist_db, journal_db, outbox_db, manifest,
            alert_id, alias, *, acknowledgement, expected_signal_id,
            expected_revision, expected_message_sha256, expected_evidence_sha256,
            expected_route_sha256, expected_binding_sha256, timeout=2.0)
    send(ledger_db, delivery_id, *, watchlist_db=None, journal_db=None,
         outbox_db=None, manifest=None, timeout=15.0)
    get(ledger_db, delivery_id, *, timeout=2.0)
    list_deliveries(ledger_db, *, state=None, limit=100, cursor=None, timeout=2.0)
    verify(ledger_db, *, timeout=2.0)
    recompute(ledger_db, watchlist_db, journal_db, outbox_db, manifest,
              delivery_id, *, timeout=2.0)
    recover(ledger_db, delivery_id, *, worker_quiesced=False, timeout=2.0)
    backup(ledger_db, destination, *, timeout=2.0)
    restore(ledger_db, destination, *, timeout=2.0)

Only explicit initialize creates a ledger. All other DB paths must exist, have
the correct exact owner/header/schema and pass established path/inode/sidecar
safety. Prepare/review/recompute and unconfirmed send require four pairwise
distinct DB files by normalized path and samefile identity. MANIFEST_V1 is a
complete raw object, detached canonically before callbacks and reparsed with
the accepted parser, including unrelated entities/bindings. A manifest path is
a CLI input only, never a serialized Python authority. No JSON DTO, typed
dataclass, caller hash, saved preview or verified=true grants admission.

Send permits omitted original arguments only to support confirmed replay.
Unconfirmed send requires all three original paths and the complete manifest.
CLI delays reading --manifest until after the locally verified replay decision.
Confirmed replay requires neither originals nor token to exist; supplied source
paths/manifest are not opened on that path. It always opens/verifies the ledger
and checks global quarantine BEFORE returning replay. Quarantine blocks every
send invocation, including confirmed replay.

Production transport selection is internal. Tests may inject a narrow internal
port; there is no CLI transport selector, URL or arbitrary-text option.

## 2. Exact original-backed admission

Every review, prepare (including replay), recompute and unconfirmed send:

1. Validate selections, four safe distinct paths, owners/versions and the
   complete detached manifest. Load immutable operator-attested route; require
   its destination_key equals the selected P8c destination_key. A route need
   not yet have validated_at to review/prepare offline; send requires it.
2. Run accepted P8c storage.verify read-only with this operation's shared
   Budget. Its complete local fold catches global retained-entry contradictions,
   not only selected-row validity.
3. Obtain the complete selected alert/evidence pair with existing P8c
   storage._get_pair(outbox_db,alert_id,budget), which reads one transaction and
   deeply reconstructs that pair, checking schema/integrity. Do not compose get
   and evidence_get from separate transactions.
4. Call unchanged P8c application.recompute(...,_budget=the_same_budget).
   It reparses the complete manifest, reads original P5b
   _verified_signal_bundle in one ro/query_only transaction with one complete
   journal fold, checks both exact historical P5a entries, recalculates both
   full P5a evaluations and the genuine fresh per-rule transition. Exact
   original revision is mandatory; never substitute latest, heads or OR MATCH.
5. Read the selected pair again with _get_pair and compare canonical complete
   alert and evidence bytes to the first read. This comparison includes
   first_prepared_at; projection change is recompute_mismatch. No rerender or
   repair is persisted in any source.
6. Require policy_version=watchlist_synthetic_alert_v1, renderer_version exact
   integer1, channel=offline_preview, state=pending, mode=synthetic and genuine
   WATCHLIST_RULE_ENTERED_MATCH signal. Both entries, sequence, IDs, complete
   intent/evidence and plain SHA256 digests must reconstruct exactly. Preserve
   the P8c message's exact UTF-8 bytes, 1..4096 bytes, including its historical
   framing and SYNTHETIC — DEMONSTRATION ONLY header. Reject instead of editing.
7. Reconstruct complete binding/consent/route and, for prepare/claim only, issue
   the private single-use authority described below. Review creates no receipt
   that a writer can consume and writes nothing.

Existing _get_pair is sufficient: no additive P8c accessor or product edit is
proposed by this freeze. It returns detached values after its transaction.
The before/recompute/after reads are deliberately separate; no distributed
snapshot over four DBs exists. Immutable original revisions/rows and trusted
directories remain assumptions. Missing/different originals fail even when
local verify/get succeed. Source bytes are never written.

## 3. Canonical values, exact schemas and commitments

All objects below have EXACT keysets. Versions/IDs/counters/amounts use strict
types; bool is never an integer. Canonical C(value) is ASCII bytes of
json.dumps(value,sort_keys=True,ensure_ascii=True,separators=(',',':'),
allow_nan=False) AFTER strict accepted normalization. No duplicate keys,
surrogates, NaN/Infinity or type coercion. Define:

    S(value) = lowercase SHA256(C(value)).hexdigest()
    H(domain,value) = lowercase SHA256(ASCII(domain) || byte(0x00) || C(value)).hexdigest()
    message_sha256 = lowercase SHA256(exact_message.encode("utf-8")).hexdigest()

Existing entry/intent/evidence canonical bytes and plain digests retain P8c
semantics. Digests are local equality commitments, not source or human signatures.

The complete P8c _get_pair alert object has exactly twelve keys:
{alert_id,destination_key,signal_id,policy_version,renderer_version,channel,state,
intent,intent_sha256,message_text,message_sha256,first_prepared_at}.
Before/after snapshot stability compares all twelve, including operational
first_prepared_at. The semantic source_alert projection has the other ELEVEN
keys, omitting first_prepared_at; source_alert_sha256=S(source_alert).
Reconstruct all eleven retained semantic fields from stored content, not only
their digest. The P8c operational timestamp is not persisted in the new binding,
so independent original copies with identical semantics and different preview
preparation clocks remain equivalent.

intent and evidence are EXACT unchanged P8c v1 schemas. intent has fifteen
keys; evidence has {version,signal,predecessor,current}, containing full P5b
snapshots/results and complete P5a entries. entry is the complete normalized
P5a current.snapshot.entry and must canonically equal predecessor.snapshot.entry.
entry_sha256=S(entry), intent_sha256=S(intent), evidence_sha256=S(evidence).

route has exactly:
{route_version,provider,destination_key,bot_id,chat_id,chat_type,operator_attested}.
route_version=1, provider=telegram, chat_type=private, operator_attested=true.
destination_key is ASCII ^[a-z][a-z0-9_-]{0,63}$.
bot_id/chat_id are strict positive integers <=4503599627370495 (2^52-1).
route_sha256=H("CMT_WATCHLIST_TELEGRAM_ROUTE_V1",route).
The first accepted route for an alias is immutable. Equivalent registration
replays; changed identity/attestation conflicts. registered_at/validated_at are
operational, excluded from route/digest. Successful revalidation updates only
validated_at; it cannot rotate bot/chat or alter any frozen delivery.

consent has exactly:
{consent_version,acknowledgement,alert_id,signal_id,watch_id,revision,
message_sha256,evidence_sha256,entry_sha256,intent_sha256,source_alert_sha256,
route_sha256}.
consent_version=1. acknowledgement is exactly
SYNTHETIC_HISTORICAL_DEMONSTRATION. All remaining values derive from the admitted
selection and immutable route. consent_sha256=
H("CMT_WATCHLIST_TELEGRAM_CONSENT_V1",consent). No consent clock or token.
This acknowledges this historical demonstration/content/route only, not current
preferences, market accuracy, freshness, human read status or future sends.

binding has exactly:
{binding_version,provider,delivery_id,alert_id,destination_key,signal_id,watch_id,
revision,cmt_id,policy_version,renderer_version,message_sha256,evidence_sha256,
entry_sha256,intent_sha256,source_alert_sha256,route_sha256,consent_sha256}.
binding_version=1, provider=telegram; all values derive as above.
binding_sha256=H("CMT_WATCHLIST_TELEGRAM_BINDING_V1",binding).
No token, physical path, global file digest, attempt owner, preview preparation
timestamp or current clock enters binding.

delivery_id matches ^wtdl1_[0-9a-f]{64}$, alert/signal retain
^walt1_[0-9a-f]{64}$ / ^wsig1_[0-9a-f]{64}$; watch/sequence/evaluation retain
accepted wlt1_/wjs1_/wje1_ grammars. cmt_id is the unchanged canonical UUIDv4.
revision is strict integer1..2147483647. SHA256 strings are exactly64 lowercase
hex. No earlier alt1:/evt3:/tdl1: grammar is broadened.

## 4. Historical review and concrete consent command

Review is an offline recomputing command returning only the safe review object
defined in section10. It calculates the candidate consent/binding as if the
fixed acknowledgement were supplied; that output conveys no write/send authority.
Before prepare the operator locally examines the exact original text with the
existing explicit P8c preview command and checks the selected original revision:

    cmt watchlist-alert-outbox preview --outbox-db OUTBOX --alert-id WALT1
    cmt watchlist-telegram-delivery review --ledger-db LEDGER --watchlist-db WATCHLIST --journal-db JOURNAL --outbox-db OUTBOX --manifest MANIFEST --alert-id WALT1 --alias ALIAS

The uppercase metavariables in CLI examples designate explicit local values;
they are not accepted literal identity values. Ordinary P8d JSON never contains
message text or evidence. P8c preview is an explicit sensitive local viewing
operation and remains unchanged; protect its stdout and do not publish it.

Prepare requires --acknowledge-historical-demonstration with the exact phrase,
plus --expected-signal-id, --expected-revision, --expected-message-sha256,
--expected-evidence-sha256, --expected-route-sha256 and
--expected-binding-sha256 copied from that reviewed selection. --alert-id and
--alias explicitly select the remaining human-reviewed context. Prepare repeats
original admission, rebuilds all digests, and rejects any expected value mismatch
as consent_mismatch before writer open. The full binding digest commits entry,
intent, original alert, consent, watch/product and exact route, so omitted
individual CLI digest flags do not weaken full-content equality. No --yes,
unchecked caller commitment or generic historical preference is sufficient.

There is no expiring consent token or stored review authority. A historical
review may be used only if fresh prepare independently reconstructs the exact
same full binding; changed content/route must fail. The immutable consent stored
with preparation is revalidated before each unconfirmed claim. This presumes a
trusted local operator/process; it is not cryptographic human authentication.
Separate live-gate authorization remains required, even after this acknowledgement.

## 5. Delivery identity, replay and watch/revision consistency

    identity_object = {"identity_version":1,"provider":"telegram","signal_id":signal_id}
    delivery_id = "wtdl1_" + H("CMT_WATCHLIST_TELEGRAM_DELIVERY_V1",identity_object)

Only provider+genuine signal determines delivery identity. Enforce
UNIQUE(provider,signal_id), and bind its first accepted alert/alias/route,
consent, entry, evidence, intent and text forever within this ledger.
Identical prepare replays without changing first_prepared_at/state/history;
different alias, route or any immutable content is conflict. Another genuine
signal episode permits another delivery. No dedup across independent ledgers or
copies and no exactly-once remote guarantee.

Identity format vectors (not admissible source signals):

    canonical_A = {"identity_version":1,"provider":"telegram","signal_id":"wsig1_0000000000000000000000000000000000000000000000000000000000000000"}
    preimage_A = b'CMT_WATCHLIST_TELEGRAM_DELIVERY_V1\x00' + canonical_A.encode('ascii')
    sha256_A = b08e2920077a2f36ba634b32c0f1215e952063c55cfc99320ab55fbbdf9d36f5
    id_A = wtdl1_b08e2920077a2f36ba634b32c0f1215e952063c55cfc99320ab55fbbdf9d36f5
    canonical_B = {"identity_version":1,"provider":"telegram","signal_id":"wsig1_ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"}
    preimage_B = b'CMT_WATCHLIST_TELEGRAM_DELIVERY_V1\x00' + canonical_B.encode('ascii')
    sha256_B = 810e8528fcea94a8ee848b56cb50ae04ff35bbaef05de8f667bddda896cac9d8
    id_B = wtdl1_810e8528fcea94a8ee848b56cb50ae04ff35bbaef05de8f667bddda896cac9d8

The Python byte literals denote ONE actual NUL, not printable backslash-x00.
Both exact preimages are164 bytes. Full literal preimage hex:

    hex_A = 434d545f57415443484c4953545f54454c454752414d5f44454c49564552595f5631007b226964656e746974795f76657273696f6e223a312c2270726f7669646572223a2274656c656772616d222c227369676e616c5f6964223a2277736967315f30303030303030303030303030303030303030303030303030303030303030303030303030303030303030303030303030303030303030303030303030303030227d
    hex_B = 434d545f57415443484c4953545f54454c454752414d5f44454c49564552595f5631007b226964656e746974795f76657273696f6e223a312c2270726f7669646572223a2274656c656772616d222c227369676e616c5f6964223a2277736967315f66666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666666227d

ARQ independently recalculated these two format-only vectors on2026-10-30 with
.NET ASCII encoding, an actual [char]0 and SHA256, without product imports,
database/network/token access or file output. Both matched the brief constants.
This author calculation is not independent QA or product evidence.
Later committed independent tests must pin full preimage bytes/hex and digest,
with an independent QA oracle. Design calculations alone are not a gate.

RW-01 applies globally: every retained delivery for (watch_id,revision) must
have identical complete canonical entry_json and entry_sha256, across all
signals/aliases/routes/series/products. A first incompatible incoming admitted
entry yields identity_conflict with transaction rollback; a preexisting retained
contradiction yields storage_corrupt. Prepare AND claim must run the same full
local fold/invariants inside BEGIN IMMEDIATE that verify enforces before commit.
A successful verify after insertion is insufficient. Equivalent independent
original copies are allowed; incompatible genuine original bundles must fail
the second prepare without corrupting verification/backup.

## 6. Private one-use authority and writer protocol

A private application-issued receipt is not a public DTO. Its canonical envelope
has exactly {authority_version,operation,binding,binding_sha256,entry_json,
intent_json,evidence_json,message_text,route_json,consent_json}.
authority_version=1; operation exactly prepare or claim. Document fields are
canonical ASCII strings of the bounded schemas above; message is exact UTF-8.
The transient seal binds the complete envelope digest, exact receipt instance,
private process sentinel, exact issuing Budget identity and immutable global
deadline, operation, ledger normalized path+inode identity, original source
path+inode identities/owners, complete canonical manifest digest and origin-phase
ceiling/start. None of these transient source descriptors is persisted or logged.
No global authority registry/cache or cross-operation receipt is allowed.

Consume validates exact private type/instance/sentinel/content, correct operation,
same Budget/global deadline, same ledger/source/route bindings and unused marker
BEFORE writable open. A shallow/deep copy, changed content, forged dataclass,
different operation/source/route/Budget or second consumption is
unsupported_evidence. Valid issued-but-expired authority is storage_timeout,
not permission to create a fresh deadline. Mark consumed once before writer
use; even a failed writer requires new normal original admission. The original
phase ceiling cannot be restarted. The writer independently reconstructs every
semantic relation/digest, then checks retained invariants transactionally.
The seal is a process boundary, not protection against privileged hostile code.

Prepare stores complete immutable entry/intent/evidence/message/route/consent
and binding in one transaction. Claim repeats original-backed admission under
its own fresh send invocation, compares complete persisted binding, checks
quarantine/route validation/cooldown/clock/state/count/full fold, then writes
claim and in_flight state durably before HTTP. No SQLite transaction spans HTTP.

Each claim has attempt_id=wtat1_ plus64 lowercase unpredictable hex and a separate
private owner of64 unpredictable hex, independently generated from32 random bytes.
Owner never leaves private process/ledger; ordinary DTO exposes only attempt_id.
Ordinal is contiguous1..3. Each immutable claim also stores route_validated_at,
the exact latest successful route validated_at copied under the claim write lock.
The INSERT guard requires equality to that current validated_at. Historical fold
checks registered_at<=snapshot<=claimed_at and snapshot<=current validated_at;
it must NOT require an old claimed_at>=a later current validated_at. Revalidating
the same immutable route later does not invalidate prior claims. This is a local
recorded admission precondition, not cryptographic proof of a provider call, and
changes neither route/binding identity nor ordinary DTOs.
A transient owned handle binds ledger identity,
delivery, attempt, owner, Budget and global deadline. Finalization validates
that handle plus exact TransportResult/Receipt types and field combinations.
CAS requires current in_flight + current_attempt_id + owner + ordinal; result
insert and state change commit atomically. Stale/duplicate finishes return
stale_attempt without overwriting any result. No public receipt insertion API.

## 7. States, transport outcomes, clocks and recovery

ready -> in_flight -> confirmed | retryable | permanent_failure | uncertain.
Only ready or due retryable with attempt_count<3 may claim. No lease expiry,
automatic retry, terminal reset, uncertain resolution or unquarantine.
Each send invocation performs at most one sendMessage. Confirmed replay is local.
Explicit worker_quiesced=true recovery only changes in_flight to uncertain
and appends exactly one fenced result. It does not assert remote nonacceptance.

The internal adapter imports the unchanged P8b transport types lazily and accepts
only its narrow methods: check_configuration(), validate_destination(bot_id,
chat_id,timeout=remaining), validate_bot(bot_id,timeout=remaining), and
send(bot_id,chat_id,exact_message,timeout=remaining)->TransportResult.
It does not call P8b application.prepare/send or its writers and does not invent
Discovery identities. No accepted P8b transport change is proposed.

| Exact accepted transport outcome | New durable result |
| --- | --- |
| TransportResult("confirmed",None,None,Receipt) with exact valid route receipt | confirmed; error_category=null, retry_after=null, not_before=null |
| retryable, provider_rate_limit, strict retry_after1..86400, receipt=null, ordinal1/2 | retryable/rate_limited; not_before=completed_at+retry_after seconds |
| same valid429 on ordinal3 | permanent_failure/retry_exhausted; retain retry_after as evidence; not_before=null |
| permanent_failure/provider_rejection, null retry_after/receipt | permanent_failure/provider_rejection |
| uncertain with accepted transport error category, null retry_after/receipt | uncertain with that fixed category |
| Invalid TransportResult/Receipt type, state or field combination | uncertain/provider_invalid |
| Known postclaim transport DeliveryError from the accepted category set | uncertain with that exact category |
| Unexpected exception raised by send/adapter, unknown category or absent result | uncertain/network_uncertain |
| local result/receipt commit failure after possible send | best-effort uncertain/local_commit_failed; otherwise retain blocked in_flight |
| quiesced explicit recover | uncertain/recovered |
| postclaim clock rollback | uncertain/clock_skew, even if provider accepted |

Accepted uncertain transport categories are token_configuration, bot_mismatch,
destination_mismatch, transport_timeout, transport_failure, provider_invalid.
A preclaim exception never creates a claim/send. A postclaim exception cannot
authorize retry. A deadline expiring after claim but before actual dispatch
becomes uncertain/deadline_exceeded when durable finalization remains possible;
otherwise in_flight remains blocked. Every outcome after claim is conservative.

P8b production transport validates fixed official HTTPS api.telegram.org:443,
TLS, no proxy/redirect/retries/debug, methods getMe/getChat/sendMessage only.
Its worker reads CMT_TELEGRAM_BOT_TOKEN from local environment itself; token
never enters authenticated URL diagnostics, IPC projection, DB, args or logs.
Parent check_configuration validates locally without returning the secret.
sendMessage payload is only chat_id, exact text and disabled link previews;
no parse_mode/entities/topic. Metadata validation uses getMe/getChat; each
unconfirmed send validates bot identity via getMe BEFORE claim.

Reuse exact accepted bounds: response<=65536 bytes, strict UTF-8/JSON,
depth<=16, duplicate keys/NaN/nonfinite and bool-as-int rejected. Success requires
HTTP200, ok is true, no error_code/parameters; positive message_id<=2^63-1;
provider date integer1..253402300799; exact positive bot/chat IDs<=2^52-1,
sender.is_bot=true, private exact recipient, exact text; forbidden alternate
sender/business/ephemeral fields remain rejected. Receipt stores exactly
{message_id,accepted_at,bot_id,chat_id} privately. accepted_at is provider Unix
seconds, separate from operational timestamps; no claim of human read/freshness.

Only a strict explicit HTTP429 rejection validated by unchanged transport permits
retryable: ok=false, integer error_code=status, no result, bounded nonempty
description, valid retry_after1..86400, no migrate_to_chat_id. Its result does
not expose HTTP status; do not invent a status column or infer other provider
details. Other strict permanent4xx exclude408/409/425/429 and parameters.
5xx, redirect, malformed success/rejection, truncated/lost bytes, timeout and
unknown network/TLS failures are uncertain. A valid provider acceptance without
durable receipt is never confirmed.

Operational UTC grammar is exactly YYYY-MM-DDTHH:MM:SS.ffffffZ (27 ASCII bytes),
Gregorian years0001..9999, real calendar dates, hour00..23, minute/second00..59,
six fractional digits, uppercase T/Z. No offsets, naive times or leap seconds.
Source P5a/P5b timestamps retain their accepted grammar and normalized values;
do not convert historical times to this new operational grammar.

Global operational_high_water is monotonic over persisted EVENT timestamps:
init, route registered_at/validated_at, delivery prepared_at, claim claimed_at
and result completed_at (including derived state.updated_at). It is at least
every retained event timestamp. Exclude future eligibility not_before, source
historical timestamps and provider accepted_at; these do not advance the mark.
Before destination validation persistence, prepare and claim, refuse wall_now
below high_water, route registered_at/validated_at or relevant delivery.updated_at
with clock_skew. Claim repeats this check in its write transaction. Retry only
when wall_now>=not_before (inclusive); no grace. A forward wall-clock jump is
not detectable as false time by this design; host UTC correctness across restarts
is an explicit assumption. Within an operation monotonic time controls deadlines.

After claim, rollback cannot turn a possible acceptance into retry. Persist
uncertain/clock_skew with completed_at=max(wall_now,claimed_at,high_water) and
advance high_water, or leave in_flight if write fails. Manual quiesced recovery
uses the same conservative clamp; its category is clock_skew on rollback and
recovered otherwise. A clamped operational timestamp is not a historical market
time or provider timestamp. not_before addition must fit UTC year9999;
overflow after claim becomes uncertain/provider_invalid, never retryable.

## 8. One global budget, aggregate origin cap and finalization reserve

Local default2.0/max5.0 seconds; destination-validate/send default15.0/max30.0.
Timeout is strict finite positive int/float, bool forbidden. Start is CLI root
entry BEFORE argument parsing, or public Python API entry. Immutable monotonic
deadline=start+timeout includes parsing, input reads, all source/local folds,
metadata, HTTP, persistence and final output encoding.

Exactly one operation Budget object travels through new modules and existing
P8c helpers via their accepted _budget hooks. It conforms to/subclasses accepted
P5b Budget without changing that source class. P5a get is unchanged: receive only
the immediately remaining effective allowance, bracketed by parent checks.
No helper receives a refreshed configured timeout or new default allowance.

For send, establish origin_start once on entering original admission; during all
manifest/P8c pair/fold/recompute/P5a work effective deadline is
min(global_deadline-reserve,origin_start+5.0). Every helper/progress callback uses
this SAME Budget and ceiling. Exit scope only after full original admission;
never restart/extend origin_start or origin ceiling in the invocation. The sealed
claim receipt records this completed origin scope and immutable global deadline.
Local-command origins already share their whole<=5s deadline.

reserve=min(0.5,timeout/5.0) seconds. Subtract reserve from every preclaim and
network allowance, including metadata; if no positive allowance remains, no new
claim or HTTP dispatch. After durable claim, send receives only current global
remaining-reserve. Finalization/recovery fallback may use reserve under the
unchanged global deadline; no fresh5s fallback. This is a conservative allowance,
not a guarantee persistence succeeds. Result encoding checks deadline before
first output byte and emits no partial successful envelope.

Reuse P8b supervised worker for DNS/connect/write/read/body-drip deadlines.
_supervise includes bounded termination joins (up to two0.1s cleanup waits);
account for cleanup in the reserve and disclose possible supervisor overhead.
SQLite busy/progress/backup callbacks cooperate with current effective deadline.
Filesystem/kernel/stdout blocking and bounded indivisible parser/evaluator work
are not hard-preemptible. Output error can follow a completed durable commit;
error does not imply no local or remote effect. Never automatically resend.

## 9. Local verification, origin recompute and quarantined recovery

Local verify checks exact owner/header/schema/SQL inventory, integrity/FK and
guarded cell bounds before loading values; reconstructs route/consent/entry/
intent/evidence/message/source alert/binding/delivery identities; checks global
watch/revision equality, history ordinals/counts/owners/results/receipt bounds,
state/cooldown/high_water and current in-flight claim. It recomputes synthetic
semantics locally, but cannot authenticate absent originals or a coherent
privileged rewrite. No authority/cache crosses operations or recovery folds.

Origin recompute independently repeats section2 against the selected stored
delivery and compares every frozen field, route/consent and digest. It is
read-only, including for confirmed deliveries. Failure is not an empty result.
Local verify may pass while recompute fails due to missing/different originals.

Backup verifies one consistent source snapshot, copied provisional and independently
reopened provisional using three separate full folds under one Budget before
fsync/exclusive publication. Restore applies global durable send_quarantined=true
in the provisional BEFORE exposure, verifies quarantine after independent reopen,
then fsyncs/publishes exclusively. No current/future/missing-at-backup delivery
can send from restored authority, including subsequently prepared records.
There is no unquarantine command. Reads/recompute/recover/prepare remain possible
on quarantined stores; destination metadata validation remains explicit and
cannot lift quarantine. Backup of quarantine preserves it.

Preserve accepted hardlink/reparse/inode/sidecar guards, trusted ancestors,
exclusive new target, source byte nonmutation, owned-inode cleanup and safe
post-link unlink compensation. Foreign replacement/sidecar/recovery evidence is
never deleted to make cleanup appear successful. Persistent filesystem refusal
can leave names requiring inspection. Disk/process fault evidence and QEMU
cannot certify electrical power-loss or physical Raspberry Pi durability.

## 10. Closed CLI, DTOs, pagination and error exits

Group cmt watchlist-telegram-delivery; every OP requires --ledger-db PATH.
No option abbreviations, stdin "-", positional source selection or unknown flags.
All OP accept --timeout NUMBER within section8 limits.

| OP | Additional required flags | Optional flags |
| --- | --- | --- |
| init, verify | none | none |
| destination-add | --alias ALIAS --bot-id INT --chat-id INT --operator-private-owned | none |
| destination-validate | --alias ALIAS | none |
| review | --watchlist-db PATH --journal-db PATH --outbox-db PATH --manifest PATH --alert-id ID --alias ALIAS | none |
| prepare | --watchlist-db PATH --journal-db PATH --outbox-db PATH --manifest PATH --alert-id ID --alias ALIAS --acknowledge-historical-demonstration SYNTHETIC_HISTORICAL_DEMONSTRATION --expected-signal-id ID --expected-revision INT --expected-message-sha256 SHA256 --expected-evidence-sha256 SHA256 --expected-route-sha256 SHA256 --expected-binding-sha256 SHA256 | none |
| send | --delivery-id ID | --watchlist-db PATH --journal-db PATH --outbox-db PATH --manifest PATH; all four required if unconfirmed |
| get | --delivery-id ID | none |
| list | none | --state STATE --limit INT --cursor TOKEN |
| recompute | --delivery-id ID --watchlist-db PATH --journal-db PATH --outbox-db PATH --manifest PATH | none |
| recover | --delivery-id ID --worker-quiesced | none |
| backup, restore | --destination NEW_PATH | none |

Success/error output is one canonical ASCII JSON object plus LF, encoded in full
before first byte; no arbitrary extra keys. Every envelope has
{version:1,operation:OP,result:RESULT} plus only the operation-specific additions.
Parser failures use operation=watchlist-telegram-delivery. Help is normal argparse
help/exit0, accesses no stores/token/transport and is not an operation envelope.

| OP | RESULT | Exact additions |
| --- | --- | --- |
| init | ok | schema_version:1, send_quarantined:false |
| destination-add | inserted or replay | destination_key, route_sha256 |
| destination-validate | ok | destination_key, route_sha256, validated_at |
| review | ok | review |
| prepare | inserted or replay | delivery |
| send confirmed / confirmed replay | ok / replay | delivery |
| get | ok | delivery |
| list | ok | items, next_cursor |
| verify | ok | level:"local", counts, send_quarantined |
| recompute | ok | level:"origin-recompute", delivery_id, binding_sha256 |
| recover | ok | delivery |
| backup / restore | ok | counts, send_quarantined |

review exact object is binding plus {binding_sha256,acknowledgement,
historical_demonstration:true}; binding already contains all eighteen keys
defined in section3. It contains no route IDs, evidence/preferences or text.

delivery exact object:
{delivery_id,alert_id,signal_id,state,attempt_count,current_attempt_id,
not_before,first_prepared_at,updated_at,message_sha256,evidence_sha256,
route_sha256,consent_sha256,binding_sha256,send_quarantined,last_error_category}.
current_attempt_id is null except in_flight; not_before is null except retryable.
last_error_category is null with no result or confirmed, otherwise the normalized
last durable category. attempt_count strict0..3. No private owner, route payload,
receipt message_id/bot/chat IDs, message, entry, money, preferences or evidence.
List items use exactly this delivery DTO; get returns no unbounded attempt array.
counts exact {destinations,watch_entries,deliveries,claims,results}, strict
integers0..100000000, reconstructed from completed verification/copy.

Error envelope exactly {version,operation,result:"error",error_category}, with
one permitted optional addition delivery. Include delivery only when a healthy
local durable snapshot was read after a send outcome/preflight/recovery error;
never fabricate a state from a failed write or emit private result data.
A failed-finalization response may omit delivery; inspect get/verify explicitly.
Exit0 is success/replay. Error does not imply remote absence.

Closed category list and exit mapping:

Exit1: input_io, unsafe_destination, storage_missing, storage_schema,
storage_corrupt, storage_locked, storage_timeout, storage_io, recompute_mismatch,
transport_timeout, transport_failure, provider_rate_limit, provider_invalid,
rate_limited, network_uncertain, deadline_exceeded, local_commit_failed.

Exit2: invalid_json, duplicate_key, input_limit, invalid_shape,
unsupported_version, invalid_field, duplicate_id, broken_relation,
contradictory_binding, duplicate_identity, identity_conflict, missing_binding,
unknown_variant, unknown_language, ambiguous_reference, no_rules,
invalid_timestamp, invalid_target, unsupported_evidence, incompatible_context,
future_sample, invalid_chronology, replay_conflict, revision_conflict,
already_exists, not_found, invalid_cursor, conflict, invalid_transition,
invalid_destination, not_validated, consent_mismatch, send_quarantined,
delivery_blocked, retry_not_due, attempt_limit, stale_attempt,
token_configuration, bot_mismatch, destination_mismatch, provider_rejection,
retry_exhausted, clock_skew.

recovered is a stored result/log category and successful recover exit0, not a
public thrown error. All other stored categories are from this closed taxonomy.
Source WatchlistError/JournalError/OutboxError categories preserve names/codes.
Unexpected exceptions map to storage_io before claim; after claim use conservative
network_uncertain/local_commit_failed handling before returning redacted error.
Unknown source errors never become success/no-match. Unsupported receipt is
unsupported_evidence; wrong acknowledgement/digests consent_mismatch; wrong route
alias invalid_destination; different already-bound content conflict; prior
ledger contradiction storage_corrupt.

Pagination: list default100/max1000, strict integer1..1000. Ascending delivery_id
keyset, predicate delivery_id>last_delivery_id. Cursor exact
{version:1,filters:{state:null-or-one-of-six-states},last_delivery_id:wtdl1_}.
Canonical ASCII JSON encoded URLsafe Base64 WITH canonical "=" padding.
Token1..2048 ASCII chars, URLsafe alphabet and<=2 terminal "=", length divisible4;
decoded cap1536 ASCII bytes. Reject duplicate/extra keys, noncanonical JSON,
wrong types/version/filter, invalid ID or nonidentical encode/decode as
invalid_cursor. Limit may change, filter may not. Pages use separate verified
snapshots, no offset/global multipage snapshot. Whole response including cursor
and LF<=1048576 bytes. Byte-limited pages continue after last included row,
never skip a row; timeout/corruption discards prospective successful page.

Public JSON/input cap1048576 bytes, depth16, nodes20000, scalar strings1024
characters; strict UTF-8/duplicates/nonfinite rejection. Unchanged tighter source
caps apply. Internal canonical documents have distinct byte caps: entry65536,
intent65536, evidence262144, route2048, consent4096, binding8192;
private receipt envelope1048576, message4096 UTF-8 bytes. Container document
strings are decoded under their own schema limits, never treated as ordinary
scalar1024. No public limit is widened by this internal exception. SQL guards
exact text/integer types, lengths and retained bound before materializing rows.

## 11. Lazy imports, secrets and completion logging

Offline operations, malformed arguments and help must work in fresh processes
denying import of telegram_delivery (including transport), token environment
access and all product sockets. New package import and P8c routes retain this
property. Only destination-validate or an unconfirmed send after all local
preflight may lazily import/instantiate the narrow production adapter.
Confirmed replay checks quarantine/healthy local receipt without adapter import,
configuration checks, token access or sockets. Root registration/dispatch is
additive and lazy; no eager import for help, invalid flags or old offline groups.

Only local environment CMT_TELEGRAM_BOT_TOKEN is supported. Do not request,
read or use it during this design step. Never add token arguments/files/fixtures,
dump environment, capture raw HTTP, publish private IDs or treat P8b T17
credentials/authority as inherited. Route ID flags are local private values;
shell history/transcripts require operator protection.

Proposed single completion event watchlist.telegram_delivery.completed,
component=cli, operation prefix watchlist_telegram_delivery_ with suffix
arguments/init/destination_add/destination_validate/review/prepare/send/get/list/
verify/recompute/recover/backup/restore. Fields retain timestamp, UUID run_id,
duration_ms>=0, result=ok/inserted/replay/error and fixed error_category on error.
Optional only grammar-validated delivery_id/attempt_id, state/previous_state,
attempt_count0..3 and delivery_count0..100000000. No hashes, aliases, source IDs,
route IDs, cursors, paths, amounts/preferences, message/evidence, provider body,
SQL, URL or raw exceptions. Exactly one completion record after durable outcome
is known; never log success before receipt commit. Public output privacy
sentinels and additive LOGGING_V1 allowlist require later tests.

## 12. Required later falsification evidence and source anchors

These are future obligations, not executed gates: genuine complete-manifest
P5a/P5b/P8c pipeline and ancient replay; forged/copied/mutated/wrong-Budget/
wrong-operation/source/route and reused receipts; altered/missing originals;
source nonmutation; exact identity NUL vectors; alternate aliases dedup;
genuine incompatible entry bundles and concurrent RW-01 rollback; two sender
processes/one durable claim/one fake send; crash/kill at all HTTP/result windows;
owner CAS/stale finalization/recovery; complete strict transport failure matrix;
third429/exact cooldown/clock rollback; real aggregate origin/global deadlines;
three-fold copy/quarantine including omitted/new deliveries; SQL tamper/bounds/
inode/sidecar/ENOSPC; cursor/DTO/errors/log privacy; import/token/socket tripwires.

Preserve prior twelve harnesses and add thirteenth offline installed-wheel,
Compose, AMD64 and ARM64/QEMU harness with five checkpoints/four genuine signals,
one selected preparation/fake send, persisted receipt, separate-process tokenless
network-denied confirmed replay, recompute/recovery/quarantine/nonmutation.
Independent QA and distinct final REVIEWER must be nonauthors and review the
exact final SHA/tree with public sanitized runnable probes. No Gate B PASS,
implementation evidence, live acceptance or physical Pi claim follows here.

Source anchors reviewed at baseline9dda9fba0aa9646a67596657d4ae9a7088903808:
P8c application.py _manifest/_origin_entry/_admit/recompute; storage.py
_selected/_get_pair/_entry_identity/_fold; policy.py validate_prepared/prepare;
P5b storage.py Budget/_verified_signal_bundle; P8b transport.py
Receipt/TransportResult/check_configuration/_receipt/_supervise/TelegramTransport;
P8b application.py _Budget/send; storage.py _claim_verified/_finish/recover.
P8b's replay-before-quarantine and per-helper Budget.local behavior are studied
historical code, not behaviors adopted for this new authority. Accepted ADR0011
through0014 and P5a/P5b/P8b/P8c API/recovery contracts remain unchanged.
