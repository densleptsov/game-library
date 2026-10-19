"""Тесты для ручек аутентификации."""


def test_get_me_with_valid_token(auth_client):
    """GET /auth/me с валидным токеном возвращает данные текущего юзера."""
    response = auth_client.get("/auth/me")

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "username" in data
    assert "email" in data
    # Убеждаемся, что пароль не утек в ответе
    assert "password" not in data
    assert "hashed_password" not in data


def test_get_me_without_token(api_client):
    """GET /auth/me без токена возвращает 401."""
    response = api_client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
