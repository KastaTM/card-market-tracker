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
_PUBLIC_DIGESTS = {
    "docs/sources/P1B_REQUEST_LEDGER.json": _ORIGINALS,
    "src/card_market_tracker/pinned_repository/approved_bundle_v1.json": _PACKAGE,
    "tests/fixtures/pinned_repository_bundle_v1.json": _PACKAGE,
    "src/card_market_tracker/pinned_repository/bundle.py": {_REVISION, _BUNDLE},
    "tests/test_pinned_repository.py": {_MIT},
}


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
