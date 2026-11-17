"""Работа с SQLite: подключение и создание схемы.

Приложение намеренно использует стандартный модуль ``sqlite3`` без ORM:
стек проекта ограничен FastAPI + Pydantic + SQLite, а вся работа с данными
собрана в слое ``app.repositories``.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    email           TEXT    NOT NULL COLLATE NOCASE UNIQUE,
    username        TEXT    NOT NULL COLLATE NOCASE UNIQUE,
    full_name       TEXT,
    organization    TEXT,
    hashed_password TEXT    NOT NULL,
    role            TEXT    NOT NULL DEFAULT 'user'
                            CHECK (role IN ('user', 'admin')),
    is_active       INTEGER NOT NULL DEFAULT 1
                            CHECK (is_active IN (0, 1)),
    created_at      TEXT    NOT NULL,
    updated_at      TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name        TEXT    NOT NULL,
    description TEXT,
    status      TEXT    NOT NULL DEFAULT 'draft'
                        CHECK (status IN ('draft', 'ready', 'archived')),
    input_data  TEXT,
    created_at  TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id);
CREATE INDEX IF NOT EXISTS idx_projects_updated_at ON projects(updated_at);

CREATE TABLE IF NOT EXISTS project_versions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    version     INTEGER NOT NULL CHECK (version > 0),
    input_data  TEXT    NOT NULL,
    comment     TEXT,
    created_by  INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at  TEXT    NOT NULL,
    UNIQUE (project_id, version)
);

CREATE INDEX IF NOT EXISTS idx_project_versions_project_id
    ON project_versions(project_id);

CREATE TABLE IF NOT EXISTS calculations (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id             INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    input_data          TEXT    NOT NULL,
    form_data           TEXT,
    result_data         TEXT    NOT NULL,
    charts              TEXT    NOT NULL,
    recommended_variant TEXT    NOT NULL
                                CHECK (recommended_variant IN ('plain', 'gwk')),
    created_at          TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_calculations_project_id
    ON calculations(project_id);
CREATE INDEX IF NOT EXISTS idx_calculations_user_id
    ON calculations(user_id);
"""


class Database:
    """Тонкая обёртка над файлом SQLite."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        """Открывает новое соединение.

        Соединение живёт в рамках одного HTTP-запроса, поэтому
        ``check_same_thread=False`` безопасен: соединение не переиспользуется
        между запросами.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(
            self.path,
            timeout=10.0,
            check_same_thread=False,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def init_schema(self) -> None:
        """Создаёт таблицы и индексы, если их ещё нет."""
        with self.connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(SCHEMA)
