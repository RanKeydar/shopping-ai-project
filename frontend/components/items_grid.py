import html
from typing import Any, Iterable, Mapping

import streamlit as st


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return html.escape(str(value))


def _price_value(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _stock_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _format_price(value: Any) -> str:
    return f"${_price_value(value):,.2f}"


def _stock_badge_html(stock: int) -> str:
    if stock <= 0:
        label = "Out of stock"
        bg = "#fee2e2"
        fg = "#991b1b"
    elif stock <= 5:
        label = f"Low stock: {stock}"
        bg = "#fef3c7"
        fg = "#92400e"
    else:
        label = f"In stock: {stock}"
        bg = "#dcfce7"
        fg = "#166534"

    return f"""
<div style="display:inline-block;padding:6px 10px;border-radius:999px;font-size:0.82rem;font-weight:600;background:{bg};color:{fg};margin-top:10px;">
    {label}
</div>
"""

def _card_html(item: Mapping[str, Any]) -> str:
    name = _safe_text(item.get("name"), "Unnamed Item")
    price = _format_price(item.get("price_usd"))
    stock = _stock_value(item.get("stock_qty"))

    badge_html = _stock_badge_html(stock)

    return f"""
<div style="border:1px solid #e5e7eb;border-radius:18px;padding:18px;background:#ffffff;min-height:220px;box-shadow:0 2px 10px rgba(15,23,42,0.06);margin-bottom:18px;">
    <div style="height:110px;border-radius:14px;background:linear-gradient(135deg,#f8fafc 0%,#eef2ff 100%);display:flex;align-items:center;justify-content:center;margin-bottom:14px;font-size:2rem;">🛍️</div>
    <div style="font-size:1.02rem;font-weight:700;color:#111827;line-height:1.4;min-height:46px;margin-bottom:10px;">{name}</div>
    <div style="font-size:1.28rem;font-weight:800;color:#0f172a;margin-bottom:2px;">{price}</div>
    <div style="font-size:0.88rem;color:#6b7280;">Price in USD</div>
    {badge_html}
</div>
"""


def render_items_grid(
    items: Iterable[Mapping[str, Any]],
    columns: int = 3,
    show_count: bool = True,
) -> None:
    items = list(items)

    if show_count:
        st.caption(f"{len(items)} items found")

    if not items:
        st.info("No items found.")
        return

    columns = max(1, columns)

    for start_idx in range(0, len(items), columns):
        row_items = items[start_idx:start_idx + columns]
        cols = st.columns(columns, gap="large")

        for col, item in zip(cols, row_items):
            with col:
                st.markdown(_card_html(item), unsafe_allow_html=True)