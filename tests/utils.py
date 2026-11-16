"""Общие данные и помощники для тестов."""

from __future__ import annotations

import copy

DEFAULT_USER = {
    "email": "engineer@example.com",
    "username": "engineer",
    "password": "Tank12345",
    "full_name": "Иван Петров",
    "organization": "ООО «АралИнжиниринг»",
}

SECOND_USER = {
    "email": "second@example.com",
    "username": "second",
    "password": "Orbit2026Pass",
    "full_name": "Пётр Сидоров",
}

ADMIN_USER = {
    "email": "admin@example.com",
    "username": "admin",
    "password": "Admin12345",
    "full_name": "Администратор",
}

VALID_INPUT = {
    "schema_version": 1,
    "object": {
        "name": "РВС-1000",
        "object_type": "vertical_cylinder",
        "material": "Сталь 09Г2С",
        "wall_thickness_mm": 8,
        "height_m": 12,
        "diameter_m": 10.4,
        "volume_m3": 1000,
    },
    "liquid": {
        "liquid_type": "oil",
        "density_kg_m3": 870,
        "viscosity_cst": 25,
        "temperature_c": 20,
        "fill_level_percent": 50,
        "volume_m3": 500,
    },
    "environment": {
        "ambient_temperature_c": 15,
        "terrain_type": "flat",
        "surface_type": "soil",
        "slope_degrees": 0,
        "has_obstacles": False,
        "containment": True,
    },
}


def valid_input() -> dict:
    return copy.deepcopy(VALID_INPUT)


def register(client, **overrides):
    payload = {**DEFAULT_USER, **overrides}
    return client.post("/api/auth/register", json=payload)


def login(client, login_value: str, password: str):
    return client.post(
        "/api/auth/login", json={"login": login_value, "password": password}
    )


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def auth_headers(
    client, *, email: str = DEFAULT_USER["email"], password: str | None = None
) -> dict[str, str]:
    response = login(client, email, password or DEFAULT_USER["password"])
    assert response.status_code == 200, response.text
    return bearer(response.json()["access_token"])
