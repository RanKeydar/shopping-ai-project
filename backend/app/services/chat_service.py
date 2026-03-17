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

    total_items = len(items)
    in_stock_count = sum(1 for item in items if item["stock_qty"] > 0)
    out_of_stock_count = total_items - in_stock_count

    for item in items:
        stock = item["stock_qty"]
        stock_text = f"in stock ({stock})" if stock > 0 else "out of stock"

        lines.append(
            f"- {item['name']} | price ${item['price_usd']:.2f} | {stock_text}"
        )

    summary = (
        f"Store summary:\n"
        f"- Total products: {total_items}\n"
        f"- In-stock products: {in_stock_count}\n"
        f"- Out-of-stock products: {out_of_stock_count}\n\n"
    )

    return summary + "Store catalog:\n" + "\n".join(lines)

def generate_ai_answer(user_prompt: str, store_context: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing")

    client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model="gpt-5-mini",
        instructions=(
            "You are a shopping assistant for an e-commerce website.\n"
            "You will receive store data that includes:\n"
            "- a store summary\n"
            "- total product counts\n"
            "- stock counts\n"
            "- a product catalog with names, prices, and stock\n\n"
            "You may answer questions about:\n"
            "- how many products exist in the catalog\n"
            "- how many are in stock or out of stock\n"
            "- prices and availability\n"
            "- product categories\n"
            "- specific products listed in the catalog\n\n"
            "Use only the provided store data.\n"
            "Do not invent products, prices, stock, or facts.\n"
            "If the answer cannot be derived from the provided store data, say clearly in the user's language:\n"
            "'I can only answer based on the store catalog.'\n\n"
            "Keep answers short, practical, and helpful."
        ),
        input=(
            f"Store catalog:\n{store_context}\n\n"
            f"User question:\n{user_prompt}"
        ),
        max_output_tokens=180,
        reasoning={"effort": "minimal"},
        text={"format": {"type": "text"}},
    )

    return response.output_text.strip()