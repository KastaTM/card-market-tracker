# Offline Alert Outbox API, identity and CLI v1

**Status:** frozen implementation contract; phase acceptance remains the Orchestrator's decision.
**Authority:** Orchestrator P8a contract and ADR-0010. Existing Journal v1 / Discovery v3 unchanged.

## Admission

Input `(captures_db:Path,journal_db:Path,outbox_db:Path,comparison_id:cmp3,destination_key:Alias,timeout:float=2)`; all paths distinct, existing and owner-verified, no implicit init. Read one journal comparison with its full canonical request/result and digest, re-run P1c original capture validation and unmodified Discovery v3 pure compare, ensure canonical complete equality and ID, and prepare the same frozen result. Zero writes if any failure or if result is baseline/no_discoveries. No `latest`, bulk scan or self-attested result DTO. One comparison maximum 1000 events and one enqueue maximum 16 MiB canonical content.

## Policy, intrinsic intention, and renderer

Policy `discovery_reference_alert_v1`. Types `SET_REFERENCE_FIRST_OBSERVED`, `CANDIDATE_REFERENCE_FIRST_OBSERVED` only. Channel `offline_preview`, state `pending`. Destination grammar ASCII `^[a-z][a-z0-9_-]{0,63}$` (1..64); alias is not a Telegram chat/contact/credential. Intrinsic intention JSON, strict exact keys:

```
{
  "version":1,
  "policy_version":"discovery_reference_alert_v1",
  "renderer_version":1,
  "channel":"offline_preview",
  "event_id":"evt3:<64 lowercase hex>",
  "type":"SET_REFERENCE_FIRST_OBSERVED | CANDIDATE_REFERENCE_FIRST_OBSERVED",
  "reference":{"namespace":"...","kind":"...","external_id":"...","language":"... or null","variant":"..."},
  "status":"accepted | candidate",
  "category":"... or null",
  "cmt_id":"uuid-v4 or null",
  "current_batch_id":"uuid-v4",
  "captured_at":"canonical UTC source capture time",
  "first_observed_in_window_at":"canonical UTC capture time",
  "profile":"tcgdex_swsh3_136_r0_r1_v1 | synthetic_multi_revision_v1",
  "evidence_level":"verified_local_pinned_bundle | producer_declared",
  "mode":"pinned | synthetic"
}
```

The source `reference` has exactly the five serialized Discovery v3 keys shown above, validated with the existing `parse_reference`. Namespace/external ID remain bounded ASCII tokens; this phase does not widen source grammar. `evidence_level` derives from verified `current.evidence_state` and `mode` from verified `current.mode`. Synthetic requires `(synthetic,producer_declared)` and the exact real profile requires `(pinned,verified_local_pinned_bundle)`. No destination, history or comparison_id enters the intrinsic intention. Exact event and all window/history remain in the association. Intent canonical text is at most 64 KiB.

Canonical function: UTF-8 value to ASCII text with `json.dumps(ensure_ascii=True,sort_keys=True,separators=(',', ':'),allow_nan=False)`, with finite typed JSON and bounded validated input. Alert ID:

```
alt1: + sha256(ASCII({"identity_version":1,"destination_key":alias,"event_id":evt3})).hexdigest()
```

Independent test vector (not an actual event): `destination_key = local-preview`, `event_id = evt3:` plus 64 ASCII `0` chars. Exact ASCII preimage:

```
{"destination_key":"local-preview","event_id":"evt3:0000000000000000000000000000000000000000000000000000000000000000","identity_version":1}
```

Expected ID `alt1:acb91b4f47f23723329afbc7dde2857cf3da79e52446485784570284a0f2826f`.

Renderer version integer 1. Deterministic UTF-8 plaintext, max 4096 bytes; no HTML/Markdown interpretation. Control, nonprintable and Unicode category C characters use the contents of their ASCII JSON string encoding, without quotes (for example CR=`\r`, LF=`\n`, ESC=`\u001b`, bidi override=`\u202e`); literal backslashes double. Other printable Unicode remains unchanged. Raw event values stay in evidence. The first three lines are `SYNTHETIC demonstration` (or `Pinned local evidence`), `Accepted set reference` (or `Unaccepted candidate reference`), and `First observed in selected comparison window.` Reference fields follow in sorted-key order as `key: value`, then category, cmt_id, current_batch_id, captured_at, first_observed_in_window_at, profile, evidence_level, mode, event_id. Null displays as `null`; lines join with LF and have no final LF. Oversize text fails rather than truncating. No names/links are invented. Message digest is lowercase SHA256 of raw UTF-8 message bytes; intention/event digests hash canonical ASCII JSON.

## Public CLI

Group: `cmt alert-outbox`. Every command takes `--outbox-db PATH`, `--timeout NUMBER` default2 max5, and never silently initializes. Commands:

