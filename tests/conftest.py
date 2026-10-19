"""Общие фикстуры pytest."""

import os
import uuid

import pytest

from tests.helpers.api_client import APIClient

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")


@pytest.fixture(scope="session")
def api_url() -> str:
    """Базовый URL API."""
    return API_URL


@pytest.fixture
def api_client(api_url: str) -> APIClient:
    """Неавторизованный HTTP-клиент."""
    return APIClient(api_url)


@pytest.fixture
def unique_user_data() -> dict[str, str]:
    """Генерирует уникальные данные для нового пользователя.

    Используем uuid4, чтобы каждый тест работал со своим пользователем.
    Это гарантирует изоляцию тестов (нет конфликтов по 409 Conflict).
    """
    uid = uuid.uuid4().hex[:8]  # 8 случайных символов
    return {
        "username": f"user_{uid}",
        "email": f"user_{uid}@example.com",
        "password": "SecretPass123!",
    }


@pytest.fixture
def registered_user(api_client: APIClient, unique_user_data: dict[str, str]) -> dict[str, str]:
    """Регистрирует пользователя через API и возвращает его данные.

    Зависит от api_client и unique_user_data.
    Pytest сам вызовет их по цепочке.
    """
    response = api_client.post("/auth/register", json=unique_user_data)

    # Если регистрация упала, тест нет смысла продолжать — падаем сразу
    assert response.status_code == 201, f"Не удалось создать юзера: {response.text}"

    return unique_user_data


@pytest.fixture
def auth_token(api_client: APIClient, registered_user: dict[str, str]) -> str:
    """Логинится зарегистрированным пользователем и возвращает JWT."""
    login_data = {
        "username": registered_user["username"],
        "password": registered_user["password"],
    }
    response = api_client.post("/auth/login", json=login_data)
    assert response.status_code == 200, f"Не удалось залогиниться: {response.text}"

    return response.json()["access_token"]


@pytest.fixture
def auth_client(api_url: str, auth_token: str) -> APIClient:
    """Авторизованный HTTP-клиент.

    Возвращает новый APIClient, у которого в заголовках уже есть токен.
    """
    client = APIClient(api_url)
    client.set_token(auth_token)
    return client
