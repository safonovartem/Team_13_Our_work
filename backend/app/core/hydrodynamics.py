"""Гидродинамический модуль: критерии подобия и траектория волны.

Класс ``WavePhysics`` рассчитывает:
- начальную скорость истечения u0;
- критерии Фруда (Fr), Струхаля (Sh) и Рейнольдса (Re);
- пересчёт модельных величин в натурные через масштабный коэффициент λ_l;
- детерминированный список точек ``WavePoint`` для 2D-анимации на Canvas.
"""
from __future__ import annotations

import math
from typing import List

from .catalog import TankSpec
from .constants import (
    GRAVITY,
    WATER_KINEMATIC_VISCOSITY,
    WAVE_TRAJECTORY_POINTS,
    MIN_MODEL_VELOCITY,
    RE_TURBULENT_THRESHOLD,
)
from .contracts import WaveData, WavePoint

from .exceptions import DomainRangeError


class WavePhysics:
    """Физический калькулятор волны при квазимгновенном разрушении стенки РВС.

    Parameters:
        tank: Типоразмер резервуара из каталога.
        clearance_l: Межстенное расстояние l, м.
    """

    def __init__(self, tank: TankSpec, clearance_l: float) -> None:
        self._tank: TankSpec = tank
        self._clearance_l: float = clearance_l

    def calculate(self) -> WaveData:
        """Выполнить полный гидродинамический расчёт.

        Returns:
            Объект ``WaveData`` с критериями подобия и траекторией волны.
        """
        h0: float = self._tank.wall_height_m
        lam: int = self._tank.scale_factor

        h0_model: float = self._tank.model_water_level_m
        u_model: float = math.sqrt(2.0 * GRAVITY * h0_model) if h0_model > 0 else 0.0
        re_model: float = (
            u_model * h0_model / WATER_KINEMATIC_VISCOSITY if h0_model > 0 else 0.0
        )
        if u_model <= MIN_MODEL_VELOCITY or re_model < RE_TURBULENT_THRESHOLD:
            raise DomainRangeError(
                f"Нарушены условия гидродинамического подобия модели: "
                f"u_мод = {u_model:.3f} м/с (требуется > {MIN_MODEL_VELOCITY} м/с), "
                f"Re_мод = {re_model:.0f} (требуется ≥ {RE_TURBULENT_THRESHOLD:.0f})."
            )

        # Начальная скорость истечения (натурная)
        u0: float = math.sqrt(2.0 * GRAVITY * h0)

        # Критерии подобия (натурные)
        froude: float = u0 ** 2 / (GRAVITY * h0)  # Fr = u² / (g·h)
        reynolds: float = u0 * h0 / WATER_KINEMATIC_VISCOSITY  # Re = u·h / ν

        # Характерное время пробега волны через зазор
        t_travel: float = self._clearance_l / u0 if u0 > 0 else 0.0
        strouhal: float = u0 * t_travel / h0 if h0 > 0 else 0.0  # Sh = u·t / h

        # Генерация траектории волны (натурные координаты)
        trajectory: List[WavePoint] = self._generate_trajectory(u0, h0)

        return WaveData(
            initial_velocity_ms=round(u0, 4),
            froude_number=round(froude, 4),
            strouhal_number=round(strouhal, 6),
            reynolds_number=round(reynolds, 1),
            scale_factor=lam,
            trajectory=trajectory,
        )

    def _generate_trajectory(self, u0: float, h0: float) -> List[WavePoint]:
        """Генерация детерминированного списка точек фронта волны.

        Участок: x ∈ [0, l].
        Модель «плотина» (dam-break): x(t) ≈ u0·t (линейное приближение фронта),
        высота потока убывает по корневой зависимости.

        Parameters:
            u0: Начальная скорость истечения, м/с.
            h0: Уровень воды, м.

        Returns:
            Список ``WavePoint`` из ``WAVE_TRAJECTORY_POINTS`` точек.
        """
        points: List[WavePoint] = []
        n: int = WAVE_TRAJECTORY_POINTS
        l: float = self._clearance_l

        if u0 <= 0 or l <= 0:
            return points

        for i in range(n):
            # Равномерная дискретизация по расстоянию
            x: float = l * i / (n - 1)
            t: float = x / u0
            # Высота потока: убывает с расстоянием (приближение Риттера)
            # h(x, t) ≈ h0 · (1 - x / (2·u0·t))² при x ≤ 2·u0·t
            # Упрощённая модель для визуализации:
            ratio: float = x / l
            wave_h: float = h0 * (1.0 - ratio * 0.5)

            points.append(
                WavePoint(
                    time_s=round(t, 6),
                    distance_m=round(x, 4),
                    wave_height_m=round(wave_h, 4),
                )
            )

        return points
