import streamlit as st

from components.items_grid import render_items_grid
from services.items_service import list_items
from services.api_client import APIClientError, APIConnectionError
from components.sidebar import render_sidebar
from services.auth_service import auth_service
from services.orders_service import orders_service

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

flash_message = st.session_state.pop("main_flash_message", None)

if flash_message:
    with st.container(border=True):
        st.success(flash_message)

        action_col1, action_col2 = st.columns([1, 4])
        with action_col1:
            st.page_link("pages/2_Orders.py", label="לעגלה", icon="🛒")
        with action_col2:
            st.caption("הפריט נוסף בהצלחה. אפשר להמשיך לקנות או לעבור לעגלת ההזמנה.")

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


def handle_add_to_order(item: dict, quantity: int) -> None:
    if not auth_service.is_authenticated():
        st.warning("צריך להתחבר כדי להוסיף פריטים לעגלה.")
        return

    item_id = int(item.get("id"))
    name = item.get("name", f"פריט {item_id}")

    try:
        orders_service.add_to_order(item_id=item_id, quantity=quantity)

        if quantity == 1:
            st.session_state["main_flash_message"] = f"'{name}' נוסף לעגלה."
        else:
            st.session_state["main_flash_message"] = f"נוספו {quantity} יחידות של '{name}' לעגלה."

        st.rerun()

    except APIConnectionError:
        st.error("לא ניתן להתחבר לשרת כרגע.")
    except APIClientError as e:
        st.error(extract_error_message(e))
    except Exception as e:
        st.error(f"שגיאה לא צפויה: {e}")

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

    render_items_grid(
        items,
        columns=3,
        show_count=False,
        enable_add_to_cart=True,
        enable_favorites=True,
        on_add_to_order=handle_add_to_order,
    )

except APIConnectionError:
    st.error("Could not connect to the server.")
except APIClientError as e:
    st.error(f"Server error: {e}")