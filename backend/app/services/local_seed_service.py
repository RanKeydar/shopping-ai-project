from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import Item


DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "products_seed.json"


def import_local_products_to_db(db: Session) -> dict:
    if db.query(Item).count() > 0:
        return {
            "message": "Items already exist. Skipping local seed.",
            "created": 0,
        }

    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Local seed file not found: {DATA_FILE}")

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        products = json.load(f)

    created = 0

    for product in products:
        item = Item(
            name=product["name"],
            price_usd=product["price_usd"],
            stock_qty=product["stock_qty"],
            category=product.get("category"),
            description=product.get("description"),
        )
        db.add(item)
        created += 1

    db.commit()

    return {
        "message": "Local products imported successfully",
        "created": created,
    }