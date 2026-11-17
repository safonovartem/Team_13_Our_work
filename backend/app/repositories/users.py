"""Репозиторий пользователей (SQLite)."""

from __future__ import annotations

import sqlite3

from app.errors import ConflictError
from app.utils import utcnow_iso

_PUBLIC_COLUMNS = (
    "id, email, username, full_name, organization, hashed_password, "
    "role, is_active, created_at, updated_at"
)

_UPDATABLE_COLUMNS = frozenset(
    {
        "email",
        "username",
        "full_name",
        "organization",
        "hashed_password",
        "role",
        "is_active",
    }
)


def _to_dict(row: sqlite3.Row | None) -> dict | None:
    return None if row is None else dict(row)


def get_by_id(conn: sqlite3.Connection, user_id: int) -> dict | None:
    row = conn.execute(
        f"SELECT {_PUBLIC_COLUMNS} FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    return _to_dict(row)


def get_by_email(conn: sqlite3.Connection, email: str) -> dict | None:
    row = conn.execute(
        f"SELECT {_PUBLIC_COLUMNS} FROM users WHERE email = ?",
        (email.strip().lower(),),
    ).fetchone()
    return _to_dict(row)


def get_by_username(conn: sqlite3.Connection, username: str) -> dict | None:
    row = conn.execute(
        f"SELECT {_PUBLIC_COLUMNS} FROM users WHERE username = ?",
        (username.strip(),),
    ).fetchone()
    return _to_dict(row)


def find_by_login(conn: sqlite3.Connection, login: str) -> dict | None:
    """Ищет пользователя по email или username (без учёта регистра)."""
    row = conn.execute(
        f"SELECT {_PUBLIC_COLUMNS} FROM users WHERE email = ? OR username = ?",
        (login.strip(), login.strip()),
    ).fetchone()
    return _to_dict(row)


def list_users(
    conn: sqlite3.Connection, *, limit: int, offset: int
) -> list[dict]:
    rows = conn.execute(
        f"SELECT {_PUBLIC_COLUMNS} FROM users ORDER BY id LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    return [dict(row) for row in rows]


def count_users(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) AS total FROM users").fetchone()
    return int(row["total"])


def create_user(
    conn: sqlite3.Connection,
    *,
    email: str,
    username: str,
    password_hash: str,
    full_name: str | None = None,
    organization: str | None = None,
    role: str = "user",
    is_active: bool = True,
) -> dict:
    now = utcnow_iso()
    try:
        cursor = conn.execute(
            """
            INSERT INTO users (
                email, username, full_name, organization,
                hashed_password, role, is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                email.strip().lower(),
                username.strip(),
                full_name,
                organization,
                password_hash,
                role,
                1 if is_active else 0,
                now,
                now,
            ),
        )
    except sqlite3.IntegrityError as exc:
        raise _map_integrity_error(exc) from exc

    user = get_by_id(conn, int(cursor.lastrowid))
    assert user is not None  # только что вставленная запись
    return user


def update_user(
    conn: sqlite3.Connection, user_id: int, changes: dict
) -> dict | None:
    """Обновляет разрешённые поля. ``None`` в значении очищает поле."""
    payload = {
        key: value for key, value in changes.items() if key in _UPDATABLE_COLUMNS
    }
    if "is_active" in payload:
        payload["is_active"] = 1 if payload["is_active"] else 0
    if "email" in payload and payload["email"] is not None:
        payload["email"] = payload["email"].strip().lower()
    if "username" in payload and payload["username"] is not None:
        payload["username"] = payload["username"].strip()

    payload["updated_at"] = utcnow_iso()

    assignments = ", ".join(f"{column} = ?" for column in payload)
    try:
        conn.execute(
            f"UPDATE users SET {assignments} WHERE id = ?",
            (*payload.values(), user_id),
        )
    except sqlite3.IntegrityError as exc:
        raise _map_integrity_error(exc) from exc

    return get_by_id(conn, user_id)


def _map_integrity_error(exc: sqlite3.IntegrityError) -> ConflictError:
    message = str(exc).lower()
    if "users.email" in message:
        return ConflictError(
            "Пользователь с таким email уже зарегистрирован", field="email"
        )
    if "users.username" in message:
        return ConflictError(
            "Пользователь с таким именем уже зарегистрирован", field="username"
        )
    return ConflictError("Нарушено ограничение целостности данных")
