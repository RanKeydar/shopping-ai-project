import streamlit as st
from services.auth_service import auth_service


def render_auth_box() -> None:
    if auth_service.is_authenticated():
        st.write(f"שלום {auth_service.get_current_user()}")

        if st.button("התנתק"):
            auth_service.logout()
            st.rerun()

    else:
        username = st.text_input("שם משתמש")
        password = st.text_input("סיסמה", type="password")

        if st.button("התחבר"):
            success = auth_service.login(username, password)

            if success:
                st.rerun()
            else:
                st.error("פרטי התחברות לא תקינים")