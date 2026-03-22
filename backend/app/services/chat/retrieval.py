from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Item


def list_items_for_ai(db: Session) -> list[dict]:
    items = db.execute(select(Item)).scalars().all()

    result: list[dict] = []
    for item in items:
        result.append(
            {
                "id": item.id,
                "name": item.name,
                "category": item.category,
                "description": item.description,
                "price_usd": float(item.price_usd),
                "stock_qty": int(item.stock_qty),
            }
        )
    return result


def search_items_by_keywords(db: Session, prompt: str) -> list[Item]:
    search = (prompt or "").strip()
    if not search:
        return []

    stmt = (
        select(Item)
        .where(
            or_(
                Item.name.ilike(f"%{search}%"),
                Item.category.ilike(f"%{search}%"),
                Item.description.ilike(f"%{search}%"),
            )
        )
        .limit(10)
    )

    return list(db.execute(stmt).scalars().all())


def items_to_dicts(items: list[Item]) -> list[dict]:
    result: list[dict] = []

    for item in items:
        result.append(
            {
                "id": item.id,
                "name": item.name,
                "category": item.category,
                "description": item.description,
                "price_usd": float(item.price_usd),
                "stock_qty": int(item.stock_qty),
            }
        )

    return result