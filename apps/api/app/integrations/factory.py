"""IntegrationFactory — `.env` dagi o'zgaruvchi bo'yicha mos adapterni beradi.

`ARCHITECTURE.md` 6-bo'lim: provayderni almashtirish uchun faqat `.env` o'zgaradi,
biznes-logikaga tegilmaydi.

    VIDEO_PROVIDER=peertube      → PeerTubeProvider
    PAYMENT_PROVIDER=payme       → PaymeProvider
    CRM_PROVIDER=bitrix24        → Bitrix24Provider
"""

from __future__ import annotations

import logging
from functools import lru_cache

from app.core.config import settings
from app.core.exceptions import IntegrationError
from app.integrations.crm.base import CrmProvider
from app.integrations.crm.bitrix24 import Bitrix24Provider
from app.integrations.crm.espocrm import EspoCrmProvider
from app.integrations.crm.mock import MockCrmProvider
from app.integrations.notification.base import NotificationProvider
from app.integrations.notification.telegram import TelegramProvider
from app.integrations.payment.base import PaymentProvider
from app.integrations.payment.click import ClickProvider
from app.integrations.payment.mock import MockPaymentProvider
from app.integrations.payment.payme import PaymeProvider
from app.integrations.video.base import VideoProvider
from app.integrations.video.bunny import BunnyStreamProvider
from app.integrations.video.kinescope import KinescopeProvider
from app.integrations.video.mock import MockVideoProvider
from app.integrations.video.peertube import PeerTubeProvider

logger = logging.getLogger(__name__)

VIDEO_PROVIDERS: dict[str, type[VideoProvider]] = {
    "mock": MockVideoProvider,
    "peertube": PeerTubeProvider,
    "kinescope": KinescopeProvider,
    "bunny": BunnyStreamProvider,
}

PAYMENT_PROVIDERS: dict[str, type[PaymentProvider]] = {
    "mock": MockPaymentProvider,
    "payme": PaymeProvider,
    "click": ClickProvider,
}

CRM_PROVIDERS: dict[str, type[CrmProvider]] = {
    "mock": MockCrmProvider,
    "bitrix24": Bitrix24Provider,
    "espocrm": EspoCrmProvider,
}


@lru_cache
def get_video_provider(name: str | None = None) -> VideoProvider:
    key = (name or settings.VIDEO_PROVIDER).lower()
    provider_cls = VIDEO_PROVIDERS.get(key)
    if provider_cls is None:
        raise IntegrationError(
            f"Noma'lum video provayder: '{key}'. Mavjud: {', '.join(VIDEO_PROVIDERS)}"
        )
    return provider_cls()


@lru_cache
def get_payment_provider(name: str | None = None) -> PaymentProvider:
    key = (name or settings.PAYMENT_PROVIDER).lower()
    provider_cls = PAYMENT_PROVIDERS.get(key)
    if provider_cls is None:
        raise IntegrationError(
            f"Noma'lum to'lov provayderi: '{key}'. Mavjud: {', '.join(PAYMENT_PROVIDERS)}"
        )
    return provider_cls()


@lru_cache
def get_crm_provider(name: str | None = None) -> CrmProvider:
    key = (name or settings.CRM_PROVIDER).lower()
    provider_cls = CRM_PROVIDERS.get(key)
    if provider_cls is None:
        raise IntegrationError(
            f"Noma'lum CRM provayderi: '{key}'. Mavjud: {', '.join(CRM_PROVIDERS)}"
        )
    return provider_cls()


@lru_cache
def get_notification_provider() -> NotificationProvider:
    return TelegramProvider()


def all_adapters() -> list[object]:
    """Super-admin monitoringi uchun barcha faol adapterlar."""
    adapters: list[object] = []
    for getter in (
        get_video_provider,
        get_payment_provider,
        get_crm_provider,
        get_notification_provider,
    ):
        try:
            adapters.append(getter())
        except IntegrationError as exc:
            logger.warning("Adapter yuklanmadi: %s", exc)
    return adapters


def reset_cache() -> None:
    """Testlarda yoki sozlama o'zgarganda cache'ni tozalash."""
    get_video_provider.cache_clear()
    get_payment_provider.cache_clear()
    get_crm_provider.cache_clear()
    get_notification_provider.cache_clear()
