"""DTO (Data Transfer Objects) вычислительного ядра Tank Safety Engine.

Все контракты данных реализованы как frozen-dataclass для обеспечения
неизменяемости и прозрачности. Имена полей и типы строго соответствуют
разделу 5 спецификации `.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class InputData:
    """Входные параметры расчёта от пользователя.

    Attributes:
        tank_volume: Номинальный объём РВС по ГОСТ, м³ (700…30 000).
        clearance_l: Межстенное расстояние l, м [1.5…3.0].
        crest_width_b: Вылет горизонтального козырька b, м [0.5…1.5].
        plain_wall_height: Высота стенки без козырька, м.
            По умолчанию None → автоматический расчёт как 1.1·h0.
        scenarios: Ключи запрашиваемых сценариев (``"plain"``, ``"gwk"``).
    """

    tank_volume: int
    clearance_l: float
    crest_width_b: float
    plain_wall_height: Optional[float] = None
    scenarios: List[str] = field(default_factory=lambda: ["plain", "gwk"])


@dataclass(frozen=True)
class WavePoint:
    """Точка траектории фронта волны для 2D-анимации на Canvas.

    Attributes:
        time_s: Натурное время, с.
        distance_m: Координата фронта волны от стенки РВС, м.
        wave_height_m: Высота потока, м.
    """

    time_s: float
    distance_m: float
    wave_height_m: float


@dataclass(frozen=True)
class WaveData:
    """Гидродинамические характеристики и траектория волны.

    Attributes:
        initial_velocity_ms: Начальная скорость истечения u0, м/с.
        froude_number: Критерий Фруда Fr (безразмерный).
        strouhal_number: Критерий Струхаля Sh (безразмерный).
        reynolds_number: Критерий Рейнольдса Re (для воды при 20 °C).
        scale_factor: Масштабный коэффициент моделирования λ_l.
        trajectory: Координаты волны для 2D-анимации.
    """

    initial_velocity_ms: float
    froude_number: float
    strouhal_number: float
    reynolds_number: float
    scale_factor: int
    trajectory: List[WavePoint]


@dataclass(frozen=True)
class EngineeringDetails:
    """Прозрачные промежуточные параметры для верификации инженером-проектировщиком.

    Attributes:
        formula_reference: Ссылка на уравнение диссертации
            (напр. ``"Тиен, ф-ла 3.1"``).
        dimensionless_params: Безразмерные комплексы:
            ``d_vn/h0``, ``l/l_min``, ``b/b_min``, ``L/R``, ``h_zs/h0``.
        static_basin_volume_m3: Статический объём чаши V_чаши, м³.
        is_basin_capacity_sufficient: Выполнение условия V_чаши ≥ V0.
    """

    formula_reference: str
    dimensionless_params: Dict[str, float]
    static_basin_volume_m3: float
    is_basin_capacity_sufficient: bool


@dataclass(frozen=True)
class WallResult:
    """Результат расчёта одного варианта защитного ограждения.

    Attributes:
        scenario_type: Ключ стратегии: ``"plain"`` | ``"gwk"``.
        wall_height_m: Итоговая высота бетонной стенки h_зс, м.
        relative_height: Относительная высота h_зс / h0.
        height_savings_m: Экономия высоты Δh = 1.1·h0 − h_зс, м.
        crest_width_m: Вылет козырька b, м (0.0 для plain).
        crest_angle_deg: Угол козырька, ° (0.0 для plain, 90.0 для gwk).
        overflow_pct: Доля перелива Q, %.
        overflow_volume_m3: Объём перелива V_пер, м³.
        secondary_wall_dist_m: Расстояние до стенки второго рубежа l_доп, м.
        secondary_wall_height_m: Высота стенки второго рубежа h_доп, м.
        safety_score: Индекс безопасности [0…100].
        capex_raw: Приведённая площадь бетонных конструкций, м².
        capex_score: Нормализованный индекс экономичности [0…100].
        feasibility_rank: Индекс конструктивной реализуемости [0…100].
        engineering_details: Детализация для проектировщика.
    """

    scenario_type: str
    wall_height_m: float
    relative_height: float
    height_savings_m: float
    crest_width_m: float
    crest_angle_deg: float
    overflow_pct: float
    overflow_volume_m3: float
    secondary_wall_dist_m: float
    secondary_wall_height_m: float
    safety_score: float
    capex_raw: float
    capex_score: float
    feasibility_rank: float
    engineering_details: EngineeringDetails


@dataclass(frozen=True)
class ResultData:
    """Полный результат работы вычислительного ядра.

    Attributes:
        tank_volume: Объём РВС, м³.
        tank_diameter_m: Внутренний диаметр d_вн, м.
        liquid_level_h0: Уровень воды h0 (= высота стенки РВС), м.
        liquid_volume_m3: Фактический объём воды V0, м³.
        wave: Данные гидродинамики и траектории волны.
        variants: Результаты по всем запрошенным сценариям.
        recommended_variant: Ключ лучшего варианта: ``"gwk"`` | ``"plain"``.
    """

    tank_volume: int
    tank_diameter_m: float
    liquid_level_h0: float
    liquid_volume_m3: float
    wave: WaveData
    variants: List[WallResult]
    recommended_variant: str
