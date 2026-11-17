"""Репозиторий проектов и истории версий исходных данных."""

from __future__ import annotations

import json
import sqlite3

from app.utils import utcnow_iso

_PROJECT_SELECT = """
    SELECT
        p.id,
        p.user_id,
        p.name,
        p.description,
        p.status,
        p.input_data,
        p.created_at,
        p.updated_at,
        COALESCE(
            (SELECT MAX(v.version) FROM project_versions v WHERE v.project_id = p.id),
            0
        ) AS current_version,
        (
            SELECT COUNT(*) FROM project_versions v WHERE v.project_id = p.id
        ) AS versions_count
    FROM projects p
"""

_PROJECT_UPDATABLE = frozenset({"name", "description", "status", "input_data"})


def _project_from_row(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    project = dict(row)
    raw = project.get("input_data")
    project["input_data"] = json.loads(raw) if raw else None
    return project


def _version_from_row(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    version = dict(row)
    version["input_data"] = json.loads(version["input_data"])
    return version


def get_project(conn: sqlite3.Connection, project_id: int) -> dict | None:
    row = conn.execute(
        f"{_PROJECT_SELECT} WHERE p.id = ?", (project_id,)
    ).fetchone()
    return _project_from_row(row)


def get_project_for_user(
    conn: sqlite3.Connection, project_id: int, user_id: int
) -> dict | None:
    row = conn.execute(
        f"{_PROJECT_SELECT} WHERE p.id = ? AND p.user_id = ?",
        (project_id, user_id),
    ).fetchone()
    return _project_from_row(row)


def list_projects(
    conn: sqlite3.Connection,
    *,
    user_id: int,
    limit: int,
    offset: int,
    status: str | None = None,
    search: str | None = None,
) -> tuple[list[dict], int]:
    conditions = ["p.user_id = ?"]
    params: list[object] = [user_id]

    if status is not None:
        conditions.append("p.status = ?")
        params.append(status)

    if search:
        conditions.append("(p.name LIKE ? OR p.description LIKE ?)")
        pattern = f"%{search.strip()}%"
        params.extend([pattern, pattern])

    where = " WHERE " + " AND ".join(conditions)

    total_row = conn.execute(
        f"SELECT COUNT(*) AS total FROM projects p{where}", params
    ).fetchone()
    total = int(total_row["total"])

    rows = conn.execute(
        f"{_PROJECT_SELECT}{where} ORDER BY p.updated_at DESC, p.id DESC "
        "LIMIT ? OFFSET ?",
        (*params, limit, offset),
    ).fetchall()
    return [_project_from_row(row) for row in rows], total


def create_project(
    conn: sqlite3.Connection,
    *,
    user_id: int,
    name: str,
    description: str | None = None,
    status: str = "draft",
) -> dict:
    now = utcnow_iso()
    cursor = conn.execute(
        """
        INSERT INTO projects (user_id, name, description, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, name, description, status, now, now),
    )
    project = get_project(conn, int(cursor.lastrowid))
    assert project is not None
    return project


def update_project(
    conn: sqlite3.Connection, project_id: int, changes: dict
) -> dict | None:
    payload = {
        key: value for key, value in changes.items() if key in _PROJECT_UPDATABLE
    }
    if not payload:
        return get_project(conn, project_id)

    payload["updated_at"] = utcnow_iso()
    assignments = ", ".join(f"{column} = ?" for column in payload)
    conn.execute(
        f"UPDATE projects SET {assignments} WHERE id = ?",
        (*payload.values(), project_id),
    )
    return get_project(conn, project_id)


def delete_project(conn: sqlite3.Connection, project_id: int) -> bool:
    cursor = conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    return cursor.rowcount > 0


def add_version(
    conn: sqlite3.Connection,
    *,
    project_id: int,
    input_data_json: str,
    comment: str | None,
    created_by: int | None,
) -> dict:
    """Добавляет снимок исходных данных и делает его актуальным."""
    next_version_row = conn.execute(
        "SELECT COALESCE(MAX(version), 0) + 1 AS next_version "
        "FROM project_versions WHERE project_id = ?",
        (project_id,),
    ).fetchone()
    version_number = int(next_version_row["next_version"])
    now = utcnow_iso()

    conn.execute(
        """
        INSERT INTO project_versions
            (project_id, version, input_data, comment, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (project_id, version_number, input_data_json, comment, created_by, now),
    )
    conn.execute(
        "UPDATE projects SET input_data = ?, updated_at = ? WHERE id = ?",
        (input_data_json, now, project_id),
    )

    version = get_version(conn, project_id, version_number)
    assert version is not None
    return version


def get_version(
    conn: sqlite3.Connection, project_id: int, version: int
) -> dict | None:
    row = conn.execute(
        """
        SELECT id, project_id, version, input_data, comment, created_by, created_at
        FROM project_versions
        WHERE project_id = ? AND version = ?
        """,
        (project_id, version),
    ).fetchone()
    return _version_from_row(row)


def list_versions(
    conn: sqlite3.Connection,
    *,
    project_id: int,
    limit: int,
    offset: int,
) -> tuple[list[dict], int]:
    total_row = conn.execute(
        "SELECT COUNT(*) AS total FROM project_versions WHERE project_id = ?",
        (project_id,),
    ).fetchone()
    total = int(total_row["total"])

    rows = conn.execute(
        """
        SELECT id, project_id, version, input_data, comment, created_by, created_at
        FROM project_versions
        WHERE project_id = ?
        ORDER BY version DESC
        LIMIT ? OFFSET ?
        """,
        (project_id, limit, offset),
    ).fetchall()
    return [_version_from_row(row) for row in rows], total
