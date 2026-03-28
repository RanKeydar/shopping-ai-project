from __future__ import annotations

from datetime import datetime


def format_order_datetime(value: str | None) -> str:
    if not value:
        return "-"

    try:
        dt = datetime.fromisoformat(value)
        return dt.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return value


def format_order_selector_label(order: dict) -> str:
    order_id = order.get("id", "-")
    status = order.get("status", "-")
    total_price = order.get("total_price")

    if total_price is None:
        total_part = ""
    else:
        try:
            total_part = f" | ${float(total_price):.2f}"
        except (TypeError, ValueError):
            total_part = f" | ${total_price}"

    return f"הזמנה #{order_id} | {status}{total_part}"