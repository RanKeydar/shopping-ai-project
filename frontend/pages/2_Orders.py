from __future__ import annotations

import pandas as pd
import streamlit as st

from components.protected_page import require_auth
from services.api_client import APIClientError, APIConnectionError
from services.auth_service import auth_service
from services.items_service import list_items
from services.orders_service import orders_service
import time

user = require_auth("הזמנות")
st.caption(f"שלום {auth_service.get_display_name()}")

st.write("ORDERS PAGE v3")  # ← כאן
st.write("ORDERS PAGE:", time.time())

if "selected_order_id" not in st.session_state:
    st.session_state.selected_order_id = None

if "shipping_address" not in st.session_state:
    city = (user.get("city") or "").strip()
    country = (user.get("country") or "").strip()
    default_address = ", ".join(part for part in [city, country] if part)
    st.session_state.shipping_address = default_address

if "order_item_search_query" not in st.session_state:
    st.session_state.order_item_search_query = ""


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

    if cart and normalize_status(cart) == "TEMP":
        result.append(cart)

    for order in orders:
        if normalize_status(order) == "TEMP":
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
        status = normalize_status(order)
        if status == "TEMP":
            return order
    return None

def search_catalog_items(query: str) -> list[dict]:
    query = (query or "").strip()

    if not query:
        return []

    hebrew_to_english = {
        "חלב": "milk",
        "לחם": "bread",
        "ביצים": "eggs",
        "עגבניות": "tomatoes",
        "עגבניה": "tomatoes",
        "תפוח": "apple",
        "תפוחים": "apple",
        "בננה": "banana",
        "בננות": "banana",
        "שוקולד": "chocolate",
        "שמפו": "shampoo",
        "מרכך": "conditioner",
        "סבון": "soap",
    }

    normalized_query = hebrew_to_english.get(query.lower(), query)

    try:
        items = list_items(limit=50, q=normalized_query)

        if not isinstance(items, list):
            return []

        return items
    except Exception:
        return []

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
                    st.session_state.selected_order_id = order_id
                    shipping_address = (order.get("shipping_address") or "").strip()
                    if shipping_address:
                        st.session_state.shipping_address = shipping_address
                    st.rerun()


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

    search_query = st.text_input(
        "חפש פריט לפי שם או תיאור",
        key="order_item_search_query",
        placeholder="לדוגמה: חלב, לחם, שמפו",
    ).strip()

    if not search_query:
        st.info("הקלד שם מוצר כדי לחפש ולהוסיף אותו להזמנה.")
        return

    items = search_catalog_items(search_query)

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
                        try:
                            orders_service.add_item(item_id=item_id, quantity=int(quantity))
                            st.success(f"'{name}' נוסף להזמנה.")
                            st.session_state.order_item_search_query = ""
                            st.rerun()
                        except APIConnectionError:
                            st.error("לא ניתן להתחבר לשרת כרגע.")
                        except APIClientError as e:
                            st.error(extract_error_message(e))
                        except Exception as e:
                            st.error(f"שגיאה לא צפויה: {e}")

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
                    try:
                        orders_service.update_quantity(item_id=int(item_id), quantity=int(new_quantity))
                        st.success(f"הכמות של '{name}' עודכנה.")
                        st.rerun()
                    except APIConnectionError:
                        st.error("לא ניתן להתחבר לשרת כרגע.")
                    except APIClientError as e:
                        st.error(extract_error_message(e))
                    except Exception as e:
                        st.error(f"שגיאה לא צפויה: {e}")

            with col3:
                if st.button("הסר מההזמנה", key=f"temp_remove_{item_id}", use_container_width=True):
                    try:
                        orders_service.remove_item(item_id=int(item_id))
                        st.success(f"'{name}' הוסר מההזמנה.")
                        st.rerun()
                    except APIConnectionError:
                        st.error("לא ניתן להתחבר לשרת כרגע.")
                    except APIClientError as e:
                        st.error(extract_error_message(e))
                    except Exception as e:
                        st.error(f"שגיאה לא צפויה: {e}")

    st.divider()

    render_item_search_and_add()

    st.divider()

    st.markdown("### פרטי משלוח ורכישה")

    shipping_address = st.text_input(
        "כתובת משלוח",
        key="shipping_address",
        placeholder="לדוגמה: הרצל 10, אשדוד",
    )

    if st.button("בצע רכישה", type="primary", use_container_width=True):
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

            st.session_state.selected_order_id = None
            st.session_state.order_item_search_query = ""
            st.rerun()

        except APIConnectionError:
            st.error("לא ניתן להתחבר לשרת כרגע.")
        except APIClientError as e:
            st.error(extract_error_message(e))
        except Exception as e:
            st.error(f"שגיאה לא צפויה: {e}")


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


cart, orders = load_orders_data()
orders_list = build_orders_list(cart, orders)
temp_order = get_temp_order(orders_list)

if orders_list:
    render_order_selector(orders_list)
    st.divider()
    render_selected_order(orders_list)
    st.divider()
    render_create_new_order_panel(temp_order)
else:
    render_create_new_order_panel(temp_order)