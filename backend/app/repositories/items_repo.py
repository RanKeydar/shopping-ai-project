from __future__ import annotations

from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session

from app.models import Item


_ALLOWED_OPS = {"<", "<=", "=", ">=", ">"}


def _apply_op(column, op: str, value):
    if op == "<":
        return column < value
    if op == "<=":
        return column <= value
    if op == "=":
        return column == value
    if op == ">=":
        return column >= value
    if op == ">":
        return column > value
    raise ValueError("Unsupported operator")


def list_items(
    db: Session,
    q: str | None = None,
    price_op: str | None = None,
    price: float | None = None,
    stock_op: str | None = None,
    stock: int | None = None,
) -> list[Item]:

    stmt = select(Item)
    conditions = []

    # Search (OR between keywords)
    if q:
        keywords = [w.strip() for w in q.split() if w.strip()]
        if keywords:
            search_conditions = [Item.name.ilike(f"%{kw}%") for kw in keywords]
            conditions.append(or_(*search_conditions))

    # Price filter
    if price_op and price is not None:
        if price_op not in _ALLOWED_OPS:
            raise ValueError("Invalid price_op")
        conditions.append(_apply_op(Item.price_usd, price_op, price))

    # Stock filter
    if stock_op and stock is not None:
        if stock_op not in _ALLOWED_OPS:
            raise ValueError("Invalid stock_op")
        conditions.append(_apply_op(Item.stock_qty, stock_op, stock))

    if conditions:
        stmt = stmt.where(and_(*conditions))

    stmt = stmt.order_by(Item.id.asc())

    return list(db.scalars(stmt).all())


def count_items(db: Session) -> int:
    return db.query(Item).count()


def create_item(db: Session, name: str, price_usd: float, stock_qty: int) -> Item:
    item = Item(name=name, price_usd=price_usd, stock_qty=stock_qty)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item