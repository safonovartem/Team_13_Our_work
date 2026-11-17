"""Схемы проектов и истории версий исходных данных."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import Field, field_validator, model_validator

from app.schemas.common import APIModel, ResponseModel
from app.schemas.inputs import ProjectInputData
from app.validators import strip_required_text


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    ARCHIVED = "archived"


class ProjectCreate(APIModel):
    """Создание проекта."""

    name: str = Field(
        min_length=1, max_length=120, examples=["Резервуарный парк №1"]
    )
    description: str | None = Field(default=None, max_length=2000)
    status: ProjectStatus = Field(
        default=ProjectStatus.DRAFT, description="Статус проекта"
    )
    input_data: ProjectInputData | None = Field(
        default=None, description="Исходные данные (необязательно)"
    )
    comment: str | None = Field(
        default=None,
        max_length=500,
        description="Комментарий к первой версии исходных данных",
    )

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str) -> str:
        return strip_required_text(value, field_name="Название проекта")

    @field_validator("description", "comment")
    @classmethod
    def _normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class ProjectUpdate(APIModel):
    """Частичное обновление проекта.

    Если передано ``input_data``, создаётся новая версия в истории проекта.
    """

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    status: ProjectStatus | None = None
    input_data: ProjectInputData | None = None
    version_comment: str | None = Field(default=None, max_length=500)

    @field_validator("name")
    @classmethod
    def _validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return strip_required_text(value, field_name="Название проекта")

    @field_validator("description", "version_comment")
    @classmethod
    def _normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @model_validator(mode="after")
    def _check_not_null(self) -> "ProjectUpdate":
        for field_name in ("name", "status"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"Поле {field_name} не может быть пустым")
        if "input_data" in self.model_fields_set and self.input_data is None:
            raise ValueError("input_data не может быть null")
        return self


class ProjectSummary(ResponseModel):
    """Краткие сведения о проекте (для списка)."""

    id: int
    name: str
    description: str | None = None
    status: ProjectStatus
    current_version: int = 0
    versions_count: int = 0
    created_at: datetime
    updated_at: datetime


class ProjectRead(ProjectSummary):
    """Проект вместе с актуальными исходными данными."""

    input_data: ProjectInputData | None = None


class ProjectVersionCreate(APIModel):
    """Ручное сохранение версии исходных данных.

    Если ``input_data`` не передан, сохраняется текущий набор данных проекта.
    """

    input_data: ProjectInputData | None = None
    comment: str | None = Field(default=None, max_length=500)

    @field_validator("comment")
    @classmethod
    def _normalize_comment(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class ProjectVersionRead(ResponseModel):
    """Снимок исходных данных проекта."""

    id: int
    project_id: int
    version: int
    input_data: ProjectInputData
    comment: str | None = None
    created_by: int | None = None
    created_at: datetime
