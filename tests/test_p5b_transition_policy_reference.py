"""Contract-level per-rule fold examples, not implementation/integration tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from p5b_transition_oracle import rules_entering_match


class TransitionOracleContract(unittest.TestCase):
    def transition(
        self,
        old: dict[str, str] | None,
        new: dict[str, str],
        prev_observed: str | None = "2026-10-23T11:00:00Z",
        now_observed: str = "2026-10-23T12:00:00Z",
        as_of: str = "2026-10-23T12:00:00Z",
        age: int = 86400,
    ) -> tuple[str, ...]:
        return rules_entering_match(
            predecessor=old,
            current=new,
            predecessor_observed_at=prev_observed,
            current_observed_at=now_observed,
            as_of=as_of,
            max_age_seconds=age,
        )

    def test_first_match_is_baseline(self) -> None:
        self.assertEqual((), self.transition(None, {"price": "MATCH", "restock": "MATCH"}, None))

    def test_two_rules_and_persistent_match(self) -> None:
        first = {"price": "NO_MATCH", "restock": "NO_MATCH"}
        match = {"price": "MATCH", "restock": "MATCH"}
        self.assertEqual(("price", "restock"), self.transition(first, match))
        self.assertEqual((), self.transition(match, match))

    def test_two_episodes_one_rule(self) -> None:
        states = ["NO_MATCH", "MATCH", "MATCH", "NO_MATCH", "MATCH"]
        signals = sum(
            len(self.transition({"price": a}, {"price": b}))
            for a, b in zip(states, states[1:], strict=False)
        )
        self.assertEqual(2, signals)

    def test_unknown_disabled_indeterminate_interrupt(self) -> None:
        for old in ("INDETERMINATE", "SKIPPED", "MATCH"):
            with self.subTest(old=old):
                self.assertEqual((), self.transition({"price": old}, {"price": "MATCH"}))
        self.assertEqual((), self.transition({"price": "NO_MATCH"}, {}))
        self.assertEqual((), self.transition({"price": "NO_MATCH"}, {"price": "INDETERMINATE"}))

    def test_freshness_age_inclusive(self) -> None:
        old, new = {"price": "NO_MATCH"}, {"price": "MATCH"}
        self.assertEqual(
            ("price",),
            self.transition(
                old,
                new,
                prev_observed="2026-10-23T11:00:00Z",
                now_observed="2026-10-23T12:00:00Z",
                age=3600,
            ),
        )
        self.assertEqual(
            (),
            self.transition(
                old,
                new,
                prev_observed="2026-10-23T11:00:00Z",
                now_observed="2026-10-23T12:00:00Z",
                age=3599,
            ),
        )
        self.assertEqual((), self.transition(old, new, age=3600, as_of="2026-10-23T12:00:01Z"))

    def test_no_or_aggregate_suppression(self) -> None:
        self.assertEqual(
            ("restock",),
            self.transition(
                {"price": "MATCH", "restock": "NO_MATCH"}, {"price": "MATCH", "restock": "MATCH"}
            ),
        )


if __name__ == "__main__":
    unittest.main()
