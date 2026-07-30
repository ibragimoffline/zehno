"""Telegram Bot API adapteri (doim bepul).

Xabarlar Celery worker orqali navbatga qo'yiladi — asosiy API bloklanmaydi
(`ARCHITECTURE.md` 6.4).
"""

from __future__ import annotations

import logging

from app.core.config import settings
from app.core.exceptions import IntegrationError
from app.integrations.notification.base import NotificationMessage, NotificationProvider
from app.models.enums import NotificationChannel

logger = logging.getLogger(__name__)

API_BASE = "https://api.telegram.org"


class TelegramProvider(NotificationProvider):
    provider_name = "telegram"
    display_name = "Telegram Bot"
    channel = NotificationChannel.telegram

    def is_configured(self) -> bool:
        return bool(settings.TELEGRAM_ENABLED and settings.TELEGRAM_BOT_TOKEN)

    @property
    def _api(self) -> str:
        if not settings.TELEGRAM_BOT_TOKEN:
            raise IntegrationError("Telegram bot tokeni sozlanmagan", provider=self.provider_name)
        return f"{API_BASE}/bot{settings.TELEGRAM_BOT_TOKEN}"

    async def send(self, message: NotificationMessage) -> bool:
        if not self.is_configured():
            logger.info("[telegram] o'chirilgan — xabar yuborilmadi: %s", message.recipient)
            return False

        payload: dict = {
            "chat_id": message.recipient,
            "text": message.body,
            "disable_notification": message.disable_notification,
        }
        if message.parse_mode:
            payload["parse_mode"] = message.parse_mode
        if message.buttons:
            payload["reply_markup"] = {"inline_keyboard": [message.buttons]}

        await self._request("POST", f"{self._api}/sendMessage", json=payload)
        return True

    async def get_updates(self, offset: int | None = None, timeout: int = 25) -> list[dict]:
        """Long-polling — `app.bot.main` workeri uchun."""
        params: dict = {"timeout": timeout}
        if offset is not None:
            params["offset"] = offset
        response = await self._request(
            "GET", f"{self._api}/getUpdates", params=params, timeout=timeout + 10
        )
        return response.json().get("result", [])

    async def set_webhook(self, url: str) -> bool:
        payload = {"url": url}
        if settings.TELEGRAM_WEBHOOK_SECRET:
            payload["secret_token"] = settings.TELEGRAM_WEBHOOK_SECRET
        await self._request("POST", f"{self._api}/setWebhook", json=payload)
        return True

    async def delete_webhook(self) -> bool:
        await self._request("POST", f"{self._api}/deleteWebhook")
        return True

    async def healthcheck(self) -> tuple[bool, str | None]:
        if not self.is_configured():
            return False, "Telegram o'chirilgan yoki token yo'q"
        try:
            await self._request("GET", f"{self._api}/getMe")
            return True, None
        except IntegrationError as exc:
            return False, str(exc)
