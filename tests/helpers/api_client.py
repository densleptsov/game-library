"""Обертка над requests для удобной работы с API в тестах."""

from typing import Any

import allure
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
        """Базовый метод для любого HTTP-запроса с логированием в Allure."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        # Дефолтный таймаут, чтобы тесты не висели, если сервер упал
        kwargs.setdefault("timeout", 10)

        # Оборачиваем запрос в шаг Allure
        with allure.step(f"{method} {path}"):
            response = self.session.request(method, url, **kwargs)

            # Прикрепляем тело запроса и ответа к отчету (если они есть)
            req_body = kwargs.get("json")
            if req_body:
                allure.attach(
                    str(req_body), name="Request JSON", attachment_type=allure.attachment_type.TEXT
                )

            allure.attach(
                response.text,
                name=f"Response {response.status_code}",
                attachment_type=allure.attachment_type.JSON,
            )

            return response

    # Удобные методы-шорткаты
    def get(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("POST", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("DELETE", path, **kwargs)
