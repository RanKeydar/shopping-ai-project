from services.orders_service import orders_service, OrderLine
import streamlit as st

st.subheader("Orders Debug")

if st.button("Create dummy order"):
    o = orders_service.create_order(
        lines=[
            OrderLine(item_id=1, name="Milk", quantity=2, unit_price=6.5),
            OrderLine(item_id=2, name="Bread", quantity=1, unit_price=8.0),
        ],
        notes="Test order",
    )
    st.success(f"Created order #{o.order_id}")
    st.rerun()

orders = orders_service.list_orders()
st.write(f"Orders count: {len(orders)}")

for o in orders:
    st.write(f"#{o.order_id} | {o.status} | {o.created_at}")
    st.json({"lines": [line.__dict__ for line in o.lines], "total": orders_service.get_order_total(o)})

    if st.button(f"Cancel #{o.order_id}", key=f"cancel_{o.order_id}"):
        orders_service.cancel_order(o.order_id)
        st.rerun()
