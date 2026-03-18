from __future__ import annotations

import os
import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any

from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Item


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


GPT_INTENTS = {
    "count_products",
    "count_in_stock",
    "count_out_of_stock",
    "product_lookup",
    "semantic_question",
    "unknown",
}

STOPWORDS = {
    # English
    "i", "me", "my", "we", "you", "your",
    "a", "an", "the",
    "and", "or", "of", "to", "for", "with", "in", "on",
    "is", "are", "do", "does", "have", "has",
    "need", "want", "looking", "look",
    # Hebrew
    "אני", "אנחנו", "אתה", "את", "אתם", "אתן",
    "של", "עם", "על", "אל", "מן", "גם", "או", "ו",
    "יש", "האם", "צריך", "צריכה", "מחפש", "מחפשת", "רוצה", "רוצה",
    "ל", "ב", "כ",
}

def meaningful_tokens(text: str) -> set[str]:
    tokens = normalize_text(text).split()
    return {token for token in tokens if token not in STOPWORDS and len(token) > 1}

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

def build_store_context(items: list[dict[str, Any]]) -> str:
    total_products = len(items)
    in_stock_count = sum(1 for item in items if item["stock_qty"] > 0)
    out_of_stock_count = total_products - in_stock_count

    lines = [
        "STORE SUMMARY:",
        f"- Total products: {total_products}",
        f"- In stock: {in_stock_count}",
        f"- Out of stock: {out_of_stock_count}",
        "",
        "CATALOG:",
    ]

    for item in items:
        stock = item["stock_qty"]
        stock_text = f"in stock ({stock})" if stock > 0 else "out of stock"
        lines.append(
            f"- {item['name']} | price ${item['price_usd']:.2f} | {stock_text}"
        )

    return "\n".join(lines)


def build_subset_context(
    items: list[dict[str, Any]],
    matched_items: list[dict[str, Any]],
) -> str:
    total_products = len(items)
    in_stock_count = sum(1 for item in items if item["stock_qty"] > 0)
    out_of_stock_count = total_products - in_stock_count

    lines = [
        "STORE SUMMARY:",
        f"- Total products: {total_products}",
        f"- In stock: {in_stock_count}",
        f"- Out of stock: {out_of_stock_count}",
        "",
        "RELEVANT PRODUCTS:",
    ]

    if not matched_items:
        lines.append("- No strongly matched products found.")
    else:
        for item in matched_items:
            stock = item["stock_qty"]
            stock_text = f"in stock ({stock})" if stock > 0 else "out of stock"

            parts = [
                f"- {item['name']}",
                f"price ${item['price_usd']:.2f}",
                stock_text,
            ]

            if item.get("category"):
                parts.append(f"category: {item['category']}")

            short_description = shorten_text(item.get("description"))
            if short_description:
                parts.append(f"description: {short_description}")

            lines.append(" | ".join(parts))

    return "\n".join(lines)

