from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import func, select

from app.core.config import settings
from app.core.deps import AdminUser, DbSession, PaginationDep
from app.core.exceptions import NotFoundError
from app.integrations.factory import all_adapters
from app.integrations.storage.s3 import StorageService
from app.models.catalog import Course
from app.models.certificate import Certificate
from app.models.commerce import Order, OrderItem, PayoutRequest
from app.models.enums import (
    CourseStatus,
    EnrollmentStatus,
    IntegrationHealth,
    IntegrationKind,
    OrderStatus,
    UserRole,
)
from app.models.learning import Enrollment
from app.models.organization import Organization
from app.models.system import AuditLog, IntegrationStatus, SystemSetting
from app.models.user import User
from app.schemas.common import Message, ORMModel, Page

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Super Admin"])


class PlatformKpi(BaseModel):
    revenue_total: Decimal
    revenue_month: Decimal
    commission_total: Decimal
    users_total: int
    users_new_week: int
    students_active: int
    teachers_total: int
    organizations_total: int
    courses_published: int
    courses_pending: int
    enrollments_total: int
    completions_total: int
    certificates_total: int
    conversion_percent: float
    pending_payouts: int


class RevenuePoint(BaseModel):
    date: str
    revenue: Decimal
    commission: Decimal
    orders: int


class ActivityItem(BaseModel):
    type: str
    title: str
    subtitle: str | None = None
    created_at: datetime


class IntegrationStatusView(ORMModel):
    provider: str
    display_name: str
    kind: IntegrationKind
    health: IntegrationHealth
    is_enabled: bool
    last_success_at: datetime | None = None
    last_error_at: datetime | None = None
    last_error_message: str | None = None
    consecutive_failures: int = 0


class SystemSettingView(ORMModel):
    key: str
    value: dict | None = None
    description: str | None = None
    is_public: bool


class SystemSettingUpsert(BaseModel):
    key: str
    value: dict
    description: str | None = None
    is_public: bool = False


class AuditLogView(ORMModel):
    id: uuid.UUID
    actor_id: uuid.UUID | None = None
    actor_email: str | None = None
    action: str
    entity_type: str | None = None
    entity_id: str | None = None
    changes: dict | None = None
    created_at: datetime


@router.get("/dashboard", response_model=PlatformKpi, summary="Platforma KPI (super-admin)")
async def dashboard(_: AdminUser, db: DbSession) -> PlatformKpi:
    now = datetime.now(UTC)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)

    revenue_total = await db.scalar(
        select(func.coalesce(func.sum(Order.total), 0)).where(Order.status == OrderStatus.paid)
    )
    revenue_month = await db.scalar(
        select(func.coalesce(func.sum(Order.total), 0)).where(
            Order.status == OrderStatus.paid, Order.paid_at >= month_start
        )
    )
    commission_total = await db.scalar(
        select(func.coalesce(func.sum(OrderItem.commission_amount), 0))
        .join(Order, OrderItem.order_id == Order.id)
        .where(Order.status == OrderStatus.paid)
    )

    users_total = await db.scalar(select(func.count(User.id)))
    users_new_week = await db.scalar(select(func.count(User.id)).where(User.created_at >= week_ago))
    teachers_total = await db.scalar(
        select(func.count(User.id)).where(User.role.in_([UserRole.teacher, UserRole.org_admin]))
    )
    students_active = await db.scalar(
        select(func.count(func.distinct(Enrollment.user_id))).where(
            Enrollment.status == EnrollmentStatus.active
        )
    )
    organizations_total = await db.scalar(select(func.count(Organization.id)))

    courses_published = await db.scalar(
        select(func.count(Course.id)).where(Course.status == CourseStatus.published)
    )
    courses_pending = await db.scalar(
        select(func.count(Course.id)).where(Course.status == CourseStatus.pending)
    )

    enrollments_total = await db.scalar(select(func.count(Enrollment.id)))
    completions_total = await db.scalar(
        select(func.count(Enrollment.id)).where(Enrollment.status == EnrollmentStatus.completed)
    )
    certificates_total = await db.scalar(select(func.count(Certificate.id)))
    pending_payouts = await db.scalar(
        select(func.count(PayoutRequest.id)).where(PayoutRequest.status == "pending")
    )

    paid_orders = await db.scalar(
        select(func.count(Order.id)).where(Order.status == OrderStatus.paid)
    )
    all_orders = await db.scalar(select(func.count(Order.id))) or 0
    conversion = round((paid_orders or 0) / all_orders * 100, 2) if all_orders else 0.0

    return PlatformKpi(
        revenue_total=Decimal(str(revenue_total or 0)),
        revenue_month=Decimal(str(revenue_month or 0)),
        commission_total=Decimal(str(commission_total or 0)),
        users_total=int(users_total or 0),
        users_new_week=int(users_new_week or 0),
        students_active=int(students_active or 0),
        teachers_total=int(teachers_total or 0),
        organizations_total=int(organizations_total or 0),
        courses_published=int(courses_published or 0),
        courses_pending=int(courses_pending or 0),
        enrollments_total=int(enrollments_total or 0),
        completions_total=int(completions_total or 0),
        certificates_total=int(certificates_total or 0),
        conversion_percent=conversion,
        pending_payouts=int(pending_payouts or 0),
    )


