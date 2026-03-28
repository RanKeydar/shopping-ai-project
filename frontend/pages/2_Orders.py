import streamlit as st

from components.protected_page import require_auth
from features.orders.page import render_orders_page
from features.orders.state import ensure_orders_page_state

user = require_auth("הזמנות")

ensure_orders_page_state()

render_orders_page(user)