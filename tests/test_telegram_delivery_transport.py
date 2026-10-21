"""Offline transport probes: no DNS or Telegram access, including worker tests."""

from __future__ import annotations

import json
import os
import socket
import ssl
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from card_market_tracker.telegram_delivery import transport
from card_market_tracker.telegram_delivery.errors import DeliveryError


@pytest.fixture
def configured(monkeypatch: pytest.MonkeyPatch) -> str:
    # Generated synthetic credential only; never a credential from a bot/provider.
    synthetic = str(123456) + ":" + "x" * 32
    monkeypatch.setenv("CMT_TELEGRAM_BOT_TOKEN", synthetic)
    return synthetic


def _body(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False).encode("utf-8")


def _message() -> dict[str, Any]:
    return {
        "ok": True,
        "result": {
            "message_id": 8,
            "date": 1700000000,
            "chat": {"id": 22, "type": "private", "first_name": "discard me"},
            "from": {"id": 11, "is_bot": True, "first_name": "discard me too"},
            "text": "frozen é https://example.invalid",
        },
    }


def test_minimal_receipt_and_private_repr() -> None:
    result = transport._receipt(200, _body(_message()), 11, 22, _message()["result"]["text"])
    assert result == transport.TransportResult(
        "confirmed", receipt=transport.Receipt(8, 1700000000, 11, 22)
    )
    assert "discard" not in repr(result)
    assert "bot_id" not in repr(result)
    assert "chat_id" not in repr(result)


@pytest.mark.parametrize(
    "body",
    [
        b'{"ok":true,"ok":false}',
        b'{"ok":true,"result":{"x":1,"x":2}}',
        b'{"ok":NaN}',
        b'{"ok":Infinity}',
        b'{"ok":-Infinity}',
        b'{"x":1e999}',
        b"[]",
        b"null",
        b'"string"',
        b'{"x":"\\ud800"}',
        b"\xff",
        b"{",
        b'{"x":' + b"[" * 18 + b"0" + b"]" * 18 + b"}",
        b" " * 65537,
        b"[" * 1500 + b"0" + b"]" * 1500,
    ],
    ids=lambda body: f"body-{len(body)}",
)
def test_strict_untrusted_json(body: bytes) -> None:
    with pytest.raises(DeliveryError, match="provider_invalid"):
        transport._decode(body)


def test_exact_body_limit() -> None:
    assert transport._decode(b'{"x":0}' + b" " * (65536 - 7)) == {"x": 0}
    transport._tree({"finite": 0.5, "list": [None, True]})


@pytest.mark.parametrize(
    "path,value",
    [
        (("message_id",), True),
        (("message_id",), 0),
        (("message_id",), 1.0),
        (("message_id",), 1 << 63),
        (("date",), 0),
        (("date",), True),
        (("date",), 253402300800),
        (("chat", "id"), True),
        (("chat", "id"), 23),
        (("chat", "type"), "group"),
        (("from", "id"), 12),
        (("from", "is_bot"), 1),
        (("text",), "changed"),
        (("from",), None),
        (("chat",), []),
        (("sender_chat",), {}),
        (("sender_business_bot",), {}),
        (("business_connection_id",), "context"),
        (("guest_query_id",), "context"),
        (("ephemeral_message_id",), 1),
    ],
)
def test_success_requires_coherent_projection(path: tuple[str, ...], value: object) -> None:
    message = _message()
    target = message["result"]
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(DeliveryError, match="provider_invalid"):
        transport._receipt(200, _body(message), 11, 22, _message()["result"]["text"])


@pytest.mark.parametrize("key", ["message_id", "date", "chat", "from", "text"])
def test_missing_receipt_fields(key: str) -> None:
    message = _message()
    del message["result"][key]
    with pytest.raises(DeliveryError, match="provider_invalid"):
        transport._receipt(200, _body(message), 11, 22, _message()["result"]["text"])


@pytest.mark.parametrize("status", [400, 401, 403, 404, 422])
def test_unequivocal_rejection(status: int, configured: str) -> None:
    result = transport._receipt(
        status,
        _body(
            {
                "ok": False,
                "error_code": status,
                "description": configured,
            }
        ),
        11,
        22,
        "text",
    )
    assert result == transport.TransportResult("permanent_failure", "provider_rejection")
    assert configured not in repr(result)


@pytest.mark.parametrize("status", [301, 302, 307, 308, 408, 409, 425, 500, 502, 503])
def test_ambiguous_and_redirects_are_uncertain(status: int) -> None:
    result = transport._receipt(
        status,
        _body(
            {
                "ok": False,
                "error_code": status,
                "description": "bounded refusal",
            }
        ),
        11,
        22,
        "text",
    )
    assert result.state == "uncertain"


