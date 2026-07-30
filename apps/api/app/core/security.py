from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from jose import JWTError, jwt

from app.core.config import settings

TokenType = Literal["access", "refresh"]

_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    if settings.PASSWORD_HASH_SCHEME == "bcrypt":
        import bcrypt

        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    return _password_hasher.hash(password)


def verify_password(password: str, hashed: str | None) -> bool:
    if not hashed:
        return False
    try:
        if hashed.startswith("$2"):
            import bcrypt

            return bcrypt.checkpw(password.encode(), hashed.encode())
        _password_hasher.verify(hashed, password)
        return True
    except (VerifyMismatchError, VerificationError, InvalidHashError, ValueError):
        return False


def needs_rehash(hashed: str) -> bool:
    if not hashed or hashed.startswith("$2"):
        return False
    try:
        return _password_hasher.check_needs_rehash(hashed)
    except InvalidHashError:
        return False


def _now() -> datetime:
    return datetime.now(UTC)


def create_token(
    subject: str | uuid.UUID,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> tuple[str, str, datetime]:
    issued_at = _now()
    expires_at = issued_at + expires_delta
    jti = uuid.uuid4().hex

    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "jti": jti,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
        "iss": settings.APP_NAME.lower(),
    }
    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti, expires_at


def create_access_token(
    subject: str | uuid.UUID,
    role: str,
    organization_id: str | None = None,
) -> tuple[str, datetime]:
    token, _, expires_at = create_token(
        subject,
        "access",
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        {"role": role, "org": organization_id},
    )
    return token, expires_at


def create_refresh_token(subject: str | uuid.UUID) -> tuple[str, str, datetime]:
    return create_token(
        subject,
        "refresh",
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str, expected_type: TokenType | None = None) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_aud": False},
        )
    except JWTError as exc:
        raise TokenDecodeError(str(exc)) from exc

    if expected_type and payload.get("type") != expected_type:
        raise TokenDecodeError(
            f"Token turi mos emas: kutilgan '{expected_type}', kelgan '{payload.get('type')}'"
        )
    return payload


class TokenDecodeError(Exception): ...


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def generate_code(length: int = 12, *, upper: bool = True) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    code = "".join(secrets.choice(alphabet) for _ in range(length))
    return code if upper else code.lower()


def constant_time_compare(a: str, b: str) -> bool:
    return secrets.compare_digest(a.encode(), b.encode())
