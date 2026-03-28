import streamlit as st

from components.protected_page import require_auth
from services.auth_service import auth_service

from features.orders.data import (
    build_orders_list,
    get_temp_order,
    load_orders_data,
)
from features.orders.sections import (
    render_create_new_order_panel,
    render_order_selector,
    render_selected_order,
)
from features.orders.state import (
    ensure_default_selected_order,
    ensure_orders_page_state,
    pop_orders_flash_message,
)

user = require_auth("הזמנות")

ensure_orders_page_state()

if not st.session_state.get("shipping_address"):
    city = (user.get("city") or "").strip()
    country = (user.get("country") or "").strip()
    default_address = ", ".join(part for part in [city, country] if part)
    st.session_state["shipping_address"] = default_address

st.caption(f"שלום {auth_service.get_display_name()}")

flash_message = pop_orders_flash_message()
if flash_message:
    st.success(flash_message)

cart, orders = load_orders_data()
orders_list = build_orders_list(cart, orders)
temp_order = get_temp_order(orders_list)

ensure_default_selected_order(orders_list, temp_order)

if temp_order is not None:
    render_selected_order(orders_list)
    st.divider()
    render_order_selector(orders_list)
    st.divider()
    render_create_new_order_panel(temp_order)

elif orders_list:
    render_create_new_order_panel(temp_order)
    st.divider()
    render_order_selector(orders_list)

else:
    render_create_new_order_panel(temp_order)