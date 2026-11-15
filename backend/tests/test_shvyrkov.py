"""Тесты формулы (4.1) Швыркова: доля перелива Q и параметры второго рубежа.

Проверяет:
- Расчёт Q при h_зс = 1.1·h0 → Q = 0 % (полное удержание).
- Расчёт Q при промежуточных значениях h_зс / h0 для всех 6 типоразмеров.
- Кусочно-линейную интерполяцию параметров второго рубежа (табл. 4.2).
- Монотонность: при увеличении h_зс/h0 перелив Q убывает.
"""
from __future__ import annotations

import math

import pytest


from app.core.catalog import TankCatalog, TANK_CATALOG
from app.core.barriers.plain_wall import PlainWall
from app.core.constants import FULL_CONTAINMENT_FACTOR, SHVYRKOV_A0, SHVYRKOV_A1, SHVYRKOV_A2


# ──────────────────────────────────────────────────────────────────────────────
# Вспомогательные функции
# ──────────────────────────────────────────────────────────────────────────────

def _compute_q_shvyrkov(d_vn: float, h0: float, clearance_l: float, rel_h: float) -> float:
    """Эталонная формула (4.1) Швыркова для проверки."""
    r = d_vn / 2.0
    big_l = r + clearance_l
    q = SHVYRKOV_A0 + SHVYRKOV_A1 * (big_l / r) + SHVYRKOV_A2 * math.sqrt(rel_h)
    return max(0.0, q)


def _v0(d_vn: float, h0: float) -> float:
    """Объём воды в резервуаре."""
    return math.pi * d_vn ** 2 / 4.0 * h0


def _basin_sufficient(d_vn: float, h0: float, clearance_l: float, rel_h: float) -> bool:
    """Проверка: достаточна ли ёмкость чаши при данных параметрах."""
    r = d_vn / 2.0
    big_l = r + clearance_l
    h_zs = rel_h * h0
    v_basin = math.pi * big_l ** 2 * h_zs
    v0 = _v0(d_vn, h0)
    return v_basin >= v0


# ──────────────────────────────────────────────────────────────────────────────
# Параметризация по всем 6 типоразмерам
# ──────────────────────────────────────────────────────────────────────────────

ALL_VOLUMES = sorted(TANK_CATALOG.keys())


