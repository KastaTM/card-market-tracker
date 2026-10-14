"""Engineering-only bounded, non-executing parser for two pinned TS objects.

All AST data is transient. Public output contains only the approved projection
and UTF-8 byte spans of approved fields. No upstream import is resolved.
"""

import re
from dataclasses import dataclass
from pathlib import PurePosixPath

from ..catalog.validation import CatalogError, date_value, string_value, token_value
from .errors import BundleError

EXTRACTOR_VERSION = "pinned_ts_literals_v1"
SET_PATH = "data/Sword & Shield/Darkness Ablaze.ts"
CARD_PATH = "data/Sword & Shield/Darkness Ablaze/136.ts"
MAX_SOURCE_BYTES = 65_536
MAX_TOKENS = 10_000
MAX_DEPTH = 16


@dataclass(frozen=True)
class _Token:
    kind: str
    value: str
    start: int
    end: int


@dataclass(frozen=True)
class _Reference:
    name: str


@dataclass(frozen=True)
class FieldSpan:
    path: str
    field: str
    start: int
    end: int
    transformation: str


@dataclass(frozen=True)
class Extraction:
    projection: tuple[dict[str, object], ...]
    fields: tuple[FieldSpan, ...]


def _tokens(raw: bytes) -> tuple[_Token, ...]:
    if type(raw) is not bytes:
        raise BundleError("invalid_shape")
    if len(raw) > MAX_SOURCE_BYTES:
        raise BundleError("input_limit")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise BundleError("invalid_encoding") from None
    offsets = [0]
    for char in text:
        offsets.append(offsets[-1] + len(char.encode("utf-8")))
    result: list[_Token] = []
    position = 0
    while position < len(text):
        start = position
        char = text[position]
        if char.isspace():
            position += 1
            continue
        if text.startswith("//", position):
            end = text.find("\n", position)
            position = len(text) if end < 0 else end + 1
            continue
        if text.startswith("/*", position):
            end = text.find("*/", position + 2)
            if end < 0:
                raise BundleError("unsupported_syntax")
            position = end + 2
            continue
        if char in "{}[]:,;=":
            kind, value = char, char
            position += 1
        elif char in "\"'":
            quote = char
            position += 1
            pieces: list[str] = []
            while position < len(text) and text[position] != quote:
                char = text[position]
                if ord(char) < 32:
                    raise BundleError("unsupported_syntax")
                if char == "\\":
                    position += 1
                    if position >= len(text):
                        raise BundleError("unsupported_syntax")
                    escaped = text[position]
                    escapes = {"n": "\n", "r": "\r", "t": "\t", "b": "\b", "f": "\f"}
                    if escaped in escapes:
                        char = escapes[escaped]
                    elif escaped in "\\\"'":
                        char = escaped
                    elif escaped == "u":
                        digits = text[position + 1 : position + 5]
                        if re.fullmatch(r"[0-9a-fA-F]{4}", digits) is None:
                            raise BundleError("unsupported_syntax")
                        char = chr(int(digits, 16))
                        position += 4
                    else:
                        raise BundleError("unsupported_syntax")
                if 0xD800 <= ord(char) <= 0xDFFF:
                    raise BundleError("invalid_encoding")
                pieces.append(char)
                position += 1
            if position == len(text):
                raise BundleError("unsupported_syntax")
            position += 1
            kind, value = "string", "".join(pieces)
            if len(value) > 4096:
                raise BundleError("input_limit")
        else:
            match = re.match(r"[A-Za-z_$][A-Za-z0-9_$]*|[0-9]+", text[position:])
            if match is None:
                raise BundleError("unsupported_syntax")
            value = match.group()
            kind = "number" if value.isdigit() else "identifier"
            position += len(value)
        result.append(_Token(kind, value, offsets[start], offsets[position]))
        if len(result) > MAX_TOKENS:
            raise BundleError("input_limit")
    result.append(_Token("eof", "", len(raw), len(raw)))
    return tuple(result)


