# WATCHLIST_ALERT_OUTBOX_V1 — frozen engineering API, policy and CLI

**Freeze:** 2026-10-26; Phase Lead review pending. **Product implementation:** NOT STARTED.
Authority: [unchanged Orchestrator contract](../phases/P8C_OFFLINE_WATCHLIST_SIGNAL_OUTBOX_CONTRACT.md).
See [ADR-0014](../adr/0014-offline-watchlist-signal-outbox.md) and
[exact storage design](WATCHLIST_ALERT_OUTBOX_STORAGE_V1.md). These are engineering
implementation targets, not final acceptance, executed gates or merge authority.

## 1. Public operations and source authority

Freeze the Python application boundaries (paths are Path, raw values are object):
enqueue(outbox_db,watchlist_db,journal_db,manifest,signal_id,destination_key,*,
timeout=2.0) -> dict[str,object];
recompute(outbox_db,watchlist_db,journal_db,manifest,alert_id,*,
timeout=2.0) -> dict[str,object].
manifest is a complete RAW MANIFEST_V1 object, not a parsed dataclass/receipt.
CLI reads it from its explicit path. No API accepts caller evidence/intent/results
as authority. Outbox must already exist through explicit init. Three database
paths must be pairwise-distinct safe existing files, checked by normalized path
and samefile identity. No latest selection, automatic iteration, bulk enqueue,
silent source repair, rerender or cross-store write.

Each enqueue, including ancient replay, must:
1. Validate fields, source paths/owners/schemas and complete raw manifest with
   accepted P5a/MANIFEST_V1 parsers, including unrelated entities and bindings. Freeze/decode bounded canonical raw
   input before callbacks; validate and consume that same detached manifest value,
   not a later-mutated caller dictionary.
2. Call the private P5b reader below for the one exact stored wsig1_.
3. Validate that both snapshots have the same complete immutable P5a entry,
   watch/revision/product/canonical identity and series/sequence. Reread the
   original exact P5a revision using its unchanged get API with explicit revision;
   when both snapshots identify the same revision, one verified reread compared
   against BOTH complete entries suffices. Parse the full manifest and compare
   complete identity_projection and its digest. No latest pointer is authority.
4. Recompute both complete P5a results from the admitted historical entry and
   each snapshot's current/previous/as_of, and rederive exact P5b sequence,
   evaluation and selected per-rule signal identities, links and freshness.
5. Require selected actual signal, enabled entry, correct synthetic mode/kind,
   consecutive pair, selected rule NO_MATCH then MATCH, and both current samples
   fresh at new as_of under unchanged P5b logic. Aggregate OR never suffices.
6. Build exact semantic evidence, derive intent/message and issue the private
   content-bound receipt. Only the new outbox writer may persist the admitted
   alert and evidence; the receipt remains transient.

Baseline evaluations have no selected signal and cannot be admitted by inventing
one. INDETERMINATE/SKIPPED/UNKNOWN/stale histories do not become NO_MATCH.
A price predecessor NO_MATCH due to OUT_OF_STOCK may legitimately have null
monetary fields. Do not reject it or invent zero shipping.

Policy: watchlist_synthetic_alert_v1. renderer_version exact integer1.
kind: WATCHLIST_RULE_ENTERED_MATCH. mode: synthetic. rule: price or restock.
Original sample provenance is synthetic, a producer declaration checked locally,
not proof of real shop evidence. channel: offline_preview. state: pending.
destination_key is ASCII ^[a-z][a-z0-9_-]{0,63}$, a local alias, no Telegram route.
All IDs have exact lowercase hex suffixes: walt1_/wsig1_ +64 (length70),
wjs1_/wje1_/wlt1_ +64 (length69); CMT product IDs retain canonical UUIDv4.

## 2. Additive P5b source-reader contract

Future addition solely in watchlist_journal/storage.py, reserved to ARQ/BE:

```text
_verified_signal_bundle(
    path: Path,
    signal_id: object,
    *,
    _budget: watchlist_journal.storage.Budget
) -> dict[str, object]
```

No default/new timeout is created. P8c internal stages share this same P5b Budget
object, translating its fixed errors at the P8c boundary. It is an integration
detail, not a new public source authority.
- Validate wsig1_ grammar and remaining budget.
- Enter existing _connect(path,_budget) (mode=ro, query_only, not immutable=1)
  and existing _transaction(db,_budget), one connection and BEGIN.