class TestShvyrkovOverflowQ:
    """Тесты доли перелива Q по формуле (4.1) Швыркова."""

    @pytest.mark.parametrize("volume", ALL_VOLUMES)
    def test_full_containment_q_zero(self, volume: int) -> None:
        """При h_зс = 1.1·h0 перелив Q = 0 % для всех типоразмеров."""
        tank = TankCatalog.resolve(volume)
        clearance_l = 1.5
        v0 = _v0(tank.diameter_m, tank.wall_height_m)
        plain = PlainWall()
        result = plain.calculate(
            tank=tank,
            clearance_l=clearance_l,
            crest_width_b=0.5,
            plain_wall_height=FULL_CONTAINMENT_FACTOR * tank.wall_height_m,
            liquid_volume_m3=v0,
        )
        assert result.overflow_pct == 0.0, (
            f"РВС-{volume}: ожидался Q=0% при h_зс=1.1·h0, получено Q={result.overflow_pct}%"
        )
        assert result.safety_score == 100.0

    @pytest.mark.parametrize("volume", ALL_VOLUMES)
    def test_q_at_rel_height_0_8(self, volume: int) -> None:
        """Проверка Q при h_зс/h0 = 0.8 для всех типоразмеров.

        Используем достаточно большое l, чтобы V_чаши >= V0 и коррекция
        высоты не срабатывала, позволяя проверить чистую формулу (4.1).
        """
        tank = TankCatalog.resolve(volume)
        # Подбираем l, при котором чаша достаточна
        rel_h = 0.8
        for clearance_l in [1.5, 2.0, 2.5, 3.0]:
            if _basin_sufficient(tank.diameter_m, tank.wall_height_m, clearance_l, rel_h):
                break
        else:
            pytest.skip(f"РВС-{volume}: невозможно найти l при котором V_чаши >= V0 для rel_h=0.8")

        h_zs = rel_h * tank.wall_height_m
        v0 = _v0(tank.diameter_m, tank.wall_height_m)

        # Эталонный расчёт
        q_expected = _compute_q_shvyrkov(tank.diameter_m, tank.wall_height_m, clearance_l, rel_h)

        plain = PlainWall()
        result = plain.calculate(
            tank=tank,
            clearance_l=clearance_l,
            crest_width_b=0.5,
            plain_wall_height=h_zs,
            liquid_volume_m3=v0,
        )

        assert abs(result.overflow_pct - q_expected) < 0.01, (
            f"РВС-{volume}, l={clearance_l}: Q ожидался {q_expected:.4f}%, "
            f"получено {result.overflow_pct}%"
        )

    @pytest.mark.parametrize("volume", ALL_VOLUMES)
    def test_q_at_rel_height_0_9(self, volume: int) -> None:
        """Проверка Q при h_зс/h0 = 0.9 для всех типоразмеров."""
        tank = TankCatalog.resolve(volume)
        rel_h = 0.9
        for clearance_l in [1.5, 2.0, 2.5, 3.0]:
            if _basin_sufficient(tank.diameter_m, tank.wall_height_m, clearance_l, rel_h):
                break
        else:
            pytest.skip(f"РВС-{volume}: невозможно найти l для rel_h=0.9")

        h_zs = rel_h * tank.wall_height_m
        v0 = _v0(tank.diameter_m, tank.wall_height_m)

        q_expected = _compute_q_shvyrkov(tank.diameter_m, tank.wall_height_m, clearance_l, rel_h)

        plain = PlainWall()
        result = plain.calculate(
            tank=tank,
            clearance_l=clearance_l,
            crest_width_b=0.5,
            plain_wall_height=h_zs,
            liquid_volume_m3=v0,
        )

        assert abs(result.overflow_pct - q_expected) < 0.01, (
            f"РВС-{volume}, l={clearance_l}: Q ожидался {q_expected:.4f}%, "
            f"получено {result.overflow_pct}%"
        )

    @pytest.mark.parametrize("volume", ALL_VOLUMES)
    def test_overflow_volume_consistent(self, volume: int) -> None:
        """V_пер = V0 · Q / 100 — проверка согласованности объёма перелива."""
        tank = TankCatalog.resolve(volume)
        clearance_l = 3.0  # максимальный зазор для надёжного V_чаши
        rel_h = 0.85
        h_zs = rel_h * tank.wall_height_m
        v0 = _v0(tank.diameter_m, tank.wall_height_m)

        plain = PlainWall()
        result = plain.calculate(
            tank=tank,
            clearance_l=clearance_l,
            crest_width_b=0.5,
            plain_wall_height=h_zs,
            liquid_volume_m3=v0,
        )

        expected_v = v0 * result.overflow_pct / 100.0
        assert abs(result.overflow_volume_m3 - round(expected_v, 2)) < 1.0, (
            f"РВС-{volume}: V_пер не согласован: "
            f"Q={result.overflow_pct}%, V_пер={result.overflow_volume_m3}, "
            f"ожидался ≈{expected_v:.2f}"
        )

    @pytest.mark.parametrize("volume", ALL_VOLUMES)
    def test_monotonicity(self, volume: int) -> None:
        """Q монотонно убывает с ростом h_зс/h0 (при неизменных прочих параметрах).

        Используем достаточно большой l=3.0, чтобы избежать коррекции чаши.
        """
        tank = TankCatalog.resolve(volume)
        clearance_l = 3.0
        v0 = _v0(tank.diameter_m, tank.wall_height_m)
        plain = PlainWall()

        prev_q = 100.0
        for rel_h_100 in range(40, 111, 5):
            rel_h = rel_h_100 / 100.0
            h_zs = rel_h * tank.wall_height_m
            result = plain.calculate(
                tank=tank,
                clearance_l=clearance_l,
                crest_width_b=0.5,
                plain_wall_height=h_zs,
                liquid_volume_m3=v0,
            )
            assert result.overflow_pct <= prev_q + 0.01, (
                f"РВС-{volume}: Q не монотонна при h_зс/h0={rel_h}: "
                f"Q={result.overflow_pct}%, предыдущее={prev_q}%"
            )
            prev_q = result.overflow_pct

    @pytest.mark.parametrize("volume", ALL_VOLUMES)
    def test_basin_correction_raises_height(self, volume: int) -> None:
        """При V_чаши < V0 высота стенки увеличивается, и относительная высота растёт."""
        tank = TankCatalog.resolve(volume)
        clearance_l = 1.5
        rel_h_input = 0.8
        h_zs_input = rel_h_input * tank.wall_height_m
        v0 = _v0(tank.diameter_m, tank.wall_height_m)

        plain = PlainWall()
        result = plain.calculate(
            tank=tank,
            clearance_l=clearance_l,
            crest_width_b=0.5,
            plain_wall_height=h_zs_input,
            liquid_volume_m3=v0,
        )

        if not result.engineering_details.is_basin_capacity_sufficient:
            # Высота должна быть увеличена
            assert result.wall_height_m >= h_zs_input, (
                f"РВС-{volume}: высота стенки не скорректирована при V_чаши < V0"
            )
            assert result.relative_height >= rel_h_input


