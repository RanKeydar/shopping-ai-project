import streamlit as st

DEFAULT_API_BASE = "http://127.0.0.1:8000"

def init_session() -> None:
    if "api_base" not in st.session_state:
        st.session_state.api_base = DEFAULT_API_BASE
    if "access_token" not in st.session_state:
        st.session_state.access_token = None
    if "user" not in st.session_state:
        st.session_state.user = None
