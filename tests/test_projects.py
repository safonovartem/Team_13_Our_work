"""Тесты проектов, истории версий и валидации исходных данных."""

from __future__ import annotations

import pytest

from tests.utils import SECOND_USER, auth_headers, register, valid_input


def _with(path: str, value) -> dict:
    data = valid_input()
    parts = path.split(".")
    target = data
    for part in parts[:-1]:
        target = target[part]
    target[parts[-1]] = value
    return data


def _without(path: str) -> dict:
    data = valid_input()
    parts = path.split(".")
    target = data
    for part in parts[:-1]:
        target = target[part]
    del target[parts[-1]]
    return data


def _messages(response) -> str:
    return " ".join(item.get("msg", "") for item in response.json()["detail"])


def test_create_project_requires_auth(client):
    response = client.post("/api/projects", json={"name": "Проект"})
    assert response.status_code == 401


def test_create_project_without_input(client, headers):
    response = client.post(
        "/api/projects", headers=headers, json={"name": "  Новый проект  "}
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["name"] == "Новый проект"
    assert body["status"] == "draft"
    assert body["input_data"] is None
    assert body["current_version"] == 0
    assert body["versions_count"] == 0


def test_create_project_with_input(client, headers, project):
    assert project["current_version"] == 1
    assert project["versions_count"] == 1
    assert project["input_data"]["object"]["name"] == "РВС-1000"

    history = client.get(
        f"/api/projects/{project['id']}/history", headers=headers
    )
    assert history.status_code == 200


def test_history_contains_initial_version(client, headers, project):
    response = client.get(
        f"/api/projects/{project['id']}/history", headers=headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["version"] == 1
    assert body["items"][0]["comment"] == "Начальные исходные данные"
    assert body["items"][0]["input_data"]["liquid"]["density_kg_m3"] == 870


def test_list_returns_only_own_projects(client, headers):
    for index in range(3):
        response = client.post(
            "/api/projects", headers=headers, json={"name": f"Проект {index}"}
        )
        assert response.status_code == 201

    register(client, **SECOND_USER)
    second_headers = auth_headers(
        client, email=SECOND_USER["email"], password=SECOND_USER["password"]
    )
    client.post("/api/projects", headers=second_headers, json={"name": "Чужой"})

    response = client.get("/api/projects", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert {item["name"] for item in body["items"]} == {
        "Проект 0",
        "Проект 1",
        "Проект 2",
    }


def test_list_filter_by_status_and_search(client, headers):
    draft = client.post("/api/projects", headers=headers, json={"name": "Парк А"}).json()
    client.post(
        "/api/projects",
        headers=headers,
        json={"name": "Парк Б", "description": "Черновик"},
    )
    ready = client.post("/api/projects", headers=headers, json={"name": "Парк В"}).json()
    client.patch(
        f"/api/projects/{ready['id']}", headers=headers, json={"status": "ready"}
    )

    by_status = client.get("/api/projects", headers=headers, params={"status": "ready"})
    assert by_status.status_code == 200
    assert by_status.json()["total"] == 1
    assert by_status.json()["items"][0]["id"] == ready["id"]

    by_search = client.get("/api/projects", headers=headers, params={"search": "Черновик"})
    assert by_search.status_code == 200
    assert by_search.json()["total"] == 1
    assert by_search.json()["items"][0]["name"] == "Парк Б"

    assert draft["status"] == "draft"


def test_get_project(client, headers, project):
    response = client.get(f"/api/projects/{project['id']}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == project["id"]


def test_unknown_project_returns_404(client, headers):
    assert client.get("/api/projects/9999", headers=headers).status_code == 404


def test_project_of_another_user_is_hidden(client, headers, project):
    register(client, **SECOND_USER)
    second_headers = auth_headers(
        client, email=SECOND_USER["email"], password=SECOND_USER["password"]
    )

    assert (
        client.get(f"/api/projects/{project['id']}", headers=second_headers).status_code
        == 404
    )
    assert (
        client.patch(
            f"/api/projects/{project['id']}",
            headers=second_headers,
            json={"name": "Взлом"},
        ).status_code
        == 404
    )
    assert (
        client.delete(
            f"/api/projects/{project['id']}", headers=second_headers
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/projects/{project['id']}/history", headers=second_headers
        ).status_code
        == 404
    )


def test_update_metadata(client, headers, project):
    response = client.patch(
        f"/api/projects/{project['id']}",
        headers=headers,
        json={
            "name": "Обновлённый проект",
            "description": "Описание",
            "status": "ready",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["name"] == "Обновлённый проект"
    assert body["description"] == "Описание"
    assert body["status"] == "ready"
    assert body["current_version"] == 1


def test_update_input_creates_new_version(client, headers, project):
    new_input = valid_input()
    new_input["object"]["name"] = "РВС-2000"

    response = client.patch(
        f"/api/projects/{project['id']}",
        headers=headers,
        json={"input_data": new_input, "version_comment": "Новый резервуар"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["current_version"] == 2
    assert body["versions_count"] == 2
    assert body["input_data"]["object"]["name"] == "РВС-2000"

    history = client.get(
        f"/api/projects/{project['id']}/history", headers=headers
    ).json()
    assert [item["version"] for item in history["items"]] == [2, 1]
    assert history["items"][0]["comment"] == "Новый резервуар"


def test_get_specific_version(client, headers, project):
    response = client.get(
        f"/api/projects/{project['id']}/history/1", headers=headers
    )
    assert response.status_code == 200
    assert response.json()["version"] == 1

    missing = client.get(
        f"/api/projects/{project['id']}/history/99", headers=headers
    )
    assert missing.status_code == 404


def test_restore_version(client, headers, project):
    new_input = valid_input()
    new_input["liquid"]["temperature_c"] = 35
    client.patch(
        f"/api/projects/{project['id']}",
        headers=headers,
        json={"input_data": new_input},
    )

    response = client.post(
        f"/api/projects/{project['id']}/history/1/restore", headers=headers
    )
    assert response.status_code == 201, response.text
    assert response.json()["version"] == 3
    assert response.json()["input_data"]["liquid"]["temperature_c"] == 20

    current = client.get(f"/api/projects/{project['id']}", headers=headers).json()
    assert current["current_version"] == 3
    assert current["input_data"]["liquid"]["temperature_c"] == 20


def test_save_current_data_as_version(client, headers, project):
    response = client.post(
        f"/api/projects/{project['id']}/history",
        headers=headers,
        json={"comment": "Контрольная точка"},
    )
    assert response.status_code == 201, response.text
    assert response.json()["version"] == 2
    assert response.json()["comment"] == "Контрольная точка"


def test_save_version_without_data_conflicts(client, headers):
    created = client.post(
        "/api/projects", headers=headers, json={"name": "Пустой проект"}
    ).json()

    response = client.post(
        f"/api/projects/{created['id']}/history", headers=headers, json={}
    )
    assert response.status_code == 409
    assert response.json()["field"] == "input_data"


def test_delete_project_cascades_history(client, app, headers, project):
    response = client.delete(f"/api/projects/{project['id']}", headers=headers)
    assert response.status_code == 204
    assert (
        client.get(f"/api/projects/{project['id']}", headers=headers).status_code == 404
    )

    with app.state.database.connect() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS total FROM project_versions WHERE project_id = ?",
            (project["id"],),
        ).fetchone()
    assert row["total"] == 0


def test_projects_pagination(client, headers):
    for index in range(3):
        client.post(
            "/api/projects", headers=headers, json={"name": f"Проект {index}"}
        )

    first = client.get(
        "/api/projects", headers=headers, params={"limit": 2, "offset": 0}
    ).json()
    assert first["total"] == 3
    assert len(first["items"]) == 2

    second = client.get(
        "/api/projects", headers=headers, params={"limit": 2, "offset": 2}
    ).json()
    assert len(second["items"]) == 1
    assert {item["id"] for item in first["items"]}.isdisjoint(
        {item["id"] for item in second["items"]}
    )


def test_patch_rejects_null_input(client, headers, project):
    response = client.patch(
        f"/api/projects/{project['id']}", headers=headers, json={"input_data": None}
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("path", "value", "expected"),
    [
        ("object.wall_thickness_mm", 0, "Толщина стенки должна быть больше 0 мм"),
        ("object.wall_thickness_mm", -4, "Толщина стенки должна быть больше 0 мм"),
        ("object.name", "   ", "Поле не может быть пустым"),
        ("object.object_type", "spherical", "Input should be"),
        ("liquid.density_kg_m3", 100, "greater than or equal to 500"),
        ("liquid.density_kg_m3", 5000, "less than or equal to 2000"),
        ("liquid.fill_level_percent", 120, "less than or equal to 100"),
        ("liquid.volume_m3", 1500, "не может превышать объём объекта"),
        ("liquid.volume_m3", 300, "не соответствует уровню заполнения"),
        ("environment.ambient_temperature_c", -100, "greater than or equal to -60"),
        (
            "environment.slope_degrees",
            30,
            "Для ровной территории уклон не может превышать 5 градусов",
        ),
    ],
)
def test_input_validation_ranges(client, headers, path, value, expected):
    response = client.post(
        "/api/projects",
        headers=headers,
        json={"name": "Проект", "input_data": _with(path, value)},
    )
    assert response.status_code == 422, response.text
    assert expected in _messages(response)


def test_input_requires_diameter_for_cylinder(client, headers):
    response = client.post(
        "/api/projects",
        headers=headers,
        json={"name": "Проект", "input_data": _without("object.diameter_m")},
    )
    assert response.status_code == 422
    assert "diameter_m" in _messages(response)


def test_input_requires_dimensions_for_rectangular_object(client, headers):
    data = _with("object.object_type", "rectangular")
    response = client.post(
        "/api/projects", headers=headers, json={"name": "Проект", "input_data": data}
    )
    assert response.status_code == 422
    assert "length_m" in _messages(response)


def test_input_rejects_obstacles_description_without_flag(client, headers):
    data = _with("environment.obstacles_description", "Стена")
    response = client.post(
        "/api/projects", headers=headers, json={"name": "Проект", "input_data": data}
    )
    assert response.status_code == 422
    assert "has_obstacles" in _messages(response)


def test_input_rejects_extra_fields(client, headers):
    data = valid_input()
    data["object"]["unknown_parameter"] = 1
    response = client.post(
        "/api/projects", headers=headers, json={"name": "Проект", "input_data": data}
    )
    assert response.status_code == 422
    assert any(
        item["type"] == "extra_forbidden" for item in response.json()["detail"]
    )


def test_input_rejects_unknown_environment_value(client, headers):
    data = _with("environment.surface_type", "lava")
    response = client.post(
        "/api/projects", headers=headers, json={"name": "Проект", "input_data": data}
    )
    assert response.status_code == 422


def test_project_name_is_required(client, headers):
    response = client.post("/api/projects", headers=headers, json={"name": "   "})
    assert response.status_code == 422
    assert "Название проекта" in _messages(response)
