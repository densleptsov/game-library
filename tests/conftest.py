"""Общие фикстуры pytest."""

import os
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from jose import jwt

from app.config import settings
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
    """Генерирует уникальные данные для нового пользователя."""
    uid = uuid.uuid4().hex[:8]
    return {
        "username": f"user_{uid}",
        "email": f"user_{uid}@example.com",
        "password": "SecretPass123!",
    }


@pytest.fixture
def registered_user(api_client: APIClient, unique_user_data: dict[str, str]) -> dict[str, str]:
    """Регистрирует пользователя через API и возвращает его данные."""
    response = api_client.post("/auth/register", json=unique_user_data)
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
    """Авторизованный HTTP-клиент."""
    client = APIClient(api_url)
    client.set_token(auth_token)
    return client


# ==========================================
# Фикстуры для невалидных токенов (этап 6.2)
# ==========================================


@pytest.fixture
def garbage_token() -> str:
    """Просто мусорная строка вместо токена."""
    return "garbage_token_123"


@pytest.fixture
def token_with_wrong_secret(registered_user: dict) -> str:
    """Валидный по структуре токен, но подписанный неверным SECRET_KEY."""
    payload = {
        "sub": "1",
        "exp": int((datetime.now(UTC) + timedelta(minutes=10)).timestamp()),
    }
    return jwt.encode(payload, "wrong-secret-key", algorithm="HS256")


@pytest.fixture
def expired_token(registered_user: dict) -> str:
    """Токен, у которого время жизни (exp) уже истекло."""
    payload = {
        "sub": "1",
        "exp": int((datetime.now(UTC) - timedelta(minutes=10)).timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


# ==========================================
# Фикстуры для Games и Library (этап 6.3)
# ==========================================


@pytest.fixture
def game_payload() -> dict:
    """Генерирует payload для создания игры.

    Используем uuid для title, чтобы избежать случайных коллизий.
    """
    uid = uuid.uuid4().hex[:6]
    return {
        "title": f"Test Game {uid}",
        "platform": "PC",
        "genre": "RPG",
        "release_year": 2023,
    }


@pytest.fixture
def created_game(auth_client, game_payload) -> dict:
    """Создает игру через API авторизованным клиентом."""
    response = auth_client.post("/games", json=game_payload)
    assert response.status_code == 201, f"Не удалось создать игру: {response.text}"
    return response.json()


@pytest.fixture
def library_entry(auth_client, created_game) -> dict:
    """Добавляет созданную игру в библиотеку текущего пользователя."""
    payload = {
        "game_id": created_game["id"],
        "status": "planned",
        "rating": None,
        "hours_played": 0,
        "notes": "Добавлено фикстурой",
    }
    response = auth_client.post("/library", json=payload)
    assert response.status_code == 201, f"Не удалось добавить в библиотеку: {response.text}"
    return response.json()
