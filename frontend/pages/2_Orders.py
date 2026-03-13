# frontend/pages/2_Orders.py

import streamlit as st

from components.order_card import render_order_card
from components.protected_page import require_auth
from services.orders_service import orders_service, OrderLine
from services.auth_service import auth_service


user = require_auth("הזמנות")

st.caption(f"שלום {auth_service.get_display_name()}")

with st.expander("פעולות מהירות (שלב 1)", expanded=False):
    st.write("בשלב 1 אין עדיין Checkout אמיתי מהעגלה, אז יש כפתור ליצירת הזמנה לדוגמה.")
    if st.button("צור הזמנה לדוגמה", use_container_width=True):
        orders_service.create_order(
            lines=[
                OrderLine(item_id=1, name="Milk", quantity=2, unit_price=6.5),
                OrderLine(item_id=2, name="Bread", quantity=1, unit_price=8.0),
            ],
            notes="Demo order",
        )
        st.success("הזמנה נוצרה ✅")
        st.rerun()

st.divider()

orders = orders_service.list_orders()

if not orders:
    st.info("אין עדיין הזמנות למשתמש הזה.")
    st.stop()

st.subheader(f"רשימת הזמנות ({len(orders)})")

for order in orders:
    render_order_card(order, orders_service)