"""Каталог типоразмеров вертикальных стальных резервуаров (РВС) по ГОСТ.

Справочник ``TankCatalog`` реализован как Static Repository / Resolver.
Данные основаны на диссертациях Швыркова и Тиена и могут быть обновлены
при получении актуальной таблицы ГОСТ.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from .exceptions import DomainRangeError


@dataclass(frozen=True)
class TankSpec:
    """Типоразмер одного РВС.

    Attributes:
        volume_m3: Номинальный объём, м³.
        diameter_m: Внутренний диаметр d_вн, м.
        wall_height_m: Высота стенки h_ст (= h0 при максимальном заполнении), м.
        scale_factor: Масштабный коэффициент λ_l для моделирования.
        model_water_level_m: Уровень воды в модели h_{0,мод}, м.
    """

    volume_m3: int
    diameter_m: float
    wall_height_m: float
    scale_factor: int
    model_water_level_m: float


# ──────────────────────────────────────────────────────────────────────────────
# Справочная таблица типоразмеров (табл. 3.1/4.1 Швыркова, табл. 2.3/3.1 Тиена)
# ──────────────────────────────────────────────────────────────────────────────

TANK_CATALOG: Dict[int, TankSpec] = {
    700: TankSpec(
        volume_m3=700,
        diameter_m=10.43,
        wall_height_m=9.0,
        scale_factor=30,
        model_water_level_m=0.30,
    ),
    2000: TankSpec(
        volume_m3=2000,
        diameter_m=15.18,
        wall_height_m=12.0,
        scale_factor=43,
        model_water_level_m=0.28,
    ),
    5000: TankSpec(
        volume_m3=5000,
        diameter_m=20.92,
        wall_height_m=15.0,
        scale_factor=60,
        model_water_level_m=0.25,
    ),
    10000: TankSpec(
        volume_m3=10000,
        diameter_m=28.50,
        wall_height_m=18.0,
        scale_factor=81,
        model_water_level_m=0.22,
    ),
    20000: TankSpec(
        volume_m3=20000,
        diameter_m=39.90,
        wall_height_m=18.0,
        scale_factor=114,
        model_water_level_m=0.16,
    ),
    30000: TankSpec(
        volume_m3=30000,
        diameter_m=45.60,
        wall_height_m=18.0,
        scale_factor=130,
        model_water_level_m=0.14,
    ),
}


class TankCatalog:
    """Static Repository для поиска типоразмера РВС по номинальному объёму.

    Пример использования::

        spec = TankCatalog.resolve(5000)  # → TankSpec(5000, 20.92, 15.0, 60, 0.25)
    """

    @staticmethod
    def resolve(volume: int) -> TankSpec:
        """Найти типоразмер по номинальному объёму.

        Parameters:
            volume: Номинальный объём РВС, м³.

        Returns:
            Спецификация резервуара ``TankSpec``.

        Raises:
            DomainRangeError: Если объём отсутствует в каталоге ГОСТ.
        """
        spec: Optional[TankSpec] = TANK_CATALOG.get(volume)
        if spec is None:
            available: str = ", ".join(str(v) for v in sorted(TANK_CATALOG.keys()))
            raise DomainRangeError(
                f"Номинальный объём РВС = {volume} м³ отсутствует в каталоге ГОСТ. "
                f"Допустимые значения: {available} м³."
            )
        return spec

    @staticmethod
    def available_volumes() -> list[int]:
        """Список доступных номинальных объёмов, м³."""
        return sorted(TANK_CATALOG.keys())