@router.get("/dashboard/revenue", response_model=list[RevenuePoint], summary="Daromad grafigi")
async def revenue_chart(
    _: AdminUser, db: DbSession, days: int = Query(default=30, ge=7, le=365)
) -> list[RevenuePoint]:
    since = datetime.now(UTC) - timedelta(days=days)
    rows = await db.execute(
        select(
            func.date(Order.paid_at),
            func.coalesce(func.sum(Order.total), 0),
            func.count(Order.id),
        )
        .where(Order.status == OrderStatus.paid, Order.paid_at >= since)
        .group_by(func.date(Order.paid_at))
        .order_by(func.date(Order.paid_at))
    )
    commission_percent = Decimal(str(settings.PLATFORM_COMMISSION_PERCENT))
    return [
        RevenuePoint(
            date=str(row[0]),
            revenue=Decimal(str(row[1] or 0)),
            commission=(Decimal(str(row[1] or 0)) * commission_percent / 100).quantize(
                Decimal("0.01")
            ),
            orders=int(row[2] or 0),
        )
        for row in rows.all()
    ]


@router.get("/dashboard/activity", response_model=list[ActivityItem], summary="So'nggi faoliyat")
async def activity_feed(
    _: AdminUser, db: DbSession, limit: int = Query(default=15, ge=1, le=50)
) -> list[ActivityItem]:
    items: list[ActivityItem] = []

    new_users = await db.scalars(select(User).order_by(User.created_at.desc()).limit(limit))
    for user in new_users.all():
        items.append(
            ActivityItem(
                type="user_registered",
                title=f"Yangi foydalanuvchi: {user.full_name}",
                subtitle=f"{user.role.value} · {user.email}",
                created_at=user.created_at,
            )
        )

    new_courses = await db.scalars(select(Course).order_by(Course.created_at.desc()).limit(limit))
    for course in new_courses.all():
        items.append(
            ActivityItem(
                type="course_created",
                title=f"Kurs: {course.title}",
                subtitle=f"holat: {course.status.value}",
                created_at=course.created_at,
            )
        )

    paid = await db.scalars(
        select(Order)
        .where(Order.status == OrderStatus.paid)
        .order_by(Order.paid_at.desc())
        .limit(limit)
    )
    for order in paid.all():
        items.append(
            ActivityItem(
                type="order_paid",
                title=f"To'lov: {order.order_number}",
                subtitle=f"{order.total} {order.currency}",
                created_at=order.paid_at or order.created_at,
            )
        )

    items.sort(key=lambda item: item.created_at, reverse=True)
    return items[:limit]


@router.get(
    "/integrations",
    response_model=list[IntegrationStatusView],
    summary="Integratsiyalar monitoringi",
)
async def integrations(_: AdminUser, db: DbSession) -> list[IntegrationStatusView]:
    stored = {
        (row.kind, row.provider): row for row in (await db.scalars(select(IntegrationStatus))).all()
    }

    result: list[IntegrationStatusView] = []
    for adapter in all_adapters():
        provider = getattr(adapter, "provider_name", "unknown")
        kind = getattr(adapter, "kind", IntegrationKind.video)
        row = stored.get((kind, provider))
        result.append(
            IntegrationStatusView(
                provider=provider,
                display_name=getattr(adapter, "display_name", provider),
                kind=kind,
                health=(
                    row.health
                    if row
                    else (
                        IntegrationHealth.ok
                        if adapter.is_configured()
                        else IntegrationHealth.disabled
                    )
                ),
                is_enabled=adapter.is_configured(),
                last_success_at=row.last_success_at if row else None,
                last_error_at=row.last_error_at if row else None,
                last_error_message=row.last_error_message if row else None,
                consecutive_failures=row.consecutive_failures if row else 0,
            )
        )

    ok, error = await asyncio.to_thread(StorageService().healthcheck)
    result.append(
        IntegrationStatusView(
            provider="s3",
            display_name="Object Storage (MinIO/S3)",
            kind=IntegrationKind.storage,
            health=IntegrationHealth.ok if ok else IntegrationHealth.error,
            is_enabled=True,
            last_error_message=error,
        )
    )
    return result


