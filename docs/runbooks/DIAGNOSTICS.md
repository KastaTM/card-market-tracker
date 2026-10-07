# Diagnostic runbook

Run `cmt --version` to identify the installed package. Run `cmt diagnose` from a directory that should be used as the default work directory, or set `CMT_WORK_DIR` to an existing writable directory. The diagnostic validates settings and creates then removes a temporary local file. It makes no network calls and does not assess external sources, database state, or overall service health.

| Exit | Meaning | Action |
| --- | --- | --- |
| 0 | Version or diagnostic succeeded | Record stdout and the JSON stderr event if collecting evidence. |
| 2 | Invalid arguments, env file, log level, or work-directory setting | Check supported keys, precedence, file readability, and whether the directory exists. Do not paste sensitive values into reports. |
| 1 | Local work-directory probe failed | Check effective user, directory permissions, available space, and host/container mount settings. |

Configuration order: defaults (`INFO`, current working directory), explicitly selected `--env-file` (diagnose only), then process environment. An env file is not loaded automatically. A process environment value wins even if an env file has a different value. For a container, the image defaults `CMT_WORK_DIR=/tmp`; if a bind mount changes it, ensure UID 10001 can write there.

Read JSON stderr by `event`, `run_id`, `result`, and `error_category`; see [logging v1](../data-contracts/LOGGING_V1.md). `config.invalid` is category `configuration`; `diagnose.completed` with `result=error` is category `local_execution`. A log does not include the offending value or path by design. If a check still fails, record command, exit code, sanitized environment description, platform, and commit for investigation.
