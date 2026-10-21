"""Bounded official Telegram transport; no persistence, retries or raw diagnostics.

The spawned worker alone constructs authenticated URLs and reads credentials.
The supervisor receives only a small validated projection, never HTTP bodies.
"""

from __future__ import annotations

import http.client
import json
import math
import multiprocessing
import os
import re
import ssl
import time
from dataclasses import dataclass, field
from multiprocessing.connection import Connection
from typing import Literal, cast

from .errors import DeliveryError

_MAX_BODY = 65536
_MAX_ID = (1 << 52) - 1
_TOKEN = re.compile(r"[0-9]{1,20}:[A-Za-z0-9_-]{20,200}\Z", re.ASCII)
_CATEGORIES = frozenset(
    {
        "token_configuration",
        "bot_mismatch",
        "destination_mismatch",
        "transport_timeout",
        "transport_failure",
        "provider_rejection",
        "provider_rate_limit",
        "provider_invalid",
    }
)
State = Literal["confirmed", "retryable", "permanent_failure", "uncertain"]


@dataclass(frozen=True)
class Receipt:
    message_id: int = field(repr=False)
    accepted_at: int
    bot_id: int = field(repr=False)
    chat_id: int = field(repr=False)


@dataclass(frozen=True)
class TransportResult:
    state: State
    error_category: str | None = None
    retry_after: int | None = None
    receipt: Receipt | None = None


def check_configuration() -> None:
    """Validate the local environment without returning or retaining its secret."""
    if _TOKEN.fullmatch(os.environ.get("CMT_TELEGRAM_BOT_TOKEN", "")) is None:
        raise DeliveryError("token_configuration") from None


def _integer(value: object, maximum: int = _MAX_ID) -> int:
    if type(value) is not int or not 1 <= value <= maximum:
        raise DeliveryError("provider_invalid")
    return value


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise DeliveryError("provider_invalid")
    return cast(dict[str, object], value)


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DeliveryError("provider_invalid")
        result[key] = value
    return result


def _constant(_: str) -> object:
    raise DeliveryError("provider_invalid")


def _tree(value: object, depth: int = 0) -> None:
    if depth > 16:
        raise DeliveryError("provider_invalid")
    if isinstance(value, float) and not math.isfinite(value):
        raise DeliveryError("provider_invalid")
    if isinstance(value, str):
        value.encode("utf-8", "strict")
    elif isinstance(value, dict):
        for key, item in value.items():
            _tree(key, depth + 1)
            _tree(item, depth + 1)
    elif isinstance(value, list):
        for item in value:
            _tree(item, depth + 1)


def _decode(body: bytes) -> dict[str, object]:
    if len(body) > _MAX_BODY:
        raise DeliveryError("provider_invalid")
    try:
        value: object = json.loads(
            body.decode("utf-8", "strict"), object_pairs_hook=_pairs, parse_constant=_constant
        )
        _tree(value)
        return _object(value)
    except (ValueError, UnicodeError, RecursionError):
        raise DeliveryError("provider_invalid") from None


def _request(method: str, payload: dict[str, object], deadline: float) -> tuple[int, bytes]:
    # HTTPSConnection does not consult proxy environment variables or follow redirects.
    # Each stage is socket-bounded; the parent additionally bounds DNS and slow drips.
    if method not in {"getMe", "getChat", "sendMessage"}:
        raise DeliveryError("provider_invalid")
    check_configuration()
    token = os.environ["CMT_TELEGRAM_BOT_TOKEN"]
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise DeliveryError("transport_timeout")
    connection = http.client.HTTPSConnection(
        "api.telegram.org", 443, timeout=min(5.0, remaining), context=ssl.create_default_context()
    )
    connection.set_debuglevel(0)
    try:
        body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
        connection.request(
            "POST",
            f"/bot{token}/{method}",
            body=body,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json",
            },
        )
        response = connection.getresponse()
        lengths = [
            value.strip()
            for name, value in response.getheaders()
            if name.lower() == "content-length"
        ]
        transfers = [
            value.strip().lower()
            for name, value in response.getheaders()
            if name.lower() == "transfer-encoding"
        ]
        if (
            len(lengths) > 1
            or len(transfers) > 1
            or (lengths and transfers)
            or (transfers and transfers != ["chunked"])
            or (
                lengths
                and (
                    not lengths[0].isascii()
                    or not lengths[0].isdigit()
                    or len(lengths[0]) > 10
                    or int(lengths[0]) > _MAX_BODY
                )
            )
        ):
            raise DeliveryError("provider_invalid")
        # One extra byte detects oversized bodies; never drain arbitrary provider data.
        received = response.read(_MAX_BODY + 1)
        if lengths and len(received) != int(lengths[0]):
            raise DeliveryError("provider_invalid")
        return response.status, received
    finally:
        connection.close()


