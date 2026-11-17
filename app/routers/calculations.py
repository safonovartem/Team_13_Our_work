"""Публичные эндпоинты расчёта (без сохранения в проект).

Расчёты выполняются вычислительным ядром ``app.core`` (ветка
``feature/backend-calculations``). Ответ содержит как «сырой» результат
ядра, так и готовые для интерфейса блоки ``variants``/``charts``.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.calculations import (
    CalculationInput,
    CalculationResponse,
    FrontendFormValues,
)
from app.services import calculations as calculation_service

router = APIRouter(prefix="/calculations", tags=["Расчёты"])


@router.post(
    "",
    response_model=CalculationResponse,
    summary="Выполнить расчёт ограждения",
    description=(
        "Принимает параметры вычислительного ядра. Возвращает результат "
        "``result``, блоки вариантов ``variants`` (как в ``ResultBlock`` "
        "фронтенда) и графики ``charts`` (Chart.js, ``data: [[x, y], ...]``)."
    ),
    responses={422: {"description": "Параметр вне границ применимости формул"}},
)
def calculate(payload: CalculationInput) -> CalculationResponse:
    return calculation_service.run_calculation(payload)


@router.post(
    "/from-form",
    response_model=CalculationResponse,
    summary="Расчёт по значениям формы главной страницы",
    description=(
        "Принимает ``FormValues`` фронтенда (camelCase). Объём РВС берётся "
        "из ``objectType`` (например, «РВС-5000 · 5 000 м³») или "
        "``objectVolume``; ``clearanceL``/``crestWidthB`` необязательны."
    ),
    responses={422: {"description": "Не удалось определить объём РВС или параметр вне диапазона"}},
)
def calculate_from_form(payload: FrontendFormValues) -> CalculationResponse:
    return calculation_service.run_calculation_from_form(payload)