- Execute accepted _verify(db,_budget) exactly ONCE. It must keep its accepted
  implementation, return shape and all deep checks; no weaker verifier.
- Select the actual signal using guarded internal SQL. If absent: not_found.
  Read exact from/to evaluations with existing _load_evaluation and the chosen
  actual _signals_for in this same transaction and budget.
- Check selected identity/body, sequence, consecutive ordinal, predecessor link
  and exact eligible P5b transition. A source relationship contradiction is
  storage_corrupt. No public signal_get/get/get composition, second connection
  or different snapshots.
- Project exactly section3 evidence, stripping operational persisted_at and the
  outer signal_ids list while retaining selected signal.signal_id;
  validate/bound it and return a detached semantic value after transaction close.

There is one FULL journal fold; loading two selected rows can recompute those
rows again. Do not claim only one evaluation computation throughout admission.
No global cache, trusted saved DTO, head/count/file hash is returned. Existing
P5b signatures, result/error shapes, writes, transitions and recovery are unchanged.
JournalError categories are preserved. This helper changes no P5a interface.

## 3. Frozen semantic models

All keysets are EXACT, versions and integers are nonbool; canonical byte equality
is stronger than Python bool/int equality.

evidence = {version,signal,predecessor,current}, version integer1.
signal = {version,kind,mode,sequence_id,rule,from_evaluation_id,
to_evaluation_id,signal_id}, version integer1.
Each predecessor/current = {evaluation_id,sequence_id,ordinal,
predecessor_evaluation_id,snapshot,evaluation_result}.
snapshot = complete accepted P5b {version,sequence_id,policy_version,entry,
current,previous,as_of}, version1 and policy_version watchlist-rules-v1.
entry/current/previous/results use COMPLETE unchanged P5a grammar and
normalization. evaluation_result contains the entire freshly recomputed P5a
result, not a selected reason alone.

ordinal is an exact integer >=1. current.ordinal=predecessor.ordinal+1.
current.predecessor_evaluation_id=predecessor.evaluation_id.
predecessor.predecessor_evaluation_id is null iff predecessor.ordinal=1;
otherwise a strict wje1_ distinct from retained predecessor/current IDs.
The selected current ordinal is >=2. Snapshot current sample IDs differ,
observed_at strictly increases, as_of never decreases and
current.snapshot.previous canonically equals predecessor.snapshot.current.
The chosen full signal body+ID must equal an unchanged P5b-derived signal.

Both entries and sequence/product/revision/series must agree exactly.
Snapshots retain their own previous evidence, including nullable baseline
previous. Two retained evaluations do not prove all omitted earlier ancestry;
the full original journal fold supplies that source assurance during admission.

intent has exactly these FIFTEEN keys:
{version,policy_version,renderer_version,channel,state,signal_id,kind,mode,rule,
sequence_id,watch_id,revision,cmt_id,from_evaluation_id,to_evaluation_id}.
version=1. All other values derive from the validated bundle and fixed policy.
No destination is embedded in intent (it is stored separately and bound by ID).
No manifest names, URLs, labels, bindings or arbitrary extras are retained.
No persisted_at, paths, run IDs, global heads/counts, current preferences or
file-wide digest enters semantic evidence/intent.

Canonical = strict normalized values serialized using json.dumps(sort_keys=True,
ensure_ascii=True,separators=(',',':'),allow_nan=False), UTF-8/ASCII bytes.
Strict field typing is required BEFORE serialization; the serializer alone
does not make arbitrary dictionaries valid.
intent_sha256/evidence_sha256 are lowercase SHA256 of their canonical bytes.
message_sha256 is lowercase SHA256 of exact rendered UTF-8 bytes.

## 4. Frozen identity and independent vectors

```text
preimage = ASCII("CMT_WATCHLIST_ALERT_V1") + byte(0x00)
         + ASCII(canonical({"identity_version":1,
                            "destination_key":alias,
                            "signal_id":signal_id}))
alert_id = "walt1_" + sha256(preimage).hexdigest()
```

Exactly one NUL byte; never printable backslash-zero/backslash-x00. No text,
renderer, clock, path or head enters identity. Same alias/signal -> one alert.
Different alias, per-rule signal, revision/series/product or later episode
produces distinct identities through its actual source signal.

