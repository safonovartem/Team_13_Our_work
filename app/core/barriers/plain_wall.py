"""Стратегия расчёта: бетонная стенка без козырька (PlainWall).

Методика А. С. Швыркова:
- Формула (4.1): доля перелива Q (%).
- Таблица 4.2: параметры бетонной стенки второго рубежа (l_доп, h_доп).
"""
from __future__ import annotations

import math

from ..catalog import TankSpec
from ..constants import (
    CAPEX_K_PLAIN,
    FULL_CONTAINMENT_FACTOR,
    CLEARANCE_L_MIN,
    CREST_WIDTH_B_MIN,
    SAFETY_Q_PENALTY,
    SECOND_BARRIER_TABLE,
    SHVYRKOV_A0,
    SHVYRKOV_A1,
    SHVYRKOV_A2,
)
from ..contracts import EngineeringDetails, WallResult
from .base import BaseWall


class PlainWall(BaseWall):
    """Бетонная защитная стенка без козырька (методика Швыркова).

    При h_зс = 1.1·h0 волна полностью удерживается (Q = 0 %).
    При h_зс < 1.1·h0 рассчитывается доля перелива Q и параметры
    дополнительного ограждения (второй рубеж) по табл. 4.2.
    """

    def calculate(
        self,
        tank: TankSpec,
        clearance_l: float,
        crest_width_b: float,
        plain_wall_height: float | None,
        liquid_volume_m3: float,
    ) -> WallResult:
        """Выполнить расчёт по методике Швыркова.

        See Also:
            :class:`BaseWall` — описание параметров.
        """
        h0: float = tank.wall_height_m
        d_vn: float = tank.diameter_m
        r: float = d_vn / 2.0
        big_l: float = r + clearance_l

        # Высота стенки
        if plain_wall_height is not None:
            h_zs: float = plain_wall_height
        else:
            h_zs = FULL_CONTAINMENT_FACTOR * h0  # 1.1 · h0

        # Относительная высота
        rel_h: float = h_zs / h0

        # Доля перелива Q (формула 4.1 Швыркова)
        q_pct: float = self._overflow_q(big_l, r, rel_h)

        # Объём воды и перелива
        v0: float = liquid_volume_m3
        v_overflow: float = v0 * q_pct / 100.0

        # Параметры второго рубежа
        l_dop: float = 0.0
        h_dop: float = 0.0
        if q_pct > 0.0:
            l_dop, h_dop = self._second_barrier_params(rel_h)

        # Проверка статической ёмкости чаши: V_чаши = π · L² · h_зс
        basin_volume: float = math.pi * big_l ** 2 * h_zs
        is_sufficient: bool = basin_volume >= v0

        # Коррекция высоты при недостаточной ёмкости чаши
        if not is_sufficient:
            h_zs = v0 / (math.pi * big_l ** 2)
            rel_h = h_zs / h0
            basin_volume = math.pi * big_l ** 2 * h_zs
            # Пересчёт Q после коррекции
            q_pct = self._overflow_q(big_l, r, rel_h)
            v_overflow = v0 * q_pct / 100.0
            if q_pct > 0.0:
                l_dop, h_dop = self._second_barrier_params(rel_h)
            else:
                l_dop, h_dop = 0.0, 0.0

        # Экономия высоты
        height_savings: float = FULL_CONTAINMENT_FACTOR * h0 - h_zs

        # CAPEX: площадь бетона
        s_wall: float = math.pi * (d_vn + 2.0 * clearance_l) * h_zs
        s_crest: float = 0.0  # нет козырька
        s_secondary: float = 0.0
        if q_pct > 0.0 and l_dop > 0.0:
            s_secondary = (
                math.pi * (d_vn + 2.0 * clearance_l + 2.0 * l_dop) * h_dop
            )
        capex_raw: float = s_wall + CAPEX_K_PLAIN * s_crest + s_secondary

        # Safety Score
        safety: float = max(0.0, 100.0 - SAFETY_Q_PENALTY * q_pct)

        # Feasibility Rank
        feasibility: float = self._feasibility(clearance_l, h_zs)

        # EngineeringDetails
        details = EngineeringDetails(
            formula_reference="Швырков, ф-ла (4.1), табл. 4.2",
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
            scenario_type="plain",
            wall_height_m=round(h_zs, 4),
            relative_height=round(rel_h, 4),
            height_savings_m=round(height_savings, 4),
            crest_width_m=0.0,
            crest_angle_deg=0.0,
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
    def _overflow_q(big_l: float, r: float, rel_h: float) -> float:
        """Доля перелива Q (%) по формуле (4.1) Швыркова.

        Q = max(0, 89.8017 − 17.1986·(L/R) − 68.899·√(h_зс/h0))

        Parameters:
            big_l: Расстояние от центра резервуара до стенки L = R + l, м.
            r: Радиус резервуара R = d_вн / 2, м.
            rel_h: Относительная высота h_зс / h0.

        Returns:
            Доля перелива Q в процентах (≥ 0).
        """
        if rel_h <= 0:
            return 100.0
        q: float = (
            SHVYRKOV_A0
            + SHVYRKOV_A1 * (big_l / r)
            + SHVYRKOV_A2 * math.sqrt(rel_h)
        )
        return max(0.0, q)

    @staticmethod
    def _second_barrier_params(rel_h: float) -> tuple[float, float]:
        """Параметры бетонной стенки второго рубежа (табл. 4.2 Швыркова).

        Кусочно-линейная интерполяция по h_зс / h0.

        Parameters:
            rel_h: Относительная высота h_зс / h0.

        Returns:
            Кортеж (l_доп, h_доп), м.
        """
        table = SECOND_BARRIER_TABLE

        # Если rel_h > 1.0 (и Q > 0) — безопасные значения
        if rel_h >= 1.0:
            return table[-1][1], table[-1][2]  # (5.0, 1.5)

        # Если rel_h ≤ минимальной точки таблицы
        if rel_h <= table[0][0]:
            return table[0][1], table[0][2]

        # Кусочно-линейная интерполяция
        for i in range(len(table) - 1):
            x0, l0, h0_ = table[i]
            x1, l1, h1_ = table[i + 1]
            if x0 <= rel_h <= x1:
                t: float = (rel_h - x0) / (x1 - x0)
                l_interp: float = l0 + t * (l1 - l0)
                h_interp: float = h0_ + t * (h1_ - h0_)
                return l_interp, h_interp

        # Fallback (не должен достигаться)
        return table[-1][1], table[-1][2]
