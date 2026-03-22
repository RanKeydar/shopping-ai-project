from __future__ import annotations

import re


def is_hebrew_text(text: str) -> bool:
    return bool(re.search(r"[א-ת]", text or ""))


def get_response_language_instruction(user_prompt: str) -> str:
    if is_hebrew_text(user_prompt):
        return """
Respond only in Hebrew.
Use natural, fluent Hebrew.
Keep product names exactly as they appear in the store context.
Do not use English section titles such as "Recommendation" or "Alternatives".
Use these exact Hebrew section titles when relevant:
המלצה:
חלופות:
""".strip()

    return """
Respond only in English.
Keep product names exactly as they appear in the store context.
Use these section titles when relevant:
Recommendation:
Alternatives:
""".strip()


def get_recommendation_format_instruction(user_prompt: str) -> str:
    if is_hebrew_text(user_prompt):
        return """
Preferred format:
המלצה:
- <product name> | $<price> | <short Hebrew explanation>

חלופות:
- <product name> | $<price> | <short Hebrew explanation>
- <product name> | $<price> | <short Hebrew explanation>

If there is only one strong match, you may return one recommendation and one or two alternatives.
If there are no good alternatives, write:
חלופות:
- אין חלופות מתאימות כרגע.
""".strip()

    return """
Preferred format:
Recommendation:
- <product name> | $<price> | <short explanation>

Alternatives:
- <product name> | $<price> | <short explanation>
- <product name> | $<price> | <short explanation>

If there are no good alternatives, write:
Alternatives:
- No suitable alternatives right now.
""".strip()


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

def build_price_behavior_instruction(price_context: dict | None) -> str:
    if not price_context:
        return ""

    match_count = price_context.get("match_count", 0)
    preference = price_context.get("price_preference", "none")

    if match_count <= 1 and preference in {"cheap", "expensive"}:
        return (
            "There is only one relevant matching item in the context. "
            "Do not describe it as cheap, budget, expensive, premium, or luxury. "
            "Instead, state that it is the only relevant matching item currently available and mention its price."
        )

    if match_count > 1 and preference == "cheap":
        return (
            "There are multiple relevant matching items in the context. "
            "You may describe the lowest-priced relevant item as the cheapest among the relevant matches. "
            "Present the remaining relevant items as alternatives."
        )

    if match_count > 1 and preference == "expensive":
        return (
            "There are multiple relevant matching items in the context. "
            "You may describe the highest-priced relevant item as the most expensive among the relevant matches. "
            "Present the remaining relevant items as alternatives."
        )

    return ""

def build_recommendation_prompt(
    user_prompt: str,
    items: list[dict],
    price_context: dict | None = None,
) -> str:
    context = build_store_context(items)
    language_instruction = get_response_language_instruction(user_prompt)
    format_instruction = get_recommendation_format_instruction(user_prompt)
    price_behavior_instruction = build_price_behavior_instruction(price_context)

    return f"""
You are a shopping assistant for a small store.

{language_instruction}

Your job:
- Recommend products only from the provided store context.
- Do not invent products, features, prices, brands, or stock.
- If the user asks for cheap / cheapest / budget / affordable items, use actual prices from the context.
- If the user asks for expensive / premium / luxury items, use actual higher-priced items from the context.
- Do not claim something is "premium" unless the data actually supports that description.
- If no suitable item exists, say that clearly.
- Keep the answer concise and structured.
- When responding in Hebrew, keep the explanation natural and not literal or robotic.

{price_behavior_instruction}

{format_instruction}

Store context:
{context}

User request:
{user_prompt}
""".strip()

def build_semantic_answer_prompt(user_prompt: str, items: list[dict]) -> str:
    context = build_store_context(items)
    language_instruction = get_response_language_instruction(user_prompt)

    return f"""
You are a shopping assistant answering questions about store products.

{language_instruction}

Rules:
- Use only the provided store context.
- Do not invent facts.
- If the answer is not supported by the data, say so clearly.
- When relevant, mention price and stock exactly as shown.
- Keep the answer direct, useful, and concise.
- When responding in Hebrew, write natural Hebrew.

Store context:
{context}

User question:
{user_prompt}
""".strip()