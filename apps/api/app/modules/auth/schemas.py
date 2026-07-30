"""Auth sxemalari."""

from __future__ import annotations

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import UserRole
from app.schemas.common import ORMModel

PHONE_RE = re.compile(r"^\+?998\d{9}$|^\+?\d{9,15}$")


def validate_password_strength(value: str) -> str:
    """Parol talablari — ro'yxatdan o'tish va parol o'zgartirishda birgalikda ishlatiladi."""
    if not any(char.isdigit() for char in value):
        raise ValueError("Parolda kamida bitta raqam bo'lishi kerak")
    if not any(char.isalpha() for char in value):
        raise ValueError("Parolda kamida bitta harf bo'lishi kerak")
    return value


def normalize_phone(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    cleaned = re.sub(r"[\s\-()]", "", value)
    if not PHONE_RE.match(cleaned):
        raise ValueError("Telefon raqam formati noto'g'ri (masalan +998901234567)")
    return cleaned


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone: str | None = Field(default=None, max_length=32)
    role: UserRole = Field(
        default=UserRole.student,
        description="Ro'yxatdan o'tishda faqat `student` yoki `teacher` tanlanishi mumkin",
    )
    organization_name: str | None = Field(
        default=None,
        max_length=200,
        description="`teacher` roli uchun ixtiyoriy: o'quv markaz/maktab nomi",
    )

    @field_validator("password")
    @classmethod
    def _strong_password(cls, value: str) -> str:
        return validate_password_strength(value)

    @field_validator("phone")
    @classmethod
    def _valid_phone(cls, value: str | None) -> str | None:
        return normalize_phone(value)

    @field_validator("role")
    @classmethod
    def _public_roles_only(cls, value: UserRole) -> UserRole:
        if value not in (UserRole.student, UserRole.teacher):
            raise ValueError("Ro'yxatdan o'tishda faqat 'student' yoki 'teacher' roli mumkin")
        return value


class LoginRequest(BaseModel):
    """Login `email` yoki `phone` orqali amalga oshiriladi."""

    login: str = Field(min_length=3, max_length=255, description="Email yoki telefon raqam")
    password: str = Field(min_length=1, max_length=128)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_at: datetime
    expires_in: int


class UserPublic(ORMModel):
    id: uuid.UUID
    full_name: str
    email: EmailStr
    phone: str | None = None
    role: UserRole
    organization_id: uuid.UUID | None = None
    avatar_url: str | None = None
    bio: str | None = None
    locale: str = "uz"
    is_active: bool
    telegram_chat_id: str | None = None
    created_at: datetime


class AuthResponse(BaseModel):
    user: UserPublic
    tokens: TokenPair


class RefreshRequest(BaseModel):
    refresh_token: str | None = Field(
        default=None,
        description="Cookie mavjud bo'lmasa (mobil ilova) shu maydon orqali yuboriladi",
    )


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _strong(cls, value: str) -> str:
        return validate_password_strength(value)


class UpdateProfileRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=160)
    phone: str | None = Field(default=None, max_length=32)
    avatar_url: str | None = Field(default=None, max_length=512)
    bio: str | None = None
    locale: str | None = Field(default=None, max_length=5)

    @field_validator("phone")
    @classmethod
    def _valid_phone(cls, value: str | None) -> str | None:
        return normalize_phone(value)


class TelegramLinkResponse(BaseModel):
    link_code: str
    deep_link: str | None = None
    instructions: str
