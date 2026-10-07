"""ORM-модели: User, Game, LibraryEntry.

Соответствуют docs/data-model.md.
При изменении здесь — обновляй документ, и наоборот.
"""
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Enum as SAEnum,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LibraryStatus(str, enum.Enum):
    """Статус прохождения игры пользователем.

    Наследуемся от str, чтобы значение автоматически работало
    в JSON-сериализации (Pydantic) и SQL.
    """

    planned = "planned"
    playing = "playing"
    completed = "completed"
    dropped = "dropped"


class User(Base):
    """Пользователь сервиса."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    # Связь: у пользователя много записей в библиотеке.
    # cascade="all, delete-orphan" — при удалении User удаляются его entries
    # (на уровне ORM; на уровне БД — через ondelete="CASCADE").
    entries: Mapped[list[LibraryEntry]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username!r})>"


class Game(Base):
    """Игра в общем каталоге."""

    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    platform: Mapped[str] = mapped_column(String(50))
    genre: Mapped[str | None] = mapped_column(String(50), default=None)
    release_year: Mapped[int | None] = mapped_column(default=None)
    cover_url: Mapped[str | None] = mapped_column(String(500), default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    entries: Mapped[list[LibraryEntry]] = relationship(
        back_populates="game",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        CheckConstraint(
            "release_year IS NULL OR (release_year BETWEEN 1950 AND 2100)",
            name="ck_games_release_year",
        ),
    )

    def __repr__(self) -> str:
        return f"<Game(id={self.id}, title={self.title!r}, platform={self.platform!r})>"


class LibraryEntry(Base):
    """Запись в библиотеке: связка User ↔ Game с метаданными."""

    __tablename__ = "library_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"))

    status: Mapped[LibraryStatus] = mapped_column(
        SAEnum(LibraryStatus, native_enum=False, length=20),
        default=LibraryStatus.planned,
    )
    rating: Mapped[int | None] = mapped_column(default=None)
    hours_played: Mapped[int | None] = mapped_column(default=0)
    notes: Mapped[str | None] = mapped_column(String(1000), default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="entries")
    game: Mapped[Game] = relationship(back_populates="entries")

    __table_args__ = (
        UniqueConstraint("user_id", "game_id", name="uq_library_user_game"),
        CheckConstraint(
            "rating IS NULL OR (rating BETWEEN 1 AND 10)",
            name="ck_library_rating",
        ),
        CheckConstraint(
            "hours_played IS NULL OR hours_played >= 0",
            name="ck_library_hours",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<LibraryEntry(id={self.id}, user_id={self.user_id}, "
            f"game_id={self.game_id}, status={self.status.value!r})>"
        )