class TestSecondBarrier:
    """Тесты кусочно-линейной интерполяции параметров второго рубежа (табл. 4.2)."""

    def test_at_rel_0_8(self) -> None:
        """При h_зс/h0 = 0.8: l_доп = 7.0 м, h_доп = 2.0 м."""
        l_d, h_d = PlainWall._second_barrier_params(0.8)
        assert l_d == 7.0
        assert h_d == 2.0

    def test_at_rel_0_9(self) -> None:
        """При h_зс/h0 = 0.9: l_доп = 5.0 м, h_доп = 2.0 м."""
        l_d, h_d = PlainWall._second_barrier_params(0.9)
        assert l_d == 5.0
        assert h_d == 2.0

    def test_at_rel_1_0(self) -> None:
        """При h_зс/h0 = 1.0: l_доп = 5.0 м, h_доп = 1.5 м."""
        l_d, h_d = PlainWall._second_barrier_params(1.0)
        assert l_d == 5.0
        assert h_d == 1.5

    def test_interpolation_0_85(self) -> None:
        """При h_зс/h0 = 0.85: интерполяция между (0.8, 7, 2) и (0.9, 5, 2)."""
        l_d, h_d = PlainWall._second_barrier_params(0.85)
        assert abs(l_d - 6.0) < 0.01  # (7 + 5) / 2
        assert abs(h_d - 2.0) < 0.01

    def test_interpolation_0_95(self) -> None:
        """При h_зс/h0 = 0.95: интерполяция между (0.9, 5, 2) и (1.0, 5, 1.5)."""
        l_d, h_d = PlainWall._second_barrier_params(0.95)
        assert abs(l_d - 5.0) < 0.01
        assert abs(h_d - 1.75) < 0.01  # (2.0 + 1.5) / 2

    def test_above_1_0(self) -> None:
        """При h_зс/h0 > 1.0 — безопасные значения (5.0, 1.5)."""
        l_d, h_d = PlainWall._second_barrier_params(1.05)
        assert l_d == 5.0
        assert h_d == 1.5

    def test_below_0_8(self) -> None:
        """При h_зс/h0 ≤ 0.8 — значения первой точки (7.0, 2.0)."""
        l_d, h_d = PlainWall._second_barrier_params(0.7)
        assert l_d == 7.0
        assert h_d == 2.0


class TestPlainWallHeightSavings:
    """Экономия высоты и CAPEX для PlainWall."""

    @pytest.mark.parametrize("volume", ALL_VOLUMES)
    def test_height_savings_at_full_containment(self, volume: int) -> None:
        """При h_зс = 1.1·h0 экономия = 0."""
        tank = TankCatalog.resolve(volume)
        v0 = _v0(tank.diameter_m, tank.wall_height_m)
        plain = PlainWall()
        result = plain.calculate(
            tank=tank,
            clearance_l=1.5,
            crest_width_b=0.5,
            plain_wall_height=FULL_CONTAINMENT_FACTOR * tank.wall_height_m,
            liquid_volume_m3=v0,
        )
        assert abs(result.height_savings_m) < 0.001

    @pytest.mark.parametrize("volume", ALL_VOLUMES)
    def test_capex_raw_positive(self, volume: int) -> None:
        """CAPEX всегда положителен."""
        tank = TankCatalog.resolve(volume)
        v0 = _v0(tank.diameter_m, tank.wall_height_m)
        plain = PlainWall()
        result = plain.calculate(
            tank=tank,
            clearance_l=3.0,
            crest_width_b=0.5,
            plain_wall_height=0.8 * tank.wall_height_m,
            liquid_volume_m3=v0,
        )
        assert result.capex_raw > 0
