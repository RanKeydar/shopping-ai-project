from __future__ import annotations

from typing import Any, Callable

import streamlit as st

from services.api_client import APIClientError, APIConnectionError
from services.auth_service import auth_service
from services.favorites_service import favorites_service


def render_items_grid(
    items: list[dict[str, Any]],
    columns: int = 3,
    show_count: bool = True,
    enable_add_to_cart: bool = False,
    enable_favorites: bool = False,
    on_add_to_order: Callable[[dict[str, Any], int], None] | None = None,
) -> None:
    if show_count:
        st.caption(f"נמצאו {len(items)} פריטים")

    if not items:
        st.info("לא נמצאו פריטים.")
        return

    columns_per_row = max(1, columns)

    favorite_ids: set[int] = set()
    if enable_favorites and auth_service.is_authenticated():
        try:
            favorite_ids = favorites_service.get_favorites_ids()
        except Exception:
            favorite_ids = set()

    for row_start in range(0, len(items), columns_per_row):
        row_items = items[row_start : row_start + columns_per_row]
        cols = st.columns(columns_per_row)

        for idx, item in enumerate(row_items):
            with cols[idx]:
                item_id = int(item.get("id", 0))
                name = item.get("name", f"Item {item_id}")
                price = float(item.get("price_usd", 0) or 0)
                stock_qty = int(item.get("stock_qty", 0) or 0)
                category = item.get("category") or ""
                description = item.get("description") or ""

                with st.container(border=True):
                    st.markdown(f"### {name}")

                    meta_parts: list[str] = []
                    if category:
                        meta_parts.append(f"קטגוריה: {category}")
                    meta_parts.append(f"מלאי: {stock_qty}")
                    st.caption(" | ".join(meta_parts))

                    if description:
                        st.write(description)

                    st.write(f"מחיר: ${price:,.2f}")

                    if enable_favorites:
                        is_favorite = item_id in favorite_ids
                        favorite_label = "הסר ממועדפים" if is_favorite else "הוסף למועדפים"

                        if st.button(
                            favorite_label,
                            key=f"favorite_toggle_{item_id}",
                            use_container_width=True,
                        ):
                            if not auth_service.is_authenticated():
                                st.warning("צריך להתחבר כדי לנהל מועדפים.")
                            else:
                                try:
                                    favorites_service.toggle(item_id)
                                    st.rerun()
                                except APIConnectionError:
                                    st.error("לא ניתן להתחבר לשרת כרגע.")
                                except APIClientError as e:
                                    st.error(f"שגיאה בעדכון המועדפים: {e}")
                                except Exception as e:
                                    st.error(f"שגיאה לא צפויה בעדכון המועדפים: {e}")

                    if enable_add_to_cart:
                        if stock_qty <= 0:
                            st.warning("אזל מהמלאי")
                            st.button(
                                "Add to cart",
                                key=f"add_to_cart_{item_id}",
                                use_container_width=True,
                                disabled=True,
                            )
                            continue

                        quantity = st.number_input(
                            f"כמות עבור פריט {item_id}",
                            min_value=1,
                            max_value=stock_qty,
                            value=1,
                            step=1,
                            key=f"grid_qty_{item_id}",
                            label_visibility="collapsed",
                        )

                        if st.button(
                            "Add to cart",
                            key=f"add_to_cart_{item_id}",
                            use_container_width=True,
                        ):
                            if on_add_to_order is not None:
                                on_add_to_order(item, int(quantity))