# Logging contract v1

## Compatible P3a extension (2026-10-10)

P3a adds `persistence.completed` with `operation` restricted to
`init|persist|read|verify|backup|restore`. One invocation has one UUID `run_id`,
independent of the producer's stable batch token. Results extend the existing
allowlist with `replay`; `ok`, `empty`, `mixed`, `error` retain their meanings.
Every completed operation has nonnegative `duration_ms`. Processing counts use
the P1a integer fields. Confirmed storage changes use additional integer fields
`new_batch_count`, `new_entity_count`, `new_observation_count`, each 0..10000,
never bool. Replays report zero newly committed rows; storage failures omit these
counts, and stdout uses null, because attempted counts are not confirmed writes.
Read operations may emit bounded `observation_count`. No batch token is logged.

P3a fixed categories add `capture_required`, `capture_conflict`, `synthetic_only`,
`replay_conflict`, `storage_schema`, `storage_locked`, `storage_io`, `storage_corrupt`,
`storage_timeout`, `unsafe_destination`, and `resolution_mismatch`. Existing input and
identity categories remain valid. Errors contain categories only; logs never
contain payloads, observed names, SQL/values, paths, external references, batch
tokens, arbitrary messages or exception text. Unknown operations/categories and
malformed counts are omitted. These additions require executable formatter and
CLI redaction tests on the P3a candidate; this contract records the interface,
not a claim that the candidate gates have passed.

DB verification describes only compatibility/integrity in the storage contract;
no source or physical Pi health state is emitted.

## Compatible P1a extension (2026-10-09)

Existing P0 events and semantics remain valid. `catalog.completed` is added for
one offline batch operation, with `component=cli`, a per-operation UUID
`run_id`, nonnegative `duration_ms` and `result=ok|empty|mixed|error`.
Optional integer fields `input_count`, `accepted_count`, `candidate_count`,
`rejected_count` are bounded to 0..10000; bools and malformed values are omitted.
Error categories add `invalid_json`, `duplicate_key`, `input_io`, `input_limit`,
`invalid_shape`, `unsupported_version`, `invalid_field`, `duplicate_id`,
`broken_relation`, `contradictory_binding`, `duplicate_identity`, `identity_conflict`,
`missing_binding`, `unknown_variant`, `unknown_language`, `ambiguous_reference`.
Only fixed categories are emitted; arbitrary parser messages,
paths, references, names, raw input and exception text never enter stderr.
Additional categories/counts require explicit contract and test review.
This is additive within v1: consumers must tolerate new allowlisted events and
optional keys. P0's original event inventory below describes its own producer.

**Producer:** `card_market_tracker.logging_json`. **Consumer:** local stderr reader or future log collector. Each event is a single JSON object on one stderr line. P0 version/diagnose write human-readable success text to stdout; P1a catalog writes structured JSON results. Stderr JSON is the operation event stream.

| Field | Type | Rule |
| --- | --- | --- |
| `timestamp` | string | Required UTC ISO 8601 timestamp with `Z` suffix |
| `level` | string | Required Python logging level, e.g. `INFO` or `ERROR` |
| `event` | string | Required; one of `cli.version`, `diagnose.completed`, `config.invalid`; any other or missing value becomes `unstructured` |
| `component` | string | Required; P0 emits `cli` and normalizes any other value to `cli` |
| `run_id` | string | Required per-CLI-invocation UUID string; same ID across its events. `configure_logging` replaces an invalid supplied ID with a generated UUID. |
| `error_category` | string | Required on P0 failure events; allowlisted `configuration`, `local_execution`, `logging` |
| `result` | string | Optional `ok` or `error`, used by `diagnose.completed` |
| `duration_ms` | integer | Optional nonnegative milliseconds, used by `diagnose.completed` |

Current event names are `cli.version`, `diagnose.completed`, and `config.invalid`. At the default `INFO` level, successful diagnosis emits `diagnose.completed` with `result=ok` and duration; setting `CMT_LOG_LEVEL` to `WARNING` or `ERROR` suppresses that INFO event. On local execution failure it emits `diagnose.completed` with `result=error`, duration, and `error_category=local_execution`. Invalid configuration or arguments emit `config.invalid` with `error_category=configuration` and CLI exit code 2. A version request emits `cli.version`. Exit code 1 denotes local execution failure; 0 denotes success.

The formatter emits only allowlisted fields and never serializes the log message, exception text, environment values, env-file contents, directory path, or arbitrary `extra` attributes. Unknown event names become `unstructured`; missing/invalid optional values are omitted. Do not add raw external payloads to logs. A new event, field, or category needs contract and test review. `configure_logging` replaces its existing handler to avoid duplicates. This contract is tested by `tests/test_logging_acceptance.py` and CLI acceptance tests; a test result must still be recorded in the phase report.

Future source health must use explicit states such as unassessed, healthy, degraded, or failed, with assessment time and scope. A source that has not been checked cannot be labeled healthy. P0 emits no source-health event because it has no sources.
