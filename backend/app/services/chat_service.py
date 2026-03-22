from __future__ import annotations

import os
from typing import Any

from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Item
from app.services.chat import (
    build_no_exact_match_message,
    build_no_relevant_products_message,
    build_subset_context,
    extract_candidate_product_name,
    find_best_product_match,
    generate_gpt_answer,
    get_user_language_code,
    normalize_text,
    search_items_for_ai,
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


GPT_INTENTS = {
    "count_products",
    "count_in_stock",
    "count_out_of_stock",
    "product_lookup",
    "semantic_question",
    "unknown",
}


def list_items_for_ai(db: Session) -> list[dict[str, Any]]:
    items = db.execute(select(Item)).scalars().all()

    result: list[dict[str, Any]] = []
    for item in items:
        result.append(
            {
                "id": item.id,
                "name": item.name,
                "price_usd": float(item.price_usd),
                "stock_qty": int(item.stock_qty),
                "category": item.category,
                "description": item.description,
            }
        )

    return result


def detect_rule_based_intent(
    prompt: str,
    items: list[dict[str, Any]],
) -> dict[str, Any] | None:
    text = normalize_text(prompt)

    total_keywords = [
        "how many products",
        "number of products",
        "total products",
        "how many items",
        "number of items",
        "total items",
        "catalog size",
        "total number of products",
        "total number of items",
        "כמה מוצרים",
        "כמה פריטים",
        "מספר המוצרים",
        "מספר הפריטים",
        "סך המוצרים",
        "סך הפריטים",
        "כמה מוצרים יש",
        "כמה פריטים יש",
    ]

    in_stock_keywords = [
        "how many in stock",
        "number in stock",
        "items in stock",
        "products in stock",
        "available products",
        "available items",
        "כמה במלאי",
        "כמה מוצרים במלאי",
        "כמה פריטים במלאי",
        "כמה זמינים",
        "מספר המוצרים במלאי",
        "מספר הפריטים במלאי",
        "כמה מוצרים זמינים",
        "כמה פריטים זמינים",
    ]

    out_of_stock_keywords = [
        "how many out of stock",
        "number out of stock",
        "items out of stock",
        "products out of stock",
        "sold out items",
        "sold out products",
        "unavailable products",
        "כמה אזלו",
        "כמה לא במלאי",
        "כמה מוצרים אזלו",
        "כמה פריטים אזלו",
        "כמה מוצרים לא במלאי",
        "כמה פריטים לא במלאי",
        "כמה אינם זמינים",
        "כמה לא זמינים",
    ]

    price_keywords = [
        "price of",
        "how much is",
        "how much does",
        "cost of",
        "מה המחיר של",
        "כמה עולה",
        "מחיר של",
        "עלות של",
    ]

    availability_indicators = [
        "available",
        "in stock",
        "do you have",
        "do you sell",
        "availability of",
        "stock of",
        "יש לכם",
        "יש לך",
        "האם יש",
        "במלאי",
        "זמין",
        "זמינה",
        "זמינות של",
        "מלאי של",
        "קיים",
        "קיימת",
    ]

    if any(keyword in text for keyword in total_keywords):
        return {"intent": "count_products"}

    if any(keyword in text for keyword in in_stock_keywords):
        return {"intent": "count_in_stock"}

    if any(keyword in text for keyword in out_of_stock_keywords):
        return {"intent": "count_out_of_stock"}

    if any(keyword in text for keyword in price_keywords):
        matched_item = find_best_product_match(prompt, items)
        if matched_item:
            return {"intent": "price_lookup", "item": matched_item}

    looks_like_availability = (
        any(indicator in text for indicator in availability_indicators)
        or text.startswith("is ")
        or text.startswith("האם ")
    )

    if looks_like_availability:
        matched_item = find_best_product_match(prompt, items)
        if matched_item:
            return {"intent": "availability_lookup", "item": matched_item}

    return None


def handle_rule_based_query(
    intent_data: dict[str, Any],
    items: list[dict[str, Any]],
) -> str | None:
    intent = intent_data["intent"]

    if intent == "count_products":
        return f"We currently have {len(items)} products in the catalog."

    if intent == "count_in_stock":
        in_stock_count = sum(1 for item in items if item["stock_qty"] > 0)
        return f"We currently have {in_stock_count} products in stock."

    if intent == "count_out_of_stock":
        out_of_stock_count = sum(1 for item in items if item["stock_qty"] <= 0)
        return f"We currently have {out_of_stock_count} out-of-stock products."

    if intent == "price_lookup":
        item = intent_data.get("item")
        if not item:
            return None
        return f"The price of {item['name']} is ${item['price_usd']:.2f}."

    if intent == "availability_lookup":
        item = intent_data.get("item")
        if not item:
            return None

        stock_qty = item["stock_qty"]
        if stock_qty > 0:
            return f"Yes, {item['name']} is available. We currently have {stock_qty} in stock."
        return f"No, {item['name']} is currently out of stock."

    return None


def classify_intent_with_gpt(prompt: str) -> str:
    system_prompt = """
You are an intent classifier for an ecommerce shopping assistant.

Return exactly one of these labels:
- count_products
- count_in_stock
- count_out_of_stock
- product_lookup
- semantic_question
- unknown

Rules:
- count_products: user asks how many products/items exist in the catalog
- count_in_stock: user asks how many products/items are available/in stock
- count_out_of_stock: user asks how many products/items are out of stock/unavailable
- product_lookup: user asks about a specific product or a small set of products, such as price, stock, availability, or product-specific details
- semantic_question: broader recommendation/comparison/meaning/style/use-case questions that require reasoning over relevant products
- unknown: unclear or unrelated request

The user may write in English or Hebrew.
Return only the label, nothing else.
""".strip()

    response = client.responses.create(
        model="gpt-5-mini",
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    )

    label = response.output_text.strip().lower()
    if label not in GPT_INTENTS:
        return "unknown"

    return label


def generate_ai_answer(prompt: str, db: Session) -> str:
    items = list_items_for_ai(db)
    user_language = get_user_language_code(prompt)

    rule_intent_data = detect_rule_based_intent(prompt, items)
    if rule_intent_data:
        rule_answer = handle_rule_based_query(rule_intent_data, items)
        if rule_answer:
            return rule_answer

    normalized_prompt = normalize_text(prompt)

    price_like = any(
        keyword in normalized_prompt
        for keyword in [
            "price of",
            "how much is",
            "how much does",
            "cost of",
            "מה המחיר של",
            "כמה עולה",
            "מחיר של",
            "עלות של",
        ]
    )

    availability_like = (
        any(
            keyword in normalized_prompt
            for keyword in [
                "available",
                "in stock",
                "do you have",
                "do you sell",
                "availability of",
                "stock of",
                "יש לכם",
                "יש לך",
                "האם יש",
                "במלאי",
                "זמין",
                "זמינה",
                "זמינות של",
                "מלאי של",
            ]
        )
        or normalized_prompt.startswith("is ")
        or normalized_prompt.startswith("האם ")
    )

    if price_like:
        candidate = extract_candidate_product_name(prompt)
        return build_no_exact_match_message(candidate, user_language)

    if availability_like:
        candidate = extract_candidate_product_name(prompt)
        return build_no_exact_match_message(candidate, user_language)

    intent = classify_intent_with_gpt(prompt)

    if intent in {"count_products", "count_in_stock", "count_out_of_stock"}:
        answer = handle_rule_based_query({"intent": intent}, items)
        if answer:
            return answer

    matched_items = search_items_for_ai(prompt, items)

    if not matched_items:
        return build_no_relevant_products_message(user_language)

    subset_context = build_subset_context(items, matched_items)
    return generate_gpt_answer(prompt, subset_context, client)