# Logging contract v1

**Producer:** `card_market_tracker.logging_json`. **Consumer:** local stderr reader or future log collector. Each event is a single JSON object on one stderr line. The CLI writes human-readable success text to stdout; stderr JSON is the machine-facing stream.

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
