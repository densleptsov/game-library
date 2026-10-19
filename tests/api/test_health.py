"""Smoke-тесты: проверка, что сервис жив и отвечает."""

import requests


def test_health_returns_ok(api_url: str) -> None:
    """GET /health должен вернуть 200 и {"status": "ok"}."""
    response = requests.get(f"{api_url}/health", timeout=5)

    assert response.status_code == 200, (
        f"Ожидали 200, получили {response.status_code}: {response.text}"
    )

    body = response.json()
    assert body == {"status": "ok"}, f"Неожиданный ответ: {body}"


def test_openapi_schema_available(api_url: str) -> None:
    """GET /openapi.json должен вернуть JSON-схему API."""
    response = requests.get(f"{api_url}/openapi.json", timeout=5)

    assert response.status_code == 200

    schema = response.json()
    assert "paths" in schema
    # Проверим, что ключевые ручки попали в схему
    assert "/health" in schema["paths"]
    assert "/auth/login" in schema["paths"]
    assert "/games" in schema["paths"]
    assert "/library" in schema["paths"]
