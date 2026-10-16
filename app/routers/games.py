"""Ручки каталога игр: /games."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Game, User
from app.schemas import GameCreate, GameList, GamePublic, GameUpdate

router = APIRouter(prefix="/games", tags=["games"])


@router.get("", response_model=GameList, summary="Список игр с фильтрами")
def list_games(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    platform: str | None = Query(None),
    genre: str | None = Query(None),
    search: str | None = Query(None, description="Подстрока в title"),
) -> GameList:
    stmt = select(Game)

    if platform is not None:
        stmt = stmt.where(Game.platform == platform)
    if genre is not None:
        stmt = stmt.where(Game.genre == genre)
    if search is not None:
        # ilike — регистронезависимый LIKE. В SQLite работает через LOWER.
        stmt = stmt.where(Game.title.ilike(f"%{search}%"))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(stmt.order_by(Game.id).offset(skip).limit(limit)).all()

    return GameList(total=total, items=list(items))


@router.post(
    "",
    response_model=GamePublic,
    status_code=status.HTTP_201_CREATED,
    summary="Создать игру (требуется авторизация)",
)
def create_game(
    payload: GameCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Game:
    game = Game(**payload.model_dump())
    db.add(game)
    db.commit()
    db.refresh(game)
    return game


@router.get("/{game_id}", response_model=GamePublic, summary="Одна игра")
def get_game(game_id: int, db: Session = Depends(get_db)) -> Game:
    game = db.get(Game, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@router.patch(
    "/{game_id}",
    response_model=GamePublic,
    summary="Обновить игру (требуется авторизация)",
)
def update_game(
    game_id: int,
    payload: GameUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Game:
    game = db.get(Game, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(
            status_code=422,
            detail="At least one field must be provided",
        )

    for field, value in data.items():
        setattr(game, field, value)

    db.commit()
    db.refresh(game)
    return game


@router.delete(
    "/{game_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить игру (требуется авторизация)",
)
def delete_game(
    game_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> None:
    game = db.get(Game, game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    db.delete(game)
    db.commit()
