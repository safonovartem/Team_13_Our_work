"""Точка входа для ASGI-сервера: ``uvicorn app.main:app``."""

from app.factory import create_app

app = create_app()
