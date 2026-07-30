"""To'lov adapterlari testlari — imzo tekshiruvi va webhook normallashtirish."""

from __future__ import annotations

import base64
import hashlib
from decimal import Decimal

import pytest

from app.core.config import settings
from app.integrations.payment.base import InvoiceRequest
from app.integrations.payment.click import ACTION_COMPLETE, ACTION_PREPARE, ClickProvider
from app.integrations.payment.mock import MockPaymentProvider
from app.integrations.payment.payme import PaymeProvider
from app.models.enums import PaymentStatus


@pytest.fixture
def click_credentials(monkeypatch):
    monkeypatch.setattr(settings, "CLICK_MERCHANT_ID", "1111")
    monkeypatch.setattr(settings, "CLICK_SERVICE_ID", "2222")
    monkeypatch.setattr(settings, "CLICK_SECRET_KEY", "secret-key")
    return settings


def _click_sign(payload: dict, secret: str) -> str:
    parts = [
        str(payload["click_trans_id"]),
        str(payload["service_id"]),
        secret,
        str(payload["merchant_trans_id"]),
    ]
    if str(payload["action"]) == str(ACTION_COMPLETE):
        parts.append(str(payload.get("merchant_prepare_id", "")))
    parts += [str(payload["amount"]), str(payload["action"]), str(payload["sign_time"])]
    return hashlib.md5("".join(parts).encode()).hexdigest()  # noqa: S324


async def test_click_prepare_accepts_valid_signature(click_credentials):
    provider = ClickProvider()
    payload = {
        "click_trans_id": "9001",
        "service_id": "2222",
        "merchant_trans_id": "order-123",
        "amount": "299000.00",
        "action": ACTION_PREPARE,
        "sign_time": "2026-07-30 12:00:00",
    }
    payload["sign_string"] = _click_sign(payload, "secret-key")

    result = await provider.parse_webhook(payload, {})
    assert result.status is PaymentStatus.pending
    assert result.provider_response["error"] == 0
    assert result.order_id == "order-123"
    assert not result.should_fulfill


async def test_click_complete_fulfills_order(click_credentials):
    provider = ClickProvider()
    payload = {
        "click_trans_id": "9001",
        "service_id": "2222",
        "merchant_trans_id": "order-123",
        "merchant_prepare_id": "order-123",
        "amount": "299000.00",
        "action": ACTION_COMPLETE,
        "error": 0,
        "sign_time": "2026-07-30 12:05:00",
    }
    payload["sign_string"] = _click_sign(payload, "secret-key")

    result = await provider.parse_webhook(payload, {})
    assert result.status is PaymentStatus.paid
    assert result.should_fulfill is True


async def test_click_rejects_bad_signature(click_credentials):
    provider = ClickProvider()
    payload = {
        "click_trans_id": "9001",
        "service_id": "2222",
        "merchant_trans_id": "order-123",
        "amount": "299000.00",
        "action": ACTION_PREPARE,
        "sign_time": "2026-07-30 12:00:00",
        "sign_string": "yolgon-imzo",
    }
    result = await provider.parse_webhook(payload, {})
    assert result.status is PaymentStatus.failed
    assert result.provider_response["error"] == -1
    assert not result.should_fulfill


async def test_payme_requires_basic_auth(monkeypatch):
    monkeypatch.setattr(settings, "PAYME_MERCHANT_ID", "merchant-1")
    monkeypatch.setattr(settings, "PAYME_MERCHANT_KEY", "payme-key")
    provider = PaymeProvider()

    payload = {
        "id": 1,
        "method": "PerformTransaction",
        "params": {"id": "txn-1", "amount": 29900000, "account": {"order_id": "order-9"}},
    }

    unauthorized = await provider.parse_webhook(payload, {})
    assert "error" in unauthorized.provider_response
    assert not unauthorized.should_fulfill

    token = base64.b64encode(b"Paycom:payme-key").decode()
    authorized = await provider.parse_webhook(payload, {"authorization": f"Basic {token}"})
    assert authorized.status is PaymentStatus.paid
    assert authorized.should_fulfill
    assert authorized.amount == Decimal("299000")
    assert authorized.provider_response["result"]["state"] == 2


async def test_payme_checkout_url_encodes_params(monkeypatch):
    monkeypatch.setattr(settings, "PAYME_MERCHANT_ID", "merchant-1")
    monkeypatch.setattr(settings, "PAYME_MERCHANT_KEY", "payme-key")
    provider = PaymeProvider()

    invoice = await provider.create_invoice(
        InvoiceRequest(
            order_id="order-9",
            order_number="ZH-260730-ABC123",
            amount=Decimal("299000"),
        )
    )
    encoded = invoice.checkout_url.rsplit("/", 1)[-1]
    decoded = base64.b64decode(encoded).decode()
    assert "m=merchant-1" in decoded
    assert "ac.order_id=order-9" in decoded
    assert "a=29900000" in decoded  # tiyinda


async def test_mock_provider_full_cycle():
    provider = MockPaymentProvider()
    invoice = await provider.create_invoice(
        InvoiceRequest(order_id="order-1", order_number="ZH-1", amount=Decimal("1000"))
    )
    assert "order_id=order-1" in invoice.checkout_url

    result = await provider.parse_webhook(
        {"order_id": "order-1", "success": True, "amount": "1000"}, {}
    )
    assert result.status is PaymentStatus.paid
    assert result.should_fulfill

    failed = await provider.parse_webhook({"order_id": "order-1", "success": False}, {})
    assert failed.status is PaymentStatus.failed
    assert not failed.should_fulfill
