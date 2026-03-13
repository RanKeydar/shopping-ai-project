# frontend/components/auth_box.py

from __future__ import annotations

import streamlit as st

from services.auth_service import auth_service


def render_auth_box() -> None:
    st.subheader("חשבון משתמש")

    if auth_service.is_authenticated():
        user = auth_service.get_current_user() or {}

        display_name = (
            user.get("first_name")
            or user.get("username")
            or user.get("email")
            or "משתמש"
        )

        st.success(f"שלום {display_name}")

        if st.button("התנתק", use_container_width=True):
            auth_service.logout()
            st.rerun()

        return

    login_tab, register_tab = st.tabs(["התחברות", "הרשמה"])

    with login_tab:
        with st.form("login_form", clear_on_submit=False):
            st.markdown("### התחברות")

            username = st.text_input("שם משתמש")
            password = st.text_input("סיסמה", type="password")

            submitted = st.form_submit_button(
                "התחבר",
                use_container_width=True,
            )

            if submitted:
                if not username or not password:
                    st.error("יש למלא שם משתמש וסיסמה")
                else:
                    success, message = auth_service.login(
                        username=username,
                        password=password,
                    )

                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

    with register_tab:
        with st.form("register_form", clear_on_submit=False):
            st.markdown("### הרשמה")

            first_name = st.text_input("שם פרטי", key="register_first_name")
            last_name = st.text_input("שם משפחה", key="register_last_name")
            email = st.text_input("אימייל", key="register_email")
            phone = st.text_input("טלפון", key="register_phone")
            country = st.text_input("מדינה", key="register_country")
            city = st.text_input("עיר", key="register_city")
            username = st.text_input("שם משתמש", key="register_username")
            password = st.text_input(
                "סיסמה",
                type="password",
                key="register_password",
            )

            submitted = st.form_submit_button(
                "הירשם",
                use_container_width=True,
            )

            if submitted:
                required_fields = {
                    "שם פרטי": first_name,
                    "שם משפחה": last_name,
                    "אימייל": email,
                    "טלפון": phone,
                    "מדינה": country,
                    "עיר": city,
                    "שם משתמש": username,
                    "סיסמה": password,
                }

                missing_fields = [
                    field_name
                    for field_name, value in required_fields.items()
                    if not value
                ]

                if missing_fields:
                    st.error(f"יש למלא את כל השדות: {', '.join(missing_fields)}")
                else:
                    success, message = auth_service.register(
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        phone=phone,
                        country=country,
                        city=city,
                        username=username,
                        password=password,
                    )

                    if success:
                        st.success(message)
                    else:
                        st.error(message)