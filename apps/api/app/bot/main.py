from __future__ import annotations

import asyncio
import logging

from sqlalchemy import func, select

import app.models  # noqa: F401
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import AsyncSessionLocal
from app.integrations.notification.telegram import TelegramProvider
from app.models.enums import EnrollmentStatus
from app.models.learning import Enrollment
from app.models.user import User

setup_logging()
logger = logging.getLogger("app.bot")

WELCOME = (
    "👋 <b>Zehno.uz botiga xush kelibsiz!</b>\n\n"
    "Bu bot orqali siz:\n"
    "• yangi darslar va deadline'lar haqida eslatma olasiz\n"
    "• to'lov tasdiqlangani haqida xabar olasiz\n"
    "• sertifikat tayyor bo'lganda birinchi bo'lib bilasiz\n\n"
    "Hisobingizni ulash uchun saytdagi <b>Profil → Telegram</b> bo'limidan kodni oling "
    "va shu yerga yuboring:\n<code>/start KOD</code>"
)

HELP = (
    "<b>Buyruqlar</b>\n"
    "/start [kod] — hisobni ulash\n"
    "/progress — kurslar progressini ko'rish\n"
    "/help — yordam\n"
    "/stop — bildirishnomalarni o'chirish"
)


async def link_account(link_code: str, chat_id: str) -> str:
    async with AsyncSessionLocal() as db:
        user = await db.scalar(select(User).where(User.telegram_link_code == link_code))
        if user is None:
            return "❌ Bunday kod topilmadi. Saytdan yangi kod oling."

        user.telegram_chat_id = str(chat_id)
        user.telegram_link_code = None
        await db.commit()
        return (
            f"✅ Hisob ulandi: <b>{user.full_name}</b>\n\n"
            "Endi barcha muhim xabarlarni shu yerda olasiz."
        )


async def progress_summary(chat_id: str) -> str:
    async with AsyncSessionLocal() as db:
        user = await db.scalar(select(User).where(User.telegram_chat_id == str(chat_id)))
        if user is None:
            return "Hisob ulanmagan. /start KOD orqali ulang."

        rows = await db.execute(
            select(
                func.count(Enrollment.id),
                func.coalesce(func.avg(Enrollment.progress_percent), 0),
            ).where(Enrollment.user_id == user.id)
        )
        total, avg = rows.one()
        completed = await db.scalar(
            select(func.count(Enrollment.id)).where(
                Enrollment.user_id == user.id, Enrollment.status == EnrollmentStatus.completed
            )
        )
        return (
            f"📊 <b>{user.full_name}</b>\n\n"
            f"Kurslar: {int(total or 0)}\n"
            f"O'rtacha progress: {int(round(float(avg or 0)))}%\n"
            f"Tugatilgan: {int(completed or 0)}\n\n"
            f"{settings.PUBLIC_WEB_URL}/dashboard"
        )


async def disable_notifications(chat_id: str) -> str:
    async with AsyncSessionLocal() as db:
        user = await db.scalar(select(User).where(User.telegram_chat_id == str(chat_id)))
        if user is None:
            return "Hisob ulanmagan."
        user.telegram_chat_id = None
        await db.commit()
        return "🔕 Bildirishnomalar o'chirildi. Qayta ulash uchun /start KOD."


async def handle_update(provider: TelegramProvider, update: dict) -> None:
    message = update.get("message") or update.get("edited_message")
    if not message:
        return

    chat_id = str((message.get("chat") or {}).get("id"))
    text = (message.get("text") or "").strip()
    if not chat_id or not text:
        return

    if text.startswith("/start"):
        parts = text.split(maxsplit=1)
        reply = await link_account(parts[1].strip().upper(), chat_id) if len(parts) > 1 else WELCOME
    elif text.startswith("/progress"):
        reply = await progress_summary(chat_id)
    elif text.startswith("/stop"):
        reply = await disable_notifications(chat_id)
    elif text.startswith("/help"):
        reply = HELP
    else:
        reply = "Buyruqni tushunmadim. /help — yordam."

    from app.integrations.notification.base import NotificationMessage

    await provider.send(NotificationMessage(recipient=chat_id, body=reply))


async def run() -> None:
    provider = TelegramProvider()
    if not provider.is_configured():
        logger.warning(
            "Telegram bot o'chirilgan (TELEGRAM_ENABLED/TELEGRAM_BOT_TOKEN). "
            "Worker kutish rejimida ishlaydi."
        )
        while True:  # noqa: ASYNC110 - konteyner tirik qolishi uchun ataylab
            await asyncio.sleep(300)

    ok, error = await provider.healthcheck()
    if not ok:
        logger.error("Telegram bot ulanmadi: %s", error)

    logger.info("Telegram bot ishga tushdi (long-polling)")
    offset: int | None = None

    while True:
        try:
            updates = await provider.get_updates(offset=offset, timeout=25)
            for update in updates:
                offset = int(update["update_id"]) + 1
                try:
                    await handle_update(provider, update)
                except Exception:
                    logger.exception("Update qayta ishlanmadi: %s", update.get("update_id"))
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("getUpdates xatolik: %s — 5 sekunddan keyin qayta urinaman", exc)
            await asyncio.sleep(5)


def main() -> None:
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi")


if __name__ == "__main__":
    main()