@pytest.mark.parametrize("value", [1, 86400])
def test_explicit_rate_limit(value: int) -> None:
    result = transport._receipt(
        429,
        _body(
            {
                "ok": False,
                "error_code": 429,
                "description": "rate limit",
                "parameters": {"retry_after": value},
            }
        ),
        11,
        22,
        "text",
    )
    assert result == transport.TransportResult("retryable", "provider_rate_limit", value)


@pytest.mark.parametrize("value", [True, 0, -1, 86401, 1.5, "2", None])
def test_invalid_rate_limit(value: object) -> None:
    with pytest.raises(DeliveryError, match="provider_invalid"):
        transport._receipt(
            429,
            _body(
                {
                    "ok": False,
                    "error_code": 429,
                    "description": "rate limit",
                    "parameters": {"retry_after": value},
                }
            ),
            11,
            22,
            "text",
        )


@pytest.mark.parametrize(
    "patch",
    [
        {"ok": True},
        {"error_code": True},
        {"error_code": 401},
        {"result": {}},
        {"description": ""},
        {"description": "x" * 4097},
        {"description": []},
    ],
)
def test_malformed_rejection_is_uncertain(patch: dict[str, object]) -> None:
    value: dict[str, object] = {"ok": False, "error_code": 400, "description": "refused"}
    value.update(patch)
    assert transport._receipt(400, _body(value), 11, 22, "text").state == "uncertain"


def test_contradictory_error_parameters() -> None:
    with pytest.raises(DeliveryError):
        transport._receipt(
            400,
            _body(
                {
                    "ok": False,
                    "error_code": 400,
                    "description": "refused",
                    "parameters": {},
                }
            ),
            11,
            22,
            "text",
        )
    with pytest.raises(DeliveryError):
        transport._receipt(
            429,
            _body(
                {
                    "ok": False,
                    "error_code": 429,
                    "description": "refused",
                    "parameters": {"retry_after": 1, "migrate_to_chat_id": 42},
                }
            ),
            11,
            22,
            "text",
        )


@pytest.mark.parametrize(
    "value",
    [
        {"ok": 1, "result": {}},
        {"ok": True, "result": {}, "error_code": 400},
        {"ok": True, "result": {}, "parameters": {}},
        {"ok": True, "result": []},
    ],
)
def test_success_envelope(value: object) -> None:
    with pytest.raises(DeliveryError):
        transport._success(200, _body(value))


def test_metadata_bot_and_destination(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    def request(method: str, payload: dict[str, object], deadline: float) -> tuple[int, bytes]:
        calls.append((method, payload))
        result = {"id": 11, "is_bot": True} if method == "getMe" else {"id": 22, "type": "private"}
        return 200, _body({"ok": True, "result": result})

    monkeypatch.setattr(transport, "_request", request)
    assert transport._perform("bot", 11, 1, "", 1) == {"validated": True}
    assert calls == [("getMe", {})]
    calls.clear()
    assert transport._perform("destination", 11, 22, "", 1) == {"validated": True}
    assert calls == [("getMe", {}), ("getChat", {"chat_id": 22})]
    with pytest.raises(DeliveryError, match="destination_mismatch"):
        transport._perform("destination", 11, 23, "", 1)
    with pytest.raises(DeliveryError, match="bot_mismatch"):
        transport._perform("bot", 12, 1, "", 1)


def test_send_exact_payload_only_once(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, object]]] = []
    text = _message()["result"]["text"]

    def request(method: str, payload: dict[str, object], deadline: float) -> tuple[int, bytes]:
        calls.append((method, payload))
        return 200, _body(_message())

    monkeypatch.setattr(transport, "_request", request)
    result = transport._perform("send", 11, 22, text, 1)
    assert result["state"] == "confirmed"
    assert calls == [
        (
            "sendMessage",
            {
                "chat_id": 22,
                "text": text,
                "link_preview_options": {"is_disabled": True},
            },
        )
    ]


