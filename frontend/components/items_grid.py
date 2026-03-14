import html
from typing import Any, Iterable, Mapping

import streamlit as st

from services.auth_service import auth_service
from services.orders_service import orders_service
from services.favorites_service import favorites_service
from services.api_client import APIClientError, APIConnectionError


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


def _extract_error_message(exc: Exception) -> str:
    text = str(exc)

    if "Requested quantity exceeds available stock" in text:
        return "אין מספיק מלאי זמין עבור הפריט הזה."
    if "Cart not found" in text:
        return "אין כרגע עגלה פעילה."
    if "Item already in favorites" in text:
        return "הפריט כבר נמצא במועדפים."
    if "Favorite not found" in text:
        return "הפריט לא נמצא במועדפים."
    if "Not authenticated" in text or "401" in text:
        return "צריך להתחבר כדי לבצע את הפעולה."

    return text


def render_items_grid(
    items: Iterable[Mapping[str, Any]],
    columns: int = 3,
    show_count: bool = True,
    enable_add_to_cart: bool = False,
    enable_favorites: bool = False,
) -> None:
    items = list(items)

    if show_count:
        st.caption(f"{len(items)} items found")

    if not items:
        st.info("No items found.")
        return

    columns = max(1, columns)
    is_authenticated = auth_service.is_authenticated()

    favorite_ids: set[int] = set()
    favorites_available = False

    if enable_favorites and is_authenticated:
        try:
            favorite_ids = favorites_service.get_favorites_ids()
            favorites_available = True
        except (APIClientError, APIConnectionError):
            favorite_ids = set()
            favorites_available = False

    for start_idx in range(0, len(items), columns):
        row_items = items[start_idx:start_idx + columns]
        cols = st.columns(columns, gap="large")

        for col, item in zip(cols, row_items):
            with col:
                st.markdown(_card_html(item), unsafe_allow_html=True)

                item_id = item.get("id")
                name = item.get("name", f"Item {item_id}")
                stock_qty = _stock_value(item.get("stock_qty"))

                if item_id is None:
                    continue

                item_id = int(item_id)

                # -------- Favorites --------
                if enable_favorites:
                    if not is_authenticated:
                        st.caption("יש להתחבר כדי לנהל מועדפים.")
                    elif not favorites_available:
                        st.caption("לא ניתן לטעון מועדפים כרגע.")
                    else:
                        is_favorite = item_id in favorite_ids
                        fav_label = "♥ Remove favorite" if is_favorite else "♡ Add favorite"

                        if st.button(
                            fav_label,
                            key=f"fav_btn_{item_id}",
                            use_container_width=True,
                        ):
                            try:
                                if is_favorite:
                                    favorites_service.remove(item_id)
                                    st.success(f"'{name}' הוסר מהמועדפים.")
                                else:
                                    favorites_service.add(item_id)
                                    st.success(f"'{name}' נוסף למועדפים.")
                                st.rerun()
                            except APIConnectionError:
                                st.error("לא ניתן להתחבר לשרת כרגע.")
                            except APIClientError as e:
                                st.error(_extract_error_message(e))

                # -------- Add to cart --------
                if not enable_add_to_cart:
                    continue

                if not is_authenticated:
                    st.caption("יש להתחבר כדי להוסיף לעגלה.")
                    continue

                qty_key = f"add_qty_{item_id}"
                btn_key = f"add_btn_{item_id}"

                max_qty = stock_qty if stock_qty > 0 else 1

                quantity = st.number_input(
                    f"Quantity for {name}",
                    min_value=1,
                    max_value=max_qty,
                    value=1,
                    step=1,
                    key=qty_key,
                    disabled=stock_qty <= 0,
                )

                if stock_qty <= 0:
                    st.button(
                        "Out of stock",
                        key=btn_key,
                        use_container_width=True,
                        disabled=True,
                    )
                    continue

                if st.button("Add to cart", key=btn_key, use_container_width=True):
                    try:
                        orders_service.add_item(
                            item_id=item_id,
                            quantity=int(quantity),
                        )
                        st.success(f"'{name}' נוסף לעגלה.")
                        st.rerun()
                    except APIConnectionError:
                        st.error("לא ניתן להתחבר לשרת כרגע.")
                    except APIClientError as e:
                        st.error(_extract_error_message(e))