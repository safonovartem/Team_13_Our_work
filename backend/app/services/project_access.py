"""Проверка доступа к проекту (один владелец).

Вынесено отдельно, чтобы и роутер проектов, и роутер истории расчётов
использовали одинаковую логику и одинаково скрывали чужие проекты (404).
"""

from __future__ import annotations

import sqlite3

from app.errors import NotFoundError
from app.repositories import projects as projects_repo


def get_owned_project(
    connection: sqlite3.Connection, project_id: int, user_id: int
) -> dict:
    project = projects_repo.get_project_for_user(connection, project_id, user_id)
    if project is None:
        raise NotFoundError("Проект не найден")
    return project
