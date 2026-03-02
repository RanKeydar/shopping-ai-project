from redis.asyncio import Redis

async def invalidate_items_list_cache(redis: Redis) -> None:
    async for key in redis.scan_iter(match="items:/items*"):
        await redis.delete(key)