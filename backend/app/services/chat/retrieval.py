from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher
from typing import Any


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
    "יש", "האם", "צריך", "צריכה", "מחפש", "מחפשת", "רוצה",
    "ל", "ב", "כ",
}

PRICE_INTENT_KEYWORDS = {
    "low": {
        "cheap",
        "budget",
        "affordable",
        "low cost",
        "low-cost",
        "inexpensive",
        "זול",
        "זולה",
        "זולים",
        "זולות",
        "בזול",
        "לא יקר",
        "לא יקרה",
    },
    "high": {
        "expensive",
        "premium",
        "high end",
        "high-end",
        "luxury",
        "יקר",
        "יקרה",
        "יקרים",
        "יקרות",
        "פרימיום",
        "יוקרתי",
        "יוקרתית",
    },
}

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


def meaningful_tokens(text: str) -> set[str]:
    tokens = normalize_text(text).split()
    return {token for token in tokens if token not in STOPWORDS and len(token) > 1}


def shorten_text(text: str | None, max_length: int = 140) -> str | None:
    if not text:
        return None

    text = text.strip()
    if len(text) <= max_length:
        return text

    return text[: max_length - 3].rstrip() + "..."


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

        if candidate == item_name:
            return item

        overlap = len(candidate_tokens & item_tokens)
        token_ratio = overlap / max(len(candidate_tokens), 1)

        ratio = _similarity(candidate, item_name)

        if len(candidate_tokens) >= 2 and (
            candidate in item_name or item_name in candidate
        ):
            containment_bonus = 0.20
        else:
            containment_bonus = 0.0

        number_penalty = 0.0
        if candidate_numbers:
            if candidate_numbers == item_numbers:
                number_penalty = 0.0
            elif candidate_numbers & item_numbers:
                number_penalty = -0.10
            else:
                number_penalty = -0.35

        score = (
            (token_ratio * 0.55)
            + (ratio * 0.25)
            + containment_bonus
            + number_penalty
        )

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
    matched_items = [item for _, item in scored_items[:limit]]
    matched_items = sort_items_by_price_intent(matched_items, prompt)
    return matched_items

def detect_price_intent(prompt: str) -> str | None:
    normalized_prompt = normalize_text(prompt)

    for keyword in PRICE_INTENT_KEYWORDS["low"]:
        if keyword in normalized_prompt:
            return "low"

    for keyword in PRICE_INTENT_KEYWORDS["high"]:
        if keyword in normalized_prompt:
            return "high"

    return None

def sort_items_by_price_intent(
    matched_items: list[dict[str, Any]],
    prompt: str,
) -> list[dict[str, Any]]:
    price_intent = detect_price_intent(prompt)

    if price_intent == "low":
        return sorted(
            matched_items,
            key=lambda item: float(item.get("price_usd", 0)),
        )

    if price_intent == "high":
        return sorted(
            matched_items,
            key=lambda item: float(item.get("price_usd", 0)),
            reverse=True,
        )

    return matched_items