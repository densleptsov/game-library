"""HTTP-клиент для общения UI с FastAPI.

Единая точка для base_url, заголовков, обработки ошибок.
"""

import os

import requests

# Базовый URL API. Можно переопределить переменной окружения API_URL.
# По умолчанию — локальный FastAPI на 8000.
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# Таймаут на запрос (сек). Чтобы UI не подвис, если API лежит.
TIMEOUT = 10


class ApiError(Exception):
    """Ошибка от API: содержит код и сообщение."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"[{status_code}] {detail}")


def _headers(token: str | None = None) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _handle(response: requests.Response) -> dict | None:
    """Единая обработка ответа: успех → json, ошибка → ApiError."""
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        # detail может быть списком (ошибки Pydantic) — приведём к строке
        if isinstance(detail, list):
            detail = "; ".join(
                f"{'.'.join(str(x) for x in e.get('loc', []))}: {e.get('msg', '')}" for e in detail
            )
        raise ApiError(response.status_code, str(detail))
    if response.status_code == 204:
        return None
    return response.json()


# --- Auth ---


def register(username: str, email: str, password: str) -> dict:
    r = requests.post(
        f"{API_URL}/auth/register",
        json={"username": username, "email": email, "password": password},
        timeout=TIMEOUT,
    )
    return _handle(r)


def login(username: str, password: str) -> dict:
    r = requests.post(
        f"{API_URL}/auth/login",
        json={"username": username, "password": password},
        timeout=TIMEOUT,
    )
    return _handle(r)


def me(token: str) -> dict:
    r = requests.get(f"{API_URL}/auth/me", headers=_headers(token), timeout=TIMEOUT)
    return _handle(r)


# --- Games ---


def list_games(
    token: str | None = None,
    search: str | None = None,
    platform: str | None = None,
) -> dict:
    params: dict[str, str] = {}
    if search:
        params["search"] = search
    if platform:
        params["platform"] = platform
    r = requests.get(
        f"{API_URL}/games",
        params=params,
        headers=_headers(token),
        timeout=TIMEOUT,
    )
    return _handle(r)


def create_game(token: str, payload: dict) -> dict:
    r = requests.post(
        f"{API_URL}/games",
        json=payload,
        headers=_headers(token),
        timeout=TIMEOUT,
    )
    return _handle(r)


# --- Library ---


def list_library(token: str, status_filter: str | None = None) -> dict:
    params = {}
    if status_filter:
        params["status"] = status_filter
    r = requests.get(
        f"{API_URL}/library",
        params=params,
        headers=_headers(token),
        timeout=TIMEOUT,
    )
    return _handle(r)


def create_entry(token: str, payload: dict) -> dict:
    r = requests.post(
        f"{API_URL}/library",
        json=payload,
        headers=_headers(token),
        timeout=TIMEOUT,
    )
    return _handle(r)


def update_entry(token: str, entry_id: int, payload: dict) -> dict:
    r = requests.patch(
        f"{API_URL}/library/{entry_id}",
        json=payload,
        headers=_headers(token),
        timeout=TIMEOUT,
    )
    return _handle(r)


def delete_entry(token: str, entry_id: int) -> None:
    r = requests.delete(
        f"{API_URL}/library/{entry_id}",
        headers=_headers(token),
        timeout=TIMEOUT,
    )
    _handle(r)
