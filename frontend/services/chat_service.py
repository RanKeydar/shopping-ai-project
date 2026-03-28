from __future__ import annotations

from services.api_client import api as api_client

class ChatService:
    def ask(self, prompt: str) -> dict:
        return api_client.post(
            "/chat-assistant",
            json={"prompt": prompt},
        )

    def get_remaining_prompts(self) -> int:
        response = api_client.get("/chat-assistant/remaining")
        return int(response["remaining_prompts"])


chat_service = ChatService()