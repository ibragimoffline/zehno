"""Foydalanuvchilarni boshqarish (super-admin) va ustozning ochiq profili."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select

from app.core.deps import AdminUser, DbSession, PaginationDep
from app.core.exceptions import NotFoundError, ValidationError
from app.models.catalog import Course
from app.models.enums import CourseStatus, UserRole
from app.models.user import User
from app.modules.auth.schemas import UserPublic
from app.schemas.common import Message, ORMModel, Page

router = APIRouter(tags=["Users"])


class UserAdminView(UserPublic):
    is_blocked: bool
    organization_name: str | None = None
    courses_count: int = 0
    enrollments_count: int = 0


class UpdateRoleRequest(BaseModel):
    role: UserRole


class BlockUserRequest(BaseModel):
    is_blocked: bool
    reason: str | None = Field(default=None, max_length=500)


class TeacherPublic(ORMModel):
    id: uuid.UUID
    full_name: str
    avatar_url: str | None = None
    bio: str | None = None
    courses_count: int = 0
    students_count: int = 0
    rating_avg: float = 0.0


# --------------------------------------------------------------- super-admin
@router.get(
    "/admin/users",
    response_model=Page[UserAdminView],
    summary="Barcha foydalanuvchilar (super-admin)",
)
async def list_users(
    _: AdminUser,
    db: DbSession,
    pagination: PaginationDep,
    search: str | None = Query(default=None, description="Ism, email yoki telefon bo'yicha"),
    role: UserRole | None = None,
    is_blocked: bool | None = None,
) -> Page[UserAdminView]:
    stmt = select(User)
    if search:
        pattern = f"%{search.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(User.full_name).like(pattern),
                func.lower(User.email).like(pattern),
                User.phone.like(f"%{search}%"),
            )
        )
    if role is not None:
        stmt = stmt.where(User.role == role)
    if is_blocked is not None:
        stmt = stmt.where(User.is_blocked == is_blocked)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = await db.scalars(
        stmt.order_by(User.created_at.desc()).offset(pagination.offset).limit(pagination.limit)
    )

    items: list[UserAdminView] = []
    for user in rows.all():
        courses_count = (
            await db.scalar(select(func.count(Course.id)).where(Course.owner_id == user.id)) or 0
        )
        view = UserAdminView.model_validate(user)
        view.courses_count = courses_count
        items.append(view)

    return Page.build(items, total, pagination.page, pagination.per_page)


@router.get("/admin/users/{user_id}", response_model=UserAdminView, summary="Foydalanuvchi (admin)")
async def get_user(user_id: uuid.UUID, _: AdminUser, db: DbSession) -> UserAdminView:
    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise NotFoundError("Foydalanuvchi topilmadi")
    return UserAdminView.model_validate(user)


@router.patch(
    "/admin/users/{user_id}/role",
    response_model=UserAdminView,
    summary="Rolni o'zgartirish (admin)",
)
async def update_role(
    user_id: uuid.UUID,
    payload: UpdateRoleRequest,
    admin: AdminUser,
    db: DbSession,
) -> UserAdminView:
    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise NotFoundError("Foydalanuvchi topilmadi")
    if user.id == admin.id and payload.role is not UserRole.admin:
        raise ValidationError("O'zingizning admin rolingizni olib tashlay olmaysiz")

    user.role = payload.role
    await db.commit()
    await db.refresh(user)
    return UserAdminView.model_validate(user)


@router.patch(
    "/admin/users/{user_id}/block",
    response_model=Message,
    summary="Bloklash / blokdan chiqarish (admin)",
)
async def block_user(
    user_id: uuid.UUID,
    payload: BlockUserRequest,
    admin: AdminUser,
    db: DbSession,
) -> Message:
    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise NotFoundError("Foydalanuvchi topilmadi")
    if user.id == admin.id:
        raise ValidationError("O'zingizni bloklay olmaysiz")

    user.is_blocked = payload.is_blocked
    await db.commit()
    return Message(
        message="Foydalanuvchi bloklandi" if payload.is_blocked else "Blokdan chiqarildi"
    )


# --------------------------------------------------------------- ochiq
@router.get("/teachers/{teacher_id}", response_model=TeacherPublic, summary="Ustoz profili")
async def teacher_profile(teacher_id: uuid.UUID, db: DbSession) -> TeacherPublic:
    user = await db.scalar(
        select(User).where(
            User.id == teacher_id,
            User.role.in_([UserRole.teacher, UserRole.org_admin]),
        )
    )
    if user is None:
        raise NotFoundError("Ustoz topilmadi")

    stats = (
        await db.execute(
            select(
                func.count(Course.id),
                func.coalesce(func.sum(Course.students_count), 0),
                func.coalesce(func.avg(Course.rating_avg), 0),
            ).where(Course.owner_id == user.id, Course.status == CourseStatus.published)
        )
    ).one()

    return TeacherPublic(
        id=user.id,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        bio=user.bio,
        courses_count=int(stats[0] or 0),
        students_count=int(stats[1] or 0),
        rating_avg=round(float(stats[2] or 0), 2),
    )
