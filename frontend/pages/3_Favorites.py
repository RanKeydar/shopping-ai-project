# frontend/pages/3_Favorites.py

import streamlit as st

from components.protected_page import require_auth
from services.favorites_service import favorites_service
from services.auth_service import auth_service

user = require_auth("מועדפים")

st.caption(f"שלום {auth_service.get_display_name()}")

favorites = favorites_service.list_favorites()

if not favorites:
    st.info("אין עדיין פריטים במועדפים.")
    st.stop()

st.subheader(f"מועדפים ({len(favorites)})")

for item in favorites:
    st.write(item)