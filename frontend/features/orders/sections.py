from __future__ import annotations

import pandas as pd
import streamlit as st

from services.search_service import filter_and_sort_items_by_query

from features.orders.actions import (
    handle_add_item,
    handle_checkout,
    handle_remove_item,
    handle_select_order,
    handle_update_quantity,
)
from features.orders.data import (
    display_status,
    format_currency,
    get_order_items,
    get_order_total,
    load_searchable_catalog_items,
    normalize_status,
)
from features.orders.state import (
    clear_order_item_search_reset_flag,
    should_reset_order_item_search,
    sync_pending_shipping_address,
)


def render_order_selector(orders_list: list[dict]) -> None:
    st.subheader("רשימת הזמנות")

    if not orders_list:
        st.info("אין עדיין הזמנות למשתמש הזה.")
        return

    for order in orders_list:
        order_id = order.get("id", "-")
        status_text = display_status(order)
        total_price = get_order_total(order)
        created_at = order.get("created_at", "")
        is_temp = normalize_status(order) == "TEMP"

        title = f"הזמנה #{order_id} | {status_text} | {format_currency(total_price)}"
        if is_temp:
            title = f"🟠 {title}"

        with st.container(border=True):
            col1, col2 = st.columns([5, 1])

            with col1:
                st.markdown(f"**{title}**")
                if created_at:
                    st.caption(f"תאריך יצירה: {created_at}")
                if is_temp:
                    st.caption("זוהי ההזמנה הפתוחה שלך. ניתן לערוך, להסיר פריטים או להשלים רכישה.")
                else:
                    st.caption("הזמנה סגורה – לצפייה בלבד.")

            with col2:
                if st.button("פתח", key=f"open_order_{order_id}", use_container_width=True):
                    handle_select_order(
                        order_id=order_id,
                        shipping_address=order.get("shipping_address"),
                    )


def render_create_new_order_panel(temp_order: dict | None) -> None:
    if temp_order is not None:
        return

    st.subheader("פתיחת הזמנה חדשה")
    st.caption("אין כרגע הזמנה פתוחה. כדי לפתוח הזמנה חדשה, חפש פריט והוסף אותו.")

    render_item_search_and_add()


def render_closed_order_details(order: dict) -> None:
    st.subheader(f"פרטי הזמנה #{order.get('id', '-')}")
    st.caption("הזמנה סגורה – לצפייה בלבד")

    created_at = order.get("created_at", "")
    shipping_address = order.get("shipping_address", "")
    items = get_order_items(order)
    total_price = get_order_total(order)

    if created_at:
        st.write(f"**תאריך:** {created_at}")
    if shipping_address:
        st.write(f"**כתובת משלוח:** {shipping_address}")

    st.write(f"**סה\"כ הזמנה:** {format_currency(total_price)}")

    if items:
        rows = []
        for item in items:
            quantity = int(item.get("quantity", 0) or 0)
            unit_price = float(item.get("unit_price", 0) or 0)
            line_total = float(item.get("line_total", quantity * unit_price))

            rows.append(
                {
                    "פריט": item.get("name", item.get("item_id", "-")),
                    "כמות": quantity,
                    "מחיר יחידה": format_currency(unit_price),
                    "סה\"כ": format_currency(line_total),
                }
            )

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("אין פריטים להצגה בהזמנה זו.")


def render_item_search_and_add() -> None:
    st.markdown("### הוספת פריט להזמנה")

    if should_reset_order_item_search():
        st.session_state["order_item_search_query"] = ""
        clear_order_item_search_reset_flag()

    search_query = st.text_input(
        "חפש פריט לפי שם או תיאור",
        key="order_item_search_query",
        placeholder="לדוגמה: חלב, לחם, שמפו",
    ).strip()

    if not search_query:
        st.info("הקלד שם מוצר כדי לחפש ולהוסיף אותו להזמנה.")
        return

    items = load_searchable_catalog_items(limit=100)
    items = filter_and_sort_items_by_query(items, search_query)

    if not items:
        st.info("לא נמצאו פריטים מתאימים לחיפוש.")
        return

    st.caption("בחר פריט מתוך תוצאות החיפוש והוסף אותו להזמנה.")

    for item in items:
        item_id = int(item.get("id"))
        name = item.get("name", f"פריט {item_id}")
        price = float(item.get("price_usd", 0) or 0)
        stock_qty = int(item.get("stock_qty", 0) or 0)
        category = item.get("category") or ""
        description = item.get("description") or ""

        with st.container(border=True):
            col1, col2, col3 = st.columns([4, 2, 1])

            with col1:
                st.markdown(f"**{name}**")
                meta_parts = []
                if category:
                    meta_parts.append(f"קטגוריה: {category}")
                meta_parts.append(f"מלאי: {stock_qty}")
                st.caption(" | ".join(meta_parts))

                if description:
                    st.write(description)

            with col2:
                st.write(f"מחיר: {format_currency(price)}")
                quantity = st.number_input(
                    f"כמות עבור פריט {item_id}",
                    min_value=1,
                    max_value=max(1, stock_qty) if stock_qty > 0 else 1,
                    value=1,
                    step=1,
                    key=f"search_add_qty_{item_id}",
                    label_visibility="collapsed",
                )

            with col3:
                if stock_qty <= 0:
                    st.caption("אזל מהמלאי")
                else:
                    if st.button("הוסף", key=f"search_add_btn_{item_id}", use_container_width=True):
                        handle_add_item(
                            item_id=item_id,
                            quantity=int(quantity),
                            item_name=name,
                        )


