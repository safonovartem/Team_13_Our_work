"""Хеширование паролей и JWT-токены.

Пароли хранятся как PBKDF2-HMAC-SHA256 (стандартная библиотека, без внешних
криптобиблиотек). Access-токены — обычные JWT (HS256).
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import timedelta

import jwt

from app.utils import utcnow

PBKDF2_ALGORITHM = "pbkdf2_sha256"
PBKDF2_ITERATIONS = 260_000
SALT_BYTES = 16


class TokenError(Exception):
    """Токен отсутствует, просрочен или подписан неверным ключом."""


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return f"{PBKDF2_ALGORITHM}${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = password_hash.split("$")
        if algorithm != PBKDF2_ALGORITHM:
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        iterations_count = int(iterations)
    except (ValueError, TypeError):
        return False

    candidate = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations_count
    )
    return hmac.compare_digest(candidate, expected)


def create_access_token(
    user_id: int,
    *,
    secret_key: str,
    ttl_minutes: int,
    algorithm: str = "HS256",
) -> tuple[str, int]:
    """Возвращает пару (токен, время жизни в секундах)."""
    now = utcnow()
    expires_delta = timedelta(minutes=ttl_minutes)
    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    return token, max(int(expires_delta.total_seconds()), 0)


def decode_access_token(
    token: str,
    *,
    secret_key: str,
    algorithm: str = "HS256",
) -> int:
    """Проверяет токен и возвращает идентификатор пользователя."""
    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[algorithm],
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenError("Срок действия токена истёк") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenError("Некорректный токен") from exc

    if payload.get("type") != "access":
        raise TokenError("Некорректный тип токена")

    try:
        return int(payload["sub"])
    except (KeyError, TypeError, ValueError) as exc:
        raise TokenError("Некорректный токен") from exc
