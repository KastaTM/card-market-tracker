"""Pure bounded plaintext presentation of frozen intrinsic alert intentions."""

from __future__ import annotations

import json
import unicodedata
from typing import cast

from ..discovery.multi_models import SYNTHETIC_PROFILE
from .errors import OutboxError


def _safe(value: object) -> str:
    if value is None:
        return "null"
    text = str(value)
    result = []
    for char in text:
        # ASCII-escape controls, bidi/format characters, separators and surrogates.
        if not char.isprintable() or unicodedata.category(char).startswith("C"):
            result.append(json.dumps(char, ensure_ascii=True)[1:-1])
        elif char == "\\":
            result.append("\\\\")
        else:
            result.append(char)
    return "".join(result)


def render(intent: dict[str, object]) -> str:
    from .policy import validate_intent

    frozen = validate_intent(intent)
    reference = cast(dict[str, object], frozen["reference"])
    lines = [
        "SYNTHETIC demonstration"
        if frozen["profile"] == SYNTHETIC_PROFILE
        else "Pinned local evidence",
        "Accepted set reference"
        if frozen["status"] == "accepted"
        else "Unaccepted candidate reference",
        "First observed in selected comparison window.",
    ]
    lines.extend(f"{key}: {_safe(reference[key])}" for key in sorted(reference))
    lines.extend(
        f"{key}: {_safe(frozen[key])}"
        for key in (
            "category",
            "cmt_id",
            "current_batch_id",
            "captured_at",
            "first_observed_in_window_at",
            "profile",
            "evidence_level",
            "mode",
            "event_id",
        )
    )
    message = "\n".join(lines)
    if len(message.encode("utf-8")) > 4096:
        raise OutboxError("input_limit")
    return message
