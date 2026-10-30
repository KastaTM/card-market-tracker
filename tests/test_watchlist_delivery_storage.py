"""P8d DB author tests: exact schema, guarded cells and genuine originals."""

from __future__ import annotations

import copy
import re
import sqlite3
from pathlib import Path
from typing import Any

import pytest
from test_watchlist_alert_rw01 import original

from card_market_tracker.watchlist_alerts import application as source_app
from card_market_tracker.watchlist_alerts import storage as source_storage
from card_market_tracker.watchlist_delivery import application as app
from card_market_tracker.watchlist_delivery import schema, storage
from card_market_tracker.watchlist_delivery.budget import Budget
from card_market_tracker.watchlist_delivery.errors import DeliveryError


def pipeline(
    directory: Path,
    *,
    ledger: Path | None = None,
    config: dict[str, Any] | None = None,
    series: str = "delivery-test",
) -> dict[str, Any]:
    source = original(directory, config=config, series=series)
    outbox = directory / "outbox.db"
    source_storage.initialize(outbox)
    alert = source_app.enqueue(
        outbox, source.watchlist, source.journal, source.manifest, source.signal, "private"
    )["alert_id"]
    if ledger is None:
        ledger = directory / "delivery.db"
        storage.initialize(ledger)
        storage.destination_add(ledger, "private", 1, 2, operator_private_owned=True)
    args = (ledger, source.watchlist, source.journal, outbox, source.manifest, alert, "private")
    reviewed = app.review(*args)["review"]
    consent = {
        "acknowledgement": reviewed["acknowledgement"],
        **{
            "expected_" + k: reviewed[k]
            for k in (
                "signal_id",
                "revision",
                "message_sha256",
                "evidence_sha256",
                "route_sha256",
                "binding_sha256",
            )
        },
    }
    return {"source": source, "outbox": outbox, "ledger": ledger, "args": args, "consent": consent}


def prepared(directory: Path, **options: Any) -> dict[str, Any]:
    context = pipeline(directory, **options)
    context["result"] = app.prepare(*context["args"], **context["consent"])
    context["did"] = context["result"]["delivery"]["delivery_id"]
    return context


def claim(context: dict[str, Any]) -> tuple[Budget, dict[str, Any]]:
    budget = Budget(5)
    storage._destination_validated(context["ledger"], "private", _budget=budget)
    ledger, watchlist, journal, outbox, manifest, alert, alias = context["args"]
    with budget.origins():
        content, frozen = app._admit(
            ledger, watchlist, journal, outbox, manifest, alert, alias, budget, operation="claim"
        )
    receipt = app._issue(content, budget, ledger, (watchlist, journal, outbox), frozen)
    return budget, storage._claim_verified(ledger, context["did"], receipt, budget)


def outcome(
    state: str = "confirmed", category: str | None = None, retry: int | None = None
) -> dict[str, Any]:
    return {
        "state": state,
        "error_category": category,
        "retry_after": retry,
        "receipt": {"message_id": 3, "accepted_at": 1, "bot_id": 1, "chat_id": 2}
        if state == "confirmed"
        else None,
    }


def test_literal_frozen_schema(tmp_path: Path) -> None:
    path = tmp_path / "ledger.db"
    storage.initialize(path)
    doc = (
        Path(__file__).parents[1] / "docs/data-contracts/WATCHLIST_TELEGRAM_DELIVERY_STORAGE_V1.md"
    ).read_text(encoding="utf-8")
    ddl = doc.split("<!-- P8D_DDL_BEGIN -->")[1].split("<!-- P8D_DDL_END -->")[0]
    assert schema.STATEMENTS == tuple(re.findall(r"^```sql\n(.*?)\n```$", ddl, re.M | re.S))
    expected = []
    for kind, name, table, authority in re.findall(
        r"^\| (table|index|trigger) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|$", doc, re.M
    ):
        expected.append(
            (
                kind,
                name.strip(),
                table.strip(),
                None
                if authority.strip() == "NULL"
                else schema.STATEMENTS[int(authority.split()[1]) - 1],
            )
        )
    with sqlite3.connect(path) as db:
        actual = tuple(
            db.execute("SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name")
        )
        assert actual == tuple(sorted(expected)) == schema.expected_inventory()
        assert len(actual) == 45 and len(schema.STATEMENTS) == 34
        assert all(
            row[-1] == 1 for row in db.execute("PRAGMA table_list") if row[1].startswith("wtd_")
        )
    assert storage.verify(path)["counts"] == dict.fromkeys(
        ("destinations", "watch_entries", "deliveries", "claims", "results"), 0
    )


