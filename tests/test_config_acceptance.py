"""Independent acceptance tests for P0 configuration boundaries."""

from pathlib import Path

import pytest

from card_market_tracker.config import ConfigurationError, load_config


def test_defaults_do_not_load_implicit_dotenv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("CMT_LOG_LEVEL=ERROR\n", encoding="utf-8")

    config = load_config(environ={})

    assert config.log_level == "INFO"
    assert config.work_dir == tmp_path


def test_explicit_dotenv_overrides_defaults_and_environment_wins(
    tmp_path: Path,
) -> None:
    dotenv = tmp_path / "selected.env"
    dotenv.write_text(f"CMT_LOG_LEVEL=WARNING\nCMT_WORK_DIR={tmp_path}\n", encoding="utf-8")

    file_config = load_config(env_file=dotenv, environ={})
    environment_config = load_config(env_file=dotenv, environ={"CMT_LOG_LEVEL": "ERROR"})

    assert file_config.log_level == "WARNING"
    assert file_config.work_dir == tmp_path
    assert environment_config.log_level == "ERROR"
    assert environment_config.work_dir == tmp_path


@pytest.mark.parametrize(
    ("environment", "field"),
    [
        ({"CMT_LOG_LEVEL": "invalid-secret-value"}, "CMT_LOG_LEVEL"),
        ({"CMT_WORK_DIR": "missing-secret-directory"}, "CMT_WORK_DIR"),
    ],
)
def test_invalid_environment_reports_field_without_value(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    environment: dict[str, str],
    field: str,
) -> None:
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ConfigurationError) as caught:
        load_config(environ=environment)

    assert field in str(caught.value)
    assert "secret" not in str(caught.value)


def test_invalid_dotenv_value_is_not_echoed(tmp_path: Path) -> None:
    dotenv = tmp_path / "selected.env"
    dotenv.write_text("CMT_LOG_LEVEL=invalid-secret-value\n", encoding="utf-8")

    with pytest.raises(ConfigurationError) as caught:
        load_config(env_file=dotenv, environ={})

    assert "CMT_LOG_LEVEL" in str(caught.value)
    assert "invalid-secret-value" not in str(caught.value)


def test_environment_override_replaces_invalid_lower_priority_value(tmp_path: Path) -> None:
    dotenv = tmp_path / "selected.env"
    dotenv.write_text("CMT_LOG_LEVEL=invalid-secret-value\n", encoding="utf-8")

    config = load_config(env_file=dotenv, environ={"CMT_LOG_LEVEL": "DEBUG"})

    assert config.log_level == "DEBUG"


def test_missing_explicit_dotenv_fails_without_echoing_path(tmp_path: Path) -> None:
    missing = tmp_path / "secret-missing.env"

    with pytest.raises(ConfigurationError) as caught:
        load_config(env_file=missing, environ={})

    assert "secret-missing.env" not in str(caught.value)


def test_malformed_dotenv_line_does_not_echo_value(tmp_path: Path) -> None:
    dotenv = tmp_path / "selected.env"
    dotenv.write_text("malformed-secret-value\n", encoding="utf-8")

    with pytest.raises(ConfigurationError) as caught:
        load_config(env_file=dotenv, environ={})

    assert "malformed-secret-value" not in str(caught.value)
