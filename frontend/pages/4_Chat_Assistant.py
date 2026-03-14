from __future__ import annotations

import streamlit as st

from components.sidebar import render_sidebar
from services.auth_service import auth_service
from services.chat_service import chat_service
from services.api_client import APIClientError, APIConnectionError


auth_service.sync_auth_header()
render_sidebar()

st.title("Chat Assistant")

if auth_service.is_authenticated():
    st.caption(f"שלום {auth_service.get_display_name()}")
else:
    st.caption("אפשר להשתמש בעוזר גם בלי להתחבר.")

CHAT_HISTORY_KEY = "chat_history"
CHAT_REMAINING_KEY = "chat_remaining_prompts"

if CHAT_HISTORY_KEY not in st.session_state:
    st.session_state[CHAT_HISTORY_KEY] = []

if CHAT_REMAINING_KEY not in st.session_state:
    st.session_state[CHAT_REMAINING_KEY] = 5

st.subheader("עוזר קניות AI")
st.caption(f"נותרו {st.session_state[CHAT_REMAINING_KEY]} פרומפטים בסשן הזה")

for message in st.session_state[CHAT_HISTORY_KEY]:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if st.session_state[CHAT_REMAINING_KEY] <= 0:
    st.warning("ניצלת את כל 5 הפרומפטים הזמינים כרגע.")
    st.stop()

prompt = st.chat_input("שאל על המוצרים באתר...")

if prompt:
    st.session_state[CHAT_HISTORY_KEY].append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("user"):
        st.write(prompt)

    try:
        with st.spinner("העוזר חושב..."):
            response = chat_service.ask(prompt)

        answer = "No response received."
        remaining_prompts = st.session_state[CHAT_REMAINING_KEY]

        if isinstance(response, dict):
            answer = response.get("answer", answer)
            remaining_prompts = response.get(
                "remaining_prompts",
                remaining_prompts,
            )

        st.session_state[CHAT_REMAINING_KEY] = max(0, int(remaining_prompts))

        st.session_state[CHAT_HISTORY_KEY].append(
            {"role": "assistant", "content": answer}
        )

        with st.chat_message("assistant"):
            st.write(answer)

        st.rerun()

    except APIConnectionError as e:
        st.error(f"לא ניתן להתחבר לשרת כרגע: {e}")
    except APIClientError as e:
        if e.detail.status_code == 429:
            st.session_state[CHAT_REMAINING_KEY] = 0
        st.error(f"העוזר אינו זמין כרגע: {e.detail.message}")
    except Exception as e:
        st.error(f"שגיאה לא צפויה: {e}")