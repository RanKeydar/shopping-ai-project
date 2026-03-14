# frontend/components/auth_box.py

from __future__ import annotations

import streamlit as st

from services.auth_service import auth_service


def render_auth_box(key_prefix: str = "auth_box") -> None:
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

        if st.button("התנתק", use_container_width=True, key=f"{key_prefix}_logout"):
            auth_service.logout()
            st.rerun()

        return

    login_tab, register_tab = st.tabs(["התחברות", "הרשמה"])

    with login_tab:
        with st.form(f"{key_prefix}_login_form", clear_on_submit=False):
            st.markdown("### התחברות")

            username = st.text_input("שם משתמש", key=f"{key_prefix}_login_username")
            password = st.text_input(
                "סיסמה",
                type="password",
                key=f"{key_prefix}_login_password",
            )

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
        with st.form(f"{key_prefix}_register_form", clear_on_submit=False):
            st.markdown("### הרשמה")

            first_name = st.text_input("שם פרטי", key=f"{key_prefix}_register_first_name")
            last_name = st.text_input("שם משפחה", key=f"{key_prefix}_register_last_name")
            email = st.text_input("אימייל", key=f"{key_prefix}_register_email")
            phone = st.text_input("טלפון", key=f"{key_prefix}_register_phone")
            country = st.text_input("מדינה", key=f"{key_prefix}_register_country")
            city = st.text_input("עיר", key=f"{key_prefix}_register_city")
            username = st.text_input("שם משתמש", key=f"{key_prefix}_register_username")
            password = st.text_input(
                "סיסמה",
                type="password",
                key=f"{key_prefix}_register_password",
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