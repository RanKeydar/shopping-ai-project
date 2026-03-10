from fastapi import APIRouter, Depends, Query, HTTPException, Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.concurrency import run_in_threadpool
from redis.asyncio import Redis
from sqlalchemy.orm import Session
import json

from app.db import get_db
from app.repositories.items_repo import list_items as repo_list_items
from app.schemas.item import ItemOut
from app.cache.redis_client import get_redis
from app.cache.cache_keys import items_list_cache_key

router = APIRouter(prefix="/items", tags=["items"])

_ALLOWED_OPS = {"<", "<=", "=", ">=", ">"}
CACHE_TTL_SECONDS = 60


@router.get("", response_model=list[ItemOut])
async def list_items(
    request: Request,
    response: Response,
    q: str | None = Query(None, min_length=1),
    price_op: str | None = Query(None, description="One of: <, <=, =, >=, >"),
    price: float | None = Query(None, ge=0),
    stock_op: str | None = Query(None, description="One of: <, <=, =, >=, >"),
    stock: int | None = Query(None, ge=0),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    # זוגות פרמטרים חייבים להגיע יחד
    if (price_op is None) ^ (price is None):
        raise HTTPException(status_code=400, detail="price_op and price must be provided together")
    if (stock_op is None) ^ (stock is None):
        raise HTTPException(status_code=400, detail="stock_op and stock must be provided together")

    # ולידציה מוקדמת ל-ops
    if price_op is not None and price_op not in _ALLOWED_OPS:
        raise HTTPException(status_code=400, detail=f"Invalid price_op. Allowed: {sorted(_ALLOWED_OPS)}")
    if stock_op is not None and stock_op not in _ALLOWED_OPS:
        raise HTTPException(status_code=400, detail=f"Invalid stock_op. Allowed: {sorted(_ALLOWED_OPS)}")

    cache_key = items_list_cache_key(request)

    # 1) try cache (best effort)
    try:
        cached = await redis.get(cache_key)
        if cached:
            response.headers["X-Cache"] = "HIT"
            return json.loads(cached)
    except Exception:
        pass

    # 2) fetch from DB via repo (sync) but called safely from async
    try:
        items = await run_in_threadpool(
            repo_list_items,
            db=db,
            q=q,
            price_op=price_op,
            price=price,
            stock_op=stock_op,
            stock=stock,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 3) set cache (best effort)
    try:
        payload = jsonable_encoder(items)
        await redis.setex(cache_key, CACHE_TTL_SECONDS, json.dumps(payload))
    except Exception:
        pass

    response.headers["X-Cache"] = "MISS"
    return items