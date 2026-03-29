from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, InsufficientStockError, NotFoundError
from app.db import get_db
from app.schemas.orders import AddItemRequest, CheckoutRequest, UpdateQuantityRequest
from app.services import orders_service
from app.api.deps.current_user import get_current_user

from redis.asyncio import Redis
from app.cache.redis_client import get_redis
from app.cache.invalidate import invalidate_items_list_cache

router = APIRouter(prefix="/orders", tags=["orders"])

def _serialize_order(order):
    if order is None:
        return None

    return {
        "id": order.id,
        "user_id": order.user_id,
        "created_at": order.created_at,
        "shipping_address": order.shipping_address,
        "status": order.status.value if hasattr(order.status, "value") else str(order.status),
        "total_price": float(order.total_price),
        "items": [
            {
                "item_id": row.item_id,
                "name": row.item.name if row.item else "",
                "quantity": row.quantity,
                "unit_price": float(row.unit_price),
                "line_total": float(row.unit_price) * row.quantity,
            }
            for row in order.items
        ],
    }

def _handle_service_error(exc: Exception):
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, BadRequestError):
        raise HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, InsufficientStockError):
        raise HTTPException(status_code=400, detail=str(exc))
    raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/cart/add-item")
def add_item_to_cart(
    payload: AddItemRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        order = orders_service.add_item_to_cart(
            db=db,
            user_id=current_user.id,
            item_id=payload.item_id,
            quantity=payload.quantity,
        )
        return _serialize_order(order)
    except Exception as exc:
        _handle_service_error(exc)

@router.post("/cart/update-quantity")
def update_cart_quantity(
    payload: UpdateQuantityRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        order = orders_service.update_cart_item_quantity(
            db=db,
            user_id=current_user.id,
            item_id=payload.item_id,
            quantity=payload.quantity,
        )
        return _serialize_order(order)
    except Exception as exc:
        _handle_service_error(exc)

@router.delete("/cart/remove-item/{item_id}")
def remove_item_from_cart(
    item_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        order = orders_service.remove_item_from_cart(
            db=db,
            user_id=current_user.id,
            item_id=item_id,
        )
        return {"cart": _serialize_order(order)}
    except Exception as exc:
        _handle_service_error(exc)

@router.post("/cart/checkout")
async def checkout_cart(          # ← async במקום def
    payload: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    redis: Redis = Depends(get_redis),   # ← הוסף
):
    try:
        order = orders_service.checkout_cart(
            db=db,
            user_id=current_user.id,
            shipping_address=payload.shipping_address,
        )
        await invalidate_items_list_cache(redis)   # ← הוסף
        return _serialize_order(order)
    except Exception as exc:
        _handle_service_error(exc)

@router.get("/cart")
def get_active_cart(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    cart = orders_service.get_active_cart(db=db, user_id=current_user.id)
    return _serialize_order(cart)

@router.get("")
def get_orders(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    orders = orders_service.list_user_orders(db=db, user_id=current_user.id)
    return [_serialize_order(order) for order in orders]