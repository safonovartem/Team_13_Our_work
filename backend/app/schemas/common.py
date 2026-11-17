"""Общие Pydantic-модели."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class APIModel(BaseModel):
    """Модель входящего запроса: лишние поля запрещены."""

    model_config = ConfigDict(extra="forbid")


class ResponseModel(BaseModel):
    """Модель ответа: неописанные поля (например, hash пароля) игнорируются."""

    model_config = ConfigDict(extra="ignore", from_attributes=True)


class Page(ResponseModel, Generic[T]):
    """Стандартный ответ со списком и пагинацией."""

    items: list[T]
    total: int
    limit: int
    offset: int
