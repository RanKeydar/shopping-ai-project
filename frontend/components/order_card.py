from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st


STATUS_LABEL = {
    "created": "נוצרה",
    "paid": "שולמה",
    "shipped": "נשלחה",
    "delivered": "נמסרה",
    "cancelled": "בוטלה",
}


def render_order_card(order, orders_service) -> None:
    created_dt = datetime.fromtimestamp(order.created_at).strftime("%Y-%m-%d %H:%M")
    status_he = STATUS_LABEL.get(order.status, order.status)

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