def _success(status: int, body: bytes) -> dict[str, object]:
    value = _decode(body)
    if status != 200 or value.get("ok") is not True or "error_code" in value:
        raise DeliveryError("provider_invalid")
    if "parameters" in value:
        raise DeliveryError("provider_invalid")
    return _object(value.get("result"))


def _bot(status: int, body: bytes, bot_id: int) -> None:
    result = _success(status, body)
    if _integer(result.get("id")) != bot_id or result.get("is_bot") is not True:
        raise DeliveryError("bot_mismatch")


def _receipt(status: int, body: bytes, bot_id: int, chat_id: int, text: str) -> TransportResult:
    value = _decode(body)
    if status == 200:
        result = _success(status, body)
        chat = _object(result.get("chat"))
        sender = _object(result.get("from"))
        if (
            _integer(chat.get("id")) != chat_id
            or chat.get("type") != "private"
            or _integer(sender.get("id")) != bot_id
            or sender.get("is_bot") is not True
            or result.get("text") != text
            or any(
                key in result
                for key in (
                    "sender_chat",
                    "sender_business_bot",
                    "business_connection_id",
                    "guest_query_id",
                    "ephemeral_message_id",
                )
            )
        ):
            raise DeliveryError("provider_invalid")
        return TransportResult(
            "confirmed",
            receipt=Receipt(
                _integer(result.get("message_id"), (1 << 63) - 1),
                _integer(result.get("date"), 253402300799),
                bot_id,
                chat_id,
            ),
        )
    description = value.get("description")
    rejection = (
        value.get("ok") is False
        and type(value.get("error_code")) is int
        and value.get("error_code") == status
        and "result" not in value
        and isinstance(description, str)
        and 0 < len(description.encode("utf-8")) <= 4096
    )
    if rejection and status == 429:
        parameters = _object(value.get("parameters"))
        if "migrate_to_chat_id" in parameters:
            raise DeliveryError("provider_invalid")
        delay = _integer(parameters.get("retry_after"), 86400)
        return TransportResult("retryable", "provider_rate_limit", retry_after=delay)
    if rejection and 400 <= status < 500 and status not in {408, 409, 425, 429}:
        if "parameters" in value:
            raise DeliveryError("provider_invalid")
        return TransportResult("permanent_failure", "provider_rejection")
    return TransportResult("uncertain", "provider_invalid")


def _perform(
    operation: str, bot_id: int, chat_id: int, text: str, deadline: float
) -> dict[str, object]:
    if operation in {"bot", "destination"}:
        _bot(*_request("getMe", {}, deadline), bot_id)
        if operation == "destination":
            chat = _success(*_request("getChat", {"chat_id": chat_id}, deadline))
            if _integer(chat.get("id")) != chat_id or chat.get("type") != "private":
                raise DeliveryError("destination_mismatch")
        return {"validated": True}
    result = _receipt(
        *_request(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": text,
                "link_preview_options": {"is_disabled": True},
            },
            deadline,
        ),
        bot_id,
        chat_id,
        text,
    )
    projection: dict[str, object] = {
        "state": result.state,
        "error_category": result.error_category,
        "retry_after": result.retry_after,
    }
    if result.receipt is not None:
        projection["receipt"] = {
            "message_id": result.receipt.message_id,
            "accepted_at": result.receipt.accepted_at,
            "bot_id": result.receipt.bot_id,
            "chat_id": result.receipt.chat_id,
        }
    return projection


def _worker(
    pipe: Connection, operation: str, bot_id: int, chat_id: int, text: str, deadline: float
) -> None:
    # Nothing from provider exceptions or response bodies crosses IPC or is printed.
    try:
        try:
            result = _perform(operation, bot_id, chat_id, text, deadline)
        except DeliveryError as error:
            category = error.category if error.category in _CATEGORIES else "transport_failure"
            result = {"error": category}
        except TimeoutError:
            result = {"error": "transport_timeout"}
        except BaseException:
            result = {"error": "transport_failure"}
        pipe.send_bytes(json.dumps(result, allow_nan=False).encode("ascii"))
    except BaseException:
        pass
    finally:
        pipe.close()


