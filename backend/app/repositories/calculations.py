"""Репозиторий истории расчётов (SQLite).

Расчёт хранится отдельно от версий исходных данных проекта: одна и та же
версия данных может быть рассчитана с разными параметрами ядра (l, b и т.п.).
"""

from __future__ import annotations

import json
import sqlite3

from app.utils import utcnow_iso

_SELECT = """
    SELECT
        id,
        project_id,
        user_id,
        input_data,
        form_data,
        result_data,
        charts,
        recommended_variant,
        created_at
    FROM calculations
"""


def _from_row(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    record = dict(row)
    record["input_data"] = json.loads(record["input_data"])
    record["result_data"] = json.loads(record["result_data"])
    record["charts"] = json.loads(record["charts"])
    raw_form = record.get("form_data")
    record["form_data"] = json.loads(raw_form) if raw_form else None
    return record


def create_calculation(
    conn: sqlite3.Connection,
    *,
    project_id: int,
    user_id: int,
    input_data_json: str,
    result_data_json: str,
    charts_json: str,
    recommended_variant: str,
    form_data_json: str | None = None,
) -> dict:
    """Сохраняет расчёт и возвращает запись с разобранным JSON."""
    cursor = conn.execute(
        """
        INSERT INTO calculations (
            project_id, user_id, input_data, form_data, result_data,
            charts, recommended_variant, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            project_id,
            user_id,
            input_data_json,
            form_data_json,
            result_data_json,
            charts_json,
            recommended_variant,
            utcnow_iso(),
        ),
    )
    record = get_calculation(conn, int(cursor.lastrowid))
    assert record is not None
    return record


def get_calculation(
    conn: sqlite3.Connection, calculation_id: int
) -> dict | None:
    row = conn.execute(
        f"{_SELECT} WHERE id = ?", (calculation_id,)
    ).fetchone()
    return _from_row(row)


def list_calculations(
    conn: sqlite3.Connection,
    *,
    project_id: int,
    limit: int,
    offset: int,
) -> tuple[list[dict], int]:
    total_row = conn.execute(
        "SELECT COUNT(*) AS total FROM calculations WHERE project_id = ?",
        (project_id,),
    ).fetchone()
    total = int(total_row["total"])

    rows = conn.execute(
        f"{_SELECT} WHERE project_id = ? "
        "ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?",
        (project_id, limit, offset),
    ).fetchall()
    return [_from_row(row) for row in rows], total


def delete_calculation(
    conn: sqlite3.Connection, calculation_id: int
) -> bool:
    cursor = conn.execute(
        "DELETE FROM calculations WHERE id = ?", (calculation_id,)
    )
    return cursor.rowcount > 0