def render_temp_order_process(order: dict) -> None:
    st.subheader(f"תהליך הזמנה | הזמנה #{order.get('id', '-')}")
    st.caption("כאן אפשר לעדכן את ההזמנה הפתוחה, להסיר פריטים, להוסיף פריטים ולהשלים רכישה.")

    items = get_order_items(order)
    total_price = get_order_total(order)
    shipping_address_from_order = (order.get("shipping_address") or "").strip()

    if shipping_address_from_order and not st.session_state.shipping_address:
        st.session_state.shipping_address = shipping_address_from_order

    if not items:
        st.info("ההזמנה הפתוחה כרגע ריקה.")
        render_item_search_and_add()
        return

    st.write(f"**סה\"כ הזמנה:** {format_currency(total_price)}")

    rows = []
    for item in items:
        quantity = int(item.get("quantity", 0) or 0)
        unit_price = float(item.get("unit_price", 0) or 0)
        line_total = float(item.get("line_total", quantity * unit_price))

        rows.append(
            {
                "פריט": item.get("name", item.get("item_id", "-")),
                "כמות": quantity,
                "מחיר יחידה": format_currency(unit_price),
                "סה\"כ": format_currency(line_total),
            }
        )

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("### עדכון פריטים בהזמנה")

    for item in items:
        item_id = item.get("item_id")
        name = item.get("name", f"פריט {item_id}")
        quantity = int(item.get("quantity", 1) or 1)
        unit_price = float(item.get("unit_price", 0) or 0)
        line_total = float(item.get("line_total", quantity * unit_price))

        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 2, 2])

            with col1:
                st.markdown(f"**{name}**")
                st.caption(f"מזהה פריט: {item_id}")
                st.write(f"מחיר יחידה: {format_currency(unit_price)}")
                st.write(f"סה\"כ שורה: {format_currency(line_total)}")

            with col2:
                new_quantity = st.number_input(
                    f"כמות עבור {item_id}",
                    min_value=1,
                    step=1,
                    value=quantity,
                    key=f"temp_qty_{item_id}",
                    label_visibility="collapsed",
                )
                if st.button("עדכן כמות", key=f"temp_update_{item_id}", use_container_width=True):
                    handle_update_quantity(
                        item_id=int(item_id),
                        quantity=int(new_quantity),
                        item_name=name,
                    )

            with col3:
                if st.button("הסר מההזמנה", key=f"temp_remove_{item_id}", use_container_width=True):
                    handle_remove_item(
                        item_id=int(item_id),
                        item_name=name,
                    )

    st.divider()

    render_item_search_and_add()

    st.divider()

    st.markdown("### פרטי משלוח ורכישה")

    sync_pending_shipping_address()

    shipping_address = st.text_input(
        "כתובת משלוח",
        key="shipping_address",
        placeholder="לדוגמה: הרצל 10, אשדוד",
    )

    if st.button("בצע רכישה", type="primary", use_container_width=True):
        handle_checkout(shipping_address)


def render_selected_order(orders_list: list[dict]) -> None:
    selected_order_id = st.session_state.selected_order_id

    if selected_order_id is None:
        st.info("בחר הזמנה מהרשימה כדי לראות פרטים או לערוך הזמנה פתוחה.")
        return

    selected_order = next(
        (order for order in orders_list if order.get("id") == selected_order_id),
        None,
    )

    if not selected_order:
        st.warning("ההזמנה שבחרת כבר לא זמינה.")
        st.session_state.selected_order_id = None
        return

    status = normalize_status(selected_order)

    if status == "TEMP":
        render_temp_order_process(selected_order)
        return

    render_closed_order_details(selected_order)