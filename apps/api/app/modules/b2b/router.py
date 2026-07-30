from __future__ import annotations

import csv
import io
import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, File, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.core.deps import B2BUser, CurrentUser, DbSession, PaginationDep
from app.core.exceptions import NotFoundError, PermissionDeniedError, ValidationError
from app.core.security import generate_code, hash_password
from app.models.catalog import Course
from app.models.certificate import Certificate
from app.models.crm import CrmSyncLog
from app.models.enums import (
    CourseStatus,
    CrmSyncStatus,
    EnrollmentSource,
    EnrollmentStatus,
    UserRole,
)
from app.models.learning import Enrollment
from app.models.organization import Organization
from app.models.user import User
from app.modules.commerce.schemas import BulkEnrollRequest, BulkEnrollResult
from app.schemas.common import Message, ORMModel, Page

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/b2b", tags=["B2B"])


class EmployeeProgress(BaseModel):
    user_id: uuid.UUID
    full_name: str
    email: str
    courses_total: int = 0
    courses_completed: int = 0
    avg_progress: int = 0
    certificates: int = 0
    last_activity: datetime | None = None


class B2BDashboard(BaseModel):
    organization_id: uuid.UUID
    organization_name: str
    employees_count: int
    seats_purchased: int
    seats_used: int
    enrollments_total: int
    completed_total: int
    avg_progress: int
    certificates_total: int
    active_courses: int
    crm_sync_enabled: bool
    crm_last_sync_at: datetime | None = None


class EnrollmentRow(ORMModel):
    id: uuid.UUID
    user_id: uuid.UUID
    course_id: uuid.UUID
    status: EnrollmentStatus
    progress_percent: int
    enrolled_at: datetime
    completed_at: datetime | None = None
    user_name: str | None = None
    user_email: str | None = None
    course_title: str | None = None


class CrmSyncLogView(ORMModel):
    id: uuid.UUID
    provider: str
    event_type: str
    status: CrmSyncStatus
    external_id: str | None = None
    error_message: str | None = None
    attempts: int = 0
    created_at: datetime
    synced_at: datetime | None = None


async def _resolve_org(db, user: User, org_id: uuid.UUID | None = None) -> Organization:
    target_id = org_id or user.organization_id
    if target_id is None:
        owned = await db.scalar(select(Organization).where(Organization.owner_id == user.id))
        if owned is None:
            raise NotFoundError("Siz hech qanday tashkilotga bog'lanmagansiz")
        return owned

    org = await db.scalar(select(Organization).where(Organization.id == target_id))
    if org is None:
        raise NotFoundError("Tashkilot topilmadi")

    if (
        user.role is not UserRole.admin
        and org.id != user.organization_id
        and org.owner_id != user.id
    ):
        raise PermissionDeniedError("Bu tashkilot ma'lumotlariga ruxsatingiz yo'q")
    return org


@router.get("/dashboard", response_model=B2BDashboard, summary="B2B dashboard statistikasi")
async def dashboard(
    user: B2BUser, db: DbSession, organization_id: uuid.UUID | None = None
) -> B2BDashboard:
    org = await _resolve_org(db, user, organization_id)

    employees = await db.scalar(select(func.count(User.id)).where(User.organization_id == org.id))
    stats = (
        await db.execute(
            select(
                func.count(Enrollment.id),
                func.coalesce(func.avg(Enrollment.progress_percent), 0),
                func.count(func.distinct(Enrollment.course_id)),
                func.count(func.distinct(Enrollment.user_id)),
            ).where(Enrollment.organization_id == org.id)
        )
    ).one()
    completed = await db.scalar(
        select(func.count(Enrollment.id)).where(
            Enrollment.organization_id == org.id,
            Enrollment.status == EnrollmentStatus.completed,
        )
    )
    certificates = await db.scalar(
        select(func.count(Certificate.id))
        .join(Enrollment, Certificate.enrollment_id == Enrollment.id)
        .where(Enrollment.organization_id == org.id)
    )
    last_sync = await db.scalar(
        select(func.max(CrmSyncLog.synced_at)).where(
            CrmSyncLog.organization_id == org.id, CrmSyncLog.status == CrmSyncStatus.success
        )
    )

    return B2BDashboard(
        organization_id=org.id,
        organization_name=org.name,
        employees_count=int(employees or 0),
        seats_purchased=org.seats_purchased,
        seats_used=int(stats[3] or 0),
        enrollments_total=int(stats[0] or 0),
        completed_total=int(completed or 0),
        avg_progress=int(round(float(stats[1] or 0))),
        certificates_total=int(certificates or 0),
        active_courses=int(stats[2] or 0),
        crm_sync_enabled=org.crm_sync_enabled,
        crm_last_sync_at=last_sync,
    )


