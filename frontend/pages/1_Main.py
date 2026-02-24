import streamlit as st
from services.items_service import list_items
from services.api_client import APIClientError, APIConnectionError
from services.auth_service import auth_service


st.title("Smoke test: backend connection")

st.subheader("Auth Debug")

if auth_service.is_authenticated():
    st.success(f"מחובר כ: {auth_service.get_current_user()}")

    if st.button("Logout"):
        auth_service.logout()
        st.rerun()
else:
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if auth_service.login(username, password):
            st.rerun()
        else:
            st.error("Login failed")


try:
    data = list_items()
    st.success("Connected to backend ✅")
    st.write(data)
except APIConnectionError as e:
    st.error(f"Backend not reachable ❌\n{e}")
except APIClientError as e:
    st.error(f"Backend responded with error ❌\n{e.detail.status_code}: {e.detail.message}")

st.title("Items")

try:
    items = list_items()
    st.write(items)
except APIConnectionError:
    st.error("Backend לא זמין")
except APIClientError as e:
    st.error(f"{e.detail.status_code}: {e.detail.message}")
