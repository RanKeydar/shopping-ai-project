from __future__ import annotations

import streamlit as st

from services.api_client import APIClientError, APIConnectionError
from services.orders_service import orders_service

from features.orders.data import extract_error_message
from features.orders.state import (
    mark_order_item_search_for_reset,
    mark_user_selected_order_once,
    set_pending_shipping_address,
    set_selected_order_id,
)


def handle_select_order(order_id: int, shipping_address: str | None = None) -> None:
    set_selected_order_id(order_id)
    set_pending_shipping_address(shipping_address)
    mark_user_selected_order_once()
    st.rerun()


def handle_add_item(item_id: int, quantity: int, item_name: str) -> None:
    try:
        orders_service.add_item(item_id=item_id, quantity=quantity)
        st.session_state["reset_order_item_search"] = True
        st.success(f"'{item_name}' נוסף להזמנה.")
        st.rerun()
    except APIConnectionError:
        st.error("לא ניתן להתחבר לשרת כרגע.")
    except APIClientError as e:
        st.error(extract_error_message(e))
    except Exception as e:
        st.error(f"שגיאה לא צפויה: {e}")


def handle_update_quantity(item_id: int, quantity: int, item_name: str) -> None:
    try:
        orders_service.update_quantity(item_id=item_id, quantity=quantity)
        st.success(f"הכמות של '{item_name}' עודכנה.")
        st.rerun()
    except APIConnectionError:
        st.error("לא ניתן להתחבר לשרת כרגע.")
    except APIClientError as e:
        st.error(extract_error_message(e))
    except Exception as e:
        st.error(f"שגיאה לא צפויה: {e}")


def handle_remove_item(item_id: int, item_name: str) -> None:
    try:
        orders_service.remove_item(item_id=item_id)
        st.success(f"'{item_name}' הוסר מההזמנה.")
        st.rerun()
    except APIConnectionError:
        st.error("לא ניתן להתחבר לשרת כרגע.")
    except APIClientError as e:
        st.error(extract_error_message(e))
    except Exception as e:
        st.error(f"שגיאה לא צפויה: {e}")


def handle_checkout(shipping_address: str) -> None:
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

        set_selected_order_id(None)
        mark_order_item_search_for_reset()
        st.rerun()

    except APIConnectionError:
        st.error("לא ניתן להתחבר לשרת כרגע.")
    except APIClientError as e:
        st.error(extract_error_message(e))
    except Exception as e:
        st.error(f"שגיאה לא צפויה: {e}")