import streamlit as st
from typing import Optional

from services.api_client import api, APIClientError, APIConnectionError


TOKEN_KEY = "auth_token"
USER_KEY = "auth_user"


class AuthService:
   
    def login(self, username: str, password: str) -> bool:
        try:
            result = api.post(
                "/auth/login",
                data={
                    "username": username,
                    "password": password,
                },
            )

            token = result["access_token"]

            st.session_state[TOKEN_KEY] = token
            st.session_state[USER_KEY] = username

            api.set_auth_token(token)
            return True

        except (APIClientError, APIConnectionError):
            return False

    def logout(self) -> None:
        st.session_state.pop(TOKEN_KEY, None)
        st.session_state.pop(USER_KEY, None)
        api.set_auth_token(None)

    def is_authenticated(self) -> bool:
        return TOKEN_KEY in st.session_state and bool(st.session_state[TOKEN_KEY])

    def get_token(self) -> Optional[str]:
        return st.session_state.get(TOKEN_KEY)

    def get_current_user(self) -> Optional[str]:
        return st.session_state.get(USER_KEY)

    def restore_session(self) -> None:
        token = st.session_state.get(TOKEN_KEY)
        if token:
            api.set_auth_token(token)


auth_service = AuthService()
auth_service.restore_session()