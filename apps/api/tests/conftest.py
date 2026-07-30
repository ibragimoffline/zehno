"""Pytest umumiy sozlamalari."""

from __future__ import annotations

import os

import pytest

# Testlar uchun himoyalangan default'lar — haqiqiy provayderlarga chiqmasligi uchun
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("VIDEO_PROVIDER", "mock")
os.environ.setdefault("PAYMENT_PROVIDER", "mock")
os.environ.setdefault("CRM_PROVIDER", "mock")
os.environ.setdefault("TELEGRAM_ENABLED", "false")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")


@pytest.fixture(autouse=True)
def _reset_integration_cache():
    """Har bir testdan keyin adapter cache tozalanadi (monkeypatch qilingan sozlamalar uchun)."""
    from app.integrations.factory import reset_cache

    reset_cache()
    yield
    reset_cache()
