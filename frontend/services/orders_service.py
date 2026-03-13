from __future__ import annotations

import time
import streamlit as st
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Literal

from services.auth_service import auth_service

ORDERS_KEY = "orders_by_user"

OrderStatus = Literal["created", "paid", "shipped", "delivered", "cancelled"]


@dataclass(frozen=True)
class OrderLine:
    item_id: int
    name: str
    quantity: int = 1
    unit_price: Optional[float] = None  # אם אין מחיר ב-mock, נשאיר None


@dataclass(frozen=True)
class Order:
    order_id: int
    user: str
    created_at: int  # epoch seconds
    status: OrderStatus
    lines: List[OrderLine]
    notes: Optional[str] = None


class OrdersService:
    # -------------------------
    # Internals
    # -------------------------

    def _get_store(self) -> Dict[str, Dict[int, dict]]:
        if ORDERS_KEY not in st.session_state:
            st.session_state[ORDERS_KEY] = {}
        return st.session_state[ORDERS_KEY]

    def _current_user(self) -> Optional[str]:
        user = auth_service.get_current_user() or {}
        return user.get("username")

    def _get_user_bucket(self, username: str) -> Dict[int, dict]:
        store = self._get_store()
        if username not in store:
            store[username] = {}
        return store[username]

    def _next_order_id(self, username: str) -> int:
        bucket = self._get_user_bucket(username)
        if not bucket:
            return 1
        return max(bucket.keys()) + 1

    def _dict_to_order(self, data: dict) -> Order:
        lines = [OrderLine(**ln) for ln in data.get("lines", [])]
        return Order(
            order_id=int(data["order_id"]),
            user=str(data["user"]),
            created_at=int(data["created_at"]),
            status=data["status"],
            lines=lines,
            notes=data.get("notes"),
        )

    def _order_to_dict(self, order: Order) -> dict:
        return {
            **asdict(order),
            "lines": [asdict(l) for l in order.lines],
        }

    # -------------------------
    # Public API (for UI)
    # -------------------------

    def list_orders(self) -> List[Order]:
        username = self._current_user()
        if not username:
            return []

        bucket = self._get_user_bucket(username)
        orders = [self._dict_to_order(v) for v in bucket.values()]
        orders.sort(key=lambda o: o.created_at, reverse=True)
        return orders

    def get_order(self, order_id: int) -> Optional[Order]:
        username = self._current_user()
        if not username:
            return None

        bucket = self._get_user_bucket(username)
        data = bucket.get(int(order_id))
        return self._dict_to_order(data) if data else None

    def create_order(self, lines: List[OrderLine], notes: Optional[str] = None) -> Order:
        username = self._current_user()
        if not username:
            raise RuntimeError("Not authenticated: cannot create order")

        if not lines:
            raise ValueError("Order must include at least one line")

        for ln in lines:
            if ln.quantity <= 0:
                raise ValueError("Quantity must be positive")

        order_id = self._next_order_id(username)
        order = Order(
            order_id=order_id,
            user=username,
            created_at=int(time.time()),
            status="created",
            lines=lines,
            notes=notes,
        )

        bucket = self._get_user_bucket(username)
        bucket[order_id] = self._order_to_dict(order)
        return order

    def cancel_order(self, order_id: int) -> bool:
        username = self._current_user()
        if not username:
            return False

        bucket = self._get_user_bucket(username)
        oid = int(order_id)
        if oid not in bucket:
            return False

        data = bucket[oid]

        # אפשר להקשיח: לא לאפשר ביטול אחרי shipped/delivered וכו'
        data["status"] = "cancelled"
        bucket[oid] = data
        return True

    def get_order_total(self, order: Order) -> Optional[float]:
        total = 0.0
        for ln in order.lines:
            if ln.unit_price is None:
                return None
            total += float(ln.unit_price) * int(ln.quantity)
        return total


orders_service = OrdersService()