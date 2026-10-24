"""Standalone, independently coded QA-style golden oracle; no production imports.

Run: python -m unittest discover -s tests -p 'test_p5b_identity_vectors_reference.py'
This validates *contract vectors*, not the P5b implementation or independence
of final-commit authors/reviewers.
"""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

FIXTURE = Path(__file__).parent / "fixtures" / "p5b_identity_vectors_v1.json"


class IdentityVectorContract(unittest.TestCase):
    def test_sha256_preimages_and_normalization(self) -> None:
        vectors = json.loads(FIXTURE.read_text(encoding="utf-8"))["vectors"]
        expected_prefix = {
            "sequence": "wjs1_",
            "baseline": "wje1_",
            "second": "wje1_",
            "signal_price": "wsig1_",
            "signal_restock": "wsig1_",
        }
        self.assertEqual(set(vectors), set(expected_prefix))
        for name, data in vectors.items():
            with self.subTest(name=name):
                obj = data["object"]
                # Independently encode the exact canonical JSON (no productive helper).
                text = json.dumps(
                    obj, separators=(",", ":"), sort_keys=True, ensure_ascii=True, allow_nan=False
                )
                raw = data["domain"].encode("ascii") + bytes([0]) + text.encode("utf-8")
                self.assertEqual(raw.decode("utf-8"), data["preimage_text"])
                self.assertEqual(
                    expected_prefix[name] + hashlib.sha256(raw).hexdigest(), data["id"]
                )
                self.assertEqual(raw.count(bytes([0])), 1)

    def test_mutation_changes_semantic_identity(self) -> None:
        vectors = json.loads(FIXTURE.read_text(encoding="utf-8"))["vectors"]
        baseline = vectors["second"]
        mutated = json.loads(json.dumps(baseline["object"]))
        mutated["as_of"] = "2026-10-23T12:00:01Z"
        content = json.dumps(mutated, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        changed_id = (
            "wje1_"
            + hashlib.sha256(baseline["domain"].encode() + b"\x00" + content.encode()).hexdigest()
        )
        self.assertNotEqual(changed_id, baseline["id"])


if __name__ == "__main__":
    unittest.main()
