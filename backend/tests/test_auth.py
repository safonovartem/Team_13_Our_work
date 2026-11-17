"""Тесты регистрации, аутентификации и валидации пользователя."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.factory import create_app
from app.security import create_access_token
from tests.utils import DEFAULT_USER, bearer, login, register


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_creates_user(client):
    response = register(client)
    assert response.status_code == 201, response.text

    body = response.json()
    assert body["email"] == DEFAULT_USER["email"]
    assert body["username"] == DEFAULT_USER["username"]
    assert body["role"] == "user"
    assert body["is_active"] is True
    assert body["full_name"] == DEFAULT_USER["full_name"]
    assert "password" not in body
    assert "hashed_password" not in body
    assert body["created_at"] == body["updated_at"]


def test_register_normalizes_email(client):
    response = register(client, email="  Engineer@Example.COM  ")
    assert response.status_code == 201, response.text
    assert response.json()["email"] == "engineer@example.com"


def test_register_duplicate_email_is_case_insensitive(client, user):
    response = register(client, email="ENGINEER@example.com", username="other")
    assert response.status_code == 409
    assert response.json()["field"] == "email"


def test_register_duplicate_username_is_case_insensitive(client, user):
    response = register(client, email="other@example.com", username="ENGINEER")
    assert response.status_code == 409
    assert response.json()["field"] == "username"


@pytest.mark.parametrize(
    "email",
    [
        "not-an-email",
        "user@",
        "@example.com",
        "user@example",
        "user@@example.com",
        "user name@example.com",
        "",
    ],
)
def test_register_rejects_invalid_email(client, email):
    response = register(client, email=email)
    assert response.status_code == 422, response.text


@pytest.mark.parametrize(
    "password",
    [
        "Ab1",  # короче 8 символов
        "12345678",  # нет букв
        "abcdefghij",  # нет цифр
        "qwerty123",  # слишком простой
    ],
)
def test_register_rejects_weak_password(client, password):
    response = register(client, password=password)
    assert response.status_code == 422, response.text


@pytest.mark.parametrize("username", ["ab", "bad name", "_user", "user_", "юзер"])
def test_register_rejects_invalid_username(client, username):
    response = register(client, username=username)
    assert response.status_code == 422, response.text


def test_register_rejects_password_with_username(client):
    response = register(client, username="tankman", password="Tankman12345")
    assert response.status_code == 422
    assert "имя пользователя" in response.text


def test_register_rejects_extra_fields(client):
    """Роль нельзя выдать себе при регистрации."""
    response = register(client, role="admin")
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "extra_forbidden"


def test_login_by_email(client, user):
    response = login(client, DEFAULT_USER["email"], DEFAULT_USER["password"])
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["expires_in"] == 30 * 60
    assert body["user"]["id"] == user["id"]


def test_login_by_username(client, user):
    response = login(client, DEFAULT_USER["username"], DEFAULT_USER["password"])
    assert response.status_code == 200
    assert response.json()["user"]["email"] == DEFAULT_USER["email"]


def test_login_wrong_password(client, user):
    response = login(client, DEFAULT_USER["email"], "WrongPass123")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_login_unknown_user(client):
    response = login(client, "nobody@example.com", "Someone12345")
    assert response.status_code == 401


def test_login_inactive_user(client, app, user):
    with app.state.database.connect() as connection:
        connection.execute(
            "UPDATE users SET is_active = 0 WHERE id = ?", (user["id"],)
        )

    response = login(client, DEFAULT_USER["email"], DEFAULT_USER["password"])
    assert response.status_code == 403


def test_me_requires_token(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_me_returns_current_user(client, headers, user):
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == user["id"]


def test_me_rejects_invalid_token(client):
    response = client.get("/api/auth/me", headers=bearer("not-a-token"))
    assert response.status_code == 401


def test_me_rejects_expired_token(client, settings, user):
    token, _ = create_access_token(
        user["id"],
        secret_key=settings.secret_key,
        ttl_minutes=-1,
    )
    response = client.get("/api/auth/me", headers=bearer(token))
    assert response.status_code == 401
    assert "истёк" in response.json()["detail"]


def test_me_rejects_token_with_other_secret(client, user):
    token, _ = create_access_token(
        user["id"], secret_key="another-test-secret-key-0123456789", ttl_minutes=30
    )
    response = client.get("/api/auth/me", headers=bearer(token))
    assert response.status_code == 401


def test_token_rejected_after_deactivation(client, app, headers, user):
    with app.state.database.connect() as connection:
        connection.execute(
            "UPDATE users SET is_active = 0 WHERE id = ?", (user["id"],)
        )

    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Учётная запись деактивирована"


def test_openapi_contains_projects(client):
    schema = client.get("/openapi.json").json()
    assert "/api/projects" in schema["paths"]
    assert "/api/auth/login" in schema["paths"]


def test_bootstrap_admin_is_created(tmp_path):
    settings = Settings(
        database_path=tmp_path / "bootstrap.db",
        secret_key="bootstrap-secret-key-0123456789abcdef",
        bootstrap_admin_email="root@example.com",
        bootstrap_admin_password="Root2026Pass",
    )

    with TestClient(create_app(settings)) as client:
        response = login(client, "root@example.com", "Root2026Pass")
        assert response.status_code == 200, response.text
        assert response.json()["user"]["role"] == "admin"


def test_bootstrap_admin_requires_email_and_password(tmp_path):
    settings = Settings(
        database_path=tmp_path / "bootstrap-broken.db",
        bootstrap_admin_email="root@example.com",
    )

    with pytest.raises(ValueError):
        create_app(settings)
