# Стек технологий

## Язык и окружение
- **Python 3.11+** — основной язык.
- **venv** — изолированное окружение для зависимостей.
- **pip + requirements.txt** — управление пакетами (проще, чем poetry, для старта).

## Backend
- **FastAPI** — веб-фреймворк для REST API.
- **Uvicorn** — ASGI-сервер, на котором запускается FastAPI.
- **Pydantic v2** — валидация данных и сериализация.
- **python-jose[cryptography]** — работа с JWT.
- **passlib[bcrypt]** — хеширование паролей.
- **SQLAlchemy 2.0** — ORM для работы с БД.
- **Alembic** — миграции схемы БД.
- **SQLite** (dev) → **PostgreSQL** (prod, позже).

## UI
- **Streamlit** — быстрый UI на Python без HTML/JS.

## Тесты
- **pytest** — фреймворк тестов.
- **requests** / **httpx** — API-тесты.
- **Playwright** — UI-тесты.
- **allure-pytest** — отчёты.

## Инструменты
- **ruff** — линтер + форматтер.
- **GitHub Actions** — CI.