| Command | Required additions | Optional arguments |
| --- | --- | --- |
| `init` | none | none |
| `enqueue` | `--captures-db`, `--journal-db`, `--comparison-id`, `--destination-key` | none |
| `get` | `--alert-id` | none |
| `list` | none | `--destination-key`, `--limit` default100 max1000, `--cursor ALT1` |
| `evidence-list` | `--alert-id` | `--limit`, `--cursor CMP3` |
| `evidence-get` | `--alert-id`, `--comparison-id` | none |
| `preview` | `--alert-id` | none |
| `verify` | none | none |
| `recompute` | `--captures-db`, `--journal-db`, `--alert-id`, `--comparison-id` | none |
| `backup` / `restore` | `--destination NEW_PATH` | none |

Every response has `version` integer1, `operation` (exact command name), and `result`. Canonical stdout is one ASCII JSON object plus LF. Exact success additions:

| Operation | Additional keys |
| --- | --- |
| init | schema_version integer1 |
| enqueue | comparison_id, alerts_new, alerts_existing, associations_new, associations_existing, events (five integer counts) |
| get | alert object |
| list | items array of alert summaries, next_cursor (alt1 or null) |
| evidence-list | alert_id, items array of evidence summaries, next_cursor (cmp3 or null) |
| evidence-get | alert_id, comparison_id, event, journal_content_sha256, event_sha256 |
| preview | alert_id, message_text, renderer_version, policy_version, channel, state |
| verify | level=`local`, counts={alerts,associations} |
| recompute | level=`origin-recompute`, alert_id, comparison_id |
| backup, restore | counts={alerts,associations} |

`alert` has exactly alert_id, destination_key, event_id, channel, policy_version, renderer_version, intent (decoded object), intent_sha256, message_text, message_sha256, first_prepared_at, state. Alert summaries omit intent/message_text and retain the other ten fields. Evidence summaries have exactly comparison_id, journal_content_sha256, event_sha256. Evidence-get supplies the full decoded frozen event. Integer renderer_version is always1, channel is always offline_preview, state always pending. first_prepared_at is the first insertion's UTC timestamp with six fractional digits, separate from source clocks.

Enqueue result is `inserted` if ANY new alert or association is added, including a mixed operation with existing alerts and new associations; `replay` if no row is added, including a zero-event baseline/no_discoveries. Four counters are disjoint: alerts_new+alerts_existing=events and associations_new+associations_existing=events. Every other success uses `ok`. Failure has exactly version, operation, result=`error`, error_category; parser failures use operation=`alert-outbox`. No partial output precedes failures.

Exit0 successful; exit2 unsupported event/profile, invalid inputs, immutable conflict, limit, invalid-field, bad JSON; exit1 source/path/IO/locked/schema/corrupt/missing/deadline/recompute mismatch. Do not log destination alias/reference/message/path. Logs: fixed component/operation, run_id, duration_ms, result, error_category, bounded alert/association counts. CLI stdout and DB/backups are locally sensitive and require restricted access.

## Semantic requirements

- Unique `(destination_key,event_id)` and alt1, conflict not overwrite for differing intrinsic intent/message/version.
- Association unique `(alert_id,comparison_id)`, includes journal SHA256 and complete canonical v3 event, including history and original indexes; same evt3/two cmp3 => exactly two rows.
- Replay no re-writing of original data or `first_prepared_at`; after restore stable IDs/messages/clocks.
- `preview` is strictly read-only and does not act as transport, advance state or log payloads.
- `verify` checks local consistency only; a coherent rewrite is not source authenticity. `recompute` requires exact association and matches parent source with originals; altered/missing source FAIL. Both read-only.
- No auto-send or exactly-once delivery semantics; pending is not sent/delivered.

## Bounds

- One explicit comparison per enqueue, at most 1000 events, 16 MiB canonical prepared content in total, 4096 UTF-8 bytes/message.
- Queries 100 summaries default, hard cap 1000 and 1 MiB canonical response; ascending keyset pagination, pages do not share one cross-request snapshot under insertion.
- `evidence-get` explicit single association, ceiling compatible with journal result 16 MiB; reject unbounded expansion.
- Timeout positive finite nonbool max5s, default2s, shared enqueue deadline across verification/preparation/commit, no stage reset. OS blocking may exceed cooperative deadline. Local whole-DB verify timeout is failure, not partial PASS.

## Internal authority and snapshot semantics

The application freezes one locally validated journal request/result and its semantic digest, recomputes it from original verified captures, and demands complete canonical equality plus cmp3. All prepared rows derive from that frozen pair. Storage accepts only a private receipt issued after this process. Its canonical envelope contains exactly comparison_id, journal_content_sha256 and all prepared rows; an internal seal binds the complete content and the exact issued receipt instance. Public construction, boolean flags, shallow/deep copies and post-validation mutation fail. This is an application boundary, not authentication against privileged in-process Python execution.

The three files do not share a distributed transaction. Enqueue represents the retained journal snapshot matched against the capture reader's verified snapshot before the atomic outbox commit. Original admitted captures and journal comparisons are assumed immutable during that interval; later changes require explicit origin recomputation. Local verify cannot detect every coherent rewrite.
