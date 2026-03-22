from app.services.chat.prompts import (
    build_system_prompt,
    build_user_message,
    detect_user_language,
)


def generate_gpt_answer(user_prompt: str, subset_context: str, client) -> str:
    user_language = detect_user_language(user_prompt)
    system_prompt = build_system_prompt(user_language)
    user_message = build_user_message(user_prompt, subset_context)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )

    return response.choices[0].message.content.strip()