"""Обертка над requests для удобной работы с API в тестах."""

from typing import Any

import requests


class APIClient:
    """Клиент для общения с API.

    Инкапсулирует базовый URL, сессию и заголовки.
    """

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        # Session автоматически хранит cookies и переиспользует TCP-соединения
        self.session = requests.Session()

    def set_token(self, token: str) -> None:
        """Устанавливает JWT токен для всех последующих запросов."""
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        """Базовый метод для любого HTTP-запроса."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        # Дефолтный таймаут, чтобы тесты не висели, если сервер упал
        kwargs.setdefault("timeout", 10)
        return self.session.request(method, url, **kwargs)

    # Удобные методы-шорткаты
    def get(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("POST", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("DELETE", path, **kwargs)
