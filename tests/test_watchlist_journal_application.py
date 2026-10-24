"""Author original-origin admission, recomputation and nonmutation integration tests."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import socket
from pathlib import Path
from typing import Any

import pytest

from card_market_tracker.catalog.manifest import parse_manifest
from card_market_tracker.watchlist import application as watchlist_app
from card_market_tracker.watchlist import storage as watchlist_storage
from card_market_tracker.watchlist_journal import application as app
from card_market_tracker.watchlist_journal import storage
from card_market_tracker.watchlist_journal.errors import JournalError

TARGET = "541b9d13-9669-4973-8413-397bea14c045"
NOW = "2026-10-23T12:00:00Z"


@pytest.fixture
def manifest() -> dict[str, Any]:
    return json.loads((Path(__file__).parent / "fixtures/synthetic_manifest.json").read_text())


@pytest.fixture
def stores(tmp_path: Path, manifest: dict[str, Any]) -> tuple[Path, Path, str]:
    origin, journal = tmp_path / "watchlist.sqlite", tmp_path / "journal.sqlite"
    watchlist_storage.initialize(origin)
    result = watchlist_app.add(
        origin,
        manifest,
        TARGET,
        {"target_price_minor": 1000, "restock_enabled": True},
        request_token="add",
    )
    storage.initialize(journal)
    return origin, journal, result["entry"]["watch_id"]


def sample(**changes: Any) -> dict[str, Any]:
    return {
        "version": 1,
        "provenance": "synthetic",
        "sample_id": "current",
        "cmt_id": TARGET,
        "series_key": "synthetic-series",
        "observed_at": NOW,
        "currency": "EUR",
        "unit_price_minor": 900,
        "shipping_minor": 100,
        "stock": "AVAILABLE",
        **changes,
    }


def record(
    stores: tuple[Path, Path, str],
    manifest: object,
    current: object = None,
    previous: object = None,
    **kwargs: Any,
) -> dict[str, Any]:
    origin, journal, key = stores
    return app.record(
        journal,
        origin,
        manifest,
        key,
        sample() if current is None else current,
        previous,
        revision=kwargs.pop("revision", 1),
        as_of=kwargs.pop("as_of", NOW),
        **kwargs,
    )


def test_record_recompute_original_revision_without_mutation_or_network(
    stores: tuple[Path, Path, str],
    manifest: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    origin, journal, key = stores
    watchlist_app.update(
        origin,
        manifest,
        key,
        {"target_price_minor": 500},
        expected_revision=1,
        request_token="update",
    )
    before = hashlib.sha256(origin.read_bytes()).hexdigest()
    original_manifest = copy.deepcopy(manifest)

    def blocked(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket, "socket", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    saved = record(stores, manifest)
    assert saved["result"] == "recorded" and saved["signals_count"] == 0
    row = storage.get(journal, saved["evaluation_id"])["evaluation"]
    assert row["snapshot"]["entry"]["revision"] == 1
    assert row["evaluation_result"]["result"] == "MATCH"
    journal_bytes = journal.read_bytes()
    recomputed = app.recompute(journal, origin, manifest, saved["evaluation_id"])
    assert recomputed["evaluation_result"] == row["evaluation_result"]
    assert journal.read_bytes() == journal_bytes
    assert hashlib.sha256(origin.read_bytes()).hexdigest() == before
    assert manifest == original_manifest
    assert "names" not in json.dumps(row) and "bindings" not in json.dumps(row)


@pytest.mark.parametrize(
    "invalid", ["extra", "parsed", "unrelated", "binding", "identity", "target"]
)
def test_full_manifest_origin_is_revalidated_even_for_ancient_replay(
    stores: tuple[Path, Path, str],
    manifest: dict[str, Any],
    invalid: str,
) -> None:
    origin, journal, _ = stores
    saved = record(stores, manifest)
    bad: Any = copy.deepcopy(manifest)
    if invalid == "extra":
        bad["extra"] = True
    elif invalid == "parsed":
        bad = parse_manifest(bad)
    elif invalid == "unrelated":
        bad["entities"][1]["extra"] = True
    elif invalid == "binding":
        bad["bindings"][0]["cmt_id"] = "ffffffff-ffff-4fff-8fff-ffffffffffff"
    elif invalid == "identity":
        next(row for row in bad["entities"] if row["cmt_id"] == TARGET)["variant"] = "holo"
    else:
        bad["entities"] = [row for row in bad["entities"] if row["cmt_id"] != TARGET]
        bad["bindings"] = []
    before = origin.read_bytes(), journal.read_bytes()
    with pytest.raises(JournalError):
        record(stores, bad)
    with pytest.raises(JournalError):
        app.recompute(journal, origin, bad, saved["evaluation_id"])
    assert before == (origin.read_bytes(), journal.read_bytes())


def test_non_identity_manifest_names_and_bindings_do_not_change_replay(
    stores: tuple[Path, Path, str],
    manifest: dict[str, Any],
) -> None:
    first = record(stores, manifest)
    manifest["entities"][0]["names"] = {"en": "Changed synthetic title"}
    manifest["bindings"] = []
    replay = record(stores, manifest)
    assert replay["result"] == "replayed"
    for key in ("evaluation_id", "persisted_at", "signal_ids"):
        assert replay[key] == first[key]


@pytest.mark.parametrize("revision", [None, True, 0, "1", 2147483648, 999])
def test_exact_existing_revision_required(
    stores: tuple[Path, Path, str],
    manifest: dict[str, Any],
    revision: Any,
) -> None:
    before = stores[1].read_bytes()
    with pytest.raises(JournalError):
        record(stores, manifest, revision=revision)
    assert stores[1].read_bytes() == before


@pytest.mark.parametrize(
    "changes",
    [
        {"provenance": "real"},
        {"result": "MATCH"},
        {"verified": True},
        {"unit_price_minor": True},
        {"currency": "USD"},
        {"series_key": []},
        {"observed_at": "2026-10-24T12:00:00Z"},
    ],
)
def test_disabled_revision_still_rejects_invalid_evidence(
    stores: tuple[Path, Path, str],
    manifest: dict[str, Any],
    changes: dict[str, Any],
) -> None:
    origin, journal, key = stores
    watchlist_app.update(
        origin, manifest, key, None, expected_revision=1, request_token="disabled", action="disable"
    )
    before = journal.read_bytes()
    with pytest.raises(JournalError):
        record(stores, manifest, sample(**changes), revision=2)
    assert journal.read_bytes() == before


def test_previous_revalidated_even_disabled_and_no_implicit_initialization(
    stores: tuple[Path, Path, str],
    manifest: dict[str, Any],
    tmp_path: Path,
) -> None:
    origin, journal, key = stores
    watchlist_app.update(
        origin, manifest, key, None, expected_revision=1, request_token="disabled", action="disable"
    )
    for prior in [
        sample(),
        sample(sample_id="old", series_key="other"),
        sample(sample_id="old", observed_at="2026-10-23T13:00:00Z"),
    ]:
        with pytest.raises(JournalError):
            record(stores, manifest, previous=prior, revision=2)
    missing = tmp_path / "missing.sqlite"
    with pytest.raises(JournalError, match="storage_missing"):
        app.record(missing, origin, manifest, key, sample(), revision=2, as_of=NOW)
    assert not missing.exists()
    assert storage.verify(journal)["counts"]["evaluations"] == 0


def test_distinct_origin_paths_and_hardlink_alias_rejected(
    stores: tuple[Path, Path, str],
    manifest: dict[str, Any],
    tmp_path: Path,
) -> None:
    origin, _, key = stores
    before = origin.read_bytes()
    for path in (origin, origin.parent / "." / origin.name):
        with pytest.raises(JournalError, match="unsafe_destination"):
            app.record(path, origin, manifest, key, sample(), revision=1, as_of=NOW)
    alias = tmp_path / "alias.sqlite"
    os.link(origin, alias)
    with pytest.raises(JournalError, match="unsafe_destination"):
        app.record(alias, origin, manifest, key, sample(), revision=1, as_of=NOW)
    assert origin.read_bytes() == before


def test_local_verify_independent_of_origin_and_recompute_demands_exact_config(
    stores: tuple[Path, Path, str],
    manifest: dict[str, Any],
    tmp_path: Path,
) -> None:
    origin, journal, _ = stores
    saved = record(stores, manifest)
    before = journal.read_bytes()
    with pytest.raises(JournalError, match="storage_missing"):
        app.recompute(journal, tmp_path / "absent.sqlite", manifest, saved["evaluation_id"])
    alternate = tmp_path / "alternate.sqlite"
    watchlist_storage.initialize(alternate)
    watchlist_app.add(
        alternate, manifest, TARGET, {"target_price_minor": 2000}, request_token="add"
    )
    with pytest.raises(JournalError, match="identity_conflict"):
        app.recompute(journal, alternate, manifest, saved["evaluation_id"])
    assert storage.verify(journal)["result"] == "ok"
    assert journal.read_bytes() == before
    assert origin.exists()


def test_same_nominal_revision_cannot_fork_config_across_series(
    stores: tuple[Path, Path, str],
    manifest: dict[str, Any],
    tmp_path: Path,
) -> None:
    record(stores, manifest)
    alternate = tmp_path / "alternate.sqlite"
    watchlist_storage.initialize(alternate)
    watchlist_app.add(
        alternate, manifest, TARGET, {"target_price_minor": 2000}, request_token="add"
    )
    before = stores[1].read_bytes()
    with pytest.raises(JournalError, match="identity_conflict"):
        app.record(
            stores[1],
            alternate,
            manifest,
            stores[2],
            sample(series_key="another"),
            revision=1,
            as_of=NOW,
        )
    assert stores[1].read_bytes() == before


def test_revision_and_series_open_independent_signal_free_sequences(
    stores: tuple[Path, Path, str],
    manifest: dict[str, Any],
) -> None:
    first = record(stores, manifest)
    another = record(stores, manifest, sample(series_key="another"))
    watchlist_app.update(
        stores[0],
        manifest,
        stores[2],
        {"target_price_minor": 1000},
        expected_revision=1,
        request_token="new-revision",
    )
    revision = record(stores, manifest, revision=2)
    assert len({row["sequence_id"] for row in [first, another, revision]}) == 3
    assert all(row["signals_count"] == 0 for row in [first, another, revision])


@pytest.mark.parametrize("timeout", [0, -1, 6, True, float("nan"), float("inf")])
def test_public_application_budget_validation(
    stores: tuple[Path, Path, str],
    manifest: dict[str, Any],
    timeout: float,
) -> None:
    with pytest.raises(JournalError, match="invalid_field"):
        record(stores, manifest, timeout=timeout)
    with pytest.raises(JournalError, match="invalid_field"):
        app.recompute(stores[1], stores[0], manifest, "wje1_" + "0" * 64, timeout=timeout)


def test_total_deadline_includes_full_manifest_admission(
    stores: tuple[Path, Path, str],
    manifest: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = [0.0]
    monkeypatch.setattr(storage.time, "monotonic", lambda: clock[0])
    original = app.identity_projection

    def delayed(manifest: object, cmt_id: object) -> dict[str, object]:
        result = original(manifest, cmt_id)
        clock[0] += 2.1
        return result

    monkeypatch.setattr(app, "identity_projection", delayed)
    before = stores[1].read_bytes()
    with pytest.raises(JournalError, match="storage_timeout"):
        record(stores, manifest)
    assert stores[1].read_bytes() == before


def test_malformed_public_path_has_safe_error(
    stores: tuple[Path, Path, str],
    manifest: dict[str, Any],
) -> None:
    with pytest.raises(JournalError, match="unsafe_destination"):
        app.record(
            Path("invalid\x00.sqlite"),
            stores[0],
            manifest,
            stores[2],
            sample(),
            revision=1,
            as_of=NOW,
        )
