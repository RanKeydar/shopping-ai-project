from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.product_import_service import (
    fetch_products_from_dummyjson,
    import_all_products_to_db,
    import_products_page_to_db,
)

router = APIRouter(prefix="/product-import", tags=["product-import"])


@router.get("/preview")
def preview_import(limit: int = 5, skip: int = 0):
    products = fetch_products_from_dummyjson(limit=limit, skip=skip)

    return {
        "count": len(products),
        "products": products,
    }


@router.post("/seed")
def seed_products(
    limit: int = 30,
    skip: int = 0,
    db: Session = Depends(get_db),
):
    return import_products_page_to_db(db=db, limit=limit, skip=skip)


@router.post("/seed-all")
def seed_all_products(
    page_size: int = 30,
    db: Session = Depends(get_db),
):
    return import_all_products_to_db(db=db, page_size=page_size)