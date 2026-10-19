"""Тесты для ручек аутентификации и регистрации."""

import allure
import pytest

# ==========================================
# 1. РЕГИСТРАЦИЯ (POST /auth/register)
# ==========================================


@allure.feature("Аутентификация")
@allure.story("Регистрация")
@allure.title("Успешная регистрация нового пользователя")
@allure.severity(allure.severity_level.CRITICAL)
def test_register_success(api_client, unique_user_data):
    with allure.step("Отправка POST /auth/register"):
        response = api_client.post("/auth/register", json=unique_user_data)

    with allure.step("Проверка статуса 201 и данных пользователя"):
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == unique_user_data["username"]
        assert data["email"] == unique_user_data["email"]
        assert "id" in data
        # Убеждаемся, что пароль не утек в ответе
        assert "hashed_password" not in data
        assert "password" not in data


@allure.feature("Аутентификация")
@allure.story("Регистрация")
@allure.title("Ошибка при занятом username (409)")
def test_register_duplicate_username(api_client, registered_user, unique_user_data):
    with allure.step("Попытка регистрации с существующим username"):
        payload = unique_user_data.copy()
        payload["email"] = "another_email@example.com"
        response = api_client.post("/auth/register", json=payload)

    with allure.step("Проверка статуса 409"):
        assert response.status_code == 409
        assert response.json()["detail"] == "Username already registered"


@allure.feature("Аутентификация")
@allure.story("Регистрация")
@allure.title("Ошибка при занятом email (409)")
def test_register_duplicate_email(api_client, registered_user, unique_user_data):
    with allure.step("Попытка регистрации с существующим email"):
        payload = unique_user_data.copy()
        payload["username"] = "another_username"
        response = api_client.post("/auth/register", json=payload)

    with allure.step("Проверка статуса 409"):
        assert response.status_code == 409
        assert response.json()["detail"] == "Email already registered"


@allure.feature("Аутентификация")
@allure.story("Регистрация")
@allure.title("Ошибки валидации Pydantic (422)")
@pytest.mark.parametrize(
    "invalid_payload, expected_field",
    [
        ({"username": "ab", "email": "test@test.com", "password": "Password123!"}, "username"),
        ({"username": "validuser", "email": "not-an-email", "password": "Password123!"}, "email"),
        ({"username": "validuser", "email": "test@test.com", "password": "short"}, "password"),
    ],
)
def test_register_validation_errors(api_client, invalid_payload, expected_field):
    with allure.step("Отправка невалидных данных"):
        response = api_client.post("/auth/register", json=invalid_payload)

    with allure.step("Проверка статуса 422 и поля ошибки"):
        assert response.status_code == 422
        error_details = response.json()["detail"]
        assert any(expected_field in err["loc"] for err in error_details)


# ==========================================
# 2. ЛОГИН (POST /auth/login)
# ==========================================


@allure.feature("Аутентификация")
@allure.story("Логин")
@allure.title("Успешный логин возвращает JWT")
@allure.severity(allure.severity_level.CRITICAL)
def test_login_success(api_client, registered_user):
    with allure.step("Отправка POST /auth/login"):
        response = api_client.post(
            "/auth/login",
            json={"username": registered_user["username"], "password": registered_user["password"]},
        )

    with allure.step("Проверка статуса 200 и наличия токена"):
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 1800


@allure.feature("Аутентификация")
@allure.story("Логин")
@allure.title("Неверный пароль (401)")
def test_login_wrong_password(api_client, registered_user):
    with allure.step("Отправка POST /auth/login с неверным паролем"):
        response = api_client.post(
            "/auth/login",
            json={"username": registered_user["username"], "password": "WrongPassword!"},
        )

    with allure.step("Проверка статуса 401"):
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect username or password"


@allure.feature("Аутентификация")
@allure.story("Логин")
@allure.title("Несуществующий пользователь (401)")
def test_login_nonexistent_user(api_client):
    with allure.step("Отправка POST /auth/login для несуществующего юзера"):
        response = api_client.post(
            "/auth/login",
            json={"username": "definitely_not_exists_123", "password": "SomePassword123!"},
        )

    with allure.step("Проверка статуса 401 и одинакового сообщения"):
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect username or password"


# ==========================================
# 3. ТОКЕНЫ И ЗАЩИЩЕННЫЕ РУЧКИ (GET /auth/me)
# ==========================================


@allure.feature("Токены")
@allure.story("Валидация JWT")
@allure.title("Доступ с валидным токеном")
def test_get_me_success(auth_client):
    with allure.step("GET /auth/me с валидным токеном"):
        response = auth_client.get("/auth/me")

    with allure.step("Проверка статуса 200"):
        assert response.status_code == 200
        assert "username" in response.json()


@allure.feature("Токены")
@allure.story("Валидация JWT")
@allure.title("Доступ без токена (401)")
def test_get_me_no_token(api_client):
    with allure.step("GET /auth/me без заголовка Authorization"):
        response = api_client.get("/auth/me")

    with allure.step("Проверка статуса 401"):
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"


@allure.feature("Токены")
@allure.story("Валидация JWT")
@allure.title("Мусорный токен (401)")
def test_get_me_garbage_token(api_client, garbage_token):
    with allure.step("Установка мусорного токена в заголовок"):
        api_client.session.headers.update({"Authorization": f"Bearer {garbage_token}"})

    with allure.step("GET /auth/me"):
        response = api_client.get("/auth/me")

    with allure.step("Проверка статуса 401"):
        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate credentials"


@allure.feature("Токены")
@allure.story("Валидация JWT")
@allure.title("Токен с неверным SECRET_KEY (401)")
def test_get_me_wrong_secret(api_client, token_with_wrong_secret):
    with allure.step("Установка токена с неверной подписью"):
        api_client.session.headers.update({"Authorization": f"Bearer {token_with_wrong_secret}"})

    with allure.step("GET /auth/me"):
        response = api_client.get("/auth/me")

    with allure.step("Проверка статуса 401"):
        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate credentials"


@allure.feature("Токены")
@allure.story("Валидация JWT")
@allure.title("Просроченный токен (401)")
def test_get_me_expired_token(api_client, expired_token):
    with allure.step("Установка просроченного токена"):
        api_client.session.headers.update({"Authorization": f"Bearer {expired_token}"})

    with allure.step("GET /auth/me"):
        response = api_client.get("/auth/me")

    with allure.step("Проверка статуса 401 и сообщения Token expired"):
        assert response.status_code == 401
        assert response.json()["detail"] == "Token expired"
