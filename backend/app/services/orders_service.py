from sqlalchemy.orm import Session

from app.core.exceptions import BadRequestError, InsufficientStockError, NotFoundError
from app.models.enums import OrderStatus
from app.repositories import orders_repository


def _get_or_create_temp_order(db: Session, user_id: int):
    order = orders_repository.get_temp_order_by_user(db, user_id)
    if order is not None:
        return order
    return orders_repository.create_temp_order(db, user_id)


def _reload_temp_order(db: Session, user_id: int):
    return orders_repository.get_temp_order_by_user(db, user_id)


def _recalculate_order_total(order) -> None:
    total = 0.0
    for row in order.items:
        total += float(row.unit_price) * int(row.quantity)
    order.total_price = round(total, 2)

def _delete_temp_order_if_empty(db: Session, user_id: int):
    order = _reload_temp_order(db, user_id)
    if order is None:
        return None

    if order.items:
        _recalculate_order_total(order)
        db.flush()
        return order

    db.delete(order)
    db.flush()
    return None

def add_item_to_cart(db: Session, user_id: int, item_id: int, quantity: int):
    if quantity <= 0:
        raise BadRequestError("Quantity must be greater than 0")

    item = orders_repository.get_item_by_id(db, item_id)
    if item is None:
        raise NotFoundError("Item not found")

    if item.stock_qty <= 0:
        raise InsufficientStockError("Item is out of stock")

    order = _get_or_create_temp_order(db, user_id)
    existing_row = orders_repository.get_order_item(db, order.id, item_id)

    if existing_row is None:
        new_quantity = quantity
    else:
        new_quantity = existing_row.quantity + quantity

    if new_quantity > item.stock_qty:
        raise InsufficientStockError("Requested quantity exceeds available stock")

    if existing_row is None:
        orders_repository.add_order_item(
            db=db,
            order_id=order.id,
            item_id=item.id,
            quantity=quantity,
            unit_price=float(item.price_usd),
        )
    else:
        existing_row.quantity = new_quantity

    db.flush()

    order = _reload_temp_order(db, user_id)
    _recalculate_order_total(order)

    db.commit()
    return _reload_temp_order(db, user_id)


def update_cart_item_quantity(db: Session, user_id: int, item_id: int, quantity: int):
    order = orders_repository.get_temp_order_by_user(db, user_id)
    if order is None:
        raise NotFoundError("Cart not found")

    row = orders_repository.get_order_item(db, order.id, item_id)
    if row is None:
        raise NotFoundError("Item not found in cart")

    if quantity < 0:
        raise BadRequestError("Quantity cannot be negative")

    if quantity == 0:
        orders_repository.delete_order_item(db, row)
        db.flush()

        order = _delete_temp_order_if_empty(db, user_id)

        db.commit()
        return order

    item = orders_repository.get_item_by_id(db, item_id)
    if item is None:
        raise NotFoundError("Item not found")

    if quantity > item.stock_qty:
        raise InsufficientStockError("Requested quantity exceeds available stock")

    row.quantity = quantity
    db.flush()

    order = _reload_temp_order(db, user_id)
    _recalculate_order_total(order)

    db.commit()
    return _reload_temp_order(db, user_id)

def remove_item_from_cart(db: Session, user_id: int, item_id: int):
    order = orders_repository.get_temp_order_by_user(db, user_id)
    if order is None:
        raise NotFoundError("Cart not found")

    row = orders_repository.get_order_item(db, order.id, item_id)
    if row is None:
        raise NotFoundError("Item not found in cart")

    orders_repository.delete_order_item(db, row)
    db.flush()

    order = _delete_temp_order_if_empty(db, user_id)

    db.commit()
    return order

def checkout_cart(db: Session, user_id: int, shipping_address: str):
    order = orders_repository.get_temp_order_by_user(db, user_id)
    if order is None:
        raise NotFoundError("Cart not found")

    if not order.items:
        raise BadRequestError("Cannot checkout an empty cart")

    if not shipping_address or not shipping_address.strip():
        raise BadRequestError("Shipping address is required")

    # validate stock again before closing the order
    for row in order.items:
        item = orders_repository.get_item_by_id(db, row.item_id)
        if item is None:
            raise NotFoundError(f"Item {row.item_id} not found")

        if row.quantity > item.stock_qty:
            raise InsufficientStockError(
                f"Not enough stock for item '{item.name}'"
            )

    # decrease stock
    for row in order.items:
        item = orders_repository.get_item_by_id(db, row.item_id)
        item.stock_qty -= row.quantity

    _recalculate_order_total(order)
    order.shipping_address = shipping_address.strip()
    order.status = OrderStatus.CLOSE

    db.commit()

    orders = orders_repository.list_orders_by_user(db, user_id)
    for existing_order in orders:
        if existing_order.status == OrderStatus.CLOSE and existing_order.id == order.id:
            return existing_order

    raise NotFoundError("Closed order not found after checkout")


def list_user_orders(db: Session, user_id: int):
    return orders_repository.list_orders_by_user(db, user_id)


def get_active_cart(db: Session, user_id: int):
    return orders_repository.get_temp_order_by_user(db, user_id)