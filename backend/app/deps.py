"""Зависимости FastAPI: подключение к БД, текущий пользователь, права."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings
from app.database import Database
from app.repositories import users as users_repo
from app.security import TokenError, decode_access_token

bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="BearerAuth",
    description="JWT access token, полученный в POST /api/auth/login",
)


def get_database(request: Request) -> Database:
    return request.app.state.database


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_connection(request: Request) -> Iterator[sqlite3.Connection]:
    """Открывает соединение на один запрос и управляет транзакцией."""
    database: Database = request.app.state.database
    connection = database.connect()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _unauthorized(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    connection: sqlite3.Connection = Depends(get_connection),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Проверяет токен и возвращает активного пользователя."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized("Требуется авторизация")

    try:
        user_id = decode_access_token(
            credentials.credentials,
            secret_key=settings.secret_key,
            algorithm=settings.jwt_algorithm,
        )
    except TokenError as exc:
        raise _unauthorized(str(exc)) from exc

    user = users_repo.get_by_id(connection, user_id)
    if user is None:
        raise _unauthorized("Пользователь не найден")
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Учётная запись деактивирована",
        )
    return user


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Доступ только для администраторов."""
    if user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав: требуется роль администратора",
        )
    return user
