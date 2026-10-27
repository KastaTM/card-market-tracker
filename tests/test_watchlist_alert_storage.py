"""DB author unit integration: exact catalog, immutable atomic pairs and bounded reads."""

from __future__ import annotations

import copy
import json
import re
import sqlite3
from pathlib import Path

import pytest

from card_market_tracker.watchlist_alerts import policy, schema, storage
from card_market_tracker.watchlist_alerts.errors import OutboxError
from card_market_tracker.watchlist_journal import identity, transitions

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def evidence():
    vectors = json.loads((FIXTURES / "p5b_identity_vectors_v1.json").read_text())["vectors"]
    first, second = vectors["baseline"]["object"], vectors["second"]["object"]
    signal = next(s for s in transitions.derive_signals(first, second) if s["rule"] == "price")
    predecessor, prior_result = identity.validate_snapshot(first)
    current, current_result = identity.validate_snapshot(second)
    return {
        "version": 1,
        "signal": signal,
        "predecessor": {
            "evaluation_id": identity.evaluation_id(first),
            "sequence_id": first["sequence_id"],
            "ordinal": 1,
            "predecessor_evaluation_id": None,
            "snapshot": predecessor,
            "evaluation_result": prior_result,
        },
        "current": {
            "evaluation_id": identity.evaluation_id(second),
            "sequence_id": second["sequence_id"],
            "ordinal": 2,
            "predecessor_evaluation_id": identity.evaluation_id(first),
            "snapshot": current,
            "evaluation_result": current_result,
        },
    }


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "outbox.db"
    storage.initialize(path)
    return path


def record(path, evidence, alias="local-preview"):
    """Private writer integration; original authority is tested separately by ARQ."""
    from card_market_tracker.watchlist_alerts import application

    budget = storage.Budget()
    return storage._enqueue_verified(
        path, application._issue(policy.prepare(evidence, alias), budget), budget
    )


@pytest.fixture
def populated(database, evidence):
    recorded = record(database, evidence)
    return database, evidence, recorded["alert_id"]


def category(expected, operation):
    with pytest.raises(OutboxError) as caught:
        operation()
    assert caught.value.category == expected


def privileged(path, table, sql, values=()):
    trigger = table + "_no_update"
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA ignore_check_constraints=ON")
        db.execute("DROP TRIGGER " + trigger)
        db.execute(sql, values)
        db.execute(next(s for s in schema.STATEMENTS if "CREATE TRIGGER " + trigger in s))


def test_exact_frozen_ddl_inventory_strict_and_configuration(database):
    contract = (
        Path(__file__).parents[1] / "docs/data-contracts/WATCHLIST_ALERT_OUTBOX_STORAGE_V1.md"
    )
    fence = chr(96) * 3
    statements = tuple(
        re.findall(
            r"(?ms)^" + fence + r"sql\n(.*?)\n" + fence, contract.read_text(encoding="utf-8")
        )
    )
    assert schema.STATEMENTS == statements
    assert len(statements) == 10 and len(schema.expected_inventory()) == 13
    with sqlite3.connect(database) as db:
        assert db.execute("PRAGMA application_id").fetchone() == (0x434D5459,)
        assert db.execute("PRAGMA user_version").fetchone() == (1,)
        assert db.execute("PRAGMA journal_mode").fetchone() == ("delete",)
        actual = tuple(
            db.execute("SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name")
        )
        assert actual == schema.expected_inventory()
        assert all(
            row[5] == 1
            for row in db.execute("PRAGMA table_list")
            if row[1].startswith("watchlist_alert")
        )
    with storage._connect(database, storage.Budget()) as db:
        assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert db.execute("PRAGMA trusted_schema").fetchone()[0] == 0
        assert db.execute("PRAGMA query_only").fetchone()[0] == 1
        assert db.getlimit(sqlite3.SQLITE_LIMIT_LENGTH) == 524288
        assert db.getlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH) == 65536
    assert storage.verify(database)["counts"] == {"alerts": 0, "evidence": 0}


def test_explicit_init_no_clobber_or_implicit_creation(database, evidence, tmp_path):
    before = database.read_bytes()
    category("unsafe_destination", lambda: storage.initialize(database))
    assert database.read_bytes() == before
    missing = tmp_path / "missing.db"
    category("storage_missing", lambda: record(missing, evidence))
    category("storage_missing", lambda: storage.verify(missing))
    assert not missing.exists()


