"""Future qualification wrapper accounting tests: native fake port only."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from test_watchlist_delivery_application import Fake, prepared

from card_market_tracker.persistence.errors import PersistenceError
from card_market_tracker.telegram_delivery.transport import Receipt, TransportResult
from card_market_tracker.watchlist_delivery import application as app
from card_market_tracker.watchlist_delivery.errors import DeliveryError

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "p8d_qualification", ROOT / "scripts/watchlist_telegram_qualification.py"
)
assert SPEC is not None and SPEC.loader is not None
qual = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qual)


def dossier(tmp_path, monkeypatch):
    ledger, origins, did = prepared(tmp_path)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(origins[3]), encoding="utf-8")
    monkeypatch.setattr(qual, "_candidate", lambda *args: None)
    monkeypatch.setattr(qual, "_ensure_installed", lambda: None)
    directory = tmp_path / "qualification"
    record = qual.preflight(
        directory, ROOT, "1" * 40, "2" * 40, ledger, *origins[:3], manifest, did
    )
    pending = json.loads((directory / "authorization-template.json").read_text())
    pending.update(decision=qual.DECISION, authorization_reference="synthetic-test-only")
    authorization = tmp_path / "authorization.json"
    authorization.write_text(json.dumps(pending), encoding="utf-8")
    return directory, authorization, ledger, origins, did, record


def test_preflight_is_offline_specific_and_does_not_grant_permission(tmp_path, monkeypatch):
    monkeypatch.setattr(
        app, "_transport_factory", lambda: pytest.fail("Unexpected provider factory")
    )
    directory, authorization, ledger, origins, did, record = dossier(tmp_path, monkeypatch)
    assert record["live_status"] == "LIVE_UNVERIFIED"
    assert record["request_counters"]["send_attempt_upper_bound"] == 0
    template = json.loads((directory / "authorization-template.json").read_text())
    assert template["decision"] == "PENDING_NOT_AUTHORIZED"
    assert record["selection"]["delivery_id"] == did
    public = json.dumps(record)
    assert all(
        key not in public for key in ('"bot_id"', '"chat_id"', '"message_id"', '"message_text"')
    )
    with pytest.raises(PersistenceError, match="unsafe_destination"):
        qual.preflight(
            directory,
            ROOT,
            "1" * 40,
            "2" * 40,
            ledger,
            *origins[:3],
            tmp_path / "manifest.json",
            did,
        )


def test_wrong_exact_authorization_never_constructs_client(tmp_path, monkeypatch):
    directory, authorization, _, _, _, _ = dossier(tmp_path, monkeypatch)
    wrong = json.loads(authorization.read_text())
    wrong["selection"]["message_sha256"] = "0" * 64
    authorization.write_text(json.dumps(wrong), encoding="utf-8")
    monkeypatch.setattr(
        app, "_transport_factory", lambda: pytest.fail("Unauthorized provider factory")
    )
    with pytest.raises(qual.QualificationError, match="specific_operator"):
        qual.remote(directory, authorization, "validate")
    assert (directory / "active.json").exists()
    assert qual._counters(qual._events(directory))["send_attempt_upper_bound"] == 0


def test_fake_validate_one_send_durable_receipt_and_no_second_allowance(tmp_path, monkeypatch):
    directory, authorization, ledger, origins, did, _ = dossier(tmp_path, monkeypatch)
    fake = Fake(TransportResult("confirmed", receipt=Receipt(3, 1, 1, 2)))

    def reserved_before_dispatch():
        assert qual._counters(qual._events(directory))["send_attempt_upper_bound"] == 1

    fake.check = reserved_before_dispatch
    monkeypatch.setattr(app, "_transport_factory", lambda: fake)
    validated = qual.remote(directory, authorization, "validate")
    assert validated["request_counters"]["metadata_request_upper_bound"] == 2
    # No extra original recompute can run outside app.send's aggregate scope.
    monkeypatch.setattr(
        app, "recompute", lambda *a, **k: pytest.fail("Duplicated original admission")
    )
    sent = qual.remote(directory, authorization, "send")
    assert sent["durable_receipt_verified"] is True
    assert sent["live_status"] == "LIVE_UNVERIFIED"
    assert sent["request_counters"]["metadata_request_upper_bound"] == 3
    assert sent["request_counters"]["send_attempt_upper_bound"] == 1
    assert app.get(ledger, did)["delivery"]["state"] == "confirmed"
    assert fake.calls.count("send") == 1
    assert qual.postflight(directory)["originals_unchanged"] is True
    replay = qual.replay(directory)
    assert replay["durable_receipt_verified"] is True
    assert replay["request_counters"]["send_attempt_upper_bound"] == 1
    with pytest.raises(qual.QualificationError, match="budget_exhausted"):
        qual.remote(directory, authorization, "send")
    assert fake.calls.count("send") == 1


@pytest.mark.parametrize(
    "state,category,retry",
    [
        ("retryable", "provider_rate_limit", 1),
        ("uncertain", "transport_timeout", None),
        ("permanent_failure", "provider_rejection", None),
    ],
)
def test_failed_fake_attempt_always_consumes_single_qualification_send(
    tmp_path, monkeypatch, state, category, retry
):
    directory, authorization, _, _, _, _ = dossier(tmp_path, monkeypatch)
    fake = Fake(TransportResult(state, category, retry))
    monkeypatch.setattr(app, "_transport_factory", lambda: fake)
    qual.remote(directory, authorization, "validate")
    result = qual.remote(directory, authorization, "send")
    assert result["result"] == "error"
    assert result["request_counters"]["send_attempt_upper_bound"] == 1
    with pytest.raises(qual.QualificationError, match="budget_exhausted"):
        qual.remote(directory, authorization, "send")
    assert fake.calls.count("send") == 1


def test_metadata_cap_and_crash_marker_are_durable(tmp_path, monkeypatch):
    directory, authorization, _, _, _, _ = dossier(tmp_path, monkeypatch)
    fake = Fake()
    monkeypatch.setattr(app, "_transport_factory", lambda: fake)
    for count in range(1, 5):
        result = qual.remote(directory, authorization, "validate")
        assert result["request_counters"]["metadata_request_upper_bound"] == count * 2
    assert qual.remote(directory, authorization, "validate")["result"] == "error"
    assert fake.calls.count("destination") == 4
    assert qual._counters(qual._events(directory))["metadata_request_upper_bound"] == 8
    # Existing active evidence is never removed or overwritten on a crash path.
    marker = directory / "active.json"
    if not marker.exists():
        marker.write_text("foreign crash evidence", encoding="utf-8")
    before = marker.read_bytes()
    with pytest.raises(FileExistsError):
        qual.remote(directory, authorization, "validate")
    assert marker.read_bytes() == before


def test_postflight_detects_source_change_offline(tmp_path, monkeypatch):
    directory, _, _, origins, _, _ = dossier(tmp_path, monkeypatch)
    monkeypatch.setattr(app, "_transport_factory", lambda: pytest.fail("No provider in postflight"))
    with origins[0].open("ab") as output:
        output.write(b"changed synthetic test source")
    with pytest.raises(qual.QualificationError, match="originals_changed"):
        qual.postflight(directory)


def test_error_arguments_are_redacted(capsys):
    assert (
        qual.main(
            ["--operation", "validate", "--directory", "unused", "--token", "PRIVATE_SENTINEL"]
        )
        == 1
    )
    output = capsys.readouterr()
    assert "PRIVATE_SENTINEL" not in output.out + output.err
    assert json.loads(output.out)["error_category"] == "invalid_arguments"


def test_expired_reservation_never_reaches_fake_provider(tmp_path, monkeypatch):
    import card_market_tracker.watchlist_delivery.budget as budget_module

    directory, authorization, ledger, _, did, _ = dossier(tmp_path, monkeypatch)
    fake = Fake(TransportResult("confirmed", receipt=Receipt(3, 1, 1, 2)))
    monkeypatch.setattr(app, "_transport_factory", lambda: fake)
    qual.remote(directory, authorization, "validate")
    moment = [100.0]
    monkeypatch.setattr(budget_module.time, "monotonic", lambda: moment[0])
    append = qual._append

    def delayed_reservation(target, kind, payload):
        append(target, kind, payload)
        if kind == "method-reserved" and payload["method"] == "send":
            moment[0] += 31

    monkeypatch.setattr(qual, "_append", delayed_reservation)
    with pytest.raises(DeliveryError, match="storage_timeout"):
        qual.remote(directory, authorization, "send", timeout=15)
    assert fake.calls.count("send") == 0
    assert qual._counters(qual._events(directory))["send_attempt_upper_bound"] == 1
    assert app.get(ledger, did)["delivery"]["state"] in {"in_flight", "uncertain"}
    assert (directory / "active.json").exists()
