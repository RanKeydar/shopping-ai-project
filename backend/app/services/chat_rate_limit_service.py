from __future__ import annotations

import os

from openai import OpenAI
from sqlalchemy.orm import Session

from app.services.chat.generation import generate_chat_response
from app.services.chat.intent import resolve_intent
from app.services.chat.prompts import (
    build_recommendation_prompt,
    build_semantic_answer_prompt,
)
from app.services.chat.retrieval import (
    items_to_dicts,
    list_items_for_ai,
    search_items_by_keywords,
)

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    return OpenAI(
        api_key=api_key,
        timeout=20.0,
    )


def generate_ai_answer(user_prompt: str, db: Session) -> str:
    client = get_openai_client()

    intent = resolve_intent(
        client=client,
        user_prompt=user_prompt,
        model=OPENAI_MODEL,
    )

    matched_items = search_items_by_keywords(
        db=db,
        prompt=user_prompt,
        client=client,
        model=OPENAI_MODEL,
    )
    matched_item_dicts = items_to_dicts(matched_items)
    all_items = list_items_for_ai(db)

    if matched_item_dicts:
        context_items = matched_item_dicts[:10]
    else:
        context_items = all_items[:25]

    if intent in {"recommendation", "price_filter"}:
        prompt = build_recommendation_prompt(
            user_prompt=user_prompt,
            items=context_items,
        )
        return generate_chat_response(
            client=client,
            prompt=prompt,
            model=OPENAI_MODEL,
        )

    prompt = build_semantic_answer_prompt(
        user_prompt=user_prompt,
        items=context_items,
    )
    return generate_chat_response(
        client=client,
        prompt=prompt,
        model=OPENAI_MODEL,
    )