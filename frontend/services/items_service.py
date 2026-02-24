# frontend/services/items_service.py

import os
from typing import Any, Dict, List, Optional

from services.api_client import api

# מאפשר לך לשנות בקלות אם ה-backend הוא /api/items או /items
API_PREFIX = os.getenv("API_PREFIX", "").rstrip("/")
ITEMS_PATH = f"{API_PREFIX}/items" if API_PREFIX else "/items"

def list_items(
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    q: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch items list.
    Supports optional pagination and search query if backend supports it.
    """
    params: Dict[str, Any] = {}
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    if q:
        params["q"] = q

    data = api.get(ITEMS_PATH, params=params or None)
    # Backend יכול להחזיר list ישירות או מעטפת {"items": [...]}
    if isinstance(data, dict) and "items" in data:
        return data["items"]
    return data or []


def get_item(item_id: int) -> Dict[str, Any]:
    """Fetch a single item by id."""
    return api.get(f"{ITEMS_PATH}/{item_id}")


def create_item(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new item.
    payload example:
      {"name": "...", "price": 123, "url": "...", ...}
    """
    return api.post(ITEMS_PATH, data=payload)


def update_item(item_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Update an item (PUT)."""
    return api.put(f"{ITEMS_PATH}/{item_id}", data=payload)


def delete_item(item_id: int) -> None:
    """Delete an item. Returns None for 204."""
    api.delete(f"{ITEMS_PATH}/{item_id}")
    return None


def favorite_item(item_id: int) -> Dict[str, Any]:
    """
    Optional endpoint (if you have it):
    POST /api/items/{id}/favorite
    """
    return api.post(f"{ITEMS_PATH}/{item_id}/favorite", data=None)


def unfavorite_item(item_id: int) -> None:
    """
    Optional endpoint (if you have it):
    DELETE /api/items/{id}/favorite
    """
    api.delete(f"{ITEMS_PATH}/{item_id}/favorite")
    return None
