from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Item, Order, OrderItem
from app.models.enums import OrderStatus


def get_temp_order_by_user(db: Session, user_id: int) -> Order | None:
    stmt = (
        select(Order)
        .where(
            Order.user_id == user_id,
            Order.status == OrderStatus.TEMP,
        )
        .options(joinedload(Order.items).joinedload(OrderItem.item))
    )
    return db.execute(stmt).unique().scalar_one_or_none()


def create_temp_order(db: Session, user_id: int) -> Order:
    order = Order(
        user_id=user_id,
        status=OrderStatus.TEMP,
        total_price=0,
    )
    db.add(order)
    db.flush()
    return order


def get_order_item(db: Session, order_id: int, item_id: int) -> OrderItem | None:
    stmt = select(OrderItem).where(
        OrderItem.order_id == order_id,
        OrderItem.item_id == item_id,
    )
    return db.execute(stmt).scalar_one_or_none()


def add_order_item(
    db: Session,
    order_id: int,
    item_id: int,
    quantity: int,
    unit_price: float,
) -> OrderItem:
    order_item = OrderItem(
        order_id=order_id,
        item_id=item_id,
        quantity=quantity,
        unit_price=unit_price,
    )
    db.add(order_item)
    db.flush()
    return order_item


def delete_order_item(db: Session, order_item: OrderItem) -> None:
    db.delete(order_item)


def get_item_by_id(db: Session, item_id: int) -> Item | None:
    stmt = select(Item).where(Item.id == item_id)
    return db.execute(stmt).scalar_one_or_none()


def list_orders_by_user(db: Session, user_id: int) -> list[Order]:
    stmt = (
        select(Order)
        .where(Order.user_id == user_id)
        .order_by(Order.created_at.desc(), Order.id.desc())
        .options(joinedload(Order.items).joinedload(OrderItem.item))
    )
    return list(db.execute(stmt).unique().scalars().all())