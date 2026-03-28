from __future__ import annotations

import streamlit as st

from services.api_client import APIClientError, APIConnectionError
from services.items_service import list_items
from services.orders_service import orders_service


def format_currency(value: float | int | None) -> str:
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return "$0.00"


def extract_error_message(exc: Exception) -> str:
    text = str(exc)

    if "Requested quantity exceeds available stock" in text:
        return "אין מספיק מלאי זמין עבור הפריט הזה."
    if "Cart not found" in text:
        return "אין כרגע הזמנה פתוחה."
    if "shipping_address" in text:
        return "יש להזין כתובת משלוח."
    if "out of stock" in text.lower():
        return "הפריט לא זמין במלאי."
    if "not found" in text.lower():
        return "הפריט או ההזמנה לא נמצאו."

    return text


def get_order_items(order: dict) -> list[dict]:
    items = order.get("items")
    if isinstance(items, list):
        return items

    lines = order.get("lines")
    if isinstance(lines, list):
        return lines

    return []


def has_order_items(order: dict) -> bool:
    return len(get_order_items(order)) > 0


def get_order_total(order: dict) -> float:
    total = order.get("total_price", order.get("total", 0))
    try:
        return float(total)
    except (TypeError, ValueError):
        return 0.0


def normalize_status(order: dict) -> str:
    status = order.get("status")

    if hasattr(status, "value"):
        status = status.value

    if status is None:
        return ""

    return str(status).strip().upper()


def is_non_empty_temp_order(order: dict) -> bool:
    return normalize_status(order) == "TEMP" and has_order_items(order)


def display_status(order: dict) -> str:
    status = normalize_status(order)
    if status == "TEMP":
        return "פתוחה"
    if status == "CLOSE":
        return "סגורה"
    return status or "-"


def load_orders_data() -> tuple[dict | None, list[dict]]:
    cart = None
    orders = []

    try:
        cart = orders_service.get_cart()
    except APIClientError as e:
        if "Cart not found" not in str(e):
            st.error(f"שגיאה בטעינת ההזמנה הפתוחה: {extract_error_message(e)}")
    except APIConnectionError:
        st.error("לא ניתן להתחבר לשרת כרגע.")
    except Exception as e:
        st.error(f"שגיאה בטעינת ההזמנה הפתוחה: {e}")

    try:
        orders = orders_service.list_orders()
    except APIConnectionError:
        st.error("לא ניתן להתחבר לשרת כרגע.")
    except APIClientError as e:
        st.error(f"שגיאה בטעינת ההזמנות: {extract_error_message(e)}")
    except Exception as e:
        st.error(f"שגיאה בטעינת ההזמנות: {e}")

    return cart, orders


def build_orders_list(cart: dict | None, orders: list[dict]) -> list[dict]:
    result: list[dict] = []

    if cart and is_non_empty_temp_order(cart):
        result.append(cart)

    for order in orders:
        if normalize_status(order) == "TEMP":
            if not has_order_items(order):
                continue

            if cart and order.get("id") == cart.get("id"):
                continue

        result.append(order)

    result.sort(
        key=lambda order: (
            0 if normalize_status(order) == "TEMP" else 1,
            str(order.get("created_at", "")),
        )
    )

    return result


def get_temp_order(orders_list: list[dict]) -> dict | None:
    for order in orders_list:
        if is_non_empty_temp_order(order):
            return order
    return None


def load_searchable_catalog_items(limit: int = 500) -> list[dict]:
    try:
        items = list_items(limit=limit)

        if not isinstance(items, list):
            return []

        return items
    except APIConnectionError:
        st.error("לא ניתן להתחבר לשרת כרגע.")
    except APIClientError as e:
        st.error(f"שגיאה בטעינת קטלוג הפריטים: {extract_error_message(e)}")
    except Exception as e:
        st.error(f"שגיאה בטעינת קטלוג הפריטים: {e}")

    return []