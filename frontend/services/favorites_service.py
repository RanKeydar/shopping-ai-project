from __future__ import annotations

from typing import Any

import streamlit as st

from services.api_client import api


FAVORITES_IDS_CACHE_KEY = "favorites_ids_cache"
FAVORITES_LIST_CACHE_KEY = "favorites_list_cache"


class FavoritesService:
    def _set_cache_from_items(self, favorites: list[dict[str, Any]]) -> None:
        st.session_state[FAVORITES_LIST_CACHE_KEY] = favorites
        st.session_state[FAVORITES_IDS_CACHE_KEY] = {
            int(item["id"])
            for item in favorites
            if isinstance(item, dict) and item.get("id") is not None
        }

    def invalidate_cache(self) -> None:
        st.session_state.pop(FAVORITES_IDS_CACHE_KEY, None)
        st.session_state.pop(FAVORITES_LIST_CACHE_KEY, None)

    def list_favorites(self, force_refresh: bool = False) -> list[dict[str, Any]]:
        if not force_refresh and FAVORITES_LIST_CACHE_KEY in st.session_state:
            cached = st.session_state[FAVORITES_LIST_CACHE_KEY]
            if isinstance(cached, list):
                return cached

        data = api.get("/favorites")

        if data is None:
            favorites: list[dict[str, Any]] = []
        elif isinstance(data, list):
            favorites = data
        else:
            favorites = []

        self._set_cache_from_items(favorites)
        return favorites

    def get_favorites_ids(self, force_refresh: bool = False) -> set[int]:
        if not force_refresh and FAVORITES_IDS_CACHE_KEY in st.session_state:
            cached = st.session_state[FAVORITES_IDS_CACHE_KEY]
            if isinstance(cached, set):
                return set(cached)

        favorites = self.list_favorites(force_refresh=force_refresh)
        ids = {
            int(item["id"])
            for item in favorites
            if isinstance(item, dict) and item.get("id") is not None
        }

        st.session_state[FAVORITES_IDS_CACHE_KEY] = ids
        return set(ids)

    def is_favorite(self, item_id: int) -> bool:
        return int(item_id) in self.get_favorites_ids()

    def add(self, item_id: int) -> dict[str, Any] | None:
        item_id = int(item_id)
        result = api.post(f"/favorites/{item_id}")

        ids = self.get_favorites_ids()
        ids.add(item_id)
        st.session_state[FAVORITES_IDS_CACHE_KEY] = ids

        if FAVORITES_LIST_CACHE_KEY in st.session_state:
            self.invalidate_cache()

        return result

    def remove(self, item_id: int) -> dict[str, Any] | None:
        item_id = int(item_id)
        result = api.delete(f"/favorites/{item_id}")

        ids = self.get_favorites_ids()
        ids.discard(item_id)
        st.session_state[FAVORITES_IDS_CACHE_KEY] = ids

        if FAVORITES_LIST_CACHE_KEY in st.session_state:
            cached_list = st.session_state[FAVORITES_LIST_CACHE_KEY]
            if isinstance(cached_list, list):
                st.session_state[FAVORITES_LIST_CACHE_KEY] = [
                    item
                    for item in cached_list
                    if int(item.get("id", -1)) != item_id
                ]

        return result

    def toggle(self, item_id: int) -> bool:
        item_id = int(item_id)

        if self.is_favorite(item_id):
            self.remove(item_id)
            return False

        self.add(item_id)
        return True

    def count(self) -> int:
        return len(self.get_favorites_ids())


favorites_service = FavoritesService()