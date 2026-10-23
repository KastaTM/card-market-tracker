"""Author integration tests using the actual independent SQLite store."""

from __future__ import annotations

import copy
import hashlib
import json
import socket
from pathlib import Path
from typing import Any

import pytest

from card_market_tracker.alerts import storage as outbox_storage
from card_market_tracker.catalog.manifest import parse_manifest
from card_market_tracker.discovery import journal_storage
from card_market_tracker.persistence import sqlite_repository as captures_storage
from card_market_tracker.telegram_delivery import storage as delivery_storage
from card_market_tracker.watchlist import application as app
from card_market_tracker.watchlist import storage
from card_market_tracker.watchlist.errors import WatchlistError

TARGET = "541b9d13-9669-4973-8413-397bea14c045"
NOW = "2026-01-02T12:00:00Z"


@pytest.fixture
def manifest() -> dict[str, Any]:
    return json.loads((Path(__file__).parent / "fixtures/synthetic_manifest.json").read_text())


@pytest.fixture
def path(tmp_path: Path) -> Path:
    database = tmp_path / "watchlist.sqlite"
    storage.initialize(database)
    return database


def add(path: Path, manifest: object, **changes: Any) -> dict[str, Any]:
    return app.add(
        path, manifest, TARGET, {"target_price_minor": 1000, **changes}, request_token="add-1"
    )


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


def test_add_update_old_replay_does_not_revert_current(
    path: Path, manifest: dict[str, Any]
) -> None:
    original = add(path, manifest)
    key = original["entry"]["watch_id"]
    result = app.update(
        path,
        manifest,
        key,
        {"target_price_minor": 2000},
        expected_revision=1,
        request_token="update-1",
    )
    assert result["entry"]["revision"] == 2
    replay = add(path, manifest)
    assert replay["replayed"] is True and replay["entry"] == original["entry"]
    assert storage.get(path, key)["entry"]["revision"] == 2
    replay = app.update(
        path,
        manifest,
        key,
        {"target_price_minor": 2000},
        expected_revision=1,
        request_token="update-1",
    )
    assert replay["replayed"] is True and replay["entry"] == result["entry"]
    for token, expected, config, category in [
        ("update-1", 1, 3000, "replay_conflict"),
        ("new", 1, 3000, "revision_conflict"),
        ("new", 99, 3000, "revision_conflict"),
    ]:
        with pytest.raises(WatchlistError, match=category):
            app.update(
                path,
                manifest,
                key,
                {"target_price_minor": config},
                expected_revision=expected,
                request_token=token,
            )
    assert storage.verify(path)["result"] == "ok"


def test_enable_disable_replay_uses_original_precondition_config(
    path: Path, manifest: dict[str, Any]
) -> None:
    first = add(path, manifest)
    key = first["entry"]["watch_id"]
    disabled = app.update(
        path, manifest, key, None, expected_revision=1, request_token="disable-1", action="disable"
    )
    app.update(
        path,
        manifest,
        key,
        {"target_price_minor": 3000, "priority": "high"},
        expected_revision=2,
        request_token="update-2",
    )
    replay = app.update(
        path, manifest, key, None, expected_revision=1, request_token="disable-1", action="disable"
    )
    assert replay["replayed"] is True and replay["entry"] == disabled["entry"]
    assert replay["entry"]["target_price_minor"] == 1000
    current = storage.get(path, key)["entry"]
    assert current["revision"] == 3 and current["target_price_minor"] == 3000
    enabled = app.update(
        path, manifest, key, None, expected_revision=3, request_token="enable-1", action="enable"
    )
    assert enabled["entry"]["enabled"] is True and enabled["entry"]["priority"] == "high"