@router.post(
    "/integrations/healthcheck",
    response_model=list[IntegrationStatusView],
    summary="Barcha integratsiyalarni tekshirish",
)
async def run_healthchecks(_: AdminUser, db: DbSession) -> list[IntegrationStatusView]:
    now = datetime.now(UTC)
    result: list[IntegrationStatusView] = []

    for adapter in all_adapters():
        provider = getattr(adapter, "provider_name", "unknown")
        kind = getattr(adapter, "kind", IntegrationKind.video)
        ok, error = await adapter.healthcheck()

        row = await db.scalar(
            select(IntegrationStatus).where(
                IntegrationStatus.kind == kind,
                IntegrationStatus.provider == provider,
            )
        )
        if row is None:
            row = IntegrationStatus(
                provider=provider,
                display_name=getattr(adapter, "display_name", provider),
                kind=kind,
                consecutive_failures=0,
            )
            db.add(row)

        row.is_enabled = adapter.is_configured()
        if ok:
            row.health = IntegrationHealth.ok
            row.last_success_at = now
            row.consecutive_failures = 0
            row.last_error_message = None
        else:
            row.consecutive_failures = (row.consecutive_failures or 0) + 1
            row.health = (
                IntegrationHealth.disabled
                if not adapter.is_configured()
                else IntegrationHealth.error
            )
            row.last_error_at = now
            row.last_error_message = error

        result.append(
            IntegrationStatusView(
                provider=provider,
                display_name=row.display_name,
                kind=row.kind,
                health=row.health,
                is_enabled=row.is_enabled,
                last_success_at=row.last_success_at,
                last_error_at=row.last_error_at,
                last_error_message=row.last_error_message,
                consecutive_failures=row.consecutive_failures,
            )
        )

    await db.commit()
    return result


@router.get(
    "/settings", response_model=list[SystemSettingView], summary="Tizim sozlamalari / feature flags"
)
async def list_settings(_: AdminUser, db: DbSession) -> list[SystemSettingView]:
    rows = await db.scalars(select(SystemSetting).order_by(SystemSetting.key))
    return [SystemSettingView.model_validate(row) for row in rows.all()]


@router.put("/settings", response_model=SystemSettingView, summary="Sozlamani saqlash")
async def upsert_setting(
    payload: SystemSettingUpsert, _: AdminUser, db: DbSession
) -> SystemSettingView:
    row = await db.scalar(select(SystemSetting).where(SystemSetting.key == payload.key))
    if row is None:
        row = SystemSetting(key=payload.key)
        db.add(row)
    row.value = payload.value
    row.description = payload.description
    row.is_public = payload.is_public
    await db.commit()
    await db.refresh(row)
    return SystemSettingView.model_validate(row)


@router.delete("/settings/{key}", response_model=Message, summary="Sozlamani o'chirish")
async def delete_setting(key: str, _: AdminUser, db: DbSession) -> Message:
    row = await db.scalar(select(SystemSetting).where(SystemSetting.key == key))
    if row is None:
        raise NotFoundError("Sozlama topilmadi")
    await db.delete(row)
    await db.commit()
    return Message(message="Sozlama o'chirildi")


@router.get("/audit-logs", response_model=Page[AuditLogView], summary="Audit loglari")
async def audit_logs(
    _: AdminUser,
    db: DbSession,
    pagination: PaginationDep,
    action: str | None = None,
    actor_id: uuid.UUID | None = None,
) -> Page[AuditLogView]:
    stmt = select(AuditLog)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if actor_id:
        stmt = stmt.where(AuditLog.actor_id == actor_id)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = await db.scalars(
        stmt.order_by(AuditLog.created_at.desc()).offset(pagination.offset).limit(pagination.limit)
    )
    return Page.build(
        [AuditLogView.model_validate(row) for row in rows.all()],
        total,
        pagination.page,
        pagination.per_page,
    )
