import streamlit as st
from services.items_service import list_items
from services.api_client import APIClientError, APIConnectionError

st.title("Smoke test: backend connection")

try:
    items = list_items()

    st.success("Connected to backend ✅")
    st.write(f"Fetched {len(items)} items")

    st.subheader("Items preview")
    st.json(items)

except APIConnectionError as e:
    st.error(f"Backend not reachable ❌\n{e}")

except APIClientError as e:
    st.error(
        f"Backend responded with error ❌\n"
        f"{e.detail.status_code}: {e.detail.message}"
    )
