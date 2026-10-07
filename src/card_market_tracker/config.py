"""Small, explicit configuration loader. Values are never included in errors."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

_KEYS = frozenset({"CMT_LOG_LEVEL", "CMT_WORK_DIR"})
_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR"})


class ConfigurationError(ValueError):
    """A configuration field is malformed or unusable."""


@dataclass(frozen=True)
class Config:
    log_level: str
    work_dir: Path


def _read_env_file(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        raise ConfigurationError("env_file: unreadable") from None
    values: dict[str, str] = {}
    for line_number, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ConfigurationError(f"env_file: invalid line {line_number}")
        key, value = line.split("=", 1)
        key = key.strip()
        if key not in _KEYS:
            raise ConfigurationError(f"env_file: unsupported key on line {line_number}")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        values[key] = value
    return values


def load_config(env_file: Path | None = None, environ: Mapping[str, str] | None = None) -> Config:
    """Load defaults, an explicitly selected .env file, then process environment."""
    values = {"CMT_LOG_LEVEL": "INFO", "CMT_WORK_DIR": str(Path.cwd())}
    if env_file is not None:
        values.update(_read_env_file(Path(env_file)))
    source = os.environ if environ is None else environ
    values.update({key: source[key] for key in _KEYS if key in source})

    level = values["CMT_LOG_LEVEL"].strip().upper()
    if level not in _LEVELS:
        raise ConfigurationError("CMT_LOG_LEVEL: invalid")
    raw_dir = values["CMT_WORK_DIR"].strip()
    if not raw_dir or "\x00" in raw_dir:
        raise ConfigurationError("CMT_WORK_DIR: invalid")
    try:
        work_dir = Path(raw_dir).expanduser().resolve()
        if not work_dir.is_dir():
            raise ConfigurationError("CMT_WORK_DIR: not a directory")
    except (OSError, RuntimeError, ValueError):
        raise ConfigurationError("CMT_WORK_DIR: invalid") from None
    return Config(log_level=level, work_dir=work_dir)