def test_genuine_prepare_replay_receipt_and_source_nonmutation(tmp_path: Path) -> None:
    context = prepared(tmp_path / "one")
    ledger = context["ledger"]
    before = tuple(
        p.read_bytes()
        for p in (context["source"].watchlist, context["source"].journal, context["outbox"])
    )
    replay = app.prepare(*context["args"], **context["consent"])
    assert replay["result"] == "replay" and replay["delivery"] == context["result"]["delivery"]
    budget, claimed = claim(context)
    assert storage.get(ledger, context["did"])["delivery"]["state"] == "in_flight"
    done = storage._finish(ledger, context["did"], claimed["_handle"], outcome(), budget)
    assert done["state"] == "confirmed" and done["attempt_count"] == 1
    assert app.send(ledger, context["did"])["result"] == "replay"
    assert storage.verify(ledger)["counts"] == {
        "destinations": 1,
        "watch_entries": 1,
        "deliveries": 1,
        "claims": 1,
        "results": 1,
    }
    assert (
        tuple(
            p.read_bytes()
            for p in (context["source"].watchlist, context["source"].journal, context["outbox"])
        )
        == before
    )


def test_global_complete_entry_conflict_preserves_verify_and_backup(tmp_path: Path) -> None:
    first = prepared(tmp_path / "one")
    ledger = first["ledger"]
    before = ledger.read_bytes()
    second = pipeline(
        tmp_path / "two",
        ledger=ledger,
        config={"target_price_minor": 1100},
        series="distinct-series",
    )
    with pytest.raises(DeliveryError, match="identity_conflict"):
        app.prepare(*second["args"], **second["consent"])
    assert ledger.read_bytes() == before
    storage.verify(ledger)
    storage.backup(ledger, tmp_path / "healthy.db")


@pytest.mark.parametrize(
    "table,column,value",
    [
        ("wtd_deliveries", "message_text", "x" * 4097),
        ("wtd_destinations", "route_json", "x" * 2049),
        ("wtd_metadata", "operational_high_water", "2026-02-30T00:00:00.000000Z"),
    ],
)
def test_guarded_cells_after_constraints_restored(
    tmp_path: Path, table: str, column: str, value: str
) -> None:
    context = prepared(tmp_path / "one")
    path = context["ledger"]
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA ignore_check_constraints=ON")
        triggers = list(
            db.execute(
                "SELECT name,sql FROM sqlite_master WHERE type='trigger' AND tbl_name=?", (table,)
            )
        )
        for name, _ in triggers:
            db.execute("DROP TRIGGER " + name)
        db.execute("UPDATE " + table + " SET " + column + "=?", (value,))
        for _, sql in triggers:
            db.execute(sql)
    with pytest.raises(DeliveryError, match="storage_corrupt"):
        storage.verify(path)


def test_copied_fake_and_reused_claim_handles_fail(tmp_path: Path) -> None:
    context = prepared(tmp_path / "one")
    budget, claimed = claim(context)
    for fake in (object(), {}, copy.copy(claimed["_handle"])):
        with pytest.raises(DeliveryError, match="stale_attempt"):
            storage._finish(context["ledger"], context["did"], fake, outcome(), budget)
    storage._finish(context["ledger"], context["did"], claimed["_handle"], outcome(), budget)
    with pytest.raises(DeliveryError, match="stale_attempt"):
        storage._finish(context["ledger"], context["did"], claimed["_handle"], outcome(), budget)


def test_foreign_header_never_reaches_writable_sqlite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "foreign.db"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE foreign_data(value)")
    (tmp_path / "foreign.db-journal").write_bytes(b"foreign recovery evidence")

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("foreign writable open")

    monkeypatch.setattr(storage.sqlite3, "connect", forbidden)
    with pytest.raises(DeliveryError, match="storage_schema"):
        storage.destination_add(path, "private", 1, 2, operator_private_owned=True)
    assert (tmp_path / "foreign.db-journal").read_bytes() == b"foreign recovery evidence"


