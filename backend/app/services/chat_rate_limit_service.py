from __future__ import annotations

import os

import redis


REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

CHAT_LIMIT = 5
CHAT_WINDOW_SECONDS = 60 * 60  # שעה


def _build_key(identifier: str) -> str:
    return f"chat_limit:{identifier}"


def get_remaining_prompts(identifier: str) -> int:
    key = _build_key(identifier)
    current = redis_client.get(key)

    used = int(current) if current is not None else 0
    return max(0, CHAT_LIMIT - used)


def has_remaining_prompts(identifier: str) -> bool:
    return get_remaining_prompts(identifier) > 0


def consume_prompt(identifier: str) -> int:
    key = _build_key(identifier)

    used = redis_client.incr(key)

    if used == 1:
        redis_client.expire(key, CHAT_WINDOW_SECONDS)

    return max(0, CHAT_LIMIT - used)