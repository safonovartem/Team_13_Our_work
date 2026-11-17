"""Схемы справочника типоразмеров РВС и границ применимости формул."""

from __future__ import annotations

from pydantic import Field

from app.schemas.calculations import ScenarioKey
from app.schemas.common import ResponseModel


class TankSpecRead(ResponseModel):
    """Типоразмер вертикального стального резервуара (ГОСТ)."""

    volume_m3: int = Field(description="Номинальный объём, м³")
    diameter_m: float = Field(description="Внутренний диаметр, м")
    wall_height_m: float = Field(description="Высота стенки, м")
    scale_factor: int = Field(description="Масштабный коэффициент моделирования")
    model_water_level_m: float = Field(description="Уровень воды в модели, м")


class CatalogLimits(ResponseModel):
    """Допустимые диапазоны параметров расчёта."""

    clearance_l_min: float
    clearance_l_max: float
    crest_width_b_min: float
    crest_width_b_max: float
    plain_wall_rel_height_min: float
    plain_wall_rel_height_max: float
    scenarios: list[ScenarioKey]


class CatalogResponse(ResponseModel):
    """Справочник РВС и границы применимости формул."""

    tanks: list[TankSpecRead]
    limits: CatalogLimits
