"""Настройки приложения.

Все параметры читаются из переменных окружения (см. README.md), поэтому
приложение можно запускать как локально, так и в контейнере без изменения кода.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "tank_safety.db"

DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
)

DEFAULT_SECRET_KEY = "dev-secret-change-me-please-set-TSP_SECRET_KEY"


@dataclass(frozen=True, slots=True)
class Settings:
    """Конфигурация приложения."""

    database_path: Path = DEFAULT_DATABASE_PATH
    secret_key: str = DEFAULT_SECRET_KEY
    access_token_ttl_minutes: int = 720
    jwt_algorithm: str = "HS256"
    cors_origins: tuple[str, ...] = DEFAULT_CORS_ORIGINS
    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        """Собирает настройки из переменных окружения."""
        return cls(
            database_path=Path(
                os.getenv("TSP_DATABASE_PATH", str(DEFAULT_DATABASE_PATH))
            ).expanduser(),
            secret_key=os.getenv("TSP_SECRET_KEY", DEFAULT_SECRET_KEY),
            access_token_ttl_minutes=int(
                os.getenv("TSP_ACCESS_TOKEN_TTL_MINUTES", "720")
            ),
            jwt_algorithm=os.getenv("TSP_JWT_ALGORITHM", "HS256"),
            cors_origins=_read_origins(
                os.getenv("TSP_CORS_ORIGINS"), DEFAULT_CORS_ORIGINS
            ),
            bootstrap_admin_email=_empty_to_none(os.getenv("TSP_ADMIN_EMAIL")),
            bootstrap_admin_password=_empty_to_none(os.getenv("TSP_ADMIN_PASSWORD")),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Настройки по умолчанию для production-запуска (uvicorn app.main:app)."""
    return Settings.from_env()


def _empty_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _read_origins(value: str | None, default: tuple[str, ...]) -> tuple[str, ...]:
    if value is None:
        return default
    origins = tuple(part.strip() for part in value.split(",") if part.strip())
    return origins or default
