"""Сервис расчётов: обёртка над вычислительным ядром ``app.core``.

Слой выполняет три задачи:

1. переводит API-схемы в контракты ядра (``InputData``) и обратно;
2. собирает из результата ядра блоки для интерфейса (``ResultBlock``);
3. готовит наборы данных для графиков Chart.js.

Вычислительная логика здесь не дублируется: все формулы и коэффициенты
берутся из ``app.core`` (ветка ``feature/backend-calculations``).
"""

from __future__ import annotations

import re
from dataclasses import asdict

from app.core import InputData, ResultData, run_engine
from app.core.catalog import TankCatalog
from app.core.exceptions import DomainRangeError
from app.schemas.calculations import (
    SCENARIO_TITLES,
    CalculationInput,
    CalculationResponse,
    CalculationSummary,
    ChartBlock,
    ChartCollection,
    EngineResultRead,
    FrontendFormValues,
    ResultBlock,
    ResultItem,
    SavedCalculation,
    ScenarioKey,
)
from app.services.charts import (
    build_overflow_chart,
    build_wave_charts,
    calculation_clearance_values,
)

#: Объём РВС в строке типа объекта: «РВС-5000 · 5 000 м³».
TANK_VOLUME_PATTERN = re.compile(r"РВС\s*[-–—]?\s*(\d+)", re.IGNORECASE)

#: Идентификаторы блоков, совпадающие с mock-api фронтенда.
SCENARIO_BLOCK_IDS: dict[str, str] = {
    ScenarioKey.PLAIN.value: "no-canopy",
    ScenarioKey.GWK.value: "gvk",
}

DEFAULT_CLEARANCE_L = 3.0
DEFAULT_CREST_WIDTH_B = 1.0


def format_number(value: float, digits: int = 2) -> str:
    """Форматирует число в русской записи (запятая, без лишних нулей)."""
    text = f"{round(float(value), digits):.{digits}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text.replace(".", ",")


def _percent(value: float, digits: int = 1) -> str:
    return f"{format_number(value, digits)} %"


def _meters(value: float, digits: int = 2) -> str:
    return f"{format_number(value, digits)} м"


def _safety_label(score: float) -> str:
    if score >= 90:
        return "Высокая"
    if score >= 70:
        return "Средняя"
    return "Низкая"


def _feasibility_label(score: float) -> str:
    if score >= 80:
        return "Высокая"
    if score >= 60:
        return "Хорошая"
    if score >= 40:
        return "Средняя"
    return "Низкая"


def to_core_input(payload: CalculationInput) -> InputData:
    """Переводит API-схему в контракт вычислительного ядра."""
    return InputData(
        tank_volume=payload.tank_volume,
        clearance_l=payload.clearance_l,
        crest_width_b=payload.crest_width_b,
        plain_wall_height=payload.plain_wall_height,
        scenarios=[scenario.value for scenario in payload.scenarios],
    )


def resolve_form_tank_volume(form: FrontendFormValues) -> int:
    """Определяет объём РВС по значениям формы главной страницы.

    Сначала объём ищется в ``objectType`` (``"РВС-5000 · 5 000 м³"``),
    затем используется числовое поле ``objectVolume``.
    """
    if form.object_type:
        match = TANK_VOLUME_PATTERN.search(form.object_type)
        if match is not None:
            return int(match.group(1))

    if form.object_volume is not None and form.object_volume > 0:
        return int(round(form.object_volume))

    raise DomainRangeError(
        "Не удалось определить объём резервуара. Передайте objectType "
        "(например, «РВС-5000 · 5 000 м³») или objectVolume в м³."
    )


def input_from_form(form: FrontendFormValues) -> CalculationInput:
    """Преобразует ``FormValues`` фронтенда в параметры расчёта.

    В форме главной страницы пока нет полей межстенного расстояния и вылета
    козырька, поэтому используются значения по умолчанию (3.0 и 1.0 м).
    """
    return CalculationInput(
        tank_volume=resolve_form_tank_volume(form),
        clearance_l=(
            DEFAULT_CLEARANCE_L
            if form.clearance_l is None
            else form.clearance_l
        ),
        crest_width_b=(
            DEFAULT_CREST_WIDTH_B
            if form.crest_width_b is None
            else form.crest_width_b
        ),
        plain_wall_height=form.plain_wall_height,
        scenarios=list(form.scenarios) if form.scenarios else [
            ScenarioKey.PLAIN,
            ScenarioKey.GWK,
        ],
    )