def _supervise(
    operation: str, bot_id: int, chat_id: int, text: str, timeout: float
) -> dict[str, object]:
    context = multiprocessing.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    deadline = time.monotonic() + timeout
    process = context.Process(
        target=_worker,
        args=(sender, operation, bot_id, chat_id, text, deadline),
        daemon=True,
    )
    try:
        process.start()
        sender.close()
        # Output is <2KiB, below pipe capacity: join before recv prevents partial IPC reads
        # from defeating the deadline. No worker can spawn descendants (daemon=True).
        process.join(max(0.0, deadline - time.monotonic()))
        if process.is_alive() or time.monotonic() >= deadline:
            raise DeliveryError("transport_timeout")
        if process.exitcode != 0 or not receiver.poll():
            raise DeliveryError("transport_failure")
        projection = _decode(receiver.recv_bytes(2048))
        category = projection.get("error")
        if category is not None:
            raise DeliveryError(category if category in _CATEGORIES else "transport_failure")
        return projection
    except DeliveryError:
        raise
    except BaseException:
        raise DeliveryError("transport_failure") from None
    finally:
        sender.close()
        receiver.close()
        if process.pid is not None:
            if process.is_alive():
                process.terminate()
                process.join(0.1)
            if process.is_alive():
                process.kill()
                process.join(0.1)
            if not process.is_alive():
                process.close()


def _inputs(bot_id: int, chat_id: int, timeout: float) -> None:
    if (
        type(bot_id) is not int
        or not 1 <= bot_id <= _MAX_ID
        or type(chat_id) is not int
        or not 1 <= chat_id <= _MAX_ID
        or type(timeout) not in {int, float}
        or not math.isfinite(timeout)
        or not 0 < timeout <= 30
    ):
        raise DeliveryError("invalid_field")


class TelegramTransport:
    """One bounded explicit operation per call; never retries or persists."""

    @staticmethod
    def check_configuration() -> None:
        check_configuration()

    def validate_bot(self, bot_id: int, *, timeout: float = 15) -> None:
        _inputs(bot_id, 1, timeout)
        check_configuration()
        projection = _supervise("bot", bot_id, 1, "", timeout)
        if projection != {"validated": True}:
            raise DeliveryError("provider_invalid")

    def validate_destination(self, bot_id: int, chat_id: int, *, timeout: float = 15) -> None:
        _inputs(bot_id, chat_id, timeout)
        check_configuration()
        projection = _supervise("destination", bot_id, chat_id, "", timeout)
        if projection != {"validated": True}:
            raise DeliveryError("provider_invalid")

    def send(
        self, bot_id: int, chat_id: int, message_text: str, *, timeout: float = 15
    ) -> TransportResult:
        _inputs(bot_id, chat_id, timeout)
        if not isinstance(message_text, str):
            raise DeliveryError("invalid_field")
        try:
            if not 1 <= len(message_text.encode("utf-8", "strict")) <= 4096:
                raise DeliveryError("invalid_field")
        except UnicodeError:
            raise DeliveryError("invalid_field") from None
        check_configuration()
        try:
            value = _supervise("send", bot_id, chat_id, message_text, timeout)
            state = value.get("state")
            if state == "confirmed":
                receipt = _object(value.get("receipt"))
                if receipt.get("bot_id") != bot_id or receipt.get("chat_id") != chat_id:
                    raise DeliveryError("provider_invalid")
                return TransportResult(
                    "confirmed",
                    receipt=Receipt(
                        _integer(receipt.get("message_id"), (1 << 63) - 1),
                        _integer(receipt.get("accepted_at"), 253402300799),
                        _integer(receipt.get("bot_id")),
                        _integer(receipt.get("chat_id")),
                    ),
                )
            category = value.get("error_category")
            if state == "retryable" and category == "provider_rate_limit":
                return TransportResult(
                    "retryable", category, retry_after=_integer(value.get("retry_after"), 86400)
                )
            if state == "permanent_failure" and category == "provider_rejection":
                return TransportResult("permanent_failure", category)
            return TransportResult("uncertain", "provider_invalid")
        except DeliveryError as error:
            return TransportResult("uncertain", error.category)
