import os
from typing import Any, Dict, List, Optional
import time

from services.api_client import api

API_PREFIX = os.getenv("API_PREFIX", "").strip()
if API_PREFIX:
    API_PREFIX = "/" + API_PREFIX.strip("/")
ITEMS_PATH = f"{API_PREFIX}/items" if API_PREFIX else "/items"


def list_items(
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    q: Optional[str] = None,
    price_op: Optional[str] = None,
    price: Optional[float] = None,
    stock_op: Optional[str] = None,
    stock: Optional[int] = None,
) -> List[Dict[str, Any]]:

    params: Dict[str, Any] = {}

    if limit is not None:
        params["limit"] = int(limit)

    if offset is not None:
        params["offset"] = int(offset)

    if q is not None:
        q = q.strip()
        if q:
            params["q"] = q

    if price_op is not None and price is not None:
        params["price_op"] = price_op
        params["price"] = float(price)

    if stock_op is not None and stock is not None:
        params["stock_op"] = stock_op
        params["stock"] = int(stock)

    import time

    start = time.perf_counter()
    data = api.get(ITEMS_PATH, params=params or None)
    print(f"GET {ITEMS_PATH} took {time.perf_counter() - start:.2f}s")

    if isinstance(data, dict) and "items" in data:
        return data["items"]

    return data or []


def get_item(item_id: int) -> Dict[str, Any]:
    return api.get(f"{ITEMS_PATH}/{item_id}")


def create_item(payload: Dict[str, Any]) -> Dict[str, Any]:
    return api.post(ITEMS_PATH, data=payload)


def update_item(item_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    return api.put(f"{ITEMS_PATH}/{item_id}", data=payload)


def delete_item(item_id: int) -> None:
    api.delete(f"{ITEMS_PATH}/{item_id}")
    return None


def favorite_item(item_id: int) -> Dict[str, Any]:
     return api.post(f"{ITEMS_PATH}/{item_id}/favorite", data=None)


def unfavorite_item(item_id: int) -> None:
    api.delete(f"{ITEMS_PATH}/{item_id}/favorite")
    return None
