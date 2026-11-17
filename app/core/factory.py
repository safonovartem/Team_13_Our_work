"""Фабрика стратегий расчёта защитных ограждений (Factory Method).

Создаёт нужную стратегию ``BaseWall`` по строковому ключу сценария.
"""
from __future__ import annotations

from .barriers.base import BaseWall
from .barriers.gwk import GWKWall
from .barriers.plain_wall import PlainWall


class WallFactory:
    """Factory Method для создания стратегий расчёта ограждений.

    Поддерживаемые ключи:
    - ``"plain"`` → :class:`PlainWall` (Швырков: стенка без козырька).
    - ``"gwk"`` → :class:`GWKWall` (Тиен: горизонтальный козырёк 90°).

    Пример использования::

        wall = WallFactory.create("gwk")
        result = wall.calculate(tank, l, b, None, v0)
    """

    _REGISTRY: dict[str, type[BaseWall]] = {
        "plain": PlainWall,
        "gwk": GWKWall,
    }

    @classmethod
    def create(cls, scenario_key: str) -> BaseWall:
        """Создать экземпляр стратегии по ключу сценария.

        Parameters:
            scenario_key: Ключ сценария (``"plain"`` или ``"gwk"``).

        Returns:
            Экземпляр конкретной стратегии ``BaseWall``.

        Raises:
            KeyError: Если ключ не зарегистрирован.
        """
        wall_cls = cls._REGISTRY.get(scenario_key)
        if wall_cls is None:
            available: str = ", ".join(sorted(cls._REGISTRY.keys()))
            raise KeyError(
                f"Неизвестный сценарий ограждения: '{scenario_key}'. "
                f"Допустимые значения: {available}."
            )
        return wall_cls()
