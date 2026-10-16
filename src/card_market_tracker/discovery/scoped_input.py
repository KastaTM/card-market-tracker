"""Strict bounded request v2, including independently constructed Python values."""

from pathlib import Path

from ..catalog.manifest import language_value
from ..catalog.validation import (
    CatalogError,
    array_value,
    object_value,
    read_json,
    string_value,
    token_value,
    uuid_value,
)
from .models import DiscoveryContext
from .scoped_errors import ScopedDiscoveryError
from .scoped_models import ScopedDiscoveryRequest, ScopedSelection
from .validation import MAX_HISTORY, bounded_value


def _selection(value: object) -> ScopedSelection:
    selection = object_value(value)
    if set(selection) != {"batch_id", "selector"}:
        raise CatalogError("invalid_shape")
    return ScopedSelection(
        uuid_value(selection["batch_id"]), string_value(selection["selector"], 256)
    )


def parse_request(document: object) -> ScopedDiscoveryRequest:
    try:
        bounded_value(document)
        wrapper = object_value(document)
        if set(wrapper) != {"version", "context", "current", "history"}:
            raise CatalogError("invalid_shape")
        if type(wrapper["version"]) is not int or wrapper["version"] != 2:
            raise CatalogError("unsupported_version")
        context = object_value(wrapper["context"])
        if set(context) != {"namespace", "kind", "language"}:
            raise CatalogError("invalid_shape")
        kind = context["kind"]
        if kind not in ("set", "card", "sealed"):
            raise CatalogError("invalid_field")
        current = _selection(wrapper["current"])
        history = tuple(_selection(item) for item in array_value(wrapper["history"], MAX_HISTORY))
        ids = [current.batch_id, *(item.batch_id for item in history)]
        if len(set(ids)) != len(ids):
            raise CatalogError("duplicate_id")
        return ScopedDiscoveryRequest(
            2,
            DiscoveryContext(
                token_value(context["namespace"]), kind, language_value(context["language"])
            ),
            current,
            tuple(sorted(history, key=lambda item: item.batch_id)),
        )
    except CatalogError as error:
        raise ScopedDiscoveryError(error.category) from None
    except (TypeError, ValueError, UnicodeError, RecursionError):
        raise ScopedDiscoveryError("invalid_json") from None


def validate_request(request: object) -> ScopedDiscoveryRequest:
    if not isinstance(request, ScopedDiscoveryRequest):
        raise ScopedDiscoveryError("invalid_shape")
    try:
        if (
            not isinstance(request.context, DiscoveryContext)
            or not isinstance(request.current, ScopedSelection)
            or not isinstance(request.history, tuple)
            or any(not isinstance(item, ScopedSelection) for item in request.history)
        ):
            raise ScopedDiscoveryError("invalid_shape")
        if len(request.history) > MAX_HISTORY:
            raise ScopedDiscoveryError("input_limit")
        return parse_request(request.to_dict())
    except (AttributeError, TypeError, ValueError) as error:
        if isinstance(error, ScopedDiscoveryError):
            raise
        raise ScopedDiscoveryError("invalid_shape") from None


def read_request(path: Path) -> ScopedDiscoveryRequest:
    try:
        return parse_request(read_json(path))
    except CatalogError as error:
        raise ScopedDiscoveryError(error.category) from None
