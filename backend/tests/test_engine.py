"""Интеграционные тесты пайплайна run_engine и UX-валидации.

Проверяет:
- Полный пайплайн для всех 6 типоразмеров РВС.
- Срабатывание DomainRangeError с корректным текстом.
- Коррекцию высоты при недостаточном объёме чаши.
- Выбор recommended_variant.
- Отсутствие сторонних импортов в app/core/.
"""
from __future__ import annotations

import math

import pytest


from app.core import run_engine, InputData, ResultData
from app.core.catalog import TANK_CATALOG
from app.core.exceptions import DomainRangeError
from app.core.constants import FULL_CONTAINMENT_FACTOR


ALL_VOLUMES = sorted(TANK_CATALOG.keys())


# ──────────────────────────────────────────────────────────────────────────────
# Интеграционные тесты: полный пайплайн
# ──────────────────────────────────────────────────────────────────────────────

class TestEngineIntegration:
    """Полный цикл run_engine для всех типоразмеров."""

    @pytest.mark.parametrize("volume", ALL_VOLUMES)
    def test_full_pipeline_both_scenarios(self, volume: int) -> None:
        """Оба сценария (plain + gwk) для каждого типоразмера."""
        data = InputData(
            tank_volume=volume,
            clearance_l=2.0,
            crest_width_b=1.0,
            scenarios=["plain", "gwk"],
        )
        result: ResultData = run_engine(data)

        # Базовые проверки
        assert result.tank_volume == volume
        assert result.tank_diameter_m > 0
        assert result.liquid_level_h0 > 0
        assert result.liquid_volume_m3 > 0
        assert len(result.variants) == 2
        assert result.recommended_variant in ("plain", "gwk")

        # WaveData
        assert result.wave.initial_velocity_ms > 0
        assert result.wave.froude_number > 0
        assert result.wave.reynolds_number > 0
        assert result.wave.scale_factor > 0
        assert len(result.wave.trajectory) > 0

    @pytest.mark.parametrize("volume", ALL_VOLUMES)
    def test_gwk_only(self, volume: int) -> None:
        """Только сценарий GWK."""
        data = InputData(
            tank_volume=volume,
            clearance_l=1.5,
            crest_width_b=0.5,
            scenarios=["gwk"],
        )
        result = run_engine(data)
        assert len(result.variants) == 1
        assert result.variants[0].scenario_type == "gwk"
        assert result.recommended_variant == "gwk"

    @pytest.mark.parametrize("volume", ALL_VOLUMES)
    def test_plain_only(self, volume: int) -> None:
        """Только сценарий Plain."""
        data = InputData(
            tank_volume=volume,
            clearance_l=1.5,
            crest_width_b=0.5,
            scenarios=["plain"],
        )
        result = run_engine(data)
        assert len(result.variants) == 1
        assert result.variants[0].scenario_type == "plain"

    @pytest.mark.parametrize("volume", ALL_VOLUMES)
    def test_recommended_is_gwk_when_both_safe(self, volume: int) -> None:
        """Когда оба варианта Q=0%, рекомендуется вариант с меньшим CAPEX."""
        data = InputData(
            tank_volume=volume,
            clearance_l=2.0,
            crest_width_b=1.0,
            # plain без явной высоты → 1.1·h0 → Q=0
            scenarios=["plain", "gwk"],
        )
        result = run_engine(data)

        plain_r = next(v for v in result.variants if v.scenario_type == "plain")
        gwk_r = next(v for v in result.variants if v.scenario_type == "gwk")

        # Оба Q = 0
        assert plain_r.overflow_pct == 0.0
        assert gwk_r.overflow_pct == 0.0

        # Рекомендуется вариант с меньшим CAPEX
        if gwk_r.capex_raw < plain_r.capex_raw:
            assert result.recommended_variant == "gwk"
        else:
            assert result.recommended_variant == "plain"


# ──────────────────────────────────────────────────────────────────────────────
# Тесты UX-валидации: DomainRangeError
# ──────────────────────────────────────────────────────────────────────────────

