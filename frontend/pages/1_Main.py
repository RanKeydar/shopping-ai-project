import streamlit as st
from services.items_service import list_items
from services.auth_service import auth_service
from components.auth_box import render_auth_box
from services.api_client import APIClientError, APIConnectionError

st.title("Items search & filters test")

st.subheader("Search and filters")

q = st.text_input("Search query", placeholder="e.g. milk")

col1, col2 = st.columns(2)

with col1:
    use_price = st.checkbox("Enable price filter")
    price_op = st.selectbox("Price operator", ["<", "<=", "=", ">=", ">"], index=1)
    price = st.number_input("Price", min_value=0.0, value=10.0, step=1.0)

with col2:
    use_stock = st.checkbox("Enable stock filter")
    stock_op = st.selectbox("Stock operator", ["<", "<=", "=", ">=", ">"], index=2)
    stock = st.number_input("Stock", min_value=0, value=0, step=1)

limit = st.number_input("Limit", min_value=1, value=50, step=1)
offset = st.number_input("Offset", min_value=0, value=0, step=1)

params_preview = {
    "limit": limit,
    "offset": offset,
    "q": q.strip() if q else None,
    "price_op": price_op if use_price else None,
    "price": price if use_price else None,
    "stock_op": stock_op if use_stock else None,
    "stock": stock if use_stock else None,
}

st.caption(f"DEBUG params: {params_preview}")

if st.button("Run query", use_container_width=True):
    try:
        items = list_items(
            limit=limit,
            offset=offset,
            q=q,
            price_op=price_op if use_price else None,
            price=price if use_price else None,
            stock_op=stock_op if use_stock else None,
            stock=stock if use_stock else None,
        )

        st.success("Connected to backend ✅")
        st.write(f"Fetched {len(items)} items")

        st.subheader("Items preview")
        st.json(items)

    except APIConnectionError as e:
        st.error(f"Backend not reachable ❌\n{e}")

    except APIClientError as e:
        st.error(
            f"Backend responded with error ❌\n"
            f"{e.detail.status_code}: {e.detail.message}"
        )