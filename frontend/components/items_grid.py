from __future__ import annotations

from typing import Any, Callable

import streamlit as st


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
                        st.caption("♡ מועדפים")

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