from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Query, status
from pydantic import BaseModel, EmailStr, Field
from slugify import slugify
from sqlalchemy import func, or_, select

from app.core.deps import AdminUser, CurrentUser, DbSession, PaginationDep
from app.core.exceptions import ConflictError, NotFoundError, PermissionDeniedError
from app.core.security import generate_code
from app.models.enums import OrganizationType, UserRole
from app.models.organization import Organization
from app.models.user import User
from app.schemas.common import Message, ORMModel, Page

router = APIRouter(tags=["Organizations"])


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    type: OrganizationType
    description: str | None = None
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=32)
    website: str | None = Field(default=None, max_length=255)


class OrganizationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    logo_url: str | None = Field(default=None, max_length=512)
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=32)
    website: str | None = Field(default=None, max_length=255)
    payout_details: dict | None = None


class OrganizationCrmUpdate(BaseModel):
    crm_sync_enabled: bool
    crm_provider: str | None = Field(default=None, max_length=32)
    crm_external_id: str | None = Field(default=None, max_length=128)
    crm_company_id: str | None = Field(default=None, max_length=128)


class OrganizationPublic(ORMModel):
    id: uuid.UUID
    name: str
    slug: str
    type: OrganizationType
    description: str | None = None
    logo_url: str | None = None
    website: str | None = None
    is_verified: bool
    created_at: datetime


class OrganizationDetail(OrganizationPublic):
    contact_email: str | None = None
    contact_phone: str | None = None
    owner_id: uuid.UUID | None = None
    seats_purchased: int = 0
    crm_sync_enabled: bool = False
    crm_provider: str | None = None
    crm_external_id: str | None = None
    members_count: int = 0
    courses_count: int = 0
    is_active: bool = True


class MemberInvite(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=160)
    role: UserRole = UserRole.student


class MemberView(ORMModel):
    id: uuid.UUID
    full_name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime


async def _unique_slug(db, name: str) -> str:
    base = slugify(name)[:200] or f"org-{generate_code(6, upper=False)}"
    slug, suffix = base, 1
    while await db.scalar(select(Organization).where(Organization.slug == slug)):
        suffix += 1
        slug = f"{base}-{suffix}"
    return slug


async def _get_org_or_404(db, org_id: uuid.UUID) -> Organization:
    org = await db.scalar(select(Organization).where(Organization.id == org_id))
    if org is None:
        raise NotFoundError("Tashkilot topilmadi")
    return org


def _assert_can_manage(user: User, org: Organization) -> None:
    if user.role is UserRole.admin:
        return
    is_owner = org.owner_id == user.id
    is_member_admin = user.organization_id == org.id and user.role in (
        UserRole.org_admin,
        UserRole.b2b_manager,
    )
    if not (is_owner or is_member_admin):
        raise PermissionDeniedError("Bu tashkilotni boshqarish huquqingiz yo'q")


@router.post(
    "/organizations",
    response_model=OrganizationDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Tashkilot yaratish",
)
async def create_organization(
    payload: OrganizationCreate,
    user: CurrentUser,
    db: DbSession,
) -> OrganizationDetail:
    if user.role is UserRole.student:
        raise PermissionDeniedError("Tashkilot yaratish uchun ustoz yoki B2B menejer roli kerak")

    exists = await db.scalar(select(Organization).where(Organization.name == payload.name.strip()))
    if exists:
        raise ConflictError("Bunday nomli tashkilot allaqachon mavjud")

    org = Organization(
        name=payload.name.strip(),
        slug=await _unique_slug(db, payload.name),
        type=payload.type,
        description=payload.description,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
        website=payload.website,
        owner_id=user.id,
    )
    db.add(org)
    await db.flush()

    if user.organization_id is None:
        user.organization_id = org.id
    if user.role is UserRole.teacher and payload.type in (
        OrganizationType.school,
        OrganizationType.training_center,
    ):
        user.role = UserRole.org_admin
    elif payload.type is OrganizationType.b2b_client and user.role is not UserRole.admin:
        user.role = UserRole.b2b_manager

    await db.commit()
    await db.refresh(org)
    return OrganizationDetail.model_validate(org)