@pytest.mark.parametrize(
    "table", ["watchlist_alert_metadata", "watchlist_alerts", "watchlist_alert_evidence"]
)
@pytest.mark.parametrize("operation", ["UPDATE", "DELETE"])
def test_all_six_immutable_triggers_reject_even_noop(populated, table, operation):
    path, _, _ = populated
    with sqlite3.connect(path) as db:
        column = "owner" if table == "watchlist_alert_metadata" else "alert_id"
        sql = (
            "DELETE FROM " + table
            if operation == "DELETE"
            else f"UPDATE {table} SET {column}={column}"
        )
        with pytest.raises(sqlite3.IntegrityError, match="immutable_"):
            db.execute(sql)


@pytest.mark.parametrize(
    "field,value",
    [
        ("alert_id", "walt1_" + "A" * 64),
        ("alert_id", "alt1__" + "a" * 64),
        ("signal_id", "wsig1_" + "g" * 64),
        ("destination_key", "Upper"),
        ("destination_key", "a.b"),
        ("destination_key", "a\x00b"),
        ("destination_key", "?"),
        ("intent_sha256", "A" * 64),
        ("renderer_version", 2),
        ("channel", "telegram"),
        ("state", "sent"),
    ],
)
def test_sql_constraints_under_trusted_schema_off(database, evidence, field, value):
    values = {
        **policy.prepare(evidence, "sql-preview"),
        "first_prepared_at": "2026-10-26T12:00:00.000000Z",
        field: value,
    }
    with sqlite3.connect(database) as db:
        db.execute("PRAGMA trusted_schema=OFF")
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(
                "INSERT INTO watchlist_alerts VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                tuple(values[k] for k in storage._ALERT_FIELDS),
            )


def test_replay_preserves_bytes_time_cardinality_and_response_shapes(populated):
    path, bundle, aid = populated
    before = path.read_bytes()
    first = storage.get(path, aid)["alert"]
    assert record(path, bundle)["result"] == "replayed"
    assert path.read_bytes() == before and storage.get(path, aid)["alert"] == first
    assert len(first) == 12
    assert storage.preview(path, aid)["message_text"] == first["message_text"]
    assert storage.evidence_get(path, aid)["evidence"] == bundle
    items = storage.list_alerts(path)["items"]
    assert len(items) == 1 and len(items[0]) == 10
    assert "intent" not in items[0] and "message_text" not in items[0]
    assert storage.verify(path)["counts"] == {"alerts": 1, "evidence": 1}
    alert, evidence = storage._get_pair(path, aid, storage.Budget())
    assert alert == first and evidence == bundle


def test_aliases_and_rules_produce_separate_alerts(database, evidence):
    second = copy.deepcopy(evidence)
    signals = transitions.derive_signals(
        evidence["predecessor"]["snapshot"], evidence["current"]["snapshot"]
    )
    second["signal"] = next(s for s in signals if s["rule"] == "restock")
    rows = [record(database, b, a) for b in (evidence, second) for a in ("a", "b")]
    assert len({r["alert_id"] for r in rows}) == 4
    assert storage.verify(database)["counts"] == {"alerts": 4, "evidence": 4}


def test_valid_changed_metadata_same_identity_conflicts_without_overwrite(populated):
    path, bundle, aid = populated
    changed = copy.deepcopy(bundle)
    changed["predecessor"]["ordinal"] = 2
    changed["predecessor"]["predecessor_evaluation_id"] = "wje1_" + "0" * 64
    changed["current"]["ordinal"] = 3
    assert policy.prepare(changed, "local-preview")["alert_id"] == aid
    before = path.read_bytes()
    category("replay_conflict", lambda: record(path, changed))
    assert path.read_bytes() == before


@pytest.mark.parametrize("missing", ["watchlist_alert_evidence", "watchlist_alerts"])
def test_missing_half_never_repaired(populated, missing):
    path, bundle, aid = populated
    with sqlite3.connect(path) as db:
        db.execute("DROP TRIGGER " + missing + "_no_delete")
        db.execute("DELETE FROM " + missing)
        db.execute(
            next(s for s in schema.STATEMENTS if "CREATE TRIGGER " + missing + "_no_delete" in s)
        )
    before = path.read_bytes()
    category("storage_corrupt", lambda: storage.get(path, aid))
    category("storage_corrupt", lambda: storage.verify(path))
    category("storage_corrupt", lambda: record(path, bundle))
    assert path.read_bytes() == before