# ──────────────────────────────────────────────────────────────────────────────
# Экспериментальные данные из Приложения А диссертации А. С. Швыркова (стр. 131–138):
# Табл. А.1 (РВС-700), А.2 (РВС-2000), А.3 (РВС-5000),
# А.4 (РВС-10000), А.5 (РВС-20000), А.6 (РВС-30000) — всего 264 опыта.
# Формат кортежа: (tank_volume_m3, clearance_l_m, rel_h, expected_q_pct)
# ──────────────────────────────────────────────────────────────────────────────

SHVYRKOV_APPENDIX_A: list[tuple[int, float, float, float]] = [
    # Таблица А.1 — РВС-700 м³ (масштаб 1:30, l_мод = 0.050, 0.070, 0.080, 0.100 м)
    (700, 1.5, 0.717, 10.323), (700, 1.5, 0.733, 9.271), (700, 1.5, 0.767, 7.582),
    (700, 1.5, 0.800, 6.157),  (700, 1.5, 0.833, 4.951), (700, 1.5, 0.867, 3.745),
    (700, 1.5, 0.900, 2.540),  (700, 1.5, 0.933, 1.553), (700, 1.5, 0.967, 0.457),
    (700, 1.5, 0.993, 0.000),
    (700, 2.1, 0.633, 11.090), (700, 2.1, 0.667, 9.140), (700, 2.1, 0.700, 7.581),
    (700, 2.1, 0.733, 5.891),  (700, 2.1, 0.767, 4.981), (700, 2.1, 0.800, 3.551),
    (700, 2.1, 0.833, 2.511),  (700, 2.1, 0.867, 1.471), (700, 2.1, 0.900, 0.561),
    (700, 2.1, 0.930, 0.000),
    (700, 2.4, 0.583, 12.555), (700, 2.4, 0.590, 11.710), (700, 2.4, 0.623, 9.598),
    (700, 2.4, 0.657, 7.908),  (700, 2.4, 0.690, 6.500),  (700, 2.4, 0.723, 5.092),
    (700, 2.4, 0.757, 4.107),  (700, 2.4, 0.790, 2.980),  (700, 2.4, 0.823, 2.135),
    (700, 2.4, 0.857, 1.149),  (700, 2.4, 0.890, 0.586),  (700, 2.4, 0.910, 0.000),
    (700, 3.0, 0.517, 16.970), (700, 3.0, 0.533, 14.514), (700, 3.0, 0.567, 11.566),
    (700, 3.0, 0.600, 9.437),  (700, 3.0, 0.633, 7.799),  (700, 3.0, 0.667, 6.325),
    (700, 3.0, 0.700, 5.015),  (700, 3.0, 0.733, 3.705),  (700, 3.0, 0.767, 2.558),
    (700, 3.0, 0.800, 1.412),  (700, 3.0, 0.873, 0.000),

    # Таблица А.2 — РВС-2000 м³ (масштаб 1:43, l_мод = 0.035, 0.049, 0.056, 0.070 м)
    (2000, 1.5, 0.768, 8.378), (2000, 1.5, 0.804, 6.608), (2000, 1.5, 0.839, 5.151),
    (2000, 1.5, 0.875, 4.213), (2000, 1.5, 0.911, 3.276), (2000, 1.5, 0.946, 1.923),
    (2000, 1.5, 0.982, 0.986), (2000, 1.5, 1.000, 0.361), (2000, 1.5, 1.018, 0.000),
    (2000, 2.1, 0.686, 10.918), (2000, 2.1, 0.721, 8.667), (2000, 2.1, 0.757, 7.127),
    (2000, 2.1, 0.793, 5.587),  (2000, 2.1, 0.829, 4.284), (2000, 2.1, 0.864, 2.981),
    (2000, 2.1, 0.900, 1.678),  (2000, 2.1, 0.936, 0.612), (2000, 2.1, 0.957, 0.000),
    (2000, 2.4, 0.650, 11.562), (2000, 2.4, 0.686, 9.294), (2000, 2.4, 0.721, 7.531),
    (2000, 2.4, 0.757, 5.968),  (2000, 2.4, 0.793, 4.633), (2000, 2.4, 0.829, 3.373),
    (2000, 2.4, 0.864, 2.239),  (2000, 2.4, 0.900, 0.980), (2000, 2.4, 0.925, 0.000),
    (2000, 3.0, 0.586, 10.579), (2000, 3.0, 0.621, 8.453), (2000, 3.0, 0.657, 7.320),
    (2000, 3.0, 0.693, 6.044),  (2000, 3.0, 0.729, 4.910), (2000, 3.0, 0.764, 3.635),
    (2000, 3.0, 0.800, 2.558),  (2000, 3.0, 0.836, 1.764), (2000, 3.0, 0.871, 0.943),
    (2000, 3.0, 0.914, 0.000),

    # Таблица А.3 — РВС-5000 м³ (масштаб 1:60, l_мод = 0.025, 0.035, 0.040, 0.050 м)
    (5000, 1.5, 0.836, 8.276), (5000, 1.5, 0.868, 6.816), (5000, 1.5, 0.900, 5.357),
    (5000, 1.5, 0.932, 4.210), (5000, 1.5, 0.964, 3.064), (5000, 1.5, 0.996, 2.022),
    (5000, 1.5, 1.028, 0.979), (5000, 1.5, 1.068, 0.000),
    (5000, 2.1, 0.764, 11.515), (5000, 2.1, 0.804, 9.101), (5000, 2.1, 0.848, 7.033),
    (5000, 2.1, 0.864, 6.228),  (5000, 2.1, 0.884, 5.309), (5000, 2.1, 0.904, 4.620),
    (5000, 2.1, 0.916, 4.275),  (5000, 2.1, 0.940, 3.355), (5000, 2.1, 0.964, 2.551),
    (5000, 2.1, 0.980, 2.091),  (5000, 2.1, 1.012, 0.483), (5000, 2.1, 1.048, 0.000),
    (5000, 2.4, 0.732, 12.430), (5000, 2.4, 0.760, 10.503), (5000, 2.4, 0.796, 8.455),
    (5000, 2.4, 0.828, 6.889),  (5000, 2.4, 0.860, 5.444),  (5000, 2.4, 0.892, 4.480),
    (5000, 2.4, 0.924, 2.794),  (5000, 2.4, 0.964, 1.228),  (5000, 2.4, 1.032, 0.000),
    (5000, 3.0, 0.700, 10.823), (5000, 3.0, 0.716, 9.635), (5000, 3.0, 0.740, 8.448),
    (5000, 3.0, 0.756, 7.789),  (5000, 3.0, 0.772, 6.865), (5000, 3.0, 0.800, 5.678),
    (5000, 3.0, 0.820, 4.886),  (5000, 3.0, 0.840, 4.227), (5000, 3.0, 0.860, 3.567),
    (5000, 3.0, 0.880, 2.776),  (5000, 3.0, 0.900, 2.116), (5000, 3.0, 0.940, 0.929),
    (5000, 3.0, 0.968, 0.000),

    # Таблица А.4 — РВС-10000 м³ (масштаб 1:81, l_мод = 0.019, 0.026, 0.030, 0.037 м)
    (10000, 1.5, 0.877, 6.718), (10000, 1.5, 0.891, 6.166), (10000, 1.5, 0.905, 5.614),
    (10000, 1.5, 0.923, 4.841), (10000, 1.5, 0.945, 4.068), (10000, 1.5, 0.977, 2.854),
    (10000, 1.5, 1.000, 2.081), (10000, 1.5, 1.023, 1.088), (10000, 1.5, 1.045, 0.536),
    (10000, 1.5, 1.068, 0.000),
    (10000, 2.1, 0.791, 9.867), (10000, 2.1, 0.814, 8.634), (10000, 2.1, 0.836, 7.524),
    (10000, 2.1, 0.859, 6.538), (10000, 2.1, 0.882, 5.551), (10000, 2.1, 0.905, 4.688),
    (10000, 2.1, 0.941, 3.455), (10000, 2.1, 0.964, 2.592), (10000, 2.1, 0.995, 1.482),
    (10000, 2.1, 1.018, 0.743), (10000, 2.1, 1.041, 0.000),
    (10000, 2.4, 0.741, 11.880), (10000, 2.4, 0.755, 11.085), (10000, 2.4, 0.768, 10.158),
    (10000, 2.4, 0.782, 9.363),  (10000, 2.4, 0.809, 7.905),  (10000, 2.4, 0.832, 6.845),
    (10000, 2.4, 0.850, 6.050),  (10000, 2.4, 0.859, 5.122),  (10000, 2.4, 0.886, 3.797),
    (10000, 2.4, 0.909, 2.869),  (10000, 2.4, 0.932, 1.942),  (10000, 2.4, 0.964, 1.147),
    (10000, 2.4, 1.000, 0.484),  (10000, 2.4, 1.027, 0.000),
    (10000, 3.0, 0.818, 9.471), (10000, 3.0, 0.832, 8.757), (10000, 3.0, 0.850, 7.327),
    (10000, 3.0, 0.864, 6.613), (10000, 3.0, 0.886, 5.779), (10000, 3.0, 0.895, 5.302),
    (10000, 3.0, 0.909, 4.707), (10000, 3.0, 0.932, 3.992), (10000, 3.0, 0.955, 3.158),
    (10000, 3.0, 1.000, 1.729), (10000, 3.0, 1.023, 0.895), (10000, 3.0, 1.055, 0.000),

    # Таблица А.5 — РВС-20000 м³ (масштаб 1:114, l_мод = 0.013, 0.018, 0.021, 0.026 м)
    (20000, 1.5, 0.906, 5.083), (20000, 1.5, 0.919, 4.645), (20000, 1.5, 0.931, 4.207),
    (20000, 1.5, 0.944, 3.769), (20000, 1.5, 0.956, 3.330), (20000, 1.5, 0.969, 2.892),
    (20000, 1.5, 0.981, 2.454), (20000, 1.5, 0.994, 2.016), (20000, 1.5, 1.006, 1.578),
    (20000, 1.5, 1.038, 0.702), (20000, 1.5, 1.056, 0.000),
    (20000, 2.1, 0.863, 6.564), (20000, 2.1, 0.875, 6.100), (20000, 2.1, 0.888, 5.481),
    (20000, 2.1, 0.900, 5.017), (20000, 2.1, 0.913, 4.553), (20000, 2.1, 0.925, 4.089),
    (20000, 2.1, 0.938, 3.625), (20000, 2.1, 0.950, 3.315), (20000, 2.1, 0.963, 2.851),
    (20000, 2.1, 0.975, 2.387), (20000, 2.1, 0.988, 2.078), (20000, 2.1, 1.000, 1.614),
    (20000, 2.1, 1.013, 1.150), (20000, 2.1, 1.025, 0.685), (20000, 2.1, 1.050, 0.000),
    (20000, 2.4, 0.844, 7.230), (20000, 2.4, 0.856, 6.576), (20000, 2.4, 0.869, 5.922),
    (20000, 2.4, 0.881, 5.431), (20000, 2.4, 0.894, 4.940), (20000, 2.4, 0.906, 4.449),
    (20000, 2.4, 0.919, 3.467), (20000, 2.4, 0.938, 2.486), (20000, 2.4, 0.963, 1.504),
    (20000, 2.4, 0.988, 0.850), (20000, 2.4, 1.025, 0.000),
    (20000, 3.0, 0.800, 8.911), (20000, 3.0, 0.806, 8.575), (20000, 3.0, 0.813, 8.240),
    (20000, 3.0, 0.819, 7.233), (20000, 3.0, 0.831, 5.891), (20000, 3.0, 0.838, 5.556),
    (20000, 3.0, 0.875, 4.046), (20000, 3.0, 0.906, 2.369), (20000, 3.0, 0.919, 1.865),
    (20000, 3.0, 0.944, 0.859), (20000, 3.0, 0.988, 0.000),

    # Таблица А.6 — РВС-30000 м³ (масштаб 1:130, l_мод = 0.012, 0.016, 0.018, 0.023 м)
    (30000, 1.5, 0.921, 5.072), (30000, 1.5, 0.929, 4.744), (30000, 1.5, 0.943, 4.251),
    (30000, 1.5, 0.957, 3.758), (30000, 1.5, 0.964, 3.430), (30000, 1.5, 0.979, 2.937),
    (30000, 1.5, 1.000, 2.280), (30000, 1.5, 1.014, 1.787), (30000, 1.5, 1.036, 0.966),
    (30000, 1.5, 1.050, 0.474), (30000, 1.5, 1.071, 0.000),
    (30000, 2.1, 0.879, 6.465), (30000, 2.1, 0.893, 5.776), (30000, 2.1, 0.907, 5.259),
    (30000, 2.1, 0.929, 4.398), (30000, 2.1, 0.964, 3.192), (30000, 2.1, 0.971, 3.020),
    (30000, 2.1, 1.000, 1.986), (30000, 2.1, 1.029, 1.125), (30000, 2.1, 1.036, 0.953),
    (30000, 2.1, 1.057, 0.264), (30000, 2.1, 1.064, 0.000),
    (30000, 2.4, 0.864, 6.829), (30000, 2.4, 0.871, 6.475), (30000, 2.4, 0.879, 6.122),
    (30000, 2.4, 0.893, 5.591), (30000, 2.4, 0.907, 4.884), (30000, 2.4, 0.929, 4.177),
    (30000, 2.4, 0.950, 3.470), (30000, 2.4, 0.971, 2.763), (30000, 2.4, 1.000, 1.879),
    (30000, 2.4, 1.029, 0.995), (30000, 2.4, 1.043, 0.464), (30000, 2.4, 1.057, 0.000),
    (30000, 3.0, 0.829, 7.999), (30000, 3.0, 0.836, 7.628), (30000, 3.0, 0.843, 7.443),
    (30000, 3.0, 0.857, 6.703), (30000, 3.0, 0.871, 6.518), (30000, 3.0, 0.879, 5.777),
    (30000, 3.0, 0.893, 5.222), (30000, 3.0, 0.921, 4.111), (30000, 3.0, 0.957, 3.000),
    (30000, 3.0, 0.986, 1.705), (30000, 3.0, 1.000, 1.149), (30000, 3.0, 1.029, 0.409),
    (30000, 3.0, 1.050, 0.000),
]

