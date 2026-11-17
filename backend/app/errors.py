"""Доменные исключения.

Слой репозиториев не зависит от FastAPI, поэтому он сообщает об ошибках
собственными исключениями. Обработчики в ``app.factory`` переводят их в
HTTP-ответы единого формата.
"""

from __future__ import annotations


class DomainError(Exception):
    """Базовая ошибка предметной области."""

    status_code = 400
    code = "bad_request"

    def __init__(
        self,
        message: str,
        *,
        field: str | None = None,
        code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.field = field
        self.code = code or type(self).code


class NotFoundError(DomainError):
    """Запрошенный объект не существует."""

    status_code = 404
    code = "not_found"


class BadRequestError(DomainError):
    """Запрос корректен синтаксически, но нарушает бизнес-правило."""

    status_code = 400
    code = "bad_request"


class ConflictError(DomainError):
    """Нарушено ограничение уникальности или бизнес-правило."""

    status_code = 409
    code = "conflict"
