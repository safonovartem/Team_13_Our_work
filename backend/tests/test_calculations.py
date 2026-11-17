"""Тесты расчётов, графиков, справочника и истории расчётов проекта."""

from __future__ import annotations

import pytest

from tests.utils import SECOND_USER, auth_headers, register

CALC_PAYLOAD = {
    "tank_volume": 5000,
    "clearance_l": 3.0,
    "crest_width_b": 1.0,
}


def _dataset(chart: dict, label: str) -> dict:
    for item in chart["datasets"]:
        if item["label"] == label:
            return item
    raise AssertionError(f"Нет набора данных с меткой {label!r}")


def test_calculate_returns_core_result_and_ui_blocks(client):
    response = client.post("/api/calculations", json=CALC_PAYLOAD)
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["input"]["tank_volume"] == 5000
    assert body["result"]["tank_volume"] == 5000
    assert body["result"]["tank_diameter_m"] == 20.92
    assert body["result"]["wave"]["trajectory"]

    assert {block["id"] for block in body["variants"]} == {"no-canopy", "gvk"}
    assert {block["scenario"] for block in body["variants"]} == {"plain", "gwk"}
    assert [block["title"] for block in body["variants"]] == [
        "Без козырька",
        "С горизонтальным козырьком (ГВК)",
    ]
    recommended = [
        block for block in body["variants"] if block["isImportant"]
    ]
    assert len(recommended) == 1
    assert recommended[0]["scenario"] == body["recommended_variant"]

    for block in body["variants"]:
        titles = {item["title"] for item in block["items"]}
        assert "Доля перелива" in titles
        assert "Безопасность" in titles
        assert all(isinstance(item["value"], str) for item in block["items"])


def test_calculate_charts_match_example(client):
    response = client.post(
        "/api/calculations",
        json={
            **CALC_PAYLOAD,
            "clearance_l": 3.0,
        },
    )
    assert response.status_code == 200, response.text

    charts = response.json()["charts"]
    assert [chart["title"] for chart in charts] == [
        "Доля перелива от высоты стенки",
        "Траектория фронта волны",
        "Высота потока вдоль пути растекания",
    ]

    overflow = charts[0]
    points = _dataset(overflow, "l = 3.0 м")["data"]
    by_ratio = {point[0]: point[1] for point in points}
    assert by_ratio[0.7] == pytest.approx(10.03, abs=0.01)
    # Сетка по умолчанию — шаг 0.05; точка 0.97 доступна через
    # /api/charts/overflow с явным height_ratios (см. отдельный тест).
    assert by_ratio[0.95] > 0
    assert by_ratio[1.0] == 0.0
    assert by_ratio[1.1] == 0.0

    # Каждая точка — пара [x, y] чисел, как в контракте Chart.js.
    for dataset in overflow["datasets"]:
        assert dataset["label"].startswith("l = ")
        assert all(
            isinstance(point, list)
            and len(point) == 2
            and all(isinstance(value, (int, float)) for value in point)
            for point in dataset["data"]
        )

    for chart in charts[1:]:
        assert len(chart["datasets"][0]["data"]) > 1


