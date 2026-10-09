"""Verify installed CLI behavior without importing the source package."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from uuid import UUID


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("installed", "docker", "compose"), required=True)
    parser.add_argument("--executable", default="cmt")
    parser.add_argument("--image", default="cmt-p1a-smoke")
    parser.add_argument("--platform", default="linux/amd64")
    parser.add_argument("--fixtures", type=Path, required=True)
    args = parser.parse_args()
    fixtures = args.fixtures.resolve()
    if args.mode == "installed":
        prefix = [args.executable]
        data_path = str(fixtures)
    elif args.mode == "docker":
        prefix = [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--platform",
            args.platform,
            "--mount",
            f"type=bind,source={fixtures},target=/fixtures,readonly",
            args.image,
        ]
        data_path = "/fixtures"
    else:
        prefix = ["docker", "compose", "run", "--rm", "-T", "catalog"]
        data_path = "/fixtures"
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    for case, expected in (
        ("valid", 0),
        ("mixed", 3),
        ("empty", 0),
        ("invalid", 2),
        ("candidates", 3),
    ):
        command = prefix + [
            "catalog",
            "--input",
            f"{data_path}/synthetic_tcgdex_{case}.json",
            "--manifest",
            f"{data_path}/synthetic_manifest.json",
        ]
        first = subprocess.run(
            command, capture_output=True, text=True, env=environment, timeout=120
        )
        assert first.returncode == expected, f"{case}: exit {first.returncode}, expected {expected}"
        result = json.loads(first.stdout)
        expected_counts = {
            "valid": (7, 0, 0),
            "mixed": (1, 1, 1),
            "empty": (0, 0, 0),
            "candidates": (0, 2, 0),
        }
        if case == "invalid":
            assert result["result"] == "error" and result["counts"] is None
        else:
            counts = result["counts"]
            assert (
                counts["accepted"],
                counts["candidates"],
                counts["rejected"],
            ) == expected_counts[case]
            assert counts["input"] == sum(expected_counts[case])
            ids = [entity["cmt_id"] for entity in result["entities"]]
            assert ids == sorted(set(ids))
        logs = [
            json.loads(line) for line in first.stderr.splitlines() if line.strip().startswith("{")
        ]
        completed = [item for item in logs if item.get("event") == "catalog.completed"]
        assert len(completed) == 1, f"{case}: missing or duplicate operation event"
        UUID(completed[0]["run_id"])
        assert completed[0]["duration_ms"] >= 0
        if case != "invalid":
            assert completed[0]["input_count"] == counts["input"]
            assert completed[0]["accepted_count"] == counts["accepted"]
            assert completed[0]["candidate_count"] == counts["candidates"]
            assert completed[0]["rejected_count"] == counts["rejected"]
        if case == "valid":
            second = subprocess.run(
                command, capture_output=True, text=True, env=environment, timeout=120
            )
            assert second.returncode == 0 and json.loads(second.stdout) == result
        print(f"catalog {args.mode} {case}: PASS (exit {expected})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
