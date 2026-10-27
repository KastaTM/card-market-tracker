"""Author tests for the additive one-snapshot original P5b source reader."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from card_market_tracker.watchlist import application as watchlist_app
from card_market_tracker.watchlist import storage as watchlist_storage
from card_market_tracker.watchlist_journal import application as journal_app
from card_market_tracker.watchlist_journal import storage as journal_storage
from card_market_tracker.watchlist_journal.errors import JournalError

TARGET = "541b9d13-9669-4973-8413-397bea14c045"


def sources(tmp_path: Path) -> tuple[Path, Path, dict[str, Any], str, list[dict[str, Any]]]:
    manifest = json.loads((Path(__file__).parent / "fixtures/synthetic_manifest.json").read_text())
    watchlist, journal = tmp_path / "watchlist.sqlite", tmp_path / "journal.sqlite"
    watchlist_storage.initialize(watchlist)
    entry = watchlist_app.add(
        watchlist,
        manifest,
        TARGET,
        {"target_price_minor": 1000, "restock_enabled": True},
        request_token="first",
    )["entry"]
    journal_storage.initialize(journal)
    points = []
    previous = None
    for ordinal, stock in enumerate(("OUT_OF_STOCK", "AVAILABLE"), 1):
        current = {
            "version": 1,
            "provenance": "synthetic",
            "sample_id": f"s{ordinal}",
            "cmt_id": TARGET,
            "series_key": "synthetic-series",
            "observed_at": f"2026-10-23T12:0{ordinal}:00Z",
            "currency": "EUR",
            "unit_price_minor": 900,
            "shipping_minor": 100,
            "stock": stock,
        }
        points.append(
            journal_app.record(
                journal,
                watchlist,
                manifest,
                entry["watch_id"],
                current,
                previous,
                revision=1,
                as_of=current["observed_at"],
            )
        )
        previous = current
    return watchlist, journal, manifest, entry["watch_id"], points


def test_source_bundle_uses_one_deep_fold_and_keeps_originals_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    watchlist, journal, _, _, points = sources(tmp_path)
    before = watchlist.read_bytes(), journal.read_bytes()
    verify = journal_storage._verify
    folds = []

    def counted(db, budget):
        assert db.execute("PRAGMA query_only").fetchone()[0] == 1
        assert db.in_transaction
        folds.append(db)
        return verify(db, budget)

    monkeypatch.setattr(journal_storage, "_verify", counted)
    bundle = journal_storage._verified_signal_bundle(
        journal, points[-1]["signal_ids"][0], _budget=journal_storage.Budget()
    )
    assert len(folds) == 1
    assert set(bundle) == {"version", "signal", "predecessor", "current"}
    assert set(bundle["current"]) == {
        "evaluation_id",
        "sequence_id",
        "ordinal",
        "predecessor_evaluation_id",
        "snapshot",
        "evaluation_result",
    }
    assert bundle["current"]["predecessor_evaluation_id"] == bundle["predecessor"]["evaluation_id"]
    assert (watchlist.read_bytes(), journal.read_bytes()) == before


def test_missing_source_signal_is_not_found_after_full_fold(tmp_path: Path) -> None:
    _, journal, _, _, _ = sources(tmp_path)
    with pytest.raises(JournalError, match="not_found"):
        journal_storage._verified_signal_bundle(
            journal, "wsig1_" + "0" * 64, _budget=journal_storage.Budget()
        )
