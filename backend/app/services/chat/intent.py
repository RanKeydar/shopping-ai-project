from __future__ import annotations

import re
from typing import Literal

from openai import OpenAI


ChatIntent = Literal[
    "recommendation",
    "price_filter",
    "semantic_question",
    "unknown",
]

PricePreference = Literal["cheap", "expensive", "none"]


_PRICE_LOW_WORDS = {
    "cheap",
    "cheapest",
    "low cost",
    "lowest price",
    "budget",
    "affordable",
    "inexpensive",
    "זול",
    "זולה",
    "זולים",
    "זולות",
    "הכי זול",
    "הכי זולה",
    "בזול",
    "מחיר נמוך",
}

_PRICE_HIGH_WORDS = {
    "expensive",
    "premium",
    "luxury",
    "high end",
    "high-end",
    "pricey",
    "יקר",
    "יקרה",
    "יקרים",
    "יקרות",
    "יוקרתי",
    "יוקרתית",
    "הכי יקר",
    "הכי יקרה",
}

_RECOMMENDATION_WORDS = {
    "recommend",
    "recommendation",
    "suggest",
    "best",
    "looking for",
    "i need",
    "show me",
    "find me",
    "need",
    "want",
    "match",
    "good for",
    "what should i buy",
    "תמליץ",
    "תמליצי",
    "המלצה",
    "מומלץ",
    "מחפש",
    "מחפשת",
    "אני צריך",
    "אני צריכה",
    "צריך",
    "צריכה",
    "רוצה",
    "תמצא לי",
    "תראי לי",
    "תראה לי",
}

_PRICE_PATTERN = re.compile(
    r"(\$|usd|dollars|nis|ils|₪|price|מחיר)",
    re.IGNORECASE,
)


def normalize_text(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def contains_any(text: str, words: set[str]) -> bool:
    return any(word in text for word in words)


def looks_like_price_filter(text: str) -> bool:
    if _PRICE_PATTERN.search(text):
        return True

    price_phrases = (
        "under ",
        "below ",
        "less than ",
        "more than ",
        "over ",
        "between ",
        "up to ",
        "at least ",
        "max price",
        "min price",
        "עד ",
        "פחות מ",
        "יותר מ",
        "מעל ",
        "מתחת ל",
        "בין ",
        "עד מחיר",
        "לפחות",
    )
    return any(phrase in text for phrase in price_phrases)


def looks_like_price_preference(text: str) -> bool:
    return contains_any(text, _PRICE_LOW_WORDS) or contains_any(text, _PRICE_HIGH_WORDS)


def looks_like_recommendation(text: str) -> bool:
    return contains_any(text, _RECOMMENDATION_WORDS)


def detect_price_preference(prompt: str) -> PricePreference:
    text = normalize_text(prompt)

    if contains_any(text, _PRICE_LOW_WORDS):
        return "cheap"

    if contains_any(text, _PRICE_HIGH_WORDS):
        return "expensive"

    return "none"


def detect_rule_based_intent(prompt: str) -> ChatIntent | None:
    text = normalize_text(prompt)

    if not text:
        return None

    if looks_like_price_filter(text):
        return "price_filter"

    if looks_like_recommendation(text) or looks_like_price_preference(text):
        return "recommendation"

    return None


def build_intent_classification_prompt(user_prompt: str) -> str:
    return f"""
You are an intent classifier for a shopping assistant.

Classify the user's message into exactly one label from this list:
- recommendation
- price_filter
- semantic_question
- unknown

Definitions:
- recommendation:
  The user wants product suggestions, alternatives, or help choosing what to buy.
  This includes requests like "I need a shampoo", "recommend something for dry hair",
  "what is good for kids", "show me a cheap laptop", "I want something premium".

- price_filter:
  The user is filtering products by explicit price logic or thresholds.
  This includes requests like "show products under $10", "items above 50",
  "what costs less than 20", "between 30 and 60".

- semantic_question:
  The user is asking an informational question about products, categories,
  ingredients, attributes, comparisons, or store inventory meaningfully.
  This includes requests like "which products are gluten free",
  "what has high protein", "do you have hair products", "what is good for dry scalp".

- unknown:
  Anything else, unclear, or not shopping-related.

Return only one label and nothing else.

User message:
{user_prompt}
""".strip()


def classify_intent_with_gpt(
    client: OpenAI,
    user_prompt: str,
    model: str,
) -> ChatIntent:
    completion = client.responses.create(
        model=model,
        input=build_intent_classification_prompt(user_prompt),
    )

    raw = (completion.output_text or "").strip().lower()

    if raw in {"recommendation", "price_filter", "semantic_question", "unknown"}:
        return raw  # type: ignore[return-value]

    return "unknown"


def resolve_intent(
    client: OpenAI,
    user_prompt: str,
    model: str,
) -> ChatIntent:
    rule_intent = detect_rule_based_intent(user_prompt)
    if rule_intent is not None:
        return rule_intent

    return classify_intent_with_gpt(
        client=client,
        user_prompt=user_prompt,
        model=model,
    )