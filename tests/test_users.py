"""Тесты профиля и административного управления пользователями."""

from __future__ import annotations

from tests.utils import DEFAULT_USER, SECOND_USER, auth_headers, login, register


def test_get_me(client, headers, user):
    response = client.get("/api/users/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["username"] == user["username"]


def test_update_profile(client, headers):
    response = client.patch(
        "/api/users/me",
        headers=headers,
        json={"full_name": "  Иван Иванович  ", "organization": "Новая организация"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["full_name"] == "Иван Иванович"
    assert body["organization"] == "Новая организация"
    assert body["updated_at"] >= body["created_at"]


def test_update_profile_can_clear_optional_fields(client, headers):
    response = client.patch(
        "/api/users/me", headers=headers, json={"full_name": None}
    )
    assert response.status_code == 200
    assert response.json()["full_name"] is None


def test_update_email_changes_login(client, headers):
    response = client.patch(
        "/api/users/me", headers=headers, json={"email": "new@example.com"}
    )
    assert response.status_code == 200, response.text
    assert response.json()["email"] == "new@example.com"

    assert login(client, "new@example.com", DEFAULT_USER["password"]).status_code == 200
    assert login(client, DEFAULT_USER["email"], DEFAULT_USER["password"]).status_code == 401


def test_update_email_conflict(client, user):
    register(client, **SECOND_USER)
    second_headers = auth_headers(
        client, email=SECOND_USER["email"], password=SECOND_USER["password"]
    )

    response = client.patch(
        "/api/users/me", headers=second_headers, json={"email": DEFAULT_USER["email"]}
    )
    assert response.status_code == 409
    assert response.json()["field"] == "email"


def test_update_username_conflict(client, user):
    register(client, **SECOND_USER)
    second_headers = auth_headers(
        client, email=SECOND_USER["email"], password=SECOND_USER["password"]
    )

    response = client.patch(
        "/api/users/me",
        headers=second_headers,
        json={"username": DEFAULT_USER["username"]},
    )
    assert response.status_code == 409
    assert response.json()["field"] == "username"


def test_change_password(client, headers):
    response = client.patch(
        "/api/users/me",
        headers=headers,
        json={
            "current_password": DEFAULT_USER["password"],
            "new_password": "NewTank2026",
        },
    )
    assert response.status_code == 200, response.text

    assert login(client, DEFAULT_USER["email"], DEFAULT_USER["password"]).status_code == 401
    assert login(client, DEFAULT_USER["email"], "NewTank2026").status_code == 200


def test_change_password_requires_correct_current(client, headers):
    response = client.patch(
        "/api/users/me",
        headers=headers,
        json={"current_password": "Wrong12345", "new_password": "NewTank2026"},
    )
    assert response.status_code == 400
    assert response.json()["code"] == "invalid_password"


def test_change_password_requires_current_password(client, headers):
    response = client.patch(
        "/api/users/me", headers=headers, json={"new_password": "NewTank2026"}
    )
    assert response.status_code == 422


def test_new_password_requires_confirmation_only_with_new(client, headers):
    response = client.patch(
        "/api/users/me",
        headers=headers,
        json={"current_password": DEFAULT_USER["password"]},
    )
    assert response.status_code == 422


def test_cannot_change_role_via_profile(client, headers):
    response = client.patch("/api/users/me", headers=headers, json={"role": "admin"})
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "extra_forbidden"


def test_regular_user_cannot_list_users(client, headers):
    response = client.get("/api/users", headers=headers)
    assert response.status_code == 403


def test_admin_can_list_users(client, admin_headers, user):
    register(client, **SECOND_USER)

    response = client.get("/api/users", headers=admin_headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 3  # admin + user + second
    assert body["limit"] == 20
    assert len(body["items"]) == 3
    assert all("hashed_password" not in item for item in body["items"])


def test_admin_can_get_user(client, admin_headers, user):
    response = client.get(f"/api/users/{user['id']}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["id"] == user["id"]


def test_admin_get_unknown_user(client, admin_headers):
    response = client.get("/api/users/9999", headers=admin_headers)
    assert response.status_code == 404


def test_admin_can_promote_user(client, admin_headers, user):
    response = client.patch(
        f"/api/users/{user['id']}", headers=admin_headers, json={"role": "admin"}
    )
    assert response.status_code == 200, response.text
    assert response.json()["role"] == "admin"

    promoted_headers = auth_headers(client)
    assert client.get("/api/users", headers=promoted_headers).status_code == 200


def test_admin_can_reset_password(client, admin_headers, user):
    response = client.patch(
        f"/api/users/{user['id']}",
        headers=admin_headers,
        json={"new_password": "ResetPass2026"},
    )
    assert response.status_code == 200, response.text
    assert login(client, DEFAULT_USER["email"], "ResetPass2026").status_code == 200


def test_admin_can_deactivate_user(client, admin_headers, user):
    response = client.delete(f"/api/users/{user['id']}", headers=admin_headers)
    assert response.status_code == 204

    assert login(client, DEFAULT_USER["email"], DEFAULT_USER["password"]).status_code == 403


def test_admin_cannot_deactivate_self(client, admin_headers):
    me = client.get("/api/users/me", headers=admin_headers).json()
    response = client.delete(f"/api/users/{me['id']}", headers=admin_headers)
    assert response.status_code == 409


def test_admin_cannot_remove_own_admin_role(client, admin_headers):
    me = client.get("/api/users/me", headers=admin_headers).json()
    response = client.patch(
        f"/api/users/{me['id']}", headers=admin_headers, json={"role": "user"}
    )
    assert response.status_code == 409


def test_admin_update_unknown_user(client, admin_headers):
    response = client.patch(
        "/api/users/9999", headers=admin_headers, json={"full_name": "Тест"}
    )
    assert response.status_code == 404


def test_users_pagination(client, admin_headers, user):
    register(client, **SECOND_USER)

    response = client.get(
        "/api/users", headers=admin_headers, params={"limit": 1, "offset": 1}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 1