The handoff's three vector cases are the byte authority for future imported
fixtures/oracle (not copied during this step):
- local-preview + price wsig1_d9f9c7f0d4ca8767a6cdb9a917cc27a61c369cecea629c790ed42fd4421bf4f0
  -> walt1_6bd35f464dd126efb7f31ef6070ea7d3257799d294d5dd3dea21c3445ef0a1af
- local-preview + restock wsig1_4bd7f7a2ca57d7e8c9e340dc5f3c27aa5f3dbe433c7ef01a0ac897675e4e8bd4
  -> walt1_89548632c3d10ccb112ab72af5ca10e5819b7cd938ffbd120a3b19d5c4c87450
- qa-preview + the same price signal
  -> walt1_338382e5b05bc41b635fe296acc7757a60756871790a6aacd29cec051bdfe1ae

Freeze full canonical_json, preimage_text (including actual NUL), preimage_hex
and expected ID in the later versioned fixture. These identities are test vectors,
NOT runtime producer authorization. Preserve all earlier evt3:/cmp3:/alt1:/tdl1:
grammars; do not synthesize or broaden them.

The supplied p8c_identity_oracle.py writes its fixture at top level. It must not
be executed/imported as a read-only check. Its FUTURE integrated interface is
read-only by default and via --check: independently compute constants/preimages
in stdlib, compare the existing fixture byte fields/digests, exit0 equality/1
mismatch without writes. Explicit --write-fixture is the only regeneration path,
mutually exclusive with --check. Independent QA/REVIEWER use their own references,
not production helpers or that oracle as the sole expected-value authority.

## 5. Renderer version1: exact pure interface and bytes

Freeze render(intent: object,evidence: object) -> str, pure and deterministic,
with no SQLite, filesystem, clock, network, provider, Telegram or environment IO.
Revalidate exact semantic shapes and reconstructed intent correspondence before
rendering. Internal normalized reuse is operation-local, never caller authority.

Join the following common lines in EXACT order with LF; no trailing LF.
Braced expressions below are specification placeholders, not literal output.

```text
SYNTHETIC — DEMONSTRATION ONLY
Not a real offer or commercial notification.
Historical Watchlist simulation; not current notification authorization.
cmt_id: {intent.cmt_id}
watch_id: {intent.watch_id}
historical_revision: {intent.revision}
rule: {intent.rule}
signal_id: {intent.signal_id}
sequence_id: {intent.sequence_id}
from_evaluation_id: {intent.from_evaluation_id}
to_evaluation_id: {intent.to_evaluation_id}
predecessor_current_observed_at: {predecessor.snapshot.current.observed_at}
predecessor_previous_observed_at: {predecessor.snapshot.previous.observed_at-or-none}
predecessor_as_of: {predecessor.snapshot.as_of}
current_current_observed_at: {current.snapshot.current.observed_at}
current_previous_observed_at: {current.snapshot.previous.observed_at}
current_as_of: {current.snapshot.as_of}
predecessor_rule_result: {selected predecessor rule.result}
predecessor_rule_reason: {selected predecessor rule.reason}
current_rule_result: {selected current rule.result}
current_rule_reason: {selected current rule.reason}
```

For price append exactly:

```text
Synthetic price rule entered MATCH.
currency: EUR
target_price_minor: {current.snapshot.entry.target_price_minor}
predecessor_unit_price_minor: {money(predecessor.snapshot.current.unit_price_minor)}
predecessor_shipping_minor: {money(predecessor.snapshot.current.shipping_minor)}
predecessor_effective_cost_minor: {total(predecessor.snapshot.current)}
current_unit_price_minor: {money(current.snapshot.current.unit_price_minor)}
current_shipping_minor: {money(current.snapshot.current.shipping_minor)}
current_effective_cost_minor: {total(current.snapshot.current)}
```

For restock append exactly:

```text
Synthetic restock rule entered MATCH; no real shop availability is asserted.
predecessor_previous_stock: {predecessor.snapshot.previous.stock-or-none}
predecessor_current_stock: {predecessor.snapshot.current.stock}
current_previous_stock: {current.snapshot.previous.stock}
current_current_stock: {current.snapshot.current.stock}
```

