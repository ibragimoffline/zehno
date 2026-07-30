from __future__ import annotations

import logging
import uuid
from decimal import Decimal

from app.core.config import settings
from app.integrations.payment.base import (
    InvoiceRequest,
    InvoiceResult,
    PaymentProvider,
    WebhookResult,
)
from app.models.enums import PaymentStatus

logger = logging.getLogger(__name__)


class MockPaymentProvider(PaymentProvider):
    provider_name = "mock"
    display_name = "Mock to'lov (sandbox)"

    async def create_invoice(self, request: InvoiceRequest) -> InvoiceResult:
        transaction_id = f"mock-{uuid.uuid4().hex[:12]}"
        checkout_url = (
            f"{settings.PUBLIC_WEB_URL.rstrip('/')}/checkout/mock"
            f"?order_id={request.order_id}&amount={request.amount}&txn={transaction_id}"
        )
        logger.info("[mock-pay] invoys yaratildi: %s → %s", request.order_number, request.amount)
        return InvoiceResult(checkout_url=checkout_url, transaction_id=transaction_id)

    async def parse_webhook(self, payload: dict, headers: dict[str, str]) -> WebhookResult:
        order_id = payload.get("order_id")
        succeed = bool(payload.get("success", True))
        amount = payload.get("amount")
        return WebhookResult(
            order_id=str(order_id) if order_id else None,
            status=PaymentStatus.paid if succeed else PaymentStatus.failed,
            transaction_id=str(payload.get("transaction_id") or f"mock-{uuid.uuid4().hex[:12]}"),
            amount=Decimal(str(amount)) if amount is not None else None,
            should_fulfill=succeed,
            provider_response={"ok": True},
            raw=payload,
        )

    async def refund(self, transaction_id: str, amount: Decimal) -> bool:
        logger.info("[mock-pay] refund: %s (%s)", transaction_id, amount)
        return True
