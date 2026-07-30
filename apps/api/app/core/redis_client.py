from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis

from app.core.config import settings

_pool: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _pool
    if _pool is None:
        _pool = aioredis.from_url(
            settings.redis_dsn,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
    return _pool


async def close_redis() -> None:
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None


async def cache_get_json(key: str) -> Any | None:
    raw = await get_redis().get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


async def cache_set_json(key: str, value: Any, ttl_seconds: int = 300) -> None:
    await get_redis().set(key, json.dumps(value, default=str), ex=ttl_seconds)


async def cache_delete_prefix(prefix: str) -> int:
    client = get_redis()
    deleted = 0
    async for key in client.scan_iter(match=f"{prefix}*", count=200):
        await client.delete(key)
        deleted += 1
    return deleted
