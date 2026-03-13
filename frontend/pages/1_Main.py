import streamlit as st

from components.items_grid import render_items_grid
from services.items_service import list_items
from services.api_client import APIClientError, APIConnectionError
from components.sidebar import render_sidebar
from services.auth_service import auth_service

auth_service.sync_auth_header()
render_sidebar()    

if "main_search_query" not in st.session_state:
    st.session_state.main_search_query = ""

if "main_use_price" not in st.session_state:
    st.session_state.main_use_price = False

if "main_price_op" not in st.session_state:
    st.session_state.main_price_op = "<="

if "main_price" not in st.session_state:
    st.session_state.main_price = 10.0

if "main_use_stock" not in st.session_state:
    st.session_state.main_use_stock = False

if "main_stock_op" not in st.session_state:
    st.session_state.main_stock_op = "="

if "main_stock" not in st.session_state:
    st.session_state.main_stock = 0


def clear_main_filters() -> None:
    st.session_state.main_search_query = ""
    st.session_state.main_use_price = False
    st.session_state.main_price_op = "<="
    st.session_state.main_price = 10.0
    st.session_state.main_use_stock = False
    st.session_state.main_stock_op = "="
    st.session_state.main_stock = 0


st.title("Shopping AI")
st.subheader("Available items")

search_query = st.text_input(
    "Search by item name",
    placeholder="Examples: milk | sun table | sun, table",
    key="main_search_query",
)

col1, col2 = st.columns(2)

with col1:
    use_price = st.checkbox("Filter by price", key="main_use_price")
    price_op = st.selectbox(
        "Price operator",
        ["<", "<=", "=", ">=", ">"],
        key="main_price_op",
    )
    price = st.number_input(
        "Price in USD",
        min_value=0.0,
        step=1.0,
        key="main_price",
    )

with col2:
    use_stock = st.checkbox("Filter by stock", key="main_use_stock")
    stock_op = st.selectbox(
        "Stock operator",
        ["<", "<=", "=", ">=", ">"],
        key="main_stock_op",
    )
    stock = st.number_input(
        "Amount in stock",
        min_value=0,
        step=1,
        key="main_stock",
    )

action_cols = st.columns([1, 1, 4])

with action_cols[0]:
    st.button("Search", use_container_width=True)

with action_cols[1]:
    st.button("Clear", on_click=clear_main_filters, use_container_width=True)

try:
    with st.spinner("Loading items..."):
        items = list_items(
            q=search_query,
            price_op=price_op if use_price else None,
            price=price if use_price else None,
            stock_op=stock_op if use_stock else None,
            stock=stock if use_stock else None,
        )

    if search_query.strip() or use_price or use_stock:
        st.caption(f"Search returned {len(items)} item(s)")
    else:
        st.caption(f"Showing all available items ({len(items)})")
   
    render_items_grid(items, columns=3, show_count=False)

except APIConnectionError:
    st.error("Could not connect to the server.")
except APIClientError as e:
    st.error(f"Server error: {e}")