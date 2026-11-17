"""Эндпоинты графиков (Chart.js) для главной страницы и отчётов.

Формат ответа совпадает с типами фронтенда::

    {"title": "...", "datasets": [{"label": "l = 3.0 м", "data": [[x, y], ...]}]}

Данные строятся по тем же формулам и коэффициентам, что и в вычислительном
ядре (``app.core``), поэтому график и результат расчёта не расходятся.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.catalog import TankCatalog
from app.core.hydrodynamics import WavePhysics
from app.schemas.calculations import (
    ChartBlock,
    ChartCollection,
    ChartsRequest,
    OverflowChartRequest,
    WaveChartRequest,
)
from app.services.charts import (
    build_overflow_chart,
    build_wave_charts,
    validate_clearance,
)

router = APIRouter(prefix="/charts", tags=["Графики"])


@router.post(
    "/overflow",
    response_model=ChartBlock,
    summary="График доли перелива от высоты стенки",
    description=(
        "Кривые Q(h_зс/h0) по формуле (4.1) Швыркова для набора значений l. "
        "Пример набора: «datasets»: [{\"label\": \"l = 3.0 м\", "
        "\"data\": [[0.7, 10.03], [0.97, 0.0], [1.1, 0.0]]}]."
    ),
    responses={422: {"description": "Объём РВС или параметры вне диапазона"}},
)
def overflow_chart(payload: OverflowChartRequest) -> ChartBlock:
    tank = TankCatalog.resolve(payload.tank_volume)
    return build_overflow_chart(
        tank,
        clearance_values=payload.clearance_values,
        height_ratios=payload.height_ratios,
    )


@router.post(
    "/wave",
    response_model=ChartCollection,
    summary="Графики траектории волны",
    description=(
        "Две кривые: расстояние фронта от времени и высота потока от "
        "расстояния. Точки берутся из ``WavePhysics`` вычислительного ядра."
    ),
    responses={422: {"description": "Объём РВС или параметры вне диапазона"}},
)
def wave_charts(payload: WaveChartRequest) -> ChartCollection:
    tank = TankCatalog.resolve(payload.tank_volume)
    validate_clearance(payload.clearance_l)
    wave = WavePhysics(tank=tank, clearance_l=payload.clearance_l).calculate()
    return ChartCollection(charts=build_wave_charts(wave, payload.clearance_l))


@router.post(
    "",
    response_model=ChartCollection,
    summary="Полный набор графиков",
    description="График перелива и два графика траектории волны.",
    responses={422: {"description": "Объём РВС или параметры вне диапазона"}},
)
def all_charts(payload: ChartsRequest) -> ChartCollection:
    tank = TankCatalog.resolve(payload.tank_volume)
    validate_clearance(payload.clearance_l)

    overflow = build_overflow_chart(
        tank, clearance_values=payload.clearance_values
    )
    wave = WavePhysics(tank=tank, clearance_l=payload.clearance_l).calculate()
    return ChartCollection(
        charts=[overflow, *build_wave_charts(wave, payload.clearance_l)]
    )
