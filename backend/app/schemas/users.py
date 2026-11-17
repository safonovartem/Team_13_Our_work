"""Pydantic-схемы пользователей и правил валидации."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import Field, field_validator, model_validator

from app.schemas.common import APIModel, ResponseModel
from app.validators import (
    strip_optional_text,
    validate_email,
    validate_password_strength,
    validate_username,
)


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"


class UserRead(ResponseModel):
    """Публичное представление пользователя (без хеша пароля)."""

    id: int
    email: str
    username: str
    full_name: str | None = None
    organization: str | None = None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserUpdate(APIModel):
    """Изменение собственного профиля.

    ``role`` и ``is_active`` здесь недоступны: их меняет только администратор
    через ``AdminUserUpdate``.
    """

    email: str | None = Field(default=None, max_length=254)
    username: str | None = Field(default=None, min_length=3, max_length=32)
    full_name: str | None = Field(default=None, max_length=120)
    organization: str | None = Field(default=None, max_length=120)
    current_password: str | None = Field(default=None, min_length=1, max_length=128)
    new_password: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def _validate_email(cls, value: str | None) -> str | None:
        return None if value is None else validate_email(value)

    @field_validator("username")
    @classmethod
    def _validate_username(cls, value: str | None) -> str | None:
        return None if value is None else validate_username(value)

    @field_validator("full_name", "organization")
    @classmethod
    def _normalize_optional_text(cls, value: str | None) -> str | None:
        return strip_optional_text(value)

    @field_validator("new_password")
    @classmethod
    def _validate_new_password(cls, value: str | None) -> str | None:
        return None if value is None else validate_password_strength(value)

    @model_validator(mode="after")
    def _check_password_change(self) -> "UserUpdate":
        if self.new_password is not None and self.current_password is None:
            raise ValueError("Для смены пароля необходимо указать current_password")
        if self.new_password is None and self.current_password is not None:
            raise ValueError("current_password указывается только вместе с new_password")

        for field_name in ("email", "username"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"Поле {field_name} не может быть пустым")
        return self


class AdminUserUpdate(APIModel):
    """Изменение пользователя администратором."""

    email: str | None = Field(default=None, max_length=254)
    username: str | None = Field(default=None, min_length=3, max_length=32)
    full_name: str | None = Field(default=None, max_length=120)
    organization: str | None = Field(default=None, max_length=120)
    role: UserRole | None = None
    is_active: bool | None = None
    new_password: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def _validate_email(cls, value: str | None) -> str | None:
        return None if value is None else validate_email(value)

    @field_validator("username")
    @classmethod
    def _validate_username(cls, value: str | None) -> str | None:
        return None if value is None else validate_username(value)

    @field_validator("full_name", "organization")
    @classmethod
    def _normalize_optional_text(cls, value: str | None) -> str | None:
        return strip_optional_text(value)

    @field_validator("new_password")
    @classmethod
    def _validate_new_password(cls, value: str | None) -> str | None:
        return None if value is None else validate_password_strength(value)

    @model_validator(mode="after")
    def _check_not_empty(self) -> "AdminUserUpdate":
        for field_name in ("email", "username", "role", "is_active"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"Поле {field_name} не может быть пустым")
        return self