@router.get(
    "/organizations",
    response_model=Page[OrganizationPublic],
    summary="Tashkilotlar ro'yxati (ochiq)",
)
async def list_organizations(
    db: DbSession,
    pagination: PaginationDep,
    type: OrganizationType | None = None,
    search: str | None = Query(default=None),
) -> Page[OrganizationPublic]:
    stmt = select(Organization).where(Organization.is_active.is_(True))
    if type is not None:
        stmt = stmt.where(Organization.type == type)
    if search:
        stmt = stmt.where(func.lower(Organization.name).like(f"%{search.lower()}%"))

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = await db.scalars(
        stmt.order_by(Organization.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
    )
    return Page.build(
        [OrganizationPublic.model_validate(o) for o in rows.all()],
        total,
        pagination.page,
        pagination.per_page,
    )


@router.get("/organizations/me", response_model=OrganizationDetail, summary="Mening tashkilotim")
async def my_organization(user: CurrentUser, db: DbSession) -> OrganizationDetail:
    org_id = user.organization_id
    if org_id is None:
        owned = await db.scalar(select(Organization).where(Organization.owner_id == user.id))
        if owned is None:
            raise NotFoundError("Siz hech qanday tashkilotga a'zo emassiz")
        org_id = owned.id

    org = await _get_org_or_404(db, org_id)
    detail = OrganizationDetail.model_validate(org)
    detail.members_count = (
        await db.scalar(select(func.count(User.id)).where(User.organization_id == org.id)) or 0
    )
    return detail


@router.get(
    "/organizations/{org_id}",
    response_model=OrganizationDetail,
    summary="Tashkilot ma'lumoti",
)
async def get_organization(org_id: uuid.UUID, db: DbSession) -> OrganizationDetail:
    org = await _get_org_or_404(db, org_id)
    detail = OrganizationDetail.model_validate(org)
    detail.members_count = (
        await db.scalar(select(func.count(User.id)).where(User.organization_id == org.id)) or 0
    )
    return detail


@router.patch(
    "/organizations/{org_id}",
    response_model=OrganizationDetail,
    summary="Tashkilotni tahrirlash",
)
async def update_organization(
    org_id: uuid.UUID,
    payload: OrganizationUpdate,
    user: CurrentUser,
    db: DbSession,
) -> OrganizationDetail:
    org = await _get_org_or_404(db, org_id)
    _assert_can_manage(user, org)

    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(org, field, value)

    await db.commit()
    await db.refresh(org)
    return OrganizationDetail.model_validate(org)


@router.patch(
    "/organizations/{org_id}/crm",
    response_model=OrganizationDetail,
    summary="CRM integratsiyasini sozlash",
)
async def update_crm_settings(
    org_id: uuid.UUID,
    payload: OrganizationCrmUpdate,
    user: CurrentUser,
    db: DbSession,
) -> OrganizationDetail:
    org = await _get_org_or_404(db, org_id)
    _assert_can_manage(user, org)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(org, field, value)

    await db.commit()
    await db.refresh(org)
    return OrganizationDetail.model_validate(org)


@router.get(
    "/organizations/{org_id}/members",
    response_model=Page[MemberView],
    summary="Tashkilot a'zolari",
)
async def list_members(
    org_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
    pagination: PaginationDep,
) -> Page[MemberView]:
    org = await _get_org_or_404(db, org_id)
    _assert_can_manage(user, org)

    stmt = select(User).where(User.organization_id == org.id)
    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = await db.scalars(
        stmt.order_by(User.created_at.desc()).offset(pagination.offset).limit(pagination.limit)
    )
    return Page.build(
        [MemberView.model_validate(m) for m in rows.all()],
        total,
        pagination.page,
        pagination.per_page,
    )


@router.post(
    "/organizations/{org_id}/members",
    response_model=MemberView,
    status_code=status.HTTP_201_CREATED,
    summary="A'zo qo'shish (mavjud bo'lmasa yaratiladi)",
)
async def add_member(
    org_id: uuid.UUID,
    payload: MemberInvite,
    user: CurrentUser,
    db: DbSession,
) -> MemberView:
    from app.core.security import (
        hash_password,
    )

    org = await _get_org_or_404(db, org_id)
    _assert_can_manage(user, org)

    email = payload.email.lower()
    member = await db.scalar(select(User).where(User.email == email))
    if member is None:
        member = User(
            full_name=payload.full_name,
            email=email,
            role=payload.role,
            organization_id=org.id,
            hashed_password=hash_password(generate_code(16)),
        )
        db.add(member)
    else:
        if member.organization_id and member.organization_id != org.id:
            raise ConflictError("Bu foydalanuvchi boshqa tashkilotga a'zo")
        member.organization_id = org.id

    await db.commit()
    await db.refresh(member)
    return MemberView.model_validate(member)


@router.delete(
    "/organizations/{org_id}/members/{member_id}",
    response_model=Message,
    summary="A'zoni chiqarish",
)
async def remove_member(
    org_id: uuid.UUID,
    member_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> Message:
    org = await _get_org_or_404(db, org_id)
    _assert_can_manage(user, org)

    member = await db.scalar(
        select(User).where(User.id == member_id, User.organization_id == org.id)
    )
    if member is None:
        raise NotFoundError("A'zo topilmadi")
    if member.id == org.owner_id:
        raise PermissionDeniedError("Tashkilot egasini chiqarib bo'lmaydi")

    member.organization_id = None
    await db.commit()
    return Message(message="A'zo tashkilotdan chiqarildi")


@router.get(
    "/admin/organizations",
    response_model=Page[OrganizationDetail],
    summary="Barcha tashkilotlar (super-admin)",
)
async def admin_list_organizations(
    _: AdminUser,
    db: DbSession,
    pagination: PaginationDep,
    search: str | None = None,
    type: OrganizationType | None = None,
) -> Page[OrganizationDetail]:
    stmt = select(Organization)
    if type is not None:
        stmt = stmt.where(Organization.type == type)
    if search:
        pattern = f"%{search.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Organization.name).like(pattern),
                func.lower(Organization.slug).like(pattern),
            )
        )

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = await db.scalars(
        stmt.order_by(Organization.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
    )

    items = []
    for org in rows.all():
        detail = OrganizationDetail.model_validate(org)
        detail.members_count = (
            await db.scalar(select(func.count(User.id)).where(User.organization_id == org.id)) or 0
        )
        items.append(detail)

    return Page.build(items, total, pagination.page, pagination.per_page)


@router.patch(
    "/admin/organizations/{org_id}/verify",
    response_model=OrganizationDetail,
    summary="Tashkilotni tasdiqlash (super-admin)",
)
async def verify_organization(
    org_id: uuid.UUID,
    _: AdminUser,
    db: DbSession,
    is_verified: bool = True,
) -> OrganizationDetail:
    org = await _get_org_or_404(db, org_id)
    org.is_verified = is_verified
    await db.commit()
    await db.refresh(org)
    return OrganizationDetail.model_validate(org)
