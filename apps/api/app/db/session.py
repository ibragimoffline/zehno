"""DB ulanishlari.

Ikki xil engine mavjud:

* **async** (`asyncpg`) — FastAPI request'lari uchun (`get_db` dependency).
* **sync** (`psycopg`) — Celery worker'lari va CLI skriptlari uchun; Celery
  task'lari sinxron bo'lgani uchun har bir task uchun `asyncio.run()` chaqirish
  o'rniga to'g'ridan-to'g'ri sinxron sessiya ishlatiladi.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# ---------------------------------------------------------------- async
async_engine = create_async_engine(
    settings.async_database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — request davomida bitta sessiya."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------- sync
sync_engine = create_engine(
    settings.sync_database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SyncSessionLocal = sessionmaker(bind=sync_engine, expire_on_commit=False, autoflush=False)


@contextmanager
def sync_session() -> Generator[Session, None, None]:
    """Celery task'lari uchun kontekst menejer."""
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
