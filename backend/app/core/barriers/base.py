"""Абстрактный базовый класс стратегии расчёта защитного ограждения.

Паттерн Strategy: все стратегии (PlainWall, GWKWall, в будущем — NVKWall)
реализуют единый контракт ``calculate()``, что позволяет добавлять новые
типы ограждений без изменения ``engine.py``.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..catalog import TankSpec
from ..contracts import WallResult
from ..constants import (
    CLEARANCE_L_MIN,
    FEASIBILITY_MAX_HEIGHT,
    FEASIBILITY_MAX_SCORE,
    FEASIBILITY_MIN_HEIGHT,
    FEASIBILITY_OPTIMAL_CLEARANCE,
)

class BaseWall(ABC):
    """Абстрактный базовый класс стратегии расчёта защитной стенки.

    Подклассы обязаны реализовать метод ``calculate``.
    """

    @abstractmethod
    def calculate(
        self,
        tank: TankSpec,
        clearance_l: float,
        crest_width_b: float,
        plain_wall_height: float | None,
        liquid_volume_m3: float,
    ) -> WallResult:
        """Рассчитать параметры защитного ограждения.

        Parameters:
            tank: Типоразмер РВС из каталога.
            clearance_l: Межстенное расстояние l, м.
            crest_width_b: Вылет козырька b, м.
            plain_wall_height: Заданная вручную высота стенки, м (или None).
            liquid_volume_m3: Объём воды в резервуаре V0, м³.

        Returns:
            Объект ``WallResult`` с полным набором расчётных параметров.
        """
        ...

    @staticmethod
    def _feasibility(clearance_l: float, h_zs: float) -> float:
        """Индекс конструктивной реализуемости [0…100].

        Учитывает удобство прохода в межстенном зазоре (l ≥ 1.8 м)
        и общую высоту бетонной стенки.
        """
        if clearance_l >= FEASIBILITY_OPTIMAL_CLEARANCE:
            gap_score: float = FEASIBILITY_MAX_SCORE
        else:
            gap_score = (
                    FEASIBILITY_MAX_SCORE
                    * (clearance_l - CLEARANCE_L_MIN)
                    / (FEASIBILITY_OPTIMAL_CLEARANCE - CLEARANCE_L_MIN)
            )
            gap_score = max(0.0, gap_score)

        if h_zs <= FEASIBILITY_MIN_HEIGHT:
            height_score: float = FEASIBILITY_MAX_SCORE
        elif h_zs >= FEASIBILITY_MAX_HEIGHT:
            height_score = 0.0
        else:
            height_score = FEASIBILITY_MAX_SCORE * (
                    1.0
                    - (h_zs - FEASIBILITY_MIN_HEIGHT)
                    / (FEASIBILITY_MAX_HEIGHT - FEASIBILITY_MIN_HEIGHT)
            )

        return round(min(100.0, gap_score + height_score), 2)