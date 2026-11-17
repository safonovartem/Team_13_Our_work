"""История расчётов проекта (требует авторизации).

Расчёт привязывается к проекту, но не к конкретной версии исходных данных:
один и тот же набор данных можно рассчитать с разными параметрами ядра.
"""

from __future__ import annotations

import json
import sqlite3

from fastapi import APIRouter, Depends, Query, Response, status

from app.deps import get_connection, get_current_user
from app.errors import NotFoundError
from app.repositories import calculations as calculations_repo
from app.schemas.calculations import (
    CalculationInput,
    CalculationResponse,
    CalculationSummary,
    ChartCollection,
    FrontendFormValues,
    SavedCalculation,
)
from app.schemas.common import Page
from app.services import calculations as calculation_service
from app.services.project_access import get_owned_project

router = APIRouter(prefix="/projects", tags=["История расчётов проекта"])


def _charts_json(response: CalculationResponse) -> str:
    return json.dumps(
        [chart.model_dump(mode="json", by_alias=True) for chart in response.charts],
        ensure_ascii=False,
    )


def _save(
    conn: sqlite3.Connection,
    *,
    project_id: int,
    user_id: int,
    response: CalculationResponse,
    form: FrontendFormValues | None = None,
) -> dict:
    return calculations_repo.create_calculation(
        conn,
        project_id=project_id,
        user_id=user_id,
        input_data_json=response.input.model_dump_json(),
        result_data_json=response.result.model_dump_json(),
        charts_json=_charts_json(response),
        recommended_variant=response.recommended_variant,
        form_data_json=(
            json.dumps(form.model_dump(mode="json", by_alias=True), ensure_ascii=False)
            if form is not None
            else None
        ),
    )


def _get_record(
    conn: sqlite3.Connection, project_id: int, calculation_id: int
) -> dict:
    record = calculations_repo.get_calculation(conn, calculation_id)
    if record is None or record["project_id"] != project_id:
        raise NotFoundError("Расчёт не найден")
    return record


@router.post(
    "/{project_id}/calculations",
    response_model=SavedCalculation,
    status_code=status.HTTP_201_CREATED,
    summary="Выполнить и сохранить расчёт проекта",
    responses={
        404: {"description": "Проект не найден"},
        422: {"description": "Некорректные параметры"},
    },
)
def create_calculation(
    project_id: int,
    payload: CalculationInput,
    user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_connection),
) -> SavedCalculation:
    get_owned_project(conn, project_id, user["id"])
    response = calculation_service.run_calculation(payload)
    record = _save(
        conn, project_id=project_id, user_id=user["id"], response=response
    )
    return calculation_service.saved_calculation_from_record(record)


@router.post(
    "/{project_id}/calculations/from-form",
    response_model=SavedCalculation,
    status_code=status.HTTP_201_CREATED,
    summary="Рассчитать по форме главной страницы и сохранить в проект",
    responses={
        404: {"description": "Проект не найден"},
        422: {"description": "Некорректные параметры"},
    },
)
def create_calculation_from_form(
    project_id: int,
    payload: FrontendFormValues,
    user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_connection),
) -> SavedCalculation:
    get_owned_project(conn, project_id, user["id"])
    response = calculation_service.run_calculation_from_form(payload)
    record = _save(
        conn,
        project_id=project_id,
        user_id=user["id"],
        response=response,
        form=payload,
    )
    return calculation_service.saved_calculation_from_record(record)


@router.get(
    "/{project_id}/calculations",
    response_model=Page[CalculationSummary],
    summary="История расчётов проекта",
    responses={404: {"description": "Проект не найден"}},
)
def list_calculations(
    project_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_connection),
) -> dict:
    get_owned_project(conn, project_id, user["id"])
    records, total = calculations_repo.list_calculations(
        conn, project_id=project_id, limit=limit, offset=offset
    )
    return {
        "items": [
            calculation_service.calculation_summary_from_record(record)
            for record in records
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get(
    "/{project_id}/calculations/{calculation_id}",
    response_model=SavedCalculation,
    summary="Сохранённый расчёт",
    responses={404: {"description": "Проект или расчёт не найдены"}},
)
def get_calculation(
    project_id: int,
    calculation_id: int,
    user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_connection),
) -> SavedCalculation:
    get_owned_project(conn, project_id, user["id"])
    record = _get_record(conn, project_id, calculation_id)
    return calculation_service.saved_calculation_from_record(record)


@router.get(
    "/{project_id}/calculations/{calculation_id}/charts",
    response_model=ChartCollection,
    summary="Графики сохранённого расчёта",
    description="Возвращает ``charts`` в формате, готовом для Chart.js.",
    responses={404: {"description": "Проект или расчёт не найдены"}},
)
def get_calculation_charts(
    project_id: int,
    calculation_id: int,
    user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_connection),
) -> ChartCollection:
    get_owned_project(conn, project_id, user["id"])
    record = _get_record(conn, project_id, calculation_id)
    return calculation_service.charts_from_record(record)


@router.delete(
    "/{project_id}/calculations/{calculation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить сохранённый расчёт",
    responses={404: {"description": "Проект или расчёт не найдены"}},
)
def delete_calculation(
    project_id: int,
    calculation_id: int,
    user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_connection),
) -> Response:
    get_owned_project(conn, project_id, user["id"])
    _get_record(conn, project_id, calculation_id)
    calculations_repo.delete_calculation(conn, calculation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
