"""Юнит-тесты валидаторов, паролей и JWT (без HTTP)."""

from __future__ import annotations

import pytest

from app.security import (
    TokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.validators import (
    validate_email,
    validate_password_not_personal,
    validate_password_strength,
    validate_username,
)

SECRET = "unit-test-secret-key-0123456789abcdef"


@pytest.mark.parametrize(
    "email",
    [
        "user@example.com",
        "a.b+c@sub.domain.ru",
        "ENGINEER@EXAMPLE.COM",
        "user_name@example.io",
    ],
)
def test_valid_emails(email):
    normalized = validate_email(email)
    assert normalized == email.strip().lower()
    assert "@" in normalized


@pytest.mark.parametrize(
    "email",
    [
        "not-an-email",
        "user@",
        "@example.com",
        "user@example",
        "user@@example.com",
        "user name@example.com",
        "user@.com",
        "",
    ],
)
def test_invalid_emails(email):
    with pytest.raises(ValueError):
        validate_email(email)


@pytest.mark.parametrize("username", ["abc", "a_b-c.d", "User123", "a" * 32])
def test_valid_usernames(username):
    assert validate_username(username) == username


@pytest.mark.parametrize(
    "username",
    ["ab", "a" * 33, "bad name", "user!", "_user", "user_", "юзер", ""],
)
def test_invalid_usernames(username):
    with pytest.raises(ValueError):
        validate_username(username)


def test_password_strength_accepts_good_password():
    assert validate_password_strength("Tank12345") == "Tank12345"


@pytest.mark.parametrize(
    ("password", "message"),
    [
        ("Short1", "не менее 8"),
        ("12345678", "хотя бы одну букву"),
        ("abcdefgh", "хотя бы одну цифру"),
        ("qwerty123", "слишком простой"),
    ],
)
def test_password_strength_rejects_weak(password, message):
    with pytest.raises(ValueError, match=message):
        validate_password_strength(password)


def test_password_must_not_contain_identity():
    with pytest.raises(ValueError, match="имя пользователя"):
        validate_password_not_personal(
            "Engineer2026", username="engineer", email="engineer@example.com"
        )

    assert validate_password_not_personal(
        "Secret2026", username="engineer", email="engineer@example.com"
    )


def test_password_hash_roundtrip():
    password_hash = hash_password("Tank12345")
    assert password_hash != "Tank12345"
    assert password_hash.startswith("pbkdf2_sha256$")
    assert verify_password("Tank12345", password_hash)
    assert not verify_password("Tank12346", password_hash)
    assert not verify_password("Tank12345", "garbage")
    assert not verify_password("Tank12345", "md5$1$aa$bb")


def test_hash_is_salted():
    assert hash_password("Tank12345") != hash_password("Tank12345")


def test_token_roundtrip():
    token, expires_in = create_access_token(42, secret_key=SECRET, ttl_minutes=10)
    assert expires_in == 600
    assert decode_access_token(token, secret_key=SECRET) == 42


def test_expired_token():
    token, _ = create_access_token(1, secret_key=SECRET, ttl_minutes=-1)
    with pytest.raises(TokenError, match="истёк"):
        decode_access_token(token, secret_key=SECRET)


def test_token_with_wrong_secret():
    token, _ = create_access_token(1, secret_key=SECRET, ttl_minutes=10)
    with pytest.raises(TokenError, match="Некорректный"):
        decode_access_token(token, secret_key=SECRET + "-other")


def test_tampered_token():
    token, _ = create_access_token(1, secret_key=SECRET, ttl_minutes=10)
    with pytest.raises(TokenError):
        decode_access_token(token + "x", secret_key=SECRET)
