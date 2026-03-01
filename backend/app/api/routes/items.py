from typing import Optional, Literal
from fastapi import APIRouter, Depends, Query, HTTPException

from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories.items_repo import list_items as repo_list_items
from app.schemas.item import ItemOut

router = APIRouter(prefix="/items", tags=["items"])

_ALLOWED_OPS = {"<", "<=", "=", ">=", ">"}

@router.get("", response_model=list[ItemOut])
def list_items(
    q: str | None = Query(None, min_length=1),
    price_op: str | None = Query(None, description="One of: <, <=, =, >=, >"),
    price: float | None = Query(None, ge=0),
    stock_op: str | None = Query(None, description="One of: <, <=, =, >=, >"),
    stock: int | None = Query(None, ge=0),
    db: Session = Depends(get_db),
):
    # זוגות פרמטרים חייבים להגיע יחד
    if (price_op is None) ^ (price is None):
        raise HTTPException(status_code=400, detail="price_op and price must be provided together")
    if (stock_op is None) ^ (stock is None):
        raise HTTPException(status_code=400, detail="stock_op and stock must be provided together")

    # ולידציה מוקדמת ל-ops (יותר ברור מאשר ValueError מהריפו)
    if price_op is not None and price_op not in _ALLOWED_OPS:
        raise HTTPException(status_code=400, detail=f"Invalid price_op. Allowed: {sorted(_ALLOWED_OPS)}")
    if stock_op is not None and stock_op not in _ALLOWED_OPS:
        raise HTTPException(status_code=400, detail=f"Invalid stock_op. Allowed: {sorted(_ALLOWED_OPS)}")

    try:
        return repo_list_items(
            db=db,
            q=q,
            price_op=price_op,
            price=price,
            stock_op=stock_op,
            stock=stock,
        )
    except ValueError as e:
        # אם משהו בכל זאת נזרק מהריפו (למשל op לא חוקי) – נחזיר 400
        raise HTTPException(status_code=400, detail=str(e))