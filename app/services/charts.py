"""Подготовка данных для графиков (Chart.js).

Возвращаемые структуры совпадают с типами фронтенда:

    ChartBlock  { title, datasets: [{ label, data: [[x, y], ...] }] }
    ChartDataset { label, data }

График перелива использует ту же регрессию Швыркова (4.1), что и
``app.core.barriers.plain_wall.PlainWall``; коэффициенты берутся из
``app.core.constants``, чтобы не расходиться с вычислительным ядром.
"""

from __future__ import annotations

import math

from app.core.catalog import TankSpec
from app.core.constants import (
    CLEARANCE_L_MAX,
    CLEARANCE_L_MIN,
    PLAIN_WALL_REL_HEIGHT_MAX,
    PLAIN_WALL_REL_HEIGHT_MIN,
    SHVYRKOV_A0,
    SHVYRKOV_A1,
    SHVYRKOV_A2,
)
from app.core.contracts import WaveData
from app.core.exceptions import DomainRangeError
from app.schemas.calculations import (
    ChartAxis,
    ChartBlock,
    ChartDataset,
)

DEFAULT_CLEARANCE_GRID: tuple[float, ...] = (1.5, 2.0, 2.5, 3.0)
DEFAULT_HEIGHT_RATIOS: tuple[float, ...] = tuple(
    round(0.4 + 0.05 * index, 2) for index in range(15)
)  # 0.40, 0.45, …, 1.10

OVERFLOW_CHART_TITLE = "Доля перелива от высоты стенки"
WAVE_DISTANCE_CHART_TITLE = "Траектория фронта волны"
WAVE_HEIGHT_CHART_TITLE = "Высота потока вдоль пути растекания"


def validate_clearance(value: float) -> float:
    if not (CLEARANCE_L_MIN <= value <= CLEARANCE_L_MAX):
        raise DomainRangeError(
            f"Межстенное расстояние l = {value} м выходит за допустимый "
            f"диапазон [{CLEARANCE_L_MIN}…{CLEARANCE_L_MAX}] м."
        )
    return value


def validate_height_ratio(value: float) -> float:
    if not (PLAIN_WALL_REL_HEIGHT_MIN <= value <= PLAIN_WALL_REL_HEIGHT_MAX):
        raise DomainRangeError(
            f"Относительная высота h_зс/h0 = {value} выходит за допустимый "
            f"диапазон [{PLAIN_WALL_REL_HEIGHT_MIN}…{PLAIN_WALL_REL_HEIGHT_MAX}]."
        )
    return value


def overflow_pct(tank: TankSpec, clearance_l: float, relative_height: float) -> float:
    """Доля перелива Q, %, по формуле (4.1) Швыркова."""
    radius = tank.diameter_m / 2.0
    big_l = radius + clearance_l
    if relative_height <= 0:
        return 100.0
    value = (
        SHVYRKOV_A0
        + SHVYRKOV_A1 * (big_l / radius)
        + SHVYRKOV_A2 * math.sqrt(relative_height)
    )
    return max(0.0, value)


def build_overflow_chart(
    tank: TankSpec,
    clearance_values: list[float] | None = None,
    height_ratios: list[float] | None = None,
) -> ChartBlock:
    """График «доля перелива от относительной высоты стенки».

    Пример набора данных (для РВС-5000 и l = 3.0 м)::

        {"label": "l = 3.0 м",
         "data": [[0.7, 10.03], [0.97, 0.0], [1.1, 0.0]]}
    """
    clearances = clearance_values or list(DEFAULT_CLEARANCE_GRID)
    ratios = sorted(
        {round(validate_height_ratio(ratio), 4)
         for ratio in (height_ratios or DEFAULT_HEIGHT_RATIOS)}
    )

    datasets: list[ChartDataset] = []
    for clearance in clearances:
        validate_clearance(clearance)
        datasets.append(
            ChartDataset(
                label=f"l = {clearance:.1f} м",
                data=[
                    [
                        ratio,
                        round(
                            overflow_pct(tank, clearance, ratio),
                            2,
                        ),
                    ]
                    for ratio in ratios
                ],
            )
        )

    return ChartBlock(
        title=OVERFLOW_CHART_TITLE,
        datasets=datasets,
        x_axis=ChartAxis(title="Относительная высота стенки h_зс / h0"),
        y_axis=ChartAxis(title="Доля перелива", unit="%"),
    )


def build_wave_charts(
    wave: WaveData, clearance_l: float, *, title_suffix: str | None = None
) -> list[ChartBlock]:
    """Графики траектории волны: расстояние и высота потока."""
    validate_clearance(clearance_l)
    label = f"l = {clearance_l:.1f} м"
    if title_suffix:
        label = f"{label} ({title_suffix})"

    distance_points = [
        [point.time_s, point.distance_m] for point in wave.trajectory
    ]
    height_points = [
        [point.distance_m, point.wave_height_m] for point in wave.trajectory
    ]

    return [
        ChartBlock(
            title=WAVE_DISTANCE_CHART_TITLE,
            datasets=[ChartDataset(label=label, data=distance_points)],
            x_axis=ChartAxis(title="Время", unit="с"),
            y_axis=ChartAxis(title="Расстояние от стенки", unit="м"),
        ),
        ChartBlock(
            title=WAVE_HEIGHT_CHART_TITLE,
            datasets=[ChartDataset(label=label, data=height_points)],
            x_axis=ChartAxis(title="Расстояние от стенки", unit="м"),
            y_axis=ChartAxis(title="Высота потока", unit="м"),
        ),
    ]


def calculation_clearance_values(current_l: float) -> list[float]:
    """Набор кривых для графика в результате расчёта."""
    values = list(DEFAULT_CLEARANCE_GRID)
    current = round(current_l, 2)
    if current not in values:
        values.append(current)
    return sorted(values)
