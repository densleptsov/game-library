"""Ручки аутентификации: регистрация, логин, текущий пользователь."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import LoginRequest, TokenResponse, UserCreate, UserPublic
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя",
)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    # Проверка уникальности username
    if db.scalar(select(User).where(User.username == payload.username)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered",
        )
    # Проверка уникальности email
    if db.scalar(select(User).where(User.email == payload.email)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Вход, получение JWT",
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.username == payload.username))

    # Одинаковый ответ при неверном username и пароле (защита от enumeration)
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user.id)
    return TokenResponse(
        access_token=token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Текущий пользователь",
)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user