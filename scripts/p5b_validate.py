"""Reproduce local P5b gates and retain complete logs bound to one clean commit."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HARNESSES = (
    "catalog",
    "observation_persistence",
    "discovery",
    "pinned_repository",
    "scoped_capture_discovery",
    "multi_revision_metadata",
    "discovery_journal",
    "alert_outbox",
    "telegram_delivery",
    "watchlist",
    "watchlist_journal",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--expected-tree", required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent

    def git(*values: str) -> str:
        return subprocess.check_output(["git", *values], cwd=root, text=True).strip()

    def identity() -> None:
        assert git("rev-parse", "HEAD") == args.expected_head, "HEAD mismatch"
        assert git("rev-parse", "HEAD^{tree}") == args.expected_tree, "tree mismatch"
        assert not git("status", "--porcelain"), "dirty tracked/untracked source"

    identity()
    logs = root / ".p5b-evidence" / args.expected_head / "local"
    logs.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, object]] = []

    def run(name: str, command: list[str], *, cwd: Path = root) -> None:
        environment = dict(os.environ)
        environment.pop("PYTHONPATH", None)
        environment.pop("CMT_TELEGRAM_BOT_TOKEN", None)
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=environment,
            text=True,
            capture_output=True,
            timeout=1200,
        )
        logfile = logs / (name + ".txt")
        logfile.write_text(
            json.dumps(
                {
                    "head": args.expected_head,
                    "tree": args.expected_tree,
                    "command": command,
                    "cwd": str(cwd),
                    "exit_code": completed.returncode,
                }
            )
            + "\nSTDOUT\n"
            + completed.stdout
            + "\nSTDERR\n"
            + completed.stderr,
            encoding="utf-8",
        )
        results.append({"name": name, "exit_code": completed.returncode, "log": str(logfile)})
        print(name + ": " + ("PASS" if completed.returncode == 0 else "FAIL"), flush=True)
        if completed.returncode:
            print(completed.stdout + completed.stderr, flush=True)
            raise RuntimeError("gate failed: " + name)

    try:
        run("frozen-dependencies", ["uv", "sync", "--frozen", "--no-install-project"])
        run("frozen-project", ["uv", "sync", "--frozen", "--no-build-isolation"])
        run("format", ["uv", "run", "--frozen", "ruff", "format", "--check", "."])
        run("lint", ["uv", "run", "--frozen", "ruff", "check", "."])
        run("mypy", ["uv", "run", "--frozen", "mypy", "src"])
        run("pytest-coverage", ["uv", "run", "--frozen", "coverage", "run", "-m", "pytest"])
        run("coverage-json", ["uv", "run", "--frozen", "coverage", "json", "-o", "coverage.json"])
        run(
            "coverage-thresholds",
            ["uv", "run", "--frozen", "python", "scripts/check_coverage.py", "coverage.json"],
        )
        run("build", ["uv", "build", "--no-build-isolation"])
        with tempfile.TemporaryDirectory(prefix="cmt-p5b-installed-") as temporary:
            outside = Path(temporary)
            venv = outside / "venv"
            run("wheel-venv", ["uv", "venv", "--python", "3.13", str(venv)])
            python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            wheel = root / "dist/card_market_tracker-0.1.0-py3-none-any.whl"
            run("wheel-install", ["uv", "pip", "install", "--python", str(python), str(wheel)])
            offline = (
                "import sys;sys.addaudithook(lambda e,a: "
                "(_ for _ in ()).throw(RuntimeError('network denied')) "
                "if e.startswith('socket.') else None);"
                "from card_market_tracker.cli import main;sys.exit(main(sys.argv[1:]))"
            )
            run("installed-version", [str(python), "-I", "-c", offline, "--version"], cwd=outside)
            run("installed-diagnose", [str(python), "-I", "-c", offline, "diagnose"], cwd=outside)
            for name in HARNESSES:
                run(
                    "smoke-" + name,
                    [
                        str(python),
                        str(root / "scripts" / (name + "_smoke.py")),
                        "--mode",
                        "installed",
                        "--fixtures",
                        str(root / "tests/fixtures"),
                    ],
                    cwd=outside,
                )
        run(
            "audit-export",
            [
                "uv",
                "export",
                "--frozen",
                "--all-groups",
                "--no-emit-project",
                "-o",
                "requirements-audit.txt",
            ],
        )
        run(
            "dependency-audit",
            ["uv", "run", "--frozen", "pip-audit", "-r", "requirements-audit.txt"],
        )
        run("secret-scan", ["uv", "run", "--frozen", "python", "scripts/check_secret_scan.py"])
        identity()
        result = "PASS"
    except Exception as error:
        print(str(error), file=sys.stderr)
        result = "FAIL"
    report = {
        "head": args.expected_head,
        "tree": args.expected_tree,
        "result": result,
        "gates": results,
        "containers": "Separate CI evidence required; local runner does not certify Docker",
    }
    (logs / "summary.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, sort_keys=True))
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
