"""Стратегия расчёта: бетонная стенка с горизонтальным козырьком 90° (GWKWall).

Методика Буй Куанг Тиена:
- Формула (3.1): расчёт относительной высоты h_зс / h0 для ГВК.
- Перелив полностью исключён (Q = 0 %), второй рубеж не требуется.
"""
from __future__ import annotations

import math

from ..catalog import TankSpec
from ..constants import (
    CAPEX_K_GWK,
    CLEARANCE_L_MIN,
    CREST_WIDTH_B_MIN,
    FULL_CONTAINMENT_FACTOR,
    GWK_CREST_ANGLE_DEG,
    SAFETY_Q_PENALTY,
    TIEN_C0,
    TIEN_C1,
    TIEN_C2,
    TIEN_C3,
)
from ..contracts import EngineeringDetails, WallResult
from .base import BaseWall


class GWKWall(BaseWall):
    """Бетонная стенка с горизонтальным козырьком 90° (методика Тиена).

    Козырёк направлен внутрь к резервуару. Перелив полностью
    исключён (Q = 0 %), дополнительное ограждение не требуется.
    """

    def calculate(
        self,
        tank: TankSpec,
        clearance_l: float,
        crest_width_b: float,
        plain_wall_height: float | None,
        liquid_volume_m3: float,
    ) -> WallResult:
        """Выполнить расчёт по формуле (3.1) Буй Куанг Тиена.

        See Also:
            :class:`BaseWall` — описание параметров.
        """
        h0: float = tank.wall_height_m
        d_vn: float = tank.diameter_m
        r: float = d_vn / 2.0
        big_l: float = r + clearance_l

        # Относительная высота по формуле (3.1) Тиена
        rel_h: float = self._relative_height(d_vn, h0, clearance_l, crest_width_b)
        h_zs: float = rel_h * h0

        # Проверка статической ёмкости чаши: V_чаши = π · L² · h_зс
        v0: float = liquid_volume_m3
        basin_volume: float = math.pi * big_l ** 2 * h_zs
        is_sufficient: bool = basin_volume >= v0

        # Коррекция высоты при недостаточной ёмкости
        if not is_sufficient:
            h_zs = v0 / (math.pi * big_l ** 2)
            rel_h = h_zs / h0
            basin_volume = math.pi * big_l ** 2 * h_zs

        # Q = 0 % — козырёк полностью удерживает волну
        q_pct: float = 0.0
        v_overflow: float = 0.0

        # Нет второго рубежа
        l_dop: float = 0.0
        h_dop: float = 0.0

        # Экономия высоты
        height_savings: float = FULL_CONTAINMENT_FACTOR * h0 - h_zs

        # CAPEX: площадь бетона
        s_wall: float = math.pi * (d_vn + 2.0 * clearance_l) * h_zs
        s_crest: float = (
            math.pi * (d_vn + 2.0 * clearance_l - crest_width_b) * crest_width_b
        )
        capex_raw: float = s_wall + CAPEX_K_GWK * s_crest

        # Safety Score (Q = 0 → safety = 100)
        safety: float = max(0.0, 100.0 - SAFETY_Q_PENALTY * q_pct)

        # Feasibility Rank
        feasibility: float = self._feasibility(clearance_l, h_zs)

        # EngineeringDetails
        details = EngineeringDetails(
            formula_reference="Тиен, ф-ла (3.1)",
            dimensionless_params={
                "d_vn/h0": round(d_vn / h0, 4),
                "l/l_min": round(clearance_l / CLEARANCE_L_MIN, 4),
                "b/b_min": round(crest_width_b / CREST_WIDTH_B_MIN, 4),
                "L/R": round(big_l / r, 4),
                "h_zs/h0": round(rel_h, 4),
            },
            static_basin_volume_m3=round(basin_volume, 2),
            is_basin_capacity_sufficient=is_sufficient,
        )

        return WallResult(
            scenario_type="gwk",
            wall_height_m=round(h_zs, 4),
            relative_height=round(rel_h, 4),
            height_savings_m=round(height_savings, 4),
            crest_width_m=crest_width_b,
            crest_angle_deg=GWK_CREST_ANGLE_DEG,
            overflow_pct=round(q_pct, 4),
            overflow_volume_m3=round(v_overflow, 2),
            secondary_wall_dist_m=round(l_dop, 2),
            secondary_wall_height_m=round(h_dop, 2),
            safety_score=round(safety, 2),
            capex_raw=round(capex_raw, 2),
            capex_score=0.0,  # Будет нормализован в BestPicker
            feasibility_rank=round(feasibility, 2),
            engineering_details=details,
        )

    @staticmethod
    def _relative_height(
        d_vn: float,
        h0: float,
        clearance_l: float,
        crest_width_b: float,
    ) -> float:
        """Относительная высота стенки h_зс / h0 по формуле (3.1) Тиена.

        h_зс / h0 = 1.166 − 0.011·(d_вн/h0) − 0.078·(l/l_min) − 0.030·(b/b_min)

        Parameters:
            d_vn: Внутренний диаметр РВС, м.
            h0: Уровень воды (= высота стенки РВС), м.
            clearance_l: Межстенное расстояние l, м.
            crest_width_b: Вылет козырька b, м.

        Returns:
            Безразмерное отношение h_зс / h0.
        """
        return (
            TIEN_C0
            + TIEN_C1 * (d_vn / h0)
            + TIEN_C2 * (clearance_l / CLEARANCE_L_MIN)
            + TIEN_C3 * (crest_width_b / CREST_WIDTH_B_MIN)
        )