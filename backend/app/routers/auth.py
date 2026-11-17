"""Регистрация, вход и сведения о текущем пользователе."""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import Settings
from app.deps import get_connection, get_current_user, get_settings
from app.errors import ConflictError
from app.repositories import users as users_repo
from app.schemas.auth import LoginRequest, TokenResponse, UserRegister
from app.schemas.users import UserRead
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Аутентификация"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать пользователя",
    responses={409: {"description": "Email или username уже заняты"}},
)
def register(
    payload: UserRegister,
    connection: sqlite3.Connection = Depends(get_connection),
) -> dict:
    """Регистрирует пользователя с ролью ``user``.

    Пароль хешируется (PBKDF2-SHA256), проверяются уникальность email и
    username, сложность пароля и корректность email.
    """
    if users_repo.get_by_email(connection, payload.email) is not None:
        raise ConflictError(
            "Пользователь с таким email уже зарегистрирован", field="email"
        )
    if users_repo.get_by_username(connection, payload.username) is not None:
        raise ConflictError(
            "Пользователь с таким именем уже зарегистрирован", field="username"
        )

    return users_repo.create_user(
        connection,
        email=payload.email,
        username=payload.username,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        organization=payload.organization,
        role="user",
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Войти и получить JWT",
    responses={
        401: {"description": "Неверный логин или пароль"},
        403: {"description": "Учётная запись деактивирована"},
    },
)
def login(
    payload: LoginRequest,
    connection: sqlite3.Connection = Depends(get_connection),
    settings: Settings = Depends(get_settings),
) -> dict:
    user = users_repo.find_by_login(connection, payload.login)
    if user is None or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Учётная запись деактивирована",
        )

    token, expires_in = create_access_token(
        user["id"],
        secret_key=settings.secret_key,
        ttl_minutes=settings.access_token_ttl_minutes,
        algorithm=settings.jwt_algorithm,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user": UserRead.model_validate(user),
    }


@router.get(
    "/me",
    response_model=UserRead,
    summary="Текущий пользователь",
    responses={401: {"description": "Требуется авторизация"}},
)
def me(user: dict = Depends(get_current_user)) -> dict:
    return user
