from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlalchemy import text

import app.models  # noqa: F401
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.core.redis_client import close_redis, get_redis
from app.db.session import async_engine

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "%s API ishga tushmoqda (env=%s, video=%s, payment=%s, crm=%s)",
        settings.APP_NAME,
        settings.APP_ENV,
        settings.VIDEO_PROVIDER,
        settings.PAYMENT_PROVIDER,
        settings.CRM_PROVIDER,
    )
    yield
    await async_engine.dispose()
    await close_redis()
    logger.info("API to'xtatildi")


app = FastAPI(
    title="Zehno.uz API",
    description=(
        "Onlayn ta'lim marketplace platformasi — maktablar, xususiy ustozlar va "
        "o'quv markazlari uchun kurs sotish, videodarslik, test, sertifikat va "
        "B2B (CRM integratsiyali) nazorat paneli."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    contact={"name": "Zehno.uz", "url": settings.PUBLIC_WEB_URL},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


register_exception_handlers(app)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["System"], summary="Healthcheck")
async def health() -> dict:
    db_ok = True
    redis_ok = True

    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        db_ok = False
        logger.warning("Healthcheck: DB xato — %s", exc)

    try:
        await get_redis().ping()
    except Exception as exc:
        redis_ok = False
        logger.warning("Healthcheck: Redis xato — %s", exc)

    return {
        "status": "ok" if db_ok and redis_ok else "degraded",
        "app": settings.APP_NAME,
        "env": settings.APP_ENV.value,
        "version": app.version,
        "database": "ok" if db_ok else "error",
        "redis": "ok" if redis_ok else "error",
        "providers": {
            "video": settings.VIDEO_PROVIDER,
            "payment": settings.PAYMENT_PROVIDER,
            "crm": settings.CRM_PROVIDER,
            "telegram": settings.TELEGRAM_ENABLED,
        },
    }


@app.get("/", tags=["System"], summary="API haqida")
async def root() -> dict:
    return {
        "name": "Zehno.uz API",
        "version": app.version,
        "docs": "/docs",
        "api": settings.API_V1_PREFIX,
    }
