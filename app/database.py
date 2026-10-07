"""Настройка подключения к базе данных через SQLAlchemy 2.0.

Содержит:
- Base: базовый класс для всех ORM-моделей.
- engine: подключение к БД (движок).
- SessionLocal: фабрика сессий.
- get_db: FastAPI-зависимость, выдающая сессию в ручки.
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """Базовый класс для ORM-моделей.

    Все модели наследуются от Base, чтобы SQLAlchemy знала о них
    и складывала их описания в Base.metadata (единый каталог схемы).
    """
    pass


# --- Движок ---
# Движок знает, как подключаться к БД и как разговаривать с её драйвером.
# connect_args с check_same_thread нужен только для SQLite: uvicorn может
# обрабатывать запросы в разных потоках, а SQLite по умолчанию это запрещает.
_connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(
    settings.database_url,
    connect_args=_connect_args,
    echo=settings.debug,  # в dev-режиме логировать SQL в консоль
)


# --- Фабрика сессий ---
# Сессия — «рабочая область» для операций с БД: добавить, найти, обновить.
# Создаём фабрику, из которой будем получать новые сессии.
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,   # коммитить явно (db.commit())
    autoflush=False,    # не «сливать» изменения в БД автоматически
    expire_on_commit=False,  # после commit() объекты остаются доступными
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI-зависимость: выдаёт сессию БД на время запроса.

    Использование в ручке:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()