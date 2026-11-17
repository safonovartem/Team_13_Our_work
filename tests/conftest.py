"""Фикстуры pytest: изолированное приложение и временная БД на каждый тест."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.factory import create_app
from app.repositories import users as users_repo
from app.security import hash_password

from tests.utils import ADMIN_USER, auth_headers, register


@pytest.fixture()
def settings(tmp_path) -> Settings:
    return Settings(
        database_path=tmp_path / "test.db",
        secret_key="test-secret-key-0123456789-abcdef",
        access_token_ttl_minutes=30,
        cors_origins=(),
    )


@pytest.fixture()
def app(settings):
    return create_app(settings)


@pytest.fixture()
def client(app):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def user(client) -> dict:
    response = register(client)
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture()
def headers(client, user) -> dict[str, str]:
    return auth_headers(client)


@pytest.fixture()
def admin_headers(client, app) -> dict[str, str]:
    with app.state.database.connect() as connection:
        users_repo.create_user(
            connection,
            email=ADMIN_USER["email"],
            username=ADMIN_USER["username"],
            password_hash=hash_password(ADMIN_USER["password"]),
            full_name=ADMIN_USER["full_name"],
            role="admin",
        )
    return auth_headers(
        client, email=ADMIN_USER["email"], password=ADMIN_USER["password"]
    )


@pytest.fixture()
def project(client, headers) -> dict:
    from tests.utils import valid_input

    response = client.post(
        "/api/projects",
        headers=headers,
        json={"name": "Резервуарный парк №1", "input_data": valid_input()},
    )
    assert response.status_code == 201, response.text
    return response.json()
