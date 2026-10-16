"""Ручки личной библиотеки пользователя: /library."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Game, LibraryEntry, LibraryStatus, User
from app.schemas import (
    LibraryEntryCreate,
    LibraryEntryPublic,
    LibraryEntryUpdate,
    LibraryList,
)

router = APIRouter(prefix="/library", tags=["library"])


def _get_own_entry(db: Session, entry_id: int, user_id: int) -> LibraryEntry:
    """Возвращает запись по id ТОЛЬКО если она принадлежит user_id.

    Если записи нет или она чужая — 404 (не раскрываем существование чужих).
    """
    stmt = (
        select(LibraryEntry)
        .options(joinedload(LibraryEntry.game))
        .where(LibraryEntry.id == entry_id, LibraryEntry.user_id == user_id)
    )
    entry = db.scalar(stmt)
    if entry is None:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.get("", response_model=LibraryList, summary="Мои записи в библиотеке")
def list_library(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: LibraryStatus | None = Query(None, alias="status"),
    sort: str = Query("-created_at"),
) -> LibraryList:
    base_stmt = select(LibraryEntry).where(LibraryEntry.user_id == current_user.id)

    if status_filter is not None:
        base_stmt = base_stmt.where(LibraryEntry.status == status_filter)

    total = db.scalar(select(func.count()).select_from(base_stmt.subquery())) or 0

    # Сортировка
    allowed_sorts = {
        "created_at": LibraryEntry.created_at.asc(),
        "-created_at": LibraryEntry.created_at.desc(),
        "rating": LibraryEntry.rating.asc(),
        "-rating": LibraryEntry.rating.desc(),
    }
    if sort not in allowed_sorts:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid sort value. Allowed: {list(allowed_sorts.keys())}",
        )

    items = db.scalars(
        base_stmt.options(joinedload(LibraryEntry.game))
        .order_by(allowed_sorts[sort])
        .offset(skip)
        .limit(limit)
    ).all()

    return LibraryList(total=total, items=list(items))


@router.post(
    "",
    response_model=LibraryEntryPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить игру в библиотеку",
)
def create_entry(
    payload: LibraryEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LibraryEntry:
    # Проверим, что игра существует
    game = db.get(Game, payload.game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    # Проверим, что у пользователя ещё нет записи по этой игре
    existing = db.scalar(
        select(LibraryEntry).where(
            LibraryEntry.user_id == current_user.id,
            LibraryEntry.game_id == payload.game_id,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Game already in library",
        )

    entry = LibraryEntry(
        user_id=current_user.id,
        **payload.model_dump(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    # Подтянем game для сериализации (Pydantic обратится к entry.game)
    _ = entry.game
    return entry


@router.get(
    "/{entry_id}",
    response_model=LibraryEntryPublic,
    summary="Одна запись из библиотеки",
)
def get_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LibraryEntry:
    return _get_own_entry(db, entry_id, current_user.id)


@router.patch(
    "/{entry_id}",
    response_model=LibraryEntryPublic,
    summary="Обновить запись в библиотеке",
)
def update_entry(
    entry_id: int,
    payload: LibraryEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LibraryEntry:
    entry = _get_own_entry(db, entry_id, current_user.id)

    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(
            status_code=422,
            detail="At least one field must be provided",
        )

    for field, value in data.items():
        setattr(entry, field, value)

    db.commit()
    db.refresh(entry)
    _ = entry.game
    return entry


@router.delete(
    "/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить запись из библиотеки",
)
def delete_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    entry = _get_own_entry(db, entry_id, current_user.id)
    db.delete(entry)
    db.commit()
