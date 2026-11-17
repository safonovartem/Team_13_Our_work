"""Проекты пользователя и история версий исходных данных."""

from __future__ import annotations

import json
import sqlite3

from fastapi import APIRouter, Depends, Query, Response, status

from app.deps import get_connection, get_current_user
from app.errors import ConflictError, NotFoundError
from app.repositories import projects as projects_repo
from app.schemas.common import Page
from app.schemas.projects import (
    ProjectCreate,
    ProjectRead,
    ProjectStatus,
    ProjectSummary,
    ProjectUpdate,
    ProjectVersionCreate,
    ProjectVersionRead,
)
from app.services.project_access import get_owned_project as _get_owned_project

router = APIRouter(prefix="/projects", tags=["Проекты"])


def _metadata_changes(payload: ProjectUpdate) -> dict:
    """Собирает только явно переданные поля метаданных."""
    changes: dict[str, object] = {}
    if "name" in payload.model_fields_set:
        changes["name"] = payload.name
    if "description" in payload.model_fields_set:
        changes["description"] = payload.description
    if "status" in payload.model_fields_set and payload.status is not None:
        changes["status"] = payload.status.value
    return changes


@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать проект",
    responses={422: {"description": "Некорректные исходные данные"}},
)
def create_project(
    payload: ProjectCreate,
    user: dict = Depends(get_current_user),
    connection: sqlite3.Connection = Depends(get_connection),
) -> dict:
    project = projects_repo.create_project(
        connection,
        user_id=user["id"],
        name=payload.name,
        description=payload.description,
        status=payload.status.value,
    )

    if payload.input_data is not None:
        projects_repo.add_version(
            connection,
            project_id=project["id"],
            input_data_json=payload.input_data.model_dump_json(),
            comment=payload.comment or "Начальные исходные данные",
            created_by=user["id"],
        )
        project = projects_repo.get_project(connection, project["id"]) or project

    return project


@router.get(
    "",
    response_model=Page[ProjectSummary],
    summary="История проектов пользователя",
    description="Проекты текущего пользователя, сначала недавно изменённые.",
)
def list_projects(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status_filter: ProjectStatus | None = Query(
        default=None, alias="status", description="Фильтр по статусу"
    ),
    search: str | None = Query(
        default=None, max_length=100, description="Поиск по названию и описанию"
    ),
    user: dict = Depends(get_current_user),
    connection: sqlite3.Connection = Depends(get_connection),
) -> dict:
    projects, total = projects_repo.list_projects(
        connection,
        user_id=user["id"],
        limit=limit,
        offset=offset,
        status=status_filter.value if status_filter else None,
        search=search,
    )
    return {"items": projects, "total": total, "limit": limit, "offset": offset}


@router.get(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Проект по id",
    responses={404: {"description": "Проект не найден"}},
)
def get_project(
    project_id: int,
    user: dict = Depends(get_current_user),
    connection: sqlite3.Connection = Depends(get_connection),
) -> dict:
    return _get_owned_project(connection, project_id, user["id"])


@router.patch(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Изменить проект и/или сохранить новую версию исходных данных",
    description=(
        "Передача ``input_data`` создаёт новую версию в истории проекта и "
        "делает её актуальной."
    ),
    responses={404: {"description": "Проект не найден"}},
)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    user: dict = Depends(get_current_user),
    connection: sqlite3.Connection = Depends(get_connection),
) -> dict:
    _get_owned_project(connection, project_id, user["id"])

    changes = _metadata_changes(payload)
    if changes:
        projects_repo.update_project(connection, project_id, changes)

    if payload.input_data is not None:
        projects_repo.add_version(
            connection,
            project_id=project_id,
            input_data_json=payload.input_data.model_dump_json(),
            comment=payload.version_comment or "Обновление исходных данных",
            created_by=user["id"],
        )

    project = projects_repo.get_project(connection, project_id)
    assert project is not None
    return project


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить проект вместе с историей",
    responses={404: {"description": "Проект не найден"}},
)
def delete_project(
    project_id: int,
    user: dict = Depends(get_current_user),
    connection: sqlite3.Connection = Depends(get_connection),
) -> Response:
    _get_owned_project(connection, project_id, user["id"])
    projects_repo.delete_project(connection, project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{project_id}/history",
    response_model=Page[ProjectVersionRead],
    summary="История версий исходных данных",
    description="Версии отсортированы от новой к старой.",
    responses={404: {"description": "Проект не найден"}},
)
def list_history(
    project_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(get_current_user),
    connection: sqlite3.Connection = Depends(get_connection),
) -> dict:
    _get_owned_project(connection, project_id, user["id"])
    versions, total = projects_repo.list_versions(
        connection, project_id=project_id, limit=limit, offset=offset
    )
    return {"items": versions, "total": total, "limit": limit, "offset": offset}


@router.get(
    "/{project_id}/history/{version}",
    response_model=ProjectVersionRead,
    summary="Конкретная версия исходных данных",
    responses={404: {"description": "Проект или версия не найдены"}},
)
def get_history_version(
    project_id: int,
    version: int,
    user: dict = Depends(get_current_user),
    connection: sqlite3.Connection = Depends(get_connection),
) -> dict:
    _get_owned_project(connection, project_id, user["id"])
    item = projects_repo.get_version(connection, project_id, version)
    if item is None:
        raise NotFoundError("Версия не найдена")
    return item


@router.post(
    "/{project_id}/history",
    response_model=ProjectVersionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Сохранить версию исходных данных",
    description=(
        "Если ``input_data`` не передан, в историю попадает текущий набор "
        "данных проекта."
    ),
    responses={
        404: {"description": "Проект не найден"},
        409: {"description": "В проекте ещё нет исходных данных"},
    },
)
def save_version(
    project_id: int,
    payload: ProjectVersionCreate,
    user: dict = Depends(get_current_user),
    connection: sqlite3.Connection = Depends(get_connection),
) -> dict:
    project = _get_owned_project(connection, project_id, user["id"])

    if payload.input_data is not None:
        raw_input = payload.input_data.model_dump_json()
    else:
        if project["input_data"] is None:
            raise ConflictError(
                "В проекте ещё нет исходных данных", field="input_data"
            )
        raw_input = json.dumps(project["input_data"], ensure_ascii=False)

    return projects_repo.add_version(
        connection,
        project_id=project_id,
        input_data_json=raw_input,
        comment=payload.comment or "Сохранение исходных данных",
        created_by=user["id"],
    )


@router.post(
    "/{project_id}/history/{version}/restore",
    response_model=ProjectVersionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Восстановить версию исходных данных",
    description="Создаёт новую версию с данными указанной версии.",
    responses={404: {"description": "Проект или версия не найдены"}},
)
def restore_version(
    project_id: int,
    version: int,
    user: dict = Depends(get_current_user),
    connection: sqlite3.Connection = Depends(get_connection),
) -> dict:
    _get_owned_project(connection, project_id, user["id"])
    source = projects_repo.get_version(connection, project_id, version)
    if source is None:
        raise NotFoundError("Версия не найдена")

    return projects_repo.add_version(
        connection,
        project_id=project_id,
        input_data_json=json.dumps(source["input_data"], ensure_ascii=False),
        comment=f"Восстановление версии {version}",
        created_by=user["id"],
    )
