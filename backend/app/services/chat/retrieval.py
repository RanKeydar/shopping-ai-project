# app/services/chat/retrieval.py

from __future__ import annotations

import json
import re

from openai import OpenAI
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
    "לכם",
    "לנו",
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


def contains_hebrew(text: str) -> bool:
    return bool(re.search(r"[א-ת]", text))


def contains_hebrew_keywords(keywords: list[str]) -> bool:
    return any(contains_hebrew(keyword) for keyword in keywords)


def build_keyword_translation_prompt(keywords: list[str]) -> str:
    keywords_json = json.dumps(keywords, ensure_ascii=False)

    return f"""
You are helping a shopping search engine.

Task:
Translate each keyword to concise English search keywords suitable for matching product
names, categories, and descriptions in an English catalog.

Rules:
- Input is a list of user keywords that may be in Hebrew or mixed language.
- Return a JSON array only.
- Each output item must be short: usually 1 word, sometimes 2 words max.
- Preserve product-search meaning, not full sentence meaning.
- Do not explain.
- Do not add categories unless directly implied by the keyword.
- Keep the number of returned keywords small and relevant.
- Deduplicate terms.

Input keywords:
{keywords_json}
""".strip()


def translate_keywords_with_gpt(
    client: OpenAI,
    keywords: list[str],
    model: str,
) -> list[str]:
    if not keywords:
        return []

    completion = client.responses.create(
        model=model,
        input=build_keyword_translation_prompt(keywords),
    )

    raw = (completion.output_text or "").strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []

    if not isinstance(parsed, list):
        return []

    translated: list[str] = []
    seen: set[str] = set()

    for item in parsed:
        if not isinstance(item, str):
            continue

        token = item.strip().lower()
        if not token:
            continue

        if token in seen:
            continue

        seen.add(token)
        translated.append(token)

    return translated[:8]


def build_search_keywords(
    prompt: str,
    client: OpenAI | None = None,
    model: str | None = None,
) -> list[str]:
    base_keywords = unique_keywords(prompt)

    if not base_keywords:
        return []

    search_keywords: list[str] = []
    seen: set[str] = set()

    def add_keyword(keyword: str) -> None:
        keyword = keyword.strip().lower()
        if not keyword:
            return
        if keyword in seen:
            return
        seen.add(keyword)
        search_keywords.append(keyword)

    for keyword in base_keywords:
        add_keyword(keyword)

    if contains_hebrew_keywords(base_keywords) and client is not None and model:
        translated_keywords = translate_keywords_with_gpt(
            client=client,
            keywords=base_keywords,
            model=model,
        )
        for keyword in translated_keywords:
            add_keyword(keyword)

    return search_keywords[:10]


def search_items_by_keywords(
    db: Session,
    prompt: str,
    client: OpenAI | None = None,
    model: str | None = None,
    limit: int = 10,
) -> list[Item]:
    keywords = build_search_keywords(
        prompt=prompt,
        client=client,
        model=model,
    )

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