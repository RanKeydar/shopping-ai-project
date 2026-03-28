# frontend/features/orders/state.py

from __future__ import annotations

import streamlit as st


SELECTED_ORDER_ID_KEY = "selected_order_id"
ORDER_ITEM_SEARCH_QUERY_KEY = "order_item_search_query"
SHIPPING_ADDRESS_KEY = "shipping_address"
PENDING_SHIPPING_ADDRESS_KEY = "pending_shipping_address"
RESET_ORDER_ITEM_SEARCH_KEY = "reset_order_item_search"
ORDERS_FLASH_MESSAGE_KEY = "orders_flash_message"
USER_SELECTED_ORDER_ONCE_KEY = "user_selected_order_once"


def ensure_orders_page_state() -> None:
    st.session_state.setdefault(SELECTED_ORDER_ID_KEY, None)
    st.session_state.setdefault(ORDER_ITEM_SEARCH_QUERY_KEY, "")
    st.session_state.setdefault(SHIPPING_ADDRESS_KEY, "")
    st.session_state.setdefault(PENDING_SHIPPING_ADDRESS_KEY, None)
    st.session_state.setdefault(RESET_ORDER_ITEM_SEARCH_KEY, False)
    st.session_state.setdefault(ORDERS_FLASH_MESSAGE_KEY, None)
    st.session_state.setdefault(USER_SELECTED_ORDER_ONCE_KEY, False)

def mark_user_selected_order_once() -> None:
    st.session_state[USER_SELECTED_ORDER_ONCE_KEY] = True


def consume_user_selected_order_once() -> bool:
    was_selected = bool(st.session_state.get(USER_SELECTED_ORDER_ONCE_KEY))
    st.session_state[USER_SELECTED_ORDER_ONCE_KEY] = False
    return was_selected

def get_selected_order_id() -> int | None:
    return st.session_state.get(SELECTED_ORDER_ID_KEY)


def set_selected_order_id(order_id: int | None) -> None:
    st.session_state[SELECTED_ORDER_ID_KEY] = order_id


def ensure_default_selected_order(
    orders_list: list[dict],
    temp_order: dict | None,
) -> None:
    current_selected_id = get_selected_order_id()
    selected_order_exists = any(
        order.get("id") == current_selected_id for order in orders_list
    )

    user_selected_order_once = consume_user_selected_order_once()

    # אם המשתמש בדיוק לחץ "פתח" על הזמנה מהרשימה,
    # נשמור את הבחירה שלו ל-rerun הנוכחי בלבד.
    if user_selected_order_once and selected_order_exists:
        return

    # בכניסה רגילה לעמוד - תמיד להעדיף TEMP אם קיימת.
    if temp_order is not None:
        set_selected_order_id(temp_order.get("id"))
        shipping_address = (temp_order.get("shipping_address") or "").strip()
        st.session_state[SHIPPING_ADDRESS_KEY] = shipping_address
        return

    # אם אין TEMP, נשמור selection תקף קיים.
    if selected_order_exists:
        return

    # fallback
    if orders_list:
        set_selected_order_id(orders_list[0].get("id"))
    else:
        set_selected_order_id(None)
        
def sync_pending_shipping_address() -> None:
    """
    חייב לרוץ לפני ה-text_input עם key='shipping_address'.
    """
    pending_shipping_address = st.session_state.get(PENDING_SHIPPING_ADDRESS_KEY)
    if pending_shipping_address is not None:
        st.session_state[SHIPPING_ADDRESS_KEY] = pending_shipping_address
        st.session_state[PENDING_SHIPPING_ADDRESS_KEY] = None


def set_pending_shipping_address(value: str | None) -> None:
    st.session_state[PENDING_SHIPPING_ADDRESS_KEY] = (value or "").strip()


def mark_order_item_search_for_reset() -> None:
    st.session_state[RESET_ORDER_ITEM_SEARCH_KEY] = True


def should_reset_order_item_search() -> bool:
    return bool(st.session_state.get(RESET_ORDER_ITEM_SEARCH_KEY))


def clear_order_item_search_reset_flag() -> None:
    st.session_state[RESET_ORDER_ITEM_SEARCH_KEY] = False


def set_orders_flash_message(message: str | None) -> None:
    st.session_state[ORDERS_FLASH_MESSAGE_KEY] = message


def pop_orders_flash_message() -> str | None:
    message = st.session_state.get(ORDERS_FLASH_MESSAGE_KEY)
    st.session_state[ORDERS_FLASH_MESSAGE_KEY] = None
    return message