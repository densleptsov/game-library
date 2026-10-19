"""Общие фикстуры pytest.

Pytest автоматически загружает этот файл. Все фикстуры отсюда
доступны в тестах без импортов — pytest сам «впрыснет» их по имени.
"""

import os

import pytest

# URL API. По умолчанию — локальный сервер.
# В CI или другом окружении можно переопределить переменной API_URL.
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")


@pytest.fixture(scope="session")
def api_url() -> str:
    """Базовый URL API.

    scope="session" — фикстура создаётся один раз на весь прогон,
    а не на каждый тест. Удобно для констант.
    """
    return API_URL
