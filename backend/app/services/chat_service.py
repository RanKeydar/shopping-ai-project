from __future__ import annotations

import os

from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Item


def list_items_for_ai(db: Session):
    items = db.execute(select(Item)).scalars().all()

    result = []
    for item in items:
        result.append(
            {
                "id": item.id,
                "name": item.name,
                "price_usd": float(item.price_usd),
                "stock_qty": int(item.stock_qty),
            }
        )
    return result


def build_store_context(items):
    lines = []

    for item in items:
        stock = item["stock_qty"]
        stock_text = f"in stock ({stock})" if stock > 0 else "out of stock"

        lines.append(
            f"- {item['name']} | price ${item['price_usd']:.2f} | {stock_text}"
        )

    return "\n".join(lines)


def generate_ai_answer(user_prompt: str, store_context: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing")

    client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model="gpt-5-mini",
        input=[
            {
                "role": "system",
                "content": (
                    "You are a shopping assistant for an e-commerce website. "
                    "Answer only based on the store catalog provided. "
                    "Mention whether items are in stock or out of stock. "
                    "If the catalog does not support the answer, say so clearly. "
                    "Keep answers short, practical, and helpful."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Store catalog:\n{store_context}\n\n"
                    f"User question:\n{user_prompt}"
                ),
            },
        ],
    )

    return response.output_text