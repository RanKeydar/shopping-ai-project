import streamlit as st
from state.session import init_session
from components.sidebar import render_sidebar

st.set_page_config(page_title="Shopping AI", layout="wide")

init_session()

render_sidebar()

st.title("Shopping AI Project")
st.caption("Use the sidebar to navigate pages.")