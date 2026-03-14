import streamlit as st

from components.protected_page import require_auth
from components.items_grid import render_items_grid
from services.favorites_service import favorites_service
from services.auth_service import auth_service
from services.api_client import APIClientError, APIConnectionError

user = require_auth("מועדפים")

st.caption(f"שלום {auth_service.get_display_name()}")

try:
    favorites = favorites_service.list_favorites()
except APIConnectionError:
    st.error("לא ניתן להתחבר לשרת כרגע.")
    st.stop()
except APIClientError as e:
    st.error(f"שגיאה בטעינת המועדפים: {e}")
    st.stop()

if not favorites:
    st.info("אין עדיין פריטים במועדפים.")
    st.stop()

st.subheader(f"מועדפים ({len(favorites)})")
render_items_grid(
    favorites,
    columns=3,
    show_count=False,
    enable_add_to_cart=True,
    enable_favorites=True,
)