def test_fixed_tls_post_without_proxy_redirect_retry(
    monkeypatch: pytest.MonkeyPatch,
    configured: str,
) -> None:
    records: list[object] = []

    class Response:
        status = 302

        def getheaders(self) -> list[tuple[str, str]]:
            return []

        def read(self, limit: int) -> bytes:
            records.append(limit)
            return b"redirect"

    class Connection:
        def __init__(self, host: str, port: int, *, timeout: float, context: ssl.SSLContext):
            assert host == "api.telegram.org" and port == 443
            assert 0 < timeout <= 5
            assert context.verify_mode == ssl.CERT_REQUIRED and context.check_hostname

        def set_debuglevel(self, level: int) -> None:
            assert level == 0

        def request(self, method: str, path: str, *, body: bytes, headers: object) -> None:
            records.append((method, path, json.loads(body), headers))

        def getresponse(self) -> Response:
            return Response()

        def close(self) -> None:
            records.append("closed")

    monkeypatch.setenv("HTTPS_PROXY", "https://proxy.invalid")
    monkeypatch.setattr(transport.http.client, "HTTPSConnection", Connection)
    assert transport._request("getMe", {}, time.monotonic() + 1) == (302, b"redirect")
    assert records[0] == (
        "POST",
        "/bot" + configured + "/getMe",
        {},
        {
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
        },
    )
    assert records[1:] == [65537, "closed"]
    with pytest.raises(DeliveryError, match="provider_invalid"):
        transport._request("arbitrary", {}, time.monotonic() + 1)
    with pytest.raises(DeliveryError, match="transport_timeout"):
        transport._request("getMe", {}, time.monotonic() - 1)


class _Pipe:
    def __init__(self) -> None:
        self.data = b""
        self.closed = False

    def send_bytes(self, data: bytes) -> None:
        self.data = data

    def close(self) -> None:
        self.closed = True


@pytest.mark.parametrize(
    "error,category",
    [
        (RuntimeError, "transport_failure"),
        (ssl.SSLError, "transport_failure"),
        (TimeoutError, "transport_timeout"),
        (KeyboardInterrupt, "transport_failure"),
    ],
)
def test_worker_sanitizes_every_exception(
    monkeypatch: pytest.MonkeyPatch,
    configured: str,
    capsys: pytest.CaptureFixture[str],
    error: type[BaseException],
    category: str,
) -> None:
    def fail(*args: object) -> dict[str, object]:
        raise error("https://api.telegram.org/bot" + configured + "/sendMessage")

    monkeypatch.setattr(transport, "_perform", fail)
    pipe = _Pipe()
    transport._worker(pipe, "send", 11, 22, "private text", 1)  # type: ignore[arg-type]
    assert json.loads(pipe.data) == {"error": category}
    assert configured.encode() not in pipe.data
    assert pipe.closed
    assert capsys.readouterr() == ("", "")


def test_worker_sanitized_delivery_error_and_success(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*args: object) -> dict[str, object]:
        raise DeliveryError("bot_mismatch")

    monkeypatch.setattr(transport, "_perform", fail)
    pipe = _Pipe()
    transport._worker(pipe, "bot", 11, 1, "", 1)  # type: ignore[arg-type]
    assert json.loads(pipe.data) == {"error": "bot_mismatch"}
    monkeypatch.setattr(transport, "_perform", lambda *args: {"validated": True})
    transport._worker(pipe, "bot", 11, 1, "", 1)  # type: ignore[arg-type]
    assert json.loads(pipe.data) == {"validated": True}


def _stall_dns(*args: object, **kwargs: object) -> None:
    Path(os.environ["CMT_TRANSPORT_TEST_STAGE"]).write_text("dns", encoding="ascii")
    time.sleep(20)


def _dns_worker(
    pipe: Any, operation: str, bot_id: int, chat_id: int, text: str, deadline: float
) -> None:
    socket.getaddrinfo = _stall_dns  # type: ignore[assignment]
    transport._worker(pipe, operation, bot_id, chat_id, text, deadline)


class _StalledHTTP:
    def __init__(self, *args: object, **kwargs: object) -> None:
        pass

    def set_debuglevel(self, level: int) -> None:
        pass

    def request(self, *args: object, **kwargs: object) -> None:
        pass

    def getresponse(self) -> _StalledHTTP:
        return self

    status = 200

    def getheaders(self) -> list[tuple[str, str]]:
        return []

    def read(self, limit: int) -> bytes:
        Path(os.environ["CMT_TRANSPORT_TEST_STAGE"]).write_text("read", encoding="ascii")
        time.sleep(20)
        return b"{}"

    def close(self) -> None:
        pass


class _DripHTTP(_StalledHTTP):
    def read(self, limit: int) -> bytes:
        # A byte arrives well within any individual socket timeout indefinitely.
        Path(os.environ["CMT_TRANSPORT_TEST_STAGE"]).write_text("drip", encoding="ascii")
        for _ in range(1000):
            time.sleep(0.02)
        return b"{}"


