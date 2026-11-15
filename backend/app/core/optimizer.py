"""Оптимизатор: сравнение вариантов и выбор рекомендуемого решения.

Класс ``BestPicker`` выполняет:
- нормализацию ``capex_score`` (0…100);
- выбор ``recommended_variant`` (минимальный CAPEX при Q = 0 %,
  иначе — минимальный перелив).
"""
from __future__ import annotations

from dataclasses import replace
from typing import List

from .contracts import WallResult


class BestPicker:
    """Pareto Ranker для выбора оптимального варианта ограждения.

    Логика выбора ``recommended_variant``:
    1. Среди вариантов с полной локализацией (Q = 0 %) выбирается
       вариант с минимальным ``capex_raw``.
    2. Если ни один вариант не обеспечивает Q = 0 %, выбирается
       вариант с минимальным ``overflow_pct``.
    """

    @staticmethod
    def pick(variants: List[WallResult]) -> tuple[List[WallResult], str]:
        """Нормализовать CAPEX-score и выбрать лучший вариант.

        Parameters:
            variants: Список результатов расчёта по всем сценариям.

        Returns:
            Кортеж:
            - список ``WallResult`` с заполненным ``capex_score``;
            - ключ ``recommended_variant`` (``"gwk"`` или ``"plain"``).
        """
        if not variants:
            return variants, "plain"

        # Нормализация capex_score: 0 = максимальный CAPEX, 100 = минимальный
        capex_values: list[float] = [v.capex_raw for v in variants]
        min_capex: float = min(capex_values)
        max_capex: float = max(capex_values)
        capex_range: float = max_capex - min_capex

        normalized: List[WallResult] = []
        for v in variants:
            if capex_range > 0:
                score: float = 100.0 * (1.0 - (v.capex_raw - min_capex) / capex_range)
            else:
                score = 100.0
            normalized.append(replace(v, capex_score=round(score, 2)))

        # Выбор рекомендуемого варианта
        safe_variants: list[WallResult] = [
            v for v in normalized if v.overflow_pct == 0.0
        ]

        if safe_variants:
            best: WallResult = min(safe_variants, key=lambda v: v.capex_raw)
        else:
            best = min(normalized, key=lambda v: v.overflow_pct)

        return normalized, best.scenario_type
