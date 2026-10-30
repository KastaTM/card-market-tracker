"""Narrow lazy reuse of the accepted P8b transport and result types.

Importing this module never imports Telegram, reads a token or opens a socket.
The application calls these functions only after local unconfirmed preflight.
"""

from __future__ import annotations

from typing import Protocol

from .models import MAX_ID

_UNCERTAIN = frozenset(
    {
        "token_configuration",
        "bot_mismatch",
        "destination_mismatch",
        "transport_timeout",
        "transport_failure",
        "provider_invalid",
    }
)


class Transport(Protocol):
    def check_configuration(self) -> None: ...

    def validate_destination(self, bot_id: int, chat_id: int, *, timeout: float = 15.0) -> None: ...

    def validate_bot(self, bot_id: int, *, timeout: float = 15.0) -> None: ...

    def send(
        self, bot_id: int, chat_id: int, message_text: str, *, timeout: float = 15.0
    ) -> object: ...


def new_transport() -> Transport:
    """Instantiate only on an authorized application remote-operation path."""
    from ..telegram_delivery.transport import TelegramTransport

    return TelegramTransport()


def _integer(value: object, maximum: int) -> bool:
    return type(value) is int and 1 <= value <= maximum


def normalize_result(result: object, bot_id: int, chat_id: int) -> dict[str, object]:
    """Reject forged shapes and inconsistent native outcomes conservatively."""
    from ..telegram_delivery.transport import Receipt, TransportResult

    invalid: dict[str, object] = {
        "state": "uncertain",
        "error_category": "provider_invalid",
        "retry_after": None,
        "receipt": None,
    }
    if type(result) is not TransportResult:
        return invalid
    try:
        state, category, retry, receipt = (
            result.state,
            result.error_category,
            result.retry_after,
            result.receipt,
        )
        if type(state) is not str or category is not None and type(category) is not str:
            return invalid
        if state == "confirmed":
            if category is not None or retry is not None or type(receipt) is not Receipt:
                return invalid
            if not (
                _integer(receipt.message_id, (1 << 63) - 1)
                and _integer(receipt.accepted_at, 253402300799)
                and _integer(receipt.bot_id, MAX_ID)
                and _integer(receipt.chat_id, MAX_ID)
                and receipt.bot_id == bot_id
                and receipt.chat_id == chat_id
            ):
                return invalid
            return {
                "state": "confirmed",
                "error_category": None,
                "retry_after": None,
                "receipt": {
                    "message_id": receipt.message_id,
                    "accepted_at": receipt.accepted_at,
                    "bot_id": receipt.bot_id,
                    "chat_id": receipt.chat_id,
                },
            }
        if receipt is not None:
            return invalid
        if state == "retryable" and category == "provider_rate_limit":
            if not _integer(retry, 86400):
                return invalid
            return {
                "state": "retryable",
                "error_category": category,
                "retry_after": retry,
                "receipt": None,
            }
        if retry is not None:
            return invalid
        if state == "permanent_failure" and category == "provider_rejection":
            return {
                "state": state,
                "error_category": category,
                "retry_after": None,
                "receipt": None,
            }
        if state == "uncertain" and category in _UNCERTAIN:
            return {
                "state": state,
                "error_category": category,
                "retry_after": None,
                "receipt": None,
            }
    except (AttributeError, TypeError, ValueError):
        return invalid
    return invalid