class _Parser:
    def __init__(self, raw: bytes, kind: str) -> None:
        self.tokens = _tokens(raw)
        self.position = 0
        self.spans: dict[tuple[str, ...], tuple[int, int]] = {}
        self.kind = kind
        self.import_name = "serie" if kind == "set" else "Set"

    def take(self, value: str | None = None, kind: str | None = None) -> _Token:
        token = self.tokens[self.position]
        if kind is None and value is not None:
            kind = value if value in {"{", "}", "[", "]", ":", ",", ";", "="} else "identifier"
        if (value is not None and token.value != value) or (
            kind is not None and token.kind != kind
        ):
            raise BundleError("unsupported_syntax")
        self.position += 1
        return token

    def optional(self, value: str) -> bool:
        token = self.tokens[self.position]
        if token.value == value and token.kind == value:
            self.position += 1
            return True
        return False

    def parse(self) -> dict[str, object]:
        type_name = "Set" if self.kind == "set" else "Card"
        interface = "../../interfaces" if self.kind == "set" else "../../../interfaces"
        parent = "../Sword & Shield" if self.kind == "set" else "../Darkness Ablaze"
        self.take("import")
        self.take("{")
        self.take(type_name)
        self.take("}")
        self.take("from")
        if self.take(kind="string").value != interface:
            raise BundleError("invalid_import")
        self.optional(";")
        self.take("import")
        self.take(self.import_name)
        self.take("from")
        imported_parent = self.take(kind="string")
        if imported_parent.value != parent:
            raise BundleError("invalid_import")
        self.spans[("$parent_import",)] = (imported_parent.start, imported_parent.end)
        self.optional(";")
        self.take("const")
        variable = self.take(kind="identifier").value
        self.take(":")
        self.take(type_name)
        self.take("=")
        root = self.value((), 0)
        self.optional(";")
        self.take("export")
        self.take("default")
        self.take(variable)
        self.optional(";")
        self.take(kind="eof")
        if not isinstance(root, dict):
            raise BundleError("invalid_shape")
        return root

    def value(self, path: tuple[str, ...], depth: int) -> object:
        if depth > MAX_DEPTH:
            raise BundleError("input_limit")
        token = self.tokens[self.position]
        start = token.start
        result: object
        if token.kind == "{":
            self.take("{")
            mapping: dict[str, object] = {}
            if not self.optional("}"):
                while True:
                    key = self.take()
                    if key.kind not in {"identifier", "string"}:
                        raise BundleError("unsupported_syntax")
                    if key.value in mapping:
                        raise BundleError("duplicate_field")
                    self.take(":")
                    mapping[key.value] = self.value((*path, key.value), depth + 1)
                    if self.optional("}"):
                        break
                    self.take(",")
                    if self.optional("}"):
                        break
            result = mapping
        elif token.kind == "[":
            self.take("[")
            items: list[object] = []
            if not self.optional("]"):
                while True:
                    items.append(self.value((*path, str(len(items))), depth + 1))
                    if self.optional("]"):
                        break
                    self.take(",")
                    if self.optional("]"):
                        break
            result = items
        elif token.kind == "string":
            result = self.take().value
        elif token.kind == "number":
            if len(token.value) > 10:
                raise BundleError("input_limit")
            result = int(self.take().value)
        elif token.kind == "identifier" and token.value in {"true", "false", "null"}:
            result = {"true": True, "false": False, "null": None}[self.take().value]
        elif (
            token.kind == "identifier"
            and token.value == self.import_name
            and path == ("serie" if self.kind == "set" else "set",)
        ):
            result = _Reference(self.take().value)
        else:
            raise BundleError("unsupported_syntax")
        self.spans[path] = (start, self.tokens[self.position - 1].end)
        return result


def project_sources(set_raw: bytes, card_raw: bytes, *, card_path: str = CARD_PATH) -> Extraction:
    """Extract only exact ES/EN metadata; synthetic paths permit number tests.

    This engineering transform does not confer admission authority. Runtime
    authority is exclusively the reviewed bundle lock, not this parser output.
    """
    if not isinstance(card_path, str) or not card_path.startswith(SET_PATH[:-3] + "/"):
        raise BundleError("invalid_selection")
    card_file = PurePosixPath(card_path)
    if str(card_file.parent) != SET_PATH[:-3] or card_file.suffix != ".ts":
        raise BundleError("invalid_selection")
    set_parser, card_parser = _Parser(set_raw, "set"), _Parser(card_raw, "card")
    source_set, source_card = set_parser.parse(), card_parser.parse()
    try:
        set_id = token_value(source_set.get("id"))
        number = string_value(card_file.stem, 64)
        card_id = token_value(f"{set_id}-{number}")
        release = date_value(source_set.get("releaseDate"))
        if "releaseDate" not in source_set:
            raise BundleError("missing_field")
        set_names, card_names = source_set.get("name"), source_card.get("name")
        if not isinstance(set_names, dict) or not isinstance(card_names, dict):
            raise BundleError("missing_translation")
        if source_card.get("set") != _Reference("Set"):
            raise BundleError("invalid_relation")
        projection: list[dict[str, object]] = []
        for kind, names in (("set", set_names), ("card", card_names)):
            for language in ("es", "en"):
                if language not in names:
                    raise BundleError("missing_translation")
                projection.append(
                    {
                        "kind": kind,
                        "language": language,
                        "external_id": set_id if kind == "set" else card_id,
                        "name": string_value(names[language], 256),
                        "set_external_id": None if kind == "set" else set_id,
                        "card_number": None if kind == "set" else number,
                        "release_date": release if kind == "set" else None,
                    }
                )
    except CatalogError:
        raise BundleError("invalid_field") from None
    fields: list[FieldSpan] = []
    for parser, file_path, paths in (
        (set_parser, SET_PATH, (("id",), ("name", "es"), ("name", "en"), ("releaseDate",))),
        (
            card_parser,
            card_path,
            (("name", "es"), ("name", "en"), ("set",), ("$parent_import",)),
        ),
    ):
        for path in paths:
            start, end = parser.spans[path]
            fields.append(FieldSpan(file_path, ".".join(path), start, end, "exact_literal"))
    return Extraction(tuple(projection), tuple(fields))
