"""Yordamchi CLI buyruqlari (Docker entrypoint va lokal ishlab chiqish uchun).

python -m app.cli wait-for-services   # postgres + redis tayyor bo'lishini kutadi
python -m app.cli migrate             # (kerak bo'lsa generatsiya qilib) migratsiyalarni qo'llaydi
python -m app.cli ensure-bucket       # MinIO/S3 bucket'ini yaratadi
python -m app.cli seed                # kategoriya, super-admin, demo kontent
python -m app.cli create-superadmin   # faqat super-admin
python -m app.cli reset-db            # DIQQAT: barcha jadvallarni o'chiradi
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import time

from sqlalchemy import text

from app.core.config import settings
from app.core.logging import setup_logging

setup_logging()
logger = logging.getLogger("app.cli")


def wait_for_services(timeout: int = 90) -> int:
    """Postgres va Redis ko'tarilishini kutadi (Docker Compose uchun)."""
    import psycopg
    import redis

    deadline = time.time() + timeout

    # ---- PostgreSQL ----
    dsn = settings.sync_database_url.replace("postgresql+psycopg://", "postgresql://")
    while True:
        try:
            with psycopg.connect(dsn, connect_timeout=3) as conn:
                conn.execute("SELECT 1")
            logger.info("PostgreSQL tayyor")
            break
        except Exception as exc:
            if time.time() > deadline:
                logger.error("PostgreSQL kutish vaqti tugadi: %s", exc)
                return 1
            logger.info("PostgreSQL kutilmoqda...")
            time.sleep(2)

    # ---- Redis ----
    while True:
        try:
            client = redis.Redis.from_url(settings.redis_dsn, socket_connect_timeout=3)
            client.ping()
            client.close()
            logger.info("Redis tayyor")
            break
        except Exception as exc:
            if time.time() > deadline:
                logger.error("Redis kutish vaqti tugadi: %s", exc)
                return 1
            logger.info("Redis kutilmoqda...")
            time.sleep(2)

    return 0


def migrate() -> int:
    """Migratsiyalarni qo'llaydi.

    Birinchi ishga tushirishda (`alembic/versions` bo'sh bo'lsa) modellar asosida
    boshlang'ich migratsiya avtomatik generatsiya qilinadi — fayl repozitoriyada
    saqlanib qoladi va keyingi o'zgarishlar unga nisbatan hisoblanadi.
    """
    from pathlib import Path

    from alembic.config import Config

    from alembic import command

    api_root = Path(__file__).resolve().parents[1]
    cfg = Config(str(api_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(api_root / "alembic"))

    versions_dir = api_root / "alembic" / "versions"
    versions_dir.mkdir(parents=True, exist_ok=True)
    has_revisions = any(path.suffix == ".py" for path in versions_dir.glob("*.py"))

    if not has_revisions:
        logger.info("Migratsiya topilmadi — boshlang'ich migratsiya generatsiya qilinmoqda")
        command.revision(cfg, message="initial schema", autogenerate=True)

    command.upgrade(cfg, "head")
    logger.info("Migratsiyalar qo'llanildi")
    return 0


def seed(demo: bool = True) -> int:
    from app.db.seed import run_seed

    asyncio.run(run_seed(with_demo=demo))
    return 0


def create_superadmin() -> int:
    from app.db.seed import ensure_superadmin

    asyncio.run(ensure_superadmin())
    return 0


def reset_db() -> int:
    from app.db.session import sync_engine

    logger.warning("DIQQAT: `public` sxemasi to'liq o'chiriladi!")
    with sync_engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    logger.info("Sxema tozalandi. Endi `alembic upgrade head` ni ishga tushiring.")
    return 0


def ensure_bucket() -> int:
    from app.integrations.storage.s3 import StorageService

    StorageService().ensure_bucket()
    return 0


COMMANDS = {
    "wait-for-services": lambda args: wait_for_services(args.timeout),
    "migrate": lambda _: migrate(),
    "seed": lambda args: seed(demo=not args.no_demo),
    "create-superadmin": lambda _: create_superadmin(),
    "reset-db": lambda _: reset_db(),
    "ensure-bucket": lambda _: ensure_bucket(),
}


def main() -> int:
    parser = argparse.ArgumentParser(prog="zehno", description="Zehno.uz API CLI")
    parser.add_argument("command", choices=sorted(COMMANDS))
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--no-demo", action="store_true", help="Demo kontentni yaratmaslik")
    args = parser.parse_args()
    return COMMANDS[args.command](args) or 0


if __name__ == "__main__":
    sys.exit(main())
