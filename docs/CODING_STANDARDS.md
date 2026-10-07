# Coding standards

Use Python 3.13 and the `src/` package layout. Prefer small typed functions, standard-library features, and explicit error paths. Add a dependency only for an implemented capability, then update and review `uv.lock` explicitly. Use `uv sync --frozen` for installation and `uv run --frozen` for checks so validation cannot silently rewrite the lockfile.

Ruff formatting and linting plus strict mypy are required. The project uses a 100-character line length. Keep module boundaries small: CLI parses and reports; configuration validates settings; logging serializes allowlisted events. Future adapters must not leak provider models into the domain. Avoid empty shells for future features.

Never log raw configuration values, secrets, file contents, external payloads, or arbitrary exception messages. Use stable events and error categories from [logging v1](data-contracts/LOGGING_V1.md). Treat all future external data as untrusted; validation must precede normalization and domain use. Changes to public data shapes need a versioned contract and compatibility assessment.

Record significant decisions in an ADR with context, decision, alternatives, consequences, status, and revisit conditions. Keep tests deterministic and independent of the Internet. Document any exception to a gate with scope, reason, impact, owner, and revisit trigger; do not hide findings with broad exclusions.
