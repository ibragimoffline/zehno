"""Parol hash va JWT testlari."""

from __future__ import annotations

import time
import uuid

import pytest

from app.core.security import (
    TokenDecodeError,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_code,
    hash_password,
    hash_token,
    verify_password,
)


def test_password_hash_and_verify():
    hashed = hash_password("StrongPass123")
    assert hashed != "StrongPass123"
    assert verify_password("StrongPass123", hashed)
    assert not verify_password("WrongPass123", hashed)


def test_verify_password_with_none_hash():
    assert not verify_password("anything", None)


def test_access_token_roundtrip():
    user_id = uuid.uuid4()
    token, expires_at = create_access_token(user_id, role="teacher", organization_id=None)

    payload = decode_token(token, expected_type="access")
    assert payload["sub"] == str(user_id)
    assert payload["role"] == "teacher"
    assert payload["type"] == "access"
    assert expires_at.timestamp() == pytest.approx(payload["exp"], abs=2)


def test_refresh_token_type_is_enforced():
    token, jti, _ = create_refresh_token(uuid.uuid4())
    assert len(jti) == 32

    # refresh tokenni access sifatida ishlatib bo'lmaydi
    with pytest.raises(TokenDecodeError):
        decode_token(token, expected_type="access")


def test_invalid_token_raises():
    with pytest.raises(TokenDecodeError):
        decode_token("aniq-yaroqsiz-token", expected_type="access")


def test_hash_token_is_deterministic():
    assert hash_token("abc") == hash_token("abc")
    assert hash_token("abc") != hash_token("abd")


def test_generate_code_has_no_ambiguous_chars():
    code = generate_code(24)
    assert len(code) == 24
    assert not set(code) & set("O0I1")


def test_tokens_are_unique_per_call():
    subject = uuid.uuid4()
    first, _ = create_access_token(subject, role="student")
    time.sleep(0.01)
    second, _ = create_access_token(subject, role="student")
    assert first != second  # jti har xil
