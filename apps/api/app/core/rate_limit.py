import logging
import time
from typing import Annotated

from fastapi import Depends, Request

from app.core.config import settings
from app.core.exceptions import RateLimitError
from app.core.redis_client import get_redis

logger = logging.getLogger(__name__)

_UNITS = {
    "second": 1,
    "seconds": 1,
    "minute": 60,
    "minutes": 60,
    "hour": 3600,
    "hours": 3600,
    "day": 86_400,
    "days": 86_400,
}


def parse_rate(rate: str) -> tuple[int, int]:
    try:
        raw_limit, _, raw_unit = rate.strip().partition("/")
        return int(raw_limit), _UNITS[raw_unit.strip().lower()]
    except (ValueError, KeyError):
        logger.warning("Rate limit formati noto'g'ri: %r — default 60/minute", rate)
        return 60, 60


def client_identity(request: Request) -> str:
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        return f"token:{auth[7:][:48]}"

    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return f"ip:{forwarded.split(',')[0].strip()}"
    return f"ip:{request.client.host if request.client else 'unknown'}"


class RateLimit:
    def __init__(self, rate: str, scope: str) -> None:
        self.limit, self.window = parse_rate(rate)
        self.scope = scope

    async def __call__(self, request: Request) -> None:
        if not settings.RATE_LIMIT_ENABLED:
            return

        bucket = int(time.time() // self.window)
        key = f"ratelimit:{self.scope}:{client_identity(request)}:{bucket}"

        try:
            client = get_redis()
            count = await client.incr(key)
            if count == 1:
                await client.expire(key, self.window + 1)
        except Exception as exc:
            logger.debug("Rate limit tekshiruvi o'tkazib yuborildi: %s", exc)
            return

        if count > self.limit:
            raise RateLimitError(
                f"So'rovlar soni chegarasidan oshdi ({self.limit}/{self.window}s). "
                "Bir oz kuting va qayta urinib ko'ring."
            )


auth_rate_limit = RateLimit(settings.RATE_LIMIT_AUTH, scope="auth")

default_rate_limit = RateLimit(settings.RATE_LIMIT_DEFAULT, scope="default")

AuthRateLimit = Annotated[None, Depends(auth_rate_limit)]
DefaultRateLimit = Annotated[None, Depends(default_rate_limit)]
