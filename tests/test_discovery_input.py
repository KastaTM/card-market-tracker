"""Discovery request JSON budgets and direct-Python forgery boundaries."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

from card_market_tracker.catalog.validation import CatalogError
from card_market_tracker.discovery import (
    DiscoveryError,
    parse_request,
    read_request,
    validate_request,
)
from card_market_tracker.discovery.models import DiscoveryContext, DiscoveryRequest
from card_market_tracker.discovery.validation import bounded_value

CURRENT = "22222222-2222-4222-8222-222222222222"
HISTORY = "11111111-1111-4111-8111-111111111111"
FIXTURES = Path(__file__).parent / "fixtures"


def document(**kwargs):
    return {
        "version": 1,
        "current_batch_id": CURRENT,
        "history_batch_ids": [HISTORY],
        "context": {"namespace": "synthetic", "kind": "set", "language": "es"},
        **kwargs,
    }


@pytest.mark.parametrize("language", [None, "es", "en"])
@pytest.mark.parametrize("kind", ["set", "card", "sealed"])
def test_exact_context_and_canonical_history(kind, language):
    other = "33333333-3333-4333-8333-333333333333"
    parsed = parse_request(
        document(
            history_batch_ids=[other, HISTORY],
            context={"namespace": "curated", "kind": kind, "language": language},
        )
    )
    assert parsed.context == DiscoveryContext("curated", kind, language)
    assert parsed.history_batch_ids == (HISTORY, other)
    assert validate_request(parsed) == parsed
    assert parse_request(parsed.to_dict()) == parsed


@pytest.mark.parametrize(
    "changes,category",
    [
        ({"version": True}, "unsupported_version"),
        ({"version": 0}, "unsupported_version"),
        ({"version": "1"}, "unsupported_version"),
        ({"version": None}, "unsupported_version"),
        ({"current_batch_id": "secret-invalid"}, "invalid_field"),
        ({"current_batch_id": "AAAAAAAA-1111-4111-8111-111111111111"}, "invalid_field"),
        ({"current_batch_id": "00000000-0000-0000-0000-000000000000"}, "invalid_field"),
        ({"history_batch_ids": [HISTORY, HISTORY]}, "duplicate_id"),
        ({"history_batch_ids": [CURRENT]}, "duplicate_id"),
        ({"history_batch_ids": None}, "invalid_shape"),
        ({"history_batch_ids": (HISTORY,)}, "invalid_shape"),
        ({"history_batch_ids": ["secret"]}, "invalid_field"),
        ({"extra": "secret"}, "invalid_shape"),
        ({"context": None}, "invalid_shape"),
        ({"context": {"namespace": "s", "kind": "set"}}, "invalid_shape"),
        (
            {"context": {"namespace": "s", "kind": "set", "language": "es", "variant": "normal"}},
            "invalid_shape",
        ),
        (
            {"context": {"namespace": "https://secret", "kind": "set", "language": "es"}},
            "invalid_field",
        ),
        ({"context": {"namespace": "s", "kind": "printing", "language": "es"}}, "invalid_field"),
        ({"context": {"namespace": "s", "kind": "set", "language": "fr"}}, "invalid_field"),
        ({"context": {"namespace": "s", "kind": "set", "language": False}}, "invalid_field"),
    ],
)
def test_invalid_exact_request(changes, category):
    with pytest.raises(DiscoveryError) as caught:
        parse_request(document(**changes))
    assert caught.value.category == category and caught.value.exit_code == 2
    assert str(caught.value) == category


@pytest.mark.parametrize("missing", ["version", "current_batch_id", "history_batch_ids", "context"])
def test_missing_fields(missing):
    value = document()
    del value[missing]
    with pytest.raises(DiscoveryError, match="invalid_shape"):
        parse_request(value)


def test_request_limits_strings_nodes_depth_bytes_and_huge_int():
    with pytest.raises(DiscoveryError, match="input_limit"):
        parse_request(document(history_batch_ids=[HISTORY] * 33))
    with pytest.raises(DiscoveryError, match="input_limit"):
        parse_request(document(extra="x" * 1025))
    with pytest.raises(DiscoveryError, match="input_limit"):
        parse_request(document(extra=[None] * 20001))
    deep = None
    for _ in range(17):
        deep = [deep]
    with pytest.raises(DiscoveryError, match="input_limit"):
        parse_request(document(extra=deep))
    with pytest.raises(DiscoveryError, match="input_limit"):
        parse_request(document(extra=["x" * 1024] * 1025))
    with pytest.raises(DiscoveryError, match="invalid_json"):
        parse_request(document(version=10**5000))


@pytest.mark.parametrize("extra", [float("nan"), float("inf"), "\ud800", object()])
def test_non_json_python_values_are_safe(extra):
    with pytest.raises(DiscoveryError) as caught:
        parse_request(document(extra=extra))
    assert caught.value.category in ("invalid_json", "invalid_shape")


@pytest.mark.parametrize(
    "field,value",
    [
        ("version", True),
        ("current_batch_id", "secret"),
        ("history_batch_ids", [HISTORY]),
        ("history_batch_ids", (HISTORY,) * 33),
        ("context", {}),
        ("context", DiscoveryContext("synthetic", "set", "fr")),
    ],
)
def test_constructor_forgery_revalidated(field, value):
    parsed = parse_request(document())
    with pytest.raises(DiscoveryError):
        validate_request(replace(parsed, **{field: value}))


def test_missing_attribute_and_wrong_dto_fail_safe():
    for value in ({}, object.__new__(DiscoveryRequest)):
        with pytest.raises(DiscoveryError, match="invalid_shape"):
            validate_request(value)


@pytest.mark.parametrize(
    "raw,category",
    [
        (b"{", "invalid_json"),
        (b"\xff", "invalid_json"),
        (b'{"version":1,"version":1}', "duplicate_key"),
        (b'{"context":{"language":null,"language":"es"}}', "duplicate_key"),
        (b'{"value":NaN}', "invalid_json"),
        (b"[" * 17 + b"]" * 17, "input_limit"),
        (b" " * 1_048_577, "input_limit"),
    ],
    ids=["malformed", "utf8", "duplicate_top", "duplicate_nested", "nan", "deep", "large"],
)
def test_bounded_strict_file(tmp_path, raw, category):
    path = tmp_path / "request.json"
    path.write_bytes(raw)
    with pytest.raises(DiscoveryError) as caught:
        read_request(path)
    assert caught.value.category == category and caught.value.exit_code == 2


def test_missing_or_nonregular_file_is_input_io_exit_two(tmp_path):
    for path in (tmp_path / "missing", tmp_path):
        with pytest.raises(DiscoveryError) as caught:
            read_request(path)
        assert caught.value.category == "input_io" and caught.value.exit_code == 2


def test_read_valid_file(tmp_path):
    path = tmp_path / "request.json"
    path.write_text(json.dumps(document()), encoding="utf-8")
    assert read_request(path) == parse_request(document())


def test_all_synthetic_request_fixtures_parse():
    paths = list(FIXTURES.glob("synthetic_discovery_*request.json"))
    assert len(paths) == 6
    for path in paths:
        assert read_request(path).version == 1


def test_errors_allowlist_never_echo_values():
    for category in ("secret-path", {}, None):
        error = DiscoveryError(category)
        assert error.category == "invalid_field" and str(error) == "invalid_field"
    for category in (
        "storage_io",
        "storage_schema",
        "storage_locked",
        "storage_timeout",
        "storage_corrupt",
    ):
        assert DiscoveryError(category).exit_code == 1
    assert DiscoveryError("input_io").exit_code == 2


def test_shared_bounded_value_rejects_bytes_budget():
    with pytest.raises(CatalogError, match="input_limit"):
        bounded_value(["x" * 1024] * 1025)
