"""Тесты для библиотеки пользователя (Library)."""

from tests.helpers.api_client import APIClient


def test_add_to_library(auth_client, created_game):
    """Добавление игры в библиотеку."""
    payload = {"game_id": created_game["id"], "status": "playing", "rating": 9}
    response = auth_client.post("/library", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "playing"
    assert data["rating"] == 9
    assert data["game"]["id"] == created_game["id"]


def test_add_non_existent_game(auth_client):
    """Нельзя добавить игру, которой нет в каталоге (404)."""
    response = auth_client.post("/library", json={"game_id": 999999})

    assert response.status_code == 404
    assert response.json()["detail"] == "Game not found"


def test_add_duplicate_to_library(auth_client, library_entry):
    """Нельзя добавить одну игру дважды (409)."""
    payload = {"game_id": library_entry["game"]["id"]}
    response = auth_client.post("/library", json=payload)

    assert response.status_code == 409
    assert response.json()["detail"] == "Game already in library"


def test_update_library_entry(auth_client, library_entry):
    """Обновление статуса и заметок в записи."""
    update_data = {"status": "completed", "rating": 10, "notes": "Прошёл!"}
    response = auth_client.patch(f"/library/{library_entry['id']}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["rating"] == 10


def test_delete_library_entry(auth_client, library_entry):
    """Удаление записи из библиотеки."""
    response = auth_client.delete(f"/library/{library_entry['id']}")
    assert response.status_code == 204

    check_response = auth_client.get(f"/library/{library_entry['id']}")
    assert check_response.status_code == 404


# ==========================================
# ROW-LEVEL SECURITY (Самое важное!)
# ==========================================


def test_user_cannot_see_other_user_library_entry(api_url, auth_client, library_entry):
    """Юзер Б не может получить запись Юзера А."""
    # library_entry принадлежит текущему auth_client (Юзер А)

    # Создаем второго пользователя (Юзер Б)
    # Но лучше создать клиента вручную
    import uuid

    uid = uuid.uuid4().hex[:8]
    user_b_data = {
        "username": f"user_b_{uid}",
        "email": f"user_b_{uid}@example.com",
        "password": "SecretPass123!",
    }

    client = APIClient(api_url)
    client.post("/auth/register", json=user_b_data)
    login_resp = client.post(
        "/auth/login",
        json={"username": user_b_data["username"], "password": user_b_data["password"]},
    )
    client.set_token(login_resp.json()["access_token"])

    # Юзер Б пытается получить запись Юзера А
    response = client.get(f"/library/{library_entry['id']}")

    # Должен быть 404 (мы договорились не палить существование чужих ресурсов)
    assert response.status_code == 404
    assert response.json()["detail"] == "Entry not found"


def test_user_cannot_delete_other_user_library_entry(api_url, auth_client, library_entry):
    """Юзер Б не может удалить запись Юзера А."""
    # (Тот же паттерн создания Юзера Б)
    import uuid

    uid = uuid.uuid4().hex[:8]
    client = APIClient(api_url)
    client.post(
        "/auth/register",
        json={"username": f"b_{uid}", "email": f"b_{uid}@mail.com", "password": "SecretPass123!"},
    )
    resp = client.post("/auth/login", json={"username": f"b_{uid}", "password": "SecretPass123!"})
    client.set_token(resp.json()["access_token"])

    # Юзер Б пытается удалить запись Юзера А
    response = client.delete(f"/library/{library_entry['id']}")

    assert response.status_code == 404
