from __future__ import annotations

from typing import Any

from services.api_client import api


class ChatService:
    def ask(self, prompt: str) -> dict[str, Any] | None:
        return api.post(
            "/chat-assistant",
            data={"prompt": prompt},
            timeout=(5, 45),  
        )

chat_service = ChatService()