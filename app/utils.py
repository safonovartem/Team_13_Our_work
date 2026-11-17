"""Мелкие утилиты, используемые в разных слоях приложения."""

from __future__ import annotations

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Текущее время в UTC (timezone-aware)."""
    return datetime.now(timezone.utc)


def utcnow_iso() -> str:
    """Текущее время UTC в виде строки, пригодной для хранения и сортировки."""
    return utcnow().isoformat(timespec="microseconds")
