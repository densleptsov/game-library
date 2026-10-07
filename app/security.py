"""Безопасность: хеширование паролей и работа с JWT."""
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import jwt

from app.config import settings


# --- Пароли ---

# bcrypt учитывает только первые 72 байта пароля. Более длинные пароли
# молча обрезались в старых версиях; в новых — ValueError. Мы явно
# ограничим длину пароля на уровне схемы (см. schemas.py).
_BCRYPT_MAX_BYTES = 72


def hash_password(plain: str) -> str:
    """Возвращает bcrypt-хеш пароля (как строку)."""
    # Кодируем в байты (UTF-8), потом хешируем
    pwd_bytes = plain.encode("utf-8")
    if len(pwd_bytes) > _BCRYPT_MAX_BYTES:
        raise ValueError(
            f"Password is too long: {len(pwd_bytes)} bytes, "
            f"max {_BCRYPT_MAX_BYTES} bytes"
        )
    salt = bcrypt.gensalt(rounds=12)
    hashed: bytes = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Проверяет, соответствует ли пароль хешу."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        # Например, если hashed — не bcrypt-строка (повреждён или старый формат)
        return False


# --- JWT ---

ALGORITHM = "HS256"


def create_access_token(user_id: int) -> str:
    """Создаёт подписанный JWT для пользователя."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Декодирует и проверяет JWT.

    Бросает jose.JWTError (или его подкласс ExpiredSignatureError),
    если токен невалиден или просрочен.
    """
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])