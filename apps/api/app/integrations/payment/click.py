"""Click Merchant API adapteri (Prepare / Complete oqimi).

Click ikki bosqichda ishlaydi:
1. **Prepare** (`action=0`) — buyurtma mavjudligi va summasi tekshiriladi.
2. **Complete** (`action=1`) — to'lov yakunlanadi, kursga kirish ochiladi.

Imzo (`sign_string`) MD5 orqali tekshiriladi.
"""

from __future__ import annotations

import hashlib
import logging
from decimal import Decimal
from urllib.parse import urlencode

from app.core.config import settings
from app.integrations.payment.base import (
    InvoiceRequest,
    InvoiceResult,
    PaymentProvider,
    WebhookResult,
)
from app.models.enums import PaymentStatus

logger = logging.getLogger(__name__)

ACTION_PREPARE = 0
ACTION_COMPLETE = 1

# Click xato kodlari
ERR_SUCCESS = 0
ERR_SIGN_CHECK_FAILED = -1
ERR_INCORRECT_AMOUNT = -2
ERR_ACTION_NOT_FOUND = -3
ERR_ALREADY_PAID = -4
ERR_ORDER_NOT_FOUND = -5
ERR_TRANSACTION_CANCELLED = -9


class ClickProvider(PaymentProvider):
    provider_name = "click"
    display_name = "Click"

    def is_configured(self) -> bool:
        return bool(
            settings.CLICK_MERCHANT_ID and settings.CLICK_SERVICE_ID and settings.CLICK_SECRET_KEY
        )

    async def create_invoice(self, request: InvoiceRequest) -> InvoiceResult:
        params = {
            "service_id": settings.CLICK_SERVICE_ID or "",
            "merchant_id": settings.CLICK_MERCHANT_ID or "",
            "amount": str(Decimal(request.amount)),
            "transaction_param": request.order_id,
        }
        if request.return_url:
            params["return_url"] = request.return_url

        checkout_url = f"{settings.CLICK_CHECKOUT_URL.rstrip('/')}/?{urlencode(params)}"
        return InvoiceResult(checkout_url=checkout_url, provider_meta=params)

    # ------------------------------------------------------------ imzo
    def _verify_sign(self, payload: dict) -> bool:
        secret = settings.CLICK_SECRET_KEY or ""
        action = str(payload.get("action", ""))
        parts = [
            str(payload.get("click_trans_id", "")),
            str(payload.get("service_id", "")),
            secret,
            str(payload.get("merchant_trans_id", "")),
        ]
        if action == str(ACTION_COMPLETE):
            parts.append(str(payload.get("merchant_prepare_id", "")))
        parts += [
            str(payload.get("amount", "")),
            action,
            str(payload.get("sign_time", "")),
        ]
        expected = hashlib.md5("".join(parts).encode()).hexdigest()  # noqa: S324 - Click talabi
        received = str(payload.get("sign_string", "")).lower()
        return expected == received

    async def parse_webhook(self, payload: dict, headers: dict[str, str]) -> WebhookResult:
        click_trans_id = payload.get("click_trans_id")
        merchant_trans_id = payload.get("merchant_trans_id")  # bizning order_id
        action = int(payload.get("action", -1))
        amount = Decimal(str(payload.get("amount", "0")))

        base_response = {
            "click_trans_id": click_trans_id,
            "merchant_trans_id": merchant_trans_id,
        }

        if not self._verify_sign(payload):
            logger.warning("Click webhook: imzo xato (order=%s)", merchant_trans_id)
            return WebhookResult(
                order_id=merchant_trans_id,
                status=PaymentStatus.failed,
                transaction_id=str(click_trans_id) if click_trans_id else None,
                provider_response={
                    **base_response,
                    "error": ERR_SIGN_CHECK_FAILED,
                    "error_note": "SIGN CHECK FAILED",
                },
                raw=payload,
            )

        if action == ACTION_PREPARE:
            return WebhookResult(
                order_id=merchant_trans_id,
                status=PaymentStatus.pending,
                transaction_id=str(click_trans_id),
                amount=amount,
                provider_response={
                    **base_response,
                    "merchant_prepare_id": merchant_trans_id,
                    "error": ERR_SUCCESS,
                    "error_note": "Success",
                },
                raw=payload,
            )

        if action == ACTION_COMPLETE:
            error_code = int(payload.get("error", 0))
            if error_code < 0:
                return WebhookResult(
                    order_id=merchant_trans_id,
                    status=PaymentStatus.cancelled,
                    transaction_id=str(click_trans_id),
                    amount=amount,
                    provider_response={
                        **base_response,
                        "merchant_confirm_id": merchant_trans_id,
                        "error": ERR_TRANSACTION_CANCELLED,
                        "error_note": "Transaction cancelled",
                    },
                    raw=payload,
                )
            return WebhookResult(
                order_id=merchant_trans_id,
                status=PaymentStatus.paid,
                transaction_id=str(click_trans_id),
                amount=amount,
                should_fulfill=True,
                provider_response={
                    **base_response,
                    "merchant_confirm_id": merchant_trans_id,
                    "error": ERR_SUCCESS,
                    "error_note": "Success",
                },
                raw=payload,
            )

        return WebhookResult(
            order_id=merchant_trans_id,
            status=PaymentStatus.failed,
            transaction_id=str(click_trans_id) if click_trans_id else None,
            provider_response={
                **base_response,
                "error": ERR_ACTION_NOT_FOUND,
                "error_note": "Action not found",
            },
            raw=payload,
        )
