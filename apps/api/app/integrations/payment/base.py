"""PaymentProvider interfeysi."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from decimal import Decimal

from app.integrations.base import IntegrationAdapter
from app.models.enums import IntegrationKind, PaymentStatus


@dataclass(slots=True)
class InvoiceRequest:
    order_id: str
    order_number: str
    amount: Decimal
    currency: str = "UZS"
    description: str | None = None
    return_url: str | None = None
    user_email: str | None = None
    user_phone: str | None = None


@dataclass(slots=True)
class InvoiceResult:
    """To'lov sahifasiga yo'naltirish uchun natija."""

    checkout_url: str
    transaction_id: str | None = None
    provider_meta: dict = field(default_factory=dict)


@dataclass(slots=True)
class WebhookResult:
    """Webhook'ni tahlil qilish natijasi.

    `provider_response` — provayderga qaytarilishi kerak bo'lgan JSON (Payme JSON-RPC
    va Click uchun format qat'iy belgilangan).
    """

    order_id: str | None
    status: PaymentStatus
    transaction_id: str | None = None
    amount: Decimal | None = None
    provider_response: dict = field(default_factory=dict)
    raw: dict = field(default_factory=dict)
    should_fulfill: bool = False


class PaymentProvider(IntegrationAdapter, abc.ABC):
    kind = IntegrationKind.payment

    @abc.abstractmethod
    async def create_invoice(self, request: InvoiceRequest) -> InvoiceResult:
        """Invoys yaratadi va checkout URL qaytaradi."""

    @abc.abstractmethod
    async def parse_webhook(self, payload: dict, headers: dict[str, str]) -> WebhookResult:
        """Webhook'ni tekshiradi (imzo!) va normallashtirilgan natija qaytaradi."""

    async def refund(self, transaction_id: str, amount: Decimal) -> bool:
        """Ixtiyoriy: to'lovni qaytarish."""
        raise NotImplementedError(f"{self.display_name} uchun refund qo'llab-quvvatlanmaydi")
