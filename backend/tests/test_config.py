"""Тесты конфигурации (переменные окружения)."""

from __future__ import annotations

from app.config import DEFAULT_SECRET_KEY, Settings


def test_settings_have_safe_defaults():
    settings = Settings()
    assert settings.secret_key == DEFAULT_SECRET_KEY
    assert isinstance(settings.secret_key, str)
    assert settings.access_token_ttl_minutes == 720
    assert settings.jwt_algorithm == "HS256"
    assert settings.cors_origins


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("TSP_SECRET_KEY", "x" * 40)
    monkeypatch.setenv("TSP_DATABASE_PATH", "C:/tmp/custom.db")
    monkeypatch.setenv("TSP_ACCESS_TOKEN_TTL_MINUTES", "15")
    monkeypatch.setenv("TSP_JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("TSP_CORS_ORIGINS", "http://a.example, http://b.example")

    settings = Settings.from_env()

    assert settings.secret_key == "x" * 40
    assert str(settings.database_path).endswith("custom.db")
    assert settings.access_token_ttl_minutes == 15
    assert settings.cors_origins == ("http://a.example", "http://b.example")


def test_settings_from_env_defaults(monkeypatch):
    for variable in (
        "TSP_DATABASE_PATH",
        "TSP_SECRET_KEY",
        "TSP_ACCESS_TOKEN_TTL_MINUTES",
        "TSP_JWT_ALGORITHM",
        "TSP_CORS_ORIGINS",
        "TSP_ADMIN_EMAIL",
        "TSP_ADMIN_PASSWORD",
    ):
        monkeypatch.delenv(variable, raising=False)

    settings = Settings.from_env()

    assert isinstance(settings.secret_key, str)
    assert settings.secret_key == DEFAULT_SECRET_KEY
    assert settings.access_token_ttl_minutes == 720
    assert settings.bootstrap_admin_email is None
    assert settings.bootstrap_admin_password is None