@router.get(
    "/employees", response_model=Page[EmployeeProgress], summary="Xodimlar ro'yxati va progressi"
)
async def employees(
    user: B2BUser,
    db: DbSession,
    pagination: PaginationDep,
    organization_id: uuid.UUID | None = None,
    search: str | None = Query(default=None),
) -> Page[EmployeeProgress]:
    org = await _resolve_org(db, user, organization_id)

    stmt = select(User).where(User.organization_id == org.id)
    if search:
        pattern = f"%{search.lower()}%"
        stmt = stmt.where(
            func.lower(User.full_name).like(pattern) | func.lower(User.email).like(pattern)
        )

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = await db.scalars(
        stmt.order_by(User.full_name).offset(pagination.offset).limit(pagination.limit)
    )

    items: list[EmployeeProgress] = []
    for employee in rows.all():
        agg = (
            await db.execute(
                select(
                    func.count(Enrollment.id),
                    func.coalesce(func.avg(Enrollment.progress_percent), 0),
                    func.max(Enrollment.updated_at),
                ).where(Enrollment.user_id == employee.id)
            )
        ).one()
        completed = await db.scalar(
            select(func.count(Enrollment.id)).where(
                Enrollment.user_id == employee.id,
                Enrollment.status == EnrollmentStatus.completed,
            )
        )
        certificates = await db.scalar(
            select(func.count(Certificate.id))
            .join(Enrollment, Certificate.enrollment_id == Enrollment.id)
            .where(Enrollment.user_id == employee.id)
        )
        items.append(
            EmployeeProgress(
                user_id=employee.id,
                full_name=employee.full_name,
                email=employee.email,
                courses_total=int(agg[0] or 0),
                courses_completed=int(completed or 0),
                avg_progress=int(round(float(agg[1] or 0))),
                certificates=int(certificates or 0),
                last_activity=agg[2],
            )
        )

    return Page.build(items, total, pagination.page, pagination.per_page)


