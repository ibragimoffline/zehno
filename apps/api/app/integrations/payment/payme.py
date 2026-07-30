from __future__ import annotations

import base64
import logging
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

ERR_TRANSACTION_NOT_FOUND = -31003
ERR_INVALID_AMOUNT = -31001
ERR_ORDER_NOT_FOUND = -31050
ERR_UNAUTHORIZED = -32504
ERR_INVALID_REQUEST = -32600


class PaymeProvider(PaymentProvider):
    provider_name = "payme"
    display_name = "Payme"

    def is_configured(self) -> bool:
        return bool(settings.PAYME_MERCHANT_ID and settings.PAYME_MERCHANT_KEY)

    async def create_invoice(self, request: InvoiceRequest) -> InvoiceResult:
        amount_tiyin = int(Decimal(request.amount) * 100)
        params = [
            f"m={settings.PAYME_MERCHANT_ID}",
            f"ac.order_id={request.order_id}",
            f"a={amount_tiyin}",
            "l=uz",
        ]
        if request.return_url:
            params.append(f"c={request.return_url}")

        encoded = base64.b64encode(";".join(params).encode()).decode()
        checkout_url = f"{settings.PAYME_CHECKOUT_URL.rstrip('/')}/{encoded}"
        return InvoiceResult(
            checkout_url=checkout_url,
            provider_meta={"amount_tiyin": amount_tiyin, "sandbox": settings.PAYMENT_SANDBOX},
        )

    def _check_auth(self, headers: dict[str, str]) -> bool:
        auth = headers.get("authorization") or headers.get("Authorization") or ""
        if not auth.lower().startswith("basic "):
            return False
        try:
            decoded = base64.b64decode(auth[6:]).decode()
        except (ValueError, UnicodeDecodeError):
            return False
        login, _, password = decoded.partition(":")
        return login == "Paycom" and password == (settings.PAYME_MERCHANT_KEY or "")

    async def parse_webhook(self, payload: dict, headers: dict[str, str]) -> WebhookResult:
        request_id = payload.get("id")
        method = payload.get("method")
        params = payload.get("params") or {}

        if not self._check_auth(headers):
            logger.warning("Payme webhook: imzo/auth xato")
            return WebhookResult(
                order_id=None,
                status=PaymentStatus.failed,
                provider_response=_error(request_id, ERR_UNAUTHORIZED, "Ruxsat berilmadi"),
                raw=payload,
            )

        account = params.get("account") or {}
        order_id = account.get("order_id")
        transaction_id = params.get("id")
        amount = Decimal(params.get("amount", 0)) / 100 if params.get("amount") else None

        if method == "CheckPerformTransaction":
            return WebhookResult(
                order_id=order_id,
                status=PaymentStatus.pending,
                transaction_id=transaction_id,
                amount=amount,
                provider_response={"id": request_id, "result": {"allow": True}},
                raw=payload,
            )

        if method == "CreateTransaction":
            return WebhookResult(
                order_id=order_id,
                status=PaymentStatus.pending,
                transaction_id=transaction_id,
                amount=amount,
                provider_response={
                    "id": request_id,
                    "result": {
                        "create_time": params.get("time"),
                        "transaction": str(transaction_id),
                        "state": 1,
                    },
                },
                raw=payload,
            )

        if method == "PerformTransaction":
            return WebhookResult(
                order_id=order_id,
                status=PaymentStatus.paid,
                transaction_id=transaction_id,
                amount=amount,
                should_fulfill=True,
                provider_response={
                    "id": request_id,
                    "result": {
                        "perform_time": params.get("time"),
                        "transaction": str(transaction_id),
                        "state": 2,
                    },
                },
                raw=payload,
            )

        if method == "CancelTransaction":
            return WebhookResult(
                order_id=order_id,
                status=PaymentStatus.cancelled,
                transaction_id=transaction_id,
                provider_response={
                    "id": request_id,
                    "result": {
                        "cancel_time": params.get("time"),
                        "transaction": str(transaction_id),
                        "state": -1,
                    },
                },
                raw=payload,
            )

        if method == "CheckTransaction":
            return WebhookResult(
                order_id=order_id,
                status=PaymentStatus.pending,
                transaction_id=transaction_id,
                provider_response={
                    "id": request_id,
                    "result": {"transaction": str(transaction_id), "state": 2},
                },
                raw=payload,
            )

        return WebhookResult(
            order_id=order_id,
            status=PaymentStatus.failed,
            provider_response=_error(request_id, ERR_INVALID_REQUEST, f"Noma'lum metod: {method}"),
            raw=payload,
        )


def _error(request_id, code: int, message: str) -> dict:
    return {
        "id": request_id,
        "error": {"code": code, "message": {"uz": message, "ru": message, "en": message}},
    }