def test_evaluate_frozen_revision_no_persistence_or_network(
    path: Path, manifest: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    key = add(path, manifest)["entry"]["watch_id"]
    app.update(
        path,
        manifest,
        key,
        {"target_price_minor": 500},
        expected_revision=1,
        request_token="update",
    )
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    snapshot = copy.deepcopy(manifest)

    def blocked(*args: object, **kwargs: object) -> Any:
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket, "socket", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    result = app.evaluate(path, manifest, key, sample(), revision=1, as_of=NOW)
    assert result["revision"] == 1 and result["result"] == "MATCH"
    assert (
        app.evaluate(path, manifest, key, sample(), revision=2, as_of=NOW)["result"] == "NO_MATCH"
    )
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    assert manifest == snapshot
    assert storage.verify(path)["counts"]["revisions"] == 2


def test_names_and_unrelated_changes_allowed_identity_change_rejected(
    path: Path, manifest: dict[str, Any]
) -> None:
    key = add(path, manifest)["entry"]["watch_id"]
    manifest["bindings"] = []
    manifest["entities"][0]["names"]["en"] = "A new localization"
    assert app.evaluate(path, manifest, key, sample(), revision=1, as_of=NOW)["result"] == "MATCH"
    next(row for row in manifest["entities"] if row["cmt_id"] == TARGET)["variant"] = "unknown"
    before = path.read_bytes()
    with pytest.raises(WatchlistError, match="identity_conflict"):
        app.update(
            path,
            manifest,
            key,
            {"target_price_minor": 2000},
            expected_revision=1,
            request_token="changed",
        )
    with pytest.raises(WatchlistError, match="identity_conflict"):
        app.evaluate(path, manifest, key, sample(), revision=1, as_of=NOW)
    assert path.read_bytes() == before


def test_full_manifest_revalidation_all_application_boundaries(
    path: Path, manifest: dict[str, Any]
) -> None:
    key = add(path, manifest)["entry"]["watch_id"]
    for invalid in [parse_manifest(manifest), {**manifest, "extra": 1}]:
        with pytest.raises(WatchlistError):
            app.add(path, invalid, TARGET, {"target_price_minor": 1}, request_token="bad")
        with pytest.raises(WatchlistError):
            app.update(
                path,
                invalid,
                key,
                {"target_price_minor": 1},
                expected_revision=1,
                request_token="bad",
            )
        with pytest.raises(WatchlistError):
            app.evaluate(path, invalid, key, sample(), revision=1, as_of=NOW)


@pytest.mark.parametrize("timeout", [0, -1, 6, True, float("nan"), float("inf")])
def test_application_budget_validation(
    path: Path, manifest: dict[str, Any], timeout: float
) -> None:
    with pytest.raises(WatchlistError, match="invalid_field"):
        app.add(
            path,
            manifest,
            TARGET,
            {"target_price_minor": 1000},
            request_token="add",
            timeout=timeout,
        )


def test_no_implicit_initialization_and_strict_update(
    path: Path, manifest: dict[str, Any], tmp_path: Path
) -> None:
    missing = tmp_path / "absent.sqlite"
    with pytest.raises(WatchlistError, match="storage_missing"):
        app.add(missing, manifest, TARGET, {"target_price_minor": 1000}, request_token="add")
    assert not missing.exists()
    key = add(path, manifest)["entry"]["watch_id"]
    for action, config in [("delete", None), ("enable", {}), ("update", {})]:
        with pytest.raises(WatchlistError):
            app.update(
                path, manifest, key, config, expected_revision=1, request_token="bad", action=action
            )
    with pytest.raises(WatchlistError, match="invalid_field"):
        app.update(
            path,
            manifest,
            key,
            {"target_price_minor": 1},
            expected_revision=True,
            request_token="bad",
        )


def test_single_application_deadline_counts_validation(
    path: Path, manifest: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    clock = [0.0]
    monkeypatch.setattr(storage.time, "monotonic", lambda: clock[0])
    real = app.identity_projection

    def delayed(manifest: object, cmt_id: object) -> dict[str, object]:
        result = real(manifest, cmt_id)
        clock[0] += 2.1
        return result

    monkeypatch.setattr(app, "identity_projection", delayed)
    with pytest.raises(WatchlistError, match="storage_timeout"):
        add(path, manifest)
    assert storage.list_entries(path)["entries"] == []


def test_evaluation_leaves_all_accepted_databases_unchanged(
    path: Path, manifest: dict[str, Any], tmp_path: Path
) -> None:
    key = add(path, manifest)["entry"]["watch_id"]
    databases = [path]
    for name, initialize in [
        ("captures", captures_storage.initialize),
        ("journal", journal_storage.initialize),
        ("outbox", outbox_storage.initialize),
        ("delivery", delivery_storage.initialize),
    ]:
        prior_path = tmp_path / (name + ".sqlite")
        initialize(prior_path)
        databases.append(prior_path)
    before = {item: hashlib.sha256(item.read_bytes()).digest() for item in databases}
    assert app.evaluate(path, manifest, key, sample(), revision=1, as_of=NOW)["result"] == "MATCH"
    with pytest.raises(WatchlistError, match="unsupported_evidence"):
        app.evaluate(path, manifest, key, sample(provenance="real"), revision=1, as_of=NOW)
    assert {item: hashlib.sha256(item.read_bytes()).digest() for item in databases} == before
