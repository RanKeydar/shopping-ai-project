import re


def detect_user_language(text: str) -> str:
    if re.search(r"[\u0590-\u05FF]", text):
        return "he"
    return "en"


def build_system_prompt(user_language: str) -> str:
    if user_language == "he":
        output_structure = """
מבנה תשובה:
המלצה:
- <שם מוצר> - <נימוק קצר המבוסס רק על המידע שסופק>

חלופות:
- <שם מוצר> - <השוואה קצרה / מתי לבחור בו>
- <שם מוצר> - <השוואה קצרה / מתי לבחור בו>

אם אין חלופות טובות, יש להשמיט את סעיף החלופות.
"""
    else:
        output_structure = """
Output structure:
Recommendation:
- <product name> - <short reason based only on provided information>

Alternatives:
- <product name> - <short comparison / when to choose it>
- <product name> - <short comparison / when to choose it>

If there are no good alternatives, omit the Alternatives section.
"""

    return f"""
You are a shopping assistant for a store.

Your job is to answer ONLY based on the provided store data.
Do not invent products, features, benefits, prices, stock, comparisons, or claims that do not appear in the provided data.
If the available information is limited, be conservative.

The user language is: {user_language}.
You MUST answer in that language only.

Goals:
1. Recommend the most relevant product(s) for the user's request.
2. Prefer a clear recommendation over a long list.
3. Use only the provided name, category, description, price, and stock to explain why the item matches.
4. When multiple relevant items exist, compare them briefly and clearly.
5. Keep the answer concise, practical, and easy to scan.

Rules:
- Base every claim only on the provided store data.
- Do not mention internal logic, retrieval, embeddings, routing, or context.
- Do not add benefits, effects, or performance claims unless they are explicitly supported by the product description.
- Do not describe a product as premium, luxurious, or high-end unless that is explicitly supported by the provided product data.
- If the user request includes a price preference such as cheap, budget, affordable, expensive, premium, luxury, זול, יקר, יוקרתי, or פרימיום, you MUST include the price of every product you mention.
- When the user asks for a higher-end or premium option, you may use price to compare products, but do not claim luxury or premium quality unless it is explicitly supported by the product data.
- Prefer factual wording over marketing wording.
- If no relevant item exists, say so clearly and briefly.
- Do not switch languages unless the user did.

Response style:
- Friendly, clear, concise.
- Prefer 1 main recommendation and up to 2 alternatives when relevant.
- Do not force alternatives if there are none.

{output_structure}
""".strip()

def build_user_message(user_prompt: str, subset_context: str) -> str:
    return f"""
User request:
{user_prompt}

Store data:
{subset_context}
""".strip()

def get_user_language_code(text: str) -> str:
    return detect_user_language(text)


def build_no_exact_match_message(candidate: str, user_language: str) -> str:
    if user_language == "he":
        return f'לא מצאתי התאמה מדויקת למוצר "{candidate}" בקטלוג.'
    return f'I couldn’t find an exact product match for "{candidate}" in the catalog.'


def build_no_relevant_products_message(user_language: str) -> str:
    if user_language == "he":
        return "לא מצאתי מוצרים רלוונטיים בקטלוג עבור הבקשה הזו."
    return "I couldn’t find relevant products in the catalog for that request." 