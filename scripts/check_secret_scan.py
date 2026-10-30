"""Scan exactly tracked source files, reporting candidates without their values."""

from __future__ import annotations

import json
import subprocess
from hashlib import sha1

# Exact public cryptographic identifiers, independently verified for P1b; these
# are not credentials. Owner SEC/Lead; rationale/revisit in SECURITY_SCANNING.md.
_REVISION = "4199850a6af49665db0080fa2bb9ef751750a406"  # pragma: allowlist secret
_MIT = (
    "12e7dd2d018848b9997d0226c4632f01da86ec4bf6ebe0c8b19953d5e5eeb6ff"  # pragma: allowlist secret
)
_BUNDLE = (
    "3b43e1a78c117ef1ecb5cf200a4b2fc7e57af8fd29e3fcf29b06f4291ae58085"  # pragma: allowlist secret
)
_PROJECTION = (
    "53100248a987378fb3ca2273b7ec219747b876b515f57087faf6becdd0caa479"  # pragma: allowlist secret
)
_ARTIFACTS = {
    "db48bc4a054b3b1c5bd2b6956257f20ba251c79c",  # pragma: allowlist secret
    "6db89c69b56552fa4e09f26e0e90d14e97466411",  # pragma: allowlist secret
    "c67ded0d5f0abc77b4fbdbfd37312f2a88de1b55",  # pragma: allowlist secret
    "77bc8108c2cdb54c663e1fdf8c4502ac65f88734",  # pragma: allowlist secret
    "4bed34217397bcfeee8925868b50816051022d1bbdb60b63eac702ae6f6bd70a",  # pragma: allowlist secret
    "bd5ab2a350fe4b453d468f8b89aa904d26b4b57c4c2d62d330111a28a92a4be6",  # pragma: allowlist secret
    "82ab33624f52569fd3b45991d90c840e8b7d77969a1b5d52071a6782cd791de5",  # pragma: allowlist secret
    _MIT,
}
_ORIGINALS = _ARTIFACTS | {_REVISION}
_PACKAGE = _ORIGINALS | {_PROJECTION}
_R1 = "af57972e8f784c2507ab9e573c99bf02ae2e5e42"  # pragma: allowlist secret
_BUNDLE_V2 = (
    "e3b6ec38358a8fc089e65a365fe2f5566459df441e67c3e8ad51b3b5352b50c0"  # pragma: allowlist secret
)
_R1_ORIGINALS = _ARTIFACTS | {_R1}
_R1_PACKAGE = _R1_ORIGINALS | {_PROJECTION}
_P5B_IDENTITY = (
    "6851dd085c9769e1df357e3ff330a02ea815baa48f60d8556f9f173f87c488de"  # pragma: allowlist secret
)
_PUBLIC_DIGESTS = {
    "docs/sources/P1B_REQUEST_LEDGER.json": _ORIGINALS,
    "src/card_market_tracker/pinned_repository/approved_bundle_v1.json": _PACKAGE,
    "tests/fixtures/pinned_repository_bundle_v1.json": _PACKAGE,
    "src/card_market_tracker/pinned_repository/bundle.py": {_REVISION, _BUNDLE},
    "tests/test_pinned_repository.py": {_MIT},
    "docs/sources/P1C_REQUEST_LEDGER.json": _R1_ORIGINALS,
    "src/card_market_tracker/pinned_repository/approved_bundle_v2.json": _R1_PACKAGE,
    "tests/fixtures/pinned_repository_bundle_v2.json": _R1_PACKAGE,
    "src/card_market_tracker/pinned_repository/bundle_v2.py": {_R1, _BUNDLE_V2},
    "tests/fixtures/p5b_identity_vectors_v1.json": {_P5B_IDENTITY},
}

