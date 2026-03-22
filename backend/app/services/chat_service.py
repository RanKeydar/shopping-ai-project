from __future__ import annotations

import os

from openai import OpenAI
from sqlalchemy.orm import Session

from app.services.chat.generation import generate_chat_response
from app.services.chat.intent import detect_price_preference, resolve_intent
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


def sort_items_by_price_preference(items: list[dict], preference: str) -> list[dict]:
    if preference == "cheap":
        return sorted(items, key=lambda item: (item["price_usd"], -item["stock_qty"]))

    if preference == "expensive":
        return sorted(
            items,
            key=lambda item: (-item["price_usd"], -item["stock_qty"]),
        )

    return items


def filter_context_items(
    matched_item_dicts: list[dict],
    all_items: list[dict],
    price_preference: str,
) -> list[dict]:
    base_items = matched_item_dicts if matched_item_dicts else all_items

    if not base_items:
        return []

    ranked_items = sort_items_by_price_preference(base_items, price_preference)
    return ranked_items[:10]


def build_price_context(items: list[dict], price_preference: str) -> dict:
    if not items:
        return {
            "has_multiple_matches": False,
            "match_count": 0,
            "price_preference": price_preference,
            "should_use_relative_price_labels": False,
            "min_price": None,
            "max_price": None,
        }

    prices = [item["price_usd"] for item in items]

    return {
        "has_multiple_matches": len(items) > 1,
        "match_count": len(items),
        "price_preference": price_preference,
        "should_use_relative_price_labels": len(items) > 1 and price_preference in {"cheap", "expensive"},
        "min_price": min(prices),
        "max_price": max(prices),
    }


def generate_ai_answer(user_prompt: str, db: Session) -> str:
    client = get_openai_client()

    intent = resolve_intent(
        client=client,
        user_prompt=user_prompt,
        model=OPENAI_MODEL,
    )

    price_preference = detect_price_preference(user_prompt)

    matched_items = search_items_by_keywords(
        db=db,
        prompt=user_prompt,
        client=client,
        model=OPENAI_MODEL,
    )
    matched_item_dicts = items_to_dicts(matched_items)
    all_items = list_items_for_ai(db)

    context_items = filter_context_items(
        matched_item_dicts=matched_item_dicts,
        all_items=all_items[:25],
        price_preference=price_preference,
    )

    price_context = build_price_context(
        items=context_items,
        price_preference=price_preference,
    )

    if intent in {"recommendation", "price_filter"}:
        prompt = build_recommendation_prompt(
            user_prompt=user_prompt,
            items=context_items,
            price_context=price_context,
        )
        return generate_chat_response(
            client=client,
            prompt=prompt,
            model=OPENAI_MODEL,
        )

    prompt = build_semantic_answer_prompt(
        user_prompt=user_prompt,
        items=context_items if context_items else all_items[:25],
    )
    return generate_chat_response(
        client=client,
        prompt=prompt,
        model=OPENAI_MODEL,
    )