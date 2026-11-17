"""Сборка FastAPI-приложения.

Фабрика вынесена отдельно от ``app.main``, чтобы тесты могли поднимать
приложение с временной базой данных, не создавая файл рабочей БД.
"""

from __future__ import annotations

import re
import sqlite3

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.config import Settings, get_settings
from app.core.exceptions import DomainRangeError
from app.database import Database
from app.errors import DomainError
from app.repositories import users as users_repo
from app.routers import (
    auth,
    catalog,
    charts,
    calculations,
    project_calculations,
    projects,
    users,
)
from app.security import hash_password
from app.validators import validate_email, validate_password_strength

API_PREFIX = "/api"

DESCRIPTION = """
Бэкенд системы **Tank Safety Platform**.

Реализованы:
* регистрация, аутентификация (JWT) и валидация пользователей;
* проекты пользователя и история версий исходных данных;
* валидация исходных параметров (объект, жидкость, окружающая среда)
  согласно ТЗ;
* расчёты на базе вычислительного ядра ``app.core`` (ветка
  ``feature/backend-calculations``) и история расчётов проекта;
* справочник типоразмеров РВС и эндпоинты графиков в формате Chart.js
  (``ChartBlock`` / ``ChartDataset`` из ``feature/main-page``).

Публичные эндпоинты ``/api/calculations``, ``/api/charts`` и ``/api/catalog``
не требуют авторизации; история расчётов доступна владельцу проекта.
"""


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()

    database = Database(app_settings.database_path)
    database.init_schema()

    app = FastAPI(
        title="Tank Safety Platform API",
        version=__version__,
        description=DESCRIPTION.strip(),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    app.state.settings = app_settings
    app.state.database = database

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(app_settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _register_error_handlers(app)

    app.include_router(auth.router, prefix=API_PREFIX)
    app.include_router(users.router, prefix=API_PREFIX)
    app.include_router(projects.router, prefix=API_PREFIX)
    app.include_router(project_calculations.router, prefix=API_PREFIX)
    app.include_router(calculations.router, prefix=API_PREFIX)
    app.include_router(charts.router, prefix=API_PREFIX)
    app.include_router(catalog.router, prefix=API_PREFIX)

    @app.get("/health", tags=["Служебные"], summary="Проверка работоспособности")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get("/", tags=["Служебные"], summary="Сведения о сервисе")
    def root() -> dict[str, str]:
        return {
            "service": "Tank Safety Platform API",
            "version": __version__,
            "docs": "/docs",
            "api": API_PREFIX,
        }

    _ensure_bootstrap_admin(app_settings, database)
    return app


def _register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        content: dict[str, object] = {"detail": exc.message, "code": exc.code}
        if exc.field is not None:
            content["field"] = exc.field
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(DomainRangeError)
    async def domain_range_error_handler(
        request: Request, exc: DomainRangeError
    ) -> JSONResponse:
        """Ошибки границ применимости формул — как ошибки валидации (422)."""
        return JSONResponse(
            status_code=422,  # ошибка валидации входных параметров
            content={"detail": str(exc), "code": "domain_range_error"},
        )


def _ensure_bootstrap_admin(settings: Settings, database: Database) -> None:
    """Создаёт администратора из переменных окружения (если он ещё не создан)."""
    email = settings.bootstrap_admin_email
    password = settings.bootstrap_admin_password
    if email is None and password is None:
        return
    if email is None or password is None:
        raise ValueError(
            "TSP_ADMIN_EMAIL и TSP_ADMIN_PASSWORD должны быть заданы вместе"
        )

    email = validate_email(email)
    validate_password_strength(password)

    with database.connect() as connection:
        if users_repo.get_by_email(connection, email) is not None:
            return

        users_repo.create_user(
            connection,
            email=email,
            username=_unique_username(connection, email),
            password_hash=hash_password(password),
            full_name="Администратор",
            role="admin",
        )


def _unique_username(connection: sqlite3.Connection, email: str) -> str:
    base = re.sub(r"[^A-Za-z0-9_.-]", "", email.split("@", 1)[0])
    base = base.strip("._-") or "admin"
    base = base[:24] or "admin"
    if len(base) < 3:
        base = f"{base}admin"

    username = base
    suffix = 1
    while users_repo.get_by_username(connection, username) is not None:
        suffix += 1
        username = f"{base}{suffix}"
    return username
