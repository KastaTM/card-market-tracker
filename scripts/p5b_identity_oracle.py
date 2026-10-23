"""Independent stdlib P5b identity oracle for frozen synthetic P5a fixtures.

Not production code and not a substitute for independent QA/repo CI.
Usage: python scripts/p5b_identity_oracle.py [--write-fixture]
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

TARGET = "541b9d13-9669-4973-8413-397bea14c045"
CARD = "70bf03c9-a465-4299-a4fc-adfb70de757d"
SET = "f9743b79-20e3-4815-98d3-bb06f0c8195f"
EXPECTED = {
    "sequence": "wjs1_380dce2c23fa07657ddf95adac1c9f96c36c8449235e3462140dd88b684e676f",
    "baseline": "wje1_411e24c6f8f6cf4089d335f5c1886b4f71b34cae34f69a9e54251007863aa284",
    "second": "wje1_017178f97a80245df9bb2e997afef80e17894af07380621530c290ccc30f5b33",
    "signal_price": "wsig1_d9f9c7f0d4ca8767a6cdb9a917cc27a61c369cecea629c790ed42fd4421bf4f0",
    "signal_restock": "wsig1_4bd7f7a2ca57d7e8c9e340dc5f3c27aa5f3dbe433c7ef01a0ac897675e4e8bd4",
}


def canonical(value: object) -> str:
    return json.dumps(
        value, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(",", ":")
    )


def full_preimage(domain: str, value: dict[str, object]) -> bytes:
    return domain.encode("ascii") + b"\x00" + canonical(value).encode("utf-8")


def freeze(name: str, prefix: str, domain: str, value: dict[str, object]) -> dict[str, object]:
    preimage = full_preimage(domain, value)
    result = prefix + hashlib.sha256(preimage).hexdigest()
    assert result == EXPECTED[name], (name, result, EXPECTED[name])
    return {
        "id": result,
        "domain": domain,
        "preimage_text": preimage.decode("utf-8"),
        "object": value,
    }


def vectors() -> dict[str, dict[str, object]]:
    wlt = "wlt1_" + hashlib.sha256(("CMT_WATCHLIST_V1\x00" + TARGET).encode("utf-8")).hexdigest()
    projection = {
        "version": 1,
        "target": {
            "cmt_id": TARGET,
            "kind": "printing",
            "card_id": CARD,
            "language": "es",
            "variant": "normal",
        },
        "parents": [
            {"cmt_id": CARD, "kind": "card", "set_id": SET, "card_number": "001"},
            {"cmt_id": SET, "kind": "set"},
        ],
    }
    entry = {
        "version": 1,
        "cmt_id": TARGET,
        "watch_id": wlt,
        "canonical_identity": projection,
        "identity_digest": hashlib.sha256(canonical(projection).encode("utf-8")).hexdigest(),
        "revision": 1,
        "priority": "high",
        "enabled": True,
        "target_price_minor": 1000,
        "restock_enabled": True,
        "max_age_seconds": 86400,
    }
    common = {
        "version": 1,
        "provenance": "synthetic",
        "cmt_id": TARGET,
        "series_key": "synthetic-series",
        "currency": "EUR",
    }
    prev = {
        **common,
        "sample_id": "synthetic-previous",
        "observed_at": "2026-10-23T11:00:00Z",
        "unit_price_minor": None,
        "shipping_minor": None,
        "stock": "OUT_OF_STOCK",
    }
    current = {
        **common,
        "sample_id": "synthetic-current",
        "observed_at": "2026-10-23T12:00:00Z",
        "unit_price_minor": 900,
        "shipping_minor": 100,
        "stock": "AVAILABLE",
    }
    s = {
        "watch_id": wlt,
        "revision": 1,
        "policy_version": "watchlist-rules-v1",
        "series_key": "synthetic-series",
    }
    vec = {"sequence": freeze("sequence", "wjs1_", "CMT_WATCHLIST_JOURNAL_SEQUENCE_V1", s)}
    seq = str(vec["sequence"]["id"])

    def evaluation(a: dict[str, object], b: dict[str, object] | None, at: str) -> dict[str, object]:
        return {
            "version": 1,
            "sequence_id": seq,
            "policy_version": "watchlist-rules-v1",
            "entry": entry,
            "current": a,
            "previous": b,
            "as_of": at,
        }

    vec["baseline"] = freeze(
        "baseline",
        "wje1_",
        "CMT_WATCHLIST_JOURNAL_EVALUATION_V1",
        evaluation(prev, None, "2026-10-23T11:00:00Z"),
    )
    vec["second"] = freeze(
        "second",
        "wje1_",
        "CMT_WATCHLIST_JOURNAL_EVALUATION_V1",
        evaluation(current, prev, "2026-10-23T12:00:00Z"),
    )
    for rule in ("price", "restock"):
        item = {
            "version": 1,
            "kind": "WATCHLIST_RULE_ENTERED_MATCH",
            "mode": "synthetic",
            "sequence_id": seq,
            "rule": rule,
            "from_evaluation_id": vec["baseline"]["id"],
            "to_evaluation_id": vec["second"]["id"],
        }
        name = "signal_" + rule
        vec[name] = freeze(name, "wsig1_", "CMT_WATCHLIST_SIGNAL_V1", item)
    return vec


def main() -> None:
    result = vectors()
    if "--write-fixture" in sys.argv:
        path = (
            Path(__file__).resolve().parent.parent
            / "tests"
            / "fixtures"
            / "p5b_identity_vectors_v1.json"
        )
        path.write_text(
            json.dumps(
                {"version": 1, "vectors": result}, indent=2, ensure_ascii=True, sort_keys=True
            )
            + "\n",
            encoding="utf-8",
        )
        print("WROTE " + str(path))
    for name, data in result.items():
        print(name + " " + str(data["id"]))
    print("PASS: all 5 golden digests / literal preimages")


if __name__ == "__main__":
    main()