def test_calculate_from_form_object_type(client):
    response = client.post(
        "/api/calculations/from-form",
        json={
            "objectName": "РВС-5000",
            "objectType": "РВС-5000 · 5 000 м³",
            "fillLevel": 100,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["input"]["tank_volume"] == 5000
    assert body["input"]["clearance_l"] == 3.0
    assert body["input"]["crest_width_b"] == 1.0
    assert body["variants"]


def test_calculate_from_form_object_volume_fallback(client):
    response = client.post(
        "/api/calculations/from-form",
        json={"objectType": "другое", "objectVolume": 2000},
    )
    assert response.status_code == 200, response.text
    assert response.json()["input"]["tank_volume"] == 2000


def test_calculate_from_form_explicit_geometry(client):
    response = client.post(
        "/api/calculations/from-form",
        json={
            "objectType": "РВС-2000 · 2 000 м³",
            "clearanceL": 1.5,
            "crestWidthB": 1.5,
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["input"]["clearance_l"] == 1.5
    assert response.json()["input"]["crest_width_b"] == 1.5


def test_calculate_from_form_without_volume_fails(client):
    response = client.post(
        "/api/calculations/from-form", json={"objectName": "без объёма"}
    )
    assert response.status_code == 422
    assert response.json()["code"] == "domain_range_error"


def test_calculate_unknown_tank_volume_fails(client):
    response = client.post("/api/calculations", json={"tank_volume": 123})
    assert response.status_code == 422
    assert response.json()["code"] == "domain_range_error"
    assert "каталоге ГОСТ" in response.json()["detail"]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("clearance_l", 0.5),
        ("clearance_l", 4.0),
        ("crest_width_b", 0.1),
        ("crest_width_b", 2.0),
    ],
)
def test_calculate_out_of_range_fails(client, field, value):
    response = client.post(
        "/api/calculations", json={**CALC_PAYLOAD, field: value}
    )
    assert response.status_code == 422
    assert response.json()["code"] == "domain_range_error"


def test_calculate_single_scenario(client):
    response = client.post(
        "/api/calculations",
        json={**CALC_PAYLOAD, "scenarios": ["plain"]},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert [block["scenario"] for block in body["variants"]] == ["plain"]
    assert body["recommended_variant"] == "plain"
    assert body["variants"][0]["isImportant"] is True


def test_overflow_chart_endpoint_matches_example(client):
    response = client.post(
        "/api/charts/overflow",
        json={
            "tank_volume": 5000,
            "clearance_values": [3.0],
            "height_ratios": [0.7, 0.97, 1.1],
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["title"]
    assert body["datasets"] == [
        {
            "label": "l = 3.0 м",
            "data": [[0.7, 10.03], [0.97, 0.0], [1.1, 0.0]],
        }
    ]


def test_overflow_chart_default_grid_has_four_curves(client):
    response = client.post("/api/charts/overflow", json={"tank_volume": 700})
    assert response.status_code == 200, response.text
    assert [item["label"] for item in response.json()["datasets"]] == [
        "l = 1.5 м",
        "l = 2.0 м",
        "l = 2.5 м",
        "l = 3.0 м",
    ]


def test_overflow_chart_rejects_invalid_heights(client):
    response = client.post(
        "/api/charts/overflow",
        json={"tank_volume": 5000, "height_ratios": [1.5]},
    )
    assert response.status_code == 422
    assert response.json()["code"] == "domain_range_error"


def test_wave_charts_endpoint(client):
    response = client.post(
        "/api/charts/wave", json={"tank_volume": 5000, "clearance_l": 2.0}
    )
    assert response.status_code == 200, response.text
    charts = response.json()["charts"]
    assert len(charts) == 2
    assert charts[0]["datasets"][0]["label"] == "l = 2.0 м"
    assert all(chart["datasets"][0]["data"] for chart in charts)


def test_all_charts_endpoint(client):
    response = client.post("/api/charts", json={"tank_volume": 2000})
    assert response.status_code == 200, response.text
    assert len(response.json()["charts"]) == 3


def test_catalog_endpoint(client):
    response = client.get("/api/catalog")
    assert response.status_code == 200, response.text
    body = response.json()
    assert [tank["volume_m3"] for tank in body["tanks"]] == [
        700,
        2000,
        5000,
        10000,
        20000,
        30000,
    ]
    assert body["limits"]["clearance_l_min"] == 1.5
    assert body["limits"]["clearance_l_max"] == 3.0
    assert body["limits"]["scenarios"] == ["plain", "gwk"]


def test_public_calculation_endpoints_do_not_require_auth(client):
    assert client.post("/api/calculations", json=CALC_PAYLOAD).status_code == 200
    assert client.post("/api/charts", json={"tank_volume": 700}).status_code == 200
    assert client.get("/api/catalog").status_code == 200


# ── История расчётов проекта ─────────────────────────────────────────────────


def test_save_and_get_project_calculation(client, headers, project):
    response = client.post(
        f"/api/projects/{project['id']}/calculations",
        headers=headers,
        json=CALC_PAYLOAD,
    )
    assert response.status_code == 201, response.text
    saved = response.json()
    assert saved["project_id"] == project["id"]
    assert saved["input"]["tank_volume"] == 5000
    assert saved["result"]["tank_volume"] == 5000
    assert saved["variants"]
    assert saved["charts"]

    found = client.get(
        f"/api/projects/{project['id']}/calculations/{saved['id']}",
        headers=headers,
    )
    assert found.status_code == 200
    assert found.json()["id"] == saved["id"]
    assert found.json()["result"] == saved["result"]


def test_project_calculation_history(client, headers, project):
    for _ in range(2):
        response = client.post(
            f"/api/projects/{project['id']}/calculations",
            headers=headers,
            json=CALC_PAYLOAD,
        )
        assert response.status_code == 201, response.text

    history = client.get(
        f"/api/projects/{project['id']}/calculations",
        headers=headers,
        params={"limit": 1, "offset": 0},
    )
    assert history.status_code == 200, response.text
    body = history.json()
    assert body["total"] == 2
    assert len(body["items"]) == 1
    assert body["items"][0]["input"]["tank_volume"] == 5000
    assert body["limit"] == 1


def test_saved_calculation_charts(client, headers, project):
    created = client.post(
        f"/api/projects/{project['id']}/calculations/from-form",
        headers=headers,
        json={"objectType": "РВС-5000 · 5 000 м³"},
    )
    assert created.status_code == 201, created.text
    assert created.json()["input"]["tank_volume"] == 5000

    charts = client.get(
        f"/api/projects/{project['id']}/calculations/{created.json()['id']}/charts",
        headers=headers,
    )
    assert charts.status_code == 200, response.text
    body = charts.json()
    assert len(body["charts"]) == 3
    assert body["charts"][0]["datasets"]


def test_delete_project_calculation(client, headers, project):
    created = client.post(
        f"/api/projects/{project['id']}/calculations",
        headers=headers,
        json=CALC_PAYLOAD,
    ).json()

    deleted = client.delete(
        f"/api/projects/{project['id']}/calculations/{created['id']}",
        headers=headers,
    )
    assert deleted.status_code == 204
    assert (
        client.get(
            f"/api/projects/{project['id']}/calculations/{created['id']}",
            headers=headers,
        ).status_code
        == 404
    )


def test_project_calculation_requires_auth(client, project):
    assert (
        client.post(
            f"/api/projects/{project['id']}/calculations", json=CALC_PAYLOAD
        ).status_code
        == 401
    )
    assert (
        client.get(
            f"/api/projects/{project['id']}/calculations"
        ).status_code
        == 401
    )


def test_project_calculation_isolated_by_owner(client, headers, project):
    register(client, **SECOND_USER)
    other_headers = auth_headers(
        client, email=SECOND_USER["email"], password=SECOND_USER["password"]
    )

    assert (
        client.post(
            f"/api/projects/{project['id']}/calculations",
            headers=other_headers,
            json=CALC_PAYLOAD,
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/api/projects/{project['id']}/calculations", headers=other_headers
        ).status_code
        == 404
    )


def test_unknown_calculation_returns_404(client, headers, project):
    response = client.get(
        f"/api/projects/{project['id']}/calculations/9999", headers=headers
    )
    assert response.status_code == 404


def test_deleting_project_cascades_calculations(client, app, headers, project):
    created = client.post(
        f"/api/projects/{project['id']}/calculations",
        headers=headers,
        json=CALC_PAYLOAD,
    )
    assert created.status_code == 201

    deleted = client.delete(
        f"/api/projects/{project['id']}", headers=headers
    )
    assert deleted.status_code == 204

    with app.state.database.connect() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS total FROM calculations WHERE project_id = ?",
            (project["id"],),
        ).fetchone()
    assert row["total"] == 0
