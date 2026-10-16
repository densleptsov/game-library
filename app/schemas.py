"""Pydantic-схемы: запросы и ответы API.

Отделены от ORM-моделей, чтобы контролировать, что клиент
отправляет и что получает. Секретные поля (hashed_password)
не попадают в ответы по дизайну.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import LibraryStatus

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


# --- Game ---


class GameBase(BaseModel):
    """Общие поля Game для создания и обновления."""

    title: str = Field(min_length=1, max_length=255)
    platform: str = Field(min_length=1, max_length=50)
    genre: str | None = Field(default=None, max_length=50)
    release_year: int | None = Field(default=None, ge=1950, le=2100)
    cover_url: str | None = Field(default=None, max_length=500)


class GameCreate(GameBase):
    """Тело запроса POST /games."""

    pass


class GameUpdate(BaseModel):
    """Тело запроса PATCH /games/{id}. Все поля опциональны."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    platform: str | None = Field(default=None, min_length=1, max_length=50)
    genre: str | None = Field(default=None, max_length=50)
    release_year: int | None = Field(default=None, ge=1950, le=2100)
    cover_url: str | None = Field(default=None, max_length=500)


class GamePublic(BaseModel):
    """Ответ API с данными игры."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    platform: str
    genre: str | None
    release_year: int | None
    cover_url: str | None
    created_at: datetime


# --- Library ---


class LibraryEntryCreate(BaseModel):
    """Тело запроса POST /library."""

    game_id: int
    status: LibraryStatus = LibraryStatus.planned
    rating: int | None = Field(default=None, ge=1, le=10)
    hours_played: int | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=1000)


class LibraryEntryUpdate(BaseModel):
    """Тело запроса PATCH /library/{id}. Все поля опциональны."""

    status: LibraryStatus | None = None
    rating: int | None = Field(default=None, ge=1, le=10)
    hours_played: int | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=1000)


class LibraryEntryPublic(BaseModel):
    """Ответ API с записью в библиотеке. Game вложен целиком."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    game: GamePublic
    status: LibraryStatus
    rating: int | None
    hours_played: int | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


# --- Общее: пагинация ---


class GameList(BaseModel):
    """Ответ GET /games — список игр с пагинацией."""

    total: int
    items: list[GamePublic]


class LibraryList(BaseModel):
    """Ответ GET /library — список записей с пагинацией."""

    total: int
    items: list[LibraryEntryPublic]
