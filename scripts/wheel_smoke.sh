#!/usr/bin/env sh
set -eu

repo="$(pwd)"
outside="$(mktemp -d)"
uv venv --python 3.13 "$outside/venv"
uv pip install --python "$outside/venv/bin/python" "$repo"/dist/*.whl
cd "$outside"
env -u PYTHONPATH "$outside/venv/bin/cmt" --version
env -u PYTHONPATH "$outside/venv/bin/cmt" diagnose
env -u PYTHONPATH "$outside/venv/bin/python" "$repo/scripts/catalog_smoke.py" --mode installed --executable "$outside/venv/bin/cmt" --fixtures "$repo/tests/fixtures"
env -u PYTHONPATH "$outside/venv/bin/python" "$repo/scripts/observation_persistence_smoke.py" --mode installed --executable "$outside/venv/bin/cmt" --fixtures "$repo/tests/fixtures"
