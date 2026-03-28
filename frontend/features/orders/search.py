from __future__ import annotations

from typing import Any


HEBREW_TO_ENGLISH_TOKENS: dict[str, list[str]] = {
    "שמפו": ["shampoo", "hair", "hair care"],
    "מרכך": ["conditioner", "hair", "hair care"],
    "מסכה": ["mask", "hair mask", "hair care"],
    "שיער": ["hair", "hair care"],
    "יבש": ["dry", "moisture", "hydration"],
    "קשקשים": ["dandruff", "scalp"],
    "קרקפת": ["scalp"],
    "כיסא": ["chair", "seat", "furniture"],
    "כסא": ["chair", "seat", "furniture"],
    "שולחן": ["table", "desk", "furniture"],
    "חלב": ["milk", "dairy"],
    "לחם": ["bread", "bakery"],
    "איפור": ["makeup", "cosmetics", "beauty"],
    "מסקרה": ["mascara", "makeup", "beauty"],
    "פנים": ["face", "facial", "skincare", "beauty"],
}


def normalize_text(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def tokenize_query(query: str) -> list[str]:
    normalized = normalize_text(query)
    if not normalized:
        return []
    return normalized.split()


def expand_query_tokens(tokens: list[str]) -> list[str]:
    expanded: list[str] = []

    for token in tokens:
        expanded.append(token)

        mapped_tokens = HEBREW_TO_ENGLISH_TOKENS.get(token, [])
        for mapped in mapped_tokens:
            expanded.append(normalize_text(mapped))

    # הסרת כפילויות תוך שמירה על סדר
    unique_tokens: list[str] = []
    seen: set[str] = set()

    for token in expanded:
        if token and token not in seen:
            seen.add(token)
            unique_tokens.append(token)

    return unique_tokens


def build_item_search_text(item: dict[str, Any]) -> str:
    parts = [
        item.get("name", ""),
        item.get("category", ""),
        item.get("description", ""),
    ]
    return normalize_text(" ".join(str(part) for part in parts if part))


def filter_items_by_query(items: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    tokens = tokenize_query(query)
    if not tokens:
        return items

    expanded_tokens = expand_query_tokens(tokens)

    matched_items: list[dict[str, Any]] = []

    for item in items:
        searchable_text = build_item_search_text(item)

        if all(token in searchable_text for token in expanded_tokens if " " not in token):
            matched_items.append(item)
            continue

        # תמיכה גם בביטויים כמו "hair care"
        if any(token in searchable_text for token in expanded_tokens):
            matched_items.append(item)

    return matched_items