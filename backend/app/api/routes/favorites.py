from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, NotFoundError
from app.db import get_db
from app.services.favorites_service import (
    list_user_favorites,
    add_favorite,
    remove_favorite,
)
from app.api.deps.current_user import get_current_user

router = APIRouter(prefix="/favorites", tags=["favorites"])


def _serialize_favorite(favorite):
    if favorite is None:
        return None

    item = favorite.item

    return {
        "id": item.id if item else None,
        "name": item.name if item else "",
        "price_usd": float(item.price_usd) if item and item.price_usd is not None else 0.0,
        "stock_qty": int(item.stock_qty) if item and item.stock_qty is not None else 0,
    }


def _handle_service_error(exc: Exception):
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, BadRequestError):
        raise HTTPException(status_code=400, detail=str(exc))
    raise HTTPException(status_code=500, detail="Internal server error")


@router.get("")
def get_favorites(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    favorites = list_user_favorites(db=db, user_id=current_user.id)
    return [_serialize_favorite(favorite) for favorite in favorites]


@router.post("/{item_id}")
def add_item_to_favorites(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        favorite = add_favorite(
            db=db,
            user_id=current_user.id,
            item_id=item_id,
        )
        return _serialize_favorite(favorite)
    except Exception as exc:
        _handle_service_error(exc)


@router.delete("/{item_id}")
def remove_item_from_favorites(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        remove_favorite(
            db=db,
            user_id=current_user.id,
            item_id=item_id,
        )
        return {"message": "Item removed from favorites"}
    except Exception as exc:
        _handle_service_error(exc)