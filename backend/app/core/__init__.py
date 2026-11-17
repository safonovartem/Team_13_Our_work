"""Вычислительное ядро Tank Safety Engine.

Экспортирует единую точку входа ``run_engine`` и основные DTO.

Пример использования::

    from app.core import run_engine, InputData

    result = run_engine(InputData(
        tank_volume=5000,
        clearance_l=2.0,
        crest_width_b=1.0,
    ))
    print(result.recommended_variant)
"""
from __future__ import annotations

from .contracts import InputData, ResultData
from .engine import run_engine

__all__ = ["run_engine", "InputData", "ResultData"]
