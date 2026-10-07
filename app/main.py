"""Точка входа FastAPI-приложения."""
from fastapi import FastAPI

from app.config import settings


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    version="0.1.0",
)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    """Проверка живости сервиса."""
    return {"status": "ok"}