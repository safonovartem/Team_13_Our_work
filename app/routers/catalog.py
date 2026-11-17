"""Справочник типоразмеров РВС и границ применимости формул.

Каталог берётся из вычислительного ядра (``app.core.catalog``), чтобы
фронтенд и API использовали один и тот же список объёмов.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.core.catalog import TANK_CATALOG
from app.core.constants import (
    CLEARANCE_L_MAX,
    CLEARANCE_L_MIN,
    CREST_WIDTH_B_MAX,
    CREST_WIDTH_B_MIN,
    PLAIN_WALL_REL_HEIGHT_MAX,
    PLAIN_WALL_REL_HEIGHT_MIN,
)
from app.schemas.calculations import ScenarioKey
from app.schemas.catalog import CatalogLimits, CatalogResponse, TankSpecRead

router = APIRouter(prefix="/catalog", tags=["Справочники"])


@router.get(
    "",
    response_model=CatalogResponse,
    summary="Типоразмеры РВС и допустимые диапазоны параметров",
)
def get_catalog() -> CatalogResponse:
    tanks = [
        TankSpecRead(
            volume_m3=spec.volume_m3,
            diameter_m=spec.diameter_m,
            wall_height_m=spec.wall_height_m,
            scale_factor=spec.scale_factor,
            model_water_level_m=spec.model_water_level_m,
        )
        for _, spec in sorted(TANK_CATALOG.items())
    ]

    return CatalogResponse(
        tanks=tanks,
        limits=CatalogLimits(
            clearance_l_min=CLEARANCE_L_MIN,
            clearance_l_max=CLEARANCE_L_MAX,
            crest_width_b_min=CREST_WIDTH_B_MIN,
            crest_width_b_max=CREST_WIDTH_B_MAX,
            plain_wall_rel_height_min=PLAIN_WALL_REL_HEIGHT_MIN,
            plain_wall_rel_height_max=PLAIN_WALL_REL_HEIGHT_MAX,
            scenarios=[ScenarioKey.PLAIN, ScenarioKey.GWK],
        ),
    )
