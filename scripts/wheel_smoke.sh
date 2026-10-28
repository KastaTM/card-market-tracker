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
env -u PYTHONPATH "$outside/venv/bin/python" "$repo/scripts/discovery_smoke.py" --mode installed --executable "$outside/venv/bin/cmt" --fixtures "$repo/tests/fixtures"
env -u PYTHONPATH "$outside/venv/bin/python" "$repo/scripts/pinned_repository_smoke.py" --mode installed --executable "$outside/venv/bin/cmt" --fixtures "$repo/tests/fixtures"
env -u PYTHONPATH "$outside/venv/bin/python" "$repo/scripts/scoped_capture_discovery_smoke.py" --mode installed --executable "$outside/venv/bin/cmt" --fixtures "$repo/tests/fixtures"
env -u PYTHONPATH "$outside/venv/bin/python" "$repo/scripts/multi_revision_metadata_smoke.py" --mode installed --executable "$outside/venv/bin/cmt" --fixtures "$repo/tests/fixtures"
env -u PYTHONPATH "$outside/venv/bin/python" "$repo/scripts/discovery_journal_smoke.py" --mode installed --executable "$outside/venv/bin/cmt" --fixtures "$repo/tests/fixtures"
env -u PYTHONPATH "$outside/venv/bin/python" "$repo/scripts/alert_outbox_smoke.py" --mode installed --executable "$outside/venv/bin/cmt" --fixtures "$repo/tests/fixtures"
env -u PYTHONPATH "$outside/venv/bin/python" "$repo/scripts/telegram_delivery_smoke.py" --mode installed --executable "$outside/venv/bin/cmt" --fixtures "$repo/tests/fixtures"
env -u PYTHONPATH "$outside/venv/bin/python" "$repo/scripts/watchlist_smoke.py" --mode installed --executable "$outside/venv/bin/cmt" --fixtures "$repo/tests/fixtures"
env -u PYTHONPATH "$outside/venv/bin/python" "$repo/scripts/watchlist_journal_smoke.py" --mode installed --executable "$outside/venv/bin/cmt" --fixtures "$repo/tests/fixtures"
env -u PYTHONPATH "$outside/venv/bin/python" "$repo/scripts/watchlist_alert_outbox_smoke.py" --mode installed --executable "$outside/venv/bin/cmt" --fixtures "$repo/tests/fixtures"
