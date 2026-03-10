import streamlit as st
from components.auth_box import render_auth_box


def render_sidebar() -> None:
    with st.sidebar:
        st.title("Shopping AI")
        st.divider()
        st.subheader("Account")
        render_auth_box()