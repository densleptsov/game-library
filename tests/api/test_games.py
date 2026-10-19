"""Тесты для каталога игр (Games)."""


def test_get_games_public(api_client, created_game):
    """Список игр доступен без авторизации."""
    response = api_client.get("/games")

    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert data["total"] >= 1
    # Проверим, что наша игра есть в списке
    assert any(g["id"] == created_game["id"] for g in data["items"])


def test_create_game_unauthorized(api_client, game_payload):
    """Создание игры без токена возвращает 401."""
    response = api_client.post("/games", json=game_payload)

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_get_game_by_id(api_client, created_game):
    """Получение игры по ID."""
    response = api_client.get(f"/games/{created_game['id']}")

    assert response.status_code == 200
    assert response.json()["title"] == created_game["title"]


def test_get_game_not_found(api_client):
    """Несуществующая игра возвращает 404."""
    response = api_client.get("/games/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Game not found"


def test_update_game(auth_client, created_game):
    """PATCH обновляет поля игры."""
    update_data = {"genre": "Action RPG", "release_year": 2024}
    response = auth_client.patch(f"/games/{created_game['id']}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["genre"] == "Action RPG"
    assert data["release_year"] == 2024
    # Название не менялось
    assert data["title"] == created_game["title"]


def test_update_game_empty_payload(auth_client, created_game):
    """PATCH с пустым телом возвращает 422."""
    response = auth_client.patch(f"/games/{created_game['id']}", json={})

    assert response.status_code == 422
    assert "At least one field must be provided" in response.json()["detail"]


def test_delete_game(auth_client, created_game):
    """DELETE удаляет игру (204) и она больше не доступна (404)."""
    response = auth_client.delete(f"/games/{created_game['id']}")
    assert response.status_code == 204

    # Проверяем, что её нет
    check_response = auth_client.get(f"/games/{created_game['id']}")
    assert check_response.status_code == 404


def test_filter_games_by_platform(api_client, created_game):
    """Фильтрация по платформе."""
    response = api_client.get("/games", params={"platform": "PC"})

    assert response.status_code == 200
    items = response.json()["items"]
    assert all(g["platform"] == "PC" for g in items)


def test_search_games_by_title(api_client, created_game):
    """Поиск по подстроке в названии (регистронезависимый)."""
    # Ищем первые 5 символов названия в нижнем регистре
    search_query = created_game["title"][:5].lower()
    response = api_client.get("/games", params={"search": search_query})

    assert response.status_code == 200
    items = response.json()["items"]
    assert any(g["id"] == created_game["id"] for g in items)
