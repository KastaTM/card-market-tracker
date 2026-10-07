"""Fail separately on P0 runtime line and branch coverage thresholds."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    totals = report["totals"]
    lines = totals["covered_lines"] / totals["num_statements"] * 100
    branches = totals["covered_branches"] / totals["num_branches"] * 100
    print(f"runtime lines: {lines:.2f}% (required >=85%)")
    print(f"runtime branches: {branches:.2f}% (required >=80%)")
    return 0 if lines >= 85 and branches >= 80 else 1


if __name__ == "__main__":
    raise SystemExit(main())
