"""Auth biznes-logikasi: ro'yxatdan o'tish, login, refresh rotatsiyasi, logout."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from slugify import slugify
from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError, ValidationError
from app.core.security import (
    TokenDecodeError,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_code,
    hash_password,
    hash_token,
    needs_rehash,
    verify_password,
)
from app.models.enums import OrganizationType, UserRole
from app.models.organization import Organization
from app.models.user import RefreshToken, User
from app.modules.auth.schemas import (
    LoginRequest,
    RegisterRequest,
    TokenPair,
    UpdateProfileRequest,
)

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ------------------------------------------------------------ register
    async def register(self, payload: RegisterRequest) -> User:
        email = payload.email.lower().strip()

        existing = await self.db.scalar(select(User).where(User.email == email))
        if existing:
            raise ConflictError("Bu email allaqachon ro'yxatdan o'tgan")

        if payload.phone:
            phone_taken = await self.db.scalar(select(User).where(User.phone == payload.phone))
            if phone_taken:
                raise ConflictError("Bu telefon raqam allaqachon ro'yxatdan o'tgan")

        organization: Organization | None = None
        if payload.role is UserRole.teacher and payload.organization_name:
            organization = await self._create_organization(
                payload.organization_name, OrganizationType.training_center
            )

        user = User(
            full_name=payload.full_name.strip(),
            email=email,
            phone=payload.phone,
            hashed_password=hash_password(payload.password),
            role=payload.role,
            organization_id=organization.id if organization else None,
        )
        self.db.add(user)
        await self.db.flush()

        if organization is not None:
            organization.owner_id = user.id

        await self.db.commit()
        await self.db.refresh(user)
        logger.info("Yangi foydalanuvchi ro'yxatdan o'tdi: %s (%s)", user.email, user.role)
        return user

    async def _create_organization(self, name: str, org_type: OrganizationType) -> Organization:
        base_slug = slugify(name)[:200] or f"org-{generate_code(6, upper=False)}"
        slug = base_slug
        suffix = 1
        while await self.db.scalar(select(Organization).where(Organization.slug == slug)):
            suffix += 1
            slug = f"{base_slug}-{suffix}"

        organization = Organization(name=name.strip(), slug=slug, type=org_type)
        self.db.add(organization)
        await self.db.flush()
        return organization

    # ------------------------------------------------------------ login
    async def authenticate(self, payload: LoginRequest) -> User:
        login = payload.login.strip()
        user = await self.db.scalar(
            select(User).where(or_(User.email == login.lower(), User.phone == login))
        )
        # Timing attack'ni kamaytirish uchun foydalanuvchi topilmasa ham hash tekshiriladi
        if user is None:
            verify_password(payload.password, "$argon2id$v=19$m=65536,t=3,p=4$" + "A" * 22)
            raise AuthenticationError("Login yoki parol xato")

        if not verify_password(payload.password, user.hashed_password):
            raise AuthenticationError("Login yoki parol xato")

        if user.is_blocked:
            raise AuthenticationError("Hisobingiz bloklangan. Administratorga murojaat qiling")
        if not user.is_active:
            raise AuthenticationError("Hisobingiz faol emas")

        # Argon2 parametrlari yangilangan bo'lsa — jimgina qayta hash qilamiz
        if user.hashed_password and needs_rehash(user.hashed_password):
            user.hashed_password = hash_password(payload.password)

        user.last_login_at = datetime.now(UTC)
        await self.db.commit()
        return user

    # ------------------------------------------------------------ tokenlar
    async def issue_tokens(
        self,
        user: User,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> TokenPair:
        access_token, expires_at = create_access_token(
            user.id,
            role=user.role.value,
            organization_id=str(user.organization_id) if user.organization_id else None,
        )
        refresh_token, jti, refresh_expires = create_refresh_token(user.id)

        self.db.add(
            RefreshToken(
                user_id=user.id,
                token_hash=hash_token(refresh_token),
                jti=jti,
                expires_at=refresh_expires,
                user_agent=(user_agent or "")[:255] or None,
                ip_address=ip_address,
            )
        )
        await self.db.commit()

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def rotate_refresh_token(
        self,
        raw_token: str,
        *,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[User, TokenPair]:
        """Refresh tokenni almashtiradi (rotation + reuse detection)."""
        try:
            payload = decode_token(raw_token, expected_type="refresh")
        except TokenDecodeError as exc:
            raise AuthenticationError("Refresh token yaroqsiz yoki muddati tugagan") from exc

        token_hash = hash_token(raw_token)
        stored = await self.db.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        if stored is None:
            raise AuthenticationError("Refresh token topilmadi")

        if stored.revoked_at is not None:
            # Bekor qilingan token qayta ishlatildi → barcha sessiyalarni yopamiz
            logger.warning("Refresh token reuse aniqlandi: user=%s", stored.user_id)
            await self.revoke_all_sessions(stored.user_id)
            raise AuthenticationError("Sessiya bekor qilingan. Iltimos qaytadan kiring")

        if stored.expires_at <= datetime.now(UTC):
            raise AuthenticationError("Refresh token muddati tugagan")

        user = await self.db.scalar(select(User).where(User.id == uuid.UUID(payload["sub"])))
        if user is None or user.is_blocked or not user.is_active:
            raise AuthenticationError("Foydalanuvchi faol emas")

        new_pair = await self.issue_tokens(user, user_agent=user_agent, ip_address=ip_address)

        stored.revoked_at = datetime.now(UTC)
        stored.replaced_by_jti = decode_token(new_pair.refresh_token or "", "refresh").get("jti")
        await self.db.commit()

        return user, new_pair

    async def revoke_refresh_token(self, raw_token: str) -> None:
        stored = await self.db.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_token))
        )
        if stored and stored.revoked_at is None:
            stored.revoked_at = datetime.now(UTC)
            await self.db.commit()

    async def revoke_all_sessions(self, user_id: uuid.UUID) -> None:
        await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )
        await self.db.commit()

    # ------------------------------------------------------------ profil
    async def update_profile(self, user: User, payload: UpdateProfileRequest) -> User:
        data = payload.model_dump(exclude_unset=True, exclude_none=True)

        if "phone" in data and data["phone"]:
            taken = await self.db.scalar(
                select(User).where(User.phone == data["phone"], User.id != user.id)
            )
            if taken:
                raise ConflictError("Bu telefon raqam boshqa foydalanuvchiga tegishli")

        for field, value in data.items():
            setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def change_password(self, user: User, current: str, new: str) -> None:
        if not verify_password(current, user.hashed_password):
            raise ValidationError("Joriy parol xato")
        if verify_password(new, user.hashed_password):
            raise ValidationError("Yangi parol joriy paroldan farq qilishi kerak")

        user.hashed_password = hash_password(new)
        await self.db.commit()
        # Parol o'zgargach barcha sessiyalar yopiladi
        await self.revoke_all_sessions(user.id)

    # ------------------------------------------------------------ telegram
    async def create_telegram_link_code(self, user: User) -> str:
        user.telegram_link_code = generate_code(10)
        await self.db.commit()
        return user.telegram_link_code

    async def link_telegram_chat(self, link_code: str, chat_id: str) -> User:
        user = await self.db.scalar(select(User).where(User.telegram_link_code == link_code))
        if user is None:
            raise NotFoundError("Bunday ulanish kodi topilmadi")
        user.telegram_chat_id = chat_id
        user.telegram_link_code = None
        await self.db.commit()
        await self.db.refresh(user)
        return user