def build_result_blocks(result: EngineResultRead) -> list[ResultBlock]:
    """Собирает карточки вариантов для интерфейса.

    Структура повторяет ``ResultBlock`` фронтенда: ``id``, ``title``,
    ``isImportant`` (рекомендуемый вариант) и ``items``.
    """
    blocks: list[ResultBlock] = []
    for variant in result.variants:
        scenario = variant.scenario_type
        items = [
            ResultItem(
                title="Доля перелива",
                value=_percent(variant.overflow_pct),
            ),
            ResultItem(
                title="Объём перелива",
                value=f"{format_number(variant.overflow_volume_m3, 1)} м³",
            ),
            ResultItem(
                title="Высота стенки",
                value=(
                    f"{_meters(variant.wall_height_m)} "
                    f"({format_number(variant.relative_height * 100, 0)} % от h₀)"
                ),
            ),
            ResultItem(
                title="Экономия высоты",
                value=_meters(max(variant.height_savings_m, 0.0)),
            ),
            ResultItem(
                title="Безопасность",
                value=_safety_label(variant.safety_score),
            ),
            ResultItem(
                title="Материалоёмкость",
                value=f"{format_number(variant.capex_raw, 1)} м² бетона",
            ),
            ResultItem(
                title="Реализуемость",
                value=_feasibility_label(variant.feasibility_rank),
            ),
        ]

        if variant.overflow_pct > 0 and variant.secondary_wall_height_m > 0:
            items.append(
                ResultItem(
                    title="Второй рубеж",
                    value=(
                        f"{_meters(variant.secondary_wall_dist_m, 1)} × "
                        f"{_meters(variant.secondary_wall_height_m, 1)}"
                    ),
                )
            )

        blocks.append(
            ResultBlock(
                id=SCENARIO_BLOCK_IDS.get(scenario, scenario),
                scenario=scenario,
                title=SCENARIO_TITLES.get(scenario, scenario),
                is_important=scenario == result.recommended_variant,
                items=items,
            )
        )
    return blocks


def build_charts(
    result: ResultData, payload: CalculationInput
) -> list[ChartBlock]:
    """Набор графиков для результата расчёта."""
    tank = TankCatalog.resolve(payload.tank_volume)
    charts = [
        build_overflow_chart(
            tank, calculation_clearance_values(payload.clearance_l)
        )
    ]
    charts.extend(build_wave_charts(result.wave, payload.clearance_l))
    return charts


def run_calculation(payload: CalculationInput) -> CalculationResponse:
    """Выполняет расчёт и возвращает ответ, готовый для фронтенда.

    Raises:
        DomainRangeError: Если параметры выходят за границы применимости
            формул (обрабатывается как HTTP 422).
    """
    core_result = run_engine(to_core_input(payload))
    engine_result = EngineResultRead.model_validate(asdict(core_result))

    return CalculationResponse(
        input=payload,
        result=engine_result,
        variants=build_result_blocks(engine_result),
        charts=build_charts(core_result, payload),
        recommended_variant=core_result.recommended_variant,
    )


def run_calculation_from_form(form: FrontendFormValues) -> CalculationResponse:
    """Расчёт по значениям формы главной страницы."""
    return run_calculation(input_from_form(form))


def charts_from_record(record: dict) -> ChartCollection:
    """Восстанавливает набор графиков из записи БД."""
    return ChartCollection(
        charts=[
            ChartBlock.model_validate(chart)
            for chart in record["charts"]
        ]
    )


def saved_calculation_from_record(record: dict) -> SavedCalculation:
    """Преобразует запись репозитория в ответ API."""
    result = EngineResultRead.model_validate(record["result_data"])
    return SavedCalculation(
        id=record["id"],
        project_id=record["project_id"],
        created_at=record["created_at"],
        input=CalculationInput.model_validate(record["input_data"]),
        result=result,
        variants=build_result_blocks(result),
        charts=charts_from_record(record).charts,
        recommended_variant=record["recommended_variant"],
    )


def calculation_summary_from_record(record: dict) -> CalculationSummary:
    """Краткая запись для списка истории расчётов проекта."""
    return CalculationSummary(
        id=record["id"],
        project_id=record["project_id"],
        input=CalculationInput.model_validate(record["input_data"]),
        recommended_variant=record["recommended_variant"],
        has_form_data=record["form_data"] is not None,
        created_at=record["created_at"],
    )
