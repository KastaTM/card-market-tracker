# Local development runbook

Use Python 3.13 and uv 0.12.10. Begin from a clean checkout at a recorded commit. `uv sync --frozen` installs from `uv.lock` without resolving or changing it. Dependency updates are explicit (`uv lock` after an intentional `pyproject.toml` change) and require review.

```sh
uv sync --frozen
uv run --frozen cmt --version
uv run --frozen cmt diagnose
uv run --frozen ruff format --check .
uv run --frozen ruff check .
uv run --frozen mypy src
uv run --frozen coverage run -m pytest
uv run --frozen coverage json -o coverage.json
uv run --frozen python scripts/check_coverage.py coverage.json
uv build --no-build-isolation
```

The build command checks package creation. On Linux, run `sh scripts/wheel_smoke.sh` after the build: it creates a temporary virtual environment outside the repository, installs the wheel, changes to that external directory, clears `PYTHONPATH`, and runs version and diagnose. CI runs the same script. On Windows, create a temporary virtual environment outside the repository with `uv venv --python 3.13`, install the built wheel into its `Scripts/python.exe` with `uv pip install --python`, change to that external directory, clear `PYTHONPATH`, and invoke `Scripts/cmt.exe --version` and `Scripts/cmt.exe diagnose`. Record the wheel, environment, command output, and exit codes in the phase report. For a local override, copy `.env.example` to an ignored `.env` and run `uv run --frozen cmt diagnose --env-file .env`. Do not commit real values.

With Docker running, `docker compose run --rm version` and `docker compose run --rm diagnose` run the two P0 commands. On a shell with Docker Buildx and QEMU support, run `sh scripts/container_smoke.sh cmt-p0-amd64 linux/amd64` and `sh scripts/container_smoke.sh cmt-p0-arm64 linux/arm64`. The script checks version, valid and invalid diagnose, and non-root UID. ARM64 emulation is early compatibility evidence, not physical Pi acceptance.

For the security gates, CI exports the frozen dependency set for `pip-audit` and runs `uv run --frozen python scripts/check_secret_scan.py`. That script asks Git for the exact tracked file paths and passes them to `detect-secrets scan`; it reports candidate line numbers and detector types without values. See `.github/workflows/ci.yml` for the exact command sequence. Preserve scanner output and handle findings, rather than recording a clean result without an executed scan.