def test_pagination_filter_cursor_and_public_projection(tmp_path: Path) -> None:
    first = prepared(tmp_path / "one")
    second = prepared(tmp_path / "two", ledger=first["ledger"], series="another-episode")
    page = storage.list_deliveries(first["ledger"], limit=1)
    assert len(page["items"]) == 1 and page["next_cursor"]
    following = storage.list_deliveries(first["ledger"], limit=100, cursor=page["next_cursor"])
    assert len(following["items"]) == 1 and following["next_cursor"] is None
    assert {page["items"][0]["delivery_id"], following["items"][0]["delivery_id"]} == {
        first["did"],
        second["did"],
    }
    assert not (
        {"owner", "message_text", "bot_id", "chat_id", "entry_json", "evidence_json"}
        & set(page["items"][0])
    )
    for token in ("bad", "!!!!", "e30="):
        with pytest.raises(DeliveryError, match="invalid_cursor"):
            storage.list_deliveries(first["ledger"], cursor=token)
    with pytest.raises(DeliveryError, match="invalid_cursor"):
        storage.list_deliveries(first["ledger"], cursor=page["next_cursor"], state="ready")
    for limit in (True, 0, 1001):
        with pytest.raises(DeliveryError, match="invalid_field"):
            storage.list_deliveries(first["ledger"], limit=limit)
    assert storage.list_deliveries(first["ledger"], state="confirmed")["items"] == []


@pytest.mark.parametrize("category", sorted(storage._UNCERTAIN))
def test_uncertain_outcomes_are_terminal(tmp_path: Path, category: str) -> None:
    context = prepared(tmp_path / "one")
    budget, claimed = claim(context)
    final = storage._finish(
        context["ledger"],
        context["did"],
        claimed["_handle"],
        outcome("uncertain", category),
        budget,
    )
    assert final["state"] == "uncertain" and final["last_error_category"] == category
    with pytest.raises(DeliveryError, match="delivery_blocked"):
        claim(context)
    storage.verify(context["ledger"])


def test_strict_permanent_rejection_and_route_mutation_boundaries(tmp_path: Path) -> None:
    context = prepared(tmp_path / "one")
    path = context["ledger"]
    budget, claimed = claim(context)
    final = storage._finish(
        path,
        context["did"],
        claimed["_handle"],
        outcome("permanent_failure", "provider_rejection"),
        budget,
    )
    assert final["state"] == "permanent_failure"
    assert (
        storage.destination_add(path, "private", 1, 2, operator_private_owned=True)["result"]
        == "replay"
    )
    with pytest.raises(DeliveryError, match="conflict"):
        storage.destination_add(path, "private", 1, 3, operator_private_owned=True)
    with pytest.raises(DeliveryError, match="invalid_destination"):
        storage.destination_add(path, "another", 1, 2)
    with pytest.raises(DeliveryError, match="not_found"):
        storage.get(path, "wtdl1_" + "f" * 64)
    with pytest.raises(DeliveryError, match="conflict"):
        storage._destination_validated(path, "private", expected_route_sha256="f" * 64)


def test_clock_prevents_new_local_events_and_expired_budget(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import time

    context = prepared(tmp_path / "one")
    path = context["ledger"]
    before = path.read_bytes()
    monkeypatch.setattr(storage, "_now", lambda: "0001-01-01T00:00:00.000000Z")
    for operation in (
        lambda: storage._destination_validated(path, "private"),
        lambda: storage.destination_add(path, "other", 1, 2, operator_private_owned=True),
        lambda: app.prepare(*context["args"], **context["consent"]),
    ):
        with pytest.raises(DeliveryError, match="clock_skew"):
            operation()
    assert path.read_bytes() == before
    expired = Budget(1, started=time.monotonic() - 2)
    with pytest.raises(DeliveryError, match="storage_timeout"):
        storage.verify(path, _budget=expired)


def test_lock_timeout_rolls_back_without_claim(tmp_path: Path) -> None:
    context = prepared(tmp_path / "one")
    path = context["ledger"]
    with sqlite3.connect(path) as locked:
        locked.execute("BEGIN IMMEDIATE")
        with pytest.raises(DeliveryError, match="storage_locked|storage_timeout"):
            storage._destination_validated(path, "private", timeout=0.05)
    assert storage.verify(path)["counts"]["claims"] == 0