# Рабочий инженерный диапазон проектирования второго рубежа (табл. 4.2: 0.8 <= h_зс/h0 <= 1.1, l <= 2.4 м)
SHVYRKOV_WORKING_RANGE_CASES: list[tuple[int, float, float, float]] = [
    row for row in SHVYRKOV_APPENDIX_A if row[2] >= 0.80 and row[1] <= 2.4
]


class TestShvyrkovAppendixA:
    """Сверка формулы (4.1) с экспериментальными таблицами А.1–А.6 Приложения А."""

    @pytest.mark.parametrize("volume,l,rel_h,expected_q", SHVYRKOV_WORKING_RANGE_CASES)
    def test_matches_appendix_a_working_range(
        self, volume: int, l: float, rel_h: float, expected_q: float
    ) -> None:
        """В рабочем диапазоне (0.8 ≤ h_зс/h0 ≤ 1.1, l ≤ 2.4 м) отклонение |ΔQ| ≤ 2.0 %."""
        tank = TankCatalog.resolve(volume)
        r = tank.diameter_m / 2.0
        actual_q = PlainWall._overflow_q(r + l, r, rel_h)
        abs_error = abs(actual_q - expected_q)
        assert abs_error <= 2.0, (
            f"РВС-{volume} (l={l}, h_зс/h0={rel_h}): расчёт Q={actual_q:.2f}%, "
            f"табл. А={expected_q:.2f}%, отклонение |ΔQ|={abs_error:.2f}% > 2.0%"
        )

    def test_full_appendix_a_regression_accuracy(self) -> None:
        """Проверка статистической точности регрессии (4.1) по всем 264 точкам Приложения А.

        Эталонные показатели из табл. 3.3 диссертации Швыркова:
        - MAE = 0.637 %;
        - Доверительный интервал Δ = 1.732 % (95 %);
        - Коэффициент детерминации R² = 92.91 %.
        """
        errors: list[float] = []
        for volume, l, rel_h, expected_q in SHVYRKOV_APPENDIX_A:
            tank = TankCatalog.resolve(volume)
            r = tank.diameter_m / 2.0
            actual_q = PlainWall._overflow_q(r + l, r, rel_h)
            errors.append(abs(actual_q - expected_q))

        mae = sum(errors) / len(errors)
        within_2pct_ratio = sum(1 for e in errors if e <= 2.0) / len(errors) * 100.0

        assert len(SHVYRKOV_APPENDIX_A) == 264
        assert mae <= 0.70, f"MAE по 264 опытам = {mae:.3f}% (ожидалось ≤ 0.70%)"
        assert within_2pct_ratio >= 93.0, (
            f"Доля опытов с |ΔQ| ≤ 2.0% составила {within_2pct_ratio:.1f}% (ожидалось ≥ 93%)"
        )