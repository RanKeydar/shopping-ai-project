from __future__ import annotations

from typing import Any

import streamlit as st

from components.sidebar import render_sidebar
from services.auth_service import auth_service


def require_auth(page_title: str) -> dict[str, Any]:
    auth_service.sync_auth_header()

    render_sidebar()
    st.title(page_title)

    if not auth_service.is_authenticated():
        st.warning("כדי לצפות בעמוד הזה צריך להתחבר דרך הסרגל הצדדי.")
        st.stop()

    return auth_service.get_current_user() or {}