"""Схемы регистрации и аутентификации."""

from __future__ import annotations

from pydantic import Field, field_validator, model_validator

from app.schemas.common import APIModel
from app.schemas.users import UserRead
from app.validators import (
    strip_optional_text,
    validate_email,
    validate_password_not_personal,
    validate_password_strength,
    validate_username,
)


class UserRegister(APIModel):
    """Данные для создания пользователя.

    Роль при самостоятельной регистрации не принимается: новый пользователь
    всегда получает роль ``user``.
    """

    email: str = Field(
        min_length=5,
        max_length=254,
        description="Email, используется для входа",
        examples=["engineer@example.com"],
    )
    username: str = Field(
        min_length=3,
        max_length=32,
        description="Уникальное имя пользователя",
        examples=["engineer"],
    )
    password: str = Field(
        min_length=8,
        max_length=128,
        description="Пароль: минимум 8 символов, хотя бы одна буква и одна цифра",
    )
    full_name: str | None = Field(
        default=None, max_length=120, description="ФИО", examples=["Иван Петров"]
    )
    organization: str | None = Field(
        default=None, max_length=120, examples=["ООО «АралИнжиниринг»"]
    )

    @field_validator("email")
    @classmethod
    def _validate_email(cls, value: str) -> str:
        return validate_email(value)

    @field_validator("username")
    @classmethod
    def _validate_username(cls, value: str) -> str:
        return validate_username(value)

    @field_validator("password")
    @classmethod
    def _validate_password(cls, value: str) -> str:
        return validate_password_strength(value)

    @field_validator("full_name", "organization")
    @classmethod
    def _normalize_optional_text(cls, value: str | None) -> str | None:
        return strip_optional_text(value)

    @model_validator(mode="after")
    def _password_must_not_contain_identity(self) -> "UserRegister":
        validate_password_not_personal(
            self.password, email=self.email, username=self.username
        )
        return self


class LoginRequest(APIModel):
    """Вход по email или username."""

    login: str = Field(
        min_length=3,
        max_length=254,
        description="Email или имя пользователя",
        examples=["engineer@example.com"],
    )
    password: str = Field(min_length=1, max_length=128)

    @field_validator("login")
    @classmethod
    def _normalize_login(cls, value: str) -> str:
        return value.strip()


class TokenResponse(APIModel):
    """Ответ на успешный вход."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Время жизни токена в секундах")
    user: UserRead
