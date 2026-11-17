"""Схемы исходных данных проекта.

Здесь описаны только структура и валидация данных (разделы 4.2 и 5 ТЗ).
Математическая модель и расчёты выполняются отдельным вычислительным модулем,
который получает от API уже проверенный снимок ``ProjectInputData``.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field, ValidationInfo, field_validator, model_validator

from app.schemas.common import APIModel


class ObjectType(str, Enum):
    """Тип объекта."""

    VERTICAL_CYLINDER = "vertical_cylinder"
    HORIZONTAL_CYLINDER = "horizontal_cylinder"
    RECTANGULAR = "rectangular"


class LiquidType(str, Enum):
    """Тип жидкости."""

    WATER = "water"
    OIL = "oil"
    PETROLEUM = "petroleum"
    DIESEL = "diesel"
    GASOLINE = "gasoline"
    ACID = "acid"
    ALKALI = "alkali"
    OTHER = "other"


class TerrainType(str, Enum):
    """Характер территории."""

    FLAT = "flat"
    SLOPE = "slope"
    ROUGH = "rough"
    URBAN = "urban"
    INDUSTRIAL = "industrial"


class SurfaceType(str, Enum):
    """Тип поверхности под объектом."""

    ASPHALT = "asphalt"
    CONCRETE = "concrete"
    SOIL = "soil"
    SAND = "sand"
    GRASS = "grass"
    WATER = "water"


class TankParams(APIModel):
    """Параметры объекта (резервуара)."""

    name: str = Field(
        min_length=1, max_length=120, description="Название объекта"
    )
    object_type: ObjectType = Field(description="Тип объекта")
    material: str = Field(
        min_length=1, max_length=120, description="Материал стенки"
    )
    wall_thickness_mm: float = Field(
        le=500, description="Толщина стенки, мм (должна быть больше 0)"
    )
    height_m: float = Field(gt=0, le=200, description="Высота, м")
    diameter_m: float | None = Field(
        default=None, gt=0, le=200, description="Диаметр, м (для цилиндров)"
    )
    length_m: float | None = Field(
        default=None, gt=0, le=500, description="Длина, м (для прямоугольных)"
    )
    width_m: float | None = Field(
        default=None, gt=0, le=500, description="Ширина, м (для прямоугольных)"
    )
    volume_m3: float | None = Field(
        default=None,
        gt=0,
        le=1_000_000,
        description="Номинальный объём, м³ (необязательно)",
    )

    @field_validator("wall_thickness_mm", mode="before")
    @classmethod
    def _check_wall_thickness(cls, value: Any) -> Any:
        try:
            number = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Толщина стенки должна быть числом") from exc
        if number <= 0:
            raise ValueError("Толщина стенки должна быть больше 0 мм")
        return number

    @field_validator("name", "material")
    @classmethod
    def _strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Поле не может быть пустым")
        return value

    @model_validator(mode="after")
    def _check_geometry_by_type(self) -> "TankParams":
        if self.object_type in (
            ObjectType.VERTICAL_CYLINDER,
            ObjectType.HORIZONTAL_CYLINDER,
        ):
            if self.diameter_m is None:
                raise ValueError(
                    "Для цилиндрического объекта необходимо указать diameter_m"
                )
            if self.length_m is not None or self.width_m is not None:
                raise ValueError(
                    "length_m и width_m допустимы только для прямоугольного объекта"
                )
        elif self.object_type is ObjectType.RECTANGULAR:
            if self.length_m is None or self.width_m is None:
                raise ValueError(
                    "Для прямоугольного объекта необходимо указать length_m и width_m"
                )
            if self.diameter_m is not None:
                raise ValueError(
                    "Для прямоугольного объекта не указывается diameter_m"
                )
        return self


class LiquidParams(APIModel):
    """Параметры содержимого."""

    liquid_type: LiquidType = Field(description="Тип жидкости")
    density_kg_m3: float = Field(
        ge=500, le=2000, description="Плотность, кг/м³"
    )
    viscosity_cst: float = Field(
        ge=0, le=1_000_000, description="Кинематическая вязкость, сСт"
    )
    temperature_c: float = Field(
        ge=-60, le=200, description="Температура жидкости, °C"
    )
    fill_level_percent: float = Field(
        ge=0, le=100, description="Уровень заполнения, %"
    )
    volume_m3: float | None = Field(
        default=None, ge=0, le=1_000_000, description="Объём жидкости, м³"
    )


class EnvironmentParams(APIModel):
    """Параметры окружающей среды и территории."""

    ambient_temperature_c: float = Field(
        ge=-60, le=60, description="Температура окружающей среды, °C"
    )
    terrain_type: TerrainType = Field(description="Характер территории")
    surface_type: SurfaceType = Field(description="Тип поверхности")
    slope_degrees: float = Field(
        ge=0, le=90, description="Уклон поверхности, градусы"
    )
    has_obstacles: bool = Field(
        default=False, description="Наличие препятствий на пути растекания"
    )
    obstacles_description: str | None = Field(
        default=None, max_length=500, description="Описание препятствий"
    )
    containment: bool = Field(
        default=False, description="Наличие обвалования (защитной стенки)"
    )
    additional_params: dict[str, str | float | bool] = Field(
        default_factory=dict,
        description="Дополнительные параметры территории",
    )

    @field_validator("obstacles_description")
    @classmethod
    def _normalize_description(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("additional_params")
    @classmethod
    def _limit_additional_params(
        cls, value: dict[str, str | float | bool]
    ) -> dict[str, str | float | bool]:
        if len(value) > 20:
            raise ValueError("Допускается не более 20 дополнительных параметров")
        for key in value:
            if not key.strip():
                raise ValueError("Ключ дополнительного параметра не может быть пустым")
        return value

    @model_validator(mode="after")
    def _check_terrain_consistency(self) -> "EnvironmentParams":
        if self.terrain_type is TerrainType.FLAT and self.slope_degrees > 5:
            raise ValueError(
                "Для ровной территории уклон не может превышать 5 градусов"
            )
        if not self.has_obstacles and self.obstacles_description:
            raise ValueError(
                "Описание препятствий допустимо только при has_obstacles=true"
            )
        return self


class ProjectInputData(APIModel):
    """Полный набор исходных данных проекта."""

    schema_version: int = Field(default=1, ge=1, le=100)
    object: TankParams
    liquid: LiquidParams
    environment: EnvironmentParams

    @field_validator("liquid")
    @classmethod
    def _check_liquid_against_object(
        cls, value: LiquidParams, info: ValidationInfo
    ) -> LiquidParams:
        tank: TankParams | None = info.data.get("object")
        if tank is None:
            return value

        liquid_volume = value.volume_m3
        tank_volume = tank.volume_m3

        if (
            liquid_volume is not None
            and tank_volume is not None
            and liquid_volume > tank_volume + 1e-9
        ):
            raise ValueError("Объём жидкости не может превышать объём объекта")

        if value.fill_level_percent == 0 and liquid_volume:
            raise ValueError(
                "При нулевом уровне заполнения объём жидкости должен быть равен 0"
            )

        if liquid_volume is not None and tank_volume is not None:
            expected = tank_volume * value.fill_level_percent / 100
            tolerance = max(expected * 0.15, 0.5)
            if abs(liquid_volume - expected) > tolerance:
                raise ValueError(
                    "Объём жидкости не соответствует уровню заполнения: "
                    f"ожидалось около {expected:.3f} м³ при объёме объекта "
                    f"{tank_volume:g} м³ и уровне {value.fill_level_percent:g}%"
                )
        return value
