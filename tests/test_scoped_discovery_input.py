"""Strict v2 request budgets, exact selectors and forged Python inputs."""

import json
from dataclasses import replace

import pytest

from card_market_tracker.discovery.errors import DiscoveryError
from card_market_tracker.discovery.models import DiscoveryContext
from card_market_tracker.discovery.scoped_input import parse_request, read_request, validate_request
from card_market_tracker.discovery.scoped_models import ScopedDiscoveryRequest, ScopedSelection

CURRENT = "22222222-2222-4222-8222-222222222222"
HISTORY = "11111111-1111-4111-8111-111111111111"


def document(**changes):
    return {
        "version": 2,
        "context": {"namespace": "synthetic_scope", "kind": "set", "language": "es"},
        "current": {"batch_id": CURRENT, "selector": "unit"},
        "history": [{"batch_id": HISTORY, "selector": "unit"}],
        **changes,
    }


@pytest.mark.parametrize("kind", ["set", "card", "sealed"])
@pytest.mark.parametrize("language", [None, "es", "en"])
def test_exact_request_context_and_canonical_order(kind, language):
    other = "33333333-3333-4333-8333-333333333333"
    parsed = parse_request(
        document(
            context={"namespace": "p1a.Token:-_", "kind": kind, "language": language},
            history=[
                {"batch_id": other, "selector": "other"},
                {"batch_id": HISTORY, "selector": "unit"},
            ],
        )
    )
    assert parsed.context == DiscoveryContext("p1a.Token:-_", kind, language)
    assert [entry.batch_id for entry in parsed.history] == [HISTORY, other]
    assert validate_request(parsed) == parsed
    assert parse_request(parsed.to_dict()) == parsed


@pytest.mark.parametrize(
    "changes,category",
    [
        ({"version": True}, "unsupported_version"),
        ({"version": 1}, "unsupported_version"),
        ({"version": 2.0}, "unsupported_version"),
        ({"version": "2"}, "unsupported_version"),
        ({"history": None}, "invalid_shape"),
        ({"history": ()}, "invalid_shape"),
        ({"history": [{"batch_id": CURRENT, "selector": "other"}]}, "duplicate_id"),
        (
            {
                "history": [
                    {"batch_id": HISTORY, "selector": "a"},
                    {"batch_id": HISTORY, "selector": "b"},
                ]
            },
            "duplicate_id",
        ),
        ({"history": [{"batch_id": HISTORY}]}, "invalid_shape"),
        (
            {"current": {"batch_id": CURRENT, "selector": "unit", "record_indexes": [0]}},
            "invalid_shape",
        ),
        ({"current": {"batch_id": CURRENT, "selector": ""}}, "invalid_field"),
        ({"current": {"batch_id": CURRENT, "selector": "x" * 257}}, "invalid_field"),
        ({"current": {"batch_id": CURRENT.upper(), "selector": "unit"}}, None),
        (
            {"current": {"batch_id": "AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA", "selector": "unit"}},
            "invalid_field",
        ),
        (
            {"current": {"batch_id": "00000000-0000-0000-0000-000000000000", "selector": "unit"}},
            "invalid_field",
        ),
        (
            {"context": {"namespace": "https://bad", "kind": "set", "language": "es"}},
            "invalid_field",
        ),
        ({"context": {"namespace": "x" * 129, "kind": "set", "language": "es"}}, "invalid_field"),
        (
            {"context": {"namespace": "synthetic_scope", "kind": "printing", "language": "es"}},
            "invalid_field",
        ),
        (
            {"context": {"namespace": "synthetic_scope", "kind": "set", "language": False}},
            "invalid_field",
        ),
        (
            {"context": {"namespace": "synthetic_scope", "kind": "set", "language": "ES"}},
            "invalid_field",
        ),
        (
            {"context": {"namespace": "synthetic_scope", "kind": "set", "language": "fr"}},
            "invalid_field",
        ),
        ({"context": {"namespace": "synthetic_scope", "kind": "set"}}, "invalid_shape"),
        ({"path": "/never/open"}, "invalid_shape"),
        ({"url": "https://never/request"}, "invalid_shape"),
        ({"sql": "SELECT * FROM records"}, "invalid_shape"),
        ({"reference": {"external_id": "ignored"}}, "invalid_shape"),
    ],
)
def test_invalid_requests(changes, category):
    if category is None:
        assert parse_request(document(**changes)).version == 2
    else:
        with pytest.raises(DiscoveryError) as caught:
            parse_request(document(**changes))
        assert caught.value.category == category and caught.value.exit_code == 2
        assert str(caught.value) == category


@pytest.mark.parametrize("key", ["version", "context", "current", "history"])
def test_required_keys(key):
    value = document()
    del value[key]
    with pytest.raises(DiscoveryError, match="invalid_shape"):
        parse_request(value)


def test_limits_depth_nodes_strings_bytes_and_history():
    for changes in (
        {"history": [{"batch_id": HISTORY, "selector": "unit"}] * 33},
        {"extra": "x" * 1025},
        {"extra": [None] * 20001},
        {"extra": ["x" * 1024] * 1025},
    ):
        with pytest.raises(DiscoveryError, match="input_limit"):
            parse_request(document(**changes))
    deep = None
    for _ in range(17):
        deep = [deep]
    with pytest.raises(DiscoveryError, match="input_limit"):
        parse_request(document(extra=deep))
    with pytest.raises(DiscoveryError, match="invalid_json"):
        parse_request(document(version=10**5000))


@pytest.mark.parametrize("value", [float("nan"), float("inf"), "\ud800", object()])
def test_non_json_python_values(value):
    with pytest.raises(DiscoveryError) as caught:
        parse_request(document(extra=value))
    assert caught.value.category in ("invalid_json", "invalid_shape")


@pytest.mark.parametrize(
    "changes",
    [
        {"version": True},
        {"context": {}},
        {"current": {}},
        {"history": []},
        {"history": (object(),)},
        {"history": (ScopedSelection(HISTORY, "unit"),) * 33},
        {"context": DiscoveryContext("synthetic_scope", "set", "fr")},
        {"current": ScopedSelection(CURRENT, "")},
    ],
)
def test_forged_python_request(changes):
    with pytest.raises(DiscoveryError):
        validate_request(replace(parse_request(document()), **changes))


def test_wrong_and_missing_dto_attributes():
    for value in ({}, object(), object.__new__(ScopedDiscoveryRequest)):
        with pytest.raises(DiscoveryError, match="invalid_shape"):
            validate_request(value)


@pytest.mark.parametrize(
    "raw,category",
    [
        ('{"version":2,"version":2}', "duplicate_key"),
        ('{"history":[{"selector":"a","selector":"b"}]}', "duplicate_key"),
        ('{"extra":NaN}', "invalid_json"),
        ('{"extra":"\\ud800"}', "invalid_json"),
        ("[" * 17, "input_limit"),
        (" " * 1048577, "input_limit"),
        ("{", "invalid_json"),
    ],
    ids=["top-dupe", "nested-dupe", "nonfinite", "surrogate", "depth", "bytes", "syntax"],
)
def test_json_file_failures(tmp_path, raw, category):
    path = tmp_path / "request.json"
    path.write_bytes(raw.encode())
    with pytest.raises(DiscoveryError, match=category):
        read_request(path)


def test_input_io_and_file_roundtrip(tmp_path):
    for path in (tmp_path, tmp_path / "missing"):
        with pytest.raises(DiscoveryError, match="input_io"):
            read_request(path)
    path = tmp_path / "request.json"
    path.write_text(json.dumps(document()))
    assert read_request(path) == parse_request(document())