@router.get("/enrollments", response_model=Page[EnrollmentRow], summary="Tashkilot enrollmentlari")
async def org_enrollments(
    user: B2BUser,
    db: DbSession,
    pagination: PaginationDep,
    organization_id: uuid.UUID | None = None,
    course_id: uuid.UUID | None = None,
    enrollment_status: EnrollmentStatus | None = None,
) -> Page[EnrollmentRow]:
    org = await _resolve_org(db, user, organization_id)

    stmt = (
        select(Enrollment)
        .where(Enrollment.organization_id == org.id)
        .options(selectinload(Enrollment.user), selectinload(Enrollment.course))
    )
    if course_id:
        stmt = stmt.where(Enrollment.course_id == course_id)
    if enrollment_status:
        stmt = stmt.where(Enrollment.status == enrollment_status)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = await db.scalars(
        stmt.order_by(Enrollment.enrolled_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
    )

    items = []
    for enrollment in rows.all():
        row = EnrollmentRow.model_validate(enrollment)
        row.user_name = enrollment.user.full_name if enrollment.user else None
        row.user_email = enrollment.user.email if enrollment.user else None
        row.course_title = enrollment.course.title if enrollment.course else None
        items.append(row)

    return Page.build(items, total, pagination.page, pagination.per_page)


@router.post(
    "/bulk-enroll",
    response_model=BulkEnrollResult,
    status_code=status.HTTP_201_CREATED,
    summary="Ko'p xodimni bir vaqtda kursga yozish",
)
async def bulk_enroll(
    payload: BulkEnrollRequest,
    user: B2BUser,
    db: DbSession,
    organization_id: uuid.UUID | None = None,
) -> BulkEnrollResult:
    org = await _resolve_org(db, user, organization_id)
    return await _do_bulk_enroll(db, org, payload.course_ids, [str(e) for e in payload.emails])


@router.post(
    "/bulk-enroll/csv",
    response_model=BulkEnrollResult,
    status_code=status.HTTP_201_CREATED,
    summary="CSV fayl orqali bulk enroll",
)
async def bulk_enroll_csv(
    user: B2BUser,
    db: DbSession,
    course_ids: str = Query(..., description="Vergul bilan ajratilgan kurs ID'lari"),
    file: UploadFile = File(..., description="CSV: email[,full_name]"),
    organization_id: uuid.UUID | None = None,
) -> BulkEnrollResult:
    org = await _resolve_org(db, user, organization_id)

    try:
        ids = [uuid.UUID(part.strip()) for part in course_ids.split(",") if part.strip()]
    except ValueError as exc:
        raise ValidationError("Kurs ID'lari noto'g'ri formatda") from exc

    raw = (await file.read()).decode("utf-8-sig", errors="ignore")
    reader = csv.reader(io.StringIO(raw))
    emails: list[str] = []
    names: dict[str, str] = {}
    for row in reader:
        if not row:
            continue
        email = row[0].strip().lower()
        if not email or "@" not in email or email == "email":
            continue
        emails.append(email)
        if len(row) > 1 and row[1].strip():
            names[email] = row[1].strip()

    if not emails:
        raise ValidationError("CSV faylda yaroqli email topilmadi")

    return await _do_bulk_enroll(db, org, ids, emails, names)


async def _do_bulk_enroll(
    db,
    org: Organization,
    course_ids: list[uuid.UUID],
    emails: list[str],
    names: dict[str, str] | None = None,
) -> BulkEnrollResult:
    names = names or {}
    courses = list(
        (
            await db.scalars(
                select(Course).where(
                    Course.id.in_(course_ids), Course.status == CourseStatus.published
                )
            )
        ).all()
    )
    if not courses:
        raise ValidationError("Nashr etilgan kurs topilmadi")

    unique_emails = list(dict.fromkeys(email.lower().strip() for email in emails))

    seats_used = int(
        await db.scalar(
            select(func.count(func.distinct(Enrollment.user_id))).where(
                Enrollment.organization_id == org.id
            )
        )
        or 0
    )
    seats_available = (org.seats_purchased - seats_used) if org.seats_purchased else None

    enrolled = 0
    created_users = 0
    skipped: list[str] = []
    new_students: set[uuid.UUID] = set()

    for email in unique_emails:
        student = await db.scalar(select(User).where(User.email == email))
        if student is None:
            if seats_available is not None and len(new_students) >= max(seats_available, 0):
                skipped.append(f"{email} (o'rinlar tugagan)")
                continue
            student = User(
                full_name=names.get(email) or email.split("@")[0].title(),
                email=email,
                role=UserRole.student,
                organization_id=org.id,
                hashed_password=hash_password(generate_code(16)),
            )
            db.add(student)
            await db.flush()
            created_users += 1
        elif student.organization_id is None:
            student.organization_id = org.id

        new_students.add(student.id)

        for course in courses:
            exists = await db.scalar(
                select(Enrollment.id).where(
                    Enrollment.user_id == student.id, Enrollment.course_id == course.id
                )
            )
            if exists:
                skipped.append(f"{email} → {course.title} (allaqachon yozilgan)")
                continue

            db.add(
                Enrollment(
                    user_id=student.id,
                    course_id=course.id,
                    organization_id=org.id,
                    source=EnrollmentSource.b2b_bulk,
                    status=EnrollmentStatus.active,
                )
            )
            course.students_count = (course.students_count or 0) + 1
            enrolled += 1

    await db.commit()

    if org.crm_sync_enabled:
        try:
            from app.worker.tasks.crm import sync_organization_to_crm

            sync_organization_to_crm.delay(str(org.id))
        except Exception as exc:
            logger.warning("CRM sync job navbatga qo'yilmadi: %s", exc)

    logger.info("Bulk enroll: org=%s enrolled=%s created=%s", org.slug, enrolled, created_users)
    return BulkEnrollResult(
        enrolled=enrolled,
        created_users=created_users,
        skipped=skipped[:100],
        seats_used=len(new_students),
        seats_available=seats_available,
    )


@router.get("/reports/csv", summary="Progress hisoboti (CSV export)")
async def export_report(user: B2BUser, db: DbSession, organization_id: uuid.UUID | None = None):
    from fastapi.responses import StreamingResponse

    org = await _resolve_org(db, user, organization_id)
    rows = await db.scalars(
        select(Enrollment)
        .where(Enrollment.organization_id == org.id)
        .options(selectinload(Enrollment.user), selectinload(Enrollment.course))
        .order_by(Enrollment.enrolled_at.desc())
    )

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["Xodim", "Email", "Kurs", "Holat", "Progress %", "Yozilgan sana", "Tugatgan sana"]
    )
    for enrollment in rows.all():
        writer.writerow(
            [
                enrollment.user.full_name if enrollment.user else "",
                enrollment.user.email if enrollment.user else "",
                enrollment.course.title if enrollment.course else "",
                enrollment.status.value,
                enrollment.progress_percent,
                enrollment.enrolled_at.strftime("%Y-%m-%d") if enrollment.enrolled_at else "",
                enrollment.completed_at.strftime("%Y-%m-%d") if enrollment.completed_at else "",
            ]
        )

    buffer.seek(0)
    filename = f"zehno-{org.slug}-{datetime.now(UTC):%Y%m%d}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/crm/sync-now", response_model=Message, summary="CRM bilan qo'lda sinxronizatsiya")
