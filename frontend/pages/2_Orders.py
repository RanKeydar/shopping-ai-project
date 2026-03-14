# frontend/pages/2_Orders.py

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.protected_page import require_auth
from services.auth_service import auth_service
from services.orders_service import orders_service
from services.api_client import APIClientError, APIConnectionError


user = require_auth("הזמנות")
st.caption(f"שלום {auth_service.get_display_name()}")

if "shipping_address" not in st.session_state:
    st.session_state.shipping_address = ""

if "clear_shipping_address" not in st.session_state:
    st.session_state.clear_shipping_address = False

def format_currency(value: float | int | None) -> str:
    try:
        return f"₪{float(value):,.2f}"
    except (TypeError, ValueError):
        return "₪0.00"


def extract_error_message(exc: Exception) -> str:
    text = str(exc)

    if "Requested quantity exceeds available stock" in text:
        return "אין מספיק מלאי זמין עבור הפריט הזה."
    if "Cart not found" in text:
        return "אין כרגע עגלה פעילה."
    if "shipping_address" in text:
        return "יש להזין כתובת משלוח."

    return text


def get_cart_items(cart: dict) -> list[dict]:
    items = cart.get("items")
    if isinstance(items, list):
        return items

    lines = cart.get("lines")
    if isinstance(lines, list):
        return lines

    return []


def get_cart_total(cart: dict) -> float:
    total = cart.get("total_price", cart.get("total", 0))
    try:
        return float(total)
    except (TypeError, ValueError):
        return 0.0


def render_cart() -> None:
    st.subheader("עגלה פעילה")

    if st.session_state.get("clear_shipping_address"):
        st.session_state.shipping_address = ""
        st.session_state.clear_shipping_address = False
        
    try:
        cart = orders_service.get_cart()
    except APIConnectionError:
        st.error("לא ניתן להתחבר לשרת כרגע.")
        return
    except APIClientError as e:
        st.error(f"שגיאה בטעינת העגלה: {extract_error_message(e)}")
        return

    if not cart:
        st.info("אין כרגע עגלה פעילה.")
        return

    items = get_cart_items(cart)
    total_price = get_cart_total(cart)

    if not items:
        st.info("העגלה כרגע ריקה.")
        return

    st.write(f"**סה\"כ לעגלה:** {format_currency(total_price)}")

    for item in items:
        item_id = item.get("item_id")
        name = item.get("name", f"פריט {item_id}")
        quantity = int(item.get("quantity", 1))
        unit_price = float(item.get("unit_price", 0))
        line_total = float(item.get("line_total", quantity * unit_price))
        stock_qty = item.get("stock_qty")

        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

            with col1:
                st.markdown(f"**{name}**")
                st.caption(f"מזהה פריט: {item_id}")
                if stock_qty is not None:
                    st.caption(f"מלאי זמין: {stock_qty}")

            with col2:
                st.write(f"מחיר יחידה: {format_currency(unit_price)}")
                st.write(f"סה\"כ שורה: {format_currency(line_total)}")

            with col3:
                new_quantity = st.number_input(
                    f"כמות עבור {item_id}",
                    min_value=1,
                    step=1,
                    value=quantity,
                    key=f"qty_{item_id}",
                    label_visibility="collapsed",
                )

                if st.button("עדכן כמות", key=f"update_{item_id}", use_container_width=True):
                    try:
                        orders_service.update_quantity(item_id=item_id, quantity=int(new_quantity))
                        st.success(f"הכמות של '{name}' עודכנה.")
                        st.rerun()
                    except APIConnectionError:
                        st.error("לא ניתן להתחבר לשרת כרגע.")
                    except APIClientError as e:
                        st.error(extract_error_message(e))

            with col4:
                if st.button("הסר מהעגלה", key=f"remove_{item_id}", use_container_width=True):
                    try:
                        orders_service.remove_item(item_id=item_id)
                        st.success(f"'{name}' הוסר מהעגלה.")
                        st.rerun()
                    except APIConnectionError:
                        st.error("לא ניתן להתחבר לשרת כרגע.")
                    except APIClientError as e:
                        st.error(extract_error_message(e))

    st.divider()

    shipping_address = st.text_input(
        "כתובת משלוח",
        key="shipping_address",
        placeholder="לדוגמה: הרצל 10, אשדוד",
    )

    if st.button("בצע Checkout", type="primary", use_container_width=True):
        shipping_address_value = (shipping_address or "").strip()

        if not shipping_address_value:
            st.error("יש להזין כתובת משלוח.")
            return

        try:
            result = orders_service.checkout(shipping_address=shipping_address_value)

            order_id = None
            if isinstance(result, dict):
                order_id = result.get("order_id") or result.get("id")

            if order_id:
                st.success(f"ההזמנה נסגרה בהצלחה. מספר הזמנה: {order_id}")
            else:
                st.success("ההזמנה נסגרה בהצלחה.")

            st.session_state.clear_shipping_address = True
            st.rerun()

        except APIConnectionError:
            st.error("לא ניתן להתחבר לשרת כרגע.")
        except APIClientError as e:
            st.error(extract_error_message(e))
       
def render_order_history() -> None:
    st.subheader("היסטוריית הזמנות")

    try:
        orders = orders_service.list_orders()
    except APIConnectionError:
        st.error("לא ניתן להתחבר לשרת כרגע.")
        return
    except APIClientError as e:
        st.error(f"שגיאה בטעינת ההזמנות: {extract_error_message(e)}")
        return

    if not orders:
        st.info("אין עדיין הזמנות למשתמש הזה.")
        return

    for order in orders:
        order_id = order.get("id", "-")
        status = order.get("status", "-")
        total_price = order.get("total_price", order.get("total", 0))
        created_at = order.get("created_at", order.get("order_date", ""))
        shipping_address = order.get("shipping_address", "")
        items = order.get("items", order.get("lines", []))

        title = f"הזמנה #{order_id} | {status} | {format_currency(total_price)}"

        with st.expander(title, expanded=False):
            if created_at:
                st.write(f"**תאריך:** {created_at}")
            if shipping_address:
                st.write(f"**כתובת משלוח:** {shipping_address}")

            if items:
                rows = []
                for item in items:
                    quantity = item.get("quantity", 0)
                    unit_price = item.get("unit_price", 0)
                    line_total = item.get("line_total", quantity * float(unit_price or 0))

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
                st.caption("אין פריטים להצגה בהזמנה זו.")


render_cart()
st.divider()
render_order_history()