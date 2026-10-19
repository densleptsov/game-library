"""Тесты для ручек аутентификации и регистрации."""

import pytest

# ==========================================
# 1. РЕГИСТРАЦИЯ (POST /auth/register)
# ==========================================


def test_register_success(api_client, unique_user_data):
    """Успешная регистрация нового пользователя."""
    response = api_client.post("/auth/register", json=unique_user_data)

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == unique_user_data["username"]
    assert data["email"] == unique_user_data["email"]
    assert "id" in data
    assert "hashed_password" not in data
    assert "password" not in data


def test_register_duplicate_username(api_client, registered_user, unique_user_data):
    """Регистрация с занятым username возвращает 409."""
    # registered_user уже зарегистрировал unique_user_data
    # Пытаемся зарегистрировать еще раз с тем же username, но другим email
    payload = unique_user_data.copy()
    payload["email"] = "another_email@example.com"

    response = api_client.post("/auth/register", json=payload)

    assert response.status_code == 409
    assert response.json()["detail"] == "Username already registered"


def test_register_duplicate_email(api_client, registered_user, unique_user_data):
    """Регистрация с занятым email возвращает 409."""
    payload = unique_user_data.copy()
    payload["username"] = "another_username"

    response = api_client.post("/auth/register", json=payload)

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"


@pytest.mark.parametrize(
    "invalid_payload, expected_field",
    [
        # Слишком короткий username
        ({"username": "ab", "email": "test@test.com", "password": "Password123!"}, "username"),
        # Невалидный email
        ({"username": "validuser", "email": "not-an-email", "password": "Password123!"}, "email"),
        # Слишком короткий пароль (меньше 8)
        ({"username": "validuser", "email": "test@test.com", "password": "short"}, "password"),
    ],
)
def test_register_validation_errors(api_client, invalid_payload, expected_field):
    """Pydantic должен отлавливать невалидные данные и возвращать 422."""
    response = api_client.post("/auth/register", json=invalid_payload)

    assert response.status_code == 422
    error_details = response.json()["detail"]

    # FastAPI возвращает список ошибок. Ищем наше поле.
    assert any(expected_field in err["loc"] for err in error_details)


# ==========================================
# 2. ЛОГИН (POST /auth/login)
# ==========================================


def test_login_success(api_client, registered_user):
    """Успешный логин возвращает access_token."""
    response = api_client.post(
        "/auth/login",
        json={"username": registered_user["username"], "password": registered_user["password"]},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 1800  # 30 минут * 60 секунд


def test_login_wrong_password(api_client, registered_user):
    """Неверный пароль возвращает 401."""
    response = api_client.post(
        "/auth/login", json={"username": registered_user["username"], "password": "WrongPassword!"}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


def test_login_nonexistent_user(api_client):
    """Несуществующий пользователь возвращает 401 (и то же сообщение)."""
    response = api_client.post(
        "/auth/login",
        json={"username": "definitely_not_exists_123", "password": "SomePassword123!"},
    )

    assert response.status_code == 401
    # Важно: сообщение должно быть ТАКИМ ЖЕ, как при неверном пароле
    # (защита от user enumeration)
    assert response.json()["detail"] == "Incorrect username or password"


# ==========================================
# 3. ТОКЕНЫ И ЗАЩИЩЕННЫЕ РУЧКИ (GET /auth/me)
# ==========================================


def test_get_me_success(auth_client):
    """Доступ к защищенной ручке с валидным токеном."""
    response = auth_client.get("/auth/me")

    assert response.status_code == 200
    assert "username" in response.json()


def test_get_me_no_token(api_client):
    """Без токена возвращает 401."""
    response = api_client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_get_me_garbage_token(api_client, garbage_token):
    """Мусорный токен возвращает 401."""
    # Вручную ставим плохой заголовок
    api_client.session.headers.update({"Authorization": f"Bearer {garbage_token}"})

    response = api_client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_get_me_wrong_secret(api_client, token_with_wrong_secret):
    """Токен, подписанный неверным ключом, возвращает 401."""
    api_client.session.headers.update({"Authorization": f"Bearer {token_with_wrong_secret}"})

    response = api_client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_get_me_expired_token(api_client, expired_token):
    """Просроченный токен возвращает 401 с сообщением Token expired."""
    api_client.session.headers.update({"Authorization": f"Bearer {expired_token}"})

    response = api_client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Token expired"
