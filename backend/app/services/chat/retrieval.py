# app/services/chat/retrieval.py

from __future__ import annotations

import re

from sqlalchemy import case, or_, select
from sqlalchemy.orm import Session

from app.models import Item


_EN_STOPWORDS = {
    "i",
    "me",
    "my",
    "we",
    "you",
    "your",
    "he",
    "she",
    "it",
    "they",
    "them",
    "a",
    "an",
    "the",
    "and",
    "or",
    "for",
    "to",
    "of",
    "in",
    "on",
    "with",
    "at",
    "by",
    "from",
    "is",
    "are",
    "be",
    "am",
    "was",
    "were",
    "this",
    "that",
    "these",
    "those",
    "do",
    "does",
    "did",
    "have",
    "has",
    "had",
    "need",
    "want",
    "looking",
    "look",
    "show",
    "find",
    "something",
    "product",
    "products",
    "item",
    "items",
    "please",
    "good",
    "best",
    "recommend",
    "recommended",
    "recommendation",
}

_HE_STOPWORDS = {
    "אני",
    "אתה",
    "את",
    "אנחנו",
    "הוא",
    "היא",
    "הם",
    "הן",
    "זה",
    "זאת",
    "של",
    "עם",
    "על",
    "אל",
    "מן",
    "מה",
    "מי",
    "יש",
    "אין",
    "גם",
    "או",
    "אבל",
    "אם",
    "כי",
    "כן",
    "לא",
    "רק",
    "כל",
    "כמה",
    "צריך",
    "צריכה",
    "רוצה",
    "מחפש",
    "מחפשת",
    "תראה",
    "תראי",
    "תמצא",
    "משהו",
    "מוצר",
    "מוצרים",
    "פריט",
    "פריטים",
    "המלצה",
    "מומלץ",
}

_STOPWORDS = _EN_STOPWORDS | _HE_STOPWORDS


def list_items_for_ai(db: Session) -> list[dict]:
    items = db.execute(select(Item)).scalars().all()

    result: list[dict] = []
    for item in items:
        result.append(
            {
                "id": item.id,
                "name": item.name,
                "category": item.category,
                "description": item.description,
                "price_usd": float(item.price_usd),
                "stock_qty": int(item.stock_qty),
            }
        )
    return result


def items_to_dicts(items: list[Item]) -> list[dict]:
    result: list[dict] = []

    for item in items:
        result.append(
            {
                "id": item.id,
                "name": item.name,
                "category": item.category,
                "description": item.description,
                "price_usd": float(item.price_usd),
                "stock_qty": int(item.stock_qty),
            }
        )

    return result


def tokenize_prompt(prompt: str) -> list[str]:
    text = (prompt or "").lower().strip()

    if not text:
        return []

    tokens = re.findall(r"[a-zA-Zא-ת0-9']+", text)

    cleaned: list[str] = []
    for token in tokens:
        token = token.strip("'")
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


def search_items_by_keywords(db: Session, prompt: str, limit: int = 10) -> list[Item]:
    keywords = unique_keywords(prompt)

    if not keywords:
        return []

    match_conditions = []
    score_parts = []

    for keyword in keywords:
        name_match = Item.name.ilike(f"%{keyword}%")
        category_match = Item.category.ilike(f"%{keyword}%")
        description_match = Item.description.ilike(f"%{keyword}%")

        match_conditions.extend([name_match, category_match, description_match])

        score_parts.append(case((name_match, 3), else_=0))
        score_parts.append(case((category_match, 2), else_=0))
        score_parts.append(case((description_match, 1), else_=0))

    relevance_score = sum(score_parts)

    stmt = (
        select(Item)
        .where(or_(*match_conditions))
        .order_by(relevance_score.desc(), Item.stock_qty.desc(), Item.price_usd.asc())
        .limit(limit)
    )

    return list(db.execute(stmt).scalars().all())