import streamlit as st
import pandas as pd
from datetime import datetime

from services.auth_service import auth_service
from services.orders_service import orders_service, OrderLine
from components.auth_box import render_auth_box

st.title("הזמנות")

render_auth_box()

if not auth_service.is_authenticated():
    st.info("כדי לצפות ולהזמין, צריך להתחבר.")
    st.stop()

user = auth_service.get_current_user()
st.caption(f"משתמש מחובר: {user}")


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
    st.warning("אין עדיין הזמנות למשתמש הזה.")
    st.stop()

st.subheader(f"רשימת הזמנות ({len(orders)})")

status_label = {
    "created": "נוצרה",
    "paid": "שולמה",
    "shipped": "נשלחה",
    "delivered": "נמסרה",
    "cancelled": "בוטלה",
}

for order in orders:
    created_dt = datetime.fromtimestamp(order.created_at).strftime("%Y-%m-%d %H:%M")
    status_he = status_label.get(order.status, order.status)

    header_cols = st.columns([2, 2, 2, 2])
    header_cols[0].markdown(f"**הזמנה #{order.order_id}**")
    header_cols[1].write(f"סטטוס: **{status_he}**")
    header_cols[2].write(f"תאריך: {created_dt}")

    total = orders_service.get_order_total(order)
    header_cols[3].write(f"סה״כ: {'N/A' if total is None else f'₪{total:,.2f}'}")

    if order.notes:
        st.caption(f"הערות: {order.notes}")

    df = pd.DataFrame(
        [
            {
                "Item ID": ln.item_id,
                "שם": ln.name,
                "כמות": ln.quantity,
                "מחיר יחידה": None if ln.unit_price is None else float(ln.unit_price),
                "סה״כ שורה": None
                if ln.unit_price is None
                else float(ln.unit_price) * int(ln.quantity),
            }
            for ln in order.lines
        ]
    )

    if not df.empty:
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
        )

    action_cols = st.columns([1, 3])

    with action_cols[0]:
        disabled_cancel = order.status in ("shipped", "delivered", "cancelled")
        if st.button(
            "בטל הזמנה",
            key=f"cancel_{order.order_id}",
            disabled=disabled_cancel,
            use_container_width=True,
        ):
            ok = orders_service.cancel_order(order.order_id)
            if ok:
                st.success("ההזמנה בוטלה.")
                st.rerun()
            else:
                st.error("לא ניתן לבטל את ההזמנה.")

    with action_cols[1]:
        if order.status in ("shipped", "delivered"):
            st.caption("הזמנה שנשלחה/נמסרה לא ניתנת לביטול בשלב הזה.")
        elif order.status == "cancelled":
            st.caption("הזמנה זו כבר בוטלה.")

    st.divider()