import os
from typing import Optional

from redis.asyncio import Redis
from redis.asyncio import from_url

_redis: Optional[Redis] = None

def get_redis() -> Redis:
    global _redis
    if _redis is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis = from_url(redis_url, encoding="utf-8", decode_responses=True)
    return _redis