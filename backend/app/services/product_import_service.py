from __future__ import annotations

from decimal import Decimal

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Item


DUMMYJSON_PRODUCTS_URL = "https://dummyjson.com/products"
PAGE_SIZE = 30


def fetch_products_from_dummyjson(limit: int = 30, skip: int = 0) -> list[dict]:
    response = requests.get(
        DUMMYJSON_PRODUCTS_URL,
        params={
            "limit": limit,
            "skip": skip,
        },
        timeout=30,
    )
    response.raise_for_status()

    data = response.json()
    products = data.get("products", [])

    if not isinstance(products, list):
        raise ValueError("Invalid products payload from DummyJSON")

    return products


def map_dummyjson_product_to_item_data(product: dict) -> dict:
    return {
        "name": str(product.get("title", "")).strip(),
        "price_usd": Decimal(str(product.get("price", 0))),
        "stock_qty": int(product.get("stock", 0)),
        "category": (
            str(product.get("category")).strip()
            if product.get("category") is not None
            else None
        ),
        "description": (
            str(product.get("description")).strip()
            if product.get("description") is not None
            else None
        ),
    }


def upsert_product(db: Session, item_data: dict) -> str:
    existing_item = db.execute(
        select(Item).where(Item.name == item_data["name"])
    ).scalar_one_or_none()

    if existing_item is None:
        item = Item(
            name=item_data["name"],
            price_usd=item_data["price_usd"],
            stock_qty=item_data["stock_qty"],
            category=item_data["category"],
            description=item_data["description"],
        )
        db.add(item)
        return "created"

    changed = False

    if existing_item.price_usd != item_data["price_usd"]:
        existing_item.price_usd = item_data["price_usd"]
        changed = True

    if existing_item.stock_qty != item_data["stock_qty"]:
        existing_item.stock_qty = item_data["stock_qty"]
        changed = True

    if existing_item.category != item_data["category"]:
        existing_item.category = item_data["category"]
        changed = True

    if existing_item.description != item_data["description"]:
        existing_item.description = item_data["description"]
        changed = True

    return "updated" if changed else "skipped"


def import_products_page_to_db(db: Session, limit: int = 30, skip: int = 0) -> dict:
    products = fetch_products_from_dummyjson(limit=limit, skip=skip)

    created_count = 0
    updated_count = 0
    skipped_count = 0
    seen_names = set()

    for product in products:
        item_data = map_dummyjson_product_to_item_data(product)
        name = item_data["name"]

        if name in seen_names:
            skipped_count += 1
            continue

        seen_names.add(name)
        result = upsert_product(db, item_data)

        if result == "created":
            created_count += 1
        elif result == "updated":
            updated_count += 1
        else:
            skipped_count += 1

    db.commit()

    return {
        "fetched_count": len(products),
        "created_count": created_count,
        "updated_count": updated_count,
        "skipped_count": skipped_count,
        "limit": limit,
        "skip": skip,
    }


def import_all_products_to_db(db: Session, page_size: int = PAGE_SIZE) -> dict:
    total_fetched = 0
    total_created = 0
    total_updated = 0
    total_skipped = 0

    skip = 0
    seen_names = set()

    while True:
        products = fetch_products_from_dummyjson(limit=page_size, skip=skip)

        if not products:
            break

        for product in products:
            item_data = map_dummyjson_product_to_item_data(product)
            name = item_data["name"]

            if name in seen_names:
                total_skipped += 1
                continue

            seen_names.add(name)
            result = upsert_product(db, item_data)

            if result == "created":
                total_created += 1
            elif result == "updated":
                total_updated += 1
            else:
                total_skipped += 1

        total_fetched += len(products)
        skip += page_size

    db.commit()

    return {
        "total_fetched": total_fetched,
        "total_created": total_created,
        "total_updated": total_updated,
        "total_skipped": total_skipped,
        "page_size": page_size,
    }