def test_rehashed_result_corruption_with_restored_triggers(populated):
    path, bundle, aid = populated
    changed = copy.deepcopy(bundle)
    changed["current"]["evaluation_result"]["rules"][0]["result"] = "NO_MATCH"
    raw = policy.canonical(changed)
    privileged(
        path,
        "watchlist_alert_evidence",
        "UPDATE watchlist_alert_evidence SET evidence_json=?,evidence_sha256=?",
        (raw, policy.digest(raw)),
    )
    category("storage_corrupt", lambda: storage.verify(path))
    category("storage_corrupt", lambda: storage.preview(path, aid))


@pytest.mark.parametrize(
    "field,value",
    [
        ("message_text", "coherently changed"),
        ("first_prepared_at", "2026-02-30T12:00:00.000000Z"),
        ("intent_json", "{" + " " * 300000 + "}"),
    ],
    ids=["changed-message", "invalid-calendar", "oversized-intent-300000"],
)
def test_hostile_cell_and_operational_date_rejected(populated, field, value):
    path, _, aid = populated
    privileged(path, "watchlist_alerts", f"UPDATE watchlist_alerts SET {field}=?", (value,))
    category("storage_corrupt", lambda: storage.get(path, aid))


def test_invalid_utf8_sqlite_text_is_corruption(populated):
    path, _, aid = populated
    privileged(
        path, "watchlist_alerts", "UPDATE watchlist_alerts SET message_text=CAST(x'80' AS TEXT)"
    )
    category("storage_corrupt", lambda: storage.preview(path, aid))


def test_extra_schema_object_rejected(database):
    with sqlite3.connect(database) as db:
        db.execute("CREATE VIEW unexpected AS SELECT 1")
    category("storage_schema", lambda: storage.verify(database))


def test_keyset_pages_filter_binding_and_cursor_validation(database, evidence):
    for alias in ("a", "b", "c"):
        record(database, evidence, alias)
    first = storage.list_alerts(database, limit=1)
    second = storage.list_alerts(database, limit=1, cursor=first["next_cursor"])
    third = storage.list_alerts(database, limit=1, cursor=second["next_cursor"])
    ids = [page["items"][0]["alert_id"] for page in (first, second, third)]
    assert ids == sorted(set(ids)) and third["next_cursor"] is None
    category(
        "invalid_cursor",
        lambda: storage.list_alerts(database, destination_key="a", cursor=first["next_cursor"]),
    )
    for cursor in ("", "x", "A" * 2049, "!!!!", first["next_cursor"] + " "):
        category(
            "invalid_cursor", lambda cursor=cursor: storage.list_alerts(database, cursor=cursor)
        )
    category("invalid_field", lambda: storage.list_alerts(database, limit=True))
    assert len(storage.list_alerts(database, destination_key="b")["items"]) == 1


@pytest.mark.parametrize("timeout", [True, 0, -1, 6, float("nan"), float("inf")])
def test_invalid_timeout_rejected_before_storage(database, timeout):
    category("invalid_field", lambda: storage.verify(database, timeout=timeout))


def test_failure_between_insertions_rolls_back_pair(database, evidence, monkeypatch):
    before = database.read_bytes()
    execute = storage._execute

    def fail_evidence(db, budget, sql, values=()):
        if sql.startswith("INSERT INTO watchlist_alert_evidence"):
            raise OSError("controlled disk failure")
        return execute(db, budget, sql, values)

    monkeypatch.setattr(storage, "_execute", fail_evidence)
    category("storage_io", lambda: record(database, evidence))
    assert storage.verify(database)["counts"] == {"alerts": 0, "evidence": 0}
    assert database.read_bytes() == before


def test_expired_shared_deadline(database):
    budget = storage.Budget()
    budget.deadline = 0
    category("storage_timeout", lambda: storage.verify(database, _budget=budget))


def test_unissued_receipt_cannot_open_writer(database, evidence, monkeypatch):
    prepared = policy.prepare(evidence, "local-preview")

    def forbidden(*args, **kwargs):
        raise AssertionError("unissued receipt reached writer")

    monkeypatch.setattr(storage, "_connect", forbidden)
    category(
        "unsupported_evidence",
        lambda: storage._enqueue_verified(database, prepared, storage.Budget()),
    )