class TestValidation:
    """Проверка корректности UX-сообщений при выходе за границы."""

    def test_empty_scenarios(self) -> None:
        """Пустой список сценариев → DomainRangeError."""
        data = InputData(
            tank_volume=5000,
            clearance_l=2.0,
            crest_width_b=1.0,
            scenarios=[],
        )
        with pytest.raises(DomainRangeError, match="пустым"):
            run_engine(data)

    def test_invalid_volume(self) -> None:
        """Неизвестный объём РВС выбрасывает DomainRangeError."""
        data = InputData(
            tank_volume=999,
            clearance_l=2.0,
            crest_width_b=1.0,
        )
        with pytest.raises(DomainRangeError, match="999"):
            run_engine(data)

    def test_invalid_volume_message_contains_allowed(self) -> None:
        """Сообщение содержит список допустимых объёмов."""
        data = InputData(
            tank_volume=1500,
            clearance_l=2.0,
            crest_width_b=1.0,
        )
        with pytest.raises(DomainRangeError, match="700"):
            run_engine(data)

    def test_clearance_too_small(self) -> None:
        """l < 1.5 → DomainRangeError."""
        data = InputData(
            tank_volume=5000,
            clearance_l=1.0,
            crest_width_b=1.0,
        )
        with pytest.raises(DomainRangeError, match="1.0"):
            run_engine(data)

    def test_clearance_too_large(self) -> None:
        """l > 3.0 → DomainRangeError."""
        data = InputData(
            tank_volume=5000,
            clearance_l=3.5,
            crest_width_b=1.0,
        )
        with pytest.raises(DomainRangeError, match="3.5"):
            run_engine(data)

    def test_crest_width_too_small(self) -> None:
        """b < 0.5 → DomainRangeError."""
        data = InputData(
            tank_volume=5000,
            clearance_l=2.0,
            crest_width_b=0.3,
        )
        with pytest.raises(DomainRangeError, match="0.3"):
            run_engine(data)

    def test_crest_width_too_large(self) -> None:
        """b > 1.5 → DomainRangeError."""
        data = InputData(
            tank_volume=5000,
            clearance_l=2.0,
            crest_width_b=2.0,
        )
        with pytest.raises(DomainRangeError, match="2.0"):
            run_engine(data)

    def test_invalid_scenario_key(self) -> None:
        """Неизвестный ключ сценария → DomainRangeError."""
        data = InputData(
            tank_volume=5000,
            clearance_l=2.0,
            crest_width_b=1.0,
            scenarios=["plain", "nvk"],
        )
        with pytest.raises(DomainRangeError, match="nvk"):
            run_engine(data)

    def test_plain_wall_height_too_low(self) -> None:
        """h_зс < 0.4·h0 → DomainRangeError."""
        data = InputData(
            tank_volume=5000,
            clearance_l=2.0,
            crest_width_b=1.0,
            plain_wall_height=3.0,  # 0.2·h0 при h0=15
        )
        with pytest.raises(DomainRangeError, match="3.0"):
            run_engine(data)

    def test_plain_wall_height_too_high(self) -> None:
        """h_зс > 1.1·h0 → DomainRangeError."""
        data = InputData(
            tank_volume=5000,
            clearance_l=2.0,
            crest_width_b=1.0,
            plain_wall_height=20.0,  # > 1.1·15 = 16.5
        )
        with pytest.raises(DomainRangeError, match="20.0"):
            run_engine(data)

    def test_error_messages_in_russian(self) -> None:
        """Сообщения об ошибках на русском языке."""
        data = InputData(
            tank_volume=999,
            clearance_l=2.0,
            crest_width_b=1.0,
        )
        try:
            run_engine(data)
        except DomainRangeError as e:
            msg = str(e)
            # Проверяем наличие кириллицы
            has_cyrillic = any('\u0400' <= c <= '\u04ff' for c in msg)
            assert has_cyrillic, f"Сообщение не содержит кириллицу: {msg}"


# ──────────────────────────────────────────────────────────────────────────────
# Тесты коррекции высоты при недостаточном объёме чаши
# ──────────────────────────────────────────────────────────────────────────────

class TestBasinCapacityCorrection:
    """Коррекция h_зс при V_чаши < V0."""

    def test_forced_basin_capacity_correction(self) -> None:
        """Принудительное срабатывание коррекции высоты при V_чаши < V0."""
        data = InputData(
            tank_volume=30000,
            clearance_l=1.5,
            crest_width_b=0.5,
            plain_wall_height=7.2,  # 0.4 * 18.0 м -> чаша заведомо меньше V0
            scenarios=["plain"],
        )
        result = run_engine(data)
        v = result.variants[0]
        h0 = result.liquid_level_h0

        assert v.engineering_details.is_basin_capacity_sufficient is False
        assert v.wall_height_m > 7.2
        assert abs(v.relative_height - round(v.wall_height_m / h0, 4)) < 0.001
        expected_savings = FULL_CONTAINMENT_FACTOR * h0 - v.wall_height_m
        assert abs(v.height_savings_m - round(expected_savings, 4)) < 0.001

    @pytest.mark.parametrize("volume", ALL_VOLUMES)
    def test_basin_check_recorded(self, volume: int) -> None:
        """Поле is_basin_capacity_sufficient заполнено для каждого варианта."""
        data = InputData(
            tank_volume=volume,
            clearance_l=2.0,
            crest_width_b=1.0,
        )
        result = run_engine(data)
        for v in result.variants:
            assert isinstance(v.engineering_details.is_basin_capacity_sufficient, bool)

    @pytest.mark.parametrize("volume", ALL_VOLUMES)
    def test_height_correction_consistency(self, volume: int) -> None:
        """После коррекции: relative_height, height_savings_m и capex_raw согласованы."""
        data = InputData(
            tank_volume=volume,
            clearance_l=2.0,
            crest_width_b=1.0,
        )
        result = run_engine(data)
        h0 = result.liquid_level_h0

        for v in result.variants:
            # relative_height = wall_height / h0
            expected_rel = v.wall_height_m / h0
            assert abs(v.relative_height - round(expected_rel, 4)) < 0.001, (
                f"{v.scenario_type}: relative_height={v.relative_height} "
                f"!= wall_height/h0={expected_rel:.4f}"
            )

            # height_savings = 1.1·h0 - wall_height
            expected_savings = FULL_CONTAINMENT_FACTOR * h0 - v.wall_height_m
            assert abs(v.height_savings_m - round(expected_savings, 4)) < 0.001

            # capex_raw > 0
            assert v.capex_raw > 0


