"""Тесты формулы (3.1) Буй Куанг Тиена: ГВК 90° для РВСЗС.

Проверяет сходимость формулы (3.1) при различных комбинациях параметров
для всех 6 типоразмеров (РВС 700–30 000 м³) с погрешностью ≤ 2 %.

Таблицы диссертации Тиена: 2.5, 2.7, 2.9, 2.11, 2.13, 2.15.
"""
from __future__ import annotations

import math

import pytest


from app.core.catalog import TankCatalog, TANK_CATALOG
from app.core.barriers.gwk import GWKWall
from app.core.constants import (
    CLEARANCE_L_MIN,
    CREST_WIDTH_B_MIN,
    TIEN_C0,
    TIEN_C1,
    TIEN_C2,
    TIEN_C3,
)


# ──────────────────────────────────────────────────────────────────────────────
# Эталонная формула (3.1)
# ──────────────────────────────────────────────────────────────────────────────

def _tien_31(d_vn: float, h0: float, l: float, b: float) -> float:
    """Эталонный расчёт h_зс / h0 по формуле (3.1) Тиена."""
    return (
        TIEN_C0
        + TIEN_C1 * (d_vn / h0)
        + TIEN_C2 * (l / CLEARANCE_L_MIN)
        + TIEN_C3 * (b / CREST_WIDTH_B_MIN)
    )


def _v0(d_vn: float, h0: float) -> float:
    return math.pi * d_vn ** 2 / 4.0 * h0


ALL_VOLUMES = sorted(TANK_CATALOG.keys())

# Репрезентативные комбинации (l, b) — имитация таблиц 2.5–2.15 Тиена
PARAMETER_GRID: list[tuple[float, float]] = [
    (1.5, 0.5),   # Минимальные значения
    (1.5, 1.0),
    (1.5, 1.5),
    (2.0, 0.5),
    (2.0, 1.0),
    (2.0, 1.5),
    (2.5, 0.5),
    (2.5, 1.0),
    (2.5, 1.5),
    (3.0, 0.5),
    (3.0, 1.0),
    (3.0, 1.5),   # Максимальные значения
]


class TestTienGWKFormula:
    """Тесты формулы (3.1) Тиена для ГВК 90°."""

    @pytest.mark.parametrize("volume", ALL_VOLUMES)
    @pytest.mark.parametrize("l,b", PARAMETER_GRID)
    def test_relative_height_convergence(
        self, volume: int, l: float, b: float
    ) -> None:
        """Сходимость h_зс/h0 с эталонным расчётом с погрешностью ≤ 2 %."""
        tank = TankCatalog.resolve(volume)
        d_vn = tank.diameter_m
        h0 = tank.wall_height_m

        expected = _tien_31(d_vn, h0, l, b)
        actual = GWKWall._relative_height(d_vn, h0, l, b)

        if expected == 0.0:
            assert abs(actual) < 0.02
        else:
            rel_error = abs(actual - expected) / abs(expected) * 100.0
            assert rel_error <= 2.0, (
                f"РВС-{volume}, l={l}, b={b}: "
                f"h_зс/h0 ожидался {expected:.6f}, получено {actual:.6f}, "
                f"относительная погрешность {rel_error:.4f}%"
            )

    @pytest.mark.parametrize("volume", ALL_VOLUMES)
    def test_q_zero_for_gwk(self, volume: int) -> None:
        """GWK всегда даёт Q = 0 %."""
        tank = TankCatalog.resolve(volume)
        v0 = _v0(tank.diameter_m, tank.wall_height_m)
        gwk = GWKWall()
        result = gwk.calculate(
            tank=tank,
            clearance_l=1.5,
            crest_width_b=0.5,
            plain_wall_height=None,
            liquid_volume_m3=v0,
        )
        assert result.overflow_pct == 0.0
        assert result.safety_score == 100.0

    @pytest.mark.parametrize("volume", ALL_VOLUMES)
    def test_no_secondary_wall(self, volume: int) -> None:
        """GWK не требует второго рубежа."""
        tank = TankCatalog.resolve(volume)
        v0 = _v0(tank.diameter_m, tank.wall_height_m)
        gwk = GWKWall()
        result = gwk.calculate(
            tank=tank,
            clearance_l=2.0,
            crest_width_b=1.0,
            plain_wall_height=None,
            liquid_volume_m3=v0,
        )
        assert result.secondary_wall_dist_m == 0.0
        assert result.secondary_wall_height_m == 0.0

    @pytest.mark.parametrize("volume", ALL_VOLUMES)
    def test_crest_angle_90(self, volume: int) -> None:
        """Угол козырька ГВК = 90°."""
        tank = TankCatalog.resolve(volume)
        v0 = _v0(tank.diameter_m, tank.wall_height_m)
        gwk = GWKWall()
        result = gwk.calculate(
            tank=tank,
            clearance_l=1.5,
            crest_width_b=0.5,
            plain_wall_height=None,
            liquid_volume_m3=v0,
        )
        assert result.crest_angle_deg == 90.0

    @pytest.mark.parametrize("volume", ALL_VOLUMES)
    def test_height_savings_positive(self, volume: int) -> None:
        """GWK всегда экономит высоту (h_зс < 1.1·h0)."""
        tank = TankCatalog.resolve(volume)
        v0 = _v0(tank.diameter_m, tank.wall_height_m)
        gwk = GWKWall()
        result = gwk.calculate(
            tank=tank,
            clearance_l=1.5,
            crest_width_b=0.5,
            plain_wall_height=None,
            liquid_volume_m3=v0,
        )
        assert result.height_savings_m > 0, (
            f"РВС-{volume}: ожидалась экономия высоты, получено Δh = {result.height_savings_m}"
        )

    @pytest.mark.parametrize("volume", ALL_VOLUMES)
    def test_relative_height_within_bounds(self, volume: int) -> None:
        """h_зс/h0 по Тиену должен быть в разумном диапазоне (0.5 … 1.1)."""
        tank = TankCatalog.resolve(volume)
        v0 = _v0(tank.diameter_m, tank.wall_height_m)
        gwk = GWKWall()
        result = gwk.calculate(
            tank=tank,
            clearance_l=1.5,
            crest_width_b=0.5,
            plain_wall_height=None,
            liquid_volume_m3=v0,
        )
        assert 0.5 <= result.relative_height <= 1.1, (
            f"РВС-{volume}: h_зс/h0 = {result.relative_height} вне диапазона [0.5, 1.1]"
        )