def _read_worker(
    pipe: Any, operation: str, bot_id: int, chat_id: int, text: str, deadline: float
) -> None:
    transport.http.client.HTTPSConnection = _StalledHTTP  # type: ignore[misc,assignment]
    transport._worker(pipe, operation, bot_id, chat_id, text, deadline)


def _drip_worker(
    pipe: Any, operation: str, bot_id: int, chat_id: int, text: str, deadline: float
) -> None:
    transport.http.client.HTTPSConnection = _DripHTTP  # type: ignore[misc,assignment]
    transport._worker(pipe, operation, bot_id, chat_id, text, deadline)


def _projection_worker(
    pipe: Any, operation: str, bot_id: int, chat_id: int, text: str, deadline: float
) -> None:
    pipe.send_bytes(b'{"validated":true}')
    pipe.close()


@pytest.mark.parametrize("worker", [_dns_worker, _read_worker, _drip_worker])
def test_real_spawn_hard_deadline(
    monkeypatch: pytest.MonkeyPatch,
    configured: str,
    worker: Callable[..., None],
    tmp_path: Path,
) -> None:
    marker = tmp_path / "worker-stage"
    monkeypatch.setenv("CMT_TRANSPORT_TEST_STAGE", str(marker))
    monkeypatch.setattr(transport, "_worker", worker)
    start = time.monotonic()
    result = transport.TelegramTransport().send(11, 22, "frozen", timeout=2)
    assert result == transport.TransportResult("uncertain", "transport_timeout")
    assert time.monotonic() - start < 5
    assert marker.read_text(encoding="ascii") in {"dns", "read", "drip"}


def test_real_spawn_minimal_ipc(monkeypatch: pytest.MonkeyPatch, configured: str) -> None:
    monkeypatch.setattr(transport, "_worker", _projection_worker)
    transport.TelegramTransport().validate_bot(11, timeout=5)
    transport.TelegramTransport().validate_destination(11, 22, timeout=5)


@pytest.mark.parametrize(
    "field,value",
    [
        ("bot", True),
        ("bot", 0),
        ("bot", 1 << 52),
        ("chat", -1),
        ("chat", "22"),
        ("timeout", True),
        ("timeout", 0),
        ("timeout", 31),
        ("timeout", float("inf")),
        ("timeout", float("nan")),
        ("timeout", "1"),
    ],
)
def test_input_bounds(field: str, value: Any) -> None:
    inputs = {"bot": 11, "chat": 22, "timeout": 15}
    inputs[field] = value
    with pytest.raises(DeliveryError, match="invalid_field"):
        transport.TelegramTransport().send(
            inputs["bot"], inputs["chat"], "text", timeout=inputs["timeout"]
        )


@pytest.mark.parametrize("text", [None, "", "é" * 2049, "\ud800"])
def test_message_bytes_not_rewritten(text: Any, configured: str) -> None:
    with pytest.raises(DeliveryError, match="invalid_field"):
        transport.TelegramTransport().send(11, 22, text)


