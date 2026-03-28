from __future__ import annotations

import re
from typing import Any


_EN_STOPWORDS = {
    "i", "me", "my", "we", "you", "your", "he", "she", "it", "they", "them",
    "a", "an", "the", "and", "or", "for", "to", "of", "in", "on", "with",
    "at", "by", "from", "is", "are", "be", "am", "was", "were",
    "this", "that", "these", "those", "do", "does", "did", "have", "has", "had",
    "need", "want", "looking", "look", "show", "find",
    "something", "product", "products", "item", "items",
    "please", "good", "best", "recommend", "recommended", "recommendation",
}

_HE_STOPWORDS = {
    "אני", "אתה", "את", "אנחנו", "הוא", "היא", "הם", "הן",
    "זה", "זאת", "של", "עם", "על", "אל", "מן", "מה", "מי",
    "יש", "אין", "גם", "או", "אבל", "אם", "כי", "כן", "לא", "רק", "כל", "כמה",
    "צריך", "צריכה", "רוצה", "מחפש", "מחפשת", "תראה", "תראי", "תמצא",
    "משהו", "מוצר", "מוצרים", "פריט", "פריטים", "המלצה", "מומלץ",
    "לכם", "לנו",
}

_STOPWORDS = _EN_STOPWORDS | _HE_STOPWORDS

_HEBREW_HINTS: dict[str, list[str]] = {
    "חלב": ["milk", "dairy"],
    "לחם": ["bread", "bakery"],
    "ביצה": ["egg", "eggs"],
    "ביצים": ["egg", "eggs"],
    "שמפו": ["shampoo", "hair"],
    "מרכך": ["conditioner", "hair"],
    "שיער": ["hair"],
    "כיסא": ["chair"],
    "כסא": ["chair"],
    "שולחן": ["table", "desk"],
    "ספה": ["sofa", "couch"],
}


def normalize_text(value: Any) -> str:
    if value is None:
        return ""

    text = str(value).strip().lower()
    text = re.sub(r"[^a-zA-Zא-ת0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize_prompt(prompt: str) -> list[str]:
    text = normalize_text(prompt)

    if not text:
        return []

    tokens = text.split()

    cleaned: list[str] = []
    for token in tokens:
        if len(token) < 2:
            continue
        if token in _STOPWORDS:
            continue
        cleaned.append(token)

    return cleaned


def unique_keywords(prompt: str, max_keywords: int = 6) -> list[str]:
    tokens = tokenize_prompt(prompt)

    seen: set[str] = set()
    keywords: list[str] = []

    for token in tokens:
        if token in seen:
            continue
        seen.add(token)
        keywords.append(token)

    return keywords[:max_keywords]


def expand_keywords(keywords: list[str]) -> list[str]:
    expanded: list[str] = []
    seen: set[str] = set()

    def add_keyword(keyword: str) -> None:
        keyword = normalize_text(keyword)
        if not keyword:
            return
        if keyword in seen:
            return
        seen.add(keyword)
        expanded.append(keyword)

    for keyword in keywords:
        add_keyword(keyword)

        for hint in _HEBREW_HINTS.get(keyword, []):
            add_keyword(hint)

    return expanded[:12]


def build_search_keywords(prompt: str) -> list[str]:
    base_keywords = unique_keywords(prompt)
    if not base_keywords:
        return []

    return expand_keywords(base_keywords)


def build_item_tokens(item: dict[str, Any]) -> dict[str, set[str]]:
    name_tokens = set(tokenize_prompt(str(item.get("name", ""))))
    category_tokens = set(tokenize_prompt(str(item.get("category", ""))))
    description_tokens = set(tokenize_prompt(str(item.get("description", ""))))

    return {
        "name": name_tokens,
        "category": category_tokens,
        "description": description_tokens,
        "all": name_tokens | category_tokens | description_tokens,
    }


def score_item_match(item: dict[str, Any], keywords: list[str]) -> int:
    tokens = build_item_tokens(item)

    score = 0

    for keyword in keywords:
        if keyword in tokens["name"]:
            score += 3
        if keyword in tokens["category"]:
            score += 2
        if keyword in tokens["description"]:
            score += 1

    return score


def filter_and_sort_items_by_query(
    items: list[dict[str, Any]],
    query: str,
) -> list[dict]:
    if not query or not query.strip():
        return items

    keywords = build_search_keywords(query)
    if not keywords:
        return items

    matched_items: list[tuple[int, dict[str, Any]]] = []

    for item in items:
        score = score_item_match(item, keywords)
        if score > 0:
            matched_items.append((score, item))

    matched_items.sort(
        key=lambda pair: (
            -pair[0],
            -int(pair[1].get("stock_qty", 0) or 0),
            float(pair[1].get("price_usd", 0) or 0),
        )
    )

    return [item for _, item in matched_items]