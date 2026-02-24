import streamlit as st
from typing import Set, Dict, Optional

from services.auth_service import auth_service


FAVORITES_KEY = "favorites_by_user"


class FavoritesService:
    """
    שלב 1 (לוקאלי):
    - ניהול מועדפים בזיכרון של session_state
    - מועדפים לפי משתמש
    - מוכן לחיבור backend בהמשך (sync)
    """

    # -------------------------
    # helpers (פרטיים)
    # -------------------------

    def _get_store(self) -> Dict[str, Set[int]]:
        """
        מחזיר dict של:
        { username: set(item_id, ...) }
        """
        if FAVORITES_KEY not in st.session_state:
            st.session_state[FAVORITES_KEY] = {}
        return st.session_state[FAVORITES_KEY]

    def _current_user(self) -> Optional[str]:
        return auth_service.get_current_user()

    def _get_user_set(self, username: str) -> Set[int]:
        store = self._get_store()
        if username not in store:
            store[username] = set()
        return store[username]

    # -------------------------
    # API ציבורי (מוכן ל-UI)
    # -------------------------

    def get_favorites_ids(self) -> Set[int]:
        """
        מחזיר סט של item_id למשתמש הנוכחי.
        אם לא מחובר -> סט ריק.
        """
        username = self._current_user()
        if not username:
            return set()
        return set(self._get_user_set(username))  # העתק כדי לא לחשוף reference

    def is_favorite(self, item_id: int) -> bool:
        username = self._current_user()
        if not username:
            return False
        return item_id in self._get_user_set(username)

    def add(self, item_id: int) -> None:
        username = self._current_user()
        if not username:
            return
        self._get_user_set(username).add(int(item_id))

    def remove(self, item_id: int) -> None:
        username = self._current_user()
        if not username:
            return
        self._get_user_set(username).discard(int(item_id))  # discard לא זורק שגיאה אם לא קיים

    def toggle(self, item_id: int) -> bool:
        """
        מחליף מצב מועדף.
        מחזיר True אם אחרי הפעולה הפריט במועדפים, אחרת False.
        """
        item_id = int(item_id)
        if self.is_favorite(item_id):
            self.remove(item_id)
            return False
        self.add(item_id)
        return True

    def count(self) -> int:
        return len(self.get_favorites_ids())

    def clear(self) -> None:
        """
        מוחק את המועדפים של המשתמש הנוכחי בלבד.
        """
        username = self._current_user()
        if not username:
            return
        self._get_user_set(username).clear()


favorites_service = FavoritesService()
