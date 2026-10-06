# API Game Library

Версия API: `v1`
Base URL (local): `http://localhost:8000`
Интерактивная документация: `http://localhost:8000/docs` (Swagger UI)

## Общие правила

### Формат данных
- Только `application/json` для тел запросов и ответов.
- Кодировка — UTF-8.
- Даты — в формате ISO 8601 UTC: `2026-10-06T12:00:00Z`.

### Аутентификация
- Защищённые ручки требуют заголовок:
  ```
  Authorization: Bearer <access_token>
  ```
- Метка 🔒 в описании ручки означает обязательную аутентификацию.
- Токен получается через `POST /auth/login`.

### Пагинация
- Все списочные ручки поддерживают query-параметры `skip` (default 0) и `limit` (default 20, max 100).
- Ответ всегда имеет структуру:
  ```json
  {
    "total": <общее число записей>,
    "items": [ <массив объектов> ]
  }
  ```

### Формат ошибок
Все ошибки возвращают единый JSON:
```json
{
  "detail": "человекочитаемое описание"
}
```
Для ошибок валидации (422) FastAPI возвращает расширенный формат:
```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "String should have at least 8 characters",
      "type": "string_too_short"
    }
  ]
}
```

### Сводка кодов ответа
| Код | Когда |
|-----|-------|
| 200 | Успешный GET/PATCH |
| 201 | Успешный POST (создание) |
| 204 | Успешный DELETE (без тела) |
| 400 | Некорректный запрос (логическая ошибка) |
| 401 | Нет токена или токен просрочен/невалиден |
| 403 | Токен валиден, но нет прав на объект |
| 404 | Объект не найден |
| 409 | Конфликт (дубликат username/email, повторное добавление игры) |
| 422 | Ошибка валидации Pydantic (типы, диапазоны, обязательные поля) |
| 500 | Внутренняя ошибка сервера |

## Health и метаданные

### GET /health — проверка живости
Проверка, что сервер запущен и отвечает. Используется в CI для ожидания
старта приложения и в мониторинге.

**Request:** без параметров, без авторизации.

**Response 200:**
```json
{ "status": "ok" }
```

**Response 503:** если сервис не готов (например, БД недоступна):
```json
{ "status": "degraded", "reason": "database unavailable" }
```

## Аутентификация

### POST /auth/register — регистрация
Создаёт нового пользователя. Возвращает публичные данные (без пароля).

**Авторизация:** не требуется.

**Request body:**
```json
{
  "username": "ivan",
  "email": "ivan@example.com",
  "password": "S3cretPass!"
}
```

**Правила валидации:**
- `username`: 3–50 символов, regex `^[a-zA-Z0-9_-]+$`.
- `email`: валидный email (проверка Pydantic `EmailStr`).
- `password`: минимум 8 символов, содержит хотя бы одну букву и одну цифру.

**Response 201:**
```json
{
  "id": 1,
  "username": "ivan",
  "email": "ivan@example.com",
  "created_at": "2026-10-06T12:00:00Z"
}
```

**Ошибки:**
| Код | Сценарий | Пример `detail` |
|-----|----------|-----------------|
| 409 | username занят | `"Username already registered"` |
| 409 | email занят | `"Email already registered"` |
| 422 | невалидные данные | список ошибок Pydantic |

---

### POST /auth/login — вход
Проверяет учётные данные, выдаёт JWT access token.

**Авторизация:** не требуется.

**Request body:**
```json
{
  "username": "ivan",
  "password": "S3cretPass!"
}
```

