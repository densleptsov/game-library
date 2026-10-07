"""Настройки приложения. Читаются из .env через pydantic-settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Все настройки приложения в одном месте.

    Значения берутся из переменных окружения или из файла .env.
    Имена полей (в нижнем регистре) соответствуют переменным (в верхнем).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Приложение ---
    app_name: str = "Game Library API"
    debug: bool = True

    # --- JWT (пригодятся на этапе 3.3) ---
    secret_key: str = "dev-secret-change-me"
    access_token_expire_minutes: int = 30

    # --- База данных (пригодится на этапе 3.2) ---
    database_url: str = "sqlite:///./game_library.db"


# Единственный экземпляр настроек на всё приложение.
# Импортируется из других модулей: `from app.config import settings`
settings = Settings()