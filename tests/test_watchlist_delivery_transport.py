"""Strict trusted-port outcomes; all provider behavior is fake."""

import pytest

from card_market_tracker.telegram_delivery.transport import Receipt, TransportResult
from card_market_tracker.watchlist_delivery import transport_adapter as adapter


@pytest.mark.parametrize(
    "result,expected",
    [
        (TransportResult("confirmed", receipt=Receipt(3, 1, 1, 2)), "confirmed"),
        (TransportResult("retryable", "provider_rate_limit", 1), "retryable"),
        (TransportResult("retryable", "provider_rate_limit", 86400), "retryable"),
        (TransportResult("permanent_failure", "provider_rejection"), "permanent_failure"),
        (TransportResult("uncertain", "transport_timeout"), "uncertain"),
        (TransportResult("confirmed", receipt=Receipt(True, 1, 1, 2)), "uncertain"),
        (TransportResult("confirmed", receipt=Receipt(3, 1, True, 2)), "uncertain"),
        (TransportResult("confirmed", receipt=Receipt(3, 1, 1, 9)), "uncertain"),
        (
            TransportResult("confirmed", "provider_invalid", receipt=Receipt(3, 1, 1, 2)),
            "uncertain",
        ),
        (TransportResult("confirmed"), "uncertain"),
        (TransportResult("retryable", "provider_rate_limit", True), "uncertain"),
        (TransportResult("retryable", "provider_rate_limit", 0), "uncertain"),
        (TransportResult("retryable", "provider_rate_limit", 86401), "uncertain"),
        (TransportResult("retryable", "provider_invalid", 1), "uncertain"),
        (TransportResult("uncertain", "unknown_sensitive_error"), "uncertain"),
        ({"state": "confirmed"}, "uncertain"),
        (None, "uncertain"),
    ],
)
def test_native_outcomes_exact_types_and_combinations(result, expected):
    value = adapter.normalize_result(result, 1, 2)
    assert set(value) == {"state", "error_category", "retry_after", "receipt"}
    assert value["state"] == expected
    if expected == "uncertain" and not (
        type(result) is TransportResult
        and result.state == "uncertain"
        and result.error_category == "transport_timeout"
    ):
        assert value["error_category"] == "provider_invalid"
    if expected != "confirmed":
        assert value["receipt"] is None


def test_subclasses_and_malformed_native_instances_are_not_authority():
    class Derived(TransportResult):
        pass

    assert (
        adapter.normalize_result(Derived("confirmed", receipt=Receipt(3, 1, 1, 2)), 1, 2)["state"]
        == "uncertain"
    )
    assert adapter.normalize_result(object.__new__(TransportResult), 1, 2)["state"] == "uncertain"


def test_factory_reuses_unmodified_native_type(monkeypatch):
    from card_market_tracker.telegram_delivery import transport

    class FakeNative:
        pass

    monkeypatch.setattr(transport, "TelegramTransport", FakeNative)
    assert type(adapter.new_transport()) is FakeNative
