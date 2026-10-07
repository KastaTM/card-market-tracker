"""Scan exactly tracked source files, reporting candidates without their values."""

from __future__ import annotations

import json
import subprocess


def main() -> int:
    tracked = (
        subprocess.run(["git", "ls-files", "-z"], capture_output=True, check=True)
        .stdout.decode("utf-8")
        .split("\0")
    )
    paths = [path for path in tracked if path]
    scan = subprocess.run(
        ["detect-secrets", "scan", *paths], capture_output=True, text=True, check=True
    )
    report = json.loads(scan.stdout)
    findings = report.get("results", {})
    for path, candidates in sorted(findings.items()):
        for candidate in candidates:
            print(
                f"{path}:{candidate.get('line_number', '?')}: "
                f"{candidate.get('type', 'unknown')} candidate"
            )
    if findings:
        print("Secret scan: FAIL; review each candidate")
        return 1
    print("Secret scan: PASS (no candidates)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