# P8d exact public Git/content IDs and independently checked synthetic vectors.
_P8D_BASE = "9dda9fba0aa9646a67596657d4ae9a7088903808"  # pragma: allowlist secret
_P8D_TREE = "dfd0414242cff364aad6082411ae88aef728783e"  # pragma: allowlist secret
_P8D_PARENT1 = "228d5c8d0d91edf03ddb86a489c8232eeb7c08bc"  # pragma: allowlist secret
_P8D_PARENT2 = "d82aba73d9bc0eb455f8664e3ccddc0134ea9d9c"  # pragma: allowlist secret
_P8D_OLDHEAD = "f80bc8cdb877946f37d76b09212d68dd8da3e246"  # pragma: allowlist secret
_P8D_OLDTREE = "dde865b6d215efc4075918088d6deddfe7cdeb1f"  # pragma: allowlist secret
_P8D_DESIGNHEAD = "50fcb55a0b0e467bcb9d94561412a0f3c6ebc8f9"  # pragma: allowlist secret
_P8D_DESIGNTREE = "d8d3eac1580dbfb3fa6aafcf94d033a8781204e2"  # pragma: allowlist secret
_P8D_AUDIT = (
    "6aa7e5d706a6492a8947d5bba614ff36c4a96c4460ce3392a018fc5f87e952c4"  # pragma: allowlist secret
)
_P8D_BRIEF = (
    "ed08f263239a8d1e628bd5af1f7efa8fe3329df2901fb5ea03dbc6dae6352cb6"  # pragma: allowlist secret
)
_P8D_CONTRACT = (
    "9b5ec931250fd66f9660c9916153f4594ae021845c6dd9f643264f7df8e8d3e3"  # pragma: allowlist secret
)
_P8D_ORACLE_A = (
    "b08e2920077a2f36ba634b32c0f1215e952063c55cfc99320ab55fbbdf9d36f5"  # pragma: allowlist secret
)
_P8D_ORACLE_B = (
    "810e8528fcea94a8ee848b56cb50ae04ff35bbaef05de8f667bddda896cac9d8"  # pragma: allowlist secret
)
_PUBLIC_DIGESTS.update(
    {
        "docs/evidence/P8D_GATE_A/baseline.json": {
            _P8D_BASE,
            _P8D_TREE,
            _P8D_PARENT1,
            _P8D_PARENT2,
            _P8D_OLDHEAD,
            _P8D_OLDTREE,
            _P8D_AUDIT,
            _P8D_BRIEF,
            _P8D_CONTRACT,
        },
        "docs/evidence/P8D_GATE_B/design_probe.py": {
            _P8D_BASE,
            _P8D_TREE,
            _P8D_AUDIT,
            _P8D_BRIEF,
            _P8D_CONTRACT,
            _P8D_ORACLE_A,
            _P8D_ORACLE_B,
        },
        "docs/evidence/P8D_REVIEWER/INITIAL_PROBE_RESULT.json": {
            _P8D_DESIGNHEAD,
            _P8D_DESIGNTREE,
        },
        "docs/evidence/P8D_REVIEWER/MANIFEST_CORRECTIVE_PROBE_RESULT.json": {
            _P8D_DESIGNHEAD,
            _P8D_DESIGNTREE,
        },
        "docs/evidence/P8D_REVIEWER/MANIFEST_GAP_PROBE_RESULT.json": {
            _P8D_DESIGNHEAD,
            _P8D_DESIGNTREE,
        },
        "scripts/p8d_qa_probe.py": {
            _P8D_ORACLE_A,
            _P8D_ORACLE_B,
        },
        "scripts/p8d_reviewer_probe.py": {
            _P8D_ORACLE_A,
            _P8D_ORACLE_B,
        },
        "tests/test_watchlist_delivery_policy.py": {
            _P8D_ORACLE_A,
            _P8D_ORACLE_B,
        },
    }
)


def _reviewed_public_candidate(path: str, candidate: dict[str, object]) -> bool:
    """No pattern exclusion: detector/path/value must all match a reviewed public ID."""
    values = _PUBLIC_DIGESTS.get(path.replace("\\", "/"), frozenset())
    return candidate.get("type") == "Hex High Entropy String" and candidate.get(
        "hashed_secret"
    ) in {sha1(value.encode("utf-8")).hexdigest() for value in values}


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
    reviewed = 0
    failed = False
    for path, candidates in sorted(findings.items()):
        for candidate in candidates:
            if _reviewed_public_candidate(path, candidate):
                reviewed += 1
                continue
            failed = True
            print(
                f"{path}:{candidate.get('line_number', '?')}: "
                f"{candidate.get('type', 'unknown')} candidate"
            )
    if failed:
        print("Secret scan: FAIL; review each candidate")
        return 1
    print(f"Secret scan: PASS (no unreviewed candidates; {reviewed} exact public digest matches)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
