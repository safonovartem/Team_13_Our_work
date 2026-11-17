"""Управление пользователями: профиль и административные операции."""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Query, Response, status

from app.deps import get_connection, get_current_user, require_admin
from app.errors import BadRequestError, ConflictError, NotFoundError
from app.repositories import users as users_repo
from app.schemas.common import Page
from app.schemas.users import AdminUserUpdate, UserRead, UserUpdate
from app.security import hash_password, verify_password
from app.validators import validate_password_not_personal

router = APIRouter(prefix="/users", tags=["Пользователи"])

_PROFILE_FIELDS = ("email", "username", "full_name", "organization")


def _check_unique(
    connection: sqlite3.Connection,
    *,
    user_id: int,
    email: str | None = None,
    username: str | None = None,
) -> None:
    """Проверяет уникальность email/username среди других пользователей."""
    if email is not None:
        existing = users_repo.get_by_email(connection, email)
        if existing is not None and existing["id"] != user_id:
            raise ConflictError(
                "Пользователь с таким email уже зарегистрирован", field="email"
            )
    if username is not None:
        existing = users_repo.get_by_username(connection, username)
        if existing is not None and existing["id"] != user_id:
            raise ConflictError(
                "Пользователь с таким именем уже зарегистрирован", field="username"
            )


@router.get(
    "/me",
    response_model=UserRead,
    summary="Профиль текущего пользователя",
)
def get_me(user: dict = Depends(get_current_user)) -> dict:
    return user


@router.patch(
    "/me",
    response_model=UserRead,
    summary="Изменить профиль (email, username, ФИО, организация, пароль)",
    responses={
        400: {"description": "Неверный текущий пароль"},
        409: {"description": "Email или username уже заняты"},
    },
)
def update_me(
    payload: UserUpdate,
    user: dict = Depends(get_current_user),
    connection: sqlite3.Connection = Depends(get_connection),
) -> dict:
    changes: dict[str, object] = {}
    for field_name in _PROFILE_FIELDS:
        if field_name in payload.model_fields_set:
            changes[field_name] = getattr(payload, field_name)

    _check_unique(
        connection,
        user_id=user["id"],
        email=changes.get("email"),  # type: ignore[arg-type]
        username=changes.get("username"),  # type: ignore[arg-type]
    )

    if payload.new_password is not None:
        if not verify_password(
            payload.current_password or "", user["hashed_password"]
        ):
            raise BadRequestError(
                "Неверный текущий пароль", code="invalid_password"
            )
        validate_password_not_personal(
            payload.new_password,
            email=str(changes.get("email") or user["email"]),
            username=str(changes.get("username") or user["username"]),
        )
        changes["hashed_password"] = hash_password(payload.new_password)

    updated = users_repo.update_user(connection, user["id"], changes)
    if updated is None:  # pragma: no cover - пользователь был получен выше
        raise NotFoundError("Пользователь не найден")
    return updated


@router.get(
    "",
    response_model=Page[UserRead],
    summary="Список пользователей (только администратор)",
    responses={403: {"description": "Недостаточно прав"}},
)
def list_users(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    _: dict = Depends(require_admin),
    connection: sqlite3.Connection = Depends(get_connection),
) -> dict:
    users = users_repo.list_users(connection, limit=limit, offset=offset)
    return {
        "items": users,
        "total": users_repo.count_users(connection),
        "limit": limit,
        "offset": offset,
    }


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Пользователь по id (только администратор)",
    responses={404: {"description": "Пользователь не найден"}},
)
def get_user(
    user_id: int,
    _: dict = Depends(require_admin),
    connection: sqlite3.Connection = Depends(get_connection),
) -> dict:
    user = users_repo.get_by_id(connection, user_id)
    if user is None:
        raise NotFoundError("Пользователь не найден")
    return user


@router.patch(
    "/{user_id}",
    response_model=UserRead,
    summary="Изменить пользователя (только администратор)",
    responses={
        403: {"description": "Недостаточно прав"},
        404: {"description": "Пользователь не найден"},
        409: {"description": "Конфликт уникальности или бизнес-правило"},
    },
)
def update_user(
    user_id: int,
    payload: AdminUserUpdate,
    current_user: dict = Depends(require_admin),
    connection: sqlite3.Connection = Depends(get_connection),
) -> dict:
    target = users_repo.get_by_id(connection, user_id)
    if target is None:
        raise NotFoundError("Пользователь не найден")

    changes: dict[str, object] = {}
    for field_name in _PROFILE_FIELDS:
        if field_name in payload.model_fields_set:
            changes[field_name] = getattr(payload, field_name)

    if payload.role is not None:
        if (
            user_id == current_user["id"]
            and payload.role.value != "admin"
        ):
            raise ConflictError("Нельзя лишить себя прав администратора")
        changes["role"] = payload.role.value

    if payload.is_active is not None:
        if user_id == current_user["id"] and not payload.is_active:
            raise ConflictError("Нельзя деактивировать собственную учётную запись")
        changes["is_active"] = payload.is_active

    _check_unique(
        connection,
        user_id=user_id,
        email=changes.get("email"),  # type: ignore[arg-type]
        username=changes.get("username"),  # type: ignore[arg-type]
    )

    if payload.new_password is not None:
        validate_password_not_personal(
            payload.new_password,
            email=str(changes.get("email") or target["email"]),
            username=str(changes.get("username") or target["username"]),
        )
        changes["hashed_password"] = hash_password(payload.new_password)

    updated = users_repo.update_user(connection, user_id, changes)
    assert updated is not None
    return updated


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Деактивировать пользователя (только администратор)",
    description=(
        "Учётная запись не удаляется физически, чтобы сохранить историю "
        "проектов; пользователь теряет возможность входа."
    ),
    responses={409: {"description": "Попытка деактивировать себя"}},
)
def deactivate_user(
    user_id: int,
    current_user: dict = Depends(require_admin),
    connection: sqlite3.Connection = Depends(get_connection),
) -> Response:
    if user_id == current_user["id"]:
        raise ConflictError("Нельзя деактивировать собственную учётную запись")

    target = users_repo.get_by_id(connection, user_id)
    if target is None:
        raise NotFoundError("Пользователь не найден")

    users_repo.update_user(connection, user_id, {"is_active": False})
    return Response(status_code=status.HTTP_204_NO_CONTENT)
