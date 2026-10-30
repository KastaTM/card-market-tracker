"""Read-only P8d documentary design probe; never imports product or creates DB files.

Run from the P8d checkout: python -B docs/evidence/P8D_GATE_B/design_probe.py
Only SQLite :memory: and fixed format examples are exercised. This is author
design evidence, not independent QA, runtime acceptance, durability or Gate B.
"""

from __future__ import annotations

import ast
import contextlib
import hashlib
import io
import json
import re
import sqlite3
import subprocess
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

BASE = "9dda9fba0aa9646a67596657d4ae9a7088903808"
BASE_TREE = "dfd0414242cff364aad6082411ae88aef728783e"
ROOT = Path(__file__).resolve().parents[3]
SQL_DOC = "docs/data-contracts/WATCHLIST_TELEGRAM_DELIVERY_STORAGE_V1.md"
API_DOC = "docs/data-contracts/WATCHLIST_TELEGRAM_DELIVERY_V1.md"
ARCHIVES = {
    "P8D_BASELINE_AUDIT.md": "6aa7e5d706a6492a8947d5bba614ff36c4a96c4460ce3392a018fc5f87e952c4",
    "P8D_CODEX_ENGINEERING_BRIEF.md": (
        "ed08f263239a8d1e628bd5af1f7efa8fe3329df2901fb5ea03dbc6dae6352cb6"
    ),
    "P8D_MANUAL_WATCHLIST_TELEGRAM_DELIVERY_CONTRACT.md": (
        "9b5ec931250fd66f9660c9916153f4594ae021845c6dd9f643264f7df8e8d3e3"
    ),
}
PRODUCT = (
    "src",
    "tests",
    "scripts",
    ".github",
    "pyproject.toml",
    "uv.lock",
    "Dockerfile",
    "compose.yaml",
    "docker-compose.yml",
)


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def links(text: str) -> set[str]:
    return set(re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", text))


def main() -> None:
    assert Path.cwd().resolve() == ROOT, "Run from checkout root"
    assert git("show", "-s", "--format=%T", BASE).decode().strip() == BASE_TREE
    assert git("rev-parse", "origin/main").decode().strip() == BASE
    assert (
        git("branch", "--show-current").decode().strip() == "feat/p8d-watchlist-telegram-delivery"
    )
    # Includes committed AND unstaged/index differences from the authority base.
    git("diff", "--exit-code", BASE, "--", *PRODUCT)
    assert not git("ls-files", "--others", "--exclude-standard", "--", *PRODUCT).strip()
    for name, expected in ARCHIVES.items():
        relative = "docs/phases/" + name
        data = (ROOT / relative).read_bytes()
        assert sha(data) == expected, name
        assert git("show", "HEAD:" + relative) == data, "Archive Git blob bytes changed"

    allocations = []
    for path in sorted((ROOT / "src").rglob("*.py")):
        literals = {}
        for node in ast.parse(path.read_text(encoding="utf-8")).body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in {"APPLICATION_ID", "OWNER"}:
                        literals[target.id] = ast.literal_eval(node.value)
        if "APPLICATION_ID" in literals:
            allocations.append(
                {
                    "file": path.relative_to(ROOT).as_posix(),
                    "application_id": literals["APPLICATION_ID"],
                    "owner": literals.get("OWNER"),
                }
            )
    assert len(allocations) == 7
    assert len({item["application_id"] for item in allocations}) == 7
    assert len({item["owner"] for item in allocations}) == 7
    assert 0x434D545A not in {item["application_id"] for item in allocations}
    assert "card-market-tracker.watchlist-telegram-delivery" not in {
        item["owner"] for item in allocations
    }

    api = (ROOT / API_DOC).read_text(encoding="utf-8")
    vectors = []
    for digit, expected in (
        ("0", "b08e2920077a2f36ba634b32c0f1215e952063c55cfc99320ab55fbbdf9d36f5"),
        ("f", "810e8528fcea94a8ee848b56cb50ae04ff35bbaef05de8f667bddda896cac9d8"),
    ):
        canonical = (
            b'{"identity_version":1,"provider":"telegram","signal_id":"wsig1_'
            + digit.encode("ascii") * 64
            + b'"}'
        )
        literal = b"CMT_WATCHLIST_TELEGRAM_DELIVERY_V1\x00" + canonical
        assert len(literal) == 164 and literal.count(b"\x00") == 1
        assert sha(literal) == expected
        assert literal.hex() in api and expected in api
        assert (
            json.dumps(
                {"identity_version": 1, "provider": "telegram", "signal_id": "wsig1_" + digit * 64},
                sort_keys=True,
                ensure_ascii=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("ascii")
            == canonical
        )
        vectors.append({"example": digit * 1, "preimage_bytes": len(literal), "sha256": expected})

    raw = (ROOT / SQL_DOC).read_text(encoding="utf-8")
    section = raw.split("<!-- P8D_DDL_BEGIN -->", 1)[1].split("<!-- P8D_DDL_END -->", 1)[0]
    statements = re.findall(r"^\x60\x60\x60sql\n(.*?)\n\x60\x60\x60$", section, re.M | re.S)
    assert len(statements) == 34
    expected_catalog = []
    for kind, name, table, authority in re.findall(
        r"^\| (table|index|trigger) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|$", raw, re.M
    ):
        authority = authority.strip()
        sql = None if authority == "NULL" else statements[int(authority.split()[1]) - 1]
        expected_catalog.append((kind, name.strip(), table.strip(), sql))
    assert len(expected_catalog) == 45
    with sqlite3.connect(":memory:") as db:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA trusted_schema=OFF")
        for sql in statements:
            db.execute(sql)
        catalog = list(
            db.execute("SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name")
        )
        assert catalog == sorted(expected_catalog)
        assert Counter(row[0] for row in catalog) == {"index": 14, "table": 7, "trigger": 24}
        assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        assert list(db.execute("PRAGMA foreign_key_check")) == []
        assert all(
            row[-1] == 1 for row in db.execute("PRAGMA table_list") if row[1].startswith("wtd_")
        )
        claim_columns = {row[1] for row in db.execute("PRAGMA table_info(wtd_claims)")}
        assert "route_validated_at" in claim_columns

    # Entire reviewed, published in-document author probe; no product code.
    probes = re.findall(r"^\x60\x60\x60python\n(.*?)\n\x60\x60\x60$", raw, re.M | re.S)
    assert len(probes) == 1
    probe_namespace = {}
    capture = io.StringIO()
    with contextlib.redirect_stdout(capture):
        exec(compile(probes[0], "<P8d documentary SQL author probe>", "exec"), probe_namespace)
    assert probe_namespace["rejections"] >= 32
    assert "invalid SQL actions" in capture.getvalue()

    # Check only added links, preserving preexisting historical documentation.
    documents = sorted(
        set(
            git("diff", "--name-only", BASE, "--", "*.md").decode().splitlines()
            + git("ls-files", "--others", "--exclude-standard", "--", "*.md").decode().splitlines()
        )
    )
    checked_links = 0
    for relative in documents:
        path = ROOT / relative
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        base_blob = subprocess.run(
            ["git", "show", BASE + ":" + relative], cwd=ROOT, capture_output=True
        )
        previous = links(base_blob.stdout.decode("utf-8")) if base_blob.returncode == 0 else set()
        for target in links(text) - previous:
            if target.startswith(("http:", "https:", "#", "mailto:")):
                continue
            target_path = unquote(target.strip("<>").split("#", 1)[0])
            assert (path.parent / target_path).resolve().exists(), (relative, target)
            checked_links += 1

    files = (
        "docs/adr/0015-manual-watchlist-telegram-delivery.md",
        API_DOC,
        SQL_DOC,
        "docs/runbooks/WATCHLIST_TELEGRAM_DELIVERY.md",
        "docs/phases/P8D_SECURITY_DESIGN_REVIEW.md",
    )
    result = {
        "version": 1,
        "scope": "Author documentary design checks only; NOT runtime QA or Gate B acceptance",
        "observed_head": git("rev-parse", "HEAD").decode().strip(),
        "observed_tree": git("rev-parse", "HEAD^{tree}").decode().strip(),
        "working_tree_clean": not bool(
            git("status", "--porcelain=v1", "--untracked-files=all").strip()
        ),
        "python": sys.version.split()[0],
        "sqlite": sqlite3.sqlite_version,
        "baseline": BASE,
        "baseline_tree": BASE_TREE,
        "prior_product_paths_unchanged": True,
        "handoff_raw_blobs_match": True,
        "source_allocations": allocations,
        "candidate_application_id": {"ascii": "CMTZ", "hex": "0x434D545A", "decimal": 1129141338},
        "identity_format_vectors": vectors,
        "ddl_statements": len(statements),
        "inventory": {"tables": 7, "indexes": 14, "triggers": 24, "objects": 45},
        "literal_catalog_sha256": sha(
            json.dumps(catalog, ensure_ascii=True, separators=(",", ":")).encode("ascii")
        ),
        "sql_author_probe_stdout": capture.getvalue().strip(),
        "sql_author_negative_actions_rejected": probe_namespace["rejections"],
        "new_local_links_checked": checked_links,
        "design_document_sha256": {name: sha((ROOT / name).read_bytes()) for name in files},
        "not_exercised": [
            "P8d product code/admission/real process races/receipt authority/CLI",
            "durability/backup/restore/filesystem faults/deadlines",
            "full suite/coverage/build/install/audit/secret scan/four CI jobs/13 harnesses",
            "independent QA/final REVIEWER",
            "Telegram metadata/send/credentials",
        ],
        "result": "PASS",
    }
    print(json.dumps(result, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
