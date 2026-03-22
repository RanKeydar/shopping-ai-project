from __future__ import annotations

from openai import OpenAI


def generate_chat_response(
    client: OpenAI,
    prompt: str,
    model: str,
) -> str:
    completion = client.responses.create(
        model=model,
        input=prompt,
    )

    return (completion.output_text or "").strip()