money(null) is literal unknown; otherwise base10 integer cents without grouping.
total is unknown unless BOTH validated components exist; otherwise exact integer
sum<=2000000000. No zero substitution, float conversion, reference, discount or
invented price. A price signal's target is required nonnull. Shipping0 is known
free shipping. A genuine absent predecessor.snapshot.previous displays none in
its time/stock positions. current.snapshot.previous is mandatory for an admitted
signal and cannot display none. Stock UNKNOWN remains uppercase UNKNOWN.
Selected rule rows are required, with original reasons preserved and exact
NO_MATCH then MATCH. Missing/invalid fields fail; no invented placeholders.
Historical P5a UTC normalization is preserved, not replaced by current clocks.

Every substituted string uses the P8a escaping discipline: for each character
that is nonprintable or Unicode category C, use json.dumps(char,
ensure_ascii=True)[1:-1]; literal backslash doubles; other printable Unicode
is preserved. Thus controls, input CR/LF, ESC, bidi and separators cannot add
display lines. Surrogates are rejected at validation; renderer defense still
escapes category C. Fixed template LF and header em dash are intentional.
Output is plaintext with no parse mode, Markdown/HTML interpretation or generated
active links. The final message must be <=4096 UTF-8 bytes; reject input_limit,
never truncate. Hash exact UTF-8 bytes, without an added LF.

## 6. CLI grammar and exact responses

cmt watchlist-alert-outbox OP; each operation requires --outbox-db PATH.
--timeout NUMBER defaults2.0, finite positive max5.0 (bool forbidden in Python).
Options do not abbreviate. No stdin '-' JSON mode, positional source selection,
extra fields or arbitrary-text input. Existing P0/prior CLI behavior is preserved.

| OP | Additional required flags | Optional flags |
| --- | --- | --- |
| init | none | none |
| enqueue | --watchlist-db PATH --journal-db PATH --manifest PATH --signal-id ID --destination-key ALIAS | none |
| get | --alert-id ID | none |
| list | none | --destination-key ALIAS --limit INT --cursor TOKEN |
| evidence-get | --alert-id ID | none |
| preview | --alert-id ID | none |
| verify | none | none |
| recompute | --watchlist-db PATH --journal-db PATH --manifest PATH --alert-id ID | none |
| backup | --destination NEW_PATH | none |
| restore | --destination NEW_PATH | none |

All operation responses are one canonical ASCII JSON object plus LF, complete
before first output byte. --help retains normal argparse help/exit0; it is not an
operation result and performs no store access. P8c help/invalid args also must not
import Telegram. No product traceback, path, SQL or arbitrary exception text.

Every response has exactly version integer1, operation, result plus the stated
operation-specific fields. operation is the subcommand spelling; parser failures
use watchlist-alert-outbox. Success exits0. result=ok except enqueue uses
recorded or replayed. No partial counts or success precedes commit.

| OP | Exact success additions |
| --- | --- |
| init | schema_version:1 |
| enqueue | alert_id, signal_id, destination_key |
| get | alert |
| list | items, next_cursor |
| evidence-get | alert_id, evidence, evidence_sha256 |
| preview | alert_id, message_text, policy_version, renderer_version, channel, state |
| verify | level:"local", counts:{alerts,evidence} |
| recompute | level:"origin-recompute", alert_id |
| backup / restore | counts:{alerts,evidence} |

alert has exactly {alert_id,destination_key,signal_id,policy_version,
renderer_version,channel,state,intent,intent_sha256,message_text,message_sha256,
first_prepared_at}. list items have the other TEN keys after omitting intent and
message_text, never bundles/full messages. first_prepared_at is a valid UTC
YYYY-MM-DDTHH:MM:SS.ffffffZ operational timestamp, generated once, not source time.
counts are exact nonnegative integers with alerts=evidence for a healthy store.

An error has exactly {version,operation,result:"error",error_category}; exit
according to section7. No field holds an untrusted exception. JSON error responses
remain redacted; explicit successful stdout/DB/backups are sensitive local data.

### Cursor freeze

list default limit100, strict nonbool integer1..1000. Ascending alert_id keyset,
exclusive predicate alert_id>last_alert_id. Cursor exact object:
{version:1,filters:{destination_key:null-or-validated-alias},last_alert_id:walt1_}.
Canonical ASCII JSON encoded with URLsafe Base64 INCLUDING canonical '=' padding.
Transport token1..2048 ASCII characters; alphabet [A-Za-z0-9_-] and <=2 terminal
'=', total length divisible by4. Strict decoded cap1536 ASCII bytes. Reject
duplicate/extra keys, wrong types/version/filter, malformed last ID,
noncanonical JSON or nonidentical decode/re-encode as invalid_cursor.
Limit may change across pages; filter may not. No offset, trusted signature,
cursor-based enqueue selection or global multipage snapshot. Payload response
<=1048576 bytes including cursor/envelope/LF. Byte-limited pages return a valid
continuation after the last included row; never skip rows. Timeout/corruption
discards the whole prospective successful page, not a partial result=ok.

## 7. Closed error taxonomy and exits

Allowed categories are exactly the current baseline P5b ERROR_CATEGORIES union
{invalid_transition,recompute_mismatch}, frozen explicitly below.

Exit1:
input_io, unsafe_destination, storage_missing, storage_schema, storage_corrupt,
storage_locked, storage_timeout, storage_io, recompute_mismatch.

Exit2:
invalid_json, duplicate_key, input_limit, invalid_shape, unsupported_version,
invalid_field, duplicate_id, broken_relation, contradictory_binding,
duplicate_identity, identity_conflict, missing_binding, unknown_variant,
unknown_language, ambiguous_reference, no_rules, invalid_timestamp,
invalid_target, unsupported_evidence, incompatible_context, future_sample,
invalid_chronology, replay_conflict, revision_conflict, already_exists,
not_found, invalid_cursor, conflict, invalid_transition.

No other categories. Preserve source names/codes when translating accepted
WatchlistError/JournalError; unknown unexpected failures become redacted
storage_io, not successful no-match. Internal category constructors may fall back
to invalid_field for an unsupported category value, but the unexpected-exception
boundary explicitly selects storage_io.

| Condition | Category |
| --- | --- |
| Malformed ID/alias/timeout | invalid_field |
| Public JSON syntax/nonfinite/encoding | invalid_json |
| Public duplicate key | duplicate_key |
| Public size/depth/node/string excess | input_limit |
| Public exact-key/type shape mismatch | invalid_shape or field-specific invalid_field |
| Missing selected original signal/revision or local alert row | not_found, preserving source lookup semantics |
| Wrong owner/schema inventory/version marker/mode | storage_schema |
| Corrupt retained cells/links/results/text, missing half-pair | storage_corrupt |
| Normalized but ineligible selected transition | invalid_transition |
| Same ID with different valid frozen content/version | replay_conflict |
| Valid locally stored alert differs from freshly admitted originals | recompute_mismatch |
| Original lookup/verifier fails | preserve its exact category |
| SQLite BUSY/LOCKED | storage_locked |
| SQLite CORRUPT/NOTADB/TOOBIG/CONSTRAINT | storage_corrupt |
| SQLite INTERRUPT or elapsed shared deadline | storage_timeout |
| Remaining SQLite/OS/unexpected exception | storage_io |

A decoder failure on retained data maps to storage_corrupt except timeout, which
MUST survive as storage_timeout. Invalid input schema version remains
unsupported_version/exit2, whereas a wrong physical DB schema is storage_schema.
No source corruption is hidden as not_found, empty pages or replay.

## 8. Limits, deadlines and private receipt

| Boundary | Hard cap / rule |
| --- | --- |
| External JSON | UTF-8 1048576 bytes; depth16; nodes20000; semantic strings/keys1024; duplicate/nonfinite/surrogate rejection |
| P5a/P5b components | all accepted stricter field limits and P5b snapshot+result cap65536 |
| Complete semantic evidence | canonical ASCII262144 bytes; depth16/nodes20000/semantic strings1024 plus original component checks |
| Intent | canonical ASCII65536 bytes; same structural validation |
| Rendered message | UTF-8 bytes1..4096; separate bound, not a generic1024 scalar |
| Private receipt envelope | canonical ASCII <=1048576 bytes, exact fields below |
| List output | <=1048576 bytes; limit100 default/1000max |
| Cursor | encoded2048, decoded1536 ASCII; exact grammar above |
| Operation | default2s; max5s finite positive cooperative deadline |

Semantic strings/keys are distinct from serialized container cells. intent_json,
evidence_json and the private receipt's encoded strings are bounded DOCUMENTS,
not semantic scalar1024 strings. Only a sealed application-issued receipt may
use that internal envelope exception; each embedded semantic document is decoded
under its own byte/depth/node/string cap. No public input limit is widened.
Message has its own UTF-8 cap. Generic response serialization must not reapply
semantic scalar1024 to already validated message/container values.

