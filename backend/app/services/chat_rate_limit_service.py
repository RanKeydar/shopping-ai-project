from __future__ import annotations

from app.cache.redis_client import get_redis
from app.core.config import settings


def _chat_limit_key(identifier: str) -> str:
    return f"chat_limit:{identifier}"


async def get_remaining_prompts(identifier: str) -> int:
    redis = get_redis()
    key = _chat_limit_key(identifier)

    current = await redis.get(key)
    if current is None:
        await redis.set(
            key,
            settings.CHAT_SESSION_LIMIT,
            ex=settings.CHAT_SESSION_TTL_SECONDS,
        )
        return settings.CHAT_SESSION_LIMIT

    try:
        return max(0, int(current))
    except (TypeError, ValueError):
        await redis.set(
            key,
            settings.CHAT_SESSION_LIMIT,
            ex=settings.CHAT_SESSION_TTL_SECONDS,
        )
        return settings.CHAT_SESSION_LIMIT


async def consume_prompt(identifier: str) -> int:
    redis = get_redis()
    key = _chat_limit_key(identifier)

    current = await get_remaining_prompts(identifier)

    if current <= 0:
        return 0

    remaining = current - 1

    await redis.set(
        key,
        remaining,
        ex=settings.CHAT_SESSION_TTL_SECONDS,
    )

    return remaining