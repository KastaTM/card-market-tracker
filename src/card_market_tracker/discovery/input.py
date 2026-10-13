"""Strict bounded local Discovery v1 requests, including the Python boundary."""

from pathlib import Path

from ..catalog.manifest import language_value
from ..catalog.validation import (
    CatalogError,
    array_value,
    object_value,
    read_json,
    token_value,
    uuid_value,
    version_one,
)
from .errors import DiscoveryError
from .models import DiscoveryContext, DiscoveryRequest
from .validation import MAX_HISTORY, bounded_value


def parse_request(document: object) -> DiscoveryRequest:
    try:
        bounded_value(document)
        wrapper = object_value(document)
        if set(wrapper) != {"version", "current_batch_id", "history_batch_ids", "context"}:
            raise CatalogError("invalid_shape")
        version_one(wrapper["version"])
        current = uuid_value(wrapper["current_batch_id"])
        history = tuple(
            uuid_value(value) for value in array_value(wrapper["history_batch_ids"], MAX_HISTORY)
        )
        if len(set(history)) != len(history) or current in history:
            raise CatalogError("duplicate_id")
        context = object_value(wrapper["context"])
        if set(context) != {"namespace", "kind", "language"}:
            raise CatalogError("invalid_shape")
        kind = context["kind"]
        if kind not in ("set", "card", "sealed"):
            raise CatalogError("invalid_field")
        return DiscoveryRequest(
            1,
            current,
            tuple(sorted(history)),
            DiscoveryContext(
                token_value(context["namespace"]), kind, language_value(context["language"])
            ),
        )
    except CatalogError as error:
        raise DiscoveryError(error.category) from None
    except (ValueError, UnicodeError, RecursionError):
        raise DiscoveryError("invalid_json") from None


def validate_request(request: object) -> DiscoveryRequest:
    if not isinstance(request, DiscoveryRequest):
        raise DiscoveryError("invalid_shape")
    try:
        if not isinstance(request.history_batch_ids, tuple) or not isinstance(
            request.context, DiscoveryContext
        ):
            raise DiscoveryError("invalid_shape")
        if len(request.history_batch_ids) > MAX_HISTORY:
            raise DiscoveryError("input_limit")
        return parse_request(request.to_dict())
    except (AttributeError, TypeError, ValueError) as error:
        if isinstance(error, DiscoveryError):
            raise
        raise DiscoveryError("invalid_shape") from None


def read_request(path: Path) -> DiscoveryRequest:
    try:
        return parse_request(read_json(path))
    except CatalogError as error:
        raise DiscoveryError(error.category) from None
