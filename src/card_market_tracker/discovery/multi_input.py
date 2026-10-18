"""Strict v3 entrypoint; no fallback from v1/v2 or caller-supplied profiles."""

from pathlib import Path

from ..catalog.validation import CatalogError, object_value, read_json
from .multi_models import PROFILES, MultiRevisionRequest
from .scoped_errors import ScopedDiscoveryError
from .scoped_input import parse_request as parse_scoped
from .validation import bounded_value


def parse_request(document: object) -> MultiRevisionRequest:
    try:
        bounded_value(document)
        wrapper = object_value(document)
        if set(wrapper) != {"version", "profile", "context", "current", "history"}:
            raise CatalogError("invalid_shape")
        if type(wrapper["version"]) is not int or wrapper["version"] != 3:
            raise CatalogError("unsupported_version")
        profile = wrapper["profile"]
        if type(profile) is not str or profile not in PROFILES:
            raise CatalogError("invalid_field")
        scoped = parse_scoped(
            {
                key: (2 if key == "version" else value)
                for key, value in wrapper.items()
                if key != "profile"
            }
        )
        return MultiRevisionRequest(3, profile, scoped.context, scoped.current, scoped.history)
    except CatalogError as error:
        raise ScopedDiscoveryError(error.category) from None


def validate_request(request: object) -> MultiRevisionRequest:
    if type(request) is not MultiRevisionRequest:
        raise ScopedDiscoveryError("invalid_shape")
    try:
        from .scoped_input import validate_request as validate_scoped

        validate_scoped(request.scoped_request())
        return parse_request(request.to_dict())
    except (AttributeError, TypeError, ValueError) as error:
        if isinstance(error, ScopedDiscoveryError):
            raise
        raise ScopedDiscoveryError("invalid_shape") from None


def read_request(path: Path) -> MultiRevisionRequest:
    try:
        return parse_request(read_json(path))
    except CatalogError as error:
        raise ScopedDiscoveryError(error.category) from None
