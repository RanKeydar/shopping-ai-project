import streamlit as st
from state.session import init_session

st.set_page_config(page_title="Shopping AI", layout="wide")
init_session()

st.title("Shopping AI Project")
st.caption("Use the sidebar to navigate pages.")