# ──────────────────────────────────────────────────────────────────────────────
# Тест отсутствия сторонних импортов в app/core/
# ──────────────────────────────────────────────────────────────────────────────

class TestZeroDependency:
    """Проверка Zero-Dependency Core."""

    def test_no_third_party_imports(self) -> None:
        """В app/core/ нет импортов pydantic, fastapi, numpy, scipy, sqlalchemy."""
        import ast
        import pathlib

        core_dir = pathlib.Path(__file__).parent.parent / "app" / "core"
        forbidden = {"pydantic", "fastapi", "numpy", "scipy", "sqlalchemy", "django"}

        violations: list[str] = []
        for py_file in core_dir.rglob("*.py"):
            source = py_file.read_text(encoding="utf-8")
            try:
                tree = ast.parse(source, filename=str(py_file))
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        top = alias.name.split(".")[0]
                        if top in forbidden:
                            violations.append(f"{py_file.name}: import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        top = node.module.split(".")[0]
                        if top in forbidden:
                            violations.append(f"{py_file.name}: from {node.module}")

        assert not violations, (
            "Обнаружены запрещённые импорты в app/core/:\n" + "\n".join(violations)
        )


# ──────────────────────────────────────────────────────────────────────────────
# Тесты CAPEX-нормализации и scoring
# ──────────────────────────────────────────────────────────────────────────────

class TestCapexNormalization:
    """Проверка нормализации capex_score."""

    @pytest.mark.parametrize("volume", ALL_VOLUMES)
    def test_capex_score_in_range(self, volume: int) -> None:
        """capex_score в диапазоне [0, 100] для обоих вариантов."""
        data = InputData(
            tank_volume=volume,
            clearance_l=2.0,
            crest_width_b=1.0,
        )
        result = run_engine(data)
        for v in result.variants:
            assert 0.0 <= v.capex_score <= 100.0, (
                f"{v.scenario_type}: capex_score={v.capex_score} вне [0, 100]"
            )

    def test_single_variant_capex_score_100(self) -> None:
        """Один вариант → capex_score = 100 (нет с чем сравнивать)."""
        data = InputData(
            tank_volume=5000,
            clearance_l=2.0,
            crest_width_b=1.0,
            scenarios=["gwk"],
        )
        result = run_engine(data)
        assert len(result.variants) == 1
        assert result.variants[0].capex_score == 100.0


class TestWaveData:
    """Проверка гидродинамических параметров."""

    @pytest.mark.parametrize("volume", ALL_VOLUMES)
    def test_froude_equals_2(self, volume: int) -> None:
        """Fr = u0² / (g·h0) = 2g·h0 / (g·h0) = 2."""
        data = InputData(
            tank_volume=volume,
            clearance_l=2.0,
            crest_width_b=1.0,
        )
        result = run_engine(data)
        assert abs(result.wave.froude_number - 2.0) < 0.01, (
            f"РВС-{volume}: Fr = {result.wave.froude_number}, ожидалось ≈ 2.0"
        )

    @pytest.mark.parametrize("volume", ALL_VOLUMES)
    def test_trajectory_length(self, volume: int) -> None:
        """Траектория содержит ожидаемое число точек."""
        data = InputData(
            tank_volume=volume,
            clearance_l=2.0,
            crest_width_b=1.0,
        )
        result = run_engine(data)
        from app.core.constants import WAVE_TRAJECTORY_POINTS
        assert len(result.wave.trajectory) == WAVE_TRAJECTORY_POINTS

    def test_model_similarity_violation(self) -> None:
        """Слишком малый уровень воды в модели → DomainRangeError."""
        from app.core.catalog import TankSpec
        from app.core.hydrodynamics import WavePhysics

        invalid_tank = TankSpec(
            volume_m3=100,
            diameter_m=3.0,
            wall_height_m=2.0,
            scale_factor=1000,
            model_water_level_m=0.002,
        )
        with pytest.raises(DomainRangeError, match="подобия модели"):
            WavePhysics(invalid_tank, clearance_l=1.5).calculate()