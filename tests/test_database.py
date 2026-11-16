"""Тесты схемы БД и ограничений целостности."""

from __future__ import annotations

import pytest

from app.database import Database
from app.errors import ConflictError
from app.repositories import projects as projects_repo
from app.repositories import users as users_repo
from app.security import hash_password
from tests.utils import valid_input


@pytest.fixture()
def database(tmp_path) -> Database:
    db = Database(tmp_path / "nested" / "test.db")
    db.init_schema()
    return db


def _create_user(connection, *, email="user@example.com", username="user") -> dict:
    return users_repo.create_user(
        connection,
        email=email,
        username=username,
        password_hash=hash_password("Tank12345"),
    )


def test_init_schema_creates_tables_and_is_idempotent(database):
    database.init_schema()

    with database.connect() as connection:
        names = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    assert {"users", "projects", "project_versions"} <= names


def test_foreign_keys_are_enabled(database):
    with database.connect() as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_email_is_unique_case_insensitive(database):
    with database.connect() as connection:
        _create_user(connection, email="User@Example.com", username="first")
        with pytest.raises(ConflictError) as error:
            _create_user(connection, email="user@example.COM", username="second")

    assert error.value.field == "email"


def test_username_is_unique_case_insensitive(database):
    with database.connect() as connection:
        _create_user(connection, email="first@example.com", username="Engineer")
        with pytest.raises(ConflictError) as error:
            _create_user(connection, email="second@example.com", username="ENGINEER")

    assert error.value.field == "username"


def test_deleting_project_cascades_versions(database):
    with database.connect() as connection:
        user = _create_user(connection)
        project = projects_repo.create_project(
            connection, user_id=user["id"], name="Проект"
        )
        projects_repo.add_version(
            connection,
            project_id=project["id"],
            input_data_json='{"ok": true}',
            comment=None,
            created_by=user["id"],
        )

        assert projects_repo.delete_project(connection, project["id"])
        versions = connection.execute(
            "SELECT COUNT(*) AS total FROM project_versions WHERE project_id = ?",
            (project["id"],),
        ).fetchone()["total"]

    assert versions == 0


def test_deleting_user_cascades_projects(database):
    with database.connect() as connection:
        user = _create_user(connection)
        project = projects_repo.create_project(
            connection, user_id=user["id"], name="Проект"
        )
        connection.execute("DELETE FROM users WHERE id = ?", (user["id"],))

        remaining = connection.execute(
            "SELECT COUNT(*) AS total FROM projects WHERE id = ?",
            (project["id"],),
        ).fetchone()["total"]

    assert remaining == 0


def test_add_version_increments_and_updates_project(database):
    with database.connect() as connection:
        user = _create_user(connection)
        project = projects_repo.create_project(
            connection, user_id=user["id"], name="Проект"
        )

        first = projects_repo.add_version(
            connection,
            project_id=project["id"],
            input_data_json='{"version": 1}',
            comment="Первая",
            created_by=user["id"],
        )
        second = projects_repo.add_version(
            connection,
            project_id=project["id"],
            input_data_json='{"version": 2}',
            comment="Вторая",
            created_by=user["id"],
        )
        project = projects_repo.get_project(connection, project["id"])

    assert (first["version"], second["version"]) == (1, 2)
    assert project is not None
    assert project["input_data"] == {"version": 2}
    assert project["current_version"] == 2
    assert project["versions_count"] == 2


def test_project_data_is_stored_as_json(database):
    with database.connect() as connection:
        user = _create_user(connection)
        project = projects_repo.create_project(
            connection, user_id=user["id"], name="Проект"
        )
        payload = valid_input()

        import json

        projects_repo.add_version(
            connection,
            project_id=project["id"],
            input_data_json=json.dumps(payload, ensure_ascii=False),
            comment=None,
            created_by=user["id"],
        )
        stored = projects_repo.get_version(connection, project["id"], 1)

    assert stored is not None
    assert stored["input_data"]["object"]["name"] == "РВС-1000"
