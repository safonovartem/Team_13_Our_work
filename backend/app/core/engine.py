"""Вычислительное ядро Tank Safety Engine — фасад ``run_engine``.

Единая точка входа. Оркестрирует:
1. UX-валидацию входных данных;
2. разрешение типоразмера по каталогу;
3. гидродинамический расчёт;
4. расчёт вариантов ограждений через фабрику стратегий;
5. оптимизацию и выбор рекомендуемого варианта.
"""
from __future__ import annotations

import math
from typing import List

from .catalog import TankCatalog, TankSpec
from .constants import (
    CLEARANCE_L_MAX,
    CLEARANCE_L_MIN,
    CREST_WIDTH_B_MAX,
    CREST_WIDTH_B_MIN,
    PLAIN_WALL_REL_HEIGHT_MAX,
    PLAIN_WALL_REL_HEIGHT_MIN,
    VALID_SCENARIO_KEYS,
)
from .contracts import InputData, ResultData, WallResult
from .exceptions import DomainRangeError
from .factory import WallFactory
from .hydrodynamics import WavePhysics
from .optimizer import BestPicker


def _validate_input(data: InputData) -> TankSpec:
    """UX-валидация входных параметров с понятными сообщениями.

    Parameters:
        data: Входные данные от пользователя.

    Returns:
        Типоразмер РВС из каталога.

    Raises:
        DomainRangeError: При выходе параметров за допустимые границы.
    """
    # 1. Объём резервуара — наличие в каталоге ГОСТ
    tank: TankSpec = TankCatalog.resolve(data.tank_volume)

    # 2. Межстенное расстояние l
    if not (CLEARANCE_L_MIN <= data.clearance_l <= CLEARANCE_L_MAX):
        raise DomainRangeError(
            f"Межстенное расстояние l = {data.clearance_l} м выходит за допустимый "
            f"диапазон [{CLEARANCE_L_MIN}…{CLEARANCE_L_MAX}] м."
        )

    # 3. Вылет козырька b
    if not (CREST_WIDTH_B_MIN <= data.crest_width_b <= CREST_WIDTH_B_MAX):
        raise DomainRangeError(
            f"Вылет горизонтального козырька b = {data.crest_width_b} м выходит за "
            f"допустимый диапазон [{CREST_WIDTH_B_MIN}…{CREST_WIDTH_B_MAX}] м."
        )
    if not data.scenarios:
        raise DomainRangeError(
            "Список сценариев расчёта не может быть пустым. "
            "Укажите хотя бы один вариант: 'plain' или 'gwk'."
        )
    # 4. Ключи сценариев
    for key in data.scenarios:
        if key not in VALID_SCENARIO_KEYS:
            raise DomainRangeError(
                f"Неизвестный сценарий '{key}'. "
                f"Допустимые значения: {', '.join(sorted(VALID_SCENARIO_KEYS))}."
            )

    # 5. Высота стенки без козырька (если задана явно)
    if data.plain_wall_height is not None:
        h0: float = tank.wall_height_m
        h_min: float = PLAIN_WALL_REL_HEIGHT_MIN * h0
        h_max: float = PLAIN_WALL_REL_HEIGHT_MAX * h0
        if not (h_min <= data.plain_wall_height <= h_max):
            raise DomainRangeError(
                f"Высота защитной стенки h_зс = {data.plain_wall_height} м выходит "
                f"за допустимый диапазон [{h_min:.1f}…{h_max:.1f}] м "
                f"(при h₀ = {h0} м, допустимое отношение h_зс/h₀ = "
                f"[{PLAIN_WALL_REL_HEIGHT_MIN}…{PLAIN_WALL_REL_HEIGHT_MAX}])."
            )

    return tank


def run_engine(data: InputData) -> ResultData:
    """Единая точка входа в вычислительное ядро Tank Safety Engine.

    Parameters:
        data: Входные параметры расчёта.

    Returns:
        Полный результат расчёта ``ResultData``.

    Raises:
        DomainRangeError: При выходе входных параметров за допустимые границы.
    """
    # 1. UX-валидация
    tank: TankSpec = _validate_input(data)

    h0: float = tank.wall_height_m
    d_vn: float = tank.diameter_m

    # 2. Объём воды V0 = π·d_вн²/4 · h0
    v0: float = math.pi * d_vn ** 2 / 4.0 * h0

    # 3. Гидродинамика
    wave_physics = WavePhysics(tank=tank, clearance_l=data.clearance_l)
    wave_data = wave_physics.calculate()

    # 4. Расчёт вариантов ограждений
    variants: List[WallResult] = []
    for scenario_key in data.scenarios:
        wall = WallFactory.create(scenario_key)
        result: WallResult = wall.calculate(
            tank=tank,
            clearance_l=data.clearance_l,
            crest_width_b=data.crest_width_b,
            plain_wall_height=data.plain_wall_height,
            liquid_volume_m3=v0,
        )
        variants.append(result)

    # 5. Оптимизация и выбор рекомендуемого
    variants, recommended = BestPicker.pick(variants)

    return ResultData(
        tank_volume=data.tank_volume,
        tank_diameter_m=d_vn,
        liquid_level_h0=h0,
        liquid_volume_m3=round(v0, 2),
        wave=wave_data,
        variants=variants,
        recommended_variant=recommended,
    )
