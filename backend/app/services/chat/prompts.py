from __future__ import annotations


def build_store_context(items: list[dict]) -> str:
    if not items:
        return "No matching items found."

    lines: list[str] = []

    for item in items:
        stock = item["stock_qty"]
        stock_text = f"in stock ({stock})" if stock > 0 else "out of stock"

        lines.append(
            f"- {item['name']} | category: {item.get('category') or 'N/A'} | "
            f"price: ${item['price_usd']:.2f} | {stock_text} | "
            f"description: {item.get('description') or 'N/A'}"
        )

    return "\n".join(lines)


def build_recommendation_prompt(user_prompt: str, items: list[dict]) -> str:
    context = build_store_context(items)

    return f"""
You are a shopping assistant for a small store.

Your job:
- Recommend products only from the provided store context.
- Do not invent products, features, prices, brands, or stock.
- If the user asks for cheap / cheapest / budget / affordable items, use actual prices from the context.
- If the user asks for expensive / premium / luxury items, use actual higher-priced items from the context.
- Do not claim something is "premium" unless the data actually supports that description.
- If no suitable item exists, say that clearly.
- Prefer a helpful format:

Recommendation:
...

Alternatives:
- ...
- ...

Store context:
{context}

User request:
{user_prompt}
""".strip()


def build_semantic_answer_prompt(user_prompt: str, items: list[dict]) -> str:
    context = build_store_context(items)

    return f"""
You are a shopping assistant answering questions about store products.

Rules:
- Use only the provided store context.
- Do not invent facts.
- If the answer is not supported by the data, say so clearly.
- When relevant, mention price and stock exactly as shown.
- Keep the answer direct and useful.

Store context:
{context}

User question:
{user_prompt}
""".strip()