"""Independent stdlib P8c identity vector oracle; read-only unless explicitly regenerating."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SIGNALS = {
    "price": "wsig1_d9f9c7f0d4ca8767a6cdb9a917cc27a61c369cecea629c790ed42fd4421bf4f0",
    "restock": "wsig1_4bd7f7a2ca57d7e8c9e340dc5f3c27aa5f3dbe433c7ef01a0ac897675e4e8bd4",
}


def reference() -> dict[str, object]:
    vectors = []
    for alias, signal in (
        ("local-preview", SIGNALS["price"]),
        ("local-preview", SIGNALS["restock"]),
        ("qa-preview", SIGNALS["price"]),
    ):
        payload = {"identity_version": 1, "destination_key": alias, "signal_id": signal}
        canonical = json.dumps(
            payload, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
        )
        preimage = b"CMT_WATCHLIST_ALERT_V1\x00" + canonical.encode("ascii")
        vectors.append(
            {
                "destination_key": alias,
                "signal_id": signal,
                "canonical_json": canonical,
                "preimage_text": preimage.decode("ascii"),
                "preimage_hex": preimage.hex(),
                "alert_id": "walt1_" + hashlib.sha256(preimage).hexdigest(),
            }
        )
    return {
        "version": 1,
        "source_signal_vectors": "tests/fixtures/p5b_identity_vectors_v1.json (baseline 228d5c8d)",
        "vectors": vectors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write-fixture", action="store_true")
    args = parser.parse_args()
    path = Path(__file__).resolve().parents[1] / "tests/fixtures/p8c_identity_vectors_v1.json"
    expected = reference()
    if args.write_fixture:
        path.write_text(
            json.dumps(expected, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        print("P8c identity fixture regenerated explicitly.")
        return 0
    try:
        actual = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print("P8c identity fixture check failed.")
        return 1
    if actual != expected:
        print("P8c identity fixture check failed.")
        return 1
    print("P8c identity fixture: three independent vectors match.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
