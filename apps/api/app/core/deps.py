"""FastAPI dependency'lari: DB sessiya, joriy foydalanuvchi, RBAC guardlar, pagination."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.core.security import TokenDecodeError, decode_token
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False, description="JWT access token")

DbSession = Annotated[AsyncSession, Depends(get_db)]
BearerCreds = Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]


async def _user_from_token(db: AsyncSession, token: str) -> User:
    try:
        payload = decode_token(token, expected_type="access")
    except TokenDecodeError as exc:
        raise AuthenticationError("Token yaroqsiz yoki muddati tugagan") from exc

    subject = payload.get("sub")
    if not subject:
        raise AuthenticationError("Token tarkibi noto'g'ri")

    try:
        user_id = uuid.UUID(str(subject))
    except ValueError as exc:
        raise AuthenticationError("Token tarkibi noto'g'ri") from exc

    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise AuthenticationError("Foydalanuvchi topilmadi")
    if not user.is_active or user.is_blocked:
        raise PermissionDeniedError("Hisob bloklangan yoki faol emas")
    return user


async def get_current_user(db: DbSession, creds: BearerCreds) -> User:
    """Majburiy autentifikatsiya."""
    if creds is None or not creds.credentials:
        raise AuthenticationError()
    return await _user_from_token(db, creds.credentials)


async def get_current_user_optional(db: DbSession, creds: BearerCreds) -> User | None:
    """Ixtiyoriy autentifikatsiya — katalog kabi ochiq endpointlar uchun.

    Token bo'lsa foydalanuvchini qaytaradi (masalan "sotib olingan" belgisini
    ko'rsatish uchun), bo'lmasa `None`.
    """
    if creds is None or not creds.credentials:
        return None
    try:
        return await _user_from_token(db, creds.credentials)
    except (AuthenticationError, PermissionDeniedError):
        return None


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]


def require_roles(*roles: UserRole) -> Callable[[User], Awaitable[User]]:
    """RBAC guard: `Depends(require_roles(UserRole.teacher, UserRole.admin))`.

    `admin` roli har doim ruxsat etiladi (super-admin barcha huquqlarga ega).
    """
    allowed: Sequence[UserRole] = (*roles, UserRole.admin)

    async def _guard(user: CurrentUser) -> User:
        if user.role not in allowed:
            raise PermissionDeniedError(
                f"Bu amal uchun quyidagi rollar kerak: {', '.join(r.value for r in roles)}"
            )
        return user

    return _guard


# Tez-tez ishlatiladigan guardlar
require_admin = require_roles(UserRole.admin)
require_teacher = require_roles(UserRole.teacher, UserRole.org_admin)
require_org_admin = require_roles(UserRole.org_admin)
require_b2b = require_roles(UserRole.b2b_manager, UserRole.org_admin)

AdminUser = Annotated[User, Depends(require_admin)]
TeacherUser = Annotated[User, Depends(require_teacher)]
B2BUser = Annotated[User, Depends(require_b2b)]


@dataclass(slots=True)
class Pagination:
    page: int
    per_page: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page

    @property
    def limit(self) -> int:
        return self.per_page


def pagination_params(
    page: Annotated[int, Query(ge=1, description="Sahifa raqami")] = 1,
    per_page: Annotated[int, Query(ge=1, le=100, description="Sahifadagi elementlar")] = 20,
) -> Pagination:
    return Pagination(page=page, per_page=per_page)


PaginationDep = Annotated[Pagination, Depends(pagination_params)]


def client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None