Receipt content exact keys:
{version,alert_id,destination_key,signal_id,policy_version,renderer_version,
channel,state,intent_json,intent_sha256,evidence_json,evidence_sha256,
message_text,message_sha256}, version1.
The entire canonical envelope, exact issued instance identity and private process
sentinel are bound in the same manner as P8a's private sealed receipt. Ordinary
construction, shallow/deep copies, changed fields/content or a public dict/hash/
verified flag fail unsupported_evidence before opening a writer. Private authority additionally binds the originating Budget object by identity
and a one-use marker outside the envelope/persisted fields. Consumption requires
supplied_budget is issued_budget, unchanged sealed content/instance/sentinel,
and an unused receipt BEFORE opening a writer. Wrong Budget, copies, mutation
or second consumption fail unsupported_evidence. A valid issued receipt whose
original deadline expired fails storage_timeout. Mark consumed once when accepted;
a failed writer requires fresh normal source admission and a new receipt, not
reuse or a new deadline. No global authority registry is permitted. Do not persist
the receipt or cache its authority. Writer independently rebuilds all content
under the current operation budget; the seal is no substitute for semantics.
This boundary resists unsupported ordinary callers, not privileged Python code.

CLI timing starts at root main entry BEFORE argument parsing; the validated
timeout yields deadline=start+timeout. Python API timing starts at API entry.
New modules/helper use the same Budget object, anchored to that deadline.
P5a get is unchanged: pass timeout=parent.remaining() immediately before its
exact-revision read, then check parent.remaining() immediately afterward.
Never pass the original configured timeout again or invent a P5a _budget option.
All parsing, manifest validation, folds, SQL waits, normalization/rendering,
receipt consumption, commit, recovery and final serialization consume the same
allowance. Check before/after indivisible stages; busy/progress/copy callbacks
cooperate. Preserve timeout through reused decoder exception adapters.
Fully encode/check output bytes and deadline before its first byte.
Blocking OS/device/stdout or individual bounded parser/evaluator calls may
outlast a cooperative deadline. Postcommit/postpublication failure may leave a
complete durable result; retry exact admission or explicitly verify a published
target, without claiming every error rolled back completed work.

## 9. Replay, local verify and original recompute

Replay never trusts a local ID hit. Revalidate all originals first, reconstruct
the entire semantic bundle/intent/message, then compare immutable contents in
the writer transaction. Preserve original prepared time, bytes and cardinality
after newer journal appends or Watchlist revisions. Original missing/invalid
means enqueue/recompute failure even when get/preview/local verify can succeed.
No overwrites, evidence additions for an old signal or automatic rerender.

verify folds the entire local store; get/evidence-get/preview rebuild the selected
complete local pair; list emits summaries only. Original-backed recompute uses
an independent origin admission on the stored signal and alias, comparing the
full semantic projection, intent/versions, IDs, message and all digests in a
read-only operation. Validate/preserve the original operational timestamp; do
not regenerate it or claim proof of its historic truth from source clocks.
Local folds do not authenticate original existence or privileged consistent
rewrites. No cached trusted result crosses operations/snapshots/recovery folds.

## 10. Transport isolation, privacy and observability

Every P8c route, including malformed args/help, must work in a fresh process
with imports of telegram_delivery (including transport) denied. Root currently
imports Telegram CLI eagerly; the future minimal Lead-owned integration makes
that import/registration/dispatch lazy for existing Telegram routes and preserves
existing root/Telegram help, argument grammar, errors and results. No edit to
Telegram application/storage/transport or source authority is permitted.
No P8c code reads Telegram token/chat configuration, initializes transport,
contacts sockets or calls a fake Telegram destination. Prior Telegram harnesses
retain their separately contracted fake transport and quarantine behavior.

Freeze completion event watchlist.alert_outbox.completed; component cli;
operation prefix watchlist_alert_outbox_ plus arguments/init/enqueue/get/list/
evidence_get/preview/verify/recompute/backup/restore.
Fields: existing timestamp, UUID run_id, event/component/operation, nonnegative
integer duration_ms, fixed error_category when error, result=ok/replay/error.
Product recorded maps to logged ok; replayed maps to replay.
Optional watchlist_alerts_count and watchlist_alert_evidence_count are strict
nonbool integers0..100000000, derived only from completed successful work/returned
items, omitted on error. No arbitrary extras or raw exception text. Exclude
all IDs, aliases, cursors, manifests, samples, amounts, preferences, message,
paths, SQL, tokens and bot/chat IDs. Explicit stdout/backups still require
private operator handling. No operational/system alert is sent.

