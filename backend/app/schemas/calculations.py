"""Схемы расчётов вычислительного ядра (``app.core``) и его результатов.

Контракты ядра — frozen-dataclass; здесь они зеркалируются Pydantic-моделями
для сериализации в JSON и документирования в OpenAPI.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import Field, field_validator

from app.schemas.common import APIModel, ResponseModel


class ScenarioKey(str, Enum):
    """Доступные сценарии защитного ограждения."""

    PLAIN = "plain"
    GWK = "gwk"


SCENARIO_TITLES: dict[str, str] = {
    ScenarioKey.PLAIN.value: "Без козырька",
    ScenarioKey.GWK.value: "С горизонтальным козырьком (ГВК)",
}


class CalculationInput(APIModel):
    """Входные параметры вычислительного ядра Tank Safety Engine.

    Значения полей соответствуют ``app.core.contracts.InputData``.
    Границы применимости проверяются самим ядром (``DomainRangeError`` → 422).
    """

    tank_volume: int = Field(
        description="Номинальный объём РВС по каталогу ГОСТ, м³",
        examples=[5000],
    )
    clearance_l: float = Field(
        default=3.0,
        description="Межстенное расстояние l, м (допустимо 1.5…3.0)",
        examples=[3.0],
    )
    crest_width_b: float = Field(
        default=1.0,
        description="Вылет горизонтального козырька b, м (допустимо 0.5…1.5)",
        examples=[1.0],
    )
    plain_wall_height: float | None = Field(
        default=None,
        description=(
            "Высота стенки без козырька h_зс, м. Если не задана — 1.1·h0"
        ),
        examples=[None, 12.0],
    )
    scenarios: list[ScenarioKey] = Field(
        default_factory=lambda: [ScenarioKey.PLAIN, ScenarioKey.GWK],
        description="Запрашиваемые сценарии (plain и/или gwk)",
    )

    @field_validator("scenarios")
    @classmethod
    def _deduplicate_scenarios(
        cls, value: list[ScenarioKey]
    ) -> list[ScenarioKey]:
        unique: list[ScenarioKey] = []
        for scenario in value:
            if scenario not in unique:
                unique.append(scenario)
        return unique


class WavePointRead(ResponseModel):
    time_s: float
    distance_m: float
    wave_height_m: float


class WaveDataRead(ResponseModel):
    initial_velocity_ms: float
    froude_number: float
    strouhal_number: float
    reynolds_number: float
    scale_factor: int
    trajectory: list[WavePointRead]


class EngineeringDetailsRead(ResponseModel):
    formula_reference: str
    dimensionless_params: dict[str, float]
    static_basin_volume_m3: float
    is_basin_capacity_sufficient: bool


class WallResultRead(ResponseModel):
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
    engineering_details: EngineeringDetailsRead


class EngineResultRead(ResponseModel):
    tank_volume: int
    tank_diameter_m: float
    liquid_level_h0: float
    liquid_volume_m3: float
    wave: WaveDataRead
    variants: list[WallResultRead]
    recommended_variant: str


class ResultItem(ResponseModel):
    """Строка результата для карточки варианта на фронтенде."""

    title: str
    value: str


class ResultBlock(ResponseModel):
    """Карточка варианта ограждения (совместима с ``ResultBlock`` фронтенда)."""

    model_config = ResponseModel.model_config | {
        "populate_by_name": True,
    }

    id: str
    title: str
    scenario: str | None = Field(
        default=None,
        description="Ключ сценария вычислительного ядра: plain или gwk",
    )
    is_important: bool = Field(default=False, alias="isImportant")
    items: list[ResultItem]


class ChartDataset(ResponseModel):
    """Набор точек для Chart.js: ``data: [[x, y], ...]``."""

    label: str
    data: list[list[float]]


class ChartAxis(ResponseModel):
    title: str
    unit: str | None = None


class ChartBlock(ResponseModel):
    """График для фронтенда (совместим с ``ChartBlock``)."""

    model_config = ResponseModel.model_config | {
        "populate_by_name": True,
    }

    title: str
    datasets: list[ChartDataset]
    x_axis: ChartAxis | None = Field(default=None, alias="xAxis")
    y_axis: ChartAxis | None = Field(default=None, alias="yAxis")


class ChartCollection(ResponseModel):
    charts: list[ChartBlock]


class CalculationResponse(ResponseModel):
    """Результат расчёта: контракт ядра + готовые блоки для интерфейса."""

    input: CalculationInput
    result: EngineResultRead
    variants: list[ResultBlock]
    charts: list[ChartBlock]
    recommended_variant: str


class SavedCalculation(CalculationResponse):
    """Сохранённый в истории проекта расчёт."""

    id: int
    project_id: int
    created_at: datetime


class CalculationSummary(ResponseModel):
    """Краткая запись истории расчётов проекта."""

    id: int
    project_id: int
    input: CalculationInput
    recommended_variant: str
    has_form_data: bool = False
    created_at: datetime


class OverflowChartRequest(APIModel):
    """Параметры графика «доля перелива от высоты стенки»."""

    tank_volume: int = Field(examples=[5000])
    clearance_values: list[float] = Field(
        default_factory=lambda: [1.5, 2.0, 2.5, 3.0],
        min_length=1,
        max_length=10,
        description="Значения межстенного расстояния l, м",
    )
    height_ratios: list[float] | None = Field(
        default=None,
        max_length=100,
        description=(
            "Отношения h_зс/h0; по умолчанию сетка 0.4…1.1 с шагом 0.05"
        ),
    )


class WaveChartRequest(APIModel):
    """Параметры графиков траектории волны."""

    tank_volume: int = Field(examples=[5000])
    clearance_l: float = Field(default=3.0, examples=[3.0])


class ChartsRequest(APIModel):
    """Параметры набора графиков для главной страницы."""

    tank_volume: int = Field(examples=[5000])
    clearance_l: float = Field(default=3.0, examples=[3.0])
    clearance_values: list[float] | None = Field(
        default=None, max_length=10, description="Набор кривых для графика перелива"
    )


class FrontendFormValues(APIModel):
    """Значения формы главной страницы (``FormValues`` из ``frontend/src/types.ts``).

    Принимаются поля в camelCase; неизвестные поля сохраняются как есть и не
    влияют на расчёт. Объём РВС берётся из ``objectType`` (например,
    ``"РВС-5000 · 5 000 м³"``) или из ``objectVolume``.
    """

    model_config = APIModel.model_config | {
        "extra": "allow",
        "populate_by_name": True,
    }

    object_name: str | None = Field(default=None, alias="objectName", max_length=200)
    object_type: str | None = Field(default=None, alias="objectType", max_length=100)
    object_volume: float | None = Field(default=None, alias="objectVolume")
    object_diameter: float | None = Field(default=None, alias="objectDiameter")
    object_height: float | None = Field(default=None, alias="objectHeight")
    object_length: float | None = Field(default=None, alias="objectLength")
    object_width: float | None = Field(default=None, alias="objectWidth")
    object_material: str | None = Field(default=None, alias="objectMaterial")
    wall_thickness: float | None = Field(default=None, alias="wallThickness")
    liquid_type: str | None = Field(default=None, alias="liquidType")
    liquid_density: float | None = Field(default=None, alias="liquidDensity")
    liquid_viscosity: float | None = Field(default=None, alias="liquidViscosity")
    liquid_temperature: float | None = Field(
        default=None, alias="liquidTemperature"
    )
    fill_level: float | None = Field(default=None, alias="fillLevel")
    liquid_volume: float | None = Field(default=None, alias="liquidVolume")

    clearance_l: float | None = Field(default=None, alias="clearanceL")
    crest_width_b: float | None = Field(default=None, alias="crestWidthB")
    plain_wall_height: float | None = Field(default=None, alias="plainWallHeight")
    scenarios: list[ScenarioKey] | None = None