def normalize_text(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFKC", text)

    text = (
        text.replace("־", " ")
        .replace("-", " ")
        .replace("_", " ")
        .replace("'", "")
        .replace("’", "")
        .replace('"', "")
        .replace("״", "")
    )

    text = re.sub(r"[^a-zא-ת0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text

def shorten_text(text: str | None, max_length: int = 140) -> str | None:
    if not text:
        return None

    text = text.strip()
    if len(text) <= max_length:
        return text

    return text[: max_length - 3].rstrip() + "..."

def extract_candidate_product_name(prompt: str) -> str:
    text = normalize_text(prompt)

    patterns = [
        # English - price
        r"price of (.+)",
        r"how much is (.+)",
        r"how much does (.+) cost",
        r"cost of (.+)",
        # English - availability
        r"is (.+) available",
        r"do you have (.+)",
        r"do you sell (.+)",
        r"stock of (.+)",
        r"availability of (.+)",
        r"is (.+) in stock",
        # Hebrew - price
        r"מה המחיר של (.+)",
        r"כמה עולה (.+)",
        r"מחיר של (.+)",
        r"עלות של (.+)",
        # Hebrew - availability
        r"האם יש (.+)",
        r"יש לכם (.+)",
        r"יש לך (.+)",
        r"האם קיים (.+)",
        r"האם קיימת (.+)",
        r"האם זמין (.+)",
        r"האם זמינה (.+)",
        r"מלאי של (.+)",
        r"זמינות של (.+)",
        r"האם (.+) במלאי",
        r"האם (.+) זמין",
        r"האם (.+) זמינה",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip(" ?!.,")

    return text


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _extract_numbers(text: str) -> set[str]:
    return set(re.findall(r"\d+", text))


def _tokenize(text: str) -> list[str]:
    return normalize_text(text).split()


def find_best_product_match(
    prompt: str,
    items: list[dict[str, Any]],
    min_score: float = 0.72,
) -> dict[str, Any] | None:
    candidate = normalize_text(extract_candidate_product_name(prompt))
    if not candidate:
        return None

    candidate_tokens = set(_tokenize(candidate))
    candidate_numbers = _extract_numbers(candidate)

    best_item: dict[str, Any] | None = None
    best_score = 0.0

    for item in items:
        item_name = normalize_text(item["name"])
        item_tokens = set(_tokenize(item_name))
        item_numbers = _extract_numbers(item_name)

        # exact full match
        if candidate == item_name:
            return item

        # token overlap
        overlap = len(candidate_tokens & item_tokens)
        token_ratio = overlap / max(len(candidate_tokens), 1)

        # string similarity
        ratio = _similarity(candidate, item_name)

        # containment bonus only if candidate has at least 2 tokens
        if len(candidate_tokens) >= 2 and (
            candidate in item_name or item_name in candidate
        ):
            containment_bonus = 0.20
        else:
            containment_bonus = 0.0

        # strong penalty if numbers exist and do not match
        number_penalty = 0.0
        if candidate_numbers:
            if candidate_numbers == item_numbers:
                number_penalty = 0.0
            elif candidate_numbers & item_numbers:
                number_penalty = -0.10
            else:
                number_penalty = -0.35

        score = (token_ratio * 0.55) + (ratio * 0.25) + containment_bonus + number_penalty

        if score > best_score:
            best_score = score
            best_item = item
  
        if best_score >= min_score:
            return best_item

    return None

def search_items_for_ai(
    prompt: str,
    items: list[dict[str, Any]],
    limit: int = 12,
) -> list[dict[str, Any]]:
    normalized_prompt = normalize_text(prompt)
    prompt_tokens = meaningful_tokens(prompt)
    prompt_numbers = _extract_numbers(normalized_prompt)

    token_aliases = {
        "shampoo": {"shampoo", "שמפו"},
        "conditioner": {"conditioner", "מרכך"},
        "hair": {"hair", "שיער"},
        "dry": {"dry", "יבש", "יבשה"},
        "skin": {"skin", "עור"},
        "skincare": {"skincare", "skin", "טיפוח", "עור"},
        "phone": {"phone", "smartphone", "טלפון", "סמארטפון", "mobile"},
        "iphone": {"iphone", "אייפון"},
        "galaxy": {"galaxy", "גלקסי"},
        "laptop": {"laptop", "notebook", "מחשב", "לפטופ"},
        "perfume": {"perfume", "fragrance", "בושם"},
        "soap": {"soap", "סבון", "body", "wash", "רחצה"},
    }

    scored_items: list[tuple[float, dict[str, Any]]] = []

    for item in items:
        item_name = normalize_text(item["name"])

        searchable_text = " ".join(
            part for part in [
                item.get("name", ""),
                item.get("category", ""),
                item.get("description", ""),
            ]
            if part
        )   

        item_tokens = meaningful_tokens(searchable_text)
        item_numbers = _extract_numbers(item_name)

        overlap = len(prompt_tokens & item_tokens)
        token_ratio = overlap / max(len(prompt_tokens), 1)

        alias_matches = 0
        for alias_group in token_aliases.values():
            if prompt_tokens & alias_group and item_tokens & alias_group:
                alias_matches += 1

        number_bonus = 0.0
        if prompt_numbers:
            if prompt_numbers == item_numbers:
                number_bonus += 0.20
            elif prompt_numbers & item_numbers:
                number_bonus += 0.08
            else:
                number_bonus -= 0.15

        containment_bonus = 0.0
        if item_name in normalized_prompt or normalized_prompt in item_name:
            containment_bonus = 0.15

        ratio = 0.0
        if overlap > 0 or alias_matches > 0:
            ratio = _similarity(normalized_prompt, item_name)

        score = (
            token_ratio * 0.55
            + alias_matches * 0.20
            + number_bonus
            + containment_bonus
            + ratio * 0.10
        )

        if overlap > 0 or alias_matches > 0:
            scored_items.append((score, item))

    scored_items.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored_items[:limit]]

def detect_rule_based_intent(
    prompt: str,
    items: list[dict[str, Any]],
) -> dict[str, Any] | None:
    text = normalize_text(prompt)

    total_keywords = [
        # English
        "how many products",
        "number of products",
        "total products",
        "how many items",
        "number of items",
        "total items",
        "catalog size",
        "total number of products",
        "total number of items",
        # Hebrew
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
        # English
        "how many in stock",
        "number in stock",
        "items in stock",
        "products in stock",
        "available products",
        "available items",
        # Hebrew
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
        # English
        "how many out of stock",
        "number out of stock",
        "items out of stock",
        "products out of stock",
        "sold out items",
        "sold out products",
        "unavailable products",
        # Hebrew
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
        # English
        "price of",
        "how much is",
        "how much does",
        "cost of",
        # Hebrew
        "מה המחיר של",
        "כמה עולה",
        "מחיר של",
        "עלות של",
    ]

    availability_indicators = [
        # English
        "available",
        "in stock",
        "do you have",
        "do you sell",
        "availability of",
        "stock of",
        # Hebrew
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
            return {
                "intent": "price_lookup",
                "item": matched_item,
            }

    looks_like_availability = (
        any(indicator in text for indicator in availability_indicators)
        or text.startswith("is ")
        or text.startswith("האם ")
    )

    if looks_like_availability:
        matched_item = find_best_product_match(prompt, items)
        if matched_item:
            return {
                "intent": "availability_lookup",
                "item": matched_item,
            }

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


def generate_gpt_answer(prompt: str, context: str) -> str:
    system_prompt = """
You are a helpful shopping assistant.
Answer the user using only the store context provided.
If the relevant information is missing, say so briefly and clearly.
Be concise and accurate.
The user may write in English or Hebrew. Reply in the same language as the user when possible.
""".strip()

    response = client.responses.create(
        model="gpt-5-mini",
        input=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"STORE CONTEXT:\n{context}\n\nUSER QUESTION:\n{prompt}",
            },
        ],
    )

    return response.output_text.strip()


def generate_ai_answer(prompt: str, db: Session) -> str:
    items = list_items_for_ai(db)

    # 1) Rule-based fast path
    rule_intent_data = detect_rule_based_intent(prompt, items)

    if rule_intent_data:
        rule_answer = handle_rule_based_query(rule_intent_data, items)
        if rule_answer:
            return rule_answer

    # 2) If this looks like a price/availability question but no exact match was found,
    # return a direct backend answer instead of falling through to GPT.
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
        return f'I couldn’t find an exact product match for "{candidate}" in the catalog.'

    if availability_like:
        candidate = extract_candidate_product_name(prompt)
        return f'I couldn’t find an exact product match for "{candidate}" in the catalog.'

    # 3) GPT classifier fallback
    intent = classify_intent_with_gpt(prompt)

    # 4) Backend answers for count intents
    if intent in {"count_products", "count_in_stock", "count_out_of_stock"}:
        answer = handle_rule_based_query({"intent": intent}, items)
        if answer:
            return answer

    # 5) Product lookup / semantic / unknown => subset + GPT
    matched_items = search_items_for_ai(prompt, items)

    if not matched_items:
        return "I couldn’t find relevant products in the catalog for that request."

    subset_context = build_subset_context(items, matched_items)
    return generate_gpt_answer(prompt, subset_context)