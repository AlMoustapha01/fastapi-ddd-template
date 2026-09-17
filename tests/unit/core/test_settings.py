"""Settings are read from environment variables and an optional `.env` file."""

from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError

from core.infrastructure.settings import (
    DatabaseSettings,
    Environment,
    LogLevel,
    Settings,
)

VARIABLES = (
    "APP__NAME",
    "APP__ENVIRONMENT",
    "APP__DOCS_ENABLED",
    "DATABASE__HOST",
    "DATABASE__PORT",
    "DATABASE__PASSWORD",
    "CORS__ALLOW_ORIGINS",
    "LOG__LEVEL",
)


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    for name in VARIABLES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)


def test_reads_nested_values_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE__PASSWORD", "secret")
    monkeypatch.setenv("DATABASE__PORT", "6543")
    monkeypatch.setenv("CORS__ALLOW_ORIGINS", '["http://localhost:3000"]')
    monkeypatch.setenv("LOG__LEVEL", "DEBUG")

    settings = Settings()

    assert settings.database.port == 6543
    assert settings.database.password.get_secret_value() == "secret"
    assert settings.cors.allow_origins == ["http://localhost:3000"]
    assert settings.log.level is LogLevel.DEBUG


def test_applies_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE__PASSWORD", "secret")

    settings = Settings()

    assert settings.app.environment is Environment.LOCAL
    assert settings.app.docs_enabled is True
    assert settings.database.host == "localhost"
    assert settings.database.name == "app"
    assert settings.cors.allow_origins == []
    assert settings.log.level is LogLevel.INFO


def test_database_password_is_required() -> None:
    with pytest.raises(ValidationError):
        Settings()


def test_reads_dotenv_file_from_working_directory(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text(
        "DATABASE__PASSWORD=from-dotenv\nAPP__NAME=Demo\n", encoding="utf-8"
    )

    settings = Settings()

    assert settings.database.password.get_secret_value() == "from-dotenv"
    assert settings.app.name == "Demo"


def test_database_url_is_built_from_parts() -> None:
    database = DatabaseSettings(
        host="db", port=5433, user="user", password=SecretStr("p@ss"), name="demo"
    )

    url = database.url

    assert url.drivername == "postgresql+psycopg"
    assert (url.host, url.port, url.username, url.database) == (
        "db",
        5433,
        "user",
        "demo",
    )
    assert url.password == database.password.get_secret_value()
    assert "p@ss" not in str(url)
