"""Валидаторы пользовательских данных.

Правила вынесены в отдельный модуль, чтобы их можно было использовать и в
Pydantic-схемах, и в роутерах (например, при смене email/username).
"""

from __future__ import annotations

import re

EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+"
    r"@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{1,30}[A-Za-z0-9]$")

COMMON_PASSWORDS = frozenset(
    {
        "12345678",
        "123456789",
        "password",
        "password1",
        "password123",
        "qwerty123",
        "qwertyuiop",
        "admin123",
        "welcome1",
        "letmein1",
        "iloveyou",
        "trustno1",
        "1234567890",
        "qazwsx123",
        "tank1234",
    }
)


def normalize_email(value: str) -> str:
    return value.strip().lower()


def validate_email(value: str) -> str:
    """Проверяет и нормализует email."""
    email = normalize_email(value)
    if len(email) > 254 or not EMAIL_PATTERN.fullmatch(email):
        raise ValueError("Некорректный email")
    local_part, domain = email.rsplit("@", 1)
    if not local_part or not domain or ".." in email:
        raise ValueError("Некорректный email")
    return email


def validate_username(value: str) -> str:
    """Проверяет имя пользователя (латиница, цифры, ``.``, ``-``, ``_``)."""
    username = value.strip()
    if not USERNAME_PATTERN.fullmatch(username):
        raise ValueError(
            "Имя пользователя должно содержать от 3 до 32 символов: латинские "
            "буквы, цифры, точку, дефис или подчёркивание, начинаться и "
            "заканчиваться буквой или цифрой"
        )
    return username


def validate_password_strength(password: str) -> str:
    """Минимальные требования к паролю.

    Длина проверяется также на уровне Pydantic-поля, здесь собраны
    содержательные правила.
    """
    if len(password) < 8:
        raise ValueError("Пароль должен содержать не менее 8 символов")
    if len(password) > 128:
        raise ValueError("Пароль должен содержать не более 128 символов")
    if not any(char.isalpha() for char in password):
        raise ValueError("Пароль должен содержать хотя бы одну букву")
    if not any(char.isdigit() for char in password):
        raise ValueError("Пароль должен содержать хотя бы одну цифру")
    if password.lower() in COMMON_PASSWORDS:
        raise ValueError("Пароль слишком простой, выберите другой")
    return password


def validate_password_not_personal(
    password: str,
    *,
    email: str | None = None,
    username: str | None = None,
) -> str:
    """Запрещает пароль, содержащий email или имя пользователя."""
    lowered = password.lower()
    candidates = []
    if username:
        candidates.append(username.strip().lower())
    if email:
        candidates.append(email.split("@", 1)[0].strip().lower())
    for candidate in candidates:
        if len(candidate) >= 3 and candidate in lowered:
            raise ValueError("Пароль не должен содержать имя пользователя или email")
    return password


def strip_required_text(value: str, *, field_name: str = "Значение") -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{field_name} не может быть пустым")
    return value


def strip_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None
