"""Pydantic-схемы: запросы и ответы API.

Отделены от ORM-моделей, чтобы контролировать, что клиент
отправляет и что получает. Секретные поля (hashed_password)
не попадают в ответы по дизайну.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --- User ---

class UserCreate(BaseModel):
    """Тело запроса POST /auth/register."""

    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="3–50 символов: буквы, цифры, _ и -",
    )
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class UserPublic(BaseModel):
    """Публичные данные пользователя (без пароля)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    created_at: datetime


# --- Auth ---

class LoginRequest(BaseModel):
    """Тело запроса POST /auth/login."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Ответ на успешный логин."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int