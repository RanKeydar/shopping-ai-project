# frontend/services/orders_service.py

from __future__ import annotations

from typing import Any

from services.api_client import api


class OrdersService:
    def get_cart(self) -> dict[str, Any] | None:
        data = api.get("/orders/cart")
        if data is None:
            return None
        if isinstance(data, dict):
            return data
        return None

    def add_item(self, item_id: int, quantity: int = 1) -> dict[str, Any] | None:
        return api.post(
            "/orders/cart/add-item",
            data={
                "item_id": item_id,
                "quantity": quantity,
            },
        )

    def add_to_order(self, item_id: int, quantity: int = 1) -> dict[str, Any] | None:
        return self.add_item(item_id=item_id, quantity=quantity)

    def update_quantity(self, item_id: int, quantity: int) -> dict[str, Any] | None:
        return api.post(
            "/orders/cart/update-quantity",
            data={
                "item_id": item_id,
                "quantity": quantity,
            },
        )

    def remove_item(self, item_id: int) -> dict[str, Any] | None:
        return api.delete(f"/orders/cart/remove-item/{item_id}")

    def checkout(self, shipping_address: str) -> dict[str, Any] | None:
        return api.post(
            "/orders/cart/checkout",
            data={
                "shipping_address": shipping_address,
            },
        )

    def list_orders(self) -> list[dict[str, Any]]:
        data = api.get("/orders")

        if data is None:
            return []

        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            if isinstance(data.get("orders"), list):
                return data["orders"]
            if isinstance(data.get("items"), list):
                return data["items"]

        return []


orders_service = OrdersService()