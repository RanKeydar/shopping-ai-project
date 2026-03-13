from __future__ import annotations

from typing import Any

import streamlit as st

from services.api_client import APIClientError, APIConnectionError, api


TOKEN_KEY = "auth_token"
USER_KEY = "auth_user"


class AuthService:
    def login(self, username: str, password: str) -> tuple[bool, str]:
        try:
            response = api.post(
                "/auth/login",
                data={
                    "username": username,
                    "password": password,
                },
            )

            access_token = response.get("access_token")
            if not access_token:
                return False, "לא התקבל access token מהשרת"

            api.set_auth_token(access_token)
            user_response = api.get("/auth/me")

            st.session_state[TOKEN_KEY] = access_token
            st.session_state[USER_KEY] = user_response

            return True, "התחברת בהצלחה"

        except APIClientError as e:
            return False, e.detail.message
        except APIConnectionError:
            return False, "שגיאת חיבור לשרת"

    def register(
        self,
        *,
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
        country: str,
        city: str,
        username: str,
        password: str,
    ) -> tuple[bool, str]:
        try:
            api.post(
                "/auth/register",
                data={
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": email,
                    "phone": phone,
                    "country": country,
                    "city": city,
                    "username": username,
                    "password": password,
                },
            )

            return True, "החשבון נוצר בהצלחה"

        except APIClientError as e:
            return False, e.detail.message
        except APIConnectionError:
            return False, "שגיאת חיבור לשרת"

    def logout(self) -> None:
        st.session_state.pop(TOKEN_KEY, None)
        st.session_state.pop(USER_KEY, None)
        api.set_auth_token(None)

    def is_authenticated(self) -> bool:
        return bool(st.session_state.get(TOKEN_KEY))

    def get_token(self) -> str | None:
        return st.session_state.get(TOKEN_KEY)

    def get_auth_headers(self) -> dict[str, str]:
        token = self.get_token()
        if not token:
            return {}
        return {"Authorization": f"Bearer {token}"}
    
    def sync_auth_header(self) -> None:
        token = self.get_token()
        api.set_auth_token(token)
 
    def get_current_user(self) -> dict[str, Any] | None:
        return st.session_state.get(USER_KEY)
    
    def get_display_name(self) -> str:
        user = self.get_current_user() or {}
        return (
            user.get("first_name")
            or user.get("username")
            or user.get("email")
            or "משתמש"
        )

    def require_login(self) -> dict[str, Any]:
        from components.auth_box import render_auth_box
        import streamlit as st

        if not self.is_authenticated():
            st.warning("כדי להמשיך צריך להתחבר.")
            render_auth_box()
            st.stop()

        return self.get_current_user() or {}

    def refresh_current_user(self) -> tuple[bool, str]:
        token = self.get_token()
        if not token:
            return False, "אין משתמש מחובר"

        try:
            api.set_auth_token(token)
            user_response = api.get("/auth/me")
            st.session_state[USER_KEY] = user_response
            return True, "פרטי המשתמש עודכנו"

        except APIClientError as e:
            self.logout()
            return False, e.detail.message
        except APIConnectionError:
            return False, "שגיאת חיבור לשרת"

    def delete_account(self) -> tuple[bool, str]:
        token = self.get_token()
        if not token:
            return False, "אין משתמש מחובר"

        try:
            api.set_auth_token(token)
            api.delete("/auth/me")
            self.logout()
            return True, "החשבון נמחק בהצלחה"

        except APIClientError as e:
            return False, e.detail.message
        except APIConnectionError:
            return False, "שגיאת חיבור לשרת"


auth_service = AuthService()