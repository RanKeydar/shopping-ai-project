from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import BadRequestError, NotFoundError
from app.models import Favorite, Item


def list_user_favorites(db: Session, user_id: int) -> list[Favorite]:
    stmt = (
        select(Favorite)
        .options(joinedload(Favorite.item))
        .where(Favorite.user_id == user_id)
        .order_by(Favorite.id.desc())
    )
    return list(db.execute(stmt).scalars().all())


def add_favorite(db: Session, user_id: int, item_id: int) -> Favorite:
    item = db.get(Item, item_id)
    if item is None:
        raise NotFoundError("Item not found")

    existing = db.execute(
        select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.item_id == item_id,
        )
    ).scalar_one_or_none()

    if existing is not None:
        raise BadRequestError("Item already in favorites")

    favorite = Favorite(user_id=user_id, item_id=item_id)
    db.add(favorite)
    db.commit()
    db.refresh(favorite)

    favorite = db.execute(
        select(Favorite)
        .options(joinedload(Favorite.item))
        .where(Favorite.id == favorite.id)
    ).scalar_one()

    return favorite


def remove_favorite(db: Session, user_id: int, item_id: int) -> None:
    favorite = db.execute(
        select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.item_id == item_id,
        )
    ).scalar_one_or_none()

    if favorite is None:
        raise NotFoundError("Favorite not found")

    db.delete(favorite)
    db.commit()