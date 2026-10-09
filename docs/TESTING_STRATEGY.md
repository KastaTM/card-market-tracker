# Testing strategy

## P1a requirements

Core and adapter unit/contract tests cover UUID and relationship constraints,
explicit cross-provider and ES/EN aliases, homonyms, printing variants, unknowns,
sealed distinction, text card numbers, missing/null/wrong-type fields,
incompatible versions, duplicate keys/IDs, conflicting bindings, bounded work
and extra-field minimization. CLI integration tests verify deterministic results,
mixed/all-rejected/empty/global failure distinctions, no network, sanitized errors
and additive logging compatibility. P0 regression tests remain mandatory.
Fixtures are synthetic and provenance is recorded under `tests/fixtures`.

Installed wheel smoke runs outside the source tree. The same five catalog cases
run in Compose and both architecture images, alongside existing P0/non-root
checks. Docker catalog smoke disables networking and mounts fixtures read only;
Compose catalog has `network_mode: none`. QA and final REVIEWER are distinct
read-only agents, independent from authors and each other, and review exact
committed SHA/tree. Their test executions and findings belong in the PR ledger.

P0 tests prove observable behavior and failure paths without network access. Test configuration defaults, explicit env files, process-environment precedence, invalid settings, and secret-safe errors. Test CLI version and diagnose outputs, exit codes 0/1/2, writable and unwritable work directories, and absence of network calls. Test JSON shape, UTC timestamp, run_id propagation, allowlisting/redaction, and no duplicate logging handlers. QA should derive cases from risks and acceptance criteria rather than merely restating code paths.

Build and install the wheel outside the source tree to prove packaging; run version and diagnose from the installed wheel. Container smoke tests must run on `linux/amd64` and `linux/arm64`: build, version, valid diagnose, invalid configuration failure, and effective non-root UID. The CI ARM64 path uses QEMU emulation and does not prove operation on a physical Pi. Compose must run both one-shot services.

Fixtures belong under `tests/fixtures/`. Name synthetic inputs `synthetic_*` and describe what they model. Future real-source fixtures must be minimal, sanitized, legally permitted to retain, and accompanied by provenance and capture date. Never commit credentials, personal data, full payload dumps, or source data whose retention is unclear. Commercial provider contract tests and database recovery tests begin in their owning phases.

Use the [quality gate commands](QUALITY_GATES.md). Coverage applies to own runtime code with thresholds of at least 85% lines and 80% branches; critical modules must not be excluded to raise a percentage. Preserve failed-case output, tool versions, environment, and commit in the phase evidence report.
