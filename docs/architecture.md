# Архитектура Game Library

## Сущности
- **User** — владелец библиотеки
- **Game** — игра (название, платформа, жанр, год)
- **LibraryEntry** — связь user ↔ game со статусом (playing/completed/dropped) и оценкой

## API (черновик)
| Метод | URL | Описание |
|-------|-----|----------|
| POST | /auth/register | регистрация |
| POST | /auth/login | логин, получить токен |
| GET | /games | список игр |
| POST | /games | добавить игру |
| GET | /games/{id} | одна игра |
| PATCH | /games/{id} | обновить |
| DELETE | /games/{id} | удалить |