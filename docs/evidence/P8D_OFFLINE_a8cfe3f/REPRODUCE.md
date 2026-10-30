# Reproduce the offline evidence

Use a fresh isolated checkout of source commit
a8cfe3f4e9e2bc50558f3a9aee13a1fbd9bf6abd, tree
820ddbdfc278ada9b2d713a1c0b834f5d59e5dbd. Keep historical worktrees untouched.
Check Git identity and a pristine status before and after. The immutable GitHub candidate is the source reference; Git-based qualification helpers need the actual checkout. Binary/source archives remain in the local full dossier.

Run the unchanged two-stage frozen installation, then:

    uv sync --frozen --no-install-project
    uv sync --frozen --no-build-isolation
    uv run --frozen ruff format --check .
    uv run --frozen ruff check .
    uv run --frozen mypy src
    uv run --frozen coverage run -m pytest
    uv run --frozen coverage json -o coverage.json
    uv run --frozen python scripts/check_coverage.py coverage.json
    uv run --frozen python scripts/p8d_qa_probe.py --fixtures tests/fixtures --mode all
    uv run --frozen python scripts/p8d_reviewer_probe.py

The committed probes derive genuine originals themselves and use fake transport.
They do not import author tests. QA and REVIEWER extras are complete in this
dossier; restore their original ignored relative paths before invoking them.
QA's ROOT is relative to that original location; reviewer's REPORT uses the
original ignored location. Running directly from the published docs directory
would therefore be incorrect. From the exact candidate root, execute this Python
using its development environment after verifying the dossier MANIFEST:

    import pathlib, subprocess
    subprocess.run(["git", "fetch", "origin",
                    "refs/heads/evidence/p8d-offline-a8cfe3f"], check=True)
    pairs = [
        ("qa/a8cfe3f/extra_probe.py",
         ".p8d-evidence/final/qa/a8cfe3f/extra_probe.py"),
        ("reviewer/a8cfe3f/independent_extra_probe.py",
         ".p8d-evidence/final/reviewer/a8cfe3f/independent_extra_probe.py"),
    ]
    for source, target in pairs:
        output = pathlib.Path(target)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(subprocess.check_output([
            "git", "show",
            "FETCH_HEAD:docs/evidence/P8D_OFFLINE_a8cfe3f/" + source]))

Then run from the candidate root:

    uv run --frozen python -B .p8d-evidence/final/qa/a8cfe3f/extra_probe.py
    uv run --frozen python -B .p8d-evidence/final/reviewer/a8cfe3f/independent_extra_probe.py

The published run_final_qa.py is the original Windows orchestration record
(.venv/Scripts/python.exe); use it only at its original ignored path on Windows.
The direct probe commands above work without that Windows-only orchestration.
On Linux one preexisting Windows-junction test skips; the captured Windows host
has a preexisting unavailable-symlink skip. No P8d test is filtered.

Package and environment gates:

    uv build --no-build-isolation
    sh scripts/wheel_smoke.sh
    sh scripts/container_smoke.sh cmt-p8d-review:amd64 linux/amd64
    sh scripts/container_smoke.sh cmt-p8d-review:arm64 linux/arm64

wheel_smoke installs outside source and retains all13 harnesses. On Windows use
an outside venv and the exact13 commands in gates/RESULTS.json; do not use editable
imports or PYTHONPATH. Compose uses the exact full commands in the candidate
.github/workflows/ci.yml; preserve fixtures, UID10001/private files, network none
and all13 harnesses. QEMU needs Docker/binfmt support. The P8d harness prints
three separate per-operation full-fixture backup/restore controls; do not replace
them with job duration, enlarge contractual limits or infer native Pi results.

    uv export --frozen --all-groups --no-emit-project -o requirements-audit.txt
    uv run --frozen pip-audit -r requirements-audit.txt
    uv run --frozen python scripts/check_secret_scan.py

Original exact-candidate commands, durations, full logs, coverage JSON, distinct
source hashes and actual CI job URLs accompany this dossier. Historical FAIL
records remain separate. Do not rerun failed same-SHA CI to obtain green.

No command here authorizes or performs real Telegram qualification. Future
real validate/send is a different operator/Phase Lead decision under the
WATCHLIST_TELEGRAM_QUALIFICATION runbook. The fake tests' fabricated authorization
and explicit installed-wheel prerequisite substitution have no real authority.

