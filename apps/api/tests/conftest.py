from __future__ import annotations

import os

import pytest

os.environ.setdefault("TESTING", "true")
os.environ.setdefault("VIDEO_PROVIDER", "mock")
os.environ.setdefault("PAYMENT_PROVIDER", "mock")
os.environ.setdefault("CRM_PROVIDER", "mock")
os.environ.setdefault("TELEGRAM_ENABLED", "false")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")


@pytest.fixture(autouse=True)
def _reset_integration_cache():
    from app.integrations.factory import reset_cache

    reset_cache()
    yield
    reset_cache()