## 11. Test/oracle/gate traceability

All entries below are REQUIRED FUTURE evidence, not results of this freeze.
Pin commands, agent, environment, date, candidate HEAD/tree and public readback.

| AC | Required reproducible evidence |
| --- | --- |
| AC-WA01 | Exact Git baseline/tree/parents/clean state; unchanged opening-contract bytes; later attributed roadmap/AGENTS update |
| AC-WA02 | Real one-signal pipeline; exact historical entry/full manifest rejection matrix, also replay |
| AC-WA03 | Instrument one ro journal transaction/one complete _verify; selected row reloads visible; reject caller authority/copies/mutation/different Budget/second consumption |
| AC-WA04 | Exact keysets/canonical bytes/full prior evidence; bounded cells/documents; reconstruction from both full results |
| AC-WA05 | Independent SHA/NUL/full-preimage vectors, alias change, old-ID isolation; read-only oracle check |
| AC-WA06 | Two rules, two aliases, five checkpoints/four signals/two episodes and revision/series/product isolation |
| AC-WA07 | Ancient replay after appends/revisions preserves bytes/time/count; invalid originals and valid content conflicts never overwrite |
| AC-WA08 | Independent processes recorded/replayed, failures between inserts/commit, crash/reopen and missing-half corruption |
| AC-WA09 | Exact message golden bytes/hash, money null/free shipping, controls/bidi/oversize, pure rendering and import denial |
| AC-WA10 | Full local fold; coherent rehash/trigger-restoration tampering still fails for invalid semantics |
| AC-WA11 | Independent read-only origin recompute, missing/different originals, complete canonical comparison/nonmutation |
| AC-WA12 | All CLI DTO/error/exits, duplicate/type/input limits, filter-bound cursor/pages and parsing-to-output deadline/no partial ok |
| AC-WA13 | Three independent prepublication folds; stage corruption/timeouts, fsync/link/unlink/ENOSPC/replacements/sidecars, restart recovery |
| AC-WA14 | Socket/import/config-access tripwires from fresh process start; bytewise quiescent source/prior-store nonmutation; P8a/P8b reject new IDs |
| AC-WA15 | Log allowlist/count/type/privacy sentinels; threat boundaries and sensitive stdout documented |
| AC-WA16 | All11 unchanged harnesses plus12th installed wheel/Compose/AMD64/ARM64-QEMU, five checkpoints/four signals in separate processes |
| AC-WA17 | Frozen installs/Ruff format+check/mypy strict/full pytest/coverage>=85lines>=80branches/sdist+wheel/outside-source install/audit/secret scan |
| AC-WA18 | Separate nonauthor QA and final REVIEWER, own published runnable probes/helpers/oracles and final-SHA/tree attestations |
| AC-WA19 | ADR/API/storage, architecture/threat/logging/testing/recovery/debt synchronized; TD-001..005 remain OPEN |
| AC-WA20 | PR and complete report/public readback; four final full CI logs and preserved failures; no premature merge/closure |

Installed harness uses one synthetic manifest, P5a revisions, original P5b five
checkpoints/four actual signals, aliases/rules, ancient replay, preview, recompute
and new-outbox backup/restore in distinct processes. Preserve entire fixture and
all eleven earlier harnesses. UID10001/network none/read-only fixture mounts as
applicable. Local ARM64/QEMU stage timings plus >=3 backup and >=3 restore
controls when available; disclose absence and require CI regardless. No
physical-Pi qualification.

Exactly four existing CI jobs remain Quality, Compose, AMD64 and ARM64/QEMU.
Preserve full failures; no failed-job retries on the same SHA without authority.
Corrective commits receive fresh normal CI and renewed affected independent
reviews. Publish full sanitized runnable QA/REVIEWER sources/helpers/results and
all four complete logs with run/attempt/job URLs/digests, exact HEAD/tree,
platform and per-harness results. File presence, old CI or design probes are not
P8c implementation gates.

Engineering Lead alone integrates shared CLI/logging/harness/CI/docs/Git. ARQ/BE
owns new semantic/application files and additive source reader; DB-OWNER owns
new schema/storage. Final QA and REVIEWER must be different nonauthors and each
other. Only Orchestrator accepts, authorizes integration and closes P8c.