**Response 200:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```
- `expires_in` — время жизни токена в секундах (30 минут = 1800).

**Ошибки:**
| Код | Сценарий | `detail` |
|-----|----------|----------|
| 401 | неверный username или пароль | `"Incorrect username or password"` |

**Важно:** одинаковое сообщение при неверном username И при неверном пароле.
Это защита от «user enumeration» — атакующий не может узнать, существует ли юзер.

---

### GET /auth/me — текущий пользователь 🔒
Возвращает данные авторизованного пользователя. Удобно для UI и для тестов
(проверить, что токен валиден и соответствует нужному юзеру).

**Response 200:**
```json
{
  "id": 1,
  "username": "ivan",
  "email": "ivan@example.com",
  "created_at": "2026-10-06T12:00:00Z"
}
```

**Ошибки:**
| Код | Сценарий | `detail` |
|-----|----------|----------|
| 401 | нет заголовка Authorization | `"Not authenticated"` |
| 401 | токен просрочен | `"Token expired"` |
| 401 | токен повреждён | `"Could not validate credentials"` |

## Каталог игр (Games)

Игра — общая сущность, доступная всем пользователям. Один раз добавили —
все могут ссылаться на неё через свою библиотеку.

### GET /games — список игр
**Авторизация:** не требуется (публичный каталог).

**Query-параметры:**
| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `skip` | int | 0 | Сколько пропустить |
| `limit` | int | 20 | Сколько вернуть (max 100) |
| `platform` | str | — | Фильтр по платформе (`PC`, `PS5`, ...) |
| `genre` | str | — | Фильтр по жанру (`RPG`, ...) |
| `search` | str | — | Поиск по `title` (регистронезависимый, подстрока) |

**Response 200:**
```json
{
  "total": 2,
  "items": [
    {
      "id": 1,
      "title": "The Witcher 3: Wild Hunt",
      "platform": "PC",
      "genre": "RPG",
      "release_year": 2015,
      "cover_url": null,
      "created_at": "2026-10-06T12:00:00Z"
    },
    {
      "id": 2,
      "title": "Cyberpunk 2077",
      "platform": "PC",
      "genre": "RPG",
      "release_year": 2020,
      "cover_url": null,
      "created_at": "2026-10-06T12:00:00Z"
    }
  ]
}
```

**Ошибки:**
| Код | Сценарий |
|-----|----------|
| 422 | `limit` > 100 или `skip` < 0 |

---

### POST /games — создать игру 🔒
**Авторизация:** требуется.

**Request body:**
```json
{
  "title": "Hades",
  "platform": "PC",
  "genre": "Roguelike",
  "release_year": 2020,
  "cover_url": null
}
```

**Правила валидации:**
- `title`: 1–255 символов, обязателен.
- `platform`: одно из `PC`, `PS5`, `Xbox`, `Switch`, `Mobile`, `Other`.
- `genre`: 0–50 символов, опционально.
- `release_year`: 1950–2100, опционально.
- `cover_url`: валидный URL, опционально.

**Response 201:**
```json
{
  "id": 3,
  "title": "Hades",
  "platform": "PC",
  "genre": "Roguelike",
  "release_year": 2020,
  "cover_url": null,
  "created_at": "2026-10-06T12:05:00Z"
}
```

**Ошибки:**
| Код | Сценарий | `detail` |
|-----|----------|----------|
| 401 | нет токена | `"Not authenticated"` |
| 422 | невалидные поля | список ошибок |

---

### GET /games/{game_id} — одна игра
**Авторизация:** не требуется.

**Response 200:** объект игры (как в списке).

**Ошибки:**
| Код | Сценарий | `detail` |
|-----|----------|----------|
| 404 | игра не найдена | `"Game not found"` |
| 422 | `game_id` не int | список ошибок |

---

### PATCH /games/{game_id} — обновить игру 🔒
**Авторизация:** требуется. Пока любой авторизованный пользователь может
обновить игру. Если позже появится роль admin — ограничим.

**Request body** (все поля опциональны, но хотя бы одно должно быть):
```json
{
  "genre": "Action Roguelike",
  "cover_url": "https://example.com/hades.jpg"
}
```

**Response 200:** обновлённый объект игры.

**Ошибки:**
| Код | Сценарий | `detail` |
|-----|----------|----------|
| 401 | нет токена | `"Not authenticated"` |
| 404 | игра не найдена | `"Game not found"` |
| 422 | пустое тело (все поля null) или невалидные значения | список ошибок |

---

### DELETE /games/{game_id} — удалить игру 🔒
Удаляет игру из каталога. Все связанные `LibraryEntry` удаляются CASCADE.

**Авторизация:** требуется.

**Response 204:** без тела.

**Ошибки:**
| Код | Сценарий | `detail` |
|-----|----------|----------|
| 401 | нет токена | `"Not authenticated"` |
| 404 | игра не найдена | `"Game not found"` |

## Библиотека пользователя (Library) 🔒

Все ручки требуют авторизации. Пользователь видит **только свои** записи.

### GET /library — мои записи
**Query-параметры:**
| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `skip` | int | 0 | Пагинация |
| `limit` | int | 20 | Пагинация (max 100) |
| `status` | str | — | Фильтр: `planned` / `playing` / `completed` / `dropped` |
| `sort` | str | `-created_at` | Сортировка: `created_at`, `-created_at`, `rating`, `-rating` |

**Response 200:**
```json
{
  "total": 1,
  "items": [
    {
      "id": 10,
      "game": {
        "id": 1,
        "title": "The Witcher 3: Wild Hunt",
        "platform": "PC",
        "genre": "RPG",
        "release_year": 2015,
        "cover_url": null
      },
      "status": "playing",
      "rating": 9,
      "hours_played": 42,
      "notes": "Прохожу второй раз",
      "created_at": "2026-10-06T12:00:00Z",
      "updated_at": "2026-10-06T14:30:00Z"
    }
  ]
}
```

**Важно:** в ответ вложен полный объект `game`, а не только `game_id`.
Это удобно для UI (не надо делать второй запрос).

---

### POST /library — добавить игру себе 🔒
**Request body:**
```json
{
  "game_id": 1,
  "status": "planned",
  "rating": null,
  "hours_played": 0,
  "notes": null
}
```

**Правила валидации:**
- `game_id`: int, обязателен.
- `status`: одно из `planned` / `playing` / `completed` / `dropped`, default `planned`.
- `rating`: 1–10 или null.
- `hours_played`: >= 0 или null.
- `notes`: до 1000 символов или null.

**Response 201:**
```json
{
  "id": 10,
  "game": { "id": 1, "title": "The Witcher 3: Wild Hunt", "platform": "PC" },
  "status": "planned",
  "rating": null,
  "hours_played": 0,
  "notes": null,
  "created_at": "2026-10-06T12:00:00Z",
  "updated_at": "2026-10-06T12:00:00Z"
}
```

**Ошибки:**
| Код | Сценарий | `detail` |
|-----|----------|----------|
| 401 | нет токена | `"Not authenticated"` |
| 404 | игры с таким id нет | `"Game not found"` |
| 409 | эта игра уже в библиотеке | `"Game already in library"` |
| 422 | невалидные поля | список ошибок |

---

### GET /library/{entry_id} — одна запись 🔒
**Response 200:** объект записи.

**Ошибки:**
| Код | Сценарий | `detail` |
|-----|----------|----------|
| 401 | нет токена | `"Not authenticated"` |
| 404 | записи нет ИЛИ запись принадлежит другому юзеру | `"Entry not found"` |

**Почему 404, а не 403 для чужой записи:** не раскрываем существование
чужих ресурсов. Так делают GitHub, Stripe.

---

### PATCH /library/{entry_id} — обновить запись 🔒
Позволяет частично обновить запись: поменять статус, поставить оценку,
отметить часы, обновить заметки.

**Request body** (все поля опциональны):
```json
{
  "status": "completed",
  "rating": 10,
  "hours_played": 120,
  "notes": "Прошёл на платину"
}
```

**Response 200:** обновлённый объект.

**Ошибки:**
| Код | Сценарий | `detail` |
|-----|----------|----------|
| 401 | нет токена | `"Not authenticated"` |
| 404 | записи нет или она не твоя | `"Entry not found"` |
| 422 | пустое тело или невалидные значения | список ошибок |

---

### DELETE /library/{entry_id} — удалить из библиотеки 🔒
**Response 204:** без тела.

**Ошибки:**
| Код | Сценарий | `detail` |
|-----|----------|----------|
| 401 | нет токена | `"Not authenticated"` |
| 404 | записи нет или она не твоя | `"Entry not found"` |

## Полные примеры

### Сценарий 1: регистрация → логин → добавить игру → добавить себе

**1. Регистрация:**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"ivan","email":"ivan@example.com","password":"S3cretPass1"}'
```

**2. Логин:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"ivan","password":"S3cretPass1"}'
```
Ответ: `{"access_token":"eyJ...","token_type":"bearer","expires_in":1800}`

**3. Создать игру (с токеном):**
```bash
curl -X POST http://localhost:8000/games \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"title":"Hades","platform":"PC","genre":"Roguelike","release_year":2020}'
```
Ответ: `{"id":1, "title":"Hades", ...}`

**4. Добавить себе:**
```bash
curl -X POST http://localhost:8000/library \
  -H "Authorization: Bearer eyJ..." \
  -H "Content-Type: application/json" \
  -d '{"game_id":1,"status":"planned"}'
```

**5. Посмотреть библиотеку:**
```bash
curl http://localhost:8000/library \
  -H "Authorization: Bearer eyJ..."
```

### Сценарий 2: чужой доступ
Пользователь A логинится, получает токен A. Пользователь B логинится,
получает токен B. B добавляет игру себе — `entry_id = 5`.
A пытается получить `/library/5` со своим токеном → **404**.

Это один из ключевых негативных тестов.