class TestTienDimensionlessParams:
    """Проверка безразмерных комплексов в EngineeringDetails."""

    @pytest.mark.parametrize("volume", ALL_VOLUMES)
    def test_dimensionless_keys_present(self, volume: int) -> None:
        """Все 5 безразмерных комплексов присутствуют."""
        tank = TankCatalog.resolve(volume)
        v0 = _v0(tank.diameter_m, tank.wall_height_m)
        gwk = GWKWall()
        result = gwk.calculate(
            tank=tank,
            clearance_l=1.5,
            crest_width_b=0.5,
            plain_wall_height=None,
            liquid_volume_m3=v0,
        )
        expected_keys = {"d_vn/h0", "l/l_min", "b/b_min", "L/R", "h_zs/h0"}
        assert set(result.engineering_details.dimensionless_params.keys()) == expected_keys

    @pytest.mark.parametrize("volume", ALL_VOLUMES)
    def test_formula_reference(self, volume: int) -> None:
        """Ссылка на формулу Тиена корректна."""
        tank = TankCatalog.resolve(volume)
        v0 = _v0(tank.diameter_m, tank.wall_height_m)
        gwk = GWKWall()
        result = gwk.calculate(
            tank=tank,
            clearance_l=1.5,
            crest_width_b=0.5,
            plain_wall_height=None,
            liquid_volume_m3=v0,
        )
        assert "Тиен" in result.engineering_details.formula_reference
        assert "3.1" in result.engineering_details.formula_reference
# ──────────────────────────────────────────────────────────────────────────────
# Экспериментальные данные из диссертации Буй Куанг Тиена (стр. 101–103):
# Табл. 2.5 (РВС-700), 2.7 (РВС-2000), 2.9 (РВС-5000),
# 2.11 (РВС-10000), 2.13 (РВС-20000), 2.15 (РВС-30000).
# Значения в матрицах — модельная высота стенки h_зс,мод (м) при ГВК 90°.
# ──────────────────────────────────────────────────────────────────────────────

TIEN_L_VALUES: tuple[float, ...] = (1.5, 1.8, 2.1, 2.4, 2.7, 3.0)
TIEN_B_VALUES: tuple[float, ...] = (1.50, 1.25, 1.00, 0.75, 0.50)

TIEN_GWK_MODEL_TABLES: dict[int, list[list[float]]] = {
    # Таблица 2.5 — РВС-700 м³ (λ_l = 30, h_{0,мод} = 0.30 м)
    700: [
        [0.294, 0.299, 0.303, 0.308, 0.312],
        [0.289, 0.294, 0.298, 0.303, 0.308],
        [0.283, 0.288, 0.294, 0.298, 0.303],
        [0.278, 0.283, 0.289, 0.294, 0.299],
        [0.272, 0.278, 0.285, 0.289, 0.294],
        [0.268, 0.274, 0.280, 0.284, 0.290],
    ],
    # Таблица 2.7 — РВС-2000 м³ (λ_l = 43, h_{0,мод} = 0.28 м)
    2000: [
        [0.276, 0.280, 0.283, 0.287, 0.292],
        [0.271, 0.275, 0.279, 0.283, 0.288],
        [0.266, 0.270, 0.275, 0.279, 0.283],
        [0.261, 0.266, 0.271, 0.275, 0.279],
        [0.257, 0.261, 0.267, 0.271, 0.276],
        [0.253, 0.258, 0.264, 0.268, 0.273],
    ],
    # Таблица 2.9 — РВС-5000 м³ (λ_l = 60, h_{0,мод} = 0.25 м)
    5000: [
        [0.246, 0.249, 0.251, 0.254, 0.257],
        [0.243, 0.245, 0.248, 0.251, 0.254],
        [0.239, 0.241, 0.244, 0.247, 0.251],
        [0.234, 0.237, 0.240, 0.243, 0.247],
        [0.229, 0.232, 0.236, 0.239, 0.243],
        [0.225, 0.228, 0.233, 0.236, 0.240],
    ],
    # Таблица 2.11 — РВС-10000 м³ (λ_l = 81, h_{0,мод} = 0.22 м)
    10000: [
        [0.218, 0.220, 0.223, 0.226, 0.230],
        [0.214, 0.217, 0.220, 0.223, 0.227],
        [0.210, 0.213, 0.216, 0.219, 0.223],
        [0.206, 0.209, 0.213, 0.216, 0.220],
        [0.202, 0.206, 0.209, 0.213, 0.217],
        [0.199, 0.203, 0.207, 0.210, 0.214],
    ],
    # Таблица 2.13 — РВС-20000 м³ (λ_l = 114, h_{0,мод} = 0.16 м)
    20000: [
        [0.158, 0.160, 0.162, 0.165, 0.167],
        [0.155, 0.157, 0.160, 0.162, 0.164],
        [0.152, 0.154, 0.157, 0.160, 0.162],
        [0.149, 0.151, 0.154, 0.157, 0.159],
        [0.146, 0.148, 0.151, 0.154, 0.157],
        [0.144, 0.146, 0.149, 0.152, 0.155],
    ],
    # Таблица 2.15 — РВС-30000 м³ (λ_l = 130, h_{0,мод} = 0.14 м)
    30000: [
        [0.135, 0.137, 0.138, 0.140, 0.142],
        [0.133, 0.135, 0.136, 0.138, 0.141],
        [0.131, 0.133, 0.134, 0.136, 0.139],
        [0.128, 0.130, 0.132, 0.134, 0.137],
        [0.125, 0.127, 0.129, 0.131, 0.134],
        [0.124, 0.126, 0.128, 0.130, 0.133],
    ],
}

TIEN_EXPERIMENTAL_CASES: list[tuple[int, float, float, float]] = [
    (volume, l_val, b_val, grid[i][j])
    for volume, grid in TIEN_GWK_MODEL_TABLES.items()
    for i, l_val in enumerate(TIEN_L_VALUES)
    for j, b_val in enumerate(TIEN_B_VALUES)
]


class TestTienExperimentalTables:
    """Сверка формулы (3.1) с таблицами 2.5, 2.7, 2.9, 2.11, 2.13, 2.15 Тиена (≤ 2 %)."""

    @pytest.mark.parametrize("volume,l,b,h_zs_model", TIEN_EXPERIMENTAL_CASES)
    def test_matches_dissertation_table(
        self, volume: int, l: float, b: float, h_zs_model: float
    ) -> None:
        tank = TankCatalog.resolve(volume)
        expected_rel_h = h_zs_model / tank.model_water_level_m
        actual_rel_h = GWKWall._relative_height(
            tank.diameter_m, tank.wall_height_m, l, b
        )
        rel_error = abs(actual_rel_h - expected_rel_h) / expected_rel_h * 100.0
        assert rel_error <= 2.0, (
            f"РВС-{volume} (l={l}, b={b}): расчёт={actual_rel_h:.4f}, "
            f"эксперимент={expected_rel_h:.4f}, погрешность={rel_error:.2f}% > 2%"
        )