async def sync_now(
    user: CurrentUser, db: DbSession, organization_id: uuid.UUID | None = None
) -> Message:
    org = await _resolve_org(db, user, organization_id)
    if not org.crm_sync_enabled:
        raise ValidationError("Bu tashkilot uchun CRM sinxronizatsiyasi yoqilmagan")

    try:
        from app.worker.tasks.crm import sync_organization_to_crm

        sync_organization_to_crm.delay(str(org.id))
    except Exception as exc:
        raise ValidationError(f"Navbatga qo'yib bo'lmadi: {exc}") from exc

    return Message(message="Sinxronizatsiya navbatga qo'yildi")


@router.get("/crm/logs", response_model=Page[CrmSyncLogView], summary="CRM sinxronizatsiya loglari")
async def crm_logs(
    user: CurrentUser,
    db: DbSession,
    pagination: PaginationDep,
    organization_id: uuid.UUID | None = None,
) -> Page[CrmSyncLogView]:
    org = await _resolve_org(db, user, organization_id)

    stmt = select(CrmSyncLog).where(CrmSyncLog.organization_id == org.id)
    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = await db.scalars(
        stmt.order_by(CrmSyncLog.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
    )
    return Page.build(
        [CrmSyncLogView.model_validate(row) for row in rows.all()],
        total,
        pagination.page,
        pagination.per_page,
    )
