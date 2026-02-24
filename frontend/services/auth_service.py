# frontend/services/auth_service.py

import streamlit as st
from typing import Optional


TOKEN_KEY = "auth_token"
USER_KEY = "auth_user"


class AuthService:
    """
    שלב 1:
    - התחברות מזויפת (stub)
    - שמירת טוקן ב-session_state
    - מוכן לחיבור עתידי ל-backend
    """

    # -------------------------
    # פעולות ציבוריות
    # -------------------------

    def login(self, username: str, password: str) -> bool:
        """
        בגרסה הזו:
        כל שם משתמש + סיסמה לא ריקים מתקבלים.
        """

        if not username or not password:
            return False

        # טוקן מזויף
        token = f"fake-token-for-{username}"

        st.session_state[TOKEN_KEY] = token
        st.session_state[USER_KEY] = username

        return True

    def logout(self) -> None:
        st.session_state.pop(TOKEN_KEY, None)
        st.session_state.pop(USER_KEY, None)

    def get_token(self) -> Optional[str]:
        return st.session_state.get(TOKEN_KEY)

    def get_current_user(self) -> Optional[str]:
        return st.session_state.get(USER_KEY)

    def is_authenticated(self) -> bool:
        return TOKEN_KEY in st.session_state


# אובייקט גלובלי לשימוש בכל האפליקציה
auth_service = AuthService()