@pytest.mark.parametrize("value", ["", "123:short", "../invalid", "123:" + "x" * 201])
def test_missing_invalid_configuration(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("CMT_TELEGRAM_BOT_TOKEN", value)
    with pytest.raises(DeliveryError, match="token_configuration"):
        transport.check_configuration()


def test_public_projection_and_errors(monkeypatch: pytest.MonkeyPatch, configured: str) -> None:
    client = transport.TelegramTransport()
    projection: dict[str, object] = {"validated": True}
    monkeypatch.setattr(transport, "_supervise", lambda *args: projection)
    client.validate_bot(11)
    client.validate_destination(11, 22)
    projection.clear()
    with pytest.raises(DeliveryError, match="provider_invalid"):
        client.validate_bot(11)
    with pytest.raises(DeliveryError, match="provider_invalid"):
        client.validate_destination(11, 22)
    projection.update(
        {
            "state": "confirmed",
            "receipt": {
                "message_id": 8,
                "accepted_at": 1700000000,
                "bot_id": 11,
                "chat_id": 22,
            },
        }
    )
    assert client.send(11, 22, "é" * 2048).receipt == transport.Receipt(8, 1700000000, 11, 22)
    for state, category in [
        ("retryable", "provider_rate_limit"),
        ("permanent_failure", "provider_rejection"),
    ]:
        projection.clear()
        projection.update({"state": state, "error_category": category, "retry_after": 2})
        assert client.send(11, 22, "text").state == state
    projection.clear()
    assert client.send(11, 22, "text").state == "uncertain"
    projection.update(
        {
            "state": "confirmed",
            "receipt": {
                "message_id": 8,
                "accepted_at": 1700000000,
                "bot_id": 12,
                "chat_id": 22,
            },
        }
    )
    assert client.send(11, 22, "text").state == "uncertain"

    def fail(*args: object) -> dict[str, object]:
        raise DeliveryError("transport_timeout")

    monkeypatch.setattr(transport, "_supervise", fail)
    assert client.send(11, 22, "text").error_category == "transport_timeout"
    with pytest.raises(DeliveryError, match="transport_timeout"):
        client.validate_bot(11)


@pytest.mark.parametrize(
    "headers,body,accepted",
    [
        ([("Content-Length", "2")], b"{}", True),
        ([("Transfer-Encoding", "chunked")], b"{}", True),
        ([("Content-Length", "3")], b"{}", False),
        ([("Content-Length", "2"), ("Content-Length", "2")], b"{}", False),
        ([("Content-Length", "2"), ("Transfer-Encoding", "chunked")], b"{}", False),
        ([("Transfer-Encoding", "gzip")], b"{}", False),
        ([("Transfer-Encoding", "chunked"), ("Transfer-Encoding", "chunked")], b"{}", False),
        ([("Content-Length", "65537")], b"{}", False),
        ([("Content-Length", "9" * 20)], b"{}", False),
        ([("Content-Length", "-1")], b"{}", False),
        ([("Content-Length", "٢")], b"{}", False),
    ],
)
def test_http_framing(
    monkeypatch: pytest.MonkeyPatch,
    configured: str,
    headers: list[tuple[str, str]],
    body: bytes,
    accepted: bool,
) -> None:
    class FramingHTTP(_StalledHTTP):
        def getheaders(self) -> list[tuple[str, str]]:
            return headers

        def read(self, limit: int) -> bytes:
            return body

    monkeypatch.setattr(transport.http.client, "HTTPSConnection", FramingHTTP)
    if accepted:
        assert transport._request("getMe", {}, time.monotonic() + 1) == (200, body)
    else:
        with pytest.raises(DeliveryError, match="provider_invalid"):
            transport._request("getMe", {}, time.monotonic() + 1)


@pytest.mark.parametrize("failure", ["start", "exit", "empty", "ipc", "category", "unknown"])
def test_supervisor_failures_are_sanitized(
    monkeypatch: pytest.MonkeyPatch,
    configured: str,
    failure: str,
) -> None:
    class Pipe(_Pipe):
        def poll(self) -> bool:
            return failure != "empty"

        def recv_bytes(self, limit: int) -> bytes:
            if failure == "ipc":
                raise OSError(configured)
            return b'{"error":"bot_mismatch"}' if failure == "category" else b'{"error":"unknown"}'

    class Process:
        pid: int | None = None
        exitcode = 1 if failure == "exit" else 0

        def start(self) -> None:
            if failure == "start":
                raise OSError(configured)
            self.pid = 1

        def join(self, timeout: float) -> None:
            pass

        def is_alive(self) -> bool:
            return False

        def close(self) -> None:
            pass

    class Context:
        def Pipe(self, *, duplex: bool) -> tuple[Pipe, Pipe]:
            return Pipe(), Pipe()

        def Process(self, **kwargs: object) -> Process:
            return Process()

    monkeypatch.setattr(transport.multiprocessing, "get_context", lambda method: Context())
    result = transport.TelegramTransport().send(11, 22, "text")
    assert result.state == "uncertain"
    assert configured not in repr(result)
    assert result.error_category == (
        "bot_mismatch" if failure == "category" else "transport_failure"
    )


def test_supervisor_escalates_termination(monkeypatch: pytest.MonkeyPatch, configured: str) -> None:
    events: list[str] = []

    class Process:
        pid = 1
        alive = True
        exitcode = 0

        def start(self) -> None:
            pass

        def join(self, timeout: float) -> None:
            events.append("join")

        def is_alive(self) -> bool:
            return self.alive

        def terminate(self) -> None:
            events.append("terminate")

        def kill(self) -> None:
            events.append("kill")
            self.alive = False

        def close(self) -> None:
            events.append("close")

    class Context:
        def Pipe(self, *, duplex: bool) -> tuple[_Pipe, _Pipe]:
            return _Pipe(), _Pipe()

        def Process(self, **kwargs: object) -> Process:
            return Process()

    monkeypatch.setattr(transport.multiprocessing, "get_context", lambda method: Context())
    result = transport.TelegramTransport().send(11, 22, "text")
    assert result == transport.TransportResult("uncertain", "transport_timeout")
    assert events == ["join", "terminate", "join", "kill", "join", "close"]


def test_local_check_method(configured: str) -> None:
    transport.TelegramTransport